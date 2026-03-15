[CRITICAL RULES — re-injected after compaction]

1. 사용자에게 질문하지 마라. 판단이 필요하면 스스로 결정하고 계속 진행해라.
2. 결과는 반드시 timestamp 디렉토리에 저장: results/iterations/YYYYMMDD_HHMMSS/
3. 시각화(plot)를 항상 생성하고 결과 디렉토리에 포함해라.
4. 코드 단위로 디버깅하고 개선해라. 에러 발생 시 직접 분석하고 수정해라.
5. 한 번에 하나의 변경만 적용 — 여러 method 동시 적용 금지.
6. git add는 변경한 파일만 — git add -A 금지.
7. git push --force, rm -rf, git reset --hard 금지.
8. CLAUDE.md와 .claude/rules/*.md의 규칙을 반드시 준수해라.
