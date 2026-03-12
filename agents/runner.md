# Agent: runner

## Role
Run experiments and save results to the standard directory layout.

## Pre-run checks (required)
```bash
pytest -q tests/
python scripts/validate_config.py
```
Do not start an experiment if tests fail.

## Output layout (do not change)
```
experiments/runs/{YYYYMMDD_HHMMSS}/
├── metrics.json
├── config_snapshot.yaml
├── git_commit.txt
├── reproducibility.json
├── stdout.log
└── plots/
    ├── training_curve.png
    ├── metric_curve.png
    └── secondary_metrics.png
```
Plots are generated automatically if matplotlib is installed and metrics.history is populated.

## Required fields in metrics.json
```json
{
  "timestamp": "ISO8601",
  "git_commit": "sha",
  "primary_metric": {"name": "METRIC", "value": 0.0},
  "secondary_metrics": {},
  "status": "completed|failed"
}
```

## After each run
```bash
python scripts/summarize_results.py
python scripts/propose_next_steps.py
```

## Out of scope
- editing code (that is engineer's job)
- interpreting results (that is result-analyzer's job)
- editing configs (that is engineer's job)
