# Skill: result-analyzer

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps

### Step 0: Sanity Checks (ALWAYS run first)
Before any analysis, run ALL checks from `sanity_checks.md` on the latest results.
These are dataset-agnostic — they apply to ANY project, ANY dataset.

**Checks (see sanity_checks.md for details):**
1. **Class imbalance exploitation** — high overall metric but minority class failing
2. **Threshold sensitivity** — accuracy collapses with ±0.05 threshold shift
3. **Train-test divergence** — gap > 0.05 or test > train (leakage?)
4. **Near-random subgroup** — any subgroup performing at chance level
5. **Metric disagreement** — AUC high but F1 low, or precision/recall severely skewed
6. **Degenerate predictions** — near-constant output, model collapsed
7. **Suspiciously perfect metrics** — AUC=1.0 or ACC=1.0, likely leakage
8. **Score distribution anomaly** — overconfident or no class separation

**If ANY flag fires:**
- Include the flag prominently in the analysis report
- Do NOT select the flagged method as "best"
- Recommend specific corrective action (see sanity_checks.md)
- If the same flag fires 3+ consecutive times → promote to hard constraint in eval_policy.md

### Step 1: Load and summarize runs
Load the last 5-10 runs from the results directory. Produce a performance trend table.
Include per-category/subgroup breakdown — never report only overall metrics.

### Step 2: Determine run phase
Check docs/baselines.md and the run's config to determine:
- **Phase A run**: faithful implementation of a paper (first time this method was tried)
- **Phase B run**: extension or modification of a previous implementation

This matters for Step 3.

### Step 3: Analyze gaps
**If Phase A (paper reproduction):**
- Compare achieved metric vs. the paper's reported number. If gap > 5%, investigate why.
  - Data mismatch? Preprocessing difference? Missing component?
  - If reproduction is successful (within 5%), mark as "paper reproduced" — proceed to gap analysis.
- Gap analysis: identify what the paper explicitly does NOT address or leaves as future work.
  - Read the paper's limitations section (docs/papers/{id}.txt if available).
  - Look for patterns in our error cases that the paper's method structurally cannot handle.
  - These gaps become the primary input for the next literature-scout + researcher cycle.

**If Phase B (extension/hybrid):**
- Did the modification improve over Phase A? By how much?
- Which part of the modification drove the gain (if multiple components changed)?
- Is there a new gap that the modification introduced?

### Step 4: Classify failure type
overfitting / instability / data issue / architecture issue / plateau / paper-gap / reproduction-failure / **imbalance-exploitation** / **metric-misleading**

### Step 5: Extract root causes
2-3 root causes with confidence level (certain / likely / hypothesis)

### Step 6: Derive next directions
For each root cause, recommend one of:
- config-only change (no code needed)
- code change (engineering fix)
- literature search needed (gap requires a new method)
- synthesis opportunity (gap matches a known limitation — researcher should look for complementary paper)
- **eval fix needed** (metric/ranking logic is misleading — change how we evaluate)

### Step 7: Reflexion
If the same failure pattern appears in 3+ consecutive runs, promote it to a learned rule in
CLAUDE.md Mutable Known Failure Taxonomy:
`- [rule] {pattern}: {mitigation}  # promoted {date}`

## Rules
- do not draw conclusions from 1-2 runs (minimum 3)
- mark uncertain claims as "hypothesis"
- only promote a pattern to a rule after 3+ consecutive occurrences
- **NEVER declare a "best method" based solely on overall AUC/ACC/F1**
- **ALWAYS report per-subgroup metrics** — if subgroups exist, they MUST appear in the report
- **Question the metric before questioning the method** — if a method "looks good" on paper
  but something feels off, check if the metric itself is misleading first

## Output format for next_actions.md
Use hierarchical task IDs to track action items across loop iterations:

```
# Next Actions

## 1. {top-level goal}
Status: pending / in-progress / done / blocked

### 1.1 {sub-task}
Status: pending
Type: config-only / code-change / literature-search / eval-fix
Confidence: certain / likely / hypothesis
Detail: {what to change and why}

### 1.2 {sub-task}
...

## 2. {another top-level goal}
...
```

IDs persist across loop iterations so progress is trackable (e.g. task 1.1 done → move to 1.2 next loop).

## Output files
- results/ reports updated (error_analysis, next_actions)
- CLAUDE.md Mutable section updated (if new rule promoted)
- docs/eval_policy.md updated (if sanity check promoted to hard constraint)
