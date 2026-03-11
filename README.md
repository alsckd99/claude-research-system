# research-os

**전역 설치형 자율 연구개발 운영체제**

프로젝트마다 `.claude/` 폴더를 복사하지 않는다.
한 번 설치하면 모든 프로젝트에서 동일한 agents, skills, hooks가 동작한다.

---

## 설치 (프로젝트별)

```bash
# research-os를 어딘가에 clone해둔다 (1회)
git clone <this-repo> ~/research-os

# 적용할 프로젝트 경로를 인자로 넘긴다
bash ~/research-os/install.sh /path/to/my-project

# 또는 프로젝트 디렉토리 안에서 실행하면 현재 디렉토리에 설치
cd /path/to/my-project
bash ~/research-os/install.sh
```

`install.sh`가 하는 일 (`~/.claude/`는 건드리지 않음):
- `{프로젝트}/.claude/agents/` → 5개 에이전트 symlink
- `{프로젝트}/.claude/skills/` → 6개 skill symlink
- `{프로젝트}/.claude/settings.json` → 프로젝트 hooks 생성/병합
- MCP 서버 등록 (`--scope project`, 이 프로젝트에만 적용)
- `.env.research-os` 생성 (RESEARCH_OS_ROOT 기록)

---

## 새 프로젝트 시작

### 방법 1: CLI
```bash
python ~/research-os/orchestrator/new_project.py \
    --name deepfake-detector \
    --mission "멀티모달 딥페이크 탐지 모델 구현" \
    --metric AUROC \
    --domain image \
    --gpu-memory 24 \
    --output ~/projects/deepfake-detector
```

### 방법 2: Claude Code에서
```
research-os로 새 프로젝트 초기화해줘.
문제: 멀티모달 딥페이크 탐지
Primary metric: AUROC
Secondary: F1, latency
제약: GPU 24GB, 추론 100ms 이내
baseline부터 재현 가능하게 시작해.
```

---

## 자율 루프 실행

### 로컬 nightly
```bash
python ~/research-os/orchestrator/main.py \
    --project ~/projects/deepfake-detector \
    --mode nightly
```

### 주기 실행 (백그라운드)
```bash
nohup python ~/research-os/orchestrator/scheduler.py \
    --project ~/projects/deepfake-detector \
    --interval 24h \
    --mode full-loop &
```

### GitHub Actions
프로젝트 `.github/workflows/nightly.yml` 활성화 후 `ANTHROPIC_API_KEY` secret 등록.

---

## 구조

```
research-os/
├─ install.sh                    ← 전역 설치 스크립트
├─ plugin.json                   ← Claude Code 플러그인 매니페스트
├─ agents/                       ← ~/.claude/agents/ 로 설치
│  ├─ researcher.md              ← 논문 탐색
│  ├─ engineer.md                ← 코드 구현
│  ├─ runner.md                  ← 실험 실행
│  ├─ reviewer.md                ← 결과 검증
│  └─ policy_guard.md            ← 정책 수호 (Immutable Core 보호)
├─ skills/                       ← ~/.claude/skills/ 로 설치
│  ├─ bootstrap-project/         ← 새 프로젝트 초기화
│  ├─ literature-scout/          ← 논문 탐색 (Semantic Scholar, arXiv)
│  ├─ experiment-runner/         ← 실험 실행 + 결과 저장
│  ├─ result-analyzer/           ← 실패 분류 + 원인 분석
│  ├─ method-reviser/            ← 근거 기반 코드 수정
│  └─ policy-evolver/            ← 평가 정책 점진적 진화
├─ hooks/
│  └─ settings.json              ← ~/.claude/settings.json 에 병합
├─ templates/
│  └─ project-skeleton/          ← 새 프로젝트 최소 구조
│     ├─ scripts/                ← 공용 스크립트 (run_experiment 등)
│     └─ .github/workflows/      ← nightly GitHub Actions
└─ orchestrator/
   ├─ new_project.py             ← 프로젝트 초기화 CLI
   ├─ main.py                    ← 자율 루프 오케스트레이터
   └─ scheduler.py               ← 주기 실행 스케줄러
```

---

## 3단계 자율 루프

| 단계 | 트리거 | 동작 |
|------|--------|------|
| 1단계 (반자동) | 사람이 지시 | bootstrap → 구현 → 실험 → 보고 |
| 2단계 (보조 루프) | nightly / PR | 분석 → 제안 → 단순 수정 → 실험 |
| 3단계 (자율 루프) | cron / 성능 하락 감지 | 문헌 탐색 → 정책 진화 → 구현 → 실험 → PR |

---

## 커뮤니티 레퍼런스

- [Awesome Claude Code](https://github.com/anthropics/awesome-claude-code) — skills, agents, plugins 큐레이션
- [Claude Code Docs](https://docs.anthropic.com/claude-code) — 공식 문서
- [Anthropic Discord](https://discord.gg/anthropic) — 개발자 커뮤니티
- [Claude Code GitHub](https://github.com/anthropics/claude-code) — 이슈, 토론
