"""Compact reproduction runner for the classified ChatDev scoring pipeline.

The runner intentionally keeps project-specific logic here and delegates model
judging, playbook conversion, and visualization work to ``chatdev.analyzer``.
By default, API-calling stages only reuse existing artifacts. Pass
``--run-api-steps`` to regenerate summarization or scoring outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


REPRO_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = REPRO_DIR.parent
CONFIG_PATH = REPRO_DIR / "config.json"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chatdev.analyzer.consistency_visualizer import write_visualization_report
from chatdev.analyzer.llm_summarizer import LLMSummarizer
from chatdev.analyzer.log_to_playbook import log_to_playbook
from chatdev.analyzer.logprob_consistency import (
    _default_client,
    aggregate_scores,
    chatdev_filename_sort_key,
    load_user_task_map,
    normalize_premise_order,
)


ALL_STEPS = [
    "playbook",
    "summarize",
    "scored",
    "scored_1",
    "scored_2",
    "scored_3",
    "scored_4",
    "visualize",
    "overview",
]
API_STEPS = {"summarize", "scored", "scored_1", "scored_3", "scored_4"}
POSITIVE_TOKENS = {"yes", " yes", "y", " y", "yes.", " true", "true"}
NEGATIVE_TOKENS = {"no", " no", "n", " n", "no.", " false", "false"}


@dataclass
class Paths:
    source_root: Path
    dataset_json: Path
    playbook_root: Path
    api_record_root: Path
    summarized_root: Path
    overview_dir: Path


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--steps", nargs="+", choices=ALL_STEPS, default=ALL_STEPS)
    parser.add_argument("--run-api-steps", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--max-workers", type=int, default=None)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    paths = load_paths(config)
    max_workers = args.max_workers or int(config.get("max_workers", 10))

    print(f"Project root: {PROJECT_ROOT}")
    print(f"API steps enabled: {args.run_api_steps}")
    print(f"Steps: {', '.join(args.steps)}")

    if "playbook" in args.steps:
        build_playbook_dataset(paths, overwrite=args.overwrite)

    if "summarize" in args.steps:
        ensure_api_allowed("summarize", args.run_api_steps)
        build_summarized_dataset(
            paths,
            model=str(config.get("summarizer_model", "gpt-4o")),
            overwrite=args.overwrite,
            run_api=args.run_api_steps,
        )

    scored_configs = config["scored_datasets"]
    for step, dataset_key in [
        ("scored", "classified_chatdev_scored"),
        ("scored_1", "classified_chatdev_scored_1"),
    ]:
        if step in args.steps:
            ensure_api_allowed(step, args.run_api_steps)
            build_logprob_scored_dataset(
                paths,
                scored_configs[dataset_key],
                model=str(config.get("default_model", "gpt-4o-mini")),
                top_logprobs=int(config.get("top_logprobs", 5)),
                overwrite=args.overwrite,
                run_api=args.run_api_steps,
                max_workers=max_workers,
            )

    if "scored_2" in args.steps:
        build_scored_2(config)

    for step, dataset_key in [
        ("scored_3", "classified_chatdev_scored_3"),
        ("scored_4", "classified_chatdev_scored_4"),
    ]:
        if step in args.steps:
            ensure_api_allowed(step, args.run_api_steps)
            build_action_reasoning_dataset(
                paths,
                scored_configs[dataset_key],
                model=str(config.get("default_model", "gpt-4o-mini")),
                top_logprobs=int(config.get("top_logprobs", 5)),
                overwrite=args.overwrite,
                run_api=args.run_api_steps,
                max_workers=max_workers,
            )

    if "visualize" in args.steps:
        build_visualizations(scored_configs)

    if "overview" in args.steps:
        write_overview(paths.overview_dir, scored_configs)

    return 0


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_paths(config: Dict[str, Any]) -> Paths:
    return Paths(
        source_root=resolve_project_path(config["source_root"]),
        dataset_json=resolve_project_path(config["dataset_json"]),
        playbook_root=resolve_project_path(config["playbook_root"]),
        api_record_root=resolve_project_path(config["api_record_root"]),
        summarized_root=resolve_project_path(config["summarized_root"]),
        overview_dir=resolve_project_path(config["overview_dir"]),
    )


def resolve_project_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def ensure_api_allowed(step: str, run_api: bool) -> None:
    if not run_api:
        print(f"[{step}] API-calling step is in reuse-only mode")


def build_playbook_dataset(paths: Paths, overwrite: bool) -> None:
    source_root = paths.source_root
    trajectory_dir = source_root / "trajectory"
    playbook_traj = paths.playbook_root / "trajectory"
    api_traj = paths.api_record_root / "trajectory"
    playbook_traj.mkdir(parents=True, exist_ok=True)
    api_traj.mkdir(parents=True, exist_ok=True)

    log_files = sorted(trajectory_dir.glob("*.log"), key=lambda path: chatdev_filename_sort_key(path.name))
    category_map = collect_category_map(source_root)
    print(f"[playbook] logs={len(log_files)}, labelled stems={len(category_map)}")

    success = 0
    for index, log_path in enumerate(log_files, start=1):
        name = log_path.stem
        pb_out = playbook_traj / f"{name}_playbook.json"
        api_out = api_traj / f"{name}_api_records.jsonl"
        if pb_out.exists() and api_out.exists() and not overwrite:
            success += 1
            continue

        log_to_playbook(str(log_path), output_path=str(pb_out), keep_api_records=True)
        default_api = log_path.parent / "api_records.jsonl"
        if default_api.exists():
            shutil.move(str(default_api), str(api_out))
        success += 1
        if index == len(log_files) or index % 20 == 0:
            print(f"[playbook] {index}/{len(log_files)}")

    distribute_by_category(paths.playbook_root, paths.api_record_root, category_map)
    write_json(
        paths.playbook_root / "_manifest.json",
        {
            "source_root": str(source_root),
            "playbook_root": str(paths.playbook_root),
            "api_record_root": str(paths.api_record_root),
            "trajectory_logs": len(log_files),
            "trajectory_playbooks": success,
            "categories": sorted({cat for cats in category_map.values() for cat in cats}),
            "updated_at": timestamp(),
        },
    )
    print(f"[playbook] done -> {paths.playbook_root}")


def collect_category_map(source_root: Path) -> Dict[str, List[str]]:
    category_map: Dict[str, List[str]] = defaultdict(list)
    for label_dir in sorted(source_root.iterdir(), key=lambda path: path.name):
        if not label_dir.is_dir() or label_dir.name == "trajectory" or label_dir.name.startswith("_"):
            continue
        for path in sorted(label_dir.glob("*.json")):
            category_map[path.stem].append(label_dir.name)
    return dict(category_map)


def distribute_by_category(playbook_root: Path, api_record_root: Path, category_map: Dict[str, List[str]]) -> None:
    playbook_traj = playbook_root / "trajectory"
    api_traj = api_record_root / "trajectory"
    for stem, labels in category_map.items():
        for label in labels:
            label_pb_dir = playbook_root / label
            label_api_dir = api_record_root / label
            label_pb_dir.mkdir(parents=True, exist_ok=True)
            label_api_dir.mkdir(parents=True, exist_ok=True)
            src_pb = playbook_traj / f"{stem}_playbook.json"
            src_api = api_traj / f"{stem}_api_records.jsonl"
            if src_pb.exists():
                shutil.copy2(src_pb, label_pb_dir / src_pb.name)
            if src_api.exists():
                shutil.copy2(src_api, label_api_dir / src_api.name)


def build_summarized_dataset(paths: Paths, model: str, overwrite: bool, run_api: bool) -> None:
    source_paths = discover_playbook_paths(paths.playbook_root)
    output_root = paths.summarized_root
    output_root.mkdir(parents=True, exist_ok=True)
    cache: Dict[str, Path] = {}
    jobs = []

    for src_path in source_paths:
        dst_path = summarized_output_path(src_path, paths.playbook_root, output_root)
        if dst_path.exists() and not overwrite:
            cache.setdefault(src_path.name, dst_path)
            continue
        if src_path.name in cache and cache[src_path.name].exists():
            copy_json(cache[src_path.name], dst_path)
            continue
        jobs.append((src_path, dst_path))

    if jobs and not run_api:
        raise RuntimeError(
            f"[summarize] {len(jobs)} summarized files are missing. "
            "Run again with --run-api-steps to generate them."
        )

    summarizer = LLMSummarizer(model=model)
    for index, (src_path, dst_path) in enumerate(jobs, start=1):
        summarizer.summarize_playbook(str(src_path), output_path=str(dst_path), verbose=False)
        cache[src_path.name] = dst_path
        print(f"[summarize] {index}/{len(jobs)} {src_path.name}")

    write_json(
        output_root / "_manifest.json",
        {
            "input_root": str(paths.playbook_root),
            "output_root": str(output_root),
            "model": model,
            "num_inputs": len(source_paths),
            "num_missing_generated": len(jobs),
            "api_stats": getattr(summarizer, "_stats", {}),
            "updated_at": timestamp(),
        },
    )
    print(f"[summarize] done -> {output_root}")


def discover_playbook_paths(root: Path) -> List[Path]:
    return sorted(
        (path for path in root.rglob("*_playbook.json") if not path.relative_to(root).parts[0].startswith("_")),
        key=lambda path: (path.relative_to(root).parts[0], chatdev_filename_sort_key(path.name)),
    )


def summarized_output_path(src_path: Path, input_root: Path, output_root: Path) -> Path:
    rel = src_path.relative_to(input_root)
    name = rel.name.replace("_playbook.json", "_summarized.json")
    return output_root / rel.parent / name


def build_logprob_scored_dataset(
    paths: Paths,
    dataset_config: Dict[str, Any],
    model: str,
    top_logprobs: int,
    overwrite: bool,
    run_api: bool,
    max_workers: int,
) -> None:
    from chatdev.analyzer.logprob_consistency import LogprobConsistencyScorer

    output_root = resolve_project_path(dataset_config["output_root"])
    premise_order = list(normalize_premise_order(dataset_config.get("premise_order")))
    target_labels = optional_label_set(dataset_config.get("target_labels"))
    write_policy = str(dataset_config.get("write_policy", "all_paths"))
    selected_paths = select_summarized_paths(paths.summarized_root, target_labels, write_policy)
    filename_groups = group_paths_by_filename(selected_paths)
    user_task_map = load_user_task_map(str(paths.dataset_json), str(paths.playbook_root / "trajectory"))

    jobs = []
    actions: Dict[str, str] = {}
    filename_to_scored: Dict[str, Path] = {}
    for filename, group in filename_groups.items():
        canonical_src = group[0]
        canonical_dst = scored_output_path(canonical_src, paths.summarized_root, output_root)
        reusable = find_reusable_logprob_output(group, paths.summarized_root, output_root, premise_order)
        if reusable and not overwrite:
            copy_json(reusable, canonical_dst)
            filename_to_scored[filename] = canonical_dst
            actions[filename] = "copied_existing"
        else:
            jobs.append((filename, canonical_src, canonical_dst))

    if jobs and not run_api:
        print(
            f"[{output_root.name}] reuse-only: {len(jobs)} scored files are missing or stale; "
            "leave them marked in the manifest. Use --run-api-steps to regenerate."
        )
        for filename, _src, _dst in jobs:
            actions[filename] = "missing_api_required"
        jobs = []

    def score_job(src_path: Path, dst_path: Path) -> Dict[str, int]:
        scorer = LogprobConsistencyScorer(model=model, top_logprobs=top_logprobs, premise_order=premise_order)
        scorer.score_summarized_json(
            str(src_path),
            str(dst_path),
            user_task_map=user_task_map,
            premise_order=premise_order,
        )
        return scorer.stats

    worker_stats: List[Dict[str, int]] = []
    if jobs:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(score_job, src, dst): (filename, src, dst)
                for filename, src, dst in jobs
            }
            for completed, future in enumerate(as_completed(future_to_job), start=1):
                filename, _src, dst = future_to_job[future]
                worker_stats.append(future.result())
                filename_to_scored[filename] = dst
                actions[filename] = "scored"
                print(f"[{output_root.name}] {completed}/{len(jobs)} {filename}")

    records = []
    labels_by_filename = collect_filename_labels(discover_summarized_paths(paths.summarized_root), paths.summarized_root)
    for filename, group in filename_groups.items():
        canonical_dst = filename_to_scored.get(filename) or scored_output_path(group[0], paths.summarized_root, output_root)
        for duplicate_src in group[1:]:
            duplicate_dst = scored_output_path(duplicate_src, paths.summarized_root, output_root)
            if canonical_dst.exists() and (overwrite or not has_logprob_premise_order(duplicate_dst, premise_order)):
                copy_json(canonical_dst, duplicate_dst)
        records.append(build_manifest_record(filename, group, labels_by_filename, target_labels, paths.summarized_root, output_root, actions.get(filename)))

    write_json(
        output_root / "_manifest.json",
        {
            "input_root": str(paths.summarized_root),
            "output_root": str(output_root),
            "dataset_json": str(paths.dataset_json),
            "trajectory_dir": str(paths.playbook_root / "trajectory"),
            "model": model,
            "top_logprobs": top_logprobs,
            "premise_order": premise_order,
            "target_labels": sorted(target_labels) if target_labels else None,
            "write_policy": write_policy,
            "selected_summarized_files": len(selected_paths),
            "selected_unique_filenames": len(filename_groups),
            "worker_stats": merge_stats(worker_stats),
            "updated_at": timestamp(),
            "records": records,
        },
    )
    write_label_score_summary(output_root, selected_paths, paths.summarized_root, metric_prefix="consistency_score")
    print(f"[{output_root.name}] done -> {output_root}")


def build_scored_2(config: Dict[str, Any]) -> None:
    script = PROJECT_ROOT / "scripts" / "build_classified_chatdev_scored_2.py"
    if not script.exists():
        raise FileNotFoundError(script)
    print("[scored_2] delegating to scripts/build_classified_chatdev_scored_2.py")
    subprocess.run([sys.executable, str(script)], cwd=str(PROJECT_ROOT), check=True)


def build_action_reasoning_dataset(
    paths: Paths,
    dataset_config: Dict[str, Any],
    model: str,
    top_logprobs: int,
    overwrite: bool,
    run_api: bool,
    max_workers: int,
) -> None:
    output_root = resolve_project_path(dataset_config["output_root"])
    premise_order = list(normalize_premise_order(dataset_config.get("premise_order")))
    target_labels = optional_label_set(dataset_config.get("target_labels"))
    write_policy = str(dataset_config.get("write_policy", "filename_hit_all_paths"))
    selected_paths = select_summarized_paths(paths.summarized_root, target_labels, write_policy)
    filename_groups = group_paths_by_filename(selected_paths)
    output_root.mkdir(parents=True, exist_ok=True)

    jobs = []
    actions: Dict[str, str] = {}
    filename_to_scored: Dict[str, Path] = {}
    for filename, group in filename_groups.items():
        canonical_src = group[0]
        canonical_dst = scored_output_path(canonical_src, paths.summarized_root, output_root)
        reusable = find_reusable_action_output(group, paths.summarized_root, output_root, premise_order)
        if reusable and not overwrite:
            copy_json(reusable, canonical_dst)
            filename_to_scored[filename] = canonical_dst
            actions[filename] = "copied_existing"
        else:
            jobs.append((filename, canonical_src, canonical_dst))

    if jobs and not run_api:
        print(
            f"[{output_root.name}] reuse-only: {len(jobs)} action-reasoning files are missing or stale; "
            "leave them marked in the manifest. Use --run-api-steps to regenerate."
        )
        for filename, _src, _dst in jobs:
            actions[filename] = "missing_api_required"
        jobs = []

    def score_job(src_path: Path, dst_path: Path) -> Dict[str, int]:
        scorer = ActionReasoningAlignmentScorer(model=model, top_logprobs=top_logprobs, premise_order=premise_order)
        scorer.score_summarized_json(src_path, dst_path)
        return scorer.stats

    worker_stats: List[Dict[str, int]] = []
    if jobs:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_job = {
                executor.submit(score_job, src, dst): (filename, src, dst)
                for filename, src, dst in jobs
            }
            for completed, future in enumerate(as_completed(future_to_job), start=1):
                filename, _src, dst = future_to_job[future]
                worker_stats.append(future.result())
                filename_to_scored[filename] = dst
                actions[filename] = "scored"
                print(f"[{output_root.name}] {completed}/{len(jobs)} {filename}")

    records = []
    labels_by_filename = collect_filename_labels(discover_summarized_paths(paths.summarized_root), paths.summarized_root)
    for filename, group in filename_groups.items():
        canonical_dst = filename_to_scored.get(filename) or scored_output_path(group[0], paths.summarized_root, output_root)
        for duplicate_src in group[1:]:
            duplicate_dst = scored_output_path(duplicate_src, paths.summarized_root, output_root)
            if canonical_dst.exists() and (overwrite or not has_action_definition(duplicate_dst, premise_order)):
                copy_json(canonical_dst, duplicate_dst)
        records.append(build_manifest_record(filename, group, labels_by_filename, target_labels, paths.summarized_root, output_root, actions.get(filename)))

    write_json(
        output_root / "_manifest.json",
        {
            "input_root": str(paths.summarized_root),
            "output_root": str(output_root),
            "model": model,
            "top_logprobs": top_logprobs,
            "scoring_definition": "action_reasoning_mismatch",
            "scoring_version": "action_reasoning_alignment_v1",
            "premise_order": premise_order,
            "action_fields": ["output"],
            "target_labels": sorted(target_labels) if target_labels else None,
            "write_policy": write_policy,
            "selected_summarized_files": len(selected_paths),
            "selected_unique_filenames": len(filename_groups),
            "worker_stats": merge_stats(worker_stats),
            "updated_at": timestamp(),
            "records": records,
        },
    )
    write_action_label_summary(output_root, selected_paths, paths.summarized_root, premise_order)
    print(f"[{output_root.name}] done -> {output_root}")


class ActionReasoningAlignmentScorer:
    def __init__(self, model: str, top_logprobs: int, premise_order: Sequence[str]) -> None:
        self.client = _default_client()
        self.model = model
        self.top_logprobs = top_logprobs
        self.premise_order = list(premise_order)
        self.stats = {"api_calls": 0, "scored_outputs": 0, "errors": 0}

    def score_summarized_json(self, input_path: Path, output_path: Path) -> Dict[str, Any]:
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        result = {}
        for role, interactions in payload.items():
            if not isinstance(interactions, list):
                result[role] = interactions
                continue
            result[role] = [
                self.score_entry(entry) if isinstance(entry, dict) else entry
                for entry in interactions
            ]
        write_json(output_path, result)
        return result

    def score_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        scored = json.loads(json.dumps(entry, ensure_ascii=False))
        reasoning_items: List[str] = []
        for key in self.premise_order:
            reasoning_items.extend(str(item) for item in (scored.get(key) or []) if str(item).strip())
        item_scores = []
        for action_item in scored.get("output") or []:
            item_scores.append({"actual_action": action_item, **self.score_action(reasoning_items, str(action_item))})
        scored["scoring_context"] = {
            "scoring_definition": "action_reasoning_mismatch",
            "scoring_version": "action_reasoning_alignment_v1",
            "premise_order": self.premise_order,
            "action_fields": ["output"],
            "reasoning_field_mapping": {"reasoning_process": self.premise_order, "actual_action": "output"},
            "judge_rule": "Yes iff the actual action is consistent with or reasonably advances the reasoning/task context; No iff it diverges from, contradicts, reverses, or ignores that context.",
        }
        scored["output_action_reasoning_alignment_scores"] = item_scores
        aggregates = aggregate_scores([item["score"] for item in item_scores])
        scored["action_reasoning_alignment_score_mean"] = aggregates["consistency_score_mean"]
        scored["action_reasoning_alignment_score_min"] = aggregates["consistency_score_min"]
        scored["action_reasoning_alignment_score_max"] = aggregates["consistency_score_max"]
        return scored

    def score_action(self, reasoning_items: Sequence[str], action_item: str) -> Dict[str, Any]:
        if not action_item.strip():
            return empty_binary_score()
        prompt = build_action_reasoning_prompt(reasoning_items, action_item)
        self.stats["api_calls"] += 1
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1,
                temperature=0.0,
                logprobs=True,
                top_logprobs=self.top_logprobs,
            )
        except Exception:
            self.stats["errors"] += 1
            raise
        self.stats["scored_outputs"] += 1
        return parse_binary_response(response)


def build_action_reasoning_prompt(reasoning_items: Sequence[str], action_item: str) -> str:
    reasoning_text = "\n".join(f"R{i}. {item}" for i, item in enumerate(reasoning_items, start=1))
    if not reasoning_text.strip():
        reasoning_text = "No explicit reasoning, decision state, or task context is available."
    return f"""You are a strict binary judge for action-reasoning alignment.

