"""
log_to_playbook.py — Convert ChatDev .log files directly to playbook.json.

Combines log_to_api (log → api_records.jsonl) and convert_to_playbook
(api_records.jsonl + parsed log → playbook) into a single call.
When a .log file exists but api_records.jsonl is missing, this module
produces a playbook of equivalent fidelity to the two-step pipeline.

Usage::

    from chatdev.analyzer.log_to_playbook import log_to_playbook

    pb_path = log_to_playbook("path/to/chatdev.log")
    # → writes <name>_playbook.json alongside the log

    # Also return the playbook dict:
    pb_path, playbook = log_to_playbook("path/to/chatdev.log", return_dict=True)
"""

import json
import os
from typing import Dict, Any, Optional, Tuple

from .parser import LogParser
from .log_to_api import log_to_api_records
from .convert_to_playbook import api_to_playbook


def log_to_playbook(
    log_path: str,
    output_path: Optional[str] = None,
    keep_api_records: bool = True,
    return_dict: bool = False,
) -> str:
    """Convert a ChatDev .log file directly to a playbook.json.

    Internally::

        1. Parses the log (or reuses cached parsed JSON).
        2. Generates api_records.jsonl via :func:`log_to_api_records`.
        3. Builds playbook via :func:`api_to_playbook`.

    The generated playbook is compatible with
    :class:`bug_detector.BugDetector.analyze_playbook`.

    Args:
        log_path:          Path to the .log file.
        output_path:       Destination path for the playbook JSON.
                           Default: ``<log_dir>/<name>_playbook.json``.
        keep_api_records:  If True, keep the intermediate api_records.jsonl
                           alongside the log.  If False, delete it after
                           the playbook is built.
        return_dict:       If True, also return the playbook dict.

    Returns:
        If ``return_dict`` is False: path to the generated playbook JSON.
        If ``return_dict`` is True:  ``(path, playbook_dict)``.
    """
    log_path = os.path.abspath(log_path)
    if not os.path.isfile(log_path):
        raise FileNotFoundError(f"Log file not found: {log_path}")

    log_dir = os.path.dirname(log_path)
    log_name = os.path.splitext(os.path.basename(log_path))[0]

    # ---- 1. Ensure parsed JSON exists ----
    parsed_json_path = os.path.join(log_dir, f"{log_name}.json")
    if not os.path.exists(parsed_json_path):
        parser = LogParser(skip_flask=True, skip_http=False)
        parser.parse(log_path, parsed_json_path)

    # ---- 2. Generate api_records.jsonl ----
    api_path = os.path.join(log_dir, "api_records.jsonl")
    if not os.path.exists(api_path):
        log_to_api_records(log_path, api_path)

    # ---- 3. Build playbook ----
    if output_path is None:
        output_path = os.path.join(log_dir, f"{log_name}_playbook.json")
    output_path = os.path.abspath(output_path)

    api_to_playbook(api_path, parsed_json_path, output_path)

    # ---- 4. Optionally clean up intermediate api_records.jsonl ----
    if not keep_api_records and os.path.exists(api_path):
        os.remove(api_path)

    if return_dict:
        with open(output_path, "r", encoding="utf-8") as f:
            playbook = json.load(f)
        return output_path, playbook

    return output_path


def log_to_playbook_batch(
    dir_path: str,
    output_dir: Optional[str] = None,
    keep_api_records: bool = True,
) -> list:
    """Batch-convert all .log files under a directory to playbook.json.

    Args:
        dir_path:          Top-level directory to search for .log files.
        output_dir:        Optional output directory for playbook files.
        keep_api_records:  Keep intermediate api_records.jsonl files?

    Returns:
        List of paths to generated playbook JSON files.
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
        log_name = os.path.splitext(os.path.basename(log_path))[0]
        log_dir = os.path.dirname(log_path)

        if output_dir:
            out_path = os.path.join(output_dir, f"{log_name}_playbook.json")
        else:
            out_path = os.path.join(log_dir, f"{log_name}_playbook.json")

        try:
            result = log_to_playbook(
                log_path, out_path, keep_api_records=keep_api_records
            )
            results.append(result)
            print(f"  [OK] {os.path.basename(log_path)}")
        except Exception as e:
            print(f"  [FAIL] {os.path.basename(log_path)}: {e}")

    print(f"\nGenerated {len(results)}/{len(log_files)} playbook(s)")
    return results
