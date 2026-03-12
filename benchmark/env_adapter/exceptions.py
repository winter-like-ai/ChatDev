# =========== Benchmark 环境适配器 - 异常层次 ===========
# 定义环境端的标准化异常类型
# ======================================================

"""
exceptions — Benchmark 环境端异常层次
=====================================

定义 ``EnvironmentAdapterBase`` 及其子类可能抛出的标准化异常。
所有异常均继承自 ``BenchmarkEnvironmentError`` 基类，
便于上层调用方统一捕获和分类处理。
"""


class BenchmarkEnvironmentError(Exception):
    """
    所有 Benchmark 环境适配器异常的基类。

    属性:
        message: 错误描述信息
        original_error: 原始底层异常（可选），便于调试追溯
    """

    def __init__(self, message: str = "", original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

    def __str__(self) -> str:
        base = f"[BenchmarkEnvironmentError] {self.message}"
        if self.original_error:
            base += f" | 原始错误: {type(self.original_error).__name__}: {self.original_error}"
        return base


class SandboxExecutionError(BenchmarkEnvironmentError):
    """
    沙盒执行失败

    当环境在隔离沙盒中执行智能体提交的代码/命令时发生错误（如超时、
    权限不足、资源限制等）时抛出。

    属性:
        command: 尝试执行的命令或代码片段
        exit_code: 进程退出码（可选）
        stderr: 标准错误输出（可选）
    """

    def __init__(
        self,
        message: str = "沙盒执行失败",
        command: str = "",
        exit_code: int | None = None,
        stderr: str = "",
        original_error: Exception | None = None,
    ):
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr
        super().__init__(message, original_error)


class TaskNotFoundError(BenchmarkEnvironmentError):
    """
    任务 ID 不存在

    当调用 ``reset(task_id)`` 时，指定的 task_id 在数据集中未找到。

    属性:
        task_id: 不存在的任务标识符
    """

    def __init__(self, task_id: str, message: str = ""):
        self.task_id = task_id
        if not message:
            message = f"任务 ID '{task_id}' 在数据集中不存在"
        super().__init__(message)


class EnvironmentNotResetError(BenchmarkEnvironmentError):
    """
    环境未初始化

    在调用 ``reset()`` 之前就尝试调用 ``step()`` 或 ``evaluate()`` 时抛出。
    """

    def __init__(self, message: str = ""):
        if not message:
            message = "环境尚未初始化，请先调用 reset(task_id) 方法"
        super().__init__(message)


class MaxStepsExceededError(BenchmarkEnvironmentError):
    """
    超出最大交互步数

    当智能体的交互步数超过任务配置的 ``max_steps`` 限制时抛出。

    属性:
        current_step: 当前步数
        max_steps: 最大允许步数
    """

    def __init__(self, current_step: int, max_steps: int, message: str = ""):
        self.current_step = current_step
        self.max_steps = max_steps
        if not message:
            message = f"已超出最大交互步数限制: {current_step}/{max_steps}"
        super().__init__(message)


class ResourceCleanupError(BenchmarkEnvironmentError):
    """
    资源清理失败

    在 ``close()`` / ``teardown()`` 过程中发生错误时抛出。
    例如：无法删除临时目录、Docker 容器停止失败等。

    属性:
        resource_type: 发生清理错误的资源类型描述
    """

    def __init__(
        self,
        resource_type: str = "unknown",
        message: str = "",
        original_error: Exception | None = None,
    ):
        self.resource_type = resource_type
        if not message:
            message = f"资源清理失败 (类型: {resource_type})"
        super().__init__(message, original_error)
