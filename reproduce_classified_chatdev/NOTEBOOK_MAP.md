# Source Notebook Map

The reproduction runner consolidates these previously scattered sources:

| Reproduction stage | Previous source | Current runner behavior |
| --- | --- | --- |
| `playbook` | `notebooks/build_classified_playbook.ipynb` | Calls `chatdev.analyzer.log_to_playbook` and mirrors label folders. |
| `summarize` | `notebooks/build_classified_chatdev_summarized.ipynb` | Calls `chatdev.analyzer.llm_summarizer.LLMSummarizer`. |
| `scored` | `notebooks/logprob_consistency_scoring.ipynb` | Calls `LogprobConsistencyScorer` for all summarized paths. |
| `scored_1` | `notebooks/build_classified_chatdev_scored_1.ipynb` | Keeps filename-level `0.0`/`1.1` filtering and `tasks,user_demand` premises. |
| `scored_2` | `scripts/build_classified_chatdev_scored_2.py` | Delegates to the already compact script. |
| `scored_3` | `notebooks/build_classified_chatdev_scored_3.ipynb` | Reimplements action-reasoning alignment with same-filename output preservation. |
| `scored_4` | `notebooks/build_classified_chatdev_scored_4.ipynb` | Reimplements action-reasoning alignment for target label directories only. |
| `visualize` | `chatdev.analyzer.consistency_visualizer` | Generates `_visualizations/` for consistency-style scored datasets. |
| `overview` | New | Writes `overview/overview.csv` and `overview/overview.md`. |
