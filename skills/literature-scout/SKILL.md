---
name: literature-scout
description: Find recent papers and methods for current failure patterns
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, WebFetch, WebSearch
---

# Skill: literature-scout

## Contract
- baselines.md에 이미 있는 method는 다시 검색하지 않는다.
- 검색 결과에서 불확실한 주장은 "hypothesis"로 표기한다.

## Trigger
- "논문 찾아줘", "관련 방법 조사해줘"
- after result-analyzer completes
- nightly loop search phase

## Steps
1. Read error_analysis.md and baselines.md to understand current state
2. Convert failure patterns into search queries
3. Paper priority and search sources: **follow agents/researcher.md** (단일 정의)
4. For promising papers, download via arXiv MCP if arXiv ID is available
5. Add top 3-5 methods to docs/baselines.md in standard format
6. Add new metric or test candidates to proposed_policy_changes.md

## Output
- docs/baselines.md updated
- results/reports/next_actions.md updated
