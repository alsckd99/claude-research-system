# Skill: data-auditor

## Trigger
- 프로젝트 시작 시 (bootstrap-project Phase 2 이후, research 전)
- "데이터 분석해줘", "데이터셋 확인해줘"
- 새 데이터셋 추가 시

## Purpose
실험 전에 데이터셋을 분석해서 문제를 미리 발견한다.
eval_policy 설계와 모델 선택에 직접 영향을 준다.

## Steps

### Step 1: 기본 통계
- 전체 sample 수 (train / val / test)
- Class별 sample 수 + 비율
- 데이터 형식: 파일 타입, shape, dtype, range
- 누락/손상 파일 확인

### Step 2: 분포 분석
- Class 불균형 정도 — imbalance ratio 계산
- Subgroup별 분포 (있으면) — 특정 subgroup이 극단적으로 적지 않은지
- Train/val/test split 간 분포 일관성 — 같은 분포인지
- 시각화: class distribution bar chart, subgroup heatmap

### Step 3: 데이터 품질
- 중복 sample 확인 (hash 기반)
- Train-test leakage 확인 — train과 test에 같은 sample이 있는지
- 이상치 탐지 — 극단적으로 다른 sample이 있는지
- Label 품질 — label 분포가 비정상적이지 않은지

### Step 4: 영향 분석
발견한 문제가 프로젝트에 미치는 영향을 정리:
```
## Data Audit — {date}

### Dataset Summary
- Total: {N} samples ({train}/{val}/{test})
- Classes: {N} — {분포}
- Imbalance ratio: {ratio}

### Issues Found
1. {issue}: {설명}
   Impact: {eval_policy나 모델 선택에 어떤 영향}
   Recommendation: {어떻게 대응할지}

### Recommendations for eval_policy
- {불균형이 심하면: balanced metric 사용 권장}
- {subgroup 차이가 크면: per-subgroup 리포트 필수}
- {leakage 발견: split 재구성 필요}
```

### Step 5: 시각화 저장
`data/audit/` 디렉토리에 저장:
- class_distribution.png
- subgroup_distribution.png (있으면)
- sample_examples.png (각 class별 대표 sample)
- 기타 발견한 패턴 시각화

## Output
- `data/audit/data_audit.md` — 전체 분석 리포트
- `data/audit/` — 시각화 파일들
- 발견한 이슈는 researcher agent에게 전달 → eval_policy 설계에 반영
