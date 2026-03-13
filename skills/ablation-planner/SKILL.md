---
name: ablation-planner
description: Design ablation experiments to verify component contributions
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Edit, Write
---

# Skill: ablation-planner

## Contract
- 각 ablation은 config flag로 제어 가능해야 한다.
- ablation plan을 `docs/ablation_plan.md`에 먼저 기록한 후 실행한다.

## Trigger
- method-reviser가 여러 component를 포함한 변경을 할 때
- "ablation 실험 계획해줘"
- 개선이 됐는데 어떤 부분이 기여했는지 모를 때

## Steps

### Step 1: 변경 분해
현재 변경을 독립적인 component로 분해. Base(변경 전)와 Full(모든 변경 포함) 정의.

### Step 2: 실험 설계
기본 전략: leave-one-out (Full, Full-A, Full-B, ..., Base).
Component 4개+ → 중요도 순 우선순위로 핵심 ablation만 실행.

### Step 3: 실행 계획
각 ablation을 config flag로 제어. 실험 테이블 작성 (config, components, expected result).

### Step 4: 결과 분석 가이드
- 개별 기여도 = Full - (Full - component)
- 기여도 없거나 음수 → 제거 검토
- A+B > A개별 + B개별 → 시너지

## Output
- `docs/ablation_plan.md`
- engineer agent에게 config flag 구현 지시
