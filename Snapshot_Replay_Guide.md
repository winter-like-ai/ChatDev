# ChatDev 快照与复现系统说明文档 (Snapshot & Replay Guide)

本项目在大模型 API 调用层 `camel/model_backend.py` 实现了两种核心运行模式，用于追踪、审查以及廉价复现智能体对话全过程。

## 1. 快照模式 (Snapshot)
这是系统的默认运行模式。每次模型请求时，系统会自动在代码生成的 `WareHouse/xxx/` 工作空间中：
1. **自动 Git 追踪**：初始化 `.git` 环境，并在每次 API 请求之前执行 `git add .` 和 `git commit`。如果代码出错或你想恢复上下文，随时可以通过 Git 撤销修改。
2. **完整 IO 录制**：把每次请求的 **Input `messages`** 和返回的 **Output**，连同配置和其他元数据完整的写入到名为 `api_records.jsonl` 的文件内。这就构成了一个不可篡改的数据回放快照。

### 使用方法：
像往常一样运行 `run.py` 即可，快照记录和 Git 特性会自动在对应生成的 `WareHouse` 文件夹下发生。
```bash
python run.py --task "Develop a basic Gomoku game." --name "Gomoku"
```

---

## 2. 复现模式 (Replay)
这是最新引入的防损耗功能。当你需要通过重新运行主程序来测试项目的内部流转逻辑，但又**不想花费任何真实的 API 金额**，可选用该模式。
* **原理**：在该模式下，所有通过 `run.py` 触发的底层 LLM 调用都被拦截。系统会去你指定的 `api_records.jsonl` 中，寻找一个 `input` 字段和当前 `messages` 完全对得上的快照记录，并利用 OpenAI 官方的 `ChatCompletion.model_validate()` 从存下的 `output` 里完整重建出一个虚假的 API 返回对象。
* **优势**：完美骗过项目其他所有上层逻辑（Agents, Parse 等），它们会认为这个对象是真的。速度极快，不消耗 Tokens，且保证 100% 同构可复现。

### 使用方法：
在运行 `run.py` 时新增一项目命令 `--replay` 并跟上任意正确的 `.jsonl` 快照绝对路径或关联相对路径。
```bash
python run.py --task "Develop a basic Gomoku game." --name "Gomoku" --replay "WareHouse/Gomoku_DefaultOrganization_.../api_records.jsonl"
```

> **注意：** 必须确保启动 `run.py` 时提供的 `--task` 以及后续的所有交互历史与 `jsonl` 内部记录的历史匹配。因为复现模式会对 `input` 内容做严格比对校验，如果任何一步发生分歧（例如你在复现时临时修改了一个 Agent 的底层 Prompt），导致查不到匹配的记录，程序会抛出 `RuntimeError` 提醒脱轨。

## 默认体验配置
我已经在此项目根目录下放置了一个运行完好的默认生成记录样例文件 `default_replay.jsonl`。这是之前要求 ChatDev "写一个命令行词汇统计工具" 任务成功录制下来的。

**体验指令：**
```bash
python run.py --task "Create a CLI tool that takes a text file path as input and outputs the total word count. The tool should handle basic punctuation and count sequences of alphanumeric characters as words. Output the count to the console." --name "CLI_Text_File_Word_Counter" --replay "default_replay.jsonl"
```
预期结果是几乎在一两秒钟之内，所有的大模型开发角色立刻光速回复并将完整的 CLI 开发代码生成到 `WareHouse`，中间所有的 API 调用会提示 `[Replay Mode]` 并跳过真实的请求损耗。
