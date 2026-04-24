"""
schema.py - JSON 输出结构验证

提供 validate() 函数，验证 LogParser 的输出是否符合预定义 schema。
"""
from typing import List, Tuple

# 预定义的 JSON Schema（简化版，用 Python dict 描述）
SCHEMA = {
    "type": "object",
    "required": ["metadata", "events", "summary", "_analysis"],
    "properties": {
        "metadata": {
            "type": "object",
            "description": "从 Preprocessing 事件提取的会话元信息",
        },
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["event_id", "event_type", "timestamp"],
                "properties": {
                    "event_id": {"type": "integer"},
                    "event_type": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "sender": {"type": ["string", "null"]},
                    "raw_line_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
            },
        },
        "summary": {
            "type": "object",
            "required": [
                "total_events",
                "total_cost",
                "total_tokens",
                "num_api_calls",
                "phases_executed",
                "event_type_counts",
            ],
        },
        "_analysis": {
            "description": "预留字段，供 bug 分析器写入结果。初始为 null",
        },
    },
}

# 已知的合法 event_type 值
VALID_EVENT_TYPES = {
    "preprocessing", "chatting", "role_playing", "start_chat",
    "agent_message", "openai_usage", "seminar_conclusion",
    "update_codes", "rewrite_codes", "software_info", "execute_detail",
    "post_info", "git_info", "test_reports",
    "test_info", "cmd_execute", "human_agent_interaction",
    "user_provided_comments", "task_prompt_improve", "memory_retrieval",
    "hybrid_replay", "loaded", "http_request", "flask_not_start",
    "files_read", "module_not_found",
    "unknown",
}


def validate(data: dict) -> Tuple[bool, List[str]]:
    """验证 LogParser 输出的 dict 是否符合预期结构。

    Args:
        data: LogParser.parse() 返回的 dict

    Returns:
        (is_valid, errors):
            is_valid: 是否通过全部检查
            errors:   不通过的原因列表（空列表表示通过）
    """
    errors: List[str] = []

    # 1. 顶层字段
    for key in ("metadata", "events", "summary", "_analysis"):
        if key not in data:
            errors.append(f"缺少顶层字段: {key}")

    if errors:
        return False, errors

    # 2. events 必须是列表
    if not isinstance(data["events"], list):
        errors.append("events 字段必须是 list")
        return False, errors

    # 3. 逐个检查 event
    for i, event in enumerate(data["events"]):
        if not isinstance(event, dict):
            errors.append(f"events[{i}] 不是 dict")
            continue
        for required in ("event_id", "event_type", "timestamp"):
            if required not in event:
                errors.append(f"events[{i}] 缺少必要字段: {required}")

        et = event.get("event_type")
        if et and et not in VALID_EVENT_TYPES:
            errors.append(f"events[{i}] 未知 event_type: {et}")

    # 4. summary 字段
    summary = data.get("summary", {})
    if not isinstance(summary, dict):
        errors.append("summary 字段必须是 dict")
    else:
        for key in ("total_events", "total_cost", "total_tokens",
                     "num_api_calls", "phases_executed", "event_type_counts"):
            if key not in summary:
                errors.append(f"summary 缺少字段: {key}")

    # 5. event_id 连续性
    event_ids = [e.get("event_id") for e in data["events"] if "event_id" in e]
    if event_ids and event_ids != list(range(len(event_ids))):
        errors.append("event_id 不连续")

    return len(errors) == 0, errors
