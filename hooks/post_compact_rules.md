[CRITICAL RULES — re-injected after compaction]

1. 사용자에게 질문하지 마라. 판단이 필요하면 스스로 결정하고 계속 진행해라.
2. 모든 결과는 반드시 `results/{YYYYMMDD_HHMMSS}/` 안에 저장 — results 루트에 파일 직접 두지 않는다. (registry.json, final_report.md만 예외)
3. 시각화(plot)는 `results/{timestamp}/plots/`에 생성.
4. 디버그 로그는 `results/{timestamp}/debug/`에 저장.
5. 분석 파일(deep_analysis.md, debug_findings.md, gap_analysis.md)은 `results/{timestamp}/analysis/`에 저장.
6. 리포트(error_analysis.md, next_actions.md, decision_report.md)는 `results/{timestamp}/report/`에 저장.
7. 코드 단위로 디버깅하고 개선해라. 에러 발생 시 직접 분석하고 수정해라.
8. 한 번에 하나의 변경만 적용 — 여러 method 동시 적용 금지.
9. git add는 변경한 파일만 (auto-commit hook이 자동 처리).
10. git push --force, rm -rf, git reset --hard 금지.
11. CLAUDE.md와 .claude/rules/*.md의 규칙을 반드시 준수해라.
12. 매 iteration 종료 시 workspace-organizer 실행: `python scripts/organize_workspace.py --cleanup`
