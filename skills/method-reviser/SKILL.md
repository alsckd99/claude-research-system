# Skill: method-reviser

## Trigger
- "코드 수정해줘", "방법 바꿔봐"
- after result-analyzer and literature-scout complete

## Preconditions
- error_analysis.md exists and is up to date
- baselines.md has relevant methods recorded
- docs/synthesis_proposals.md exists (written by researcher Mode B)

## Steps

### Step 1: Read context
1. results/reports/error_analysis.md — what is failing and why
2. docs/synthesis_proposals.md — ranked proposals from researcher (preferred input)
3. docs/baselines.md — individual paper methods as fallback
4. Current src/ code — understand what is already implemented

### Step 2: Determine implementation mode

**Mode A — Faithful reproduction** (default for any new method):
- Check if this method has ever been run before (look in results/registry.json)
- If not: implement the paper exactly as described — no modifications, no improvements
- Goal: reproduce the paper's reported metric. 재현 성공 기준은 프로젝트와 metric에 따라 다르다 (default: within 5%, eval_policy.md에 다른 기준이 있으면 따른다)
- Do NOT add ideas from other papers yet

**Mode B — Improvement** (only after Mode A succeeded):
- Read result-analyzer's gap analysis from error_analysis.md
- Read docs/synthesis_proposals.md for ranked proposals
- Select the highest-ranked proposal that addresses a confirmed gap
- Keep Mode A implementation behind a config flag for rollback

Mode A → B 순서를 권장하지만, 재현이 불가능한 경우 (코드 비공개, 데이터셋 불일치 등) 사유를 기록하고 Mode B로 진행할 수 있다.

### Step 3: Write a change plan BEFORE touching code
Document in results/reports/next_actions.md:
```
## Change Plan — {date}
proposal: {name from synthesis_proposals.md or baselines.md}

### What changes
- {module/file}: {what and why}

### What stays the same (behind config flag)
- {old method}: enabled via config flag

### Expected effect on primary metric
{estimate with reasoning — cite paper evidence}

### Novel elements (if any)
{what is not directly from any paper — clearly labeled as "hypothesis"}

### Rollback condition
{어떤 조건에서 되돌릴 것인지}

### Test plan
- existing tests must still pass
- add test for new module
```

### Step 4: Implement
- One change at a time — never mix two proposals in one implementation
- Keep old method behind a config flag
- Label novel/hypothetical code with `# hypothesis: {reason}` comments

### Step 5: Verify
Tests must pass before handoff:
```bash
pytest -q tests/
```
프로젝트에 linter가 설정되어 있으면 함께 확인.

## Not allowed
- changing data split
- multiple simultaneous proposals in one implementation
- changing metrics without literature evidence (metric changes go through policy-evolver)

## Output
- updated src/ code (tests passing)
- results/reports/next_actions.md updated with change plan
- docs/handoff_method_reviser.md: what was changed, what is novel, rollback instructions
