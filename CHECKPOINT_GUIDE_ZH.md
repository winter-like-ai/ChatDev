# ChatDev Checkpoint 与回滚（Rollback）功能使用指南

本指南将介绍如何在 ChatDev 中生成任务检查点（Checkpoints），并通过回滚（Rollback）功能恢复之前的状态以继续生成，或在中断点修改指令（Prompt）进行深度优化。

## 🌟 功能简介

在 ChatDev 的标准运行流程中，任务会被拆散为多个不同的阶段（Phase），例如：`DemandAnalysis`（需求分析）→ `LanguageChoose`（语言选择）→ `Coding`（编码）→ `CodeCompleteAll` 等等。

**Checkpointing (检查点机制):** 
每当 ChatDev 准备进入下一个新的 Phase 时，系统会自动对当前完整的环境上下文（包含已生成的代码、对话记忆、角色环境等）进行序列化备份，保存在你的项目 `WareHouse` 输出目录中。 

**Rollback (回滚机制):**
当你对某一生成的软件不满意，或者因为网络波动导致意外中断时，你可以通过指定某个检查点的序号（或阶段名称），让 ChatDev 瞬间“穿越”回那个历史时刻。在回滚的同时，你还可以**修改原始的 Prompt 任务需求**，让智能体们从中断的地方，按照你的新要求重新接手工作！

## 📁 检查点在哪里？

当你使用 `python run.py` (或 `python run_benchmark.py`) 运行任务时，检查点数据会自动生成在你指定的项目结果文件夹内的一个 `checkpoints` 子目录中。

例如跑了这样一个任务：
```bash
python run.py --task "开发一个贪吃蛇游戏" --name "SnakeGame"
```
项目被结算存放到了 `WareHouse/SnakeGame_DefaultOrganization_2026xxxx` 文件夹下。
如果你点开这个文件夹，就会看到一个 `checkpoints` 目录：
```text
WareHouse/
└── SnakeGame_DefaultOrganization_2026xxxx/
    ├── main.py
    ├── game.py
    └── checkpoints/
        ├── phase_0.pkl  (进入阶段 0 之前的备份)
        ├── phase_1.pkl  (进入阶段 1 之前的备份)
        ├── phase_2.pkl  (进入阶段 2 之前的备份)
        └── ...
```
这里面保存的就是环境状态（以 `.pkl` 后缀结尾）。

---

## 🚀 如何使用回滚功能 (Rollback)

使用回滚功能，你需要在终端启动 `run.py` 时传入两个额外的核心参数：

1. `--project_path`：你需要回滚的任务输出目录的**相对或绝对路径**。
2. `--rollback_phase`：你想回滚到的阶段（可以是诸如 `0`, `3`, `5` 这样的**整数索引**，也可以是 `Coding` 这样的**阶段名称**）。

### 示例 1: 纯粹恢复意外中断的任务

假设你在第 3 阶段（或第三个 `.pkl` 文件处）不小心关掉了终端，你可以这样无缝恢复：

```bash
python run.py --project_path "WareHouse/SnakeGame_DefaultOrganization_2026xxxx" --rollback_phase 3
```
*ChatDev 会直接读取当时的环境，在磁盘中复原所有的代码文件原貌，然后直接跳过阶段 0~2，从阶段 3 开始继续执行后续任务链。*

### 示例 2: 中途优化/修改提示词 (Prompt Optimization)

如果你发现在第 5 阶段代码审查时生成的 UI 很丑，你希望回到最开始或者早些时候，并**补充一段新的描述**，那么你可以在回滚时加上新的 `--task` 参数！

```bash
python run.py --project_path "WareHouse/SnakeGame_DefaultOrganization_2026xxxx" --rollback_phase 1 --task "开发一个贪吃蛇游戏。必须包含精美的 Pygame 计分板，且蛇的颜色必须是彩虹色连续渐变。"
```

*此模式下，ChatDev 在穿越回你指定的阶段时，会悄悄把你最新的 Prompt 替换进它的历史记忆中，智能体接下来将根据你的新需求接着展开讨论/编程。*

---

## 📊 在 Benchmark (评测) 模式中的应用

我们的 Benchmark 运行脚本 `run_benchmark.py` 也全面支持 Checkpoint 功能！参数用法与 `run.py` **完全一致**。当你由于某些 Token 超限或中断想要重测某一条数据集时，这就变得非常有用了。

```bash
# 遇到错误中断后，恢复 benchmark_task_001
python run_benchmark.py --task "0" --project_path "WareHouse/benchmark_task_001_BenchmarkOrg_2026xxxx" --rollback_phase "2"
```

## ⚠️ 注意事项

1. **不可跨配置回滚**: 如果你在首次运行时使用的是 `Default` 公司配置，回滚时也必须在相同的公司配置下进行（默认就是 `Default`），不要随意切换使用的角色架构体系。
2. **磁盘文件覆写机制**: 发出回滚指令后，ChatDev 会根据备份文件强行**复原磁盘中的代码**。这意味着你（在项目输出文件夹里）手动修改的代码可能会被回滚覆盖到旧版本！如果要人工改代码，请在回滚操作执行完毕（并进入下一步需要人工干预的节点）后再改，或者提前做好本地文件备份。 
