# Skill: report-writer

## Trigger
- "결과 정리해줘", "리포트 써줘"
- 프로젝트 마무리 단계

## Steps

### Step 1: 전체 실험 히스토리 수집
- results/registry.json, results/runs/*/metrics.json, results/runs/*/analysis/
- docs/baselines.md, docs/research_log.md, docs/eval_policy.md

### Step 2: 요약 테이블 생성
모든 방법 비교 테이블 (method, primary metric, secondary metrics, notes)

### Step 3: 핵심 발견 정리
무엇을 시도했고 됐는지, 왜 됐/안됐는지, 가장 효과적이었던 변경, 실패에서 배운 것

### Step 4: 시각화 종합
`python scripts/visualize_results.py --auto` 실행 → cross-run 시각화 자동 생성.
각 run의 plots/에서 핵심 시각화 모아서 before/after 비교.

### Step 5: Decision Report 통합
`python scripts/generate_decision_report.py --auto` 실행.
모델 선택 이유, 개선 방식 이유, 디버깅 요약을 Approach 섹션에 통합.

### Step 6: 리포트 작성
`results/report.md` — Objective, Approach, Results, Key Findings, What Worked/Didn't, Visualizations, Remaining Issues, References

## Output
- `results/report.md`
- `results/reports/decision_report.md`
- `results/reports/plots/`
