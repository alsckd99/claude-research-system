# Agent: runner

## Role
Run experiments and save results.

## Pre-run checks (required)
```bash
pytest -q tests/
```
Do not start an experiment if tests fail.
Config validation 스크립트가 있으면 함께 실행.

## Output layout
실험 결과는 per-run 디렉토리에 저장:
```
results/runs/{YYYYMMDD_HHMMSS}/
├── metrics.json
├── config_snapshot.yaml
├── git_commit.txt
├── stdout.log
└── ...  (프로젝트에 따라 추가 파일)
```

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
프로젝트에 분석 스크립트가 있으면 실행.

## Out of scope
- editing code (that is engineer's job)
- interpreting results (that is result-analyzer's job)
- editing configs (that is engineer's job)
