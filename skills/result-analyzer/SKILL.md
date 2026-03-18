---
name: result-analyzer
description: Failure classification, code-level deep analysis, and review validation
disable-model-invocation: false
---

# Skill: result-analyzer

## Contract
- Sanity checks를 반드시 Step 0에서 먼저 실행한다 — 건너뛰지 않는다.
- overall metric만으로 "best method" 판단하지 않는다 — subgroup/per-class 분석 필수.
- minimum 3 runs for conclusions. 단일 run 결과로 결론 내리지 않는다.

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps

### Step 0: Sanity Checks (ALWAYS run first)
Run checks from `sanity_checks.md`. eval_policy.md 기준이 있으면 그걸 따른다.

Checks: class imbalance exploitation, threshold sensitivity, train-test divergence, near-random subgroup, metric disagreement, degenerate predictions, suspiciously perfect metrics, score distribution anomaly.

If ANY flag fires: report prominently, do NOT select as "best", recommend corrective action.
Same flag 3+ consecutive times → promote to hard constraint in eval_policy.md.

### Step 1: Load and summarize runs
Last 5-10 runs. Per-category/subgroup breakdown 필수.

### Step 2: Determine run phase
- Phase A: faithful paper reproduction (first time)
- Phase B: extension/modification

### Step 3: Analyze gaps
Phase A: 논문 수치와 비교, gap analysis
Phase B: Phase A 대비 개선 여부, 어떤 부분이 gain을 drove했는지

### Step 4: Deep analysis — 코드와 값 수준 디버깅

4.0: `results/{timestamp}/debug/debug_summary.json` 확인
- errors > 0 → debug_report.md에서 traceback
- value_checks_flagged > 0 → NaN/Inf, near-constant, out of range

4.1: 시각화 확인 (`results/{timestamp}/plots/`)

4.2: 중간값 검증 — output, feature/embedding, input data, 수식/계산

4.3: 코드 추적 — 문제 함수 특정, 논문 수식 vs 구현 비교, edge case

4.4: 디버깅 제안 → Location, Issue, Evidence, Fix

### Step 5: Classify failure

### Step 6: Extract root causes
2-3 root causes with confidence (certain / likely / hypothesis)

### Step 7: Derive next directions

### Step 8: Reflexion
Same failure pattern 3+ consecutive runs → promote to learned rule in CLAUDE.md

## Review checklist (fairness & validity)
- same data split / same seed / same preprocessing across compared runs
- no hyperparameter tuning that favors one method only
- 3+ seeds, report mean
- hypotheses and facts clearly distinguished
- confidence ≥80% for flagging issues; borderline → "low-confidence observation"

## Output — 모두 해당 timestamp 디렉토리에 저장
분석 결과는 `results/{timestamp}/analysis/`에 저장:
- sanity_checks.json — sanity check 결과
- deep_analysis.md — 코드 수준 심층 분석
- debug_findings.md — 디버깅 발견 사항
- gap_analysis.md — 논문 대비 차이 분석

리포트는 `results/{timestamp}/report/`에 저장:
- error_analysis.md — 에러 분류 및 원인
- next_actions.md — 다음 단계 제안

## IMPORTANT: 파일 저장 규칙
- results 루트나 results/reports/에 파일을 두지 않는다
- 모든 분석/리포트는 반드시 `results/{timestamp}/` 하위에 저장
