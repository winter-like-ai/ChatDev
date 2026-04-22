"""
rules.py - ChatDev 日志事件解析规则注册表

提供:
  - @register_rule 装饰器：用于注册新的事件解析规则
  - get_rules(): 获取当前已注册的全部规则
  - classify(): 根据内容匹配规则
  - 全部内置事件的解析函数

规则匹配顺序由 priority 控制（数字越小优先级越高）。
"""
import re
from dataclasses import dataclass
from typing import Callable, List, Optional

from .event_types import RawEntry

# ============================================================
#  规则注册机制
# ============================================================

@dataclass
class EventRule:
    """描述一条事件解析规则。

    Attributes:
        name:        规则唯一标识名称
        event_type:  对应的事件类型字符串（写入 JSON 的 event_type）
        pattern:     编译后的正则表达式
        parser_func: 解析函数  (RawEntry) -> dict
        priority:    优先级数字，越小越先匹配（默认 100）
    """
    name: str
    event_type: str
    pattern: re.Pattern
    parser_func: Callable[[RawEntry], dict]
    priority: int = 100


# 全局规则列表（按 priority 升序排列）
_RULES: List[EventRule] = []


def register_rule(
    name: str,
    event_type: str,
    pattern: str,
    priority: int = 100,
) -> Callable:
    """规则注册装饰器。

    用法::

        @register_rule(
            name="seminar_conclusion",
            event_type="seminar_conclusion",
            pattern=r"\\*\\*\\[Seminar Conclusion\\]\\*\\*",
        )
        def parse_seminar_conclusion(entry: RawEntry) -> dict:
            return {"conclusion": ...}

    Args:
        name:       规则唯一标识
        event_type: JSON 中的 event_type 值
        pattern:    正则表达式字符串
        priority:   优先级（0 最高，默认 100）

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        rule = EventRule(
            name=name,
            event_type=event_type,
            pattern=re.compile(pattern, re.DOTALL),
            parser_func=func,
            priority=priority,
        )
        _RULES.append(rule)
        _RULES.sort(key=lambda r: r.priority)
        return func
    return decorator


def get_rules() -> List[EventRule]:
    """获取当前已注册的全部规则（按 priority 升序）。"""
    return list(_RULES)


def classify(content: str) -> Optional[EventRule]:
    """根据 content 匹配最高优先级的规则。

    Returns:
        匹配到的 EventRule，或 None
    """
    for rule in _RULES:
        if rule.pattern.search(content):
            return rule
    return None


# ============================================================
#  辅助工具
# ============================================================

def _parse_markdown_table(text: str) -> dict:
    """从 Markdown 表格中提取 key-value 对。

    表格格式::

        | Parameter | Value |
        | --- | --- |
        | **key** | value |
    """
    result = {}
    for m in re.finditer(
        r"\|\s*\*\*(\w+)\*\*\s*\|\s*(.*?)\s*\|", text
    ):
        key = m.group(1).strip()
        value = m.group(2).strip()
        result[key] = value
    return result


def _parse_kv_lines(text: str) -> dict:
    """从 'key: value' 行中提取 key-value 对。"""
    result = {}
    for m in re.finditer(r"^(\w[\w_]*)\s*:\s*(.+)$", text, re.MULTILINE):
        result[m.group(1).strip()] = m.group(2).strip()
    return result


def _parse_stats_lines(text: str) -> dict:
    """从带 emoji 的统计行中提取数据。

    格式示例::

        💰**cost**=$0.032960
        🔨**version_updates**=-1
    """
    result = {}
    for m in re.finditer(
        r"\*\*(\w+)\*\*\s*=\s*(.+?)(?:\n|$)", text
    ):
        key = m.group(1).strip()
        raw_val = m.group(2).strip()
        # 尝试转换数字
        if raw_val.startswith("$"):
            try:
                result[key] = float(raw_val[1:])
            except ValueError:
                result[key] = raw_val
        else:
            try:
                result[key] = int(raw_val)
            except ValueError:
                try:
                    result[key] = float(raw_val)
                except ValueError:
                    result[key] = raw_val
    return result


def _safe_int(val: str, default: int = 0) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _safe_float(val: str, default: float = 0.0) -> float:
    try:
        return float(val.lstrip("$"))
    except (ValueError, TypeError):
        return default


# ============================================================
#  内置规则：主要事件（priority 100）
# ============================================================

@register_rule(
    name="preprocessing",
    event_type="preprocessing",
    pattern=r"\*\*\[Preprocessing\]\*\*",
    priority=10,
)
def parse_preprocessing(entry: RawEntry) -> dict:
    """解析 Preprocessing 事件，提取会话元信息。"""
    content = entry.content
    result = {}

    patterns = {
        "start_time": r"\*\*ChatDev Starts\*\*\s*\((\d+)\)",
        "timestamp": r"\*\*Timestamp\*\*:\s*(\d+)",
        "config_path": r"\*\*config_path\*\*:\s*(.+?)(?:\n|$)",
        "config_phase_path": r"\*\*config_phase_path\*\*:\s*(.+?)(?:\n|$)",
        "config_role_path": r"\*\*config_role_path\*\*:\s*(.+?)(?:\n|$)",
        "task_prompt": r"\*\*task_prompt\*\*:\s*(.+?)(?:\n\n|\*\*)",
        "project_name": r"\*\*project_name\*\*:\s*(.+?)(?:\n|$)",
        "log_file": r"\*\*Log File\*\*:\s*(.+?)(?:\n|$)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, content, re.DOTALL)
        if m:
            result[key] = m.group(1).strip()

    # ChatDevConfig
    cdc_match = re.search(
        r"\*\*ChatDevConfig\*\*:\s*\n(.*?)(?:\n\n|\*\*ChatGPTConfig\*\*)",
        content, re.DOTALL,
    )
    if cdc_match:
        result["chatdev_config"] = _parse_kv_lines(cdc_match.group(1))

    # ChatGPTConfig
    cgc_match = re.search(
        r"\*\*ChatGPTConfig\*\*:\s*\n(.*?)$",
        content, re.DOTALL,
    )
    if cgc_match:
        result["chatgpt_config"] = _parse_kv_lines(cgc_match.group(1))

    return result


@register_rule(
    name="execute_detail",
    event_type="execute_detail",
    pattern=r"\*\*\[Execute Detail\]\*\*",
    priority=20,
)
def parse_execute_detail(entry: RawEntry) -> dict:
    """解析 Phase 执行顺序事件。"""
    content = entry.content
    result = {}
    m = re.search(
        r"execute SimplePhase:\[(\w+)\] in ComposedPhase:\[(\w+)\],\s*cycle\s*(\d+)",
        content,
    )
    if m:
        result["simple_phase"] = m.group(1)
        result["composed_phase"] = m.group(2)
        result["cycle"] = int(m.group(3))
    return result


@register_rule(
    name="chatting",
    event_type="chatting",
    pattern=r"\*\*\[chatting\]\*\*",
    priority=30,
)
def parse_chatting(entry: RawEntry) -> dict:
    """解析 chatting 参数表事件。"""
    content = entry.content
    params = _parse_markdown_table(content)
    result = {"parameters": params}

    # 提取关键字段到顶层
    if "phase_name" in params:
        result["phase_name"] = params["phase_name"]
    if "assistant_role_name" in params:
        result["assistant_role"] = params["assistant_role_name"]
    if "user_role_name" in params:
        result["user_role"] = params["user_role_name"]
    return result


@register_rule(
    name="role_playing",
    event_type="role_playing",
    pattern=r"\*\*\[RolePlaying\]\*\*",
    priority=30,
)
def parse_role_playing(entry: RawEntry) -> dict:
    """解析 RolePlaying 配置表事件。"""
    content = entry.content
    params = _parse_markdown_table(content)
    result = {"parameters": params}

    if "assistant_role_name" in params:
        result["assistant_role"] = params["assistant_role_name"]
    if "user_role_name" in params:
        result["user_role"] = params["user_role_name"]
    return result


@register_rule(
    name="start_chat",
    event_type="start_chat",
    pattern=r"\*\*\[Start Chat\]\*\*",
    priority=40,
)
def parse_start_chat(entry: RawEntry) -> dict:
    """解析 Start Chat 事件。"""
    content = entry.content
    result = {}

    # 提取 system prompt: 在 [...] 内的部分
    sp_match = re.search(r"\[Start Chat\]\*\*\s*\n\n\[(.*?)\]\s*\n\n", content, re.DOTALL)
    if sp_match:
        result["system_prompt"] = sp_match.group(1).strip()
        result["user_message"] = content[sp_match.end():].strip()
    else:
        # fallback: 整个内容在 [Start Chat]** 之后
        after = content.split("[Start Chat]**")[-1].strip()
        result["user_message"] = after

    return result


@register_rule(
    name="agent_message",
    event_type="agent_message",
    pattern=r"\<-\>\s*\w+.*?\s+on\s*:\s*\w+,\s*turn\s*\d+",
    priority=50,
)
def parse_agent_message(entry: RawEntry) -> dict:
    """解析 Agent 间消息交互事件。"""
    content = entry.content
    result = {}

    # 提取对话元数据: **SenderRole<->ReceiverRole on : PhaseName, turn N**
    meta_match = re.search(
        r"\*\*(\w[\w\s]*?)\s*<->\s*(\w[\w\s]*?)\s+on\s*:\s*(\w+),\s*turn\s*(\d+)\*\*",
        content,
    )
    if meta_match:
        result["sender"] = meta_match.group(1).strip()
        result["receiver"] = meta_match.group(2).strip()
        result["phase_name"] = meta_match.group(3).strip()
        result["turn"] = int(meta_match.group(4))

    # 提取 system prompt 和 message
    sp_match = re.search(r"\[(.*?)\]\s*\n\n", content, re.DOTALL)
    if sp_match:
        # system prompt 在 [...] 内
        result["system_prompt"] = sp_match.group(1).strip()
        result["message"] = content[sp_match.end():].strip()
    else:
        # 获取 meta 行之后的全部内容
        if meta_match:
            result["message"] = content[meta_match.end():].strip()
        else:
            result["message"] = content

    return result


@register_rule(
    name="openai_usage",
    event_type="openai_usage",
    pattern=r"\*\*\[OpenAI_Usage_Info Receive\]\*\*",
    priority=50,
)
def parse_openai_usage(entry: RawEntry) -> dict:
    """解析 OpenAI Token 使用统计事件。"""
    content = entry.content
    result = {}

    for field_name in ("prompt_tokens", "completion_tokens", "total_tokens"):
        m = re.search(rf"{field_name}:\s*(\d+)", content)
        if m:
            result[field_name] = int(m.group(1))

    m = re.search(r"cost:\s*\$?([\d.]+)", content)
    if m:
        result["cost"] = float(m.group(1))

    return result


@register_rule(
    name="seminar_conclusion",
    event_type="seminar_conclusion",
    pattern=r"\*\*\[Seminar Conclusion\]\*\*",
    priority=50,
)
def parse_seminar_conclusion(entry: RawEntry) -> dict:
    """解析 Seminar Conclusion 事件。"""
    content = entry.content
    after = content.split("[Seminar Conclusion]**:")[-1].strip()
    return {"conclusion": after}


@register_rule(
    name="update_codes",
    event_type="update_codes",
    pattern=r"\*\*\[Update Codes\]\*\*",
    priority=50,
)
def parse_update_codes(entry: RawEntry) -> dict:
    """解析代码更新事件，提取文件名和 diff。"""
    content = entry.content
    result = {}

    # 提取文件名
    m = re.search(r"(\S+\.py)\s+updated", content)
    if m:
        result["file_name"] = m.group(1)

    # 提取 diff 内容
    diff_match = re.search(r"```\s*\n(.*?)```", content, re.DOTALL)
    if diff_match:
        result["diff"] = diff_match.group(1).strip()

    return result


@register_rule(
    name="rewrite_codes",
    event_type="rewrite_codes",
    pattern=r"\*\*\[Rewrite Codes\]\*\*",
    priority=50,
)
def parse_rewrite_codes(entry: RawEntry) -> dict:
    """解析代码重写到文件系统事件。"""
    content = entry.content
    lines = content.split("\n")
    files_written = []
    for line in lines:
        if "Wrote" in line:
            files_written.append(line.strip().replace(" Wrote", ""))
        elif "Created" in line and "Rewrite" not in line:
            files_written.append(line.strip().replace(" Created", ""))
    return {"files": files_written}


@register_rule(
    name="software_info",
    event_type="software_info",
    pattern=r"\*\*\[Software Info\]\*\*",
    priority=60,
)
def parse_software_info(entry: RawEntry) -> dict:
    """解析软件统计信息事件。"""
    return {"stats": _parse_stats_lines(entry.content)}


@register_rule(
    name="post_info",
    event_type="post_info",
    pattern=r"\*\*\[Post Info\]\*\*",
    priority=20,
)
def parse_post_info(entry: RawEntry) -> dict:
    """解析 Post Info 事件（最终统计）。"""
    content = entry.content
    result = {"stats": _parse_stats_lines(content)}

    # 提取 duration
    m = re.search(r"\*\*duration\*\*\s*=\s*([\d.]+)s", content)
    if m:
        result["duration_seconds"] = float(m.group(1))

    # 提取 start / end time
    m_start = re.search(r"ChatDev Starts\s*\((\d+)\)", content)
    m_end = re.search(r"ChatDev Ends\s*\((\d+)\)", content)
    if m_start:
        result["start_time"] = m_start.group(1)
    if m_end:
        result["end_time"] = m_end.group(1)

    return result


@register_rule(
    name="git_info",
    event_type="git_info",
    pattern=r"\*\*\[Git (?:Information|Log)\]\*\*",
    priority=50,
)
def parse_git_info(entry: RawEntry) -> dict:
    """解析 Git 操作日志事件。"""
    content = entry.content
    is_log = "Git Log" in content
    return {
        "sub_type": "git_log" if is_log else "git_operation",
        "content": content.split("**\n\n", 1)[-1].strip() if "**\n\n" in content else content,
    }


@register_rule(
    name="test_reports",
    event_type="test_reports",
    pattern=r"\*\*\[Test Reports\]\*\*",
    priority=50,
)
def parse_test_reports(entry: RawEntry) -> dict:
    """解析测试报告事件。"""
    content = entry.content
    report = content.split("[Test Reports]**:")[-1].strip()
    return {"report_content": report}


# ============================================================
#  内置规则：附加事件（priority 100-200）
# ============================================================

@register_rule(
    name="test_info",
    event_type="test_info",
    pattern=r"\*\*\[Test Info\]\*\*",
    priority=100,
)
def parse_test_info(entry: RawEntry) -> dict:
    """解析测试通过信息事件。"""
    return {"passed": "Test Pass" in entry.content}


@register_rule(
    name="cmd_execute",
    event_type="cmd_execute",
    pattern=r"\*\*\[CMD Execute\]\*\*",
    priority=100,
)
def parse_cmd_execute(entry: RawEntry) -> dict:
    """解析命令执行事件。"""
    m = re.search(r"\[CMD\]\s*(.+?)(?:\n|$)", entry.content)
    return {"command": m.group(1).strip() if m else entry.content}


@register_rule(
    name="human_agent_interaction",
    event_type="human_agent_interaction",
    pattern=r"\*\*\[Human-Agent-Interaction\]\*\*",
    priority=100,
)
def parse_human_agent_interaction(entry: RawEntry) -> dict:
    """解析人机交互提示事件。"""
    return {"prompt_content": entry.content}


@register_rule(
    name="user_provided_comments",
    event_type="user_provided_comments",
    pattern=r"\*\*\[User Provided Comments\]\*\*",
    priority=100,
)
def parse_user_provided_comments(entry: RawEntry) -> dict:
    """解析用户反馈事件。"""
    content = entry.content
    m = re.search(r"comments:\s*\n\n(.+)", content, re.DOTALL)
    return {"comments": m.group(1).strip() if m else content}


@register_rule(
    name="task_prompt_improve",
    event_type="task_prompt_improve",
    pattern=r"\*\*\[Task Prompt Self Improvement\]\*\*",
    priority=100,
)
def parse_task_prompt_improve(entry: RawEntry) -> dict:
    """解析 Prompt 自优化事件。"""
    content = entry.content
    result = {}
    m_orig = re.search(r"\*\*Original Task Prompt\*\*:\s*(.+?)(?:\n\*\*|$)", content, re.DOTALL)
    m_impr = re.search(r"\*\*Improved Task Prompt\*\*:\s*(.+?)$", content, re.DOTALL)
    if m_orig:
        result["original_prompt"] = m_orig.group(1).strip()
    if m_impr:
        result["improved_prompt"] = m_impr.group(1).strip()
    return result


@register_rule(
    name="memory_retrieval",
    event_type="memory_retrieval",
    pattern=r"thinking back (?:and found|but find)",
    priority=110,
)
def parse_memory_retrieval(entry: RawEntry) -> dict:
    """解析 Memory 检索事件。"""
    found = "and found" in entry.content
    return {"found": found, "content": entry.content}


@register_rule(
    name="hybrid_replay",
    event_type="hybrid_replay",
    pattern=r"\*\*\[Hybrid (?:Replay|Switch|Live)\]\*\*",
    priority=100,
)
def parse_hybrid_replay(entry: RawEntry) -> dict:
    """解析混合模式控制事件。"""
    content = entry.content
    if "Hybrid Switch" in content:
        sub_type = "switch"
    elif "Hybrid Live" in content:
        sub_type = "live"
    else:
        sub_type = "replay"
    return {"sub_type": sub_type, "content": content}


@register_rule(
    name="loaded",
    event_type="loaded",
    pattern=r"\*\*\[Loaded\]\*\*",
    priority=100,
)
def parse_loaded(entry: RawEntry) -> dict:
    """解析快照记录加载事件。"""
    m = re.search(r"(\d+)\s*条快照记录", entry.content)
    count = int(m.group(1)) if m else 0
    return {"record_count": count}


@register_rule(
    name="http_request",
    event_type="http_request",
    pattern=r"HTTP Request:\s*POST",
    priority=200,
)
def parse_http_request(entry: RawEntry) -> dict:
    """解析 HTTP API 请求日志。"""
    content = entry.content
    m = re.search(r"POST\s+(https?://\S+)", content)
    url = m.group(1).rstrip('"') if m else ""
    status_m = re.search(r'"(HTTP/\S+\s+\d+\s+\w+)"', content)
    status = status_m.group(1) if status_m else ""
    return {"url": url, "status": status}


@register_rule(
    name="flask_not_start",
    event_type="flask_not_start",
    pattern=r"flask app\.py did not start",
    priority=250,
)
def parse_flask_not_start(entry: RawEntry) -> dict:
    """解析 Flask 状态日志（通常可忽略）。"""
    return {}


@register_rule(
    name="files_read",
    event_type="files_read",
    pattern=r"files read from",
    priority=110,
)
def parse_files_read(entry: RawEntry) -> dict:
    """解析文件加载事件。"""
    m = re.search(r"(\d+)\s+files read from\s+(.+?)$", entry.content, re.MULTILINE)
    return {
        "file_count": int(m.group(1)) if m else 0,
        "directory": m.group(2).strip() if m else "",
    }


@register_rule(
    name="module_not_found",
    event_type="module_not_found",
    pattern=r"ModuleNotFoundError",
    priority=110,
)
def parse_module_not_found(entry: RawEntry) -> dict:
    """解析模块导入错误修复事件。"""
    modules = re.findall(r"No module named '(\S+)'", entry.content)
    return {"missing_modules": modules}
