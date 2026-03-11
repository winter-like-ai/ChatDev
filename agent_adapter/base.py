# =========== Agent Adapter - 抽象基类 ===========
# 定义智能体适配器的标准化接口规范
# ================================================

"""
base — 智能体适配器抽象基类
===========================

定义 ``AgentAdapterBase`` 抽象基类，规范所有智能体适配器必须实现的四大接口:

1. **生命周期管理** — ``reset_session()``
2. **核心交互** — ``act()`` / ``aact()``
3. **内部轨迹导出** — ``get_internal_logs()``
4. **异常容错处理** — ``_handle_error()``（内建）

任何底层智能体系统（单体 LLM、多智能体框架等）只需继承此基类并实现
抽象方法，即可与 Benchmark 引擎对接。
"""

import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from agent_adapter.models import (
    ActionOutput,
    ActionType,
    ErrorResponse,
    ErrorType,
    InternalLogEntry,
    ObservationInput,
)
from agent_adapter.exceptions import (
    AgentAdapterError,
    InternalComponentError,
    SafetyFilterTriggeredError,
    SessionNotInitializedError,
    TokenLimitExceededError,
)

logger = logging.getLogger(__name__)


class AgentAdapterBase(ABC):
    """
    智能体适配器抽象基类

    作为黑盒包装器，将任意复杂的底层智能体系统封装为统一的标准形式，
    以便无缝对接外部的自动化 Benchmark 引擎。

    核心设计原则:
        - **状态隔离**: 每次 ``reset_session()`` 必须彻底清空所有内部状态
        - **黑盒封装**: ``act()`` 将底层所有内部交互封装为单次输入→单次输出
        - **容错健壮**: 底层异常不会导致 Benchmark 崩溃，而是返回标准化错误
        - **可审计性**: ``get_internal_logs()`` 支持安全对齐和效率分析

    子类必须实现:
        - ``reset_session(task_id, **kwargs)``
        - ``act(observation) -> ActionOutput``
        - ``get_internal_logs() -> list[InternalLogEntry]``

    使用示例::

        class MyAdapter(AgentAdapterBase):
            def reset_session(self, task_id, **kwargs):
                # 清空内部状态
                ...

            def act(self, observation):
                # 执行智能体逻辑，返回动作
                ...

            def get_internal_logs(self):
                return self._internal_logs
    """

    def __init__(self):
        """初始化适配器基础设施"""
        self._session_initialized: bool = False
        self._current_task_id: str | None = None
        self._internal_logs: list[InternalLogEntry] = []

    # ================================================================
    #  1. 生命周期管理接口 (Session & State Control)
    # ================================================================

    @abstractmethod
    def reset_session(self, task_id: str, **kwargs: Any) -> None:
        """
        重置会话状态，为新任务做准备。

        Benchmark 在每次评估新任务前会调用此接口。适配器必须在此方法中:
        1. 彻底清空底层智能体系统的历史上下文
        2. 清除内部 Agent 的记忆缓存
        3. 清理临时文件
        4. 重置所有状态变量

        以确保任务之间的 **绝对物理/逻辑隔离**，防止上下文污染。

        参数:
            task_id: Benchmark 分配的唯一任务标识符
            **kwargs: 可选的额外配置参数（如 model_override, timeout 等）

        注意:
            子类实现时必须在最后调用 ``super().reset_session(task_id, **kwargs)``
            以确保基础设施状态正确更新。
        """
        self._session_initialized = True
        self._current_task_id = task_id
        self._internal_logs.clear()
        logger.info(f"[AgentAdapter] 会话已重置，任务 ID: {task_id}")

    # ================================================================
    #  2. 核心交互接口 (Action Generation)
    # ================================================================

    @abstractmethod
    def act(self, observation: ObservationInput) -> ActionOutput:
        """
        根据观测生成动作（同步版本）。

        **核心接口**：接收标准化观测输入，返回标准化动作输出。

        解耦要求:
            底层多智能体系统的多轮内部对话、代码生成、自我审查等复杂过程，
            必须 **完全封装在此方法内部**。对外部 Benchmark 而言，
            只能看到一次输入对应一次最终的动作输出。

        参数:
            observation: 标准化观测输入，必须包含 instruction 字段

        返回:
            ActionOutput: 标准化动作输出

        异常:
            SessionNotInitializedError: 未调用 reset_session() 就调用 act()

        注意:
            子类应使用 ``safe_act()`` 包装器来自动获得异常捕获和容错能力，
            或在实现中手动调用 ``_handle_error()`` 处理异常。
        """
        pass

    async def aact(self, observation: ObservationInput) -> ActionOutput:
        """
        根据观测生成动作（异步版本）。

        默认实现将同步的 ``act()`` 方法在线程池中执行以避免阻塞事件循环。
        子类可覆写此方法提供真正的异步实现。

        参数:
            observation: 标准化观测输入

        返回:
            ActionOutput: 标准化动作输出
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.act, observation)

    def safe_act(self, observation: ObservationInput) -> ActionOutput:
        """
        带完整容错保护的动作生成包装器。

        自动处理:
        1. 会话初始化检查
        2. 输入验证
        3. 底层异常捕获与标准化错误输出

        参数:
            observation: 标准化观测输入

        返回:
            ActionOutput: 正常情况返回实际动作，异常情况返回标准化错误动作

        注意:
            此方法 **永远不会抛出异常**，所有错误都被转换为
            ``ActionType.NO_ACTION`` 的标准输出。
        """
        # 检查会话是否已初始化
        if not self._session_initialized:
            return self._handle_error(
                SessionNotInitializedError()
            )

        try:
            # 执行实际的 act 逻辑
            result = self.act(observation)
            return result
        except AgentAdapterError as e:
            logger.error(f"[AgentAdapter] 适配器异常: {e}")
            return self._handle_error(e)
        except Exception as e:
            logger.error(f"[AgentAdapter] 未预期的底层异常: {e}")
            logger.error(traceback.format_exc())
            wrapped = InternalComponentError(
                message=f"底层系统发生未预期错误: {type(e).__name__}: {str(e)}",
                component_name="unknown",
                original_error=e
            )
            return self._handle_error(wrapped)

    # ================================================================
    #  3. 内部轨迹与对齐日志 (Trajectory & Alignment Auditing)
    # ================================================================

    @abstractmethod
    def get_internal_logs(self) -> list[InternalLogEntry]:
        """
        导出内部轨迹日志。

        为便于后续针对安全对齐和智能体协作效率进行分析，
        返回底层系统在生成最终 action 时产生的内部数据:
        - 内部思考过程
        - 中间通讯记录
        - 阶段性决策结论
        - 拦截/审查日志

        这些数据 **不参与 Benchmark 的核心步骤推进**。

        返回:
            list[InternalLogEntry]: 内部日志条目列表，按时间顺序排列
        """
        pass

    # ================================================================
    #  4. 异常与容错处理 (Robustness)
    # ================================================================

    def _handle_error(self, error: AgentAdapterError) -> ActionOutput:
        """
        统一异常处理：将适配器异常转换为标准化的无动作输出。

        当底层系统因超出 Token 限制、触发安全审查墙或内部组件崩溃时，
        此方法将异常信息封装为标准化的 ``ActionOutput``，
        而不是直接导致评测进程崩溃。

        参数:
            error: 捕获到的适配器层异常

        返回:
            ActionOutput: action_type 为 NO_ACTION 的标准化错误输出
        """
        # 根据异常类型确定 ErrorType
        if isinstance(error, TokenLimitExceededError):
            error_type = ErrorType.TOKEN_LIMIT_EXCEEDED
            is_recoverable = True
        elif isinstance(error, SafetyFilterTriggeredError):
            error_type = ErrorType.SAFETY_FILTER_TRIGGERED
            is_recoverable = False
        elif isinstance(error, SessionNotInitializedError):
            error_type = ErrorType.INTERNAL_ERROR
            is_recoverable = True
        elif isinstance(error, InternalComponentError):
            error_type = ErrorType.INTERNAL_ERROR
            is_recoverable = False
        else:
            error_type = ErrorType.UNKNOWN
            is_recoverable = False

        # 构建标准化错误响应
        error_response = ErrorResponse(
            error_code=type(error).__name__,
            error_message=str(error),
            error_type=error_type,
            is_recoverable=is_recoverable,
        )

        # 记录到内部日志
        self._log_event(
            phase_name="ErrorHandling",
            agent_role="System",
            event_type="error_caught",
            content=str(error),
            metadata=error_response.model_dump(),
        )

        logger.warning(
            f"[AgentAdapter] 已捕获异常并转换为标准错误输出: "
            f"{error_response.error_code} - {error_response.error_message}"
        )

        return ActionOutput(
            action_type=ActionType.NO_ACTION,
            action_content="",
            confidence=0.0,
            metadata={"error": error_response.model_dump()},
        )

    # ================================================================
    #  内部辅助方法
    # ================================================================

    def _log_event(
        self,
        phase_name: str,
        agent_role: str,
        event_type: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        追加一条内部日志条目。

        子类在执行底层逻辑时应调用此方法记录关键事件，
        以供后续通过 ``get_internal_logs()`` 导出。

        参数:
            phase_name: 所属阶段名称
            agent_role: 智能体角色
            event_type: 事件类型
            content: 事件内容
            metadata: 附加元数据（可选）
        """
        entry = InternalLogEntry(
            timestamp=datetime.now().isoformat(),
            phase_name=phase_name,
            agent_role=agent_role,
            event_type=event_type,
            content=content,
            metadata=metadata,
        )
        self._internal_logs.append(entry)

    def _check_session(self) -> None:
        """
        检查会话是否已初始化。

        如果未初始化则抛出 SessionNotInitializedError。
        子类可在 ``act()`` 开头调用此方法。
        """
        if not self._session_initialized:
            raise SessionNotInitializedError()

    @property
    def session_initialized(self) -> bool:
        """当前会话是否已初始化"""
        return self._session_initialized

    @property
    def current_task_id(self) -> str | None:
        """当前任务 ID"""
        return self._current_task_id
