# =========== Benchmark 环境适配器 - 包初始化 ===========
# 导出所有公共 API
# ======================================================

"""
benchmark.env_adapter — Benchmark 环境适配器包
===============================================

提供标准化的 Gym 风格 Benchmark 环境接口，供外部评测引擎使用。

公共 API:

    基类与具体实现::

        from benchmark.env_adapter import EnvironmentAdapterBase, ProgramDevEnv

    数据模型::

        from benchmark.env_adapter import (
            ActionInput, ActionType, Observation, StepResult,
            EvaluationMetrics, TaskConfig,
        )

    异常::

        from benchmark.env_adapter import (
            BenchmarkEnvironmentError, SandboxExecutionError,
            TaskNotFoundError, EnvironmentNotResetError,
            MaxStepsExceededError, ResourceCleanupError,
        )
"""

# 数据模型
from benchmark.env_adapter.models import (
    ActionInput,
    ActionType,
    EvaluationMetrics,
    Observation,
    StepResult,
    TaskConfig,
)

# 异常
from benchmark.env_adapter.exceptions import (
    BenchmarkEnvironmentError,
    EnvironmentNotResetError,
    MaxStepsExceededError,
    ResourceCleanupError,
    SandboxExecutionError,
    TaskNotFoundError,
)

# 基类
from benchmark.env_adapter.base import EnvironmentAdapterBase

# 具体实现
from benchmark.env_adapter.programdev_env import ProgramDevEnv

__all__ = [
    # 基类
    "EnvironmentAdapterBase",
    # 具体实现
    "ProgramDevEnv",
    # 模型
    "ActionInput",
    "ActionType",
    "Observation",
    "StepResult",
    "EvaluationMetrics",
    "TaskConfig",
    # 异常
    "BenchmarkEnvironmentError",
    "SandboxExecutionError",
    "TaskNotFoundError",
    "EnvironmentNotResetError",
    "MaxStepsExceededError",
    "ResourceCleanupError",
]
