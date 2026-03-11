# Skill: experiment-runner

## Trigger
- "실험 돌려줘", "학습 시작해줘"
- after engineer finishes code changes

## Pre-run checks
```bash
pytest -q tests/
python scripts/validate_config.py
```

## Run
```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
conda run -n $ENV python scripts/run_experiment.py --config configs/base.yaml --output experiments/runs/${TIMESTAMP}
```

## Post-run
```bash
python scripts/summarize_results.py
python scripts/propose_next_steps.py
```

## Output
- experiments/runs/{timestamp}/ saved (includes reproducibility.json)
- experiments/registry.json updated
- experiments/reports/latest.md updated
