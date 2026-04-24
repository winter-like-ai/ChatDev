# log_analyzer - ChatDev 日志结构化解析模块

将 ChatDev 生成的 `.log` 文件解析为结构化 JSON 格式，便于程序化分析、bug 识别和统计。

## 功能特性

- **完整事件解析**：识别并解析 26 种日志事件类型（全部源代码级追踪确认）
- **结构化输出**：输出标准化 JSON，包含 metadata、events、summary 三大块
- **批量处理**：支持递归解析目录下所有日志文件
- **规则可扩展**：通过 `@register_rule` 装饰器添加自定义事件解析规则
- **Bug 分析扩展**：预留 `_analysis` 字段和 `AnalyzerBase` 接口，支持后续集成 bug 检测器
- **命令行工具**：提供 CLI 入口，支持单文件/批量/验证模式

## 快速开始

### Python API

```python
from log_analyzer import LogParser

parser = LogParser()

# 单文件解析 — 输出 JSON 到日志同目录
result = parser.parse("path/to/project.log")

# 指定输出路径
result = parser.parse("project.log", output_path="output/result.json")

# 批量解析
results = parser.parse_batch("dataset_mini/")

# 批量解析并指定输出目录
results = parser.parse_batch("dataset_mini/", output_dir="parsed_results/")
```

### 便捷函数

```python
from log_analyzer import parse_log, parse_batch

result = parse_log("project.log")
results = parse_batch("dataset_mini/")
```

### 命令行

```bash
# 单文件
python -m log_analyzer.cli input.log
python -m log_analyzer.cli input.log -o output.json

# 批量
python -m log_analyzer.cli ./dataset_mini/ --batch
python -m log_analyzer.cli ./dataset_mini/ --batch -o ./results/

# 带验证
python -m log_analyzer.cli input.log --validate
```

## JSON 输出格式

```json
{
  "metadata": {
    "project_name": "...",
    "task_prompt": "...",
    "config_path": "...",
    "chatdev_config": { ... },
    "chatgpt_config": { ... }
  },
  "events": [
    {
      "event_id": 0,
      "event_type": "preprocessing",
      "timestamp": "2026-03-31T21:29:16",
      "sender": "System",
      "raw_line_range": [1, 20],
      ...
    }
  ],
  "summary": {
    "total_events": 42,
    "total_cost": 0.224375,
    "total_tokens": 30163,
    "num_api_calls": 16,
    "phases_executed": ["DemandAnalysis", "LanguageChoose", "Coding", ...],
    "event_type_counts": { "chatting": 8, "openai_usage": 16, ... }
  },
  "_analysis": null
}
```

## 事件类型完整表

### 主要事件（几乎所有日志都会出现）

| event_type | 说明 | 源代码出处 |
|---|---|---|
| `preprocessing` | 会话元信息 | `chat_chain.py: pre_processing()` |
| `chatting` | Phase 参数表 | `phase.py: @log_arguments chatting()` |
| `role_playing` | 角色扮演配置 | `role_playing.py: @log_arguments __init__()` |
| `start_chat` | 对话开始 | `role_playing.py: init_chat()` |
| `agent_message` | Agent 消息交互 | `phase.py: chatting() loop` |
| `openai_usage` | Token 消耗统计 | `model_backend.py: _log_usage()` |
| `seminar_conclusion` | Phase 结论 | `phase.py: chatting()` |
| `update_codes` | 代码更新 diff | `codes.py: _update_codes()` |
| `rewrite_codes` | 代码写入文件 | `codes.py: _rewrite_codes()` |
| `software_info` | 累计统计 | `phase.py: update_chat_env()` |
| `execute_detail` | 执行顺序 | `composed_phase.py: execute()` |
| `post_info` | 最终统计 | `chat_chain.py: post_processing()` |
| `git_info` | Git 操作 | `codes.py / chat_chain.py` |
| `test_reports` | 测试报告 | `phase.py: TestErrorSummary` |

### 附加事件

| event_type | 说明 |
|---|---|
| `test_info` | 测试通过 |
| `cmd_execute` | pip install |
| `human_agent_interaction` | 人机交互 |
| `user_provided_comments` | 用户反馈 |
| `task_prompt_improve` | Prompt 自优化 |
| `memory_retrieval` | Memory 检索 |
| `hybrid_replay` | 混合模式 |
| `loaded` | 快照加载 |
| `http_request` | API 请求 |
| `flask_not_start` | Flask 状态 |
| `files_read` | 文件加载 |
| `module_not_found` | 模块错误修复 |

## 规则注册机制

