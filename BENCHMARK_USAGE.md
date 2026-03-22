# ChatDev Benchmark 使用说明

## 简介

`run_benchmark.py` 是 ChatDev 的基准测试运行脚本，用于评估 ChatDev 在 ProgramDev 数据集上的表现。

## 基本用法

### 运行所有任务

```bash
python run_benchmark.py
```

或

```bash
python run_benchmark.py --task all
```

这将顺序执行 `benchmark/programdev/programdev_dataset.json` 中的所有任务。

### 运行单个任务

#### 使用项目名称运行

```bash
python run_benchmark.py --task Checkers
```

#### 使用数字索引运行

```bash
python run_benchmark.py --task 0
```

索引从 0 开始，对应数据集中的第一个任务。

## 参数说明

| 参数 | 简写 | 类型 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--task` | `-t` | string | `"all"` | 要运行的任务标识符（项目名如 'TicTacToe' 或数字索引如 '0'），输入 'all' 运行全部 |
| `--dataset` | `-d` | string | `None` | 指定数据集的 JSON 文件路径，默认使用内置的 `benchmark/programdev/programdev_dataset.json` |
| `--project_path` | - | string | `None` | 指定一个历史运行的项目目录，用于恢复执行（例如 `WareHouse/Checkers_DefaultOrganization_20260318114510`） |
| `--rollback_phase` | - | string | `None` | 指定要恢复执行的具体阶段名称或索引（例如 `6` 或 `Coding`） |

## 使用示例

### 示例 1：运行单个 Checkers 任务

```bash
python run_benchmark.py --task Checkers
```

### 示例 2：运行索引为 0 的任务

```bash
python run_benchmark.py --task 0
```

### 示例 3：使用自定义数据集运行任务

```bash
python run_benchmark.py --task TicTacToe --dataset /path/to/custom_dataset.json
```

### 示例 4：从历史项目恢复执行

```bash
python run_benchmark.py --task Checkers --project_path "WareHouse/Checkers_DefaultOrganization_20260318114510" --rollback_phase 6
```

### 示例 5：运行所有任务

```bash
python run_benchmark.py --task all
```

## 支持的任务列表

当前 `programdev_dataset.json` 中包含以下任务：

| 索引 | 项目名称 | 描述 |
|------|----------|------|
| 0 | Checkers | 开发一个国际跳棋游戏 |
| 1 | Sudoku | 开发一个经典的数独游戏 |
| 2 | TheCrossword | 实现一个填字游戏 |
| 3 | DetectPalindromes | 检测文本文件中的回文 |
| 4 | BudgetTracker | 创建预算追踪器 |
| 5 | FibonacciNumbers | 生成斐波那契数列 |
| 6 | TicTacToe | 井字棋游戏 |
| 7 | Gomoku | 五子棋游戏 |
| 8 | Chess | 国际象棋游戏 |
| 9 | 2048 | 2048 游戏 |
| 10 | Tiny Rouge | 类似塔楼术士的 Roguelike 游戏 |
| 11 | Wordle | Wordle 猜词游戏 |
| 12 | Minesweeper | 扫雷游戏 |
| 13 | ConnectionsNYT | 纽约时报 Connections 拼图 |
| 14 | StrandsNYT | 纽约时报 Strands 拼图 |
| 15 | SnakeGame | 贪吃蛇游戏 |
| 16 | ConnectFour | 四子棋游戏 |
| 17 | TriviaQuiz | 问答测验程序 |
| 18 | DouDizhuPoker | 斗地主游戏 |
| 19 | Tetris | 俄罗斯方块游戏 |
| 20 | ReversiOthello | 黑白棋游戏 |
| 21 | StrandsGame | Strands 文字拼图 |
| 22 | MonopolyGo | 简化版大富翁游戏 |
| 23 | EpisodeChooseYourStory | 互动故事游戏 |
| 24 | CandyCrush | 类似 Candy Crush 的三消游戏 |
| 25 | FlappyBird | Flappy Bird 克隆版 |
| 26 | TextBasedSpaceInvaders | 文本版太空侵略者 |
| 27 | GoldMiner | 黄金矿工游戏 |
| 28 | Pong | 双人乒乓球游戏 |
| 29 | Mastermind | 猜密码游戏 |

## 输出说明

运行完成后，脚本会输出评测报告，包含以下信息：

- **代码验证通过率**：代码测试用例的通过百分比
- **是否能成功运行**：程序是否能成功执行
- **是否有语法错误**：代码是否存在语法错误
- **是否有安全警报**：代码是否存在安全问题
- **运行总耗时**：程序执行所需的时间（毫秒）
- **详情**：详细的评测信息

## 注意事项

1. 运行单个任务时，建议使用项目名称而不是索引，因为索引可能会随着数据集的更新而变化。
2. 使用 `--project_path` 和 `--rollback_phase` 参数时，确保指定的项目目录和检查点存在。
3. 运行所有任务可能需要较长时间，请根据实际情况选择运行单个任务或全部任务。
4. 生成的项目文件会保存在 `WareHouse/` 目录下，目录命名格式为 `{项目名}_{组织名}_{时间戳}`。
