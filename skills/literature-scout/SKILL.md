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
3. Search in order:
   - Semantic Scholar: https://api.semanticscholar.org/graph/v1/paper/search?query={q}&fields=title,abstract,year,citationCount,url&limit=10
   - arXiv: http://export.arxiv.org/api/query?search_query=all:{q}&sortBy=submittedDate&sortOrder=descending&max_results=10
   - OpenAlex (supplement): https://api.openalex.org/works?search={q}&sort=cited_by_count:desc&per-page=10&select=title,authorships,publication_year,doi,open_access,cited_by_count,abstract_inverted_index
   - Brave Search MCP (if available): for GitHub repos, official docs, benchmark leaderboards
4. Add top 3-5 methods to docs/baselines.md in standard format
5. Add new metric or test candidates to proposed_policy_changes.md

## Output
- docs/baselines.md updated
- experiments/reports/next_actions.md updated
