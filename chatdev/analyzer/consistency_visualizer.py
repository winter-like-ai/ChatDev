"""
Visualize logprob consistency scores for classified ChatDev scored datasets.

Default input:
    data/classified_chatdev_scored

The module treats each scored interaction turn as one observation and uses
``consistency_score_mean`` as the primary metric.  Label directories such as
``0.0`` or ``1.1`` are compared with box plots and phase-level heatmaps.
The ``trajectory`` directory is excluded by default because it duplicates the
same samples across label directories.
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


DEFAULT_SCORED_ROOT = Path("data/classified_chatdev_scored")
DEFAULT_OUTPUT_DIRNAME = "_visualizations"


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
        label = rel.parts[0]
        if label == "trajectory" and not include_trajectory:
            continue

        try:
            with path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except Exception as exc:
            records.append(
                {
                    "label": label,
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


def aggregate_records_by_file(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aggregate turn-level records into one mean score per scored JSON file."""
    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for record in records:
        label = str(record.get("label") or "")
        source_file = str(record.get("source_file") or "")
        score = _to_float(record.get("consistency_score_mean"))
        if label and source_file and score is not None:
            grouped[(label, source_file)].append(record)

    rows: List[Dict[str, Any]] = []
    for (label, source_file), items in sorted(
        grouped.items(), key=lambda item: (_label_sort_key(item[0][0]), item[0][1])
    ):
        scores = [float(item["consistency_score_mean"]) for item in items]
        sorted_scores = sorted(scores)
        worst = min(items, key=lambda item: float(item["consistency_score_mean"]))
        rows.append(
            {
                "label": label,
                "source_file": source_file,
                "file_name": Path(source_file).name,
                "consistency_score_file_mean": mean(scores),
                "consistency_score_file_median": median(scores),
                "consistency_score_file_min": min(scores),
                "consistency_score_file_max": max(scores),
                "consistency_score_file_std": pstdev(scores) if len(scores) > 1 else 0.0,
                "consistency_score_file_q10": _quantile(sorted_scores, 0.10),
                "consistency_score_file_q25": _quantile(sorted_scores, 0.25),
                "consistency_score_file_q75": _quantile(sorted_scores, 0.75),
                "consistency_score_file_iqr": _quantile(sorted_scores, 0.75) - _quantile(sorted_scores, 0.25),
                "low_score_rate_0_2": sum(score < 0.2 for score in scores) / len(scores),
                "low_score_rate_0_5": sum(score < 0.5 for score in scores) / len(scores),
                "high_score_rate_0_8": sum(score >= 0.8 for score in scores) / len(scores),
                "worst_score": float(worst["consistency_score_mean"]),
                "worst_role": worst.get("role") or "",
                "worst_phase": worst.get("phase") or "",
                "worst_turn": worst.get("turn"),
                "num_turns": len(scores),
                "num_roles": len({str(item.get("role") or "") for item in items}),
                "num_phases": len({str(item.get("phase") or "") for item in items}),
                "user_demand": next((item.get("user_demand") or "" for item in items), ""),
            }
        )
    return rows


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
    valid_records = [record for record in records if "error" not in record]
    file_records = aggregate_records_by_file(valid_records)
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
    file_feature_heatmap_png = out_dir / "consistency_file_feature_heatmap.png"
    phase_boxplots_png = out_dir / "consistency_phase_boxplots_by_label.png"
    role_boxplots_png = out_dir / "consistency_role_boxplots_by_label.png"
    worst_score_png = out_dir / "consistency_worst_score_by_label_boxplot.png"
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
    plot_file_feature_heatmap(file_records, file_feature_heatmap_png)
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
        "file_feature_heatmap_png": str(file_feature_heatmap_png),
        "phase_boxplots_png": str(phase_boxplots_png),
        "role_boxplots_png": str(role_boxplots_png),
        "worst_score_png": str(worst_score_png),
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
            f"- File feature heatmap: `{Path(report['file_feature_heatmap_png']).name}`",
            f"- Phase boxplot grid: `{Path(report['phase_boxplots_png']).name}`",
            f"- Role boxplot grid: `{Path(report['role_boxplots_png']).name}`",
            f"- Worst-turn score boxplot: `{Path(report['worst_score_png']).name}`",
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
    try:
        return (0, float(label), label)
    except ValueError:
        return (1, label)


if __name__ == "__main__":
    raise SystemExit(main())
