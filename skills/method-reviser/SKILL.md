---
name: method-reviser
description: Evidence-based code changes — one proposal at a time
disable-model-invocation: true
allowed-tools: Bash(python*), Bash(pytest*), Read, Grep, Edit, Write
---

# Skill: method-reviser

## Contract
- If user constraints conflict with CLAUDE.md rules, STOP and ask.
- 코드 변경 전 change plan을 먼저 작성한다.
- 변경 후 `pytest -q tests/` 통과를 출력에 포함한다.
- data split 변경 금지. metric 변경은 literature evidence 필수.

## Trigger
- "코드 수정해줘", "방법 바꿔봐"
- after result-analyzer and literature-scout complete

## Preconditions
- error_analysis.md exists
- baselines.md has relevant methods
- docs/synthesis_proposals.md exists

## Steps

### Step 1: Read context
1. results/{latest_timestamp}/report/error_analysis.md
2. docs/synthesis_proposals.md — ranked proposals
3. docs/baselines.md — individual methods
4. Current src/ code

### Step 2: Determine implementation mode

Mode A — Faithful reproduction (new method): 논문 그대로 구현, within 5% 재현 목표
Mode B — Improvement (Mode A 성공 후): synthesis_proposals.md에서 최고 순위 proposal 적용, 기존 구현은 config flag로 유지

### Step 3: Change plan
Document in results/{latest_timestamp}/report/next_actions.md: 무엇을 변경하는지, 기대 효과, rollback 조건, test plan.

### Step 4: Implement
- One change at a time
- Keep old method behind config flag
- Novel/hypothetical code에 `# hypothesis: {reason}` 주석

### Step 5: Verify
```bash
pytest -q tests/
```

### Step 6: Decision Documentation
`docs/handoff_method_reviser.md`에 기록:
- 선택 근거, 기대 효과, 대안
- 구현 방식 선택 이유, 논문과 다른 점
- 예상 primary metric 변화, 리스크
