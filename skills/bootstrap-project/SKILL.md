# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
사용자의 objective를 받아서, 연구 탐색 → 구현 → 실험 → 개선 루프까지
자동으로 수행하는 연구 프로젝트를 만든다.

---

## Phase 1: Collect info

사용자에게 질문:
1. **Objective** — 한 문장
2. **Train dataset** — 학습에 쓸 데이터 경로 또는 이름
3. **Test dataset** — 평가에 쓸 데이터 경로 또는 이름 (train과 같을 수 있음)
4. **GPU** — 사용 가능한 GPU (예: 0 / 0,1 / all / cpu)

질문하지 않는 것:
- 어떤 모델을 쓸지 (자동 탐색)
- 어떤 metric을 쓸지 (논문 기반 자동 결정)
- 어떤 방법론을 쓸지 (논문 기반 자동 결정)

---

## Phase 2: Objective analysis & project type

Objective를 분석해서 **프로젝트 유형**을 판단한다. 이 판단이 이후 모든 Phase의 흐름을 결정한다.

### Step 2.1: Project type 분류

```
objective를 읽고 다음 중 해당하는 유형을 판단:

A. Multi-model combination
   — "여러 모델을 합쳐서", "ensemble", "fusion"
   — 기존 모델 여러 개를 조합해서 성능을 높이는 것이 핵심
   → 모델 여러 개 탐색 + 조합 방법론 탐색

B. Single-model improvement
   — "이 모델의 성능을 높이고 싶어", "Diffusion model로 X를 잘하고 싶어"
   — 하나의 모델/아키텍처를 개선하는 것이 핵심
   → 베이스 모델 1개 + 개선 기법 탐색 (loss, layer, feature, embedding, augmentation 등)

C. New method development
   — "새로운 방법으로 X를 풀고 싶어", "기존 방법들의 한계를 넘고 싶어"
   — 기존 SOTA를 분석하고 새로운 접근법을 설계
   → SOTA 모델 분석 + 한계점 기반 새 방법론 설계

D. Task adaptation
   — "X 모델을 Y task에 적용하고 싶어", "domain adaptation"
   — 기존 모델을 새로운 도메인/task에 맞추는 것이 핵심
   → 소스 모델 + adaptation 기법 탐색

E. Data-centric
   — "데이터가 적어", "few-shot", "self-supervised", "augmentation"
   — 제한된 데이터로 최대 성능을 뽑는 것이 핵심
   → 모델 + 데이터 효율적 학습 기법 탐색

위 5개에 맞지 않으면, objective에 맞게 새로운 유형을 정의한다.
유형은 고정 목록이 아니라 가이드라인이다.
```

사용자에게 판단 결과를 보여주고 확인:
```
프로젝트 유형: {type}
근거: {왜 이 유형으로 판단했는지}
이 방향으로 진행할까요?
```

### Step 2.2: Project structure

판단된 유형에 따라 디렉토리 구조를 생성:
```
{project}/
├── CLAUDE.md
├── configs/base.yaml
├── data/                  # immutable inputs
├── models/                # cloned repos + checkpoints
├── results/runs/          # per-iteration results
├── src/                   # 구조는 유형에 따라 다름 (아래 참고)
├── scripts/               # pipeline scripts
├── docs/                  # eval_policy, baselines, improvement_log
└── tests/
```

`src/` 하위 구조는 프로젝트 유형에 맞게 동적으로 결정:
```
# Type A (multi-model): src/models/, src/fusion/, src/evaluation/
# Type B (single-model): src/model/, src/modifications/, src/evaluation/
# Type C (new method): src/baselines/, src/proposed/, src/evaluation/
# Type D (adaptation): src/source_model/, src/adaptation/, src/evaluation/
# Type E (data-centric): src/model/, src/data_strategy/, src/evaluation/
# 기타: objective에 맞게 자유롭게 결정
```

conda 환경 생성:
```bash
conda create -n {project_name} python=3.10 pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
```

---

## Phase 3: Research (researcher agent, parallel tracks)

프로젝트 유형에 따라 연구 전략이 완전히 달라진다.
**두 track을 병렬로 수행한다.**

### Track A: 기반 모델/코드 탐색

프로젝트 유형별로 찾는 것이 다르다:

**Type A (multi-model):**
- Objective를 sub-task로 분해
- 각 sub-task를 커버하는 모델 후보를 찾되 **상호보완적** 조합 선택
- 모델 3~6개

