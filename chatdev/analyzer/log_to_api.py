"""
log_to_api.py — Reconstruct api_records.jsonl from ChatDev .log files.

When api_records.jsonl is missing but a .log file exists, this module
reconstructs the API call records from parsed log events.  The output is
interface-compatible with convert_to_playbook.api_to_playbook() and
bug_detector.BugDetector.analyze_playbook().

Usage::

    from chatdev.analyzer.log_to_api import log_to_api_records

    api_path = log_to_api_records("path/to/chatdev.log")
    # → writes api_records.jsonl alongside the log

    # Or specify output path:
    api_path = log_to_api_records("path/to/chatdev.log", "output/api_records.jsonl")
"""

import json
import os
import re
import time as _time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from .parser import LogParser
from .event_types import EventType


# ============================================================================
#  Timestamp conversion
# ============================================================================

def _log_timestamp_to_epoch(ts: str) -> float:
    """Convert a ChatDev log timestamp to Unix epoch.

    Input formats handled:
      - "2026-31-03 21:29:16"  (YYYY-DD-MM HH:MM:SS — day/month swapped)
      - "2026-03-31T21:29:16"  (ISO 8601, already normalized by LogParser)
    """
    if not ts:
        return _time.time()

    ts_clean = ts.strip()
    try:
        if "T" in ts_clean:
            dt = datetime.fromisoformat(ts_clean)
        else:
            parts = ts_clean.split()
            date_part = parts[0]
            time_part = parts[1] if len(parts) > 1 else "00:00:00"
            dp = date_part.split("-")
            if len(dp) == 3:
                year, day, month = dp
                dt = datetime(int(year), int(month), int(day),
                              *map(int, time_part.split(":")))
            else:
                return _time.time()
        return dt.timestamp()
    except (ValueError, IndexError):
        return _time.time()


# ============================================================================
#  Placeholder substitution
# ============================================================================

def _substitute_placeholders(text: str, background_prompt: str, task_prompt: str) -> str:
    """Replace {chatdev_prompt} and {task} placeholders in prompt text."""
    if not text:
        return text
    result = text.replace("{chatdev_prompt}", background_prompt)
    result = result.replace("{task}", task_prompt)
    return result


# ============================================================================
#  Model & config extraction
# ============================================================================

_MODEL_TYPE_MAP = {
    "ModelType.GPT_4O": "gpt-4o",
    "ModelType.GPT_4O_MINI": "gpt-4o-mini",
    "ModelType.GPT_4_TURBO": "gpt-4-turbo",
    "ModelType.GPT_4": "gpt-4",
    "ModelType.GPT_3_5_TURBO": "gpt-3.5-turbo",
}


def _model_type_to_name(model_type: str) -> str:
    """Convert ModelType enum string to OpenAI model name."""
    if not model_type:
        return "gpt-4o"
    return _MODEL_TYPE_MAP.get(model_type.strip(), model_type.strip().lower())


def _parse_chatgpt_config(raw_text: str) -> Dict[str, Any]:
    """Parse ChatGPTConfig(...) string from preprocessing event into a dict."""
    config: Dict[str, Any] = {}
    if not raw_text:
        return config

    m = re.search(r"ChatGPTConfig\((.+)\)", raw_text, re.DOTALL)
    if not m:
        return config

    inner = m.group(1)
    for part in inner.split(","):
        part = part.strip()
        if "=" not in part:
            continue
        key, _, val = part.partition("=")
        key = key.strip()
        val = val.strip()

        if val == "None" or val == "null":
            config[key] = None
        elif val == "True":
            config[key] = True
        elif val == "False":
            config[key] = False
        elif val.startswith("'") and val.endswith("'"):
            config[key] = val[1:-1]
        elif val.startswith('"') and val.endswith('"'):
            config[key] = val[1:-1]
        elif val == "{}":
            config[key] = {}
        else:
            try:
                config[key] = int(val)
            except ValueError:
                try:
                    config[key] = float(val)
                except ValueError:
                    config[key] = val

    return config


