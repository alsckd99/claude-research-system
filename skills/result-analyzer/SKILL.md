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

## Output
- experiments/reports/error_analysis.md updated
- experiments/reports/next_actions.md updated
- CLAUDE.md Mutable section updated (if new rule promoted)
