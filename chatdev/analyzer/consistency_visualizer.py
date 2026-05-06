"""
Visualize logprob consistency scores for classified ChatDev scored datasets.

Default input:
    data/classified_chatdev_scored

The module treats each scored interaction turn as one observation and uses
``consistency_score_mean`` as the primary metric.  Raw label directories are
mapped to display labels c0 through c4 before plotting, and the original raw
labels are kept in CSV outputs for traceability.  The ``trajectory`` directory
is excluded by default because it duplicates the same samples across label
directories.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any, Dict, Iterable, List, Optional


def _threshold_suffix_for_constant(threshold: float) -> str:
    return str(threshold).replace(".", "_")


DEFAULT_SCORED_ROOT = Path("data/classified_chatdev_scored")
DEFAULT_OUTPUT_DIRNAME = "_visualizations"
HIGH_SCORE_THRESHOLDS = [round(idx / 10, 1) for idx in range(1, 10)]
SCORE_BINS = [idx / 5 for idx in range(6)]
RECALL_CONSTRAINTS = [0.75, 0.70, 0.65, 0.60, 0.50]
HIGH_RECALL_FLOORS = [0.80, 0.90, 0.95, 1.00]
RECALL_WEIGHTED_BETA = 2.0
HIGH_LOW_GAP_PAIRS = [
    (0.6, 0.2),
    (0.6, 0.3),
    (0.6, 0.4),
    (0.7, 0.2),
    (0.7, 0.3),
    (0.7, 0.4),
    (0.7, 0.5),
    (0.8, 0.2),
    (0.8, 0.3),
    (0.8, 0.4),
    (0.8, 0.5),
    (0.9, 0.3),
    (0.9, 0.4),
    (0.9, 0.5),
]
EVALUATION_SCORE_SPECS = [
    {"key": "consistency_score_file_mean", "title": "Mean Turn Score", "higher_is_better": True},
    {"key": "consistency_score_file_median", "title": "Median Turn Score", "higher_is_better": True},
    {"key": "consistency_score_file_q10", "title": "Q10 Score", "higher_is_better": True},
    {"key": "consistency_score_file_q25", "title": "Q25 Score", "higher_is_better": True},
    {"key": "worst_score", "title": "Worst Turn Score", "higher_is_better": True},
    {"key": "mean_minus_std_score", "title": "Mean Minus Std", "higher_is_better": True},
    {"key": "failure_sensitive_score", "title": "70% Mean + 30% Worst", "higher_is_better": True},
    {"key": "low_tail_penalty_score", "title": "Mean Minus Low Tail", "higher_is_better": True},
    {"key": "high_density_score_0_8", "title": "Mean Times High Rate >=0.8", "higher_is_better": True},
    {"key": "entropy_normalized", "title": "Binned Score Entropy", "higher_is_better": False},
    {"key": "low_score_rate_0_2", "title": "Low Rate <0.2", "higher_is_better": False},
    {"key": "low_score_rate_0_5", "title": "Low Rate <0.5", "higher_is_better": False},
    {"key": "high_score_rate_0_8", "title": "High Rate >=0.8", "higher_is_better": True},
    {"key": "high_score_rate_0_9", "title": "High Rate >=0.9", "higher_is_better": True},
    {"key": "c2_repetition_symptom_score", "title": "c2 Repetition Symptom Score", "higher_is_better": True},
] + [
    {
        "key": f"high_low_gap_{_threshold_suffix_for_constant(high)}_{_threshold_suffix_for_constant(low)}",
        "title": f"High >= {high:.1f} Minus Low < {low:.1f}",
        "higher_is_better": True,
    }
    for high, low in HIGH_LOW_GAP_PAIRS
] + [
    {
        "key": f"high_low_half_penalty_{_threshold_suffix_for_constant(high)}_{_threshold_suffix_for_constant(low)}",
        "title": f"High >= {high:.1f} Minus 0.5 Low < {low:.1f}",
        "higher_is_better": True,
    }
    for high, low in HIGH_LOW_GAP_PAIRS
]
LABEL_GROUPS = {
    "c0": ["0.0"],
    "c1": ["1.1"],
    "c2": ["1.3", "1.5"],
    "c3": ["2.2", "2.3"],
    "c4": ["2.6"],
}
RAW_LABEL_TO_DISPLAY_LABEL = {
    raw_label: display_label
    for display_label, raw_labels in LABEL_GROUPS.items()
    for raw_label in raw_labels
}
CORE_CLUSTER_LABELS = list(LABEL_GROUPS)
CORE_OVERLAP_CLUSTER_LABELS = ["c1", "c2", "c3", "c4"]
CORE_OVERLAP_CLUSTER_K_VALUES = [2, 3, 4]


def load_consistency_records(
    scored_root: str | os.PathLike[str] = DEFAULT_SCORED_ROOT,
    include_trajectory: bool = False,
) -> List[Dict[str, Any]]:
    """Load turn-level consistency records from a classified scored dataset."""
    root = Path(scored_root)
    records: List[Dict[str, Any]] = []

    for path in sorted(root.rglob("*_scored.json"), key=lambda item: str(item)):
        rel = path.relative_to(root)
        if not rel.parts:
            continue
        raw_label = rel.parts[0]
        if raw_label == "trajectory" and not include_trajectory:
            continue
        label = _display_label_for_raw_label(raw_label)
        if label is None:
            continue

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as exc:
            records.append(
                {
                    "label": label,
                    "raw_label": raw_label,
                    "source_file": str(rel),
                    "error": f"failed_to_read_json: {exc}",
                }
            )
            continue

        for role, interactions in payload.items():
            if not isinstance(interactions, list):
                continue
            for interaction_index, entry in enumerate(interactions):
                if not isinstance(entry, dict):
                    continue
                score = _to_float(entry.get("consistency_score_mean"))
                if score is None:
                    continue
                records.append(
                    {
                        "label": label,
                        "raw_label": raw_label,
                        "source_file": str(rel),
                        "file_name": path.name,
                        "role": role,
                        "phase": entry.get("phase") or "",
                        "turn": entry.get("turn"),
                        "phase_turn": entry.get("phase_turn"),
                        "interaction_index": interaction_index,
                        "consistency_score_mean": score,
                        "consistency_score_min": _to_float(entry.get("consistency_score_min")),
                        "consistency_score_max": _to_float(entry.get("consistency_score_max")),
                        "num_output_items": len(entry.get("output") or []),
                        "num_output_scores": len(entry.get("output_consistency_scores") or []),
                        "user_demand": entry.get("user_demand") or "",
                    }
                )

    return records


def summarize_by_label(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return descriptive statistics per classification label."""
    grouped: Dict[str, List[float]] = defaultdict(list)
    file_names: Dict[str, set] = defaultdict(set)
    for record in records:
        score = _to_float(record.get("consistency_score_mean"))
        label = str(record.get("label") or "")
        if label and score is not None:
            grouped[label].append(score)
            file_names[label].add(str(record.get("file_name") or ""))

    rows = []
    for label in sorted(grouped, key=_label_sort_key):
        values = sorted(grouped[label])
        rows.append(
            {
                "label": label,
                "num_turns": len(values),
                "num_files": len(file_names[label]),
                "mean": mean(values),
                "median": median(values),
                "std": pstdev(values) if len(values) > 1 else 0.0,
                "min": values[0],
                "q1": _quantile(values, 0.25),
                "q3": _quantile(values, 0.75),
                "max": values[-1],
            }
        )
    return rows


