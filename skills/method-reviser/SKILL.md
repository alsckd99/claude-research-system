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
1. experiments/reports/error_analysis.md — what is failing and why
2. docs/synthesis_proposals.md — ranked proposals from researcher (preferred input)
3. docs/baselines.md — individual paper methods as fallback
4. Current src/ code — understand what is already implemented

### Step 2: Determine implementation mode

**Mode A — Faithful reproduction** (default for any new method):
- Check if this method has ever been run before (look in experiments/registry.json)
- If not: implement the paper exactly as described — no modifications, no improvements
- Goal: reproduce the paper's reported metric within 5%
- Do NOT add ideas from other papers yet

**Mode B — Improvement** (only after Mode A succeeded):
- Read result-analyzer's gap analysis from error_analysis.md
- Read docs/synthesis_proposals.md for ranked proposals
- Select the highest-ranked proposal that addresses a confirmed gap
- Implement as: extension (1 paper + 1 modification) or hybrid (2+ papers composed)
- Keep Mode A implementation behind a config flag for rollback

Never skip Mode A to go directly to Mode B — the paper must be reproduced first.

### Step 3: Write a change plan BEFORE touching code
Document in experiments/reports/next_actions.md:
```
## Change Plan — {date}
proposal: {name from synthesis_proposals.md or baselines.md}
type: direct / extension / hybrid

### What changes
- {module/file}: {what and why}

### What stays the same (behind config flag)
- {old method}: enabled via config `model.{name}_enabled: false`

### Expected effect on primary metric
{estimate with reasoning — cite paper evidence}

### Novel elements (if extension or hybrid)
{what is not directly from any paper — clearly labeled as "hypothesis"}

### Rollback condition
If primary metric drops more than {X}% vs previous best, revert via config flag.

### Test plan
- existing tests must still pass
- add test for new module: tests/test_{module}.py
```

### Step 4: Implement
- One change at a time — never mix two proposals in one implementation
- Keep old method behind a config flag (`configs/base.yaml`)
- For hybrid: implement each paper's component as a separate class/module, then compose
- Label novel/hypothetical code with `# hypothesis: {reason}` comments

### Step 5: Verify
```bash
ruff check src/ && black --check src/ && pytest -q tests/
```
All must pass before handoff to runner.

## Not allowed
- changing data split
- multiple simultaneous proposals in one implementation
- changing metrics without literature evidence (metric changes go through policy-evolver)
- implementing a hybrid without a mechanistic reason in the change plan

## Output
- updated src/ code (tests passing)
- experiments/reports/next_actions.md updated with change plan
- docs/handoff_method_reviser.md: what was changed, what is novel, rollback instructions
