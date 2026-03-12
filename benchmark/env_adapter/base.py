# =========== Benchmark 环境适配器 - 抽象基类 ===========
# 定义 Gym 风格的 Benchmark 环境标准化接口
# ======================================================

"""
base — Benchmark 环境适配器抽象基类
====================================

定义 ``EnvironmentAdapterBase`` 抽象基类，规范所有 Benchmark 环境必须实现的
四大核心接口：

1. **环境初始化与隔离** — ``reset(task_id) → Observation``
2. **状态推演与动作执行** — ``step(action) → StepResult``
3. **最终评测与打分** — ``evaluate() → EvaluationMetrics``
4. **资源清理** — ``close()``

遵循 OpenAI Gym 风格 API 设计，使得任何 Benchmark 任务类型（代码生成、
问答、数学推理等）都可以通过继承此基类来实现标准化接入。
"""

import logging
import traceback
from abc import ABC, abstractmethod
from typing import Any

from benchmark.env_adapter.models import (
    ActionInput,
    ActionType,
    EvaluationMetrics,
    Observation,
    StepResult,
    TaskConfig,
)
from benchmark.env_adapter.exceptions import (
    BenchmarkEnvironmentError,
    EnvironmentNotResetError,
    MaxStepsExceededError,
    ResourceCleanupError,
    SandboxExecutionError,
)

logger = logging.getLogger(__name__)