def dedupe_records_by_display_label(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Collapse the same scored turn when multiple raw labels map to one display label."""
    deduped: Dict[tuple, Dict[str, Any]] = {}
    raw_labels_by_key: Dict[tuple, set] = defaultdict(set)
    source_files_by_key: Dict[tuple, set] = defaultdict(set)
    for record in records:
        label = str(record.get("label") or "")
        file_name = str(record.get("file_name") or "")
        if not label or not file_name:
            continue
        key = (
            label,
            file_name,
            str(record.get("role") or ""),
            str(record.get("phase") or ""),
            str(record.get("turn") or ""),
            str(record.get("phase_turn") or ""),
            str(record.get("interaction_index") or ""),
        )
        raw_labels_by_key[key].add(str(record.get("raw_label") or ""))
        source_files_by_key[key].add(str(record.get("source_file") or ""))
        if key not in deduped:
            deduped[key] = dict(record)

    rows = []
    for key in sorted(deduped, key=lambda item: (_label_sort_key(item[0]), item[1:])):
        row = deduped[key]
        row["raw_labels"] = ";".join(sorted(raw_labels_by_key[key], key=_label_sort_key))
        row["source_files"] = ";".join(sorted(source_files_by_key[key]))
        rows.append(row)
    return rows


def aggregate_records_by_file(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate turn-level records into one mean score per scored JSON file."""
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        label = str(record.get("label") or "")
        file_name = str(record.get("file_name") or "")
        score = _to_float(record.get("consistency_score_mean"))
        if label and file_name and score is not None:
            grouped[(label, file_name)].append(record)

    rows: List[Dict[str, Any]] = []
    for (label, file_name), items in sorted(
        grouped.items(), key=lambda item: (_label_sort_key(item[0][0]), item[0][1])
    ):
        scores = [float(item["consistency_score_mean"]) for item in items]
        sorted_scores = sorted(scores)
        worst = min(items, key=lambda item: float(item["consistency_score_mean"]))
        score_mean = mean(scores)
        score_std = pstdev(scores) if len(scores) > 1 else 0.0
        low_rate_0_2 = sum(score < 0.2 for score in scores) / len(scores)
        low_rate_0_5 = sum(score < 0.5 for score in scores) / len(scores)
        high_rate_0_8 = sum(score >= 0.8 for score in scores) / len(scores)
        high_rate_0_9 = sum(score >= 0.9 for score in scores) / len(scores)
        worst_score = float(worst["consistency_score_mean"])
        rows.append(
            _with_threshold_rates(
                {
                "label": label,
                "file_name": file_name,
                "source_files": ";".join(sorted({str(item.get("source_file") or "") for item in items})),
                "raw_labels": ";".join(sorted({str(item.get("raw_label") or "") for item in items}, key=_label_sort_key)),
                "consistency_score_file_mean": score_mean,
                "consistency_score_file_median": median(scores),
                "consistency_score_file_min": min(scores),
                "consistency_score_file_max": max(scores),
                "consistency_score_file_std": score_std,
                "consistency_score_file_q10": _quantile(sorted_scores, 0.10),
                "consistency_score_file_q25": _quantile(sorted_scores, 0.25),
                "consistency_score_file_q75": _quantile(sorted_scores, 0.75),
                "consistency_score_file_iqr": _quantile(sorted_scores, 0.75) - _quantile(sorted_scores, 0.25),
                "low_score_rate_0_2": low_rate_0_2,
                "low_score_rate_0_5": low_rate_0_5,
                "high_score_rate_0_8": high_rate_0_8,
                "high_low_ratio_0_8_over_0_2": _safe_ratio(
                    high_rate_0_8,
                    low_rate_0_2,
                ),
                "high_low_ratio_0_8_over_0_2_smoothed": (
                    (sum(score >= 0.8 for score in scores) + 1)
                    / (sum(score < 0.2 for score in scores) + 1)
                ),
                "worst_score": worst_score,
                "mean_minus_std_score": score_mean - score_std,
                "failure_sensitive_score": 0.7 * score_mean + 0.3 * worst_score,
                "low_tail_penalty_score": score_mean - low_rate_0_2,
                "high_low_gap_0_8_0_2": high_rate_0_8 - low_rate_0_2,
                "strict_high_low_gap_0_9_0_5": high_rate_0_9 - low_rate_0_5,
                "high_density_score_0_8": score_mean * high_rate_0_8,
                "entropy_normalized": _normalized_score_entropy(scores),
                "worst_role": worst.get("role") or "",
                "worst_phase": worst.get("phase") or "",
                "worst_turn": worst.get("turn"),
                "num_turns": len(scores),
                "num_roles": len({str(item.get("role") or "") for item in items}),
                "num_phases": len({str(item.get("phase") or "") for item in items}),
                "user_demand": next((item.get("user_demand") or "" for item in items), ""),
                },
                scores,
            )
        )
    return rows


def enrich_file_records_with_c2_symptoms(
    turn_records: Iterable[Dict[str, Any]],
    file_records: List[Dict[str, Any]],
) -> None:
    """Add interpretable c2 repetition/non-termination symptom features."""
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for record in turn_records:
        label = str(record.get("label") or "")
        file_name = str(record.get("file_name") or "")
        if label and file_name:
            grouped[(label, file_name)].append(record)

    metrics_by_key: Dict[tuple, Dict[str, float]] = {}
    for key, items in grouped.items():
        scores = [float(record["consistency_score_mean"]) for record in items]
        sorted_items = sorted(
            items,
            key=lambda record: (
                str(record.get("role") or ""),
                str(record.get("phase") or ""),
                int(record.get("turn") or 0),
                int(record.get("interaction_index") or 0),
            ),
        )
        current_low_run = 0
        max_low_run = 0
        for record in sorted_items:
            if float(record["consistency_score_mean"]) < 0.5:
                current_low_run += 1
                max_low_run = max(max_low_run, current_low_run)
            else:
                current_low_run = 0

        low_turns = [record for record in items if float(record["consistency_score_mean"]) < 0.5]
        phase_values = _group_turn_scores(items, "phase")
        role_values = _group_turn_scores(items, "role")
        metrics_by_key[key] = {
            "c2_max_low_run": float(max_low_run),
            "c2_low_turn_avg_output_items": (
                mean([int(record.get("num_output_items") or 0) for record in low_turns])
                if low_turns
                else 0.0
            ),
            "c2_low_turn_count": float(len(low_turns)),
            "c2_low05_rate": sum(score < 0.5 for score in scores) / len(scores),
            "c2_coding_low05_rate": _rate_below(phase_values.get("Coding", []), 0.5),
            "c2_reviewmod_low05_rate": _rate_below(phase_values.get("CodeReviewModification", []), 0.5),
            "c2_programmer_low05_rate": _rate_below(role_values.get("Programmer", []), 0.5),
            "c2_score_std": pstdev(scores) if len(scores) > 1 else 0.0,
            "c2_num_turns": float(len(items)),
        }

    for record in file_records:
        key = (str(record.get("label") or ""), str(record.get("file_name") or ""))
        record.update(metrics_by_key.get(key, {}))

    symptom_keys = [
        "c2_coding_low05_rate",
        "c2_reviewmod_low05_rate",
        "c2_max_low_run",
        "c2_score_std",
        "c2_num_turns",
        "c2_low_turn_avg_output_items",
    ]
    _add_standardized_composite(file_records, symptom_keys, "c2_repetition_symptom_score")


def write_visualization_report(
    scored_root: str | os.PathLike[str] = DEFAULT_SCORED_ROOT,
    output_dir: str | os.PathLike[str] | None = None,
    include_trajectory: bool = False,
) -> Dict[str, Any]:
    """Generate CSV summaries and figures for the scored dataset."""
    root = Path(scored_root)
    out_dir = Path(output_dir) if output_dir else root / DEFAULT_OUTPUT_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)

    records = load_consistency_records(root, include_trajectory=include_trajectory)
    valid_records = dedupe_records_by_display_label(record for record in records if "error" not in record)
    file_records = aggregate_records_by_file(valid_records)
    enrich_file_records_with_c2_symptoms(valid_records, file_records)
    summary = summarize_by_label(valid_records)
    file_summary = summarize_by_label(
        {
            "label": record["label"],
            "file_name": record["file_name"],
            "consistency_score_mean": record["consistency_score_file_mean"],
        }
        for record in file_records
    )

    records_csv = out_dir / "consistency_turn_records.csv"
    file_records_csv = out_dir / "consistency_file_records.csv"
    summary_csv = out_dir / "consistency_label_summary.csv"
    file_summary_csv = out_dir / "consistency_file_label_summary.csv"
    boxplot_png = out_dir / "consistency_by_label_boxplot.png"
    file_boxplot_png = out_dir / "consistency_by_label_file_boxplot.png"
    phase_heatmap_png = out_dir / "consistency_label_phase_heatmap.png"
    role_heatmap_png = out_dir / "consistency_label_role_heatmap.png"
    ecdf_png = out_dir / "consistency_by_label_ecdf.png"
    file_low_rate_png = out_dir / "consistency_file_low_score_rates.png"
    high_rate_boxplot_paths = {
        threshold: out_dir / f"consistency_file_high_score_rate_{_threshold_suffix(threshold)}_boxplot.png"
        for threshold in HIGH_SCORE_THRESHOLDS
    }
    high_rate_heatmap_png = out_dir / "consistency_file_high_score_rate_threshold_heatmap.png"
    high_low_ratio_boxplot_png = out_dir / "consistency_file_high_low_ratio_0_8_over_0_2_boxplot.png"
    file_feature_heatmap_png = out_dir / "consistency_file_feature_heatmap.png"
    evaluation_score_boxplots_png = out_dir / "consistency_file_evaluation_score_boxplots.png"
    evaluation_score_summary_csv = out_dir / "consistency_file_evaluation_score_summary.csv"
    evaluation_score_rank_csv = out_dir / "consistency_file_evaluation_score_separation_rank.csv"
    c3_positive_score_csv = out_dir / "c3_positive_score_candidates.csv"
    c3_positive_score_boxplots_png = out_dir / "c3_positive_score_boxplots.png"
    one_vs_rest_standards_csv = out_dir / "one_vs_rest_best_classification_standards.csv"
    one_vs_rest_standards_png = out_dir / "one_vs_rest_best_classification_standards.png"
    c0_vs_c1_summary_csv = out_dir / "c0_vs_c1_eta2_f1_summary.csv"
    c0_vs_c1_thresholds_csv = out_dir / "c0_vs_c1_single_score_thresholds.csv"
    c0_vs_c1_recall_constrained_csv = out_dir / "c0_vs_c1_recall_constrained_eta2_f1_summary.csv"
    c0_vs_c1_high_recall_csv = out_dir / "c0_vs_c1_high_recall_eta2_f2_summary.csv"
    c0_vs_c1_high_recall_png = out_dir / "c0_vs_c1_high_recall_eta2_f2_top_scores.png"
    c0_vs_c1_boxplot_png = out_dir / "c0_vs_c1_best_single_score_boxplot.png"
    phase_boxplots_png = out_dir / "consistency_phase_boxplots_by_label.png"
    role_boxplots_png = out_dir / "consistency_role_boxplots_by_label.png"
    worst_score_png = out_dir / "consistency_worst_score_by_label_boxplot.png"
    overlap_count_heatmap_png = out_dir / "label_overlap_count_heatmap.png"
    overlap_jaccard_heatmap_png = out_dir / "label_overlap_jaccard_heatmap.png"
    overlap_csv = out_dir / "label_overlap_matrix.csv"
    label_cluster_csv = out_dir / "label_cluster_assignments.csv"
    label_cluster_png = out_dir / "label_cluster_pca.png"
    core_label_cluster_csv = out_dir / "label_cluster_assignments_c0_to_c4.csv"
    core_label_cluster_png = out_dir / "label_cluster_pca_c0_to_c4.png"
    core_overlap_cluster_csv = out_dir / "label_overlap_clusters_c0_to_c4.csv"
    core_overlap_cluster_png = out_dir / "label_overlap_clusters_c0_to_c4_heatmap.png"
    core_major_overlap_cluster_paths = {
        k: {
            "csv": out_dir / f"label_overlap_clusters_core_c1_to_c4_k{k}.csv",
            "png": out_dir / f"label_overlap_clusters_core_c1_to_c4_k{k}_heatmap.png",
            "scatter_png": out_dir / f"label_overlap_clusters_core_c1_to_c4_k{k}_mds_scatter.png",
        }
        for k in CORE_OVERLAP_CLUSTER_K_VALUES
    }
    report_md = out_dir / "README.md"

    _write_csv(records_csv, valid_records)
    _write_csv(file_records_csv, file_records)
    _write_csv(summary_csv, summary)
    _write_csv(file_summary_csv, file_summary)
    plot_label_boxplot(valid_records, boxplot_png)
    plot_label_boxplot(
        file_records,
        file_boxplot_png,
        value_key="consistency_score_file_mean",
        title="File-Level Consistency Score Distribution by Classified Label",
        ylabel="mean consistency_score_mean per JSON file",
    )
    plot_group_heatmap(
        valid_records,
        row_key="label",
        col_key="phase",
        value_key="consistency_score_mean",
        output_path=phase_heatmap_png,
        title="Mean Consistency Score by Label and Phase",
    )
    plot_group_heatmap(
        valid_records,
        row_key="label",
        col_key="role",
        value_key="consistency_score_mean",
        output_path=role_heatmap_png,
        title="Mean Consistency Score by Label and Role",
    )
    plot_label_ecdf(valid_records, ecdf_png)
    plot_low_score_rates(file_records, file_low_rate_png)
    for threshold, output_path in high_rate_boxplot_paths.items():
        suffix = _threshold_suffix(threshold)
        plot_label_boxplot(
            file_records,
            output_path,
            value_key=f"high_score_rate_{suffix}",
            title=f"File-Level Turn Rate >= {threshold:.1f} by Classified Label",
            ylabel=f"fraction of turns with consistency_score_mean >= {threshold:.1f}",
        )
    plot_threshold_rate_heatmap(file_records, high_rate_heatmap_png)
    plot_label_boxplot(
        file_records,
        high_low_ratio_boxplot_png,
        value_key="high_low_ratio_0_8_over_0_2_smoothed",
        title="File-Level High/Low Consistency Ratio by Classified Label",
        ylabel="(turns >= 0.8 + 1) / (turns < 0.2 + 1)",
        fixed_ylim=False,
    )
    plot_file_feature_heatmap(file_records, file_feature_heatmap_png)
    evaluation_summary = summarize_evaluation_scores(file_records)
    evaluation_rank = rank_evaluation_scores_by_label_separation(file_records)
    _write_csv(evaluation_score_summary_csv, evaluation_summary)
    _write_csv(evaluation_score_rank_csv, evaluation_rank)
    plot_evaluation_score_grid(file_records, evaluation_score_boxplots_png)
    c3_positive_report = build_c3_positive_score_report(valid_records)
    _write_csv(c3_positive_score_csv, c3_positive_report["rows"])
    plot_c3_positive_score_boxplots(c3_positive_report["rows"], c3_positive_score_boxplots_png)
    one_vs_rest_standards = build_one_vs_rest_classification_standards(file_records)
    _write_csv(one_vs_rest_standards_csv, one_vs_rest_standards)
    plot_one_vs_rest_classification_standards(one_vs_rest_standards, one_vs_rest_standards_png)
    c0_vs_c1_report = build_binary_label_pair_score_report(
        file_records,
        negative_label="c0",
        positive_label="c1",
    )
    _write_csv(c0_vs_c1_summary_csv, c0_vs_c1_report["summary_rows"])
    _write_csv(c0_vs_c1_thresholds_csv, c0_vs_c1_report["threshold_rows"])
    _write_csv(c0_vs_c1_recall_constrained_csv, c0_vs_c1_report["recall_constrained_rows"])
    _write_csv(c0_vs_c1_high_recall_csv, c0_vs_c1_report["high_recall_rows"])
    plot_binary_high_recall_scores(
        c0_vs_c1_report["high_recall_rows"],
        c0_vs_c1_high_recall_png,
        negative_label="c0",
        positive_label="c1",
    )
    plot_binary_label_pair_best_score(
        c0_vs_c1_report["file_score_rows"],
        c0_vs_c1_report["best_score_key"],
        c0_vs_c1_boxplot_png,
        negative_label="c0",
        positive_label="c1",
    )
    plot_category_boxplot_grid(
        valid_records,
        category_key="phase",
        output_path=phase_boxplots_png,
        title="Turn-Level Consistency by Label within Each Phase",
    )
    plot_category_boxplot_grid(
        valid_records,
        category_key="role",
        output_path=role_boxplots_png,
        title="Turn-Level Consistency by Label within Each Role",
    )
    plot_label_boxplot(
        file_records,
        worst_score_png,
        value_key="worst_score",
        title="Worst Turn Score Distribution by Classified Label",
        ylabel="minimum turn consistency score per JSON file",
    )
    overlap = compute_label_overlap(file_records)
    _write_csv(overlap_csv, overlap["rows"])
    plot_label_overlap_heatmap(
        overlap["labels"],
        overlap["count_matrix"],
        overlap_count_heatmap_png,
        title="Shared JSON Count Between Labels",
        colorbar_label="shared JSON files",
        value_format="{:.0f}",
    )
    plot_label_overlap_heatmap(
        overlap["labels"],
        overlap["jaccard_matrix"],
        overlap_jaccard_heatmap_png,
        title="Jaccard Overlap Between Labels",
        colorbar_label="intersection / union",
        value_format="{:.2f}",
        vmin=0,
        vmax=1,
    )
    cluster_report = cluster_labels_for_consistency(valid_records, file_records)
    _write_csv(label_cluster_csv, cluster_report["rows"])
    plot_label_cluster_pca(cluster_report["rows"], label_cluster_png)
    available_labels = {str(record.get("label") or "") for record in file_records}
    core_labels = [label for label in CORE_CLUSTER_LABELS if label in available_labels]
    core_cluster_report = cluster_labels_for_consistency(
        valid_records,
        file_records,
        labels=core_labels,
        k=4,
    )
    _write_csv(core_label_cluster_csv, core_cluster_report["rows"])
    plot_label_cluster_pca(core_cluster_report["rows"], core_label_cluster_png)
    core_overlap_cluster = cluster_labels_by_overlap(file_records, labels=core_labels, k=4)
    _write_csv(core_overlap_cluster_csv, core_overlap_cluster["rows"])
    plot_overlap_cluster_heatmap(
        core_overlap_cluster["labels"],
        core_overlap_cluster["similarity_matrix"],
        core_overlap_cluster["cluster_by_label"],
        core_overlap_cluster_png,
    )
    core_major_labels = [label for label in CORE_OVERLAP_CLUSTER_LABELS if label in available_labels]
    for k, paths in core_major_overlap_cluster_paths.items():
        core_major_overlap_cluster = cluster_labels_by_overlap(file_records, labels=core_major_labels, k=k)
        _write_csv(paths["csv"], core_major_overlap_cluster["rows"])
        plot_overlap_cluster_heatmap(
            core_major_overlap_cluster["labels"],
            core_major_overlap_cluster["similarity_matrix"],
            core_major_overlap_cluster["cluster_by_label"],
            paths["png"],
        )
        plot_overlap_cluster_scatter(
            core_major_overlap_cluster["labels"],
            core_major_overlap_cluster["similarity_matrix"],
            core_major_overlap_cluster["cluster_by_label"],
            paths["scatter_png"],
        )

    report = {
        "scored_root": str(root),
        "output_dir": str(out_dir),
        "include_trajectory": include_trajectory,
        "num_records": len(valid_records),
        "num_file_records": len(file_records),
        "num_labels": len(summary),
        "records_csv": str(records_csv),
        "file_records_csv": str(file_records_csv),
        "summary_csv": str(summary_csv),
        "file_summary_csv": str(file_summary_csv),
        "boxplot_png": str(boxplot_png),
        "file_boxplot_png": str(file_boxplot_png),
        "phase_heatmap_png": str(phase_heatmap_png),
        "role_heatmap_png": str(role_heatmap_png),
        "ecdf_png": str(ecdf_png),
        "file_low_rate_png": str(file_low_rate_png),
        "high_rate_boxplot_pngs": {
            f"{threshold:.1f}": str(path)
            for threshold, path in high_rate_boxplot_paths.items()
        },
        "high_rate_heatmap_png": str(high_rate_heatmap_png),
        "high_low_ratio_boxplot_png": str(high_low_ratio_boxplot_png),
        "file_feature_heatmap_png": str(file_feature_heatmap_png),
        "evaluation_score_boxplots_png": str(evaluation_score_boxplots_png),
        "evaluation_score_summary_csv": str(evaluation_score_summary_csv),
        "evaluation_score_rank_csv": str(evaluation_score_rank_csv),
        "c3_positive_score_csv": str(c3_positive_score_csv),
        "c3_positive_score_boxplots_png": str(c3_positive_score_boxplots_png),
        "one_vs_rest_standards_csv": str(one_vs_rest_standards_csv),
        "one_vs_rest_standards_png": str(one_vs_rest_standards_png),
        "c0_vs_c1_summary_csv": str(c0_vs_c1_summary_csv),
        "c0_vs_c1_thresholds_csv": str(c0_vs_c1_thresholds_csv),
        "c0_vs_c1_recall_constrained_csv": str(c0_vs_c1_recall_constrained_csv),
        "c0_vs_c1_high_recall_csv": str(c0_vs_c1_high_recall_csv),
        "c0_vs_c1_high_recall_png": str(c0_vs_c1_high_recall_png),
        "c0_vs_c1_boxplot_png": str(c0_vs_c1_boxplot_png),
        "phase_boxplots_png": str(phase_boxplots_png),
        "role_boxplots_png": str(role_boxplots_png),
        "worst_score_png": str(worst_score_png),
        "overlap_count_heatmap_png": str(overlap_count_heatmap_png),
        "overlap_jaccard_heatmap_png": str(overlap_jaccard_heatmap_png),
        "overlap_csv": str(overlap_csv),
        "label_cluster_csv": str(label_cluster_csv),
        "label_cluster_png": str(label_cluster_png),
        "label_groups": LABEL_GROUPS,
        "core_label_cluster_csv": str(core_label_cluster_csv),
        "core_label_cluster_png": str(core_label_cluster_png),
        "core_overlap_cluster_csv": str(core_overlap_cluster_csv),
        "core_overlap_cluster_png": str(core_overlap_cluster_png),
        "core_major_overlap_cluster_outputs": {
            str(k): {
                "csv": str(paths["csv"]),
                "png": str(paths["png"]),
                "scatter_png": str(paths["scatter_png"]),
            }
            for k, paths in core_major_overlap_cluster_paths.items()
        },
        "report_md": str(report_md),
    }
    _write_markdown_report(report_md, report, summary)
    return report


