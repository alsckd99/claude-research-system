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
2. Convert failure patterns + objective into search queries
3. Paper priority and search sources: **follow agents/researcher.md** (단일 정의)
4. **광범위 조사**: 최소 20편 이상 수집, 각 논문 간략 정리 → `docs/literature_survey.md`
5. **논문별 분석**: 핵심 방법론, 적합 task, 강점, 약점, 코드/checkpoint 여부
6. **선별**: 분석 기반 3-5편 최종 선택 → `docs/model_selection_log.md`에 채택 근거 기록
7. 선별된 method를 docs/baselines.md에 추가
8. For promising papers, download via arXiv MCP if arXiv ID is available
9. Add new metric or test candidates to proposed_policy_changes.md

## Output
- `docs/literature_survey.md` — 전체 조사 결과 (20편+, 간략 분석 포함)
- `docs/model_selection_log.md` — 선별 모델의 채택 근거 상세
- docs/baselines.md updated
- results/{latest_timestamp}/report/next_actions.md updated
