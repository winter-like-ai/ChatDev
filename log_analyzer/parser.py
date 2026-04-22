"""
parser.py - ChatDev 日志核心解析器

提供 LogParser 类，将 .log 文件解析为结构化 JSON。

使用示例::

    from log_analyzer import LogParser

    parser = LogParser()

    # 单文件解析
    result = parser.parse("path/to/log.log")

    # 批量解析
    results = parser.parse_batch("path/to/dataset_mini/")
"""
import json
import os
import re
from datetime import datetime
from typing import List, Optional

from .event_types import EventType, RawEntry
from .rules import classify, get_rules

# 日志条目起始行的正则：[YYYY-DD-MM HH:MM:SS LEVEL]
# 注意 ChatDev 时间戳月日颠倒：实际是 [YYYY-DD-MM ...]
_ENTRY_PATTERN = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+(\w+)\]\s*(.*)",
    re.MULTILINE,
)


class LogParser:
    """ChatDev 日志文件的核心解析器。

    将 .log 文件解析为结构化 dict/JSON，保留扩展性以支持后续 bug 分析。

    Attributes:
        skip_flask: 是否跳过 flask_not_start 事件（默认 True）
        skip_http: 是否跳过 http_request 事件（默认 False）
    """

    def __init__(self, skip_flask: bool = True, skip_http: bool = False):
        self.skip_flask = skip_flask
        self.skip_http = skip_http

    # ================================================================
    #  公开 API
    # ================================================================

    def parse(self, log_path: str, output_path: Optional[str] = None) -> dict:
        """解析单个日志文件。

        Args:
            log_path:    日志文件路径
            output_path: JSON 输出路径。None 则默认与日志同目录同名 .json

        Returns:
            解析后的 dict（同时会写入 JSON 文件）
        """
        log_path = os.path.abspath(log_path)
        if not os.path.isfile(log_path):
            raise FileNotFoundError(f"日志文件不存在: {log_path}")

        with open(log_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # 流水线
        entries = self._split_entries(raw_text)
        events = self._parse_all_entries(entries)
        metadata = self._extract_metadata(events)
        summary = self._build_summary(events, metadata)

        result = {
            "metadata": metadata,
            "events": events,
            "summary": summary,
            "_analysis": None,
        }

        # 写入 JSON
        if output_path is None:
            output_path = os.path.splitext(log_path)[0] + ".json"
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def parse_batch(
        self, dir_path: str, output_dir: Optional[str] = None
    ) -> List[dict]:
        """批量解析目录下所有子目录中的 .log 文件。

        会递归搜索 dir_path 下所有 .log 文件并逐个解析。

        Args:
            dir_path:   顶层目录路径（如 dataset_mini/）
            output_dir: JSON 输出目录。None 则输出到各日志所在目录

        Returns:
            所有解析结果的列表
        """
        dir_path = os.path.abspath(dir_path)
        if not os.path.isdir(dir_path):
            raise NotADirectoryError(f"目录不存在: {dir_path}")

        results = []
        log_files = []

        for root, _dirs, files in os.walk(dir_path):
            for fname in files:
                if fname.endswith(".log"):
                    log_files.append(os.path.join(root, fname))

        log_files.sort()

        for log_path in log_files:
            if output_dir:
                rel = os.path.relpath(log_path, dir_path)
                out_path = os.path.join(
                    output_dir, os.path.splitext(rel)[0] + ".json"
                )
            else:
                out_path = None

            try:
                result = self.parse(log_path, out_path)
                results.append(result)
                print(f"  [OK] {os.path.basename(log_path)}")
            except Exception as e:
                print(f"  [FAIL] {os.path.basename(log_path)}: {e}")

        print(f"\n解析完成: {len(results)}/{len(log_files)} 个文件成功")
        return results

    # ================================================================
    #  内部方法
    # ================================================================

    def _split_entries(self, raw_text: str) -> List[RawEntry]:
        """按时间戳行分割日志为独立条目。

        每个 [YYYY-DD-MM HH:MM:SS LEVEL] 行标记一个新条目的开始。
        条目内容包括从该行到下一个时间戳行之前的所有行。
        """
        lines = raw_text.split("\n")
        entries: List[RawEntry] = []

        current_ts = None
        current_level = None
        current_first_line = None
        content_lines: List[str] = []
        start_line = 1

        for i, line in enumerate(lines, 1):
            m = _ENTRY_PATTERN.match(line)
            if m:
                # 保存上一个条目
                if current_ts is not None:
                    entry = self._build_entry(
                        current_ts,
                        current_level,
                        current_first_line,
                        content_lines,
                        start_line,
                        i - 1,
                    )
                    entries.append(entry)

                current_ts = m.group(1)
                current_level = m.group(2)
                current_first_line = m.group(3)
                content_lines = []
                start_line = i
            else:
                content_lines.append(line)

        # 最后一个条目
        if current_ts is not None:
            entry = self._build_entry(
                current_ts,
                current_level,
                current_first_line,
                content_lines,
                start_line,
                len(lines),
            )
            entries.append(entry)

        return entries

    def _build_entry(
        self,
        timestamp: str,
        level: str,
        first_line: str,
        content_lines: List[str],
        line_start: int,
        line_end: int,
    ) -> RawEntry:
        """构建一个 RawEntry 对象。

        拆分 first_line 中的 sender 和 content。
        """
        first_line = first_line.strip()
        sender = None
        content = first_line

        # 尝试从 first_line 中提取 sender
        # 格式: "RoleName: content..." 或 纯 content
        # 需区分开 "key: value" 格式和 "RoleName: content"
        # RoleName 通常以大写字母开头
        colon_pos = first_line.find(": ")
        if colon_pos > 0:
            possible_sender = first_line[:colon_pos].strip()
            # sender 判定：以大写字母开头 / 是 "System" 等
            if (
                possible_sender
                and possible_sender[0].isupper()
                and len(possible_sender.split()) <= 5
                and not possible_sender.startswith("HTTP")
                and not possible_sender.startswith("flask")
            ):
                sender = possible_sender
                content = first_line[colon_pos + 2:]

        # 拼接后续行
        if content_lines:
            extra = "\n".join(content_lines)
            content = content + "\n" + extra if content else extra

        return RawEntry(
            timestamp=timestamp,
            level=level,
            sender=sender,
            content=content.rstrip(),
            line_start=line_start,
            line_end=line_end,
        )

    def _parse_all_entries(self, entries: List[RawEntry]) -> List[dict]:
        """对所有条目进行分类和解析。"""
        events = []
        event_id = 0

        for entry in entries:
            rule = classify(entry.content)

            if rule is None:
                event_type = EventType.UNKNOWN.value
                parsed = {"raw_content": entry.content[:500]}
            else:
                event_type = rule.event_type
                # 跳过不需要的事件
                if self.skip_flask and event_type == EventType.FLASK_NOT_START.value:
                    continue
                if self.skip_http and event_type == EventType.HTTP_REQUEST.value:
                    continue
                try:
                    parsed = rule.parser_func(entry)
                except Exception as e:
                    parsed = {"parse_error": str(e), "raw_content": entry.content[:500]}

            event = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": self._normalize_timestamp(entry.timestamp),
                "sender": entry.sender,
                "raw_line_range": [entry.line_start, entry.line_end],
                **parsed,
            }
            events.append(event)
            event_id += 1

        return events

    def _extract_metadata(self, events: List[dict]) -> dict:
        """从 preprocessing 事件中提取元数据。"""
        metadata = {}
        for event in events:
            if event.get("event_type") == EventType.PREPROCESSING.value:
                # 将 preprocessing 事件的解析结果作为 metadata
                for key in (
                    "start_time", "timestamp", "config_path",
                    "config_phase_path", "config_role_path",
                    "task_prompt", "project_name", "log_file",
                    "chatdev_config", "chatgpt_config",
                ):
                    if key in event:
                        metadata[key] = event[key]
                break
        return metadata

    def _build_summary(self, events: List[dict], metadata: dict) -> dict:
        """生成统计摘要。"""
        summary = {
            "total_events": len(events),
            "total_cost": 0.0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0,
            "num_api_calls": 0,
            "phases_executed": [],
            "event_type_counts": {},
        }

        seen_phases = []

        for event in events:
            et = event.get("event_type", "unknown")
            summary["event_type_counts"][et] = (
                summary["event_type_counts"].get(et, 0) + 1
            )

            if et == EventType.OPENAI_USAGE.value:
                summary["num_api_calls"] += 1
                summary["total_cost"] += event.get("cost", 0.0)
                summary["total_prompt_tokens"] += event.get("prompt_tokens", 0)
                summary["total_completion_tokens"] += event.get(
                    "completion_tokens", 0
                )
                summary["total_tokens"] += event.get("total_tokens", 0)

            elif et == EventType.EXECUTE_DETAIL.value:
                phase = event.get("simple_phase", "")
                if phase and phase not in seen_phases:
                    seen_phases.append(phase)

            elif et == EventType.POST_INFO.value:
                if "duration_seconds" in event:
                    summary["duration_seconds"] = event["duration_seconds"]
                if "start_time" in event:
                    summary["start_time"] = event["start_time"]
                if "end_time" in event:
                    summary["end_time"] = event["end_time"]

        summary["phases_executed"] = seen_phases
        summary["total_cost"] = round(summary["total_cost"], 6)

        return summary

    @staticmethod
    def _normalize_timestamp(ts: str) -> str:
        """将 ChatDev 非标准时间戳转为 ISO 格式。

        输入: "2026-31-03 21:29:16"  (YYYY-DD-MM HH:MM:SS)
        输出: "2026-03-31T21:29:16"  (ISO 8601)
        """
        try:
            # ChatDev 的格式是: YYYY-DD-MM
            parts = ts.split()
            date_parts = parts[0].split("-")
            if len(date_parts) == 3:
                year, day, month = date_parts
                # 交换 day 和 month
                corrected = f"{year}-{month}-{day}"
                time_part = parts[1] if len(parts) > 1 else "00:00:00"
                return f"{corrected}T{time_part}"
        except (IndexError, ValueError):
            pass
        return ts
