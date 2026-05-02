"""
Test script for LLMSummarizer.

Reads playbooks from data/classified_chatdev_playbook/, summarizes them
via LLMSummarizer, and writes the results to examples/.

Usage:
    python notebooks/_test_llm_summarizer.py
"""

import json
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from chatdev.analyzer.llm_summarizer import LLMSummarizer


def main():
    print("=" * 60)
    print("LLMSummarizer 测试脚本")
    print("=" * 60)

    # ---- Pick two example playbooks ----
    playbooks = [
        (
            "data/classified_chatdev_playbook/0.0/ChatDev_ProgramDev2_GPT4o_0_playbook.json",
            "examples/ChatDev_ProgramDev2_GPT4o_0_summarized.json",
        ),
        (
            "data/classified_chatdev_playbook/1.1/ChatDev_ProgramDev2_GPT4o_5_playbook.json",
            "examples/ChatDev_ProgramDev2_GPT4o_5_summarized.json",
        ),
    ]

    summarizer = LLMSummarizer(max_retries=3)

    for src, dst in playbooks:
        src_path = os.path.join(_project_root, src)
        dst_path = os.path.join(_project_root, dst)

        if not os.path.exists(src_path):
            print(f"\n[SKIP] Input not found: {src_path}")
            continue

        print(f"\n{'─' * 60}")
        print(f"Input:  {src}")
        print(f"Output: {dst}")
        print(f"{'─' * 60}")

        try:
            result = summarizer.summarize_playbook(src_path, output_path=dst_path, verbose=True)
            _print_summary(result)
            print(f"[OK] Saved to {dst}")
        except Exception as e:
            print(f"[FAIL] {e}")

    print(f"\n{'=' * 60}")
    print(f"Stats: {summarizer.stats}")
    print("Done.")
    print(f"{'=' * 60}")


def _print_summary(result: dict):
    total_known = 0
    total_tasks = 0
    total_output_items = 0
    total_interactions = 0

    for role, interactions in result.items():
        if not isinstance(interactions, list):
            continue
        for ix, entry in enumerate(interactions):
            known_items = entry.get("known_context", [])
            task_items = entry.get("tasks", [])
            output_items = entry.get("output", [])
            total_known += len(known_items)
            total_tasks += len(task_items)
            total_output_items += len(output_items)
            total_interactions += 1

            print(f"  [{role}:{ix}] known_context={len(known_items)}, tasks={len(task_items)}, output={len(output_items)}")

    print(f"  --- Total: {total_interactions} interactions, "
          f"known_context={total_known}, tasks={total_tasks}, output={total_output_items}")


if __name__ == "__main__":
    main()
