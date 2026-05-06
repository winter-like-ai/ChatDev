# classified_chatdev_scored_2

FM-1.3 repetition scoring for `c0=0.0` versus `c2=1.3+1.5`.

Primary per-turn metric:
- `repetition_score_mean__fm_1_3`: higher means more repetitive.
- `consistency_score_mean`: compatibility field equal to `1 - repetition_score_mean__fm_1_3`.

Key outputs:
- `c0_vs_c2_eta2_f1_summary.csv`: ranked c0-vs-c2 score candidates.
- `c0_vs_c2_single_score_thresholds.csv`: best threshold per score.
- `c0_vs_c2_best_single_score_boxplot.png`: best score distribution.