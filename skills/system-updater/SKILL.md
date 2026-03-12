# Skill: system-updater

## Trigger
- 세션 시작 시 자동 (SessionStart hook에서 호출)
- "업데이트 확인해줘", "최신 기능 확인해줘"

## Purpose
Claude Code 및 관련 도구의 최신 변경사항을 확인하고,
claude-research-system에 반영할 것이 있으면 사용자에게 제안한다.

---

## Step 1: 최신 정보 수집

아래 소스를 확인한다 (접근 가능한 것만):

1. Claude Code 공식 문서
   - https://docs.anthropic.com/en/docs/claude-code/overview
   - https://docs.anthropic.com/en/docs/claude-code/cli-usage
   - https://docs.anthropic.com/en/docs/claude-code/hooks
   - https://docs.anthropic.com/en/docs/claude-code/mcp
   - https://docs.anthropic.com/en/docs/claude-code/settings
   - https://docs.anthropic.com/en/docs/claude-code/agents
   - https://docs.anthropic.com/en/docs/claude-code/skills

2. Claude Code GitHub
   - https://github.com/anthropics/claude-code/releases
   - https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md

3. Anthropic API / Model 업데이트
   - https://docs.anthropic.com/en/docs/about-claude/models
   - https://docs.anthropic.com/en/api/getting-started

4. MCP 생태계
   - https://github.com/modelcontextprotocol/servers

수집 시 중점:
- 새 CLI 옵션, 새 hook 이벤트, 새 permission 패턴
- 새 모델 (더 빠르거나 저렴한 모델이 나왔는지)
- 새 MCP 서버 (연구에 유용한 것)
- deprecated/removed 기능
- 새 skill/agent 관련 기능 (frontmatter, 호출 방식 등)

---

## Step 2: 영향 분석

수집한 변경사항 중 claude-research-system에 영향이 있는 것을 분류:

```
## Update Check — {date}

### 반영 권장 (직접적 영향)
1. {변경}: {어떤 파일에 어떤 영향}
   - 현재: {현재 상태}
   - 변경 후: {변경 후 상태}
   - 이유: {왜 반영해야 하는지}

### 반영 검토 (개선 가능)
1. {변경}: {설명}
   - 장점: ...
   - 단점/리스크: ...

### 참고만 (당장 영향 없음)
- ...
```

---

## Step 3: 사용자에게 제안

분석 결과를 사용자에게 보여주고 확인:

```
[system-updater] Claude Code 업데이트 확인 완료

반영 권장:
1. {변경 A} — {한줄 설명}
2. {변경 B} — {한줄 설명}

반영 검토:
1. {변경 C} — {한줄 설명}

적용할까요? (전체 / 선택 / 스킵)
```

사용자가 승인하지 않으면 아무것도 수정하지 않는다.

---

## Step 4: 적용

승인된 변경사항을 적용한다. 수정 대상이 될 수 있는 파일들:

### 시스템 파일 (claude-research-system 내부)
- `agents/*.md` — 새 기능 활용, deprecated 기능 제거
- `skills/*/SKILL.md` — 새 tool/hook 활용
- `hooks/hooks.json` — 새 hook 이벤트, 새 permission 패턴
- `orchestrator/*.py` — 새 CLI 옵션, 새 API 기능
- `install.sh` — 새 MCP 서버, 새 dependency
- `templates/**` — 프로젝트 템플릿 업데이트

### 프로젝트 파일 (설치된 프로젝트)
- `.claude/settings.json` — 새 permission 패턴
- `.claude/agents/*.md` — agent frontmatter 변경
- `.mcp.json` — 새 MCP 서버

### 적용 규칙
- 한 파일씩 수정하고 즉시 git commit
- 커밋 메시지: `chore(update): {무엇을 왜 변경했는지}`
- 기존 동작을 깨뜨리지 않도록 주의
- 불확실한 변경은 적용하지 않음

---

## Step 5: 로그

적용 결과를 기록:

`docs/update_log.md` (claude-research-system repo):
```
## {date} — System Update

### Applied
1. {변경}: {무엇을 수정했는지}
   - files: {수정된 파일 목록}

### Skipped
1. {변경}: {왜 스킵했는지}

### Source
- {확인한 URL/문서}
```

---

## Output
- 사용자에게 업데이트 요약 보고
- 승인된 변경사항 적용 + git commit
- `docs/update_log.md` 갱신
