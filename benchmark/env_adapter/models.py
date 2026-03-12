# =========== Benchmark 环境适配器 - Pydantic 数据模型 ===========
# 定义环境端的标准化输入/输出/评测结果数据结构
# ==============================================================

"""
models — Benchmark 环境端标准化数据模型
======================================

使用 Pydantic v2 定义 Benchmark 环境与智能体之间的数据契约。
所有模型均支持 JSON 序列化/反序列化和严格的字段校验。

本模块定义的模型与 ``agent_adapter.models`` 互补：
- ``agent_adapter`` 定义智能体 → Benchmark 的输出格式
- 本模块定义 Benchmark → 智能体的输入格式 及 环境内部数据结构
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ========================
# 复用 agent_adapter 中的 ActionType 枚举
# ========================
class ActionType(str, Enum):
    """
    动作类型枚举（与 agent_adapter.models.ActionType 保持一致）

    定义智能体可以向环境提交的所有动作类型。
    """
    TEXT_RESPONSE = "text_response"          # 纯文本回复
    BASH_COMMAND = "bash_command"            # Shell/Bash 命令
    FILE_EDIT = "file_edit"                  # 文件编辑操作
    CODE_GENERATION = "code_generation"      # 代码生成（多文件）
    NO_ACTION = "no_action"                  # 无动作（错误/超时/拒绝）


# ========================
# 输入模型：智能体 → 环境
# ========================
class ActionInput(BaseModel):
    """
    智能体传入环境的标准化动作

    在 ``step()`` 接口中由智能体提交，环境据此推演内部状态。

    属性:
        action_type: 动作类型枚举，标识本次动作的类别。
        action_content: 动作的具体内容（代码文本、Shell 命令、文件编辑等）。
        metadata: 扩展元数据（可选），例如文件名映射、执行参数等。

    示例::

        action = ActionInput(
            action_type=ActionType.CODE_GENERATION,
            action_content="# main.py\\nprint('hello')",
            metadata={"files": {"main.py": "print('hello')"}}
        )
    """
    action_type: ActionType = Field(
        ...,
        description="动作类型，标识智能体提交的动作类别"
    )
    action_content: str = Field(
        ...,
        description="动作的具体内容（代码/命令/文本等）"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="扩展元数据，如文件名映射、执行参数等"
    )


# ========================
# 输出模型：环境 → 智能体
# ========================
class Observation(BaseModel):
    """
    环境返回给智能体的标准化观测

    在 ``reset()`` 和 ``step()`` 中返回，包含智能体继续执行所需的信息。

    属性:
        instruction: 任务指令/题目描述（首次由 ``reset()`` 返回）。
        initial_state: 初始文件状态或环境快照（可选）。
        feedback: 上一步执行后的反馈信息（如终端输出、编译错误）。
        current_files: 当前工作目录中的文件列表及内容（可选）。
        step_count: 当前已执行的步数。
        metadata: 附加元数据（可选）。

    示例::

        obs = Observation(
            instruction="开发一个命令行版 2048 游戏",
            initial_state={"files": []},
            feedback="",
            step_count=0,
        )
    """
    instruction: str = Field(
        ...,
        description="任务指令/题目描述"
    )
    initial_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="初始文件状态或环境快照"
    )
    feedback: Optional[str] = Field(
        default=None,
        description="上一步执行后的反馈信息（终端输出、编译错误等）"
    )
    current_files: Optional[dict[str, str]] = Field(
        default=None,
        description="当前工作目录中的文件列表及内容 {filename: content}"
    )
    step_count: int = Field(
        default=0,
        ge=0,
        description="当前已执行的步数"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="附加元数据"
    )


class StepResult(BaseModel):
    """
    ``step()`` 方法的标准化返回值

    遵循 OpenAI Gym 风格的四元组设计：(observation, reward, done, info)。

    属性:
        observation: 执行动作后的新环境观测。
        reward: 即时奖励分数（不适用强化学习时默认为 0.0）。
        done: 布尔值，标识该任务是否结束。
        info: 附加信息字典，用于记录执行轨迹或内部状态。

    示例::

        result = StepResult(
            observation=Observation(instruction="...", feedback="执行成功"),
            reward=0.0,
            done=False,
            info={"files_written": ["main.py"]},
        )
    """
    observation: Observation = Field(
        ...,
        description="执行动作后的新环境观测"
    )
    reward: float = Field(
        default=0.0,
        description="即时奖励分数（不适用 RL 时默认 0.0）"
    )
    done: bool = Field(
        default=False,
        description="任务是否结束"
    )
    info: dict[str, Any] = Field(
        default_factory=dict,
        description="附加信息（执行轨迹、内部状态等）"
    )


# ========================
# 评测结果模型
# ========================
class EvaluationMetrics(BaseModel):
    """
    ``evaluate()`` 方法的标准化返回值

    包含多维度的量化评测指标。

    属性:
        pass_rate: 测试通过率（0.0 ~ 1.0）。
        execution_time_ms: 代码执行耗时（毫秒）。
        security_violation: 是否存在安全违规行为。
        compilation_success: 代码是否通过编译/语法检查。
        runtime_success: 代码是否成功运行（无异常退出）。
        details: 人类可读的评测详细说明。
        sub_metrics: 子维度指标字典（可选），用于细粒度分析。

    示例::

        metrics = EvaluationMetrics(
            pass_rate=0.85,
            execution_time_ms=120.5,
            security_violation=False,
            compilation_success=True,
            runtime_success=True,
            details="17/20 测试用例通过",
            sub_metrics={"code_quality": 0.9, "documentation": 0.7},
        )
    """
    pass_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="测试通过率（0.0 ~ 1.0）"
    )
    execution_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="代码执行耗时（毫秒）"
    )
    security_violation: bool = Field(
        default=False,
        description="是否存在安全违规行为"
    )
    compilation_success: bool = Field(
        default=False,
        description="代码是否通过编译/语法检查"
    )
    runtime_success: bool = Field(
        default=False,
        description="代码是否成功运行（无异常退出）"
    )
    details: str = Field(
        default="",
        description="人类可读的评测详细说明"
    )
    sub_metrics: Optional[dict[str, Any]] = Field(
        default=None,
        description="子维度指标字典，用于细粒度分析"
    )


# ========================
# 任务配置模型
# ========================
class TaskConfig(BaseModel):
    """
    任务配置

    描述单个 Benchmark 任务的完整配置信息。

    属性:
        task_id: 唯一任务标识符。
        project_name: 项目名称（对应 dataset 中的 project_name）。
        description: 任务描述文本。
        ground_truth: 标准答案/参考实现（可选）。
        test_cases: 测试用例列表（可选），每条为可执行的检查逻辑。
        timeout_s: 单步执行超时时间（秒），默认 30 秒。
        max_steps: 最大交互步数，超限自动结束。默认 10 步。
        metadata: 扩展配置参数（可选）。

    示例::

        config = TaskConfig(
            task_id="programdev_001",
            project_name="TicTacToe",
            description="Design a tic-tac-toe game...",
            timeout_s=60,
            max_steps=5,
        )
    """
    task_id: str = Field(
        ...,
        min_length=1,
        description="唯一任务标识符"
    )
    project_name: str = Field(
        default="",
        description="项目名称"
    )
    description: str = Field(
        ...,
        min_length=1,
        description="任务描述文本"
    )
    ground_truth: Optional[dict[str, Any]] = Field(
        default=None,
        description="标准答案/参考实现"
    )
    test_cases: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="测试用例列表，每条为可执行的检查逻辑"
    )
    timeout_s: float = Field(
        default=30.0,
        gt=0,
        description="单步执行超时时间（秒）"
    )
    max_steps: int = Field(
        default=10,
        gt=0,
        description="最大交互步数，超限自动结束"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="扩展配置参数"
    )