**Type B (single-model):**
- 해당 task의 SOTA 또는 base 모델 1개를 찾음
- 그 모델의 강점/약점/한계를 논문에서 분석
- 같은 task에서 다른 접근법을 쓰는 모델도 1-2개 참고용으로 분석 (직접 쓰지 않더라도 아이디어 차용)

**Type C (new method):**
- 현재 SOTA 모델들을 2-3개 분석 (baseline 용도)
- 각 모델의 구조적 한계점을 파악

**Type D (adaptation):**
- 소스 모델 1개 확보
- 타겟 도메인에서 잘 되는 모델들을 참고 분석

**Type E (data-centric):**
- 해당 task의 모델 1개 확보
- 데이터 효율적 학습에 관한 모델/기법 탐색

**모든 유형 공통 — 모델 분석 템플릿:**
```
Model: {name}
Paper: {title} ({venue} {year})
GitHub: {url} (stars: {N}, last commit: {date})
Role in this project: base model / reference / baseline / component
Strengths: {이 task에서 잘하는 것}
Weaknesses: {한계점 — 이것이 개선 방향의 단서}
Checkpoint: available / needs training / needs fine-tuning
```

### Track B: 개선 방향 탐색

**이것이 프로젝트의 핵심이다.** 프로젝트 유형에 따라 찾는 것이 완전히 다르다.

**Type A (multi-model):**
- 조합 방법론: fusion, ensemble, stacking, etc.
- 초기 baseline 1개 선정

**Type B (single-model):**
- 해당 모델의 약점을 개선할 수 있는 기법 논문 탐색. 예시:
  - Loss function 변경/추가 (contrastive loss, focal loss, etc.)
  - Architecture 수정 (attention 추가, layer 변경, skip connection, etc.)
  - Feature extraction 개선 (다른 backbone, multi-scale, etc.)
  - Embedding 변경 (positional encoding, learned embedding, etc.)
  - Training strategy (curriculum learning, mixup, etc.)
  - Regularization (dropout, weight decay, etc.)
- **어떤 기법이 필요한지는 모델의 약점에 따라 결정** — 위 예시는 가능한 방향일 뿐
- 초기 baseline: 모델 원본 그대로 (개선 전 성능 측정)

**Type C (new method):**
- 기존 SOTA들의 공통 한계를 해결하는 방향 탐색
- 다른 도메인에서 비슷한 문제를 해결한 기법 탐색
- 초기 baseline: 기존 SOTA 재현

**Type D (adaptation):**
- Domain adaptation 기법: fine-tuning, adapter, prompt tuning, etc.
- 초기 baseline: 소스 모델 zero-shot 성능

**Type E (data-centric):**
- Few-shot learning, data augmentation, self-supervised pretraining, etc.
- 초기 baseline: 제한된 데이터로 vanilla training

**모든 유형 공통 — 개선 방향 분석 템플릿:**
```
Improvement: {name}
Paper: {title} ({venue} {year})
What it changes: {loss / architecture / feature / training / data / ...}
Why applicable: {우리 모델/task의 어떤 약점을 해결하는지}
Implementation complexity: low / medium / high
Expected impact: {근거와 함께}
Risk: {실패할 수 있는 이유}
```

모든 후보를 `docs/baselines.md`에 기록. 초기 baseline 1개만 선정, 나머지는 loop에서 순차 적용.

사용자에게 연구 결과 보고:
```
## Research Summary

### Base: {모델/코드 무엇을 쓰는지}
### Improvement candidates (priority order):
1. {기법} — {왜 이게 첫 번째인지}
2. {기법} — ...
3. ...

이 방향으로 진행할까요?
```

---

## Phase 4: Setup

사용자가 연구 결과를 확인하면:

**Step 4.1: Clone repos**
```bash
git clone {repo_url} models/{model_name}
```

**Step 4.2: Checkpoint download**
- HuggingFace: `huggingface_hub.hf_hub_download()`
- Google Drive: `gdown`
- Direct URL: `wget`
- 자동화 불가능 (Baidu Pan 등): `DOWNLOAD_MANUAL.md` 작성

**Step 4.3: Usage mode 판단**
```
if checkpoint이 target dataset과 같은 도메인:
    → pretrained 그대로 사용
elif checkpoint이 있지만 도메인이 다름:
    → fine-tune (training code 있으면)
    → 없으면 pretrained 그대로 + 성능 저하 가능성 기록
elif checkpoint 없음:
    → train from scratch (training code 필요)
    → training code 없으면 사용자에게 보고
```

