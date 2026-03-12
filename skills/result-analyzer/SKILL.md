# Skill: result-analyzer

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps

### Step 1: Load and summarize runs
Load the last 5-10 runs from experiments/registry.json. Produce a performance trend table.

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
overfitting / instability / data issue / architecture issue / plateau / paper-gap / reproduction-failure

### Step 5: Extract root causes
2-3 root causes with confidence level (certain / likely / hypothesis)

### Step 6: Derive next directions
For each root cause, recommend one of:
- config-only change (no code needed)
- code change (engineering fix)
- literature search needed (gap requires a new method)
- synthesis opportunity (gap matches a known limitation — researcher should look for complementary paper)

### Step 7: Reflexion
If the same failure pattern appears in 3+ consecutive runs, promote it to a learned rule in
CLAUDE.md Mutable Known Failure Taxonomy:
`- [rule] {pattern}: {mitigation}  # promoted {date}`

## Rules
- do not draw conclusions from 1-2 runs (minimum 3)
- mark uncertain claims as "hypothesis"
- only promote a pattern to a rule after 3+ consecutive occurrences

## Output format for next_actions.md
Use hierarchical task IDs to track action items across loop iterations:

```
# Next Actions

## 1. {top-level goal}
Status: pending / in-progress / done / blocked

### 1.1 {sub-task}
Status: pending
Type: config-only / code-change / literature-search
Confidence: certain / likely / hypothesis
Detail: {what to change and why}

### 1.2 {sub-task}
...

## 2. {another top-level goal}
...
```

IDs persist across loop iterations so progress is trackable (e.g. task 1.1 done → move to 1.2 next loop).

## Output files
- experiments/reports/error_analysis.md updated
- experiments/reports/next_actions.md updated (hierarchical task IDs)
- CLAUDE.md Mutable section updated (if new rule promoted)
