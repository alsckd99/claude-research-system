# Skill: result-analyzer

## Trigger
- "결과 분석해줘", "왜 성능이 안 올랐지?"
- after experiment-runner completes

## Steps
1. Load the last 5-10 runs from experiments/registry.json
2. Analyze performance trend (table format)
3. Classify failure type: overfitting / instability / data issue / architecture issue / plateau
4. Extract 2-3 root causes with confidence level noted (certain / likely / hypothesis)
5. Derive next directions (config-only change / code change / literature search needed)
6. Reflexion: if the same failure pattern appears in 3+ consecutive runs, promote it to a
   learned rule in CLAUDE.md Mutable Known Failure Taxonomy section:
   `- [rule] {pattern}: {mitigation}  # promoted {date}`
   This prevents repeating the same mistake in future loops.

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
