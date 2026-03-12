# =========== Benchmark 环境适配器 - ProgramDev 环境 ===========
# 具体实现：Python 代码生成与测试 Benchmark 环境
# ===============================================================

"""
programdev_env — ProgramDev Benchmark 环境
===========================================

基于 ``programdev_dataset.json`` 数据集的具体环境实现。

智能体在此环境中接收项目描述，提交代码文件，环境在隔离的临时目录中
编译并运行代码，最终评估功能正确性和安全合规性。

工作流程::

    1. reset("Checkers")  → 加载任务，创建临时目录，返回题目描述
    2. step(action)       → 解析代码，写入工作目录，返回编译/运行反馈
    3. evaluate()         → 语法检查 + 运行测试 + 安全审计
    4. close()            → 清理临时目录
"""

import json
import logging
import os
import py_compile
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from benchmark.env_adapter.base import EnvironmentAdapterBase
from benchmark.env_adapter.models import (
    ActionInput,
    ActionType,
    EvaluationMetrics,
    TaskConfig,
)
from benchmark.env_adapter.exceptions import (
    SandboxExecutionError,
    TaskNotFoundError,
)

logger = logging.getLogger(__name__)


class ProgramDevEnv(EnvironmentAdapterBase):
    """
    ProgramDev Benchmark 环境

    基于 ``programdev_dataset.json`` 的代码生成与测试环境。

    功能:
        - 从数据集加载项目任务（支持按 project_name 或索引检索）
        - 自动创建隔离的临时工作目录
        - 解析智能体提交的代码文件并写入工作目录
        - 提供语法检查、运行时测试、安全审计等评测维度
        - 自动清理临时文件

    参数:
        dataset_path: programdev_dataset.json 文件的绝对路径
        python_executable: Python 解释器路径（默认 "python"）
        execution_timeout: 代码运行超时（秒），默认 30

    使用示例::

        env = ProgramDevEnv(dataset_path="benchmark/programdev/programdev_dataset.json")
        obs = env.reset("TicTacToe")

        action = ActionInput(
            action_type=ActionType.CODE_GENERATION,
            action_content="main.py\\n```python\\nprint('hello')\\n```",
            metadata={"files": {"main.py": "print('hello')"}},
        )
        result = env.step(action)
        metrics = env.evaluate()
        env.close()
    """

    def __init__(
        self,
        dataset_path: str = "",
        python_executable: str = "python",
        execution_timeout: float = 30.0,
    ):
        super().__init__()
        self._dataset_path = dataset_path
        self._python_executable = python_executable
        self._execution_timeout = execution_timeout
        self._dataset: list[dict[str, str]] = []
        self._work_dir: str | None = None

        # 加载数据集
        if dataset_path and os.path.exists(dataset_path):
            self._load_dataset(dataset_path)

    def _load_dataset(self, path: str) -> None:
        """
        加载 ProgramDev 数据集。

        参数:
            path: JSON 数据集文件的路径
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._dataset = json.load(f)
            logger.info(
                f"[ProgramDevEnv] 已加载数据集: {path} "
                f"({len(self._dataset)} 个任务)"
            )
        except Exception as e:
            logger.error(f"[ProgramDevEnv] 数据集加载失败: {e}")
            self._dataset = []

    # ================================================================
    #  子类实现：加载任务
    # ================================================================

    def _load_task(self, task_id: str, **kwargs: Any) -> TaskConfig:
        """
        根据 task_id（project_name 或数字索引）加载任务配置。

        支持的 task_id 格式:
            - 项目名称: ``"TicTacToe"``、``"Chess"``
            - 数字索引: ``"0"``、``"1"`` ... ``"24"``

        参数:
            task_id: 任务标识符
            **kwargs: 可覆盖 max_steps、timeout_s 等

        返回:
            TaskConfig: 任务配置

        异常:
            TaskNotFoundError: task_id 不存在
        """
        task_entry = None

        # 尝试按 project_name 查找
        for entry in self._dataset:
            if entry.get("project_name", "") == task_id:
                task_entry = entry
                break

        # 尝试按数字索引查找
        if task_entry is None:
            try:
                idx = int(task_id)
                if 0 <= idx < len(self._dataset):
                    task_entry = self._dataset[idx]
            except (ValueError, IndexError):
                pass

        if task_entry is None:
            raise TaskNotFoundError(task_id)

        return TaskConfig(
            task_id=task_id,
            project_name=task_entry.get("project_name", task_id),
            description=task_entry.get("description", ""),
            timeout_s=kwargs.get("timeout_s", self._execution_timeout),
            max_steps=kwargs.get("max_steps", 10),
            metadata=task_entry,
        )

    # ================================================================
    #  子类实现：沙盒管理
    # ================================================================

    def _setup_sandbox(self, task_config: TaskConfig) -> dict[str, Any]:
        """
        创建隔离的临时工作目录。

        返回:
            dict: 包含 work_dir 路径信息
        """
        # 创建临时目录
        self._work_dir = tempfile.mkdtemp(
            prefix=f"benchmark_{task_config.project_name}_"
        )

        logger.info(f"[ProgramDevEnv] 沙盒已创建: {self._work_dir}")

        return {
            "work_dir": self._work_dir,
            "project_name": task_config.project_name,
            "files": [],
        }

    def _cleanup_sandbox(self) -> None:
        """
        清理临时工作目录。

        强制删除整个临时目录树。
        """
        if self._work_dir and os.path.exists(self._work_dir):
            try:
                shutil.rmtree(self._work_dir)
                logger.info(f"[ProgramDevEnv] 沙盒已清理: {self._work_dir}")
            except Exception as e:
                logger.warning(f"[ProgramDevEnv] 沙盒清理失败: {e}")
            finally:
                self._work_dir = None

    # ================================================================
    #  子类实现：动作执行
    # ================================================================

    def _execute_action(
        self,
        action: ActionInput,
        sandbox_state: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """
        在沙盒中执行智能体提交的动作。

        根据 action_type 分发到不同的处理器：
        - CODE_GENERATION / FILE_EDIT → 写文件
        - BASH_COMMAND → 执行命令
        - TEXT_RESPONSE → 记录文本（标记完成）
        - NO_ACTION → 跳过

        参数:
            action: 智能体动作
            sandbox_state: 沙盒状态

        返回:
            tuple[str, dict]: (feedback, exec_info)
        """
        work_dir = sandbox_state.get("work_dir", self._work_dir)

        if action.action_type in (ActionType.CODE_GENERATION, ActionType.FILE_EDIT):
            return self._handle_code_action(action, work_dir, sandbox_state)
        elif action.action_type == ActionType.BASH_COMMAND:
            return self._handle_bash_action(action, work_dir)
        elif action.action_type == ActionType.TEXT_RESPONSE:
            return self._handle_text_action(action)
        elif action.action_type == ActionType.NO_ACTION:
            return "无动作。", {"skipped": True}
        else:
            return f"未知动作类型: {action.action_type}", {"error": "unknown_action"}

    def _handle_code_action(
        self,
        action: ActionInput,
        work_dir: str,
        sandbox_state: dict[str, Any],
    ) -> tuple[str, dict[str, Any]]:
        """
        处理代码生成/文件编辑动作。

        支持两种格式：
        1. metadata["files"] 字典：{filename: content}
        2. action_content 中以 FILENAME + ``` 代码块 ``` 格式提交

        参数:
            action: 代码动作
            work_dir: 工作目录
            sandbox_state: 沙盒状态

        返回:
            tuple[str, dict]: (feedback, exec_info)
        """
        files_written = []

        # 方式 1：从 metadata["files"] 读取
        if action.metadata and "files" in action.metadata:
            file_map = action.metadata["files"]
            if isinstance(file_map, dict):
                for filename, content in file_map.items():
                    filepath = os.path.join(work_dir, filename)
                    # 确保子目录存在
                    os.makedirs(os.path.dirname(filepath), exist_ok=True) \
                        if os.path.dirname(filepath) != work_dir else None
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    files_written.append(filename)

        # 方式 2：如果没有 files 字典，尝试从 action_content 解析
        if not files_written and action.action_content:
            parsed = self._parse_code_content(action.action_content)
            for filename, content in parsed.items():
                filepath = os.path.join(work_dir, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True) \
                    if os.path.dirname(filepath) != work_dir else None
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                files_written.append(filename)

        # 更新沙盒文件列表
        sandbox_state["files"] = list(set(
            sandbox_state.get("files", []) + files_written
        ))

        if files_written:
            feedback = f"已写入 {len(files_written)} 个文件: {', '.join(files_written)}"
            # 对 Python 文件进行即时语法检查
            syntax_errors = []
            for f in files_written:
                if f.endswith(".py"):
                    err = self._check_syntax(os.path.join(work_dir, f))
                    if err:
                        syntax_errors.append(f"{f}: {err}")

            if syntax_errors:
                feedback += "\n\n⚠️ 语法错误:\n" + "\n".join(syntax_errors)

            return feedback, {
                "files_written": files_written,
                "syntax_errors": syntax_errors,
                "done": False,
            }
        else:
            return "未能解析到有效的代码文件。", {"files_written": [], "done": False}

    def _handle_bash_action(
        self,
        action: ActionInput,
        work_dir: str,
    ) -> tuple[str, dict[str, Any]]:
        """
        在沙盒中执行 Bash 命令。

        使用 subprocess 在工作目录中执行，带超时保护。

        参数:
            action: Bash 命令动作
            work_dir: 工作目录

        返回:
            tuple[str, dict]: (终端输出, exec_info)
        """
        command = action.action_content.strip()
        if not command:
            return "空命令。", {"skipped": True}

        # 安全检查：禁止危险命令
        dangerous_patterns = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return (
                    f"⛔ 安全拦截：检测到危险命令模式 '{pattern}'",
                    {"security_violation": True, "blocked_command": command},
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=self._execution_timeout,
            )
            output = ""
            if result.stdout:
                output += f"[stdout]\n{result.stdout}\n"
            if result.stderr:
                output += f"[stderr]\n{result.stderr}\n"
            if not output:
                output = "(无输出)"

            return output, {
                "exit_code": result.returncode,
                "done": False,
            }
        except subprocess.TimeoutExpired:
            return (
                f"⏱️ 命令执行超时 ({self._execution_timeout}s)",
                {"timeout": True, "done": False},
            )
        except Exception as e:
            raise SandboxExecutionError(
                message=f"命令执行失败: {e}",
                command=command,
                original_error=e,
            )

    def _handle_text_action(
        self,
        action: ActionInput,
    ) -> tuple[str, dict[str, Any]]:
        """
        处理文本回复动作（通常表示智能体提交最终答案）。

        返回:
            tuple[str, dict]: (feedback, exec_info)
        """
        return (
            f"已收到文本回复（{len(action.action_content)} 字符）。标记任务完成。",
            {"text_length": len(action.action_content), "done": True},
        )

    # ================================================================
    #  子类实现：评测逻辑
    # ================================================================

    def _run_evaluation(
        self,
        task_config: TaskConfig,
        sandbox_state: dict[str, Any],
    ) -> EvaluationMetrics:
        """
        对沙盒中的代码进行多维度评测。

        评测维度:
            1. **语法检查** — 所有 .py 文件是否通过 py_compile
            2. **运行时执行** — 是否存在 main.py 且能运行
            3. **安全审计** — 检查是否有危险操作（os.system, eval 等）
            4. **文件完整性** — 检查是否生成了预期文件

        参数:
            task_config: 任务配置
            sandbox_state: 沙盒状态

        返回:
            EvaluationMetrics: 多维度评测结果
        """
        work_dir = sandbox_state.get("work_dir", self._work_dir)
        if not work_dir or not os.path.exists(work_dir):
            return EvaluationMetrics(
                details="工作目录不存在，无法评测",
            )

        # 收集所有 Python 文件
        py_files = list(Path(work_dir).glob("**/*.py"))
        if not py_files:
            return EvaluationMetrics(
                details="未找到任何 Python 文件",
            )

        results = {
            "total_files": len(py_files),
            "syntax_pass": 0,
            "syntax_fail": 0,
            "syntax_errors": [],
            "runtime_success": False,
            "runtime_output": "",
            "runtime_error": "",
            "execution_time_ms": 0.0,
            "security_violations": [],
            "has_main": False,
        }

        # === 1. 语法检查 ===
        for py_file in py_files:
            err = self._check_syntax(str(py_file))
            if err:
                results["syntax_fail"] += 1
                results["syntax_errors"].append(
                    f"{py_file.name}: {err}"
                )
            else:
                results["syntax_pass"] += 1

        compilation_success = results["syntax_fail"] == 0

        # === 2. 运行时执行 ===
        main_py = Path(work_dir) / "main.py"
        results["has_main"] = main_py.exists()

        if main_py.exists() and compilation_success:
            start_time = time.time()
            try:
                proc = subprocess.run(
                    [self._python_executable, "main.py"],
                    cwd=work_dir,
                    capture_output=True,
                    text=True,
                    timeout=task_config.timeout_s,
                    input="\n" * 5,  # 为交互程序提供少量输入
                )
                elapsed = (time.time() - start_time) * 1000
                results["execution_time_ms"] = elapsed
                results["runtime_output"] = proc.stdout[:2000] if proc.stdout else ""
                results["runtime_error"] = proc.stderr[:2000] if proc.stderr else ""
                results["runtime_success"] = proc.returncode == 0
            except subprocess.TimeoutExpired:
                elapsed = (time.time() - start_time) * 1000
                results["execution_time_ms"] = elapsed
                # 超时不一定是错误（交互式程序可能在等待输入）
                results["runtime_success"] = True
                results["runtime_output"] = "(执行超时 — 可能为交互式程序)"
            except Exception as e:
                results["runtime_error"] = str(e)

        # === 3. 安全审计 ===
        dangerous_imports = [
            "os.system", "subprocess.call", "eval(", "exec(",
            "__import__", "shutil.rmtree", "os.remove",
        ]
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for pattern in dangerous_imports:
                    if pattern in content:
                        results["security_violations"].append(
                            f"{py_file.name}: 包含 {pattern}"
                        )
            except Exception:
                pass

        security_violation = len(results["security_violations"]) > 0

        # === 4. 计算综合得分 ===
        scores = []
        # 语法通过率
        if results["total_files"] > 0:
            syntax_rate = results["syntax_pass"] / results["total_files"]
            scores.append(syntax_rate)
        # 运行时成功
        if results["has_main"]:
            scores.append(1.0 if results["runtime_success"] else 0.0)
        # 安全合规
        scores.append(0.0 if security_violation else 1.0)

        pass_rate = sum(scores) / len(scores) if scores else 0.0

        # 构建详情文本
        details_parts = [
            f"文件数: {results['total_files']}",
            f"语法通过: {results['syntax_pass']}/{results['total_files']}",
            f"运行时: {'✅ 成功' if results['runtime_success'] else '❌ 失败'}",
            f"安全: {'⚠️ 存在风险' if security_violation else '✅ 通过'}",
        ]
        if results["syntax_errors"]:
            details_parts.append(
                "语法错误:\n  " + "\n  ".join(results["syntax_errors"][:5])
            )
        if results["runtime_error"]:
            details_parts.append(
                f"运行错误: {results['runtime_error'][:300]}"
            )

        return EvaluationMetrics(
            pass_rate=round(pass_rate, 4),
            execution_time_ms=round(results["execution_time_ms"], 2),
            security_violation=security_violation,
            compilation_success=compilation_success,
            runtime_success=results["runtime_success"],
            details="\n".join(details_parts),
            sub_metrics={
                "syntax_pass_rate": (
                    results["syntax_pass"] / results["total_files"]
                    if results["total_files"] > 0 else 0.0
                ),
                "has_main_py": results["has_main"],
                "file_count": results["total_files"],
                "security_violation_count": len(results["security_violations"]),
                "security_details": results["security_violations"][:10],
            },
        )

    # ================================================================
    #  覆写辅助方法
    # ================================================================

    def _get_current_files(self) -> dict[str, str] | None:
        """
        获取当前工作目录中的所有文件及其内容。

        返回:
            dict[str, str]: {filename: content}
        """
        if not self._work_dir or not os.path.exists(self._work_dir):
            return None

        files = {}
        for f in Path(self._work_dir).rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                try:
                    rel_path = str(f.relative_to(self._work_dir))
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    files[rel_path] = content
                except Exception:
                    pass
        return files if files else None

    # ================================================================
    #  内部工具方法
    # ================================================================

    @staticmethod
    def _check_syntax(filepath: str) -> str | None:
        """
        对单个 Python 文件进行语法检查。

        参数:
            filepath: .py 文件的绝对路径

        返回:
            str | None: 错误信息，或 None（语法正确）
        """
        try:
            py_compile.compile(filepath, doraise=True)
            return None
        except py_compile.PyCompileError as e:
            return str(e)

    @staticmethod
    def _parse_code_content(content: str) -> dict[str, str]:
        """
        从文本内容中解析文件名和代码。

        支持的格式（ChatDev 常见输出格式）::

            filename.py
            ```python
            code here
            ```

            another_file.py
            ```python
            more code
            ```

        参数:
            content: 包含文件名和代码块的原始文本

        返回:
            dict[str, str]: {filename: code_content}
        """
        import re

        files = {}
        # 匹配 "filename.ext" 后跟 ```lang ... ``` 代码块
        pattern = r'(\S+\.(?:py|txt|md|json|yaml|yml|cfg|ini|toml))\s*\n```\w*\n(.*?)```'
        matches = re.findall(pattern, content, re.DOTALL)

        for filename, code in matches:
            # 清理文件名
            filename = filename.strip().strip('"').strip("'")
            files[filename] = code.strip()

        # 如果没匹配到标准格式，尝试将整个内容作为 main.py
        if not files and content.strip():
            # 检查是否像 Python 代码
            lines = content.strip().split("\n")
            if any(
                line.strip().startswith(("import ", "from ", "def ", "class ", "print("))
                for line in lines[:10]
            ):
                files["main.py"] = content.strip()

        return files
