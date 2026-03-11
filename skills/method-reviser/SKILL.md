# Skill: method-reviser

## Trigger
- "코드 수정해줘", "방법 바꿔봐"
- after result-analyzer and literature-scout complete

## Preconditions
- error_analysis.md exists and is up to date
- baselines.md has relevant methods recorded

## Steps
1. Write a change plan before touching code: rationale / expected effect / rollback condition
2. One change at a time; keep old methods behind a config flag
3. After changes: ruff && black && pytest -q must pass

## Not allowed
- changing data split
- multiple simultaneous changes
- changing metrics without literature evidence (metric changes go through policy-evolver)

## Output
- updated src/ code (tests passing)
- experiments/reports/next_actions.md updated
