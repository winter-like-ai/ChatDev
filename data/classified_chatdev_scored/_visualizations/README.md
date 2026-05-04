# ChatDev Consistency Visualization

- Scored root: `data\classified_chatdev_scored`
- Records: `4372`
- File-level records: `318`
- Labels: `13`
- Include trajectory: `False`

## Label Summary

| label | files | turns | mean | median | q1 | q3 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.0 | 37 | 513 | 0.6231 | 0.7100 | 0.3764 | 0.9621 | 0.0000 | 1.0000 |
| 1.1 | 32 | 430 | 0.5947 | 0.6667 | 0.3525 | 0.8875 | 0.0000 | 1.0000 |
| 1.3 | 47 | 653 | 0.5946 | 0.6671 | 0.3303 | 0.9195 | 0.0000 | 1.0000 |
| 1.4 | 5 | 70 | 0.5905 | 0.6750 | 0.3049 | 0.8595 | 0.0046 | 1.0000 |
| 1.5 | 38 | 527 | 0.5827 | 0.6627 | 0.3011 | 0.9214 | 0.0000 | 1.0000 |
| 2.1 | 4 | 56 | 0.5577 | 0.5920 | 0.2901 | 0.7986 | 0.0046 | 1.0000 |
| 2.2 | 27 | 371 | 0.5952 | 0.6667 | 0.3426 | 0.9074 | 0.0000 | 1.0000 |
| 2.3 | 19 | 263 | 0.5662 | 0.6250 | 0.2381 | 0.8794 | 0.0000 | 1.0000 |
| 2.4 | 4 | 53 | 0.5187 | 0.6075 | 0.0900 | 0.7916 | 0.0006 | 1.0000 |
| 2.6 | 37 | 510 | 0.6163 | 0.6723 | 0.4003 | 0.9502 | 0.0000 | 1.0000 |
| 3.1 | 13 | 176 | 0.5694 | 0.6582 | 0.2649 | 0.8901 | 0.0000 | 1.0000 |
| 3.2 | 22 | 297 | 0.6221 | 0.7133 | 0.3731 | 0.9530 | 0.0000 | 1.0000 |
| 3.3 | 33 | 453 | 0.5917 | 0.6641 | 0.3605 | 0.8679 | 0.0000 | 1.0000 |

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
- File feature heatmap: `consistency_file_feature_heatmap.png`
- Phase boxplot grid: `consistency_phase_boxplots_by_label.png`
- Role boxplot grid: `consistency_role_boxplots_by_label.png`
- Worst-turn score boxplot: `consistency_worst_score_by_label_boxplot.png`
