# Benchmark 环境端适配器 (Environment Adapter)

## 引言

本项目提供了一套标准化、高扩展性的 **Benchmark 环境适配器 (Environment Adapter)**，位于 `benchmark/env_adapter` 目录下。它的核心作用是作为一个交互式环境（类似 OpenAI Gym），接收外部智能体传入的动作 (Action)，在隔离的沙盒中推演状态，并最终对智能体的表现进行量化评估。

该设计与系统中的 `agent_adapter`（智能体端包装器）相对应，共同构成了 **Agent ↔ Environment** 之间的标准化双向通信协议。

## 目录结构

```text
benchmark/
├── __init__.py
├── README.md                 # 当前使用说明文档
├── env_adapter/              # 环境适配器核心框架
│   ├── __init__.py           # 公共 API 导出
│   ├── base.py               # 核心抽象基类 EnvironmentAdapterBase
│   ├── exceptions.py         # 标准化异常层次定义
│   ├── models.py             # Pydantic v2 标准化输入/输出数据模型
│   └── programdev_env.py     # 针对 "代码编写与执行" 所提供的具体环境实现
└── programdev/               # Benchmark 原始任务数据集
    └── programdev_dataset.json  # 25 个编程任务集
```

## 核心设计与接口规范

环境端适配器基于 `EnvironmentAdapterBase` 抽象基类实现，强制规范了四大生命周期接口（参考了强化学习中 Gym 环境的常见约定）：

### 1. 环境初始化与隔离 (`reset`)
* **签名**: `reset(task_id: str, **kwargs) -> Observation`
* **功能**: 接收一个特定的任务 ID，初始化该任务的测试环境，如在运行时准备初始代码库、搭建临时操作目录或沙盒环境等。
* **返回**: 包含智能体开始任务所需初始信息的 `Observation` 对象（内含 `instruction` 题目描述、初始状态等）。

### 2. 状态推演与动作执行 (`step` / `safe_step`)
* **签名**: `step(action: ActionInput) -> StepResult`
* **功能**: 接收外部智能体传入的标准动作（如生成代码、执行 Bash 命令），在内部沙盒中真正“执行”该操作，并反馈执行结果。
* **返回**: OpenAI Gym 风格的四大核心要素整合结构 `StepResult`：
  * `observation`: 执行动作后的新环境状态反馈（例如终端的报错输出、文件修改后的内容等）
  * `reward`: 即时奖励（如果不需进行强化学习反馈评估，则默认 `0.0`）
  * `done`: 是否满足评测结束条件（例如代码编写结束任务、产生不可逆错误、超步数）
  * `info`: 附加信息字典，用于给平台作记录参考。

### 3. 最终评测与打分 (`evaluate`)
* **签名**: `evaluate() -> EvaluationMetrics`
* **功能**: 当触发 `done=True` 并在任务回合结束后调用，通过该接口对比沙盒中得到的“终态结果”和“Ground Truth”，对智能体此次推演给出评价。
* **返回**: 细粒度、多维度的评测指标 `EvaluationMetrics`（包含测试的 `pass_rate`, 代码执行消耗时长 `execution_time_ms`, 是否包含高危安全隐患 `security_violation` 等项）。

### 4. 资源清理 (`close`)
* **签名**: `close() -> None`
* **功能**: 在当次流程彻底结束后安全地拆卸和销毁沙盒。强制移除临时生成的工作文件和环境系统资源，防止因为任务意外结束导致资源泄漏。适配器原生支持作为 Context Manager (`with` 语句) 运行来免去手动清理的烦恼。

## I/O 数据契约 (Pydantic Models)

所有的环境与智能体互操作必须遵循建立在 `models.py` 之上的验证约束规则（使用 Pydantic v2）：

- **ActionType**: 严格的动作类型枚举协议（与外部的 `agent_adapter` 完全平齐）。涵盖 `TEXT_RESPONSE`, `BASH_COMMAND`, `FILE_EDIT`, `CODE_GENERATION`, `NO_ACTION` 等。
- **ActionInput**: 智能体调用 `step()` 时传入入参。主要由动作类别及具体荷载(`action_content`)构成。
- **Observation**: 描述当前环境信息的视窗状态，包含全局题目 (`instruction`)、最后一句反馈报错内容 (`feedback`) 以及本地存储列表等。
- **StepResult**: 包裹着新的一层 Observation, reward 以及 done 进程标识符。
- **EvaluationMetrics**: 精细化返回评分体系字典约束结构。
- **TaskConfig**: 单个 Benchmark 任务加载及环境边界约束记录卡（记录步数边界与任务目标等）。

## 鲁棒异常处理体系 (Exceptions)

由于自动评测在沙盒中运转非常容易产生诸如死循环、编译器死锁等系统问题，框架内置了 `BenchmarkEnvironmentError` 基类以及多项细分类异：

- `TaskNotFoundError`: 请求测试任务不存在
- `SandboxExecutionError`: 环境中（比如 Bash / 编译阶段）发生彻底底层的运行异常
- `EnvironmentNotResetError`: 存在生命周期失序调用情况（如未 reset 就调用 step 工作）
- `MaxStepsExceededError`: 大量无效输出和来回死锁造成的交互轮次溢出
- `ResourceCleanupError`: 关闭清理资源无法安全释放

所有上述异常在直接使用底层 `safe_step()` 变体进行触发执行时都会被平滑捕获包装转成 `done=True` 的状态返回并反馈明确错误。

## 扩展使用指南: 如何新增属于你的 Benchmark

如果你打算建立针对如 “多模态理解推断评测” 的新 Benchmark，请按以下框架开发：

1. 继承核心框架 `EnvironmentAdapterBase`。
2. 实现 `_load_task(self, task_id, ...)`: 结合你的 JSON/DB 库加载验证题目与标答信息。
3. 实现 `_setup_sandbox(self, taskconfig)`: 用于准备你的计算物理路径或者 Docker 环境等初始资源占用声明。
4. 实现 `_execute_action(self, action, state)`: 解析传来的 Action（如文本提交或者代码编辑），修改状态信息并产生相应动作反馈内容回去。
5. 实现 `_run_evaluation(self, taskconf, state)`: 对最终留下的内容按你的标准输出结果计分。
6. 实现 `_cleanup_sandbox(self)`: 进行抹除重置。

具体可通读 `benchmark/env_adapter/programdev_env.py`，其中包含了一段从 Python 代码文件创建写入、到语法 AST 分析，乃至直接运行和排查危险挂载逻辑 (`eval`/`os.remove`) 的极佳实现用例。
