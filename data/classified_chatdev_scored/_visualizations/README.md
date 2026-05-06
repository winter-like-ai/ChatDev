# ChatDev Consistency Visualization

- Scored root: `data\classified_chatdev_scored`
- Records: `2614`
- File-level records: `190`
- Labels: `5`
- Include trajectory: `False`
- Label groups: `{"c0": ["0.0"], "c1": ["1.1"], "c2": ["1.3", "1.5"], "c3": ["2.2", "2.3"], "c4": ["2.6"]}`

## Label Summary

| label | files | turns | mean | median | q1 | q3 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| c0 | 37 | 513 | 0.6231 | 0.7100 | 0.3764 | 0.9621 | 0.0000 | 1.0000 |
| c1 | 32 | 430 | 0.5947 | 0.6667 | 0.3525 | 0.8875 | 0.0000 | 1.0000 |
| c2 | 52 | 720 | 0.5926 | 0.6667 | 0.3215 | 0.9205 | 0.0000 | 1.0000 |
| c3 | 32 | 441 | 0.5871 | 0.6656 | 0.3157 | 0.9260 | 0.0000 | 1.0000 |
| c4 | 37 | 510 | 0.6163 | 0.6723 | 0.4003 | 0.9502 | 0.0000 | 1.0000 |

## Outputs

- Turn records CSV: `consistency_turn_records.csv`
- File records CSV: `consistency_file_records.csv`
- Label summary CSV: `consistency_label_summary.csv`
- File-level label summary CSV: `consistency_file_label_summary.csv`
- Label boxplot: `consistency_by_label_boxplot.png`
- File-level label boxplot: `consistency_by_label_file_boxplot.png`
- Label-phase heatmap: `consistency_label_phase_heatmap.png`
- Label-role heatmap: `consistency_label_role_heatmap.png`
- ECDF curves: `consistency_by_label_ecdf.png`
- Low/high score rate bars: `consistency_file_low_score_rates.png`
- High-score-rate threshold heatmap: `consistency_file_high_score_rate_threshold_heatmap.png`
- High/low ratio boxplot: `consistency_file_high_low_ratio_0_8_over_0_2_boxplot.png`
- High-score-rate boxplots:
  - `consistency_file_high_score_rate_0_1_boxplot.png`
  - `consistency_file_high_score_rate_0_2_boxplot.png`
  - `consistency_file_high_score_rate_0_3_boxplot.png`
  - `consistency_file_high_score_rate_0_4_boxplot.png`
  - `consistency_file_high_score_rate_0_5_boxplot.png`
  - `consistency_file_high_score_rate_0_6_boxplot.png`
  - `consistency_file_high_score_rate_0_7_boxplot.png`
  - `consistency_file_high_score_rate_0_8_boxplot.png`
  - `consistency_file_high_score_rate_0_9_boxplot.png`
- File feature heatmap: `consistency_file_feature_heatmap.png`
- Evaluation score boxplot grid: `consistency_file_evaluation_score_boxplots.png`
- Evaluation score summary CSV: `consistency_file_evaluation_score_summary.csv`
- Evaluation score separation rank CSV: `consistency_file_evaluation_score_separation_rank.csv`
- c3-positive score candidates CSV: `c3_positive_score_candidates.csv`
- c3-positive score eta-squared plot: `c3_positive_score_boxplots.png`
- Phase boxplot grid: `consistency_phase_boxplots_by_label.png`
- Role boxplot grid: `consistency_role_boxplots_by_label.png`
- Worst-turn score boxplot: `consistency_worst_score_by_label_boxplot.png`
- Label overlap count heatmap: `label_overlap_count_heatmap.png`
- Label overlap Jaccard heatmap: `label_overlap_jaccard_heatmap.png`
- Label overlap CSV: `label_overlap_matrix.csv`
- Label cluster assignments: `label_cluster_assignments.csv`
- Label cluster PCA: `label_cluster_pca.png`
- Core c0-to-c4 cluster assignments: `label_cluster_assignments_c0_to_c4.csv`
- Core c0-to-c4 cluster PCA: `label_cluster_pca_c0_to_c4.png`
- Core c0-to-c4 overlap cluster assignments: `label_overlap_clusters_c0_to_c4.csv`
- Core c0-to-c4 overlap cluster heatmap: `label_overlap_clusters_c0_to_c4_heatmap.png`
- Core c1-to-c4 overlap clusters:
  - k=2: `label_overlap_clusters_core_c1_to_c4_k2.csv`, `label_overlap_clusters_core_c1_to_c4_k2_heatmap.png`, `label_overlap_clusters_core_c1_to_c4_k2_mds_scatter.png`
  - k=3: `label_overlap_clusters_core_c1_to_c4_k3.csv`, `label_overlap_clusters_core_c1_to_c4_k3_heatmap.png`, `label_overlap_clusters_core_c1_to_c4_k3_mds_scatter.png`
  - k=4: `label_overlap_clusters_core_c1_to_c4_k4.csv`, `label_overlap_clusters_core_c1_to_c4_k4_heatmap.png`, `label_overlap_clusters_core_c1_to_c4_k4_mds_scatter.png`
