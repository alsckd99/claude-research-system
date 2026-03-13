---
name: policy-evolver
description: Update eval_policy.md based on literature evidence — policy_guard approval required
disable-model-invocation: true
---

# Skill: policy-evolver

## Contract
- CLAUDE.md Immutable Core는 절대 수정하지 않는다.
- 모든 변경은 policy_guard 승인 후에만 적용한다.
- 변경 사유와 문헌 근거를 policy_changelog.md에 기록한다.

## Trigger
- after researcher proposes new metric or test candidates
- "평가 정책 업데이트해줘"

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
