# Skill: ablation-planner

## Trigger
- method-reviser가 여러 component를 포함한 변경을 할 때
- "ablation 실험 계획해줘"
- 개선이 됐는데 어떤 부분이 기여했는지 모를 때

## Purpose
변경의 어떤 부분이 실제로 효과가 있었는지 체계적으로 검증하는 실험 계획을 세운다.

## Steps

### Step 1: 변경 분해
현재 변경 사항을 독립적인 component로 분해:
```
## Ablation Plan — {date}
Base: {변경 전 baseline}
Full: {모든 변경을 포함한 버전}

### Components
1. {component A}: {설명}
2. {component B}: {설명}
3. {component C}: {설명}
```

### Step 2: 실험 설계
어떤 조합을 테스트할지 결정:

**기본 전략: leave-one-out**
- Full (A+B+C)
- Full - A (B+C만)
- Full - B (A+C만)
- Full - C (A+B만)
- Base (아무것도 없음)

Component가 많으면 (4개+) 중요도 순으로 우선순위를 매겨서 핵심 ablation만 실행.

### Step 3: 실행 계획
각 ablation을 config flag로 제어할 수 있도록 설계:
```
### Experiments to run
| # | Config | Components | Expected result |
|---|--------|-----------|-----------------|
| 1 | base | none | baseline |
| 2 | full | A+B+C | best |
| 3 | no_A | B+C | A의 기여 확인 |
| 4 | no_B | A+C | B의 기여 확인 |
| 5 | no_C | A+B | C의 기여 확인 |

### Config flags needed
- component_a_enabled: true/false
- component_b_enabled: true/false
- component_c_enabled: true/false
```

### Step 4: 결과 분석 가이드
ablation 실행 후 분석 기준:
- 각 component의 개별 기여도 = Full - (Full - component)
- 기여도가 없거나 음수인 component → 제거 검토
- Component 간 상호작용: A+B > A + B 개별 기여 합이면 시너지

## Output
- `docs/ablation_plan.md` — 실험 계획
- engineer agent에게 config flag 구현 지시
- 실행 후 result-analyzer에게 ablation 결과 분석 위임
