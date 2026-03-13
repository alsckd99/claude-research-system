---
paths:
  - "docs/**/*.md"
  - "agents/researcher.md"
  - "skills/literature-scout/**"
---

# Paper Search Policy

논문 검색 시 항상 이 우선순위 적용:
- **현재연도-1 (최신 1년) 최우선**. 2-3년 전은 보조. 그 이전은 foundational/widely cited만.
- 탑티어 venue 우선: NeurIPS, ICML, ICLR, CVPR, ICCV, ECCV, ACL, EMNLP, NAACL, SIGKDD, AAAI, IJCAI, TPAMI, IJCV, JMLR
- 3년 이상 논문은 citationCount > 50 필요
- 스킵: 워크숍 단독, arXiv-only + 인용 5 미만 + 1년 이상

조사 → 선별 흐름:
1. 최소 20편 이상 광범위 조사 → `docs/literature_survey.md`
2. 논문별 분석 (방법론, 강점, 약점, 적합 task)
3. 3-5편 선별 + 채택 근거 → `docs/model_selection_log.md`

검색 순서: Semantic Scholar → arXiv MCP → OpenAlex → Brave Search
