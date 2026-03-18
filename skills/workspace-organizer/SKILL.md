---
name: workspace-organizer
description: Auto-organize workspace files and clean up obsolete scripts
disable-model-invocation: true
allowed-tools: Bash(python*), Bash(find*), Bash(mv*), Bash(mkdir*), Read, Grep, Glob, Edit, Write
---

# Skill: workspace-organizer

## Contract
- 삭제 전 반드시 git에 커밋되어 있는지 확인한다 — 커밋 안 된 파일은 삭제하지 않는다.
- 아카이브는 삭제가 아니라 `_archive/` 디렉토리로 이동이다.
- `results/{timestamp}/` 내 파일은 절대 삭제하지 않는다.

## Trigger
- 매 improvement loop iteration 종료 후 자동 실행
- "정리해줘", "workspace 정리", "clean up"

## Part 1: 파일 자동 정리 (organize)

프로젝트 루트나 잘못된 위치에 흩어진 파일들을 올바른 timestamp 디렉토리로 정리.

### 규칙

| 파일 패턴 | 이동 대상 |
|---|---|
| `*.log` (루트 또는 logs/) | `logs/YYYYMMDD/` |
| `*.png`, `*.jpg`, `*.pdf` (루트) | `results/{latest_timestamp}/plots/` |
| `*_results*.json` (루트) | `results/{latest_timestamp}/` |
| `debug_*.md`, `debug_*.json` (루트) | `results/{latest_timestamp}/debug/` |
| `*_analysis*.md` (루트) | `results/{latest_timestamp}/analysis/` |
| `error_analysis.md`, `next_actions.md` (results 루트) | `results/{latest_timestamp}/report/` |
| `decision_report.md` (results 루트) | `results/{latest_timestamp}/report/` |
| `results/reports/plots/*` | `results/{latest_timestamp}/plots/` |
| `tmp_*`, `temp_*` | `_archive/{YYYYMMDD}/` |

### 실행 방법
```bash
python scripts/organize_workspace.py
```

## Part 2: 스크립트 정리 (cleanup)

한번 쓰고 더 이상 필요 없는 스크립트를 식별하고 아카이브.

### 판별 기준 — 아래 조건 모두 충족 시 "불필요":
1. `scripts/` 내 `.py` 파일
2. 다른 `.py`, `.sh`, `.yaml`, `SKILL.md` 파일에서 import/호출되지 않음
3. `hooks.json`에서 참조되지 않음
4. 파일명이 core 스크립트 목록에 없음 (아래 참조)
5. 최근 3일 이내 생성된 임시 스크립트 (prefix: `tmp_`, `test_`, `debug_`, `scratch_`, `fix_`)

### Core 스크립트 (절대 정리 대상 아님)
```
run_experiment.py, validate_config.py, debug_logger.py, server_utils.py,
analyze_failures.py, summarize_results.py, propose_next_steps.py,
visualize_results.py, generate_decision_report.py, save_session_state.py,
organize_workspace.py
```

### 아카이브 동작
1. `_archive/scripts/YYYYMMDD/`로 이동 (삭제 아님)
2. `_archive/scripts/archive_log.md`에 기록: 파일명, 이동일, 이유
3. git commit: `chore: archive unused scripts`

### 실행 방법
```bash
python scripts/organize_workspace.py --cleanup
```

## Part 3: improvement loop 연동

매 iteration 종료 시 자동 실행:
1. `organize_workspace.py` — 흩어진 파일 정리
2. `organize_workspace.py --cleanup` — 불필요 스크립트 아카이브
3. git commit

## Output
- 정리된 `results/{timestamp}/` 구조
- `_archive/` — 아카이브된 파일들
- `_archive/scripts/archive_log.md` — 아카이브 로그