### 内置规则

模块导入时自动注册所有内置规则。你可以查看已注册的规则：

```python
from log_analyzer.rules import get_rules

for rule in get_rules():
    print(f"[{rule.priority:03d}] {rule.name}: {rule.event_type}")
```

### 自定义规则

使用 `@register_rule` 装饰器添加新的解析规则：

```python
from log_analyzer.rules import register_rule
from log_analyzer.event_types import RawEntry

@register_rule(
    name="my_custom_event",
    event_type="custom_event",
    pattern=r"\*\*\[CustomMarker\]\*\*",
    priority=50  # 数字越小优先级越高，内置规则默认 100
)
def parse_custom_event(entry: RawEntry) -> dict:
    """解析自定义事件。"""
    return {
        "custom_field": entry.content.split("[CustomMarker]**")[-1].strip()
    }

# 注册后，LogParser 自动使用该规则
from log_analyzer import LogParser
parser = LogParser()
result = parser.parse("my_log.log")
```

### 优先级说明

当一个日志条目匹配多个规则时，`priority` 最小的规则优先。建议：

- `0-49`：最高优先级，用于覆盖内置规则
- `50-99`：高优先级自定义规则
- `100`：内置主要事件的默认优先级
- `200+`：低优先级兜底规则

## Bug 分析扩展

### 接口说明

每个 bug 检测器是一个 `AnalyzerBase` 子类，核心方法是 `check_event()`：

```python
from log_analyzer.analyzer_base import AnalyzerBase, BugAnalyzerRegistry

class RepeatOutputBug(AnalyzerBase):
    bug_type_id = "BUG_001"
    bug_type_name = "Agent 重复输出"

    def check_event(self, event: dict) -> tuple:
        """
        输入: 一个 event dict
        输出: (is_buggy: bool, detail: dict | None)
        """
        if event["event_type"] != "agent_message":
            return False, None
        # ... 检测逻辑 ...
        return is_buggy, {"reason": "..."}
```

### 使用注册中心

```python
registry = BugAnalyzerRegistry()
registry.register(RepeatOutputBug())
# registry.register(AnotherBugAnalyzer())

# 运行所有分析器
parsed_data = parser.parse("log.log")
parsed_data["_analysis"] = registry.run_all(parsed_data)

# 运行单个分析器
bugs_001 = registry.run_single("BUG_001", parsed_data)

# 查看已注册的分析器
print(registry.list_analyzers())
```

### 输出格式

```json
{
  "_analysis": {
    "total_bugs_found": 3,
    "analyzers_used": ["BUG_001", "BUG_002"],
    "by_type": {
      "BUG_001": [
        {"event_id": 12, "bug_type_id": "BUG_001", "bug_type_name": "Agent 重复输出", "detail": {...}}
      ],
      "BUG_002": [...]
    }
  }
}
```

## 模块结构

```
log_analyzer/
├── __init__.py          # 模块入口，导出 LogParser, parse_log, parse_batch
├── event_types.py       # EventType 枚举 + RawEntry 数据结构
├── rules.py             # @register_rule 装饰器 + 26 种内置事件解析函数
├── parser.py            # LogParser 核心解析器
├── schema.py            # JSON 输出 schema 验证
├── analyzer_base.py     # AnalyzerBase + BugAnalyzerRegistry
├── cli.py               # 命令行入口
└── README.md            # 本文档
```

## API Reference

### `LogParser`

| 方法 | 说明 |
|---|---|
| `parse(log_path, output_path=None)` | 解析单个日志，返回 dict，写入 JSON |
| `parse_batch(dir_path, output_dir=None)` | 批量解析目录，返回 list[dict] |

构造参数:

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `skip_flask` | bool | True | 跳过 flask_not_start 事件 |
| `skip_http` | bool | False | 跳过 http_request 事件 |

### `validate(data) -> (bool, list[str])`

验证 LogParser 输出是否符合 schema。

### `AnalyzerBase`

| 方法 | 说明 |
|---|---|
| `check_event(event) -> (bool, dict\|None)` | 检查单个 event（抽象方法） |
| `analyze_all(parsed_data) -> list[dict]` | 对所有 events 执行检查 |

### `BugAnalyzerRegistry`

| 方法 | 说明 |
|---|---|
| `register(analyzer)` | 注册分析器 |
| `unregister(bug_type_id)` | 取消注册 |
| `list_analyzers()` | 列出已注册的分析器 |
| `run_all(parsed_data)` | 运行全部分析器 |
| `run_single(bug_type_id, parsed_data)` | 运行单个分析器 |