class EnvironmentAdapterBase(ABC):
    """
    Benchmark 环境适配器抽象基类

    作为交互式环境（类似 OpenAI Gym），接收外部智能体传入的动作，
    在隔离沙盒中推演状态，并最终对智能体表现进行量化评估。

    核心设计原则:
        - **沙盒隔离**: 每个任务在独立环境中执行，防止恶意代码逃逸
        - **步数限制**: ``max_steps`` 自动截断，防止无限循环
        - **GYM 风格**: ``reset()`` → ``step()`` → ``evaluate()`` → ``close()``
        - **容错保护**: ``safe_step()`` 不会因底层错误导致评测崩溃

    子类必须实现:
        - ``_load_task(task_id, **kwargs) → TaskConfig``
        - ``_setup_sandbox(task_config) → dict``
        - ``_execute_action(action, sandbox_state) → tuple[str, dict]``
        - ``_run_evaluation(task_config, sandbox_state) → EvaluationMetrics``
        - ``_cleanup_sandbox()``

    使用示例::

        with MyBenchmarkEnv(dataset_path="tasks.json") as env:
            obs = env.reset("task_001")
            done = False
            while not done:
                action = agent.act(obs)
                result = env.step(action)
                obs, done = result.observation, result.done
            metrics = env.evaluate()
            print(metrics.pass_rate)
    """

    def __init__(self):
        """初始化环境基础设施"""
        self._is_reset: bool = False
        self._current_task_config: TaskConfig | None = None
        self._step_count: int = 0
        self._sandbox_state: dict[str, Any] = {}
        self._done: bool = False
        self._action_history: list[ActionInput] = []
        self._execution_log: list[dict[str, Any]] = []

    # ================================================================
    #  上下文管理器支持
    # ================================================================

    def __enter__(self):
        """支持 ``with`` 语句"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出时自动清理资源"""
        try:
            self.close()
        except Exception as e:
            logger.warning(f"[BenchmarkEnv] 退出时清理资源失败: {e}")
        return False  # 不吞掉异常

    # ================================================================
    #  1. 环境初始化与隔离 (Environment Reset & Isolation)
    # ================================================================

    def reset(self, task_id: str, **kwargs: Any) -> Observation:
        """
        初始化任务的测试环境。

        Benchmark 引擎在评估每个新任务前调用此接口。环境必须：
        1. 加载指定 task_id 的任务配置（题目、测试用例等）
        2. 准备隔离的沙盒（临时目录 / Docker 容器等）
        3. 返回智能体开始任务所需的初始观测

        参数:
            task_id: Benchmark 任务的唯一标识符
            **kwargs: 可选的额外配置参数

        返回:
            Observation: 初始观测，包含 instruction 和 initial_state

        异常:
            TaskNotFoundError: 当 task_id 在数据集中不存在时
            BenchmarkEnvironmentError: 沙盒准备失败时
        """
        # 如果已有旧环境，先清理
        if self._is_reset:
            try:
                self._cleanup_sandbox()
            except Exception as e:
                logger.warning(f"[BenchmarkEnv] 重置前清理旧环境失败: {e}")

        # 重置内部状态
        self._step_count = 0
        self._done = False
        self._action_history.clear()
        self._execution_log.clear()
        self._sandbox_state.clear()

        # 1. 加载任务配置（子类实现）
        task_config = self._load_task(task_id, **kwargs)
        self._current_task_config = task_config

        # 2. 准备沙盒环境（子类实现）
        sandbox_info = self._setup_sandbox(task_config)
        self._sandbox_state.update(sandbox_info)

        # 3. 标记已初始化
        self._is_reset = True

        logger.info(
            f"[BenchmarkEnv] 环境已重置 | task_id={task_id} "
            f"| project={task_config.project_name} "
            f"| max_steps={task_config.max_steps}"
        )

        # 4. 构造并返回初始观测
        return Observation(
            instruction=task_config.description,
            initial_state=sandbox_info,
            feedback="环境已就绪，请开始执行任务。",
            step_count=0,
            metadata={
                "task_id": task_id,
                "project_name": task_config.project_name,
                "max_steps": task_config.max_steps,
                "timeout_s": task_config.timeout_s,
            },
        )

    # ================================================================
    #  2. 状态推演与动作执行 (Environment Step)
    # ================================================================

    def step(self, action: ActionInput) -> StepResult:
        """
        执行智能体提交的动作，推演环境状态。

        接收一个标准化动作并在内部沙盒中实际执行，返回 Gym 风格的
        四元组 (observation, reward, done, info)。

        参数:
            action: 智能体提交的标准化动作

        返回:
            StepResult: (observation, reward, done, info)

        异常:
            EnvironmentNotResetError: 未调用 reset() 就调用 step()
            MaxStepsExceededError: 超出最大交互步数
        """
        # 检查环境是否已初始化
        self._check_env()

        # 检查是否已结束
        if self._done:
            return StepResult(
                observation=Observation(
                    instruction=self._current_task_config.description,
                    feedback="任务已结束，无法继续执行。请调用 evaluate() 获取评测结果。",
                    step_count=self._step_count,
                ),
                reward=0.0,
                done=True,
                info={"reason": "task_already_done"},
            )

        # 检查步数限制
        if self._step_count >= self._current_task_config.max_steps:
            self._done = True
            raise MaxStepsExceededError(
                current_step=self._step_count,
                max_steps=self._current_task_config.max_steps,
            )

        # 记录动作
        self._step_count += 1
        self._action_history.append(action)

        # 执行动作（子类实现）
        feedback, exec_info = self._execute_action(action, self._sandbox_state)

        # 记录执行日志
        self._execution_log.append({
            "step": self._step_count,
            "action_type": action.action_type.value,
            "feedback_preview": feedback[:200] if feedback else "",
            "exec_info": exec_info,
        })

        # 检查是否因动作触发结束条件
        if exec_info.get("done", False):
            self._done = True

        # 再次检查步数限制（执行后）
        if self._step_count >= self._current_task_config.max_steps:
            self._done = True

        # 获取当前文件状态
        current_files = self._get_current_files()

        # 构造观测
        observation = Observation(
            instruction=self._current_task_config.description,
            feedback=feedback,
            current_files=current_files,
            step_count=self._step_count,
            metadata={
                "steps_remaining": max(
                    0,
                    self._current_task_config.max_steps - self._step_count
                ),
            },
        )

        return StepResult(
            observation=observation,
            reward=exec_info.get("reward", 0.0),
            done=self._done,
            info=exec_info,
        )

    def safe_step(self, action: ActionInput) -> StepResult:
        """
        带完整容错保护的 ``step()`` 包装器。

        自动处理：
        1. 环境初始化检查
        2. 沙盒执行异常捕获
        3. 步数超限处理
        4. 所有错误转换为标准化 StepResult（done=True + info 含错误详情）

        参数:
            action: 智能体提交的标准化动作

        返回:
            StepResult: 正常或错误情况下均返回有效的 StepResult

        注意:
            此方法 **永远不会抛出异常**。
        """
        try:
            return self.step(action)
        except EnvironmentNotResetError as e:
            logger.error(f"[BenchmarkEnv] 环境未初始化: {e}")
            return StepResult(
                observation=Observation(
                    instruction="（环境未初始化）",
                    feedback=str(e),
                    step_count=0,
                ),
                reward=0.0,
                done=True,
                info={"error": str(e), "error_type": "environment_not_reset"},
            )
        except MaxStepsExceededError as e:
            logger.warning(f"[BenchmarkEnv] 步数超限: {e}")
            return StepResult(
                observation=Observation(
                    instruction=self._current_task_config.description
                        if self._current_task_config else "",
                    feedback=f"已达到最大步数限制 ({e.max_steps})",
                    step_count=e.current_step,
                ),
                reward=0.0,
                done=True,
                info={"error": str(e), "error_type": "max_steps_exceeded"},
            )
        except SandboxExecutionError as e:
            logger.error(f"[BenchmarkEnv] 沙盒执行错误: {e}")
            return StepResult(
                observation=Observation(
                    instruction=self._current_task_config.description
                        if self._current_task_config else "",
                    feedback=f"沙盒执行错误: {e.message}",
                    step_count=self._step_count,
                ),
                reward=0.0,
                done=False,  # 沙盒错误不一定需要终止
                info={
                    "error": str(e),
                    "error_type": "sandbox_execution_error",
                    "stderr": e.stderr,
                },
            )
        except Exception as e:
            logger.error(f"[BenchmarkEnv] 未预期异常: {e}")
            logger.error(traceback.format_exc())
            self._done = True
            return StepResult(
                observation=Observation(
                    instruction=self._current_task_config.description
                        if self._current_task_config else "",
                    feedback=f"内部错误: {type(e).__name__}: {e}",
                    step_count=self._step_count,
                ),
                reward=0.0,
                done=True,
                info={
                    "error": str(e),
                    "error_type": "internal_error",
                    "traceback": traceback.format_exc(),
                },
            )

    # ================================================================
    #  3. 最终评测与打分 (Evaluation & Metrics)
    # ================================================================

    def evaluate(self) -> EvaluationMetrics:
        """
        对智能体的最终表现进行量化评测。

        当 ``step()`` 返回 ``done=True`` 后调用。环境将对比沙盒中的
        最终状态与该任务的标准答案/测试用例，返回多维度评测指标。

        返回:
            EvaluationMetrics: 量化评测结果

        异常:
            EnvironmentNotResetError: 未调用 reset() 就调用 evaluate()
        """
        self._check_env()

        logger.info(
            f"[BenchmarkEnv] 开始评测 | task_id={self._current_task_config.task_id} "
            f"| 总步数={self._step_count}"
        )

        # 执行评测（子类实现）
        metrics = self._run_evaluation(
            self._current_task_config,
            self._sandbox_state,
        )

        logger.info(
            f"[BenchmarkEnv] 评测完成 | pass_rate={metrics.pass_rate:.2%} "
            f"| compilation={metrics.compilation_success} "
            f"| runtime={metrics.runtime_success}"
        )

        return metrics

    # ================================================================
    #  4. 资源清理 (Teardown)
    # ================================================================

    def close(self) -> None:
        """
        彻底清理环境资源。

        确保在单个任务评测结束或发生异常时：
        - 销毁所有临时文件
        - 关闭数据库连接
        - 强制结束 Docker 容器
        - 释放所有占用的系统资源

        此方法在以下场景被调用：
        - 显式调用 ``env.close()``
        - ``with`` 语句退出时
        - Benchmark 引擎结束时

        异常:
            ResourceCleanupError: 资源清理过程中发生错误
        """
        if not self._is_reset:
            return  # 无需清理

        try:
            self._cleanup_sandbox()
        except Exception as e:
            logger.error(f"[BenchmarkEnv] 资源清理失败: {e}")
            raise ResourceCleanupError(
                resource_type="sandbox",
                message=f"沙盒清理失败: {e}",
                original_error=e,
            ) from e
        finally:
            # 无论清理是否成功，都重置标志位
            self._is_reset = False
            self._current_task_config = None
            self._sandbox_state.clear()
            self._done = False
            self._step_count = 0

        logger.info("[BenchmarkEnv] 环境已关闭，资源已清理")

    # ================================================================
    #  抽象方法（子类必须实现）
    # ================================================================

    @abstractmethod
    def _load_task(self, task_id: str, **kwargs: Any) -> TaskConfig:
        """
        加载指定任务的配置信息。

        子类需根据 task_id 从数据集/数据库中检索任务配置，
        包括题目描述、测试用例、超时设置等。

        参数:
            task_id: 任务唯一标识符
            **kwargs: 额外配置参数

        返回:
            TaskConfig: 任务的完整配置

        异常:
            TaskNotFoundError: 当 task_id 不存在时
        """
        ...

    @abstractmethod
    def _setup_sandbox(self, task_config: TaskConfig) -> dict[str, Any]:
        """
        准备隔离的沙盒环境。

        根据任务配置创建隔离执行空间（如临时目录、Docker 容器），
        注入初始数据/文件/依赖等。

        参数:
            task_config: 任务配置

        返回:
            dict: 沙盒状态信息（如工作目录路径、容器 ID 等）
        """
        ...

    @abstractmethod
    def _execute_action(
        self,
        action: ActionInput,
        sandbox_state: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """
        在沙盒中执行智能体的动作。

        解析动作并在内部沙盒中实际执行（写文件、运行命令等）。

        参数:
            action: 智能体提交的动作
            sandbox_state: 当前沙盒状态

        返回:
            tuple[str, dict]:
                - feedback: 执行后的反馈文本（如终端输出、错误信息）
                - exec_info: 执行附加信息（可含 "done"=True 触发结束，
                  "reward" 即时奖励等）

        异常:
            SandboxExecutionError: 沙盒内执行失败
        """
        ...

    @abstractmethod
    def _run_evaluation(
        self,
        task_config: TaskConfig,
        sandbox_state: dict[str, Any],
    ) -> EvaluationMetrics:
        """
        执行最终评测逻辑。

        对比沙盒中的最终状态与标准答案/测试用例，生成多维度评测指标。

        参数:
            task_config: 任务配置（含 ground_truth 和 test_cases）
            sandbox_state: 当前沙盒状态

        返回:
            EvaluationMetrics: 量化评测结果
        """
        ...

    @abstractmethod
    def _cleanup_sandbox(self) -> None:
        """
        清理沙盒环境。

        销毁临时文件、关闭容器等。即使清理失败也不应抛出异常
        （由上层 ``close()`` 统一包装为 ``ResourceCleanupError``）。
        """
        ...

    # ================================================================
    #  辅助方法
    # ================================================================

    def _check_env(self) -> None:
        """
        检查环境是否已初始化。

        若未初始化则抛出 ``EnvironmentNotResetError``。
        """
        if not self._is_reset:
            raise EnvironmentNotResetError()

    def _get_current_files(self) -> dict[str, str] | None:
        """
        获取当前沙盒中的文件列表及内容。

        默认返回 None。子类可覆写以返回实际文件内容。

        返回:
            dict[str, str] | None: 文件名→内容映射，或 None
        """
        return None

    @property
    def is_reset(self) -> bool:
        """环境是否已初始化"""
        return self._is_reset

    @property
    def step_count(self) -> int:
        """当前已执行的步数"""
        return self._step_count

    @property
    def is_done(self) -> bool:
        """任务是否已结束"""
        return self._done

    @property
    def current_task_config(self) -> TaskConfig | None:
        """当前任务配置"""
        return self._current_task_config

    @property
    def action_history(self) -> list[ActionInput]:
        """历史动作列表"""
        return list(self._action_history)

    @property
    def execution_log(self) -> list[dict[str, Any]]:
        """执行日志"""
        return list(self._execution_log)
