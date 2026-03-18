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
프로젝트의 실행 방법에 맞게 실행. 결과는 `results/{timestamp}/`에 저장.

## Post-run: 시각화

공통: 학습 curve, primary metric 추이
분류/탐지: confusion matrix, ROC/PR curve, score distribution, per-class bar chart
생성: sample 결과, quality metric 분포
모델 내부 (가능 시): feature 분포, attention map, score별 sample 예시

시각화는 `results/{timestamp}/plots/`에 저장. matplotlib 없으면 skip.

## Post-run: 디버그 리포트

`results/{timestamp}/debug/` 확인:
1. `debug_summary.json` — errors/warnings 수치
2. errors > 0 → `debug_report.md`에서 traceback 확인
3. value_checks_flagged > 0 → NaN, 상수 출력, 범위 초과 등 확인

## Output layout
```
results/{timestamp}/
├── metrics.json              # 실험 결과 수치
├── config_snapshot.yaml      # 사용한 설정
├── git_commit.txt            # 실험 시점 커밋 해시
├── plots/                    # 시각화
│   ├── training_curve.png
│   ├── roc_curve.png
│   ├── confusion_matrix.png
│   └── score_distribution.png
├── debug/                    # 디버그 로그
│   ├── debug_summary.json
│   ├── debug_steps.json
│   ├── value_checks.json
│   └── debug_report.md
├── analysis/                 # result-analyzer가 생성
│   ├── sanity_checks.json
│   ├── deep_analysis.md
│   ├── debug_findings.md
│   └── gap_analysis.md
└── report/                   # 이 iteration의 리포트
    ├── error_analysis.md
    ├── next_actions.md
    └── decision_report.md
```
- `results/registry.json`도 함께 업데이트 (이것만 results 루트에 위치)

## Post-run: Workspace 정리
```bash
python scripts/organize_workspace.py --cleanup
```
흩어진 로그/시각화/임시 파일 정리 + 불필요 스크립트 아카이브.

## IMPORTANT: 파일 저장 규칙
- 모든 output은 반드시 `results/{timestamp}/` 안에 저장
- results 루트에 파일을 직접 두지 않는다 (registry.json, final_report.md 제외)
- 시각화, JSON, 분석, 리포트 모두 해당 timestamp 디렉토리 안에 포함
