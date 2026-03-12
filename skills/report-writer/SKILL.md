# Skill: report-writer

## Trigger
- "결과 정리해줘", "리포트 써줘"
- 프로젝트 마무리 단계
- 일정 수의 실험이 쌓였을 때

## Purpose
전체 실험 과정을 논문/발표 수준으로 정리한다.

## Steps

### Step 1: 전체 실험 히스토리 수집
- results/registry.json — 모든 run 목록
- results/runs/*/metrics.json — 각 run의 결과
- results/runs/*/analysis/ — 각 run의 분석 기록
- docs/baselines.md — 시도한 방법들
- docs/research_log.md — 방향 변경 기록
- docs/eval_policy.md — 평가 기준

### Step 2: 요약 테이블 생성
모든 방법을 비교하는 테이블:
```
| Method | Primary Metric | Secondary Metrics... | Notes |
|--------|---------------|---------------------|-------|
| baseline | ... | ... | ... |
| method A | ... | ... | Phase A 재현 |
| method A + mod | ... | ... | Phase B 개선 |
```

### Step 3: 핵심 발견 정리
- 무엇을 시도했고 무엇이 됐는지
- 왜 됐는지 / 안 됐는지 (root cause 분석 요약)
- 가장 효과적이었던 변경과 그 근거
- 실패에서 배운 것

### Step 4: 시각화 종합
각 run의 plots/에서 핵심 시각화를 모아서:
- 전체 성능 추이 그래프 (iteration별)
- 최종 best method의 주요 시각화
- Ablation 결과 (있으면)
- Before/after 비교

### Step 5: 리포트 작성

```
# {Project Name} — Experiment Report
date: {date}

## Objective
{CLAUDE.md에서}

## Approach
{어떤 접근을 했는지 — 연구 방향, 선택한 모델, 적용한 기법}

## Results Summary
{Step 2의 비교 테이블}

## Key Findings
{Step 3}

## What Worked
{성능을 올린 변경들과 근거}

## What Didn't Work
{실패한 시도들과 원인}

## Visualizations
{Step 4}

## Remaining Issues
{아직 해결 안 된 문제, 추가 실험이 필요한 부분}

## References
{사용한 논문들}
```

## Output
- `results/report.md` — 전체 리포트
- `results/report_plots/` — 리포트용 시각화 모음
