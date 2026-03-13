# Skill: result-analyzer

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps

### Step 0: Sanity Checks (ALWAYS run first)
Before any analysis, run the checks from `sanity_checks.md` on the latest results.
These are guidelines — 프로젝트의 metric과 특성에 맞게 적용한다.
sanity_checks.md의 숫자 threshold는 기본값이다. eval_policy.md에 다른 기준이 있으면 그걸 따른다.

Checks (see sanity_checks.md for details):
1. Class imbalance exploitation — high overall metric but minority class failing
2. Threshold sensitivity — metric collapses with small threshold shift
3. Train-test divergence — significant gap or test > train (leakage?)
4. Near-random subgroup — any subgroup performing at chance level
5. Metric disagreement — primary and secondary metrics tell different stories
6. Degenerate predictions — near-constant output, model collapsed
7. Suspiciously perfect metrics — perfect score, likely leakage
8. Score distribution anomaly — overconfident or no class separation

If ANY flag fires:
- Include the flag prominently in the analysis report
- Do NOT select the flagged method as "best"
- Recommend specific corrective action
- If the same flag fires 3+ consecutive times, promote to hard constraint in eval_policy.md

### Step 1: Load and summarize runs
Load the last 5-10 runs from the results directory. Produce a performance trend table.
Include per-category/subgroup breakdown — never report only overall metrics.

### Step 2: Determine run phase
Check docs/baselines.md and the run's config to determine:
- Phase A run: faithful implementation of a paper (first time this method was tried)
- Phase B run: extension or modification of a previous implementation

### Step 3: Analyze gaps
If Phase A (paper reproduction):
- Compare achieved metric vs. the paper's reported number. Significant gap? Investigate why.
- If reproduced, do gap analysis: what does the paper NOT address?

If Phase B (extension/hybrid):
- Did the modification improve over Phase A? By how much?
- Which part drove the gain?
- New gap introduced?

### Step 4: Deep analysis — 코드와 값 수준 디버깅

metric만 보고 끝내지 않는다. 결과가 왜 그렇게 나왔는지를 코드와 중간값 수준에서 추적한다.

4.0: 디버그 리포트 확인 (ALWAYS 먼저)
- `results/runs/{latest}/debug/debug_summary.json` 확인 — errors, warnings, value_checks_flagged
- errors > 0: `debug_report.md`의 Errors 섹션에서 traceback과 원인 파악
- value_checks_flagged > 0: `value_checks.json`에서 어떤 값이 비정상인지 확인
  - NaN/Inf → 수치 불안정 (gradient explosion, log(0), division by zero 등)
  - Near-constant → model collapse, dead neurons, degenerate learning
  - Out of range → 전처리 오류, normalization 문제
- `debug_steps.json`에서 어떤 단계에서 문제가 발생했는지 timeline 확인
- 디버그 리포트의 발견을 이후 분석의 시작점으로 사용

4.1: 시각화 확인
- `results/runs/{latest}/plots/` 에 저장된 시각화를 확인
- Score distribution, confusion matrix, training curve 등에서 이상한 패턴이 보이는지 확인
- 시각화가 없으면 생성을 권장

4.2: 중간값 검증
결과가 이상하면 pipeline의 각 단계를 역추적한다:
- 최종 output: 값이 이상한가? (score가 전부 같은 값, NaN, 극단값 등)
- 중간 feature/embedding: 모델의 중간 layer output을 확인. feature 분포가 정상인가? 특정 layer에서 값이 collapse되지 않았나?
- 입력 데이터: 모델에 들어가는 input이 제대로 전처리되었나? shape, range, dtype 확인
- 수식/계산: loss 계산, metric 계산, score 변환 등의 수식이 논문대로 구현되었나? 코드를 직접 읽고 검증

4.3: 코드 추적
문제가 발견되면 해당 코드를 직접 읽고 분석:
- 어떤 파일의 어떤 함수에서 문제가 발생했는지 특정
- 논문의 수식과 코드의 구현을 비교 — 차이가 있는지
- edge case 처리가 빠졌는지 (0으로 나누기, empty batch, 등)
- config 값이 코드에 제대로 전달되는지

4.4: 디버깅 제안
분석 결과를 바탕으로 구체적인 디버깅 지시를 생성:
```
## Debug Finding — {date}
Location: {file}:{function}:{line}
Issue: {무엇이 잘못되었는지}
Evidence: {어떤 값/시각화에서 발견했는지}
Fix: {구체적인 수정 방안}
```

### Step 5: Classify failure
실패를 분류한다. 고정된 목록이 아니라 상황에 맞게 판단한다.

### Step 6: Extract root causes
2-3 root causes with confidence level (certain / likely / hypothesis)
Step 4의 deep analysis 결과를 근거로 포함.

### Step 7: Derive next directions
각 root cause에 대해 적절한 next action을 제안한다.

### Step 8: Reflexion
If the same failure pattern appears in 3+ consecutive runs, promote it to a learned rule in
CLAUDE.md Mutable Known Failure Taxonomy:
`- [rule] {pattern}: {mitigation}  # promoted {date}`

## Rules
- do not draw conclusions from 1-2 runs (minimum 3)
- mark uncertain claims as "hypothesis"
- only promote a pattern to a rule after 3+ consecutive occurrences
- overall metric만으로 "best method" 판단하지 않는다 — subgroup/per-class 분석 필수
- metric이 이상하면 method보다 metric부터 의심한다
- 결과가 이상하면 항상 코드를 읽어서 원인을 추적한다 — metric만 보고 추측하지 않는다

## Output format for next_actions.md
Use hierarchical task IDs to track action items across loop iterations:

```
# Next Actions

## 1. {top-level goal}
Status: pending / in-progress / done / blocked

### 1.1 {sub-task}
Status: pending
Confidence: certain / likely / hypothesis
Detail: {what to change and why}
```

## Logging — 모든 분석 결과는 해당 run에 저장

분석 결과는 해당 run 디렉토리 안에 남긴다. 나중에 어떤 run에서 무슨 분석을 했는지 추적 가능해야 한다.

```
results/runs/{timestamp}/analysis/
├── sanity_checks.json        # 각 check의 pass/fail + flag 내용
├── deep_analysis.md          # Step 4 코드/값 분석 전체 기록
├── debug_findings.md         # 발견된 버그/문제 + fix 제안
├── gap_analysis.md           # Phase A/B gap 분석
└── plots/                    # 분석 중 추가 생성한 시각화
```

`sanity_checks.json` 예시:
```json
{
  "run_id": "{timestamp}",
  "checks": {
    "class_imbalance": {"status": "pass"},
    "threshold_sensitivity": {"status": "flag", "detail": "..."},
    "degenerate_predictions": {"status": "pass"}
  },
  "flags_fired": 1,
  "consecutive_flag_count": {"threshold_sensitivity": 2}
}
```

## Output files (summary level)
- results/runs/{latest}/analysis/ — 이 run의 분석 기록 (위 참고)
- results/reports/error_analysis.md — 최신 분석 요약 (전체 run 걸쳐)
- results/reports/next_actions.md — 다음 할 일
- CLAUDE.md Mutable section updated (if new rule promoted)
- docs/eval_policy.md updated (if sanity check promoted to hard constraint)
