# =========== Agent Adapter - Pydantic 数据模型 ===========
# 定义标准化的输入/输出/日志/错误数据结构
# ========================================================

"""
models — 标准化数据模型
======================

使用 Pydantic v2 定义 Benchmark 引擎与智能体适配器之间的数据契约。
所有模型均支持 JSON 序列化/反序列化和严格的字段校验。
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """
    动作类型枚举

    定义适配器可以返回给 Benchmark 引擎的所有动作类型。
    """
    TEXT_RESPONSE = "text_response"          # 纯文本回复
    BASH_COMMAND = "bash_command"            # Shell/Bash 命令
    FILE_EDIT = "file_edit"                  # 文件编辑操作
    CODE_GENERATION = "code_generation"      # 代码生成（多文件）
    NO_ACTION = "no_action"                  # 无动作（错误/超时/拒绝）


class ErrorType(str, Enum):
    """
    错误类型枚举

    标识底层系统产生错误的类别，便于 Benchmark 引擎分类统计。
    """
    TOKEN_LIMIT_EXCEEDED = "token_limit_exceeded"      # Token 超限
    SAFETY_FILTER_TRIGGERED = "safety_filter_triggered"  # 安全审查拦截
    INTERNAL_ERROR = "internal_error"                    # 内部组件崩溃
    TIMEOUT = "timeout"                                  # 超时
    UNKNOWN = "unknown"                                  # 未知错误


class ObservationInput(BaseModel):
    """
    标准化观测输入

    Benchmark 引擎在每个评估步骤中传递给适配器的标准化观测数据。

    属性:
        instruction: 当前指令/题目（必填）。Benchmark 向智能体下发的具体任务描述。
        context: 环境背景信息（可选）。包含任务的全局设定、约束条件等。
        history: 外部环境可见的历史交互记录（可选）。
                 每条记录为字典格式，至少包含 "role" 和 "content" 字段。
        metadata: 扩展元数据（可选）。用于传递 Benchmark 特定的附加参数，
                  如 task_id, difficulty, domain 等。

    示例::

        obs = ObservationInput(
            instruction="开发一个基于命令行的2048游戏",
            context="目标平台为 Python 3.10+",
            history=[
                {"role": "system", "content": "你是一个软件开发团队"},
                {"role": "user", "content": "请开始开发"}
            ],
            metadata={"task_id": "benchmark_001", "difficulty": "medium"}
        )
    """
    instruction: str = Field(
        ...,
        min_length=1,
        description="当前指令/题目，Benchmark 向智能体下发的具体任务描述"
    )
    context: Optional[str] = Field(
        default=None,
        description="环境背景信息，包含任务的全局设定、约束条件等"
    )
    history: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="外部环境可见的历史交互记录，每条至少含 'role' 和 'content'"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="扩展元数据，用于传递 Benchmark 特定的附加参数"
    )


class ActionOutput(BaseModel):
    """
    标准化动作输出

    适配器在处理完观测后返回给 Benchmark 引擎的标准化动作结果。
    底层多智能体系统的所有内部交互（多轮对话、代码审查、自测试等）
    均被封装在适配器内部，对外只暴露这一个最终输出。

    属性:
        action_type: 动作类型枚举，标识本次输出的动作类别。
        action_content: 具体动作内容（代码、命令、文本等）。
        confidence: 置信度分数（可选），范围 0.0～1.0。
        metadata: 扩展元数据（可选），可包含代码文件列表、执行耗时等。

    示例::

        output = ActionOutput(
            action_type=ActionType.CODE_GENERATION,
            action_content="main.py:\\n```python\\nprint('hello')\\n```",
            confidence=0.92,
            metadata={"files_generated": ["main.py"], "duration_s": 45.2}
        )
    """
    action_type: ActionType = Field(
        ...,
        description="动作类型，标识本次输出的动作类别"
    )
    action_content: str = Field(
        ...,
        description="具体动作内容（代码/命令/文本等）"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="置信度分数，范围 0.0～1.0"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="扩展元数据，可包含文件列表、耗时等附加信息"
    )


class ErrorResponse(BaseModel):
    """
    标准化错误响应

    当底层智能体系统遇到不可恢复或可恢复的错误时，
    适配器将错误信息封装为此结构，嵌入到 ActionOutput.metadata 中。

    属性:
        error_code: 错误编码（如 "E001", "TOKEN_OVERFLOW"）。
        error_message: 人类可读的错误描述信息。
        error_type: 错误类型枚举。
        is_recoverable: 该错误是否可恢复（重试可能成功）。

    示例::

        err = ErrorResponse(
            error_code="E001",
            error_message="Token 使用量超出模型上限 (16384)",
            error_type=ErrorType.TOKEN_LIMIT_EXCEEDED,
            is_recoverable=True
        )
    """
    error_code: str = Field(
        ...,
        description="错误编码，如 'E001', 'TOKEN_OVERFLOW'"
    )
    error_message: str = Field(
        ...,
        description="人类可读的错误描述信息"
    )
    error_type: ErrorType = Field(
        default=ErrorType.UNKNOWN,
        description="错误类型枚举"
    )
    is_recoverable: bool = Field(
        default=False,
        description="该错误是否可恢复（重试可能成功）"
    )


class InternalLogEntry(BaseModel):
    """
    内部轨迹日志条目

    记录底层智能体系统在生成最终 action 过程中的内部活动。
    这些日志用于安全对齐分析和智能体协作效率评估，
    不参与 Benchmark 的核心步骤推进。

    属性:
        timestamp: 事件发生的 ISO 格式时间戳。
        phase_name: 所属阶段名称（如 "Coding", "CodeReview"）。
        agent_role: 参与的智能体角色（如 "Programmer", "CTO"）。
        event_type: 事件类型（如 "chat_start", "chat_message", "seminar_conclusion"）。
        content: 事件内容（对话文本/决策结果/错误信息等）。
        metadata: 附加元数据（可选）。

    示例::

        log = InternalLogEntry(
            timestamp="2024-01-15T10:30:00",
            phase_name="CodeReview",
            agent_role="Code Reviewer",
            event_type="chat_message",
            content="建议将数据库连接改为连接池模式以提升性能",
            metadata={"turn": 3, "chat_turn_limit": 10}
        )
    """
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="事件发生的 ISO 格式时间戳"
    )
    phase_name: str = Field(
        ...,
        description="所属阶段名称，如 'Coding', 'CodeReview'"
    )
    agent_role: str = Field(
        ...,
        description="参与的智能体角色，如 'Programmer', 'CTO'"
    )
    event_type: str = Field(
        ...,
        description="事件类型，如 'chat_start', 'chat_message', 'seminar_conclusion'"
    )
    content: str = Field(
        ...,
        description="事件内容（对话文本/决策结果/错误信息等）"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="附加元数据"
    )
