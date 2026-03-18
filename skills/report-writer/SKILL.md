---
name: report-writer
description: Generate experiment report with visualizations and decision rationale
disable-model-invocation: true
allowed-tools: Bash(python*), Read, Grep, Glob, Edit, Write
---

# Skill: report-writer

## Contract
- 리포트의 모든 수치는 results/registry.json과 metrics.json에서 가져온다 — 임의 생성 금지.
- 시각화 스크립트 실행 결과를 출력에 포함한다.

## Trigger
- "결과 정리해줘", "리포트 써줘"
- 프로젝트 마무리 단계

## Steps

### Step 1: 전체 실험 히스토리 수집
- results/registry.json
- results/*/metrics.json (각 timestamp 디렉토리)
- results/*/analysis/ (각 timestamp의 분석 결과)
- docs/baselines.md, docs/research_log.md, docs/eval_policy.md

### Step 2: 요약 테이블 생성
모든 방법 비교 테이블 (method, primary metric, secondary metrics, notes)

### Step 3: 핵심 발견 정리
무엇을 시도했고 됐는지, 왜 됐/안됐는지, 가장 효과적이었던 변경, 실패에서 배운 것

### Step 4: 시각화 종합
`python scripts/visualize_results.py --auto` 실행.
cross-run 시각화는 최신 timestamp 디렉토리의 `plots/`에 저장:
- `results/{latest_timestamp}/plots/cross_run_comparison.png`
- `results/{latest_timestamp}/plots/metric_trend.png`

### Step 5: Decision Report 통합
`python scripts/generate_decision_report.py --auto` 실행.
결과는 `results/{latest_timestamp}/report/decision_report.md`에 저장.

### Step 6: 리포트 작성

**Iteration 리포트** → `results/{latest_timestamp}/report/iteration_report.md`
- 이번 iteration의 상세 결과

**최종 종합 리포트** → `results/final_report.md` (유일하게 results 루트에 위치)
- Objective, Approach, Results, Key Findings, What Worked/Didn't, Visualizations, Remaining Issues, References

## Output
- `results/{timestamp}/report/` — iteration별 리포트, decision report
- `results/{timestamp}/plots/` — cross-run 시각화
- `results/final_report.md` — 최종 종합 리포트 (results 루트의 유일한 md 파일)
