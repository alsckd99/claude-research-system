# Skill: result-analyzer

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps

### Step 0: Sanity Checks (ALWAYS run first)
Before any analysis, run the checks from `sanity_checks.md` on the latest results.
These are guidelines — 프로젝트의 metric과 특성에 맞게 적용한다.
sanity_checks.md의 숫자 threshold는 기본값이다. eval_policy.md에 다른 기준이 있으면 그걸 따른다.

**Checks (see sanity_checks.md for details):**
1. **Class imbalance exploitation** — high overall metric but minority class failing
2. **Threshold sensitivity** — metric collapses with small threshold shift
3. **Train-test divergence** — significant gap or test > train (leakage?)
4. **Near-random subgroup** — any subgroup performing at chance level
5. **Metric disagreement** — primary and secondary metrics tell different stories
6. **Degenerate predictions** — near-constant output, model collapsed
7. **Suspiciously perfect metrics** — perfect score, likely leakage
8. **Score distribution anomaly** — overconfident or no class separation

**If ANY flag fires:**
- Include the flag prominently in the analysis report
- Do NOT select the flagged method as "best"
- Recommend specific corrective action
- If the same flag fires 3+ consecutive times → promote to hard constraint in eval_policy.md

### Step 1: Load and summarize runs
Load the last 5-10 runs from the results directory. Produce a performance trend table.
Include per-category/subgroup breakdown — never report only overall metrics.

### Step 2: Determine run phase
Check docs/baselines.md and the run's config to determine:
- **Phase A run**: faithful implementation of a paper (first time this method was tried)
- **Phase B run**: extension or modification of a previous implementation

### Step 3: Analyze gaps
**If Phase A (paper reproduction):**
- Compare achieved metric vs. the paper's reported number. Significant gap? Investigate why.
- If reproduced → gap analysis: what does the paper NOT address?

**If Phase B (extension/hybrid):**
- Did the modification improve over Phase A? By how much?
- Which part drove the gain?
- New gap introduced?

### Step 4: Classify failure
실패를 분류한다. 고정된 목록이 아니라 상황에 맞게 판단한다.
흔한 패턴: overfitting, instability, data issue, architecture issue, plateau, paper-gap, reproduction-failure, imbalance-exploitation, metric-misleading 등.
이 목록에 없는 새로운 유형이면 자유롭게 정의한다.

### Step 5: Extract root causes
2-3 root causes with confidence level (certain / likely / hypothesis)

### Step 6: Derive next directions
각 root cause에 대해 적절한 next action을 제안한다. 고정된 카테고리가 아니라 상황에 맞게 자유롭게 판단.

### Step 7: Reflexion
If the same failure pattern appears in 3+ consecutive runs, promote it to a learned rule in
CLAUDE.md Mutable Known Failure Taxonomy:
`- [rule] {pattern}: {mitigation}  # promoted {date}`

## Rules
- do not draw conclusions from 1-2 runs (minimum 3)
- mark uncertain claims as "hypothesis"
- only promote a pattern to a rule after 3+ consecutive occurrences
- overall metric만으로 "best method" 판단하지 않는다 — subgroup/per-class 분석 필수
- metric이 이상하면 method보다 metric부터 의심한다

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

## Output files
- results/ reports updated (error_analysis, next_actions)
- CLAUDE.md Mutable section updated (if new rule promoted)
- docs/eval_policy.md updated (if sanity check promoted to hard constraint)
