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
실험 결과는 per-run 디렉토리에 저장. 각 run이 완전한 기록이 되어야 한다:
```
results/runs/{YYYYMMDD_HHMMSS}/
├── metrics.json
├── config_snapshot.yaml
├── git_commit.txt
├── stdout.log
├── plots/                    # 시각화 (experiment-runner가 생성)
├── debug/                    # 디버그 로그 (debug_logger가 자동 생성)
│   ├── debug_summary.json
│   ├── debug_steps.json
│   ├── value_checks.json
│   └── debug_report.md
└── analysis/                 # 분석 기록 (result-analyzer가 생성)
    ├── sanity_checks.json
    ├── deep_analysis.md
    └── debug_findings.md
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
