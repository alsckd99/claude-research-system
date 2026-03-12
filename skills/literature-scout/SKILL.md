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

3. Paper priority — apply before selecting candidates:
   - Prefer papers from the last 3 years
   - Top-tier venues first: NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, ACL, EMNLP, NAACL, SIGKDD, AAAI, IJCAI, TPAMI, IJCV, JMLR
   - For papers 3+ years old: citationCount > 50 required
   - Skip: workshop-only or arXiv-only with < 5 citations and > 1 year old

4. Search in order:

   **Semantic Scholar** (use fetch MCP — includes venue and citation count):
   - https://api.semanticscholar.org/graph/v1/paper/search?query={q}&fields=title,abstract,year,citationCount,url,venue,externalIds&limit=20
   - Sort results: top-tier venue → recency → citation count

   **arXiv MCP** (for recent preprints, last 3 years):
   - `search_papers(query, max_results=20)` then filter by year
   - `download_paper(paper_id)` / `read_paper(paper_id)` for full text

   **OpenAlex** (supplement, use fetch MCP):
   - https://api.openalex.org/works?search={q}&sort=cited_by_count:desc&per-page=10&select=title,authorships,publication_year,doi,open_access,cited_by_count,abstract_inverted_index

   **Brave Search MCP** (if available): benchmark leaderboards, GitHub repos, official docs

5. For promising papers found via Semantic Scholar or OpenAlex, download via arXiv MCP if arXiv ID is available
6. Add top 3-5 methods to docs/baselines.md in standard format
7. Add new metric or test candidates to proposed_policy_changes.md

## Note on token efficiency
arXiv MCP provides structured tool calls (no XML parsing, no manual HTTP construction).
Papers downloaded once are cached at ~/.arxiv-mcp-server/papers and can be re-read without re-downloading.

## Output
- docs/baselines.md updated
- experiments/reports/next_actions.md updated
