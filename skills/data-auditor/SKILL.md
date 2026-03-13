---
name: data-auditor
description: Dataset quality analysis — distribution, imbalance, leakage detection
disable-model-invocation: false
allowed-tools: Bash(python*), Read, Grep, Glob, Write
---

# Skill: data-auditor

## Contract
- train-test leakage 발견 시 즉시 보고하고 실험 진행을 중단 권고한다.
- 분석 결과는 `data/audit/data_audit.md`에 기록한다.

## Trigger
- 프로젝트 시작 시 (bootstrap-project Phase 2)
- "데이터 분석해줘", "데이터셋 확인해줘"
- 새 데이터셋 추가 시

## Steps

### Step 1: 기본 통계
전체/class별 sample 수, 데이터 형식, 누락/손상 파일 확인

### Step 2: 분포 분석
Class 불균형 정도, subgroup별 분포, train/val/test split 간 일관성, 시각화

### Step 3: 데이터 품질
중복 sample (hash), train-test leakage, 이상치, label 품질

### Step 4: 영향 분석
발견한 문제가 eval_policy와 모델 선택에 미치는 영향 정리 + 대응 권장

### Step 5: 시각화 저장
`data/audit/`에 class_distribution.png, subgroup_distribution.png 등 저장

## Output
- `data/audit/data_audit.md`
- `data/audit/` — 시각화 파일들
