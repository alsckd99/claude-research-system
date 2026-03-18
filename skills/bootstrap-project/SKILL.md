---
name: bootstrap-project
description: New project initialization — auto plan mode, collect info, research, setup, run baseline, enter loop
disable-model-invocation: false
---

# Skill: bootstrap-project

## Contract
- Phase 6 safety gate를 반드시 통과한 후에만 improvement loop 진입.
- 사용자에게 질문은 Phase 1에서 한 번만. 이후 추가 확인 질문 하지 않는다.
- 모든 모델 선정 이유를 `docs/model_selection_log.md`에 기록한다.

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘", "create a new project"
- project directory is empty

## Core principle: 연구는 비선형이다

어느 단계에서든 새 발견이 있으면 기존 계획을 수정한다.
변경 시 `docs/research_log.md`에 기록.

Phase 0~7은 최초 셋업 순서. Loop 진입 후에는 분석/탐색/구현/실험이 유기적으로 반복.

---

## Phase -1: Auto Plan Mode (MANDATORY FIRST STEP)

"create a new project" 또는 동의어 입력 시 **자동으로 Plan 모드 진입**.

### 동작
1. Plan 모드 진입 (EnterPlanMode)
2. 사용자에게 아래 질문 (한 번에 모아서):
   - Objective — 무엇을 달성하려는가 (한 문장)
   - Train dataset — 경로 또는 이름
   - Test dataset — 경로 또는 이름
   - (선택) 특별한 제약사항이나 요구사항
3. 사용자 답변 기반으로 실행 계획 작성:
   - 연구 방향 & 관련 키워드
   - 예상 모델 후보군 (논문 기반)
   - 프로젝트 구조
   - 평가 프레임워크 초안
   - 예상 타임라인 (Phase별)
4. 계획을 사용자에게 보여줌
5. 사용자 확인 ("좋아", "진행해", "ㅇㅇ" 등) 받으면:
   - Plan 모드 종료 (ExitPlanMode)
   - **이후 Phase 0~7 + Loop를 사용자 추가 질문 없이 자율 실행**
6. 사용자 수정 요청 시 → 계획 수정 → 다시 확인 요청

### 핵심 원칙
- 계획 확인 받은 후에는 **절대 추가 질문하지 않는다**
- 판단이 필요한 상황은 스스로 결정하고 `docs/research_log.md`에 기록
- 에러 발생 시 직접 분석하고 수정한다

---

## Phase 0: System check

GPU 확인 — `python scripts/server_utils.py`. 다른 사용자 GPU 자동 회피. 가용 GPU 없으면 그때만 대기.

## Phase 1: (Skipped — Phase -1에서 이미 수집)

Phase -1에서 받은 정보 사용. 추가 질문 없음.

## Phase 2: Initial research + Data audit

1. 관련 논문에서 기존 모델/코드 검색 (직접 설계 X)
2. 찾은 논문의 참조도 따라감
3. 모델 선정 이유를 `docs/model_selection_log.md`에 기록
4. data-auditor skill로 데이터셋 분석

보고 후 **확인을 기다리지 않고 바로 진행**.

## Phase 3: Setup

1. Project structure 생성
2. Clone repos & download checkpoints
3. Register: `models/model_registry.json`
4. conda 환경 생성

## Phase 4: Evaluation framework

eval metrics 설계. Sanity checks from `sanity_checks.md` 포함. Output: `docs/eval_policy.md`

## Phase 5: Implement & run baseline

Engineer agent → pipeline 구현 → baseline 실행

## Phase 6: Safety gate — DO NOT SKIP

1. `pytest -q` passes
2. `docs/eval_policy.md` has confirmed primary metric
3. At least 1 completed evaluation in results/
4. Sanity checks pass on baseline results

## Phase 7: Improvement loop (continuous, autonomous)

자동으로 continuous 모드 진입. 매 iteration:
1. 분석 (result-analyzer)
2. 완료된 method 스킵
3. 논문 검색 (3iter마다, literature-scout)
4. 구현 (method-reviser → engineer)
5. 실행/비교/개선 or revert (experiment-runner)
6. **workspace 정리 (workspace-organizer)** — 흩어진 파일 정리 + 불필요 스크립트 아카이브
7. Repeat

Escalation: 2+ loops 개선없음→literature search, error 3+회→다음 method, pytest fail→fix후 재실행
