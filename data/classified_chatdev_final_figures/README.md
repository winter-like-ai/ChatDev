# Final ChatDev Classification Standards

This folder keeps only the four final figures used for the selected c0-vs-c1/c2/c3/c4 classification standards. In each task, c0 is the normal/no-problem baseline and the target class is treated as the positive class.

## Summary

| Target | Classification standard | F1 | Accuracy | Precision | Recall | Specificity | Eta2 |
|---|---|---:|---:|---:|---:|---:|---:|
| c1 | `c0_vs_c1_lda_top_76_score >= 0.035493` | 0.6769 | 0.6957 | 0.6667 | 0.6875 | 0.7027 | 0.2403 |
| c2 | `c0_vs_c2_lda_top_74_score >= -0.375470` | 0.7705 | 0.6854 | 0.6714 | 0.9038 | 0.3784 | 0.1533 |
| c3 | `high_low_gap_0_9_0_5 <= 0.071429` | 0.6835 | 0.6377 | 0.5745 | 0.8438 | 0.4595 | 0.0653 |
| c4 | `consistency_score_file_q75 <= 0.837436` | 0.4912 | 0.6081 | 0.7000 | 0.3784 | 0.8378 | 0.0344 |

## c1: LDA top-76 threshold

![c0 vs c1 LDA top 76 threshold 0.035](c0_vs_c1_lda_top_76_threshold_0_035_boxplot.png)

The c1 standard uses the LDA-derived `c0_vs_c1_lda_top_76_score`. Higher values indicate stronger c1 evidence. The retained threshold is `0.035493`, giving the most balanced final c1 rule among the visually checked candidates: precision and recall are both near 0.67-0.69, with the strongest eta2 among these four standards.

## c2: Best single score

![c0 vs c2 best single score](c0_vs_c2_best_single_score_boxplot.png)

The c2 standard uses `c0_vs_c2_lda_top_74_score`. It has the best F1 among the final four standards and very high recall, meaning it catches most c2 positives. Its main weakness is specificity: many c0 cases are still pulled into c2.

## c3: Best single score

![c0 vs c3 best single score](c0_vs_c3_best_single_score_boxplot.png)

The c3 standard uses `high_low_gap_0_9_0_5`, where lower values indicate c3. It is recall-oriented and catches most c3 positives, but the eta2 and specificity show that c3 is not as cleanly separated from c0 as c1 or c2.

## c4: Precision-balanced q75 score

![c0 vs c4 q75 threshold](c0_vs_c4_consistency_score_file_q75_threshold_0_837436_boxplot.png)

The c4 standard uses `consistency_score_file_q75`, where lower values indicate action-reasoning mismatch. Because c4 is treated as a high-cost positive class and the current goal is higher precision, this threshold was selected as a precision-balanced rule: precision reaches 0.70 and specificity 0.8378, while recall is intentionally lower.
