# =========== Agent Adapter for ChatDev Benchmark Integration ===========
# 智能体端适配器 - 将 ChatDev 多智能体系统封装为标准化 Benchmark 接口
# ======================================================================

"""
agent_adapter 包
================

本包提供了一套标准化、高扩展性的智能体端适配器接口，用于将任意复杂的底层智能体系统
（如 ChatDev 多角色软件开发框架）封装为统一形式，以便无缝对接外部自动化 Benchmark 引擎。

主要组件:
    - AgentAdapterBase: 抽象基类，定义适配器标准接口
    - ChatDevAdapter: ChatDev 具体适配器实现
    - ObservationInput / ActionOutput: Pydantic 数据模型，用于标准化输入输出
    - api_config: 统一 API 配置（支持 OpenAI / DeepSeek 自动回退）

使用示例::

    from agent_adapter import ChatDevAdapter, ObservationInput

    adapter = ChatDevAdapter(config="Default", model="DEEPSEEK_CHAT")
    adapter.reset_session(task_id="task_001")
    result = adapter.act(ObservationInput(instruction="开发一个贪吃蛇游戏"))
    print(result.action_type, result.action_content)
"""

from agent_adapter.models import (
    ObservationInput,
    ActionOutput,
    ActionType,
    ErrorType,
    ErrorResponse,
    InternalLogEntry,
)
from agent_adapter.exceptions import (
    AgentAdapterError,
    TokenLimitExceededError,
    SafetyFilterTriggeredError,
    InternalComponentError,
    SessionNotInitializedError,
)
from agent_adapter.base import AgentAdapterBase
from agent_adapter.chatdev_adapter import ChatDevAdapter
from agent_adapter.api_config import get_api_key, get_base_url, get_model_name

__all__ = [
    # 核心接口
    "AgentAdapterBase",
    "ChatDevAdapter",
    # 数据模型
    "ObservationInput",
    "ActionOutput",
    "ActionType",
    "ErrorType",
    "ErrorResponse",
    "InternalLogEntry",
    # 异常类型
    "AgentAdapterError",
    "TokenLimitExceededError",
    "SafetyFilterTriggeredError",
    "InternalComponentError",
    "SessionNotInitializedError",
    # API 配置
    "get_api_key",
    "get_base_url",
    "get_model_name",
]
