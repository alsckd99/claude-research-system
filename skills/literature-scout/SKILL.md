# Skill: literature-scout

## Trigger
- "논문 찾아줘", "관련 방법 조사해줘"
- after result-analyzer completes
- nightly loop search phase

## Purpose
Find recent papers and methods related to current failure patterns.

## Steps
1. Read error_analysis.md and baselines.md to understand current state
2. Convert failure patterns into search queries

3. Paper priority and search sources: **follow agents/researcher.md** (단일 정의)
   - 우선순위: 최근 3년 > 탑티어 venue > citation count
   - 검색 순서: Semantic Scholar → arXiv MCP → OpenAlex → Brave Search
   - 상세 URL/API 형식은 researcher.md 참조

4. For promising papers, download via arXiv MCP if arXiv ID is available
5. Add top 3-5 methods to docs/baselines.md in standard format
6. Add new metric or test candidates to proposed_policy_changes.md

## Note on token efficiency
arXiv MCP provides structured tool calls (no XML parsing, no manual HTTP construction).
Papers downloaded once are cached at ~/.arxiv-mcp-server/papers and can be re-read without re-downloading.

## Output
- docs/baselines.md updated
- results/reports/next_actions.md updated
