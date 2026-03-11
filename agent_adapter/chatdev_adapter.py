# =========== Agent Adapter - ChatDev 具体适配器实现 ===========
# 将 ChatDev 多角色软件开发系统封装为标准 Benchmark 接口
# =============================================================

"""
chatdev_adapter — ChatDev 具体适配器
====================================

将 ChatDev 的多智能体协作系统（ChatChain → Phase → RolePlaying）
封装为标准化的 ``AgentAdapterBase`` 接口。

ChatDev 内部流程:
    1. 初始化 ChatChain（加载配置、角色、阶段）
    2. pre_processing（清理、设置目录、任务增强）
    3. make_recruitment（招募 Agent 角色）
    4. execute_chain（按链式阶段依次执行多轮角色对话）
    5. post_processing（总结、日志归档、Git 管理）

所有这些步骤在 ``act()`` 中被封装为单次调用。
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from agent_adapter.api_config import get_api_key, get_base_url, get_model_name
from agent_adapter.base import AgentAdapterBase
from agent_adapter.exceptions import (
    InternalComponentError,
    SafetyFilterTriggeredError,
    TokenLimitExceededError,
)
from agent_adapter.models import (
    ActionOutput,
    ActionType,
    InternalLogEntry,
    ObservationInput,
)

logger = logging.getLogger(__name__)


class ChatDevAdapter(AgentAdapterBase):
    """
    ChatDev 智能体适配器

    将 ChatDev 多角色软件开发框架封装为标准 Benchmark 接口。
    底层系统包含 CEO、CTO、Programmer、Reviewer、Tester 等多个角色，
    通过多轮对话协作完成软件开发任务。

    所有内部多轮对话、代码生成、审查、测试等过程对 Benchmark 完全不可见，
    仅暴露最终的代码生成结果。

    参数:
        config: ChatDev 配置名称（对应 CompanyConfig/ 下的子目录）
        model: 模型类型名称（如 "GPT_4O", "DEEPSEEK_CHAT"）
        org_name: 组织名称
        chatdev_root: ChatDev 项目根目录路径（默认自动检测）

    使用示例::

        adapter = ChatDevAdapter(
            config="Default",
            model="DEEPSEEK_CHAT",
            org_name="BenchmarkOrg"
        )
        adapter.reset_session(task_id="task_001")
        result = adapter.act(ObservationInput(
            instruction="开发一个命令行计算器程序"
        ))
        print(result.action_type)   # ActionType.CODE_GENERATION
        print(result.action_content) # 生成的代码内容

        # 导出内部日志用于分析
        logs = adapter.get_internal_logs()
        for log in logs:
            print(f"[{log.phase_name}] {log.agent_role}: {log.content[:80]}...")
    """

    def __init__(
        self,
        config: str = "Default",
        model: str = "GPT_3_5_TURBO",
        org_name: str = "DefaultOrganization",
        chatdev_root: str | None = None,
    ):
        """
        初始化 ChatDev 适配器。

        参数:
            config: 配置名称，对应 CompanyConfig/ 下的子目录名
            model: 模型类型名称，支持 OpenAI 和 DeepSeek 模型
            org_name: 组织名称，用于生成输出目录
            chatdev_root: ChatDev 项目根目录（默认自动检测为本文件的上级目录）
        """
        super().__init__()

        # ChatDev 项目根路径
        if chatdev_root is None:
            self._chatdev_root = str(Path(__file__).resolve().parent.parent)
        else:
            self._chatdev_root = chatdev_root

        # 确保 ChatDev 根目录在 sys.path 中
        if self._chatdev_root not in sys.path:
            sys.path.insert(0, self._chatdev_root)

        self._config_name = config
        self._model_name = model
        self._org_name = org_name

        # 内部状态（在 reset_session 中初始化）
        self._chat_chain = None
        self._current_software_path: str | None = None

    # ================================================================
    #  1. 生命周期管理
    # ================================================================

    def reset_session(self, task_id: str, **kwargs: Any) -> None:
        """
        重置 ChatDev 会话，彻底清空所有内部状态。

        执行以下清理操作:
        1. 销毁已有的 ChatChain 实例
        2. 清除上一次生成的软件输出目录（可选）
        3. 重置内部日志缓冲
        4. 准备新的 ChatChain 实例（延迟到 act() 时初始化）

        参数:
            task_id: Benchmark 分配的唯一任务标识符
            **kwargs: 可选参数:
                - model_override (str): 覆盖默认模型类型
                - config_override (str): 覆盖默认配置名
                - clean_output (bool): 是否清理上次输出（默认 True）
        """
        # 记录重置事件
        self._log_event(
            phase_name="SessionManagement",
            agent_role="System",
            event_type="session_reset",
            content=f"正在重置会话，新任务 ID: {task_id}",
            metadata={"previous_task": self._current_task_id},
        )

        # 清理上一次的软件输出目录
        clean_output = kwargs.get("clean_output", True)
        if clean_output and self._current_software_path:
            if os.path.exists(self._current_software_path):
                try:
                    shutil.rmtree(self._current_software_path)
                    logger.info(f"已清理上次输出目录: {self._current_software_path}")
                except OSError as e:
                    logger.warning(f"清理输出目录失败: {e}")

        # 销毁 ChatChain 实例
        self._chat_chain = None
        self._current_software_path = None

        # 应用覆盖参数
        if "model_override" in kwargs:
            self._model_name = kwargs["model_override"]
        if "config_override" in kwargs:
            self._config_name = kwargs["config_override"]

        # 调用基类重置（设置 _session_initialized, 清空日志）
        super().reset_session(task_id, **kwargs)

    # ================================================================
    #  2. 核心交互
    # ================================================================

    def act(self, observation: ObservationInput) -> ActionOutput:
        """
        执行 ChatDev 软件开发流程并返回生成结果。

        内部流程:
        1. 将 observation.instruction 映射为 ChatDev 的 task_prompt
        2. 初始化 ChatChain（加载配置、解析角色和阶段）
        3. 依次执行: pre_processing → make_recruitment → execute_chain → post_processing
        4. 收集生成的代码文件，封装为 ActionOutput 返回

        所有内部多角色对话、代码审查、自测试等过程对 Benchmark 完全透明。

        参数:
            observation: 标准化观测输入

        返回:
            ActionOutput: 包含生成代码的标准化输出
        """
        # 检查会话状态
        self._check_session()

        self._log_event(
            phase_name="ActionGeneration",
            agent_role="System",
            event_type="act_start",
            content=f"开始处理任务: {observation.instruction[:100]}...",
            metadata={"task_id": self._current_task_id},
        )

        try:
            # ---- Step 1: 准备 ChatChain ----
            chat_chain = self._initialize_chat_chain(
                task_prompt=observation.instruction,
                project_name=self._current_task_id or "benchmark_task",
            )

            self._log_event(
                phase_name="Initialization",
                agent_role="System",
                event_type="chain_initialized",
                content="ChatChain 初始化完成",
                metadata={
                    "config": self._config_name,
                    "model": self._model_name,
                },
            )

            # ---- Step 2: 执行完整的 ChatDev 流程 ----
            # 预处理（清理、目录设置、任务增强）
            chat_chain.pre_processing()
            self._log_event(
                phase_name="PreProcessing",
                agent_role="System",
                event_type="phase_complete",
                content="预处理阶段完成",
            )

            # 人员招募
            chat_chain.make_recruitment()
            self._log_event(
                phase_name="Recruitment",
                agent_role="CHRO",
                event_type="phase_complete",
                content=f"角色招募完成: {list(chat_chain.chat_env.roster.agents)}",
            )

            # 执行链式阶段（核心多轮对话协作）
            for i, phase_item in enumerate(chat_chain.chain):
                phase_name = phase_item.get("phase", f"Phase_{i}")
                self._log_event(
                    phase_name=phase_name,
                    agent_role="System",
                    event_type="phase_start",
                    content=f"开始执行阶段: {phase_name}",
                    metadata=phase_item,
                )
                try:
                    chat_chain.execute_step(phase_item)
                    self._log_event(
                        phase_name=phase_name,
                        agent_role="System",
                        event_type="phase_complete",
                        content=f"阶段 {phase_name} 执行完成",
                    )
                except Exception as phase_error:
                    self._log_event(
                        phase_name=phase_name,
                        agent_role="System",
                        event_type="phase_error",
                        content=f"阶段 {phase_name} 执行失败: {phase_error}",
                        metadata={"traceback": traceback.format_exc()},
                    )
                    # 对单个阶段的错误进行容错，继续执行后续阶段
                    logger.warning(f"阶段 {phase_name} 执行失败，继续执行: {phase_error}")

            # 后处理（总结、Git 管理、日志归档）
            try:
                chat_chain.post_processing()
            except Exception as post_err:
                logger.warning(f"后处理阶段失败（不影响结果）: {post_err}")

            # ---- Step 3: 收集生成结果 ----
            software_path = chat_chain.chat_env.env_dict.get("directory", "")
            self._current_software_path = software_path
            generated_code = self._collect_generated_code(software_path)

            self._log_event(
                phase_name="ResultCollection",
                agent_role="System",
                event_type="act_complete",
                content=f"任务完成，生成代码长度: {len(generated_code)} 字符",
                metadata={"software_path": software_path},
            )

            return ActionOutput(
                action_type=ActionType.CODE_GENERATION,
                action_content=generated_code,
                confidence=0.85,
                metadata={
                    "software_path": software_path,
                    "task_id": self._current_task_id,
                    "files": list(chat_chain.chat_env.codes.codebooks.keys())
                    if chat_chain.chat_env.codes.codebooks
                    else [],
                },
            )

        except Exception as e:
            # 分类底层异常
            adapter_error = self._classify_error(e)
            return self._handle_error(adapter_error)

    # ================================================================
    #  3. 内部轨迹导出
    # ================================================================

    def get_internal_logs(self) -> list[InternalLogEntry]:
        """
        导出本次任务的内部轨迹日志。

        返回适配器在执行 ``act()`` 过程中记录的所有内部事件，
        包括各阶段的开始/完成/错误事件。

        返回:
            list[InternalLogEntry]: 按时间顺序排列的日志条目列表
        """
        return list(self._internal_logs)

    # ================================================================
    #  内部辅助方法
    # ================================================================

    def _initialize_chat_chain(self, task_prompt: str, project_name: str):
        """
        初始化 ChatChain 实例。

        参数:
            task_prompt: 任务描述
            project_name: 项目名称

        返回:
            ChatChain 实例
        """
        from camel.typing import ModelType
        from chatdev.chat_chain import ChatChain

        # 获取配置文件路径
        config_path, config_phase_path, config_role_path = self._get_config_paths()

        # 解析模型类型
        model_type = self._resolve_model_type(self._model_name)

        # 创建 ChatChain
        chat_chain = ChatChain(
            config_path=config_path,
            config_phase_path=config_phase_path,
            config_role_path=config_role_path,
            task_prompt=task_prompt,
            project_name=project_name,
            org_name=self._org_name,
            model_type=model_type,
            code_path="",
        )

        self._chat_chain = chat_chain
        return chat_chain

    def _get_config_paths(self) -> tuple[str, str, str]:
        """
        获取 ChatDev 配置文件路径。

        返回:
            (config_path, config_phase_path, config_role_path)
        """
        config_dir = os.path.join(self._chatdev_root, "CompanyConfig", self._config_name)
        default_config_dir = os.path.join(self._chatdev_root, "CompanyConfig", "Default")

        config_files = [
            "ChatChainConfig.json",
            "PhaseConfig.json",
            "RoleConfig.json",
        ]

        config_paths = []
        for config_file in config_files:
            company_path = os.path.join(config_dir, config_file)
            default_path = os.path.join(default_config_dir, config_file)
            if os.path.exists(company_path):
                config_paths.append(company_path)
            else:
                config_paths.append(default_path)

        return tuple(config_paths)

    def _resolve_model_type(self, model_name: str):
        """
        将模型名称字符串解析为 ModelType 枚举值。

        支持 OpenAI 和 DeepSeek 模型名称。

        参数:
            model_name: 模型名称字符串

        返回:
            ModelType 枚举值
        """
        from camel.typing import ModelType

        # 标准模型名称映射
        name_to_type = {
            "GPT_3_5_TURBO": ModelType.GPT_3_5_TURBO,
            "GPT_3_5_TURBO_NEW": ModelType.GPT_3_5_TURBO_NEW,
            "GPT_4": ModelType.GPT_4,
            "GPT_4_32K": ModelType.GPT_4_32k,
            "GPT_4_TURBO": ModelType.GPT_4_TURBO,
            "GPT_4O": ModelType.GPT_4O,
            "GPT_4O_MINI": ModelType.GPT_4O_MINI,
        }

        # 尝试 DeepSeek 模型
        if model_name.upper().startswith("DEEPSEEK"):
            try:
                return ModelType[model_name.upper()]
            except KeyError:
                # 回退到默认模型
                logger.warning(
                    f"未知的 DeepSeek 模型: {model_name}，回退到 GPT_3_5_TURBO"
                )
                return ModelType.GPT_3_5_TURBO

        # 标准映射
        model_type = name_to_type.get(model_name.upper())
        if model_type is None:
            logger.warning(f"未知模型: {model_name}，回退到 GPT_3_5_TURBO")
            model_type = ModelType.GPT_3_5_TURBO

        # 检测是否需要使用 NEW API 版本
        try:
            from openai.types.chat.chat_completion_message_tool_call import (
                ChatCompletionMessageToolCall,
            )

            if model_type == ModelType.GPT_3_5_TURBO:
                model_type = ModelType.GPT_3_5_TURBO_NEW
        except ImportError:
            pass

        return model_type

    def _collect_generated_code(self, software_path: str) -> str:
        """
        从输出目录收集生成的代码文件内容。

        参数:
            software_path: 软件输出目录路径

        返回:
            str: 格式化的代码内容（包含文件名和代码块标记）
        """
        if not software_path or not os.path.exists(software_path):
            return ""

        code_content_parts = []
        try:
            for filename in sorted(os.listdir(software_path)):
                filepath = os.path.join(software_path, filename)
                if os.path.isfile(filepath) and filename.endswith(".py"):
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()
                    lang = "python"
                    code_content_parts.append(
                        f"{filename}\n```{lang}\n{code}\n```"
                    )
        except OSError as e:
            logger.error(f"读取生成代码失败: {e}")

        return "\n\n".join(code_content_parts)

    def _classify_error(self, error: Exception):
        """
        将底层异常分类为适配器标准异常。

        参数:
            error: 原始底层异常

        返回:
            AgentAdapterError 的子类实例
        """
        error_str = str(error).lower()

        # Token 超限检测
        if any(keyword in error_str for keyword in [
            "token", "max_tokens", "context_length", "context length"
        ]):
            return TokenLimitExceededError(
                message=f"Token 超限: {error}",
                original_error=error,
            )

        # 安全审查检测
        if any(keyword in error_str for keyword in [
            "content_policy", "safety", "filtered", "moderation",
            "content policy", "harmful"
        ]):
            return SafetyFilterTriggeredError(
                message=f"安全审查拦截: {error}",
                filter_reason=str(error),
                original_error=error,
            )

        # 其他归类为内部组件错误
        return InternalComponentError(
            message=f"ChatDev 内部错误: {type(error).__name__}: {error}",
            component_name="ChatChain",
            original_error=error,
        )