**Step 4.4: Register in `models/model_registry.json`**

---

## Phase 5: Evaluation framework (researcher agent)

"Objective: '{objective}'.
Project type: {type}.
Models: {from model_registry.json}.
Design evaluation metrics.
Include sanity checks from .claude/skills/result-analyzer/sanity_checks.md.
Pay special attention to dataset class balance."

Output: `docs/eval_policy.md`

---

## Phase 6: Implement (engineer agent)

"Objective: '{objective}'.
Project type: {type}.
Models: see model_registry.json.
Baseline: {from Track B}.
Evaluation: see docs/eval_policy.md.

Implement the pipeline. What needs to be implemented depends entirely on the project type:

- Type A: model wrappers → score extraction → combination method → evaluation
- Type B: model wrapper → baseline evaluation → modification code → evaluation
- Type C: baseline reproduction → proposed method → evaluation
- Type D: source model wrapper → adaptation code → evaluation
- Type E: model wrapper → data strategy → training → evaluation

Design the scripts/ and src/ structure to match. Each script independently runnable.
Implement scripts/run_all.sh and scripts/improve_loop.py.
Tests must pass."

---

## Phase 7: Run baseline (runner agent)

"Run the full pipeline. Save results to results/runs/."

---

## Phase 7.5: Safety gate — DO NOT SKIP

Verify:
1. `pytest -q` passes
2. docs/eval_policy.md has confirmed primary metric
3. At least 1 completed evaluation in results/
4. models/model_registry.json has at least 1 model with status "ready"
5. Sanity checks pass on baseline results

If any fails → fix before proceeding.

---

## Phase 8: Autonomous improvement loop

**핵심: 매 iteration마다 논문을 찾고, 그 논문의 기법을 적용한다.**
무엇을 바꿀지는 이전 결과의 분석에서 나온다.

Loop:
1. **result-analyzer**: 결과 분석 + sanity checks → 현재 약점/bottleneck 파악
2. **literature-scout**: 약점을 해결하는 논문 검색
   - 프로젝트 유형에 따라 찾는 논문이 다름:
     - Type A: 더 나은 조합 방법
     - Type B: 모델의 현재 약점을 해결하는 기법 (loss, layer, feature, embedding, training 등 뭐든)
     - Type C: 제안 방법의 약점을 보완하는 기법
     - Type D: 더 나은 adaptation 기법
     - Type E: 더 나은 data strategy
   - **무엇을 찾을지를 미리 정하지 않는다.** 결과 분석에서 나온 약점이 검색 쿼리를 결정한다.
3. **method-reviser**: 논문의 기법을 구현 (한 번에 하나씩)
4. **experiment-runner**: 실행
5. **result-analyzer**: 비교, 다음 방향 결정
6. Repeat

#### Phase A cycle (faithful reproduction)
새 기법을 적용하기 전, 해당 논문의 방법을 먼저 원본대로 재현:
1. 논문대로 구현
2. 실행
3. 논문의 보고 수치와 비교 (within 5%)
   - 재현 실패 → 엔지니어링 이슈 해결
   - 재현 성공 → gap analysis: 이 기법이 구조적으로 못하는 건 뭔가?

#### Phase B cycle (적용 & 개선)
1. 재현된 기법을 우리 프로젝트에 적용
2. 실행 & 비교
   - 개선됨 → 새 baseline으로 채택, 다음 약점 분석
   - 악화됨 → revert, 다음 후보 시도
3. 반복

**Escalation triggers:**
- stall_count >= 2: 2+ loops 개선 없음
- Same error 3+ times
- Sanity check flag 3+ consecutive
- pytest fails → 즉시 중단

---

## Notes
- **프로젝트 유형이 모든 것을 결정한다** — 같은 skill이지만 유형에 따라 완전히 다른 연구를 수행
- improvement loop에서 무엇을 바꿀지는 미리 정하지 않음 — 결과 분석 + 논문 검색의 결과로 동적 결정
- loss를 바꿀 수도, layer를 추가할 수도, feature를 바꿀 수도, 완전히 다른 접근법을 쓸 수도 있음
- 한 번에 하나의 변경만 적용 (ablation 가능하도록)
- pretrain checkpoint 있으면 우선 사용
- 데이터셋 불균형은 eval framework에서 선제 대응