Definition: A good action-reasoning alignment means the ACTUAL_ACTION is supported by, consistent with, or a reasonable continuation of the REASONING_AND_TASK_CONTEXT. A 2.6 Action-Reasoning Mismatch exists when the actual action diverges from, contradicts, reverses, or ignores that context in a way that can cause unexpected or undesirable behavior.

Decision rule:
1. Answer "Yes" if the ACTUAL_ACTION is supported by, consistent with, or a reasonable continuation of the REASONING_AND_TASK_CONTEXT.
2. Answer "Yes" if the action implements, documents, verifies, or concretely advances one of the listed tasks without contradicting the known context.
3. Answer "No" if the action contradicts, reverses, replaces, or is disconnected from an important point in the context.
4. Answer "No" if the context establishes one modality, language, interface, requirement, plan, or constraint, but the action implements a materially different one.
5. Do not penalize an action merely because it adds reasonable implementation detail.

Output exactly one word: "Yes" or "No".
Do not output punctuation, explanations, or extra text.

REASONING_AND_TASK_CONTEXT:
{reasoning_text}

ACTUAL_ACTION:
{action_item}

Answer:"""


def parse_binary_response(response: Any) -> Dict[str, Any]:
    token_data = response.choices[0].logprobs.content[0]
    generated_token = getattr(token_data, "token", "") or ""
    generated_token_logprob = getattr(token_data, "logprob", None)
    top_logprobs = [candidate_to_dict(candidate) for candidate in (token_data.top_logprobs or [])]
    if generated_token and generated_token_logprob is not None:
        normalized = generated_token.lower()
        if not any(item["token"].lower() == normalized for item in top_logprobs):
            logprob = float(generated_token_logprob)
            top_logprobs.append({"token": generated_token, "logprob": logprob, "probability": safe_exp(logprob)})
    positive_probability = sum(item["probability"] for item in top_logprobs if item["token"].lower() in POSITIVE_TOKENS and item["probability"] is not None)
    negative_probability = sum(item["probability"] for item in top_logprobs if item["token"].lower() in NEGATIVE_TOKENS and item["probability"] is not None)
    return {
        "score": clamp(positive_probability),
        "generated_token": generated_token,
        "generated_token_logprob": generated_token_logprob,
        "generated_token_probability": safe_exp(generated_token_logprob),
        "positive_probability": clamp(positive_probability),
        "negative_probability": clamp(negative_probability),
        "top_logprobs": top_logprobs,
    }


def build_visualizations(scored_configs: Dict[str, Dict[str, Any]]) -> None:
    for name, dataset_config in scored_configs.items():
        output_root = resolve_project_path(dataset_config["output_root"])
        if not output_root.exists():
            print(f"[visualize] skip missing {output_root}")
            continue
        if dataset_config.get("kind") == "action_reasoning_alignment":
            print(f"[visualize] skip {name}: action-reasoning scores use _label_score_summary only")
            continue
        try:
            report = write_visualization_report(scored_root=output_root, output_dir=output_root / "_visualizations")
            print(f"[visualize] {name}: records={report.get('num_records')}, out={report.get('output_dir')}")
        except Exception as exc:
            print(f"[visualize] {name}: failed: {exc}")


def write_overview(overview_dir: Path, scored_configs: Dict[str, Dict[str, Any]]) -> None:
    overview_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, dataset_config in scored_configs.items():
        root = resolve_project_path(dataset_config["output_root"])
        manifest = read_json_if_exists(root / "_manifest.json")
        label_summary = root / "_label_score_summary.csv"
        vis_dir = root / "_visualizations"
        rows.append(
            {
                "dataset": name,
                "kind": dataset_config.get("kind"),
                "output_root": str(root.relative_to(PROJECT_ROOT)) if root.is_relative_to(PROJECT_ROOT) else str(root),
                "exists": root.exists(),
                "scored_files": count_files(root, "*_scored.json"),
                "visualization_files": count_visualization_files(vis_dir),
                "manifest": (root / "_manifest.json").exists(),
                "label_summary": label_summary.exists(),
                "target_labels": ",".join(dataset_config.get("target_labels") or []),
                "premise_order": ",".join(dataset_config.get("premise_order") or []),
                "selected_unique_filenames": manifest.get("selected_unique_filenames") if manifest else "",
                "selected_summarized_files": manifest.get("selected_summarized_files") if manifest else "",
            }
        )
    csv_path = overview_dir / "overview.csv"
    md_path = overview_dir / "overview.md"
    write_csv(csv_path, rows)
    write_markdown_table(md_path, rows)
    print(f"[overview] {csv_path}")
    print(f"[overview] {md_path}")


def select_summarized_paths(input_root: Path, target_labels: Optional[set[str]], write_policy: str) -> List[Path]:
    all_paths = discover_summarized_paths(input_root)
    if target_labels is None:
        return all_paths
    if write_policy == "target_label_paths_only":
        return [path for path in all_paths if summarized_label(path, input_root) in target_labels]
    labels_by_filename = collect_filename_labels(all_paths, input_root)
    return [path for path in all_paths if labels_by_filename.get(path.name, set()) & target_labels]


def discover_summarized_paths(input_root: Path) -> List[Path]:
    return sorted(
        (path for path in input_root.rglob("*_summarized.json") if not path.relative_to(input_root).parts[0].startswith("_")),
        key=lambda path: (path.relative_to(input_root).parts[0], chatdev_filename_sort_key(path.name)),
    )


def group_paths_by_filename(paths: Iterable[Path]) -> Dict[str, List[Path]]:
    groups: Dict[str, List[Path]] = defaultdict(list)
    for path in paths:
        groups[path.name].append(path)
    return dict(sorted(groups.items(), key=lambda item: chatdev_filename_sort_key(item[0])))


def collect_filename_labels(paths: Iterable[Path], input_root: Path) -> Dict[str, set[str]]:
    labels: Dict[str, set[str]] = defaultdict(set)
    for path in paths:
        labels[path.name].add(summarized_label(path, input_root))
    return dict(labels)


def summarized_label(path: Path, input_root: Path) -> str:
    return path.relative_to(input_root).parts[0]


def scored_output_path(src_path: Path, input_root: Path, output_root: Path) -> Path:
    rel = src_path.relative_to(input_root)
    name = rel.name.replace("_summarized.json", "_scored.json")
    return output_root / rel.parent / name


def optional_label_set(labels: Any) -> Optional[set[str]]:
    if labels is None:
        return None
    return {str(label) for label in labels}


def find_reusable_logprob_output(paths: Sequence[Path], input_root: Path, output_root: Path, premise_order: Sequence[str]) -> Optional[Path]:
    for path in paths:
        candidate = scored_output_path(path, input_root, output_root)
        if has_logprob_premise_order(candidate, premise_order):
            return candidate
    return None


def find_reusable_action_output(paths: Sequence[Path], input_root: Path, output_root: Path, premise_order: Sequence[str]) -> Optional[Path]:
    for path in paths:
        candidate = scored_output_path(path, input_root, output_root)
        if has_action_definition(candidate, premise_order):
            return candidate
    return None


def has_logprob_premise_order(path: Path, premise_order: Sequence[str]) -> bool:
    data = read_json_if_exists(path)
    if not isinstance(data, dict):
        return False
    for interactions in data.values():
        if not isinstance(interactions, list):
            continue
        for entry in interactions:
            if not isinstance(entry, dict):
                continue
            if entry.get("scoring_context", {}).get("premise_order") != list(premise_order):
                return False
            if "output_consistency_scores" in entry:
                return True
    return False


def has_action_definition(path: Path, premise_order: Sequence[str]) -> bool:
    data = read_json_if_exists(path)
    if not isinstance(data, dict):
        return False
    for interactions in data.values():
        if not isinstance(interactions, list):
            continue
        for entry in interactions:
            if not isinstance(entry, dict):
                continue
            context = entry.get("scoring_context") or {}
            if context.get("scoring_definition") != "action_reasoning_mismatch":
                return False
            if context.get("scoring_version") != "action_reasoning_alignment_v1":
                return False
            if context.get("premise_order") != list(premise_order):
                return False
            if "output_action_reasoning_alignment_scores" in entry:
                return True
    return False


def build_manifest_record(
    filename: str,
    group: Sequence[Path],
    labels_by_filename: Dict[str, set[str]],
    target_labels: Optional[set[str]],
    input_root: Path,
    output_root: Path,
    action: Optional[str],
) -> Dict[str, Any]:
    labels = labels_by_filename.get(filename, set())
    return {
        "filename": filename,
        "labels": sorted(labels),
        "target_label_hit": sorted(labels & target_labels) if target_labels else [],
        "action": action or "reused",
        "canonical_input": str(group[0].relative_to(input_root)),
        "canonical_output": str(scored_output_path(group[0], input_root, output_root).relative_to(output_root)),
        "path_count": len(group),
        "outputs": [str(scored_output_path(path, input_root, output_root).relative_to(output_root)) for path in group],
    }


def write_label_score_summary(output_root: Path, selected_paths: Sequence[Path], input_root: Path, metric_prefix: str) -> None:
    rows_by_label: Dict[str, Dict[str, Any]] = {}
    for src_path in selected_paths:
        scored_path = scored_output_path(src_path, input_root, output_root)
        payload = read_json_if_exists(scored_path)
        if not isinstance(payload, dict):
            continue
        label = scored_path.relative_to(output_root).parts[0]
        row = rows_by_label.setdefault(label, {"label": label, "files": 0, "entries": 0, "outputs": 0, "entry_score_sum": 0.0, "output_score_sum": 0.0})
        row["files"] += 1
        for interactions in payload.values():
            if not isinstance(interactions, list):
                continue
            for entry in interactions:
                if not isinstance(entry, dict):
                    continue
                entry_mean = entry.get(f"{metric_prefix}_mean")
                if isinstance(entry_mean, (int, float)):
                    row["entries"] += 1
                    row["entry_score_sum"] += float(entry_mean)
                for item in entry.get("output_consistency_scores") or []:
                    score = item.get("score") if isinstance(item, dict) else None
                    if isinstance(score, (int, float)):
                        row["outputs"] += 1
                        row["output_score_sum"] += float(score)
    rows = []
    for row in rows_by_label.values():
        rows.append({
            "label": row["label"],
            "files": row["files"],
            "entries": row["entries"],
            "outputs": row["outputs"],
            "entry_score_mean": row["entry_score_sum"] / row["entries"] if row["entries"] else None,
            "output_score_mean": row["output_score_sum"] / row["outputs"] if row["outputs"] else None,
        })
    write_json(output_root / "_label_score_summary.json", sorted(rows, key=lambda item: item["label"]))
    write_csv(output_root / "_label_score_summary.csv", sorted(rows, key=lambda item: item["label"]))


def write_action_label_summary(output_root: Path, selected_paths: Sequence[Path], input_root: Path, premise_order: Sequence[str]) -> None:
    rows_by_label: Dict[str, Dict[str, Any]] = {}
    for src_path in selected_paths:
        scored_path = scored_output_path(src_path, input_root, output_root)
        payload = read_json_if_exists(scored_path)
        if not isinstance(payload, dict):
            continue
        label = scored_path.relative_to(output_root).parts[0]
        row = rows_by_label.setdefault(label, {"label": label, "files": 0, "entries": 0, "outputs": 0, "entry_sum": 0.0, "output_sum": 0.0})
        row["files"] += 1
        for interactions in payload.values():
            if not isinstance(interactions, list):
                continue
            for entry in interactions:
                if not isinstance(entry, dict):
                    continue
                entry_mean = entry.get("action_reasoning_alignment_score_mean")
                if isinstance(entry_mean, (int, float)):
                    row["entries"] += 1
                    row["entry_sum"] += float(entry_mean)
                for item in entry.get("output_action_reasoning_alignment_scores") or []:
                    score = item.get("score") if isinstance(item, dict) else None
                    if isinstance(score, (int, float)):
                        row["outputs"] += 1
                        row["output_sum"] += float(score)
    rows = []
    for row in rows_by_label.values():
        rows.append({
            "label": row["label"],
            "files": row["files"],
            "entries": row["entries"],
            "outputs": row["outputs"],
            "entry_alignment_score_mean": row["entry_sum"] / row["entries"] if row["entries"] else None,
            "output_alignment_score_mean": row["output_sum"] / row["outputs"] if row["outputs"] else None,
            "scoring_definition": "action_reasoning_mismatch",
            "premise_order": ",".join(premise_order),
            "action_fields": "output",
        })
    write_json(output_root / "_label_score_summary.json", sorted(rows, key=lambda item: item["label"]))
    write_csv(output_root / "_label_score_summary.csv", sorted(rows, key=lambda item: item["label"]))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json_if_exists(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as file:
        if not fieldnames:
            return
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_table(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    headers = list(rows[0])
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    path.write_text("\n".join(lines), encoding="utf-8")


def copy_json(src: Path, dst: Path) -> None:
    if src.resolve() == dst.resolve():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def count_files(root: Path, pattern: str) -> int:
    return sum(1 for path in root.rglob(pattern) if path.is_file()) if root.exists() else 0


def count_visualization_files(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.iterdir() if path.is_file() and path.suffix.lower() in {".csv", ".png", ".md", ".json"})


def merge_stats(stats: Sequence[Dict[str, int]]) -> Dict[str, int]:
    merged: Dict[str, int] = defaultdict(int)
    for item in stats:
        for key, value in item.items():
            merged[key] += int(value)
    return dict(merged)


def candidate_to_dict(candidate: Any) -> Dict[str, Any]:
    logprob = float(getattr(candidate, "logprob", float("-inf")))
    return {"token": str(getattr(candidate, "token", "")), "logprob": logprob, "probability": safe_exp(logprob)}


def safe_exp(logprob: Any) -> Optional[float]:
    if logprob is None:
        return None
    value = float(logprob)
    if math.isinf(value) and value < 0:
        return 0.0
    return math.exp(value)


def clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def empty_binary_score() -> Dict[str, Any]:
    return {
        "score": 0.0,
        "generated_token": "",
        "generated_token_logprob": None,
        "generated_token_probability": None,
        "positive_probability": 0.0,
        "negative_probability": 0.0,
        "top_logprobs": [],
    }


def timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    raise SystemExit(main())
