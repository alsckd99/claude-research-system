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

   **arXiv** (use arxiv MCP tools — more token-efficient than HTTP fetch):
   - `search_papers(query, max_results=10)` — returns structured results with IDs
   - `download_paper(paper_id)` — downloads PDF locally
   - `read_paper(paper_id)` — reads full text including figures and tables

   **Semantic Scholar** (use fetch MCP — HTTP call):
   - https://api.semanticscholar.org/graph/v1/paper/search?query={q}&fields=title,abstract,year,citationCount,url&limit=10

   **OpenAlex** (supplement, use fetch MCP):
   - https://api.openalex.org/works?search={q}&sort=cited_by_count:desc&per-page=10&select=title,authorships,publication_year,doi,open_access,cited_by_count,abstract_inverted_index

   **Brave Search MCP** (if available): for GitHub repos, official docs, benchmark leaderboards

4. For promising papers found via Semantic Scholar or OpenAlex, download via arXiv MCP if arXiv ID is available
5. Add top 3-5 methods to docs/baselines.md in standard format
6. Add new metric or test candidates to proposed_policy_changes.md

## Note on token efficiency
arXiv MCP provides structured tool calls (no XML parsing, no manual HTTP construction).
Papers downloaded once are cached at ~/.arxiv-mcp-server/papers and can be re-read without re-downloading.

## Output
- docs/baselines.md updated
- experiments/reports/next_actions.md updated
