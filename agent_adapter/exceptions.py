# =========== Agent Adapter - 标准异常类型 ===========
# 定义适配器层的异常层次结构
# ===================================================

"""
exceptions — 标准化异常类型
==========================

定义适配器层的异常层次结构，用于将底层智能体系统的各类异常
统一转换为标准形式，避免评测进程崩溃。

异常层次::

    AgentAdapterError (基础异常)
    ├── TokenLimitExceededError    Token 超限
    ├── SafetyFilterTriggeredError 安全审查拦截
    ├── InternalComponentError     内部组件崩溃
    └── SessionNotInitializedError 未初始化会话
"""


class AgentAdapterError(Exception):
    """
    智能体适配器基础异常

    所有适配器相关的异常都应继承此类，
    便于 Benchmark 引擎统一捕获和处理。

    属性:
        message: 错误描述信息
        original_error: 原始底层异常（可选），用于调试追踪
    """

    def __init__(self, message: str = "智能体适配器发生未知错误",
                 original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        base = f"[AgentAdapterError] {self.message}"
        if self.original_error:
            base += f" | 原始错误: {type(self.original_error).__name__}: {self.original_error}"
        return base


class TokenLimitExceededError(AgentAdapterError):
    """
    Token 超限异常

    当底层模型调用因 Token 使用量超出上限而失败时抛出。
    通常是可恢复的（可尝试裁剪上下文后重试）。

    属性:
        token_used: 实际使用的 Token 数
        token_limit: 模型的 Token 上限
    """

    def __init__(self, message: str = "Token 使用量超出模型上限",
                 token_used: int = 0, token_limit: int = 0,
                 original_error: Exception | None = None):
        self.token_used = token_used
        self.token_limit = token_limit
        super().__init__(
            f"{message} (已用: {token_used}, 上限: {token_limit})",
            original_error
        )


class SafetyFilterTriggeredError(AgentAdapterError):
    """
    安全审查拦截异常

    当底层模型因内容安全策略（如 OpenAI Content Policy、
    DeepSeek 安全过滤等）拒绝处理请求时抛出。
    通常不可恢复（相同请求会被反复拦截）。

    属性:
        filter_reason: 触发过滤的原因描述
    """

    def __init__(self, message: str = "请求被安全审查策略拦截",
                 filter_reason: str = "",
                 original_error: Exception | None = None):
        self.filter_reason = filter_reason
        detail = f"{message} (原因: {filter_reason})" if filter_reason else message
        super().__init__(detail, original_error)


class InternalComponentError(AgentAdapterError):
    """
    内部组件崩溃异常

    当底层多智能体系统的某个内部组件（如某个 Phase 执行失败、
    RolePlaying 会话异常终止等）发生错误时抛出。

    属性:
        component_name: 发生故障的组件名称
    """

    def __init__(self, message: str = "底层系统内部组件发生错误",
                 component_name: str = "",
                 original_error: Exception | None = None):
        self.component_name = component_name
        detail = f"{message} (组件: {component_name})" if component_name else message
        super().__init__(detail, original_error)


class SessionNotInitializedError(AgentAdapterError):
    """
    未初始化会话异常

    当在未调用 ``reset_session()`` 的情况下直接调用 ``act()`` 时抛出。
    提醒调用方必须先初始化会话以确保任务间状态隔离。
    """

    def __init__(self, message: str = "请先调用 reset_session() 初始化会话后再调用 act()"):
        super().__init__(message)