def plot_label_boxplot(
    records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
    value_key: str = "consistency_score_mean",
    title: str = "Consistency Score Distribution by Classified Label",
    ylabel: str = "consistency_score_mean",
    fixed_ylim: bool = True,
) -> None:
    """Create a box plot of a score field grouped by label."""
    plt = _import_pyplot()
    grouped: Dict[str, List[float]] = defaultdict(list)
    for record in records:
        score = _to_float(record.get(value_key))
        label = str(record.get("label") or "")
        if label and score is not None:
            grouped[label].append(score)

    labels = sorted(grouped, key=_label_sort_key)
    values = [grouped[label] for label in labels]
    if not values:
        _write_empty_plot(plt, output_path, "No consistency records found")
        return

    width = max(10, min(24, len(labels) * 0.75))
    fig, ax = plt.subplots(figsize=(width, 6))
    try:
        ax.boxplot(values, tick_labels=labels, showmeans=True, patch_artist=True)
    except TypeError:
        ax.boxplot(values, labels=labels, showmeans=True, patch_artist=True)
    ax.set_title(title)
    ax.set_xlabel("Class label")
    ax.set_ylabel(ylabel)
    if fixed_ylim:
        ax.set_ylim(-0.03, 1.03)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_group_heatmap(
    records: Iterable[Dict[str, Any]],
    row_key: str,
    col_key: str,
    value_key: str,
    output_path: str | os.PathLike[str],
    title: str,
) -> None:
    """Plot a mean-score heatmap for two categorical fields."""
    plt = _import_pyplot()
    grouped: Dict[tuple, List[float]] = defaultdict(list)
    row_values = set()
    col_values = set()
    for record in records:
        row = str(record.get(row_key) or "")
        col = str(record.get(col_key) or "")
        value = _to_float(record.get(value_key))
        if not row or not col or value is None:
            continue
        grouped[(row, col)].append(value)
        row_values.add(row)
        col_values.add(col)

    rows = sorted(row_values, key=_label_sort_key if row_key == "label" else str)
    cols = sorted(col_values)
    if not rows or not cols:
        _write_empty_plot(plt, output_path, "No heatmap records found")
        return

    matrix = []
    for row in rows:
        matrix_row = []
        for col in cols:
            values = grouped.get((row, col), [])
            matrix_row.append(mean(values) if values else math.nan)
        matrix.append(matrix_row)

    fig_width = max(10, min(28, len(cols) * 0.8))
    fig_height = max(5, min(18, len(rows) * 0.55))
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    image = ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_title(title)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels(cols, rotation=45, ha="right")
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(rows)
    ax.set_xlabel(col_key)
    ax.set_ylabel(row_key)
    fig.colorbar(image, ax=ax, label=value_key)

    for row_idx, row in enumerate(rows):
        for col_idx, _col in enumerate(cols):
            value = matrix[row_idx][col_idx]
            if not math.isnan(value):
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", color="white", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_label_ecdf(
    records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
    value_key: str = "consistency_score_mean",
) -> None:
    """Plot empirical CDF curves per label to reveal distribution separation."""
    plt = _import_pyplot()
    grouped: Dict[str, List[float]] = defaultdict(list)
    for record in records:
        value = _to_float(record.get(value_key))
        label = str(record.get("label") or "")
        if label and value is not None:
            grouped[label].append(value)

    if not grouped:
        _write_empty_plot(plt, output_path, "No ECDF records found")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    for label in sorted(grouped, key=_label_sort_key):
        values = sorted(grouped[label])
        y_values = [(idx + 1) / len(values) for idx in range(len(values))]
        ax.step(values, y_values, where="post", label=f"{label} (n={len(values)})")
    ax.set_title("ECDF of Turn-Level Consistency Scores by Label")
    ax.set_xlabel(value_key)
    ax.set_ylabel("cumulative fraction of turns")
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.25)
    ax.legend(loc="lower right", fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_low_score_rates(
    file_records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot label-level mean low/high score rates from file-level records."""
    plt = _import_pyplot()
    rate_keys = ["low_score_rate_0_2", "low_score_rate_0_5", "high_score_rate_0_8"]
    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in file_records:
        label = str(record.get("label") or "")
        if not label:
            continue
        for key in rate_keys:
            value = _to_float(record.get(key))
            if value is not None:
                grouped[label][key].append(value)

    labels = sorted(grouped, key=_label_sort_key)
    if not labels:
        _write_empty_plot(plt, output_path, "No low-score rate records found")
        return

    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 0.8), 6))
    x_positions = list(range(len(labels)))
    width = 0.24
    offsets = [-width, 0, width]
    colors = ["#c44e52", "#dd8452", "#55a868"]
    display = {
        "low_score_rate_0_2": "turns < 0.2",
        "low_score_rate_0_5": "turns < 0.5",
        "high_score_rate_0_8": "turns >= 0.8",
    }
    for offset, key, color in zip(offsets, rate_keys, colors):
        values = [mean(grouped[label][key]) if grouped[label][key] else 0.0 for label in labels]
        ax.bar([pos + offset for pos in x_positions], values, width=width, label=display[key], color=color)
    ax.set_title("Mean File-Level Low/High Score Rates by Label")
    ax.set_xlabel("Class label")
    ax.set_ylabel("mean fraction of turns per JSON file")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_file_feature_heatmap(
    file_records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot interpretable file-level feature means by label."""
    plt = _import_pyplot()
    feature_keys = [
        "consistency_score_file_mean",
        "consistency_score_file_median",
        "consistency_score_file_min",
        "consistency_score_file_q10",
        "consistency_score_file_std",
        "consistency_score_file_iqr",
        "low_score_rate_0_2",
        "low_score_rate_0_5",
        "high_score_rate_0_8",
        "worst_score",
    ]
    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in file_records:
        label = str(record.get("label") or "")
        if not label:
            continue
        for key in feature_keys:
            value = _to_float(record.get(key))
            if value is not None:
                grouped[label][key].append(value)

    labels = sorted(grouped, key=_label_sort_key)
    if not labels:
        _write_empty_plot(plt, output_path, "No file feature records found")
        return

    matrix = []
    for label in labels:
        matrix.append([mean(grouped[label][key]) if grouped[label][key] else math.nan for key in feature_keys])

    fig, ax = plt.subplots(figsize=(max(12, len(feature_keys) * 1.1), max(5, len(labels) * 0.55)))
    image = ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="magma")
    ax.set_title("Mean File-Level Features by Label")
    ax.set_xticks(range(len(feature_keys)))
    ax.set_xticklabels(feature_keys, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    fig.colorbar(image, ax=ax, label="feature mean")
    for row_idx, _label in enumerate(labels):
        for col_idx, _feature in enumerate(feature_keys):
            value = matrix[row_idx][col_idx]
            if not math.isnan(value):
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", color="white", fontsize=7)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_threshold_rate_heatmap(
    file_records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot mean high-score rates for thresholds 0.1 through 0.9."""
    plt = _import_pyplot()
    grouped: Dict[str, Dict[float, List[float]]] = defaultdict(lambda: defaultdict(list))
    for record in file_records:
        label = str(record.get("label") or "")
        if not label:
            continue
        for threshold in HIGH_SCORE_THRESHOLDS:
            value = _to_float(record.get(f"high_score_rate_{_threshold_suffix(threshold)}"))
            if value is not None:
                grouped[label][threshold].append(value)

    labels = sorted(grouped, key=_label_sort_key)
    if not labels:
        _write_empty_plot(plt, output_path, "No threshold-rate records found")
        return

    matrix = []
    for label in labels:
        matrix.append([
            mean(grouped[label][threshold]) if grouped[label][threshold] else math.nan
            for threshold in HIGH_SCORE_THRESHOLDS
        ])

    fig, ax = plt.subplots(figsize=(12, max(5, len(labels) * 0.55)))
    image = ax.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_title("Mean File-Level High-Score Rate by Label and Threshold")
    ax.set_xticks(range(len(HIGH_SCORE_THRESHOLDS)))
    ax.set_xticklabels([f">= {threshold:.1f}" for threshold in HIGH_SCORE_THRESHOLDS], rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("turn consistency threshold")
    ax.set_ylabel("Class label")
    fig.colorbar(image, ax=ax, label="mean fraction of turns")
    for row_idx, _label in enumerate(labels):
        for col_idx, _threshold in enumerate(HIGH_SCORE_THRESHOLDS):
            value = matrix[row_idx][col_idx]
            if not math.isnan(value):
                ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", color="white", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def summarize_evaluation_scores(file_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Summarize every candidate file-level evaluation score by display label."""
    records_list = list(file_records)
    rows: List[Dict[str, Any]] = []
    for spec in EVALUATION_SCORE_SPECS:
        key = spec["key"]
        grouped: Dict[str, List[float]] = defaultdict(list)
        for record in records_list:
            label = str(record.get("label") or "")
            value = _to_float(record.get(key))
            if label and value is not None:
                grouped[label].append(value)
        for label in sorted(grouped, key=_label_sort_key):
            values = sorted(grouped[label])
            rows.append(
                {
                    "score_key": key,
                    "score_title": spec["title"],
                    "higher_is_better": spec["higher_is_better"],
                    "label": label,
                    "num_files": len(values),
                    "mean": mean(values),
                    "median": median(values),
                    "q1": _quantile(values, 0.25),
                    "q3": _quantile(values, 0.75),
                    "min": values[0],
                    "max": values[-1],
                    "std": pstdev(values) if len(values) > 1 else 0.0,
                }
            )
    return rows


def rank_evaluation_scores_by_label_separation(file_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rank candidate scores by eta-squared across display labels."""
    records_list = list(file_records)
    rows: List[Dict[str, Any]] = []
    for spec in EVALUATION_SCORE_SPECS:
        key = spec["key"]
        grouped: Dict[str, List[float]] = defaultdict(list)
        for record in records_list:
            label = str(record.get("label") or "")
            value = _to_float(record.get(key))
            if label and value is not None:
                grouped[label].append(value)
        labels = sorted(grouped, key=_label_sort_key)
        values = [value for label in labels for value in grouped[label]]
        if len(values) < 2 or len(labels) < 2:
            continue
        grand_mean = mean(values)
        between_ss = sum(len(grouped[label]) * (mean(grouped[label]) - grand_mean) ** 2 for label in labels)
        total_ss = sum((value - grand_mean) ** 2 for value in values)
        eta_squared = between_ss / total_ss if total_ss else 0.0
        label_means = {label: mean(grouped[label]) for label in labels}
        sorted_by_mean = sorted(label_means.items(), key=lambda item: item[1], reverse=bool(spec["higher_is_better"]))
        rows.append(
            {
                "score_key": key,
                "score_title": spec["title"],
                "higher_is_better": spec["higher_is_better"],
                "eta_squared": eta_squared,
                "mean_range": max(label_means.values()) - min(label_means.values()),
                "best_label": sorted_by_mean[0][0],
                "best_label_mean": sorted_by_mean[0][1],
                "worst_label": sorted_by_mean[-1][0],
                "worst_label_mean": sorted_by_mean[-1][1],
                "label_means": "; ".join(f"{label}:{label_means[label]:.4f}" for label in labels),
            }
        )
    return sorted(rows, key=lambda row: float(row["eta_squared"]), reverse=True)


def plot_evaluation_score_grid(
    file_records: Iterable[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot candidate file-level evaluation scores as label-grouped boxplots."""
    plt = _import_pyplot()
    records_list = list(file_records)
    labels = sorted({str(record.get("label") or "") for record in records_list if record.get("label")}, key=_label_sort_key)
    if not labels:
        _write_empty_plot(plt, output_path, "No evaluation score records found")
        return

    n_cols = 4
    n_rows = math.ceil(len(EVALUATION_SCORE_SPECS) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(20, max(8, n_rows * 3.4)), squeeze=False)
    for idx, spec in enumerate(EVALUATION_SCORE_SPECS):
        ax = axes[idx // n_cols][idx % n_cols]
        grouped_values = []
        used_labels = []
        for label in labels:
            values = [
                _to_float(record.get(spec["key"]))
                for record in records_list
                if str(record.get("label") or "") == label
            ]
            values = [value for value in values if value is not None]
            if values:
                grouped_values.append(values)
                used_labels.append(label)
        if grouped_values:
            try:
                ax.boxplot(grouped_values, tick_labels=used_labels, showmeans=True, patch_artist=True)
            except TypeError:
                ax.boxplot(grouped_values, labels=used_labels, showmeans=True, patch_artist=True)
        ax.set_title(spec["title"], fontsize=10)
        ax.tick_params(axis="x", labelrotation=0)
        ax.grid(axis="y", alpha=0.25)
    for idx in range(len(EVALUATION_SCORE_SPECS), n_rows * n_cols):
        axes[idx // n_cols][idx % n_cols].axis("off")
    fig.suptitle("Candidate File-Level Evaluation Scores by c Label", fontsize=16)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_c3_positive_score_report(turn_records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Build c3-vs-rest candidate scores from raw turn scores and phase/role features."""
    import numpy as np

    file_rows = _build_file_phase_role_feature_rows(turn_records)
    if not file_rows:
        return {"rows": []}

    base_feature_keys = [
        key
        for key in file_rows[0]
        if key not in {"label", "file_name", "binary_label", "is_c3"}
    ]
    candidate_scores: Dict[str, List[float]] = {
        key: [_to_float(row.get(key)) or 0.0 for row in file_rows]
        for key in base_feature_keys
    }

    candidate_scores["c3_interpretable_symptom_score"] = _linear_score(
        file_rows,
        {
            "phase_mean::Manual": 1.0,
            "phase_mean::TestModification": 0.8,
            "phase_mean::DemandAnalysis": -0.8,
            "low_score_rate_0_2": 0.6,
            "role_low05::Code Reviewer": 0.6,
            "phase_low05::CodeReviewComment": 0.6,
            "num_phases": 0.4,
            "consistency_score_file_q25": -0.4,
        },
    )
    candidate_scores["c3_code_review_failure_score"] = _linear_score(
        file_rows,
        {
            "role_low05::Code Reviewer": 1.0,
            "phase_low05::CodeReviewComment": 1.0,
            "phase_low05::Coding": 0.6,
            "phase_mean::Coding": -0.5,
            "consistency_score_file_mean": -0.4,
        },
    )
    candidate_scores["c3_low_tail_score"] = _linear_score(
        file_rows,
        {
            "low_score_rate_0_2": 1.0,
            "low_score_rate_0_4": 0.6,
            "consistency_score_file_q25": -0.8,
            "high_score_rate_0_8": -0.5,
        },
    )

    x = np.array([[float(row[key]) for key in base_feature_keys] for row in file_rows], dtype=float)
    y = np.array([1 if row["label"] == "c3" else 0 for row in file_rows], dtype=int)
    z, _, _ = _standardize_matrix(x)
    single_rank = []
    for idx, key in enumerate(base_feature_keys):
        values = z[:, idx]
        single_rank.append((_binary_eta_squared(values.tolist(), y.tolist()), idx))
    ordered_indices = [idx for _eta, idx in sorted(single_rank, reverse=True)]
    for top_n in [8, 20, min(40, len(base_feature_keys)), len(base_feature_keys)]:
        selected = ordered_indices[:top_n]
        candidate_scores[f"c3_lda_top_{top_n}_score"] = _ridge_lda_score(z[:, selected], y).tolist()

    rows = []
    for score_key, values in candidate_scores.items():
        eta_squared = _binary_eta_squared(values, y.tolist())
        auc = _binary_auc(values, y.tolist())
        direction = "high_is_c3" if auc >= 0.5 else "low_is_c3"
        c3_values = [value for value, is_c3 in zip(values, y.tolist()) if is_c3]
        rest_values = [value for value, is_c3 in zip(values, y.tolist()) if not is_c3]
        rows.append(
            {
                "score_key": score_key,
                "eta_squared": eta_squared,
                "auc_best_direction": max(auc, 1 - auc),
                "direction": direction,
                "c3_mean": mean(c3_values),
                "rest_mean": mean(rest_values),
                "mean_delta_c3_minus_rest": mean(c3_values) - mean(rest_values),
                "c3_n": len(c3_values),
                "rest_n": len(rest_values),
            }
        )
    return {"rows": sorted(rows, key=lambda row: float(row["eta_squared"]), reverse=True)}


def plot_c3_positive_score_boxplots(
    rows: List[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot top c3-positive candidate scores as eta-squared bars."""
    plt = _import_pyplot()
    if not rows:
        _write_empty_plot(plt, output_path, "No c3-positive candidate scores found")
        return
    top_rows = rows[:20]
    labels = [row["score_key"] for row in top_rows]
    values = [float(row["eta_squared"]) for row in top_rows]
    fig, ax = plt.subplots(figsize=(12, max(6, len(top_rows) * 0.35)))
    positions = list(range(len(top_rows)))
    ax.barh(positions, values, color="#2c7fb8")
    ax.set_yticks(positions)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("binary eta-squared for c3 vs c0/c1/c2/c4")
    ax.set_title("Top c3-Positive Candidate Scores")
    for idx, row in enumerate(top_rows):
        ax.text(values[idx] + 0.001, idx, f"auc={float(row['auc_best_direction']):.3f}", va="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_one_vs_rest_classification_standards(
    file_records: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Find the strongest one-vs-rest threshold rule for each display label."""
    records_list = list(file_records)
    labels = sorted(
        {str(record.get("label") or "") for record in records_list if record.get("label")},
        key=_label_sort_key,
    )
    rows: List[Dict[str, Any]] = []

    for target_label in labels:
        y = [1 if str(record.get("label") or "") == target_label else 0 for record in records_list]
        if not any(y) or all(y):
            continue

        for spec in EVALUATION_SCORE_SPECS:
            values = [_to_float(record.get(spec["key"])) for record in records_list]
            paired = [
                (float(value), label)
                for value, label in zip(values, y)
                if value is not None
            ]
            if len(paired) < 2:
                continue

            clean_values = [value for value, _label in paired]
            clean_labels = [label for _value, label in paired]
            auc = _binary_auc(clean_values, clean_labels)
            high_is_target = auc >= 0.5
            threshold_report = _best_binary_threshold(clean_values, clean_labels, high_is_target)
            positives = [value for value, label in paired if label]
            negatives = [value for value, label in paired if not label]

            rows.append(
                {
                    "target_label": target_label,
                    "positive_raw_labels": ",".join(LABEL_GROUPS.get(target_label, [target_label])),
                    "score_key": spec["key"],
                    "score_title": spec["title"],
                    "eta_squared": _binary_eta_squared(clean_values, clean_labels),
                    "auc_best_direction": max(auc, 1 - auc),
                    "direction": "high_is_target" if high_is_target else "low_is_target",
                    "threshold": threshold_report["threshold"],
                    "threshold_rule": (
                        f"{spec['key']} >= {threshold_report['threshold']:.6g}"
                        if high_is_target
                        else f"{spec['key']} <= {threshold_report['threshold']:.6g}"
                    ),
                    "f1": threshold_report["f1"],
                    "accuracy": threshold_report["accuracy"],
                    "precision": threshold_report["precision"],
                    "recall": threshold_report["recall"],
                    "positive_mean": mean(positives),
                    "rest_mean": mean(negatives),
                    "positive_n": len(positives),
                    "rest_n": len(negatives),
                }
            )

    return sorted(
        rows,
        key=lambda row: (
            _label_sort_key(str(row["target_label"])),
            -float(row["f1"]),
            -float(row["auc_best_direction"]),
            -float(row["eta_squared"]),
        ),
    )


def plot_one_vs_rest_classification_standards(
    rows: List[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot the best one-vs-rest classification standard for each label."""
    plt = _import_pyplot()
    if not rows:
        _write_empty_plot(plt, output_path, "No one-vs-rest standards found")
        return

    best_by_label: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        label = str(row["target_label"])
        if label not in best_by_label:
            best_by_label[label] = row

    labels = sorted(best_by_label, key=_label_sort_key)
    f1_values = [float(best_by_label[label]["f1"]) for label in labels]
    auc_values = [float(best_by_label[label]["auc_best_direction"]) for label in labels]
    score_names = [str(best_by_label[label]["score_key"]) for label in labels]

    fig, ax = plt.subplots(figsize=(max(10, len(labels) * 1.8), 6))
    positions = list(range(len(labels)))
    width = 0.36
    ax.bar([pos - width / 2 for pos in positions], f1_values, width=width, label="best F1", color="#2c7fb8")
    ax.bar([pos + width / 2 for pos in positions], auc_values, width=width, label="AUC", color="#7fcdbb")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score")
    ax.set_title("Best One-vs-Rest Classification Standard by Label")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    for pos, label, score_name in zip(positions, labels, score_names):
        ax.text(pos, 1.02, score_name, ha="center", va="bottom", rotation=45, fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def build_binary_label_pair_score_report(
    file_records: Iterable[Dict[str, Any]],
    negative_label: str,
    positive_label: str,
) -> Dict[str, Any]:
    """Evaluate single-score threshold rules for a binary label pair."""
    records_list = [
        record
        for record in file_records
        if str(record.get("label") or "") in {negative_label, positive_label}
    ]
    summary_rows: List[Dict[str, Any]] = []
    threshold_rows: List[Dict[str, Any]] = []
    recall_constrained_rows: List[Dict[str, Any]] = []
    high_recall_rows: List[Dict[str, Any]] = []
    file_score_rows: List[Dict[str, Any]] = []

    if not records_list:
        return {
            "summary_rows": [],
            "threshold_rows": [],
            "recall_constrained_rows": [],
            "high_recall_rows": [],
            "file_score_rows": [],
            "best_score_key": "",
        }

    for record in records_list:
        row = {
            "label": str(record.get("label") or ""),
            "binary_label": positive_label if str(record.get("label") or "") == positive_label else negative_label,
            "is_positive": 1 if str(record.get("label") or "") == positive_label else 0,
            "file_name": str(record.get("file_name") or ""),
        }
        for key, raw_value in record.items():
            value = _to_float(raw_value)
            if value is not None:
                row[key] = value
        file_score_rows.append(row)

    labels = [int(row["is_positive"]) for row in file_score_rows]
    if not any(labels) or all(labels):
        return {
            "summary_rows": [],
            "threshold_rows": [],
            "recall_constrained_rows": [],
            "high_recall_rows": [],
            "file_score_rows": file_score_rows,
            "best_score_key": "",
        }

    candidate_specs = list(EVALUATION_SCORE_SPECS)
    candidate_specs.extend(
        _add_binary_lda_candidate_scores(
            file_score_rows,
            negative_label=negative_label,
            positive_label=positive_label,
        )
    )

    for spec in candidate_specs:
        paired = [
            (float(row[spec["key"]]), int(row["is_positive"]))
            for row in file_score_rows
            if spec["key"] in row
        ]
        if len(paired) < 2:
            continue
        values = [value for value, _label in paired]
        binary_labels = [label for _value, label in paired]
        positives = [value for value, label in paired if label]
        negatives = [value for value, label in paired if not label]
        if len(positives) < 1 or len(negatives) < 1:
            continue

        auc = _binary_auc(values, binary_labels)
        high_is_positive = auc >= 0.5
        threshold_report = _best_binary_threshold(values, binary_labels, high_is_positive)
        threshold_candidates = _binary_threshold_candidates(values, binary_labels, high_is_positive)
        direction = f"high_is_{positive_label}" if high_is_positive else f"low_is_{positive_label}"
        eta2 = _binary_eta_squared(values, binary_labels)
        row = {
            "score_key": spec["key"],
            "eta2": eta2,
            "f1": threshold_report["f1"],
            "f2": threshold_report["f2"],
            "accuracy": threshold_report["accuracy"],
            "precision": threshold_report["precision"],
            "recall": threshold_report["recall"],
            "specificity": threshold_report["specificity"],
            "balanced_accuracy": threshold_report["balanced_accuracy"],
            "auc_best_direction": max(auc, 1 - auc),
            "direction": direction,
            "threshold": threshold_report["threshold"],
            "tp": threshold_report["tp"],
            "fp": threshold_report["fp"],
            "tn": threshold_report["tn"],
            "fn": threshold_report["fn"],
            f"{positive_label}_mean": mean(positives),
            f"{negative_label}_mean": mean(negatives),
            f"{positive_label}_n": len(positives),
            f"{negative_label}_n": len(negatives),
        }
        summary_rows.append(row)
        threshold_rows.append(
            {
                "score_key": spec["key"],
                "direction": direction,
                "threshold": threshold_report["threshold"],
                "f1": threshold_report["f1"],
                "f2": threshold_report["f2"],
                "precision": threshold_report["precision"],
                "recall": threshold_report["recall"],
                "accuracy": threshold_report["accuracy"],
                "specificity": threshold_report["specificity"],
                "balanced_accuracy": threshold_report["balanced_accuracy"],
                "tp": threshold_report["tp"],
                "fp": threshold_report["fp"],
                "tn": threshold_report["tn"],
                "fn": threshold_report["fn"],
                "n": len(binary_labels),
            }
        )
        for recall_cap in RECALL_CONSTRAINTS:
            feasible = [
                candidate
                for candidate in threshold_candidates
                if 0 < float(candidate["recall"]) <= recall_cap
            ]
            if not feasible:
                continue
            constrained = max(
                feasible,
                key=lambda candidate: (
                    float(candidate["f1"]),
                    float(candidate["balanced_accuracy"]),
                    float(candidate["precision"]),
                    float(candidate["specificity"]),
                ),
            )
            recall_constrained_rows.append(
                {
                    "recall_cap": recall_cap,
                    "score_key": spec["key"],
                    "eta2": eta2,
                    "f1": constrained["f1"],
                    "f2": constrained["f2"],
                    "accuracy": constrained["accuracy"],
                    "precision": constrained["precision"],
                    "recall": constrained["recall"],
                    "specificity": constrained["specificity"],
                    "balanced_accuracy": constrained["balanced_accuracy"],
                    "auc_best_direction": max(auc, 1 - auc),
                    "direction": direction,
                    "threshold": constrained["threshold"],
                    "tp": constrained["tp"],
                    "fp": constrained["fp"],
                    "tn": constrained["tn"],
                    "fn": constrained["fn"],
                    f"{positive_label}_mean": mean(positives),
                    f"{negative_label}_mean": mean(negatives),
                    f"{positive_label}_n": len(positives),
                    f"{negative_label}_n": len(negatives),
                }
            )
        for recall_floor in HIGH_RECALL_FLOORS:
            feasible = [
                candidate
                for candidate in threshold_candidates
                if float(candidate["recall"]) >= recall_floor
            ]
            if not feasible:
                continue
            high_recall = max(
                feasible,
                key=lambda candidate: (
                    float(candidate["f2"]),
                    float(candidate["precision"]),
                    float(candidate["balanced_accuracy"]),
                    float(candidate["specificity"]),
                ),
            )
            high_recall_rows.append(
                {
                    "recall_floor": recall_floor,
                    "score_key": spec["key"],
                    "eta2": eta2,
                    "f1": high_recall["f1"],
                    "f2": high_recall["f2"],
                    "accuracy": high_recall["accuracy"],
                    "precision": high_recall["precision"],
                    "recall": high_recall["recall"],
                    "specificity": high_recall["specificity"],
                    "balanced_accuracy": high_recall["balanced_accuracy"],
                    "auc_best_direction": max(auc, 1 - auc),
                    "direction": direction,
                    "threshold": high_recall["threshold"],
                    "tp": high_recall["tp"],
                    "fp": high_recall["fp"],
                    "tn": high_recall["tn"],
                    "fn": high_recall["fn"],
                    f"{positive_label}_mean": mean(positives),
                    f"{negative_label}_mean": mean(negatives),
                    f"{positive_label}_n": len(positives),
                    f"{negative_label}_n": len(negatives),
                }
            )

    summary_rows = sorted(
        summary_rows,
        key=lambda row: (float(row["f1"]), float(row["eta2"]), float(row["auc_best_direction"])),
        reverse=True,
    )
    threshold_rows = sorted(
        threshold_rows,
        key=lambda row: (float(row["f1"]), float(row["balanced_accuracy"])),
        reverse=True,
    )
    recall_constrained_rows = sorted(
        recall_constrained_rows,
        key=lambda row: (
            float(row["recall_cap"]),
            -float(row["f1"]),
            -float(row["eta2"]),
            -float(row["balanced_accuracy"]),
        ),
    )
    high_recall_rows = sorted(
        high_recall_rows,
        key=lambda row: (
            float(row["recall_floor"]),
            -float(row["f2"]),
            -float(row["precision"]),
            -float(row["eta2"]),
        ),
    )
    best_score_key = str(summary_rows[0]["score_key"]) if summary_rows else ""
    return {
        "summary_rows": summary_rows,
        "threshold_rows": threshold_rows,
        "recall_constrained_rows": recall_constrained_rows,
        "high_recall_rows": high_recall_rows,
        "file_score_rows": file_score_rows,
        "best_score_key": best_score_key,
    }


def plot_binary_label_pair_best_score(
    file_score_rows: List[Dict[str, Any]],
    score_key: str,
    output_path: str | os.PathLike[str],
    negative_label: str,
    positive_label: str,
) -> None:
    """Plot the best single score for a binary label pair."""
    plt = _import_pyplot()
    if not file_score_rows or not score_key:
        _write_empty_plot(plt, output_path, "No binary pair score records found")
        return

    grouped = {
        negative_label: [
            _to_float(row.get(score_key))
            for row in file_score_rows
            if str(row.get("label") or "") == negative_label
        ],
        positive_label: [
            _to_float(row.get(score_key))
            for row in file_score_rows
            if str(row.get("label") or "") == positive_label
        ],
    }
    labels = [negative_label, positive_label]
    values = [[value for value in grouped[label] if value is not None] for label in labels]
    if not any(values):
        _write_empty_plot(plt, output_path, "No binary pair score records found")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    try:
        ax.boxplot(values, tick_labels=labels, showmeans=True, patch_artist=True)
    except TypeError:
        ax.boxplot(values, labels=labels, showmeans=True, patch_artist=True)
    ax.set_title(f"{negative_label} vs {positive_label}: Best Single Score")
    ax.set_xlabel("Class label")
    ax.set_ylabel(score_key)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_binary_high_recall_scores(
    rows: List[Dict[str, Any]],
    output_path: str | os.PathLike[str],
    negative_label: str,
    positive_label: str,
) -> None:
    """Plot top high-recall binary classification candidates."""
    plt = _import_pyplot()
    if not rows:
        _write_empty_plot(plt, output_path, "No high-recall binary score records found")
        return

    best_by_floor: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        floor = str(row.get("recall_floor") or "")
        current = best_by_floor.get(floor)
        if current is None or (
            float(row.get("f2") or 0.0),
            float(row.get("precision") or 0.0),
            float(row.get("eta2") or 0.0),
        ) > (
            float(current.get("f2") or 0.0),
            float(current.get("precision") or 0.0),
            float(current.get("eta2") or 0.0),
        ):
            best_by_floor[floor] = row

    selected = [
        best_by_floor[floor]
        for floor in sorted(best_by_floor, key=lambda value: float(value))
    ]
    labels = [f"recall >= {float(row['recall_floor']):.2f}" for row in selected]
    metrics = ["f2", "f1", "precision", "recall", "eta2"]
    colors = ["#2c7fb8", "#7fcdbb", "#fdae61", "#d7191c", "#756bb1"]

    x_positions = list(range(len(selected)))
    width = 0.14
    fig, ax = plt.subplots(figsize=(max(10, len(selected) * 2.2), 6))
    for metric_index, metric in enumerate(metrics):
        values = [float(row.get(metric) or 0.0) for row in selected]
        offset = (metric_index - (len(metrics) - 1) / 2) * width
        ax.bar(
            [pos + offset for pos in x_positions],
            values,
            width=width,
            label=metric,
            color=colors[metric_index],
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("score")
    ax.set_title(f"{negative_label} vs {positive_label}: High-Recall Candidate Metrics")
    ax.legend(ncol=len(metrics), loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax.grid(axis="y", alpha=0.25)

    for pos, row in zip(x_positions, selected):
        score_key = str(row.get("score_key") or "")
        threshold = float(row.get("threshold") or 0.0)
        ax.text(
            pos,
            1.02,
            f"{score_key}\nth={threshold:.3g}",
            ha="center",
            va="bottom",
            fontsize=8,
            rotation=30,
        )

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _add_binary_lda_candidate_scores(
    file_score_rows: List[Dict[str, Any]],
    negative_label: str,
    positive_label: str,
) -> List[Dict[str, Any]]:
    """Add LDA-style linear composite scores for a binary label pair."""
    import numpy as np

    if not file_score_rows:
        return []

    excluded_keys = {
        "label",
        "raw_label",
        "raw_labels",
        "binary_label",
        "is_positive",
        "file_name",
        "source_file",
        "source_files",
        "turn",
        "phase_turn",
        "worst_turn",
    }
    numeric_keys = [
        key
        for key in file_score_rows[0]
        if key not in excluded_keys
        and all(_to_float(row.get(key)) is not None for row in file_score_rows)
        and len({_to_float(row.get(key)) for row in file_score_rows}) > 1
    ]
    labels = [int(row["is_positive"]) for row in file_score_rows]
    if len(numeric_keys) < 2 or not any(labels) or all(labels):
        return []

    matrix = np.array(
        [[float(_to_float(row.get(key)) or 0.0) for key in numeric_keys] for row in file_score_rows],
        dtype=float,
    )
    label_array = np.array(labels, dtype=int)
    standardized, _, _ = _standardize_matrix(matrix)
    single_rank = sorted(
        [
            (_binary_eta_squared(standardized[:, idx].tolist(), labels), idx)
            for idx in range(len(numeric_keys))
        ],
        reverse=True,
    )
    ordered_indices = [idx for _eta, idx in single_rank]

    candidate_specs = []
    top_ns = [3, 5, 8, 12, 20, 30, min(50, len(numeric_keys)), len(numeric_keys)]
    seen_top_ns = []
    for top_n in top_ns:
        if top_n < 1 or top_n in seen_top_ns:
            continue
        seen_top_ns.append(top_n)
        selected = ordered_indices[:top_n]
        score_key = f"{negative_label}_vs_{positive_label}_lda_top_{top_n}_score"
        scores = _ridge_lda_score(standardized[:, selected], label_array).tolist()
        for row, score in zip(file_score_rows, scores):
            row[score_key] = float(score)
        candidate_specs.append(
            {
                "key": score_key,
                "title": f"{negative_label} vs {positive_label} LDA Top {top_n}",
                "higher_is_better": True,
            }
        )

    return candidate_specs


def plot_category_boxplot_grid(
    records: Iterable[Dict[str, Any]],
    category_key: str,
    output_path: str | os.PathLike[str],
    title: str,
    value_key: str = "consistency_score_mean",
) -> None:
    """Create one label boxplot per phase or role."""
    plt = _import_pyplot()
    records_list = list(records)
    categories = sorted({str(record.get(category_key) or "") for record in records_list if record.get(category_key)})
    labels = sorted({str(record.get("label") or "") for record in records_list if record.get("label")}, key=_label_sort_key)
    if not categories or not labels:
        _write_empty_plot(plt, output_path, f"No {category_key} records found")
        return

    ncols = min(3, len(categories))
    nrows = math.ceil(len(categories) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(max(12, ncols * 5), max(4, nrows * 3.5)), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")

    for idx, category in enumerate(categories):
        ax = axes[idx // ncols][idx % ncols]
        ax.axis("on")
        values = []
        used_labels = []
        for label in labels:
            label_values = [
                float(record[value_key])
                for record in records_list
                if str(record.get(category_key) or "") == category
                and str(record.get("label") or "") == label
                and _to_float(record.get(value_key)) is not None
            ]
            if label_values:
                values.append(label_values)
                used_labels.append(label)
        if values:
            try:
                ax.boxplot(values, tick_labels=used_labels, showmeans=True, patch_artist=True)
            except TypeError:
                ax.boxplot(values, labels=used_labels, showmeans=True, patch_artist=True)
        ax.set_title(category)
        ax.set_ylim(-0.03, 1.03)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(axis="y", alpha=0.2)

    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def compute_label_overlap(file_records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute overlap between labels using scored JSON file names as sample IDs."""
    sample_to_labels: Dict[str, set] = defaultdict(set)
    for record in file_records:
        file_name = str(record.get("file_name") or "")
        label = str(record.get("label") or "")
        if file_name and label:
            sample_to_labels[file_name].add(label)

    labels = sorted({label for labels_set in sample_to_labels.values() for label in labels_set}, key=_label_sort_key)
    label_to_samples = {
        label: {sample for sample, labels_set in sample_to_labels.items() if label in labels_set}
        for label in labels
    }

    count_matrix: List[List[float]] = []
    jaccard_matrix: List[List[float]] = []
    rows: List[Dict[str, Any]] = []
    for row_label in labels:
        count_row = []
        jaccard_row = []
        row_samples = label_to_samples[row_label]
        for col_label in labels:
            col_samples = label_to_samples[col_label]
            intersection = row_samples & col_samples
            union = row_samples | col_samples
            count = len(intersection)
            jaccard = count / len(union) if union else 0.0
            count_row.append(float(count))
            jaccard_row.append(float(jaccard))
            rows.append(
                {
                    "label_a": row_label,
                    "label_b": col_label,
                    "label_a_files": len(row_samples),
                    "label_b_files": len(col_samples),
                    "shared_files": count,
                    "union_files": len(union),
                    "jaccard_overlap": jaccard,
                }
            )
        count_matrix.append(count_row)
        jaccard_matrix.append(jaccard_row)

    return {
        "labels": labels,
        "count_matrix": count_matrix,
        "jaccard_matrix": jaccard_matrix,
        "rows": rows,
        "multi_label_samples": sum(len(labels_set) > 1 for labels_set in sample_to_labels.values()),
        "num_samples": len(sample_to_labels),
    }


def plot_label_overlap_heatmap(
    labels: List[str],
    matrix: List[List[float]],
    output_path: str | os.PathLike[str],
    title: str,
    colorbar_label: str,
    value_format: str,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
) -> None:
    """Plot a square label-overlap heatmap."""
    plt = _import_pyplot()
    if not labels:
        _write_empty_plot(plt, output_path, "No label overlap records found")
        return

    fig_size = max(8, min(18, len(labels) * 0.75))
    fig, ax = plt.subplots(figsize=(fig_size, fig_size))
    image = ax.imshow(matrix, aspect="equal", cmap="Blues", vmin=vmin, vmax=vmax)
    ax.set_title(title)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_xlabel("Class label")
    ax.set_ylabel("Class label")
    fig.colorbar(image, ax=ax, label=colorbar_label)

    for row_idx, _row_label in enumerate(labels):
        for col_idx, _col_label in enumerate(labels):
            value = matrix[row_idx][col_idx]
            ax.text(col_idx, row_idx, value_format.format(value), ha="center", va="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_overlap_cluster_scatter(
    labels: List[str],
    similarity_matrix: List[List[float]],
    cluster_by_label: Dict[str, int],
    output_path: str | os.PathLike[str],
    edge_threshold: float = 0.5,
) -> None:
    """Plot labels as 2D points from classical MDS over overlap distance."""
    import numpy as np

    plt = _import_pyplot()
    if not labels:
        _write_empty_plot(plt, output_path, "No overlap cluster records found")
        return

    similarity = np.array(similarity_matrix, dtype=float)
    distance = 1.0 - similarity
    coords = _classical_mds_2d(distance)
    clusters = sorted({cluster_by_label[label] for label in labels})
    colors = plt.cm.tab10(range(len(clusters)))
    color_by_cluster = {cluster: colors[idx] for idx, cluster in enumerate(clusters)}

    fig, ax = plt.subplots(figsize=(9, 7))
    for row_idx, label_a in enumerate(labels):
        for col_idx in range(row_idx + 1, len(labels)):
            value = similarity[row_idx, col_idx]
            if value >= edge_threshold:
                ax.plot(
                    [coords[row_idx, 0], coords[col_idx, 0]],
                    [coords[row_idx, 1], coords[col_idx, 1]],
                    color="gray",
                    alpha=min(0.75, float(value)),
                    linewidth=1 + 3 * float(value),
                    zorder=1,
                )
                midpoint_x = (coords[row_idx, 0] + coords[col_idx, 0]) / 2
                midpoint_y = (coords[row_idx, 1] + coords[col_idx, 1]) / 2
                ax.text(midpoint_x, midpoint_y, f"{value:.2f}", fontsize=8, color="dimgray")

    for idx, label in enumerate(labels):
        cluster = cluster_by_label[label]
        ax.scatter(
            coords[idx, 0],
            coords[idx, 1],
            s=180,
            color=color_by_cluster[cluster],
            edgecolor="black",
            linewidth=0.8,
            label=f"C{cluster}",
            zorder=2,
        )
        ax.text(coords[idx, 0] + 0.015, coords[idx, 1] + 0.015, label, fontsize=12, weight="bold")

    handles, legend_labels = ax.get_legend_handles_labels()
    dedup = dict(zip(legend_labels, handles))
    ax.legend(dedup.values(), dedup.keys(), title="Cluster")
    ax.set_title("Overlap-Based Label Clusters after Excluding Small Labels")
    ax.set_xlabel("MDS dimension 1 from overlap distance")
    ax.set_ylabel("MDS dimension 2 from overlap distance")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def cluster_labels_by_overlap(
    file_records: Iterable[Dict[str, Any]],
    labels: List[str],
    k: int = 4,
) -> Dict[str, Any]:
    """Cluster labels by normalized sample overlap, robust to unequal label sizes."""
    sample_to_labels: Dict[str, set] = defaultdict(set)
    for record in file_records:
        label = str(record.get("label") or "")
        file_name = str(record.get("file_name") or "")
        if label in labels and file_name:
            sample_to_labels[file_name].add(label)

    labels = [label for label in labels if any(label in values for values in sample_to_labels.values())]
    label_to_samples = {
        label: {sample for sample, values in sample_to_labels.items() if label in values}
        for label in labels
    }
    similarity_matrix: List[List[float]] = []
    for label_a in labels:
        row = []
        samples_a = label_to_samples[label_a]
        for label_b in labels:
            samples_b = label_to_samples[label_b]
            shared = len(samples_a & samples_b)
            denom = math.sqrt(len(samples_a) * len(samples_b))
            row.append(shared / denom if denom else 0.0)
        similarity_matrix.append(row)

    assignments = _average_linkage_clusters(labels, similarity_matrix, k=min(k, len(labels)))
    cluster_by_label = {label: int(assignments[idx]) + 1 for idx, label in enumerate(labels)}
    rows = []
    for idx, label in enumerate(labels):
        samples = label_to_samples[label]
        neighbors = []
        for other_idx, other in enumerate(labels):
            if other == label:
                continue
            shared = len(samples & label_to_samples[other])
            union = len(samples | label_to_samples[other])
            min_size = min(len(samples), len(label_to_samples[other]))
            neighbors.append(
                {
                    "label": other,
                    "cosine_overlap": similarity_matrix[idx][other_idx],
                    "shared": shared,
                    "jaccard": shared / union if union else 0.0,
                    "containment": shared / min_size if min_size else 0.0,
                }
            )
        neighbors.sort(key=lambda item: item["cosine_overlap"], reverse=True)
        rows.append(
            {
                "label": label,
                "cluster": cluster_by_label[label],
                "num_files": len(samples),
                "nearest_labels_by_cosine_overlap": "; ".join(
                    f"{item['label']}:{item['cosine_overlap']:.3f}({item['shared']})"
                    for item in neighbors[:4]
                ),
                "max_jaccard_overlap": max((item["jaccard"] for item in neighbors), default=0.0),
                "max_containment_overlap": max((item["containment"] for item in neighbors), default=0.0),
            }
        )

    return {
        "labels": labels,
        "similarity_matrix": similarity_matrix,
        "cluster_by_label": cluster_by_label,
        "rows": rows,
    }


def plot_overlap_cluster_heatmap(
    labels: List[str],
    similarity_matrix: List[List[float]],
    cluster_by_label: Dict[str, int],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot cosine-normalized sample overlap sorted by overlap cluster."""
    plt = _import_pyplot()
    if not labels:
        _write_empty_plot(plt, output_path, "No overlap cluster records found")
        return

    order = sorted(range(len(labels)), key=lambda idx: (cluster_by_label[labels[idx]], _label_sort_key(labels[idx])))
    ordered_labels = [labels[idx] for idx in order]
    ordered_matrix = [[similarity_matrix[row][col] for col in order] for row in order]

    fig, ax = plt.subplots(figsize=(9, 8))
    image = ax.imshow(ordered_matrix, aspect="equal", cmap="YlGnBu", vmin=0, vmax=1)
    ax.set_title("Overlap-Based Label Clusters (cosine-normalized shared JSONs)")
    ax.set_xticks(range(len(ordered_labels)))
    ax.set_xticklabels(ordered_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(ordered_labels)))
    ax.set_yticklabels(ordered_labels)
    ax.set_xlabel("Class label")
    ax.set_ylabel("Class label")
    fig.colorbar(image, ax=ax, label="shared / sqrt(label_a_files * label_b_files)")
    for row_idx, label_a in enumerate(ordered_labels):
        for col_idx, label_b in enumerate(ordered_labels):
            value = ordered_matrix[row_idx][col_idx]
            ax.text(col_idx, row_idx, f"{value:.2f}", ha="center", va="center", fontsize=8)
        ax.text(
            len(ordered_labels) + 0.15,
            row_idx,
            f"C{cluster_by_label[label_a]}",
            va="center",
            fontsize=9,
        )
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def cluster_labels_for_consistency(
    turn_records: Iterable[Dict[str, Any]],
    file_records: Iterable[Dict[str, Any]],
    labels: Optional[List[str]] = None,
    k: int = 4,
) -> Dict[str, Any]:
    """Cluster non-baseline labels using interpretable consistency features."""
    import numpy as np

    turn_records_list = list(turn_records)
    file_records_list = list(file_records)
    if labels is None:
        labels = sorted(
            {
                str(record.get("label") or "")
                for record in file_records_list
                if str(record.get("label") or "") and str(record.get("label") or "") != "c0"
            },
            key=_label_sort_key,
        )

    base_features = [
        "consistency_score_file_mean",
        "consistency_score_file_median",
        "consistency_score_file_q75",
        "consistency_score_file_q25",
        "consistency_score_file_q10",
        "consistency_score_file_std",
        "consistency_score_file_iqr",
        "low_score_rate_0_2",
        "low_score_rate_0_5",
        "high_score_rate_0_7",
        "high_score_rate_0_8",
        "high_score_rate_0_9",
        "worst_score",
    ]
    phases = sorted({str(record.get("phase") or "") for record in turn_records_list if record.get("phase")})
    roles = sorted({str(record.get("role") or "") for record in turn_records_list if record.get("role")})

    feature_names = (
        base_features
        + [f"phase_mean::{phase}" for phase in phases]
        + [f"role_mean::{role}" for role in roles]
    )

    rows_by_label: Dict[str, List[Dict[str, Any]]] = {
        label: [record for record in file_records_list if str(record.get("label") or "") == label]
        for label in labels
    }
    turns_by_label: Dict[str, List[Dict[str, Any]]] = {
        label: [record for record in turn_records_list if str(record.get("label") or "") == label]
        for label in labels
    }

    matrix = []
    raw_feature_rows = []
    for label in labels:
        row = []
        file_rows = rows_by_label[label]
        turn_rows = turns_by_label[label]
        for feature in base_features:
            values = [_to_float(record.get(feature)) for record in file_rows]
            values = [value for value in values if value is not None]
            row.append(mean(values) if values else 0.0)
        for phase in phases:
            values = [
                _to_float(record.get("consistency_score_mean"))
                for record in turn_rows
                if str(record.get("phase") or "") == phase
            ]
            values = [value for value in values if value is not None]
            row.append(mean(values) if values else 0.0)
        for role in roles:
            values = [
                _to_float(record.get("consistency_score_mean"))
                for record in turn_rows
                if str(record.get("role") or "") == role
            ]
            values = [value for value in values if value is not None]
            row.append(mean(values) if values else 0.0)
        matrix.append(row)
        raw_feature_rows.append(dict(zip(feature_names, row)))

    x = np.array(matrix, dtype=float)
    z, _, _ = _standardize_matrix(x)
    assignments = _kmeans_deterministic(z, k=min(k, len(labels)))
    pca = _pca_2d(z)

    rows = []
    for idx, label in enumerate(labels):
        row = {
            "label": label,
            "cluster": int(assignments[idx]) + 1,
            "pca_x": float(pca[idx, 0]),
            "pca_y": float(pca[idx, 1]),
            "num_files": len(rows_by_label[label]),
            "num_turns": len(turns_by_label[label]),
        }
        row.update(raw_feature_rows[idx])
        rows.append(row)

    return {"rows": rows, "feature_names": feature_names}


def plot_label_cluster_pca(
    cluster_rows: List[Dict[str, Any]],
    output_path: str | os.PathLike[str],
) -> None:
    """Plot 2D PCA projection of label-level clustering features."""
    plt = _import_pyplot()
    if not cluster_rows:
        _write_empty_plot(plt, output_path, "No label cluster records found")
        return

    clusters = sorted({int(row["cluster"]) for row in cluster_rows})
    colors = plt.cm.tab10(range(len(clusters)))
    color_by_cluster = {cluster: colors[idx] for idx, cluster in enumerate(clusters)}

    fig, ax = plt.subplots(figsize=(9, 7))
    for row in cluster_rows:
        cluster = int(row["cluster"])
        x = float(row["pca_x"])
        y = float(row["pca_y"])
        ax.scatter(x, y, s=120, color=color_by_cluster[cluster], label=f"C{cluster}")
        ax.text(x + 0.03, y + 0.03, str(row["label"]), fontsize=10)
    handles, labels = ax.get_legend_handles_labels()
    dedup = dict(zip(labels, handles))
    ax.legend(dedup.values(), dedup.keys(), title="Cluster")
    ax.set_title("Label Clusters from Consistency Feature Vectors")
    ax.set_xlabel("PCA component 1")
    ax.set_ylabel("PCA component 2")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Visualize classified ChatDev logprob consistency scores.",
    )
    parser.add_argument(
        "--scored-root",
        default=str(DEFAULT_SCORED_ROOT),
        help="Root directory containing classified *_scored.json files.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for CSV and PNG outputs. Defaults to <scored-root>/_visualizations.",
    )
    parser.add_argument(
        "--include-trajectory",
        action="store_true",
        help="Include trajectory/ records. Default excludes them to avoid duplicate samples.",
    )
    args = parser.parse_args(argv)

    report = write_visualization_report(
        scored_root=args.scored_root,
        output_dir=args.output_dir,
        include_trajectory=args.include_trajectory,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as file:
        if not fieldnames:
            file.write("")
            return
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_markdown_report(path: Path, report: Dict[str, Any], summary: List[Dict[str, Any]]) -> None:
    lines = [
        "# ChatDev Consistency Visualization",
        "",
        f"- Scored root: `{report['scored_root']}`",
        f"- Records: `{report['num_records']}`",
        f"- File-level records: `{report['num_file_records']}`",
        f"- Labels: `{report['num_labels']}`",
        f"- Include trajectory: `{report['include_trajectory']}`",
        f"- Label groups: `{json.dumps(report['label_groups'], ensure_ascii=False)}`",
        "",
        "## Label Summary",
        "",
        "| label | files | turns | mean | median | q1 | q3 | min | max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        lines.append(
            "| {label} | {num_files} | {num_turns} | {mean:.4f} | {median:.4f} | "
            "{q1:.4f} | {q3:.4f} | {min:.4f} | {max:.4f} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- Turn records CSV: `{Path(report['records_csv']).name}`",
            f"- File records CSV: `{Path(report['file_records_csv']).name}`",
            f"- Label summary CSV: `{Path(report['summary_csv']).name}`",
            f"- File-level label summary CSV: `{Path(report['file_summary_csv']).name}`",
            f"- Label boxplot: `{Path(report['boxplot_png']).name}`",
            f"- File-level label boxplot: `{Path(report['file_boxplot_png']).name}`",
            f"- Label-phase heatmap: `{Path(report['phase_heatmap_png']).name}`",
            f"- Label-role heatmap: `{Path(report['role_heatmap_png']).name}`",
            f"- ECDF curves: `{Path(report['ecdf_png']).name}`",
            f"- Low/high score rate bars: `{Path(report['file_low_rate_png']).name}`",
            f"- High-score-rate threshold heatmap: `{Path(report['high_rate_heatmap_png']).name}`",
            f"- High/low ratio boxplot: `{Path(report['high_low_ratio_boxplot_png']).name}`",
            "- High-score-rate boxplots:",
            *[
                f"  - `{Path(path).name}`"
                for _threshold, path in sorted(report["high_rate_boxplot_pngs"].items())
            ],
            f"- File feature heatmap: `{Path(report['file_feature_heatmap_png']).name}`",
            f"- Evaluation score boxplot grid: `{Path(report['evaluation_score_boxplots_png']).name}`",
            f"- Evaluation score summary CSV: `{Path(report['evaluation_score_summary_csv']).name}`",
            f"- Evaluation score separation rank CSV: `{Path(report['evaluation_score_rank_csv']).name}`",
            f"- c3-positive score candidates CSV: `{Path(report['c3_positive_score_csv']).name}`",
            f"- c3-positive score eta-squared plot: `{Path(report['c3_positive_score_boxplots_png']).name}`",
            f"- One-vs-rest best classification standards CSV: `{Path(report['one_vs_rest_standards_csv']).name}`",
            f"- One-vs-rest best classification standards plot: `{Path(report['one_vs_rest_standards_png']).name}`",
            f"- c0-vs-c1 eta2/F1 summary CSV: `{Path(report['c0_vs_c1_summary_csv']).name}`",
            f"- c0-vs-c1 threshold CSV: `{Path(report['c0_vs_c1_thresholds_csv']).name}`",
            f"- c0-vs-c1 recall-constrained eta2/F1 summary CSV: `{Path(report['c0_vs_c1_recall_constrained_csv']).name}`",
            f"- c0-vs-c1 high-recall eta2/F2 summary CSV: `{Path(report['c0_vs_c1_high_recall_csv']).name}`",
            f"- c0-vs-c1 high-recall eta2/F2 plot: `{Path(report['c0_vs_c1_high_recall_png']).name}`",
            f"- c0-vs-c1 best-score boxplot: `{Path(report['c0_vs_c1_boxplot_png']).name}`",
            f"- Phase boxplot grid: `{Path(report['phase_boxplots_png']).name}`",
            f"- Role boxplot grid: `{Path(report['role_boxplots_png']).name}`",
            f"- Worst-turn score boxplot: `{Path(report['worst_score_png']).name}`",
            f"- Label overlap count heatmap: `{Path(report['overlap_count_heatmap_png']).name}`",
            f"- Label overlap Jaccard heatmap: `{Path(report['overlap_jaccard_heatmap_png']).name}`",
            f"- Label overlap CSV: `{Path(report['overlap_csv']).name}`",
            f"- Label cluster assignments: `{Path(report['label_cluster_csv']).name}`",
            f"- Label cluster PCA: `{Path(report['label_cluster_png']).name}`",
            f"- Core c0-to-c4 cluster assignments: `{Path(report['core_label_cluster_csv']).name}`",
            f"- Core c0-to-c4 cluster PCA: `{Path(report['core_label_cluster_png']).name}`",
            f"- Core c0-to-c4 overlap cluster assignments: `{Path(report['core_overlap_cluster_csv']).name}`",
            f"- Core c0-to-c4 overlap cluster heatmap: `{Path(report['core_overlap_cluster_png']).name}`",
            "- Core c1-to-c4 overlap clusters:",
            *[
                f"  - k={k}: `{Path(paths['csv']).name}`, `{Path(paths['png']).name}`, `{Path(paths['scatter_png']).name}`"
                for k, paths in sorted(report["core_major_overlap_cluster_outputs"].items())
            ],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _import_pyplot():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError(
            "matplotlib is required for consistency visualizations. "
            "Install matplotlib or run in the project environment."
        ) from exc
    return plt


def _write_empty_plot(plt: Any, output_path: str | os.PathLike[str], message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result):
        return None
    return result


def _safe_ratio(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return numerator / denominator


def _with_threshold_rates(row: Dict[str, Any], scores: List[float]) -> Dict[str, Any]:
    for threshold in HIGH_SCORE_THRESHOLDS:
        row[f"high_score_rate_{_threshold_suffix(threshold)}"] = (
            sum(score >= threshold for score in scores) / len(scores)
        )
        row[f"low_score_rate_{_threshold_suffix(threshold)}"] = (
            sum(score < threshold for score in scores) / len(scores)
        )
    for high_threshold, low_threshold in HIGH_LOW_GAP_PAIRS:
        high_rate = row[f"high_score_rate_{_threshold_suffix(high_threshold)}"]
        low_rate = row[f"low_score_rate_{_threshold_suffix(low_threshold)}"]
        row[f"high_low_gap_{_threshold_suffix(high_threshold)}_{_threshold_suffix(low_threshold)}"] = (
            high_rate - low_rate
        )
        row[f"high_low_half_penalty_{_threshold_suffix(high_threshold)}_{_threshold_suffix(low_threshold)}"] = (
            high_rate - 0.5 * low_rate
        )
    return row


def _threshold_suffix(threshold: float) -> str:
    return str(threshold).replace(".", "_")


def _normalized_score_entropy(scores: List[float]) -> float:
    if not scores:
        return 0.0
    counts = [0 for _bin in SCORE_BINS[:-1]]
    for score in scores:
        for idx in range(len(SCORE_BINS) - 1):
            lower = SCORE_BINS[idx]
            upper = SCORE_BINS[idx + 1]
            if lower <= score < upper or (idx == len(SCORE_BINS) - 2 and score == upper):
                counts[idx] += 1
                break
    total = sum(counts)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counts:
        if count:
            probability = count / total
            entropy -= probability * math.log(probability)
    return entropy / math.log(len(counts)) if len(counts) > 1 else 0.0


def _group_turn_scores(records: Iterable[Dict[str, Any]], key: str) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for record in records:
        group = str(record.get(key) or "")
        score = _to_float(record.get("consistency_score_mean"))
        if group and score is not None:
            grouped[group].append(score)
    return grouped


def _rate_below(values: List[float], threshold: float) -> float:
    return sum(value < threshold for value in values) / len(values) if values else 0.0


def _add_standardized_composite(records: List[Dict[str, Any]], feature_keys: List[str], output_key: str) -> None:
    values_by_key: Dict[str, List[float]] = defaultdict(list)
    for record in records:
        for key in feature_keys:
            value = _to_float(record.get(key))
            if value is not None:
                values_by_key[key].append(value)

    stats = {}
    for key in feature_keys:
        values = values_by_key[key]
        if not values:
            stats[key] = (0.0, 1.0)
            continue
        center = mean(values)
        scale = pstdev(values) if len(values) > 1 else 1.0
        stats[key] = (center, scale if scale else 1.0)

    for record in records:
        components = []
        for key in feature_keys:
            value = _to_float(record.get(key))
            if value is None:
                continue
            center, scale = stats[key]
            components.append((value - center) / scale)
        record[output_key] = mean(components) if components else 0.0


def _build_file_phase_role_feature_rows(turn_records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    records = list(turn_records)
    phases = sorted({str(record.get("phase") or "") for record in records if record.get("phase")})
    roles = sorted({str(record.get("role") or "") for record in records if record.get("role")})
    for record in records:
        label = str(record.get("label") or "")
        file_name = str(record.get("file_name") or "")
        if label and file_name:
            grouped[(label, file_name)].append(record)

    rows = []
    for (label, file_name), items in sorted(grouped.items(), key=lambda item: (_label_sort_key(item[0][0]), item[0][1])):
        scores = [float(item["consistency_score_mean"]) for item in items]
        sorted_scores = sorted(scores)
        row = {
            "label": label,
            "file_name": file_name,
            "binary_label": "c3" if label == "c3" else "not_c3",
            "is_c3": 1 if label == "c3" else 0,
            "consistency_score_file_mean": mean(scores),
            "consistency_score_file_median": median(scores),
            "consistency_score_file_q10": _quantile(sorted_scores, 0.10),
            "consistency_score_file_q25": _quantile(sorted_scores, 0.25),
            "consistency_score_file_std": pstdev(scores) if len(scores) > 1 else 0.0,
            "low_score_rate_0_2": sum(score < 0.2 for score in scores) / len(scores),
            "low_score_rate_0_4": sum(score < 0.4 for score in scores) / len(scores),
            "low_score_rate_0_5": sum(score < 0.5 for score in scores) / len(scores),
            "high_score_rate_0_2": sum(score >= 0.2 for score in scores) / len(scores),
            "high_score_rate_0_8": sum(score >= 0.8 for score in scores) / len(scores),
            "num_turns": len(scores),
            "num_phases": len({str(item.get("phase") or "") for item in items}),
        }
        for phase in phases:
            values = [
                float(item["consistency_score_mean"])
                for item in items
                if str(item.get("phase") or "") == phase
            ]
            row[f"phase_mean::{phase}"] = mean(values) if values else 0.0
            row[f"phase_low05::{phase}"] = _rate_below(values, 0.5)
            row[f"phase_count::{phase}"] = len(values)
        for role in roles:
            values = [
                float(item["consistency_score_mean"])
                for item in items
                if str(item.get("role") or "") == role
            ]
            row[f"role_mean::{role}"] = mean(values) if values else 0.0
            row[f"role_low05::{role}"] = _rate_below(values, 0.5)
        rows.append(row)
    return rows


def _linear_score(rows: List[Dict[str, Any]], weights: Dict[str, float]) -> List[float]:
    stats = {}
    for key in weights:
        values = [_to_float(row.get(key)) or 0.0 for row in rows]
        center = mean(values) if values else 0.0
        scale = pstdev(values) if len(values) > 1 else 1.0
        stats[key] = (center, scale if scale else 1.0)
    scores = []
    for row in rows:
        score = 0.0
        for key, weight in weights.items():
            center, scale = stats[key]
            score += weight * (((_to_float(row.get(key)) or 0.0) - center) / scale)
        scores.append(score)
    return scores


def _binary_eta_squared(values: List[float], labels: List[int]) -> float:
    positives = [value for value, label in zip(values, labels) if label]
    negatives = [value for value, label in zip(values, labels) if not label]
    if len(positives) < 2 or len(negatives) < 2:
        return 0.0
    all_values = positives + negatives
    grand_mean = mean(all_values)
    between = len(positives) * (mean(positives) - grand_mean) ** 2
    between += len(negatives) * (mean(negatives) - grand_mean) ** 2
    total = sum((value - grand_mean) ** 2 for value in all_values)
    return between / total if total else 0.0


def _binary_auc(values: List[float], labels: List[int]) -> float:
    pairs = sorted(zip(values, labels), key=lambda item: item[0])
    num_positive = sum(labels)
    num_negative = len(labels) - num_positive
    if not num_positive or not num_negative:
        return 0.5
    rank_sum = 0.0
    rank = 1
    idx = 0
    while idx < len(pairs):
        end = idx
        while end < len(pairs) and pairs[end][0] == pairs[idx][0]:
            end += 1
        average_rank = (rank + rank + end - idx - 1) / 2
        rank_sum += average_rank * sum(label for _value, label in pairs[idx:end])
        rank += end - idx
        idx = end
    return (rank_sum - num_positive * (num_positive + 1) / 2) / (num_positive * num_negative)


def _best_binary_threshold(values: List[float], labels: List[int], high_is_positive: bool) -> Dict[str, float]:
    candidates = _binary_threshold_candidates(values, labels, high_is_positive)
    if not candidates:
        return {
            "threshold": 0.0,
            "f1": 0.0,
            "f2": 0.0,
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "specificity": 0.0,
            "balanced_accuracy": 0.0,
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
        }

    return max(
        candidates,
        key=lambda candidate: (
            candidate["f1"],
            candidate["accuracy"],
            candidate["precision"],
            candidate["recall"],
        ),
    )


def _binary_threshold_candidates(values: List[float], labels: List[int], high_is_positive: bool) -> List[Dict[str, float]]:
    if not values:
        return []

    unique_values = sorted(set(values))
    if len(unique_values) == 1:
        thresholds = unique_values
    else:
        thresholds = [unique_values[0]]
        thresholds.extend(
            (left + right) / 2
            for left, right in zip(unique_values, unique_values[1:])
        )
        thresholds.append(unique_values[-1])

    candidates: List[Dict[str, float]] = []
    for threshold in thresholds:
        predictions = [
            1 if (value >= threshold if high_is_positive else value <= threshold) else 0
            for value in values
        ]
        true_positive = sum(1 for prediction, label in zip(predictions, labels) if prediction and label)
        false_positive = sum(1 for prediction, label in zip(predictions, labels) if prediction and not label)
        false_negative = sum(1 for prediction, label in zip(predictions, labels) if not prediction and label)
        true_negative = sum(1 for prediction, label in zip(predictions, labels) if not prediction and not label)

        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        specificity = true_negative / (true_negative + false_positive) if true_negative + false_positive else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        beta_squared = RECALL_WEIGHTED_BETA ** 2
        f2 = (
            (1 + beta_squared) * precision * recall / ((beta_squared * precision) + recall)
            if precision + recall
            else 0.0
        )
        accuracy = (true_positive + true_negative) / len(labels) if labels else 0.0
        candidate = {
            "threshold": float(threshold),
            "f1": float(f1),
            "f2": float(f2),
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "specificity": float(specificity),
            "balanced_accuracy": float((recall + specificity) / 2),
            "tp": true_positive,
            "fp": false_positive,
            "tn": true_negative,
            "fn": false_negative,
        }
        candidates.append(candidate)

    return candidates


def _ridge_lda_score(matrix: Any, labels: Any, ridge: float = 1.0) -> Any:
    import numpy as np

    if matrix.shape[1] == 0:
        return np.zeros(matrix.shape[0])
    positives = matrix[labels == 1]
    negatives = matrix[labels == 0]
    covariance = np.cov(matrix, rowvar=False)
    covariance = np.atleast_2d(covariance)
    weights = np.linalg.solve(
        covariance + ridge * np.eye(covariance.shape[0]),
        positives.mean(axis=0) - negatives.mean(axis=0),
    )
    return matrix @ weights


def _standardize_matrix(matrix: Any) -> tuple:
    import numpy as np

    mu = matrix.mean(axis=0)
    sigma = matrix.std(axis=0)
    sigma[sigma == 0] = 1.0
    return (matrix - mu) / sigma, mu, sigma


def _kmeans_deterministic(matrix: Any, k: int, max_iter: int = 100) -> Any:
    import numpy as np

    best_assignments = None
    best_inertia = None
    n_rows = len(matrix)
    if n_rows == 0:
        return np.array([])
    for seed in range(50):
        rng = np.random.default_rng(seed)
        center_indices = rng.choice(n_rows, size=k, replace=False)
        centers = matrix[center_indices].copy()
        assignments = None
        for _ in range(max_iter):
            distances = ((matrix[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            new_assignments = distances.argmin(axis=1)
            if assignments is not None and np.array_equal(assignments, new_assignments):
                break
            assignments = new_assignments
            for cluster in range(k):
                points = matrix[assignments == cluster]
                if len(points):
                    centers[cluster] = points.mean(axis=0)
        inertia = sum(
            ((matrix[row_idx] - centers[int(assignments[row_idx])]) ** 2).sum()
            for row_idx in range(n_rows)
        )
        if best_inertia is None or inertia < best_inertia:
            best_inertia = inertia
            best_assignments = assignments.copy()
    return _renumber_clusters(best_assignments)


def _average_linkage_clusters(labels: List[str], similarity_matrix: List[List[float]], k: int) -> List[int]:
    clusters = [[idx] for idx in range(len(labels))]
    while len(clusters) > k:
        best_pair = None
        for left_idx in range(len(clusters)):
            for right_idx in range(left_idx + 1, len(clusters)):
                similarities = [
                    similarity_matrix[row][col]
                    for row in clusters[left_idx]
                    for col in clusters[right_idx]
                ]
                avg_similarity = mean(similarities) if similarities else 0.0
                if best_pair is None or avg_similarity > best_pair[0]:
                    best_pair = (avg_similarity, left_idx, right_idx)
        if best_pair is None:
            break
        _avg_similarity, left_idx, right_idx = best_pair
        clusters[left_idx].extend(clusters[right_idx])
        del clusters[right_idx]

    assignments = [0 for _label in labels]
    ordered_clusters = sorted(
        clusters,
        key=lambda cluster: [_label_sort_key(labels[idx]) for idx in cluster],
    )
    for cluster_idx, cluster in enumerate(ordered_clusters):
        for label_idx in cluster:
            assignments[label_idx] = cluster_idx
    return assignments


def _renumber_clusters(assignments: Any) -> Any:
    import numpy as np

    mapping = {}
    next_id = 0
    result = []
    for assignment in assignments:
        assignment = int(assignment)
        if assignment not in mapping:
            mapping[assignment] = next_id
            next_id += 1
        result.append(mapping[assignment])
    return np.array(result)


def _pca_2d(matrix: Any) -> Any:
    import numpy as np

    if len(matrix) == 0:
        return np.zeros((0, 2))
    centered = matrix - matrix.mean(axis=0)
    _u, _s, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(len(coords))])
    return coords


def _classical_mds_2d(distance_matrix: Any) -> Any:
    import numpy as np

    distance = np.array(distance_matrix, dtype=float)
    n_rows = len(distance)
    if n_rows == 0:
        return np.zeros((0, 2))
    centering = np.eye(n_rows) - np.ones((n_rows, n_rows)) / n_rows
    gram = -0.5 * centering @ (distance ** 2) @ centering
    values, vectors = np.linalg.eigh(gram)
    order = np.argsort(values)[::-1]
    values = values[order]
    vectors = vectors[:, order]
    coords = vectors[:, :2] * np.sqrt(np.maximum(values[:2], 0))
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(n_rows)])
    return coords


def _quantile(values: List[float], q: float) -> float:
    if not values:
        return math.nan
    if len(values) == 1:
        return values[0]
    position = (len(values) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return values[int(position)]
    lower_value = values[lower]
    upper_value = values[upper]
    return lower_value + (upper_value - lower_value) * (position - lower)


def _label_sort_key(label: str) -> tuple:
    if label.startswith("c") and label[1:].isdigit():
        return (0, int(label[1:]), label)
    try:
        return (1, float(label), label)
    except ValueError:
        return (2, label)


def _display_label_for_raw_label(raw_label: str) -> Optional[str]:
    return RAW_LABEL_TO_DISPLAY_LABEL.get(raw_label)


if __name__ == "__main__":
    raise SystemExit(main())
