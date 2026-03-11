# Skill: policy-evolver

## Trigger
- after researcher proposes new metric or test candidates
- "평가 정책 업데이트해줘"

## Purpose
Incrementally update eval_policy.md and the mutable section of CLAUDE.md based on literature evidence and failure analysis.
Immutable Core is never touched.

## Steps
1. Load pending proposals from proposed_policy_changes.md
2. Delegate to policy_guard for approval review
3. Apply only approved changes to docs/eval_policy.md
4. Update CLAUDE.md Mutable Research Policy section only
5. Record changes in policy_changelog.md

## Editable files
- docs/eval_policy.md
- CLAUDE.md Mutable Research Policy section

## Never edit
- CLAUDE.md Immutable Core
- primary metric