# ============================================================================
#  Core: log → api_records.jsonl
# ============================================================================

def log_to_api_records(
    log_path: str,
    output_path: Optional[str] = None,
) -> str:
    """Generate api_records.jsonl from a ChatDev .log file.

    Parses the log, correlates agent_message/openai_usage events, reconstructs
    the full API input message array per call, and writes a JSONL file whose
    schema is compatible with ``convert_to_playbook.api_to_playbook()`` and
    ``bug_detector.BugDetector.analyze_playbook()``.

    Args:
        log_path:    Path to the .log file.
        output_path: Destination path for api_records.jsonl.
                     Default: ``<log_dir>/api_records.jsonl``.

    Returns:
        Absolute path to the generated api_records.jsonl.
    """
    log_path = os.path.abspath(log_path)
    if not os.path.isfile(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")

    # ---- 1. Parse the log ----
    parser = LogParser(skip_flask=True, skip_http=False)
    with open(log_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    entries = parser._split_entries(raw_text)
    events = parser._parse_all_entries(entries)

    # ---- 2. Extract global metadata ----
    metadata = _extract_global_metadata(events, raw_text)

    # ---- 3. Walk events phase-by-phase, building API records ----
    api_records = _build_api_records(events, metadata)

    # ---- 4. Write output ----
    if output_path is None:
        output_path = os.path.join(os.path.dirname(log_path), "api_records.jsonl")
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        for record in api_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return output_path


# ============================================================================
#  Internal helpers
# ============================================================================

def _extract_global_metadata(events: List[dict], raw_text: str) -> dict:
    """Extract model, config, and task info from preprocessing + raw log text."""
    meta: Dict[str, Any] = {
        "model": "gpt-4o",
        "config": {},
        "task_prompt": "",
        "background_prompt": (
            "ChatDev is a software company powered by multiple intelligent agents, "
            "such as chief executive officer, chief human resources officer, "
            "chief product officer, chief technology officer, etc, with a "
            "multi-agent organizational structure and the mission of "
            "'changing the digital world through programming'."
        ),
    }

    for event in events:
        if event.get("event_type") == EventType.PREPROCESSING.value:
            meta["task_prompt"] = event.get("task_prompt", "")

            raw_config = event.get("chatgpt_config", {})
            if not raw_config:
                raw_config = _parse_chatgpt_config(raw_text)
            meta["config"] = raw_config

            chatdev = event.get("chatdev_config", {})
            if "background_prompt" in chatdev:
                meta["background_prompt"] = chatdev["background_prompt"]

            break

    # Look for model_type in role_playing events
    for event in events:
        if event.get("event_type") == EventType.ROLE_PLAYING.value:
            params = event.get("parameters", {})
            mt = params.get("model_type", "")
            if mt:
                meta["model"] = _model_type_to_name(mt)

    return meta


def _build_api_records(events: List[dict], metadata: dict) -> List[dict]:
    """Walk parsed events and build api_records.jsonl entries.

    Tracks per-phase conversation context:
      - phase_name, assistant_role, user_role
      - assistant_prompt, user_prompt (with placeholder placeholders — resolved at
        record-build time using the phase's own background/task)
      - phase_prompt_text: the first user message, taken from the start_chat event
        (preserves original newlines, unlike the markdown-table version in chatting)
      - conversation: list of raw message texts accumulated in order

    For each agent_message event, reconstructs the full API input array
    using positional role alternation (matches the original ChatDev API behaviour).
    """
    records: List[dict] = []
    node_index = 0

    # Per-phase state — reset on each chatting event
    phase_ctx: dict = {}
    conversation: List[str] = []       # raw message texts, in chronological order
    usage_queue: List[dict] = []       # pending openai_usage events
    phase_bg: str = metadata["background_prompt"]
    phase_task: str = metadata["task_prompt"]

    model = metadata["model"]
    base_config = metadata["config"]

    for event in events:
        et = event.get("event_type", "")

        # ---- Phase start: chatting ----
        if et == EventType.CHATTING.value:
            params = event.get("parameters", {})
            phase_ctx = {
                "phase_name": event.get("phase_name", params.get("phase_name", "Unknown")),
                "assistant_role": event.get("assistant_role", params.get("assistant_role_name", "")),
                "user_role": event.get("user_role", params.get("user_role_name", "")),
                "phase_prompt_text": params.get("phase_prompt", ""),
                "assistant_prompt": params.get("assistant_role_prompt", ""),
                "user_prompt": params.get("user_role_prompt", ""),
            }
            conversation = []
            usage_queue = []
            continue

        # ---- Role playing: capture the phase's own bg/task + prompts ----
        if et == EventType.ROLE_PLAYING.value:
            if not phase_ctx:
                phase_ctx = {}
            rp = event.get("parameters", {})
            if not phase_ctx.get("assistant_role"):
                phase_ctx["assistant_role"] = event.get("assistant_role", rp.get("assistant_role_name", ""))
            if not phase_ctx.get("user_role"):
                phase_ctx["user_role"] = event.get("user_role", rp.get("user_role_name", ""))
            if rp.get("assistant_role_prompt"):
                phase_ctx["assistant_prompt"] = rp["assistant_role_prompt"]
            if rp.get("user_role_prompt"):
                phase_ctx["user_prompt"] = rp["user_role_prompt"]
            if rp.get("background_prompt"):
                phase_bg = rp["background_prompt"]
            if rp.get("task_prompt"):
                phase_task = rp["task_prompt"]
            if rp.get("model_type"):
                model = _model_type_to_name(rp["model_type"])
            continue

        # ---- Start chat: use its user_message as the high-fidelity phase prompt ----
        if et == EventType.START_CHAT.value:
            um = event.get("user_message", "")
            if um and phase_ctx:
                phase_ctx["phase_prompt_text"] = um
            continue

        # ---- Collect openai_usage events ----
        if et == EventType.OPENAI_USAGE.value:
            usage_queue.append(event)
            continue

        # ---- Agent message → build API record ----
        if et == EventType.AGENT_MESSAGE.value:
            if not phase_ctx:
                continue

            message_text = event.get("message", "") or ""

            # Determine which role is being called (produces this message)
            # Messages alternate: first in phase = assistant_role, then user_role, ...
            msg_index = len(conversation)
            called_role = (
                phase_ctx["assistant_role"] if (msg_index % 2 == 0)
                else phase_ctx["user_role"]
            )

            # Build the input message array
            input_messages = _build_input_messages(
                phase_ctx=phase_ctx,
                conversation=conversation,
                called_role=called_role,
                background_prompt=phase_bg,
                task_prompt=phase_task,
            )

            # Build output object (simplified OpenAI format)
            output_obj = {
                "choices": [{
                    "finish_reason": "stop",
                    "index": 0,
                    "message": {
                        "content": message_text,
                        "role": "assistant",
                    },
                }],
                "model": model,
                "usage": {},
            }

            # Match with openai_usage
            if usage_queue:
                ue = usage_queue.pop(0)
                output_obj["usage"] = {
                    "prompt_tokens": ue.get("prompt_tokens", 0),
                    "completion_tokens": ue.get("completion_tokens", 0),
                    "total_tokens": ue.get("total_tokens", 0),
                }

            ts = _log_timestamp_to_epoch(event.get("timestamp", ""))

            max_tokens_val = _estimate_max_tokens(
                base_config.get("max_tokens"), msg_index
            )
            record_config = dict(base_config)
            record_config["max_tokens"] = max_tokens_val

            record = {
                "timestamp": ts,
                "node_index": node_index,
                "model": model,
                "config": record_config,
                "input": input_messages,
                "output": output_obj,
            }
            records.append(record)
            node_index += 1

            # Append to conversation history
            conversation.append(message_text)

    return records


def _build_input_messages(
    phase_ctx: dict,
    conversation: List[str],
    called_role: str,
    background_prompt: str,
    task_prompt: str,
) -> List[Dict[str, str]]:
    """Build the API input message array for a given API call.

    After the system message, non-system roles alternate strictly by position::

        assistant_role calls → user, assistant, user, assistant, ...
        user_role calls      → assistant, user, assistant, user, ...

    The first non-system slot is always the phase prompt.  Subsequent slots
    are filled by conversation messages in chronological order.  This
    positional scheme matches how ChatDev RolePlaying constructs the
    messages array for each OpenAI call.
    """
    assistant_role = phase_ctx.get("assistant_role", "")
    user_role = phase_ctx.get("user_role", "")

    messages: List[Dict[str, str]] = []

    # 1. System prompt — the called role's system prompt
    if called_role == assistant_role:
        sys_prompt = phase_ctx.get("assistant_prompt", "")
    else:
        sys_prompt = phase_ctx.get("user_prompt", "")
    sys_prompt = _substitute_placeholders(sys_prompt, background_prompt, task_prompt)
    messages.append({"role": "system", "content": sys_prompt})

    # 2. Build the ordered list of non-system texts:
    #    [phase_prompt, convo_msg_0, convo_msg_1, ...]
    phase_text = phase_ctx.get("phase_prompt_text", "")
    # The start_chat user_message is already expanded; if we fell back to the
    # chatting table version it may still contain placeholders.
    phase_text = _substitute_placeholders(phase_text, background_prompt, task_prompt)
    # Also substitute {assistant_role} / {user_role} (present in some templates)
    phase_text = phase_text.replace("{assistant_role}", assistant_role)
    phase_text = phase_text.replace("{user_role}", user_role)

    all_texts = [phase_text] + list(conversation)

    # 3. Assign alternating roles
    if called_role == assistant_role:
        role_cycle = ["user", "assistant"]
    else:
        role_cycle = ["assistant", "user"]

    for idx, text in enumerate(all_texts):
        role = role_cycle[idx % 2]
        messages.append({"role": role, "content": text})

    return messages


def _estimate_max_tokens(base_max_tokens, msg_index: int) -> int:
    """Estimate max_tokens for an API call.

    In real api_records.jsonl, max_tokens decreases across turns because
    the prompt grows.  Returns a reasonable estimate.
    """
    if base_max_tokens is not None:
        return base_max_tokens

    return max(500, 3600 - msg_index * 60)


# ============================================================================
#  Convenience: batch processing
# ============================================================================

def log_to_api_records_batch(
    dir_path: str,
    output_dir: Optional[str] = None,
) -> List[str]:
    """Batch-convert all .log files under a directory.

    Recursively finds .log files, generates api_records.jsonl alongside each
    (or under output_dir preserving relative paths).

    Args:
        dir_path:   Top-level directory to search for .log files.
        output_dir: Optional output directory.  If None, writes alongside each log.

    Returns:
        List of paths to generated api_records.jsonl files.
    """
    dir_path = os.path.abspath(dir_path)
    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    log_files = []
    for root, _dirs, files in os.walk(dir_path):
        for fname in files:
            if fname.endswith(".log"):
                log_files.append(os.path.join(root, fname))
    log_files.sort()

    results = []
    for log_path in log_files:
        if output_dir:
            rel = os.path.relpath(log_path, dir_path)
            out_path = os.path.join(
                output_dir,
                os.path.splitext(rel)[0].replace(os.sep, "_") + "_api_records.jsonl",
            )
        else:
            out_path = None

        try:
            result = log_to_api_records(log_path, out_path)
            results.append(result)
            print(f"  [OK] {os.path.basename(log_path)}")
        except Exception as e:
            print(f"  [FAIL] {os.path.basename(log_path)}: {e}")

    print(f"\nGenerated {len(results)}/{len(log_files)} api_records.jsonl file(s)")
    return results
