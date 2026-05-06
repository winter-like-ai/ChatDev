"""Build classified_chatdev_scored_2 and c0-vs-c2 threshold reports.

The generated scored dataset mirrors selected labels from
``data/classified_chatdev_summarized``.  By default it writes c0/c2 labels only:
``0.0``, ``1.3``, and ``1.5``.

A file is selected when any same-filename summarized JSON appears under one of
the target labels.  Once selected, all same-filename copies are written, including
copies under other labels and ``trajectory``.  This matches the scored_1
pipeline and preserves multi-label membership for later analysis.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chatdev.analyzer.consistency_visualizer import (
    aggregate_records_by_file,
    build_binary_label_pair_score_report,
    dedupe_records_by_display_label,
    enrich_file_records_with_c2_symptoms,
    load_consistency_records,
    plot_binary_high_recall_scores,
    plot_binary_label_pair_best_score,
)
from chatdev.analyzer.repetition_scoring import score_summarized_json


DEFAULT_INPUT_ROOT = PROJECT_ROOT / "data" / "classified_chatdev_summarized"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "classified_chatdev_scored_2"
DEFAULT_LABELS = ("0.0", "1.3", "1.5")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--labels", nargs="+", default=list(DEFAULT_LABELS))
    parser.add_argument("--window", type=int, default=3)
    parser.add_argument("--include-trajectory", action="store_true")
    args = parser.parse_args()

    input_root = args.input_root.resolve()
    output_root = args.output_root.resolve()
    target_labels = set(args.labels)

    candidate_paths = discover_summarized_paths(input_root, include_trajectory=args.include_trajectory)
    candidate_filename_labels = collect_filename_labels(candidate_paths, input_root)
    selected_filenames = {
        filename
        for filename, labels in candidate_filename_labels.items()
        if labels & target_labels
    }
    source_paths = [
        path
        for path in discover_summarized_paths(input_root, include_trajectory=True)
        if path.name in selected_filenames
    ]
    filename_groups = group_by_filename(source_paths)

    scored_canonical_count = 0
    copied_duplicate_count = 0
    records = []
    for index, (filename, paths) in enumerate(filename_groups.items(), start=1):
        canonical_src = choose_canonical_path(paths, input_root)
        canonical_dst = scored_output_path(canonical_src, input_root, output_root)
        score_summarized_json(canonical_src, canonical_dst, window=args.window)
        scored_canonical_count += 1

        for duplicate_src in paths:
            duplicate_dst = scored_output_path(duplicate_src, input_root, output_root)
            if duplicate_dst == canonical_dst:
                continue
            score_summarized_json(duplicate_src, duplicate_dst, window=args.window)
            copied_duplicate_count += 1

        labels = collect_path_labels(paths, input_root)
        records.append(
            {
                "index": index,
                "filename": filename,
                "labels": sorted(labels),
                "target_label_hit": sorted(labels & target_labels),
                "canonical_input": str(canonical_src.relative_to(input_root)),
                "canonical_output": str(canonical_dst.relative_to(output_root)),
                "path_count": len(paths),
                "outputs": [
                    str(scored_output_path(path, input_root, output_root).relative_to(output_root))
                    for path in paths
                ],
            }
        )
        if index == 1 or index % 10 == 0 or index == len(filename_groups):
            print(
                f"[{index}/{len(filename_groups)}] scored {filename}: "
                f"labels={sorted(labels)}, copies={len(paths) - 1}"
            )

    manifest = {
        "input_root": str(input_root),
        "output_root": str(output_root),
        "target_labels": sorted(target_labels),
        "target_label_policy": (
            "Include a filename when any same-filename summarized JSON appears "
            "under a target label; write every same-filename copy so multi-label "
            "membership is preserved."
        ),
        "window": args.window,
        "all_unique_filenames": len(candidate_filename_labels),
        "selected_unique_filenames": len(filename_groups),
        "selected_summarized_files": len(source_paths),
        "scored_canonical_files": scored_canonical_count,
        "duplicate_outputs": copied_duplicate_count,
        "num_scored_files": len(source_paths),
        "scorer": "chatdev.analyzer.repetition_scoring",
        "primary_metric": "repetition_score_mean__fm_1_3",
        "compatibility_metric": "consistency_score_mean = 1 - repetition_score_mean__fm_1_3",
        "records": records,
    }
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = build_c0_vs_c2_report(output_root)
    print(f"Manifest: {output_root / '_manifest.json'}")
    print(f"Report dir: {report['output_dir']}")
    if report["summary_rows"]:
        best = report["summary_rows"][0]
        print(
            "Best c0-vs-c2 score: "
            f"{best['score_key']} | direction={best['direction']} | "
            f"threshold={best['threshold']:.6g} | f1={best['f1']:.4f} | "
            f"precision={best['precision']:.4f} | recall={best['recall']:.4f}"
        )


def scored_output_path(src_path: Path, input_root: Path, output_root: Path) -> Path:
    rel = src_path.relative_to(input_root)
    if rel.name.endswith("_summarized.json"):
        name = rel.name[: -len("_summarized.json")] + "_scored.json"
    else:
        name = rel.stem + "_scored.json"
    return output_root / rel.parent / name


def discover_summarized_paths(input_root: Path, include_trajectory: bool) -> List[Path]:
    paths = []
    for path in sorted(input_root.rglob("*_summarized.json"), key=lambda item: str(item)):
        rel = path.relative_to(input_root)
        if not rel.parts:
            continue
        if rel.parts[0].startswith("_"):
            continue
        if rel.parts[0] == "trajectory" and not include_trajectory:
            continue
        paths.append(path)
    return paths


def collect_filename_labels(paths: Iterable[Path], input_root: Path) -> Dict[str, set[str]]:
    labels_by_filename: Dict[str, set[str]] = {}
    for path in paths:
        labels_by_filename.setdefault(path.name, set()).add(summarized_label(path, input_root))
    return labels_by_filename


def collect_path_labels(paths: Iterable[Path], input_root: Path) -> set[str]:
    return {summarized_label(path, input_root) for path in paths}


def summarized_label(path: Path, input_root: Path) -> str:
    rel = path.relative_to(input_root)
    return rel.parts[0] if rel.parts else ""


def group_by_filename(paths: Sequence[Path]) -> Dict[str, List[Path]]:
    groups: Dict[str, List[Path]] = {}
    for path in paths:
        groups.setdefault(path.name, []).append(path)
    return dict(sorted(groups.items(), key=lambda item: item[0]))


def choose_canonical_path(paths: Sequence[Path], input_root: Path) -> Path:
    return sorted(
        paths,
        key=lambda path: (
            summarized_label(path, input_root) != "trajectory",
            str(path.relative_to(input_root)),
        ),
    )[0]


def build_c0_vs_c2_report(scored_root: Path) -> Dict[str, Any]:
    output_dir = scored_root / "_visualizations"
    output_dir.mkdir(parents=True, exist_ok=True)

    turn_records = load_consistency_records(scored_root, include_trajectory=False)
    turn_records = dedupe_records_by_display_label(turn_records)
    file_records = aggregate_records_by_file(turn_records)
    enrich_file_records_with_c2_symptoms(turn_records, file_records)
    report = build_binary_label_pair_score_report(
        file_records,
        negative_label="c0",
        positive_label="c2",
    )

    summary_csv = output_dir / "c0_vs_c2_eta2_f1_summary.csv"
    threshold_csv = output_dir / "c0_vs_c2_single_score_thresholds.csv"
    high_recall_csv = output_dir / "c0_vs_c2_high_recall_eta2_f2_summary.csv"
    file_records_csv = output_dir / "c0_vs_c2_file_records.csv"
    boxplot_png = output_dir / "c0_vs_c2_best_single_score_boxplot.png"
    high_recall_png = output_dir / "c0_vs_c2_high_recall_eta2_f2_top_scores.png"

    write_csv(summary_csv, report["summary_rows"])
    write_csv(threshold_csv, report["threshold_rows"])
    write_csv(high_recall_csv, report["high_recall_rows"])
    write_csv(file_records_csv, report["file_score_rows"])

    plot_binary_label_pair_best_score(
        report["file_score_rows"],
        report["best_score_key"],
        boxplot_png,
        negative_label="c0",
        positive_label="c2",
    )
    plot_binary_high_recall_scores(
        report["high_recall_rows"],
        high_recall_png,
        negative_label="c0",
        positive_label="c2",
    )

    readme_lines = [
        "# classified_chatdev_scored_2",
        "",
        "FM-1.3 repetition scoring for `c0=0.0` versus `c2=1.3+1.5`.",
        "",
        "Primary per-turn metric:",
        "- `repetition_score_mean__fm_1_3`: higher means more repetitive.",
        "- `consistency_score_mean`: compatibility field equal to `1 - repetition_score_mean__fm_1_3`.",
        "",
        "Key outputs:",
        f"- `{summary_csv.name}`: ranked c0-vs-c2 score candidates.",
        f"- `{threshold_csv.name}`: best threshold per score.",
        f"- `{boxplot_png.name}`: best score distribution.",
    ]
    (output_dir / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")

    return {
        **report,
        "output_dir": str(output_dir),
        "summary_csv": str(summary_csv),
        "threshold_csv": str(threshold_csv),
        "high_recall_csv": str(high_recall_csv),
        "file_records_csv": str(file_records_csv),
        "boxplot_png": str(boxplot_png),
        "high_recall_png": str(high_recall_png),
    }


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
