---
paths:
  - "docs/**/*.md"
  - "agents/researcher.md"
  - "skills/literature-scout/**"
---

# Paper Search Policy

논문 검색 시 항상 이 우선순위 적용:
- 최근 3년 우선. 이전 논문은 foundational하거나 많이 인용된 경우만.
- 탑티어 venue 우선: NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, ACL, EMNLP, NAACL, SIGKDD, AAAI, IJCAI, TPAMI, IJCV, JMLR
- 3년 이상 논문은 citationCount > 50 필요
- 스킵: 워크숍 단독, arXiv-only + 인용 5 미만 + 1년 이상

검색 순서: Semantic Scholar → arXiv MCP → OpenAlex → Brave Search
