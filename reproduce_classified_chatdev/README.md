# classified_chatdev Reproduction

This directory is the compact reproduction entry point for the classified
ChatDev scoring pipeline. It starts from `data/classified_chatdev` and can
rebuild the derived playbook, summarized, scored, visualization, and overview
artifacts while reusing the project APIs under `chatdev.analyzer`.

## Default Contract

- Source dataset: `data/classified_chatdev`
- Playbook output: `data/classified_chatdev_playbook`
- API-record output: `data/classified_chatdev_api_record`
- Summarized output: `data/classified_chatdev_summarized`
- Scored outputs:
  - `data/classified_chatdev_scored`
  - `data/classified_chatdev_scored_1`
  - `data/classified_chatdev_scored_2`
  - `data/classified_chatdev_scored_3`
  - `data/classified_chatdev_scored_4`
- Visualization outputs: each scored directory's `_visualizations/`
- Overview table: `reproduce_classified_chatdev/overview/overview.csv`

## Run

Fast reproducibility check that reuses existing API-derived artifacts and
refreshes visualizations plus the overview table:

```bash
python reproduce_classified_chatdev/run_reproduction.py
```

Full rebuild, including API-calling summarization and logprob scoring:

```bash
python reproduce_classified_chatdev/run_reproduction.py --run-api-steps --overwrite
```

Run only selected stages:

```bash
python reproduce_classified_chatdev/run_reproduction.py --steps playbook summarize scored_1 visualize overview --run-api-steps
```

## API Switch

By default, the runner does not call the LLM APIs for summarization or scoring.
It verifies and reuses existing artifacts when they are present. Add
`--run-api-steps` when the source data changed or when the derived artifacts
must be regenerated from scratch.

## Notes

- `scored_1` uses filename-level target-label filtering for labels `0.0` and
  `1.1`, with `premise_order=["tasks", "user_demand"]`.
- `scored_2` delegates to the existing compact script
  `scripts/build_classified_chatdev_scored_2.py`.
- `scored_3` and `scored_4` reproduce the action-reasoning alignment scoring
  from the notebooks while keeping their different output policies.
- The original exploratory notebooks remain in `notebooks/`; this directory is
  intended to be the clean operational wrapper.
