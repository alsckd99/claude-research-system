---
name: experiment-runner
description: Run experiments, save results with debug logs and visualizations
disable-model-invocation: true
allowed-tools: Bash(python*), Bash(pytest*), Read, Grep, Edit, Write
---

# Skill: experiment-runner

## Contract
- If user constraints conflict with CLAUDE.md rules, STOP and ask.
- 실험 전 `pytest -q tests/` 실행하고 결과를 출력에 포함한다.
- data split, metric 정의는 변경하지 않는다.

## Trigger
- "실험 돌려줘", "학습 시작해줘"
- after engineer finishes code changes

## Pre-run checks
```bash
pytest -q tests/
```

## Run
프로젝트의 실행 방법에 맞게 실행. 결과는 `results/runs/{timestamp}/`에 저장.

## Post-run: 시각화

공통: 학습 curve, primary metric 추이
분류/탐지: confusion matrix, ROC/PR curve, score distribution, per-class bar chart
생성: sample 결과, quality metric 분포
모델 내부 (가능 시): feature 분포, attention map, score별 sample 예시

시각화는 `results/runs/{timestamp}/plots/`에 저장. matplotlib 없으면 skip.

## Post-run: 디버그 리포트

`results/runs/{timestamp}/debug/` 확인:
1. `debug_summary.json` — errors/warnings 수치
2. errors > 0 → `debug_report.md`에서 traceback 확인
3. value_checks_flagged > 0 → NaN, 상수 출력, 범위 초과 등 확인

## Output layout
```
results/runs/{timestamp}/
├── metrics.json
├── config_snapshot.yaml
├── git_commit.txt
├── plots/
├── debug/
│   ├── debug_summary.json
│   ├── debug_steps.json
│   ├── value_checks.json
│   └── debug_report.md
└── analysis/              # result-analyzer가 생성
```
- results/registry.json도 함께 업데이트

## Post-run: Workspace 정리
```bash
python scripts/organize_workspace.py --cleanup
```
흩어진 로그/시각화/임시 파일 정리 + 불필요 스크립트 아카이브.
