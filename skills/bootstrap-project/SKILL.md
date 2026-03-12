# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
사용자의 objective를 받아서, 모델 탐색 → 방법론 탐색 → 구현 → 실험 → 개선 루프까지
자동으로 수행하는 연구 프로젝트를 만든다.

---

## Phase 1: Collect info

사용자에게 질문:
1. **Objective** — 한 문장 (예: "multimodal deepfake detection에서 FakeAVCeleb SOTA 달성", "medical image segmentation에서 few-shot 성능 향상")
2. **Train dataset** — 학습에 쓸 데이터 경로 또는 이름
3. **Test dataset** — 평가에 쓸 데이터 경로 또는 이름 (train과 같을 수 있음)
4. **GPU** — 사용 가능한 GPU (예: 0 / 0,1 / all / cpu)

질문하지 않는 것:
- 어떤 모델을 쓸지 (자동 탐색)
- 어떤 metric을 쓸지 (논문 기반 자동 결정)
- 어떤 방법론을 쓸지 (objective 분석 후 자동 결정)

---

## Phase 2: Project structure

Create:
```
{project}/
├── CLAUDE.md
├── configs/base.yaml
├── data/                  # immutable inputs: scores, extracted features, raw data
├── models/                # cloned repos + checkpoints
├── results/runs/          # per-iteration results (growing output)
├── src/models/            # model wrappers
├── src/methods/           # approach implementations (determined by objective)
├── src/evaluation/        # metrics
├── scripts/               # pipeline scripts
├── docs/                  # eval_policy, baselines
└── tests/
```

conda 환경 생성:
```bash
conda create -n {project_name} python=3.10 pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
```

---

## Phase 3: Parallel search — models AND approach

**이 두 가지를 동시에 수행한다.** 순서가 아니라 병렬이다.

### Track A: Model search (researcher agent)

목표: objective에 적합한 개별 모델 후보를 찾되, **각 모델이 task의 어떤 측면을 잘하는지** 분석.

**Step A.1: Task 분해**

Objective를 sub-task로 분해한다. 예시:
```
# Example 1: multimodal deepfake detection
Task decomposition:
- Visual forgery detection (face swap, reenactment)
- Audio forgery detection (voice conversion, TTS)
- Audio-visual synchronization (lip-sync consistency)
- Cross-modal identity verification

# Example 2: medical image segmentation
Task decomposition:
- Organ boundary delineation
- Small lesion detection
- Multi-scale feature extraction
- Domain generalization across scanners
```

각 sub-task별로 어떤 모델이 강한지를 찾는다.

**Step A.2: Search per sub-task**

각 sub-task에 대해 검색:
1. Semantic Scholar — title + abstract에서 해당 sub-task 언급 확인
2. arXiv MCP — 최근 관련 논문
3. GitHub — `gh search repos "{sub_task}" --sort=stars --limit=10`
4. Brave Search MCP — 추가 검색

**Step A.3: Per-model analysis**

각 후보 모델에 대해 반드시 분석:
```
Model: {name}
Paper: {title} ({venue} {year})
GitHub: {url} (stars: {N}, last commit: {date})

Sub-task coverage:
- {sub-task 1}: ✓/✗ (어떤 방식으로 해결하는지)
- {sub-task 2}: ✓/✗
- ...

Strengths:
- {이 모델이 잘하는 specific sub-task와 이유}

Weaknesses:
- {이 모델이 못하는 sub-task와 이유}

Checkpoint:
- Available: ✓/✗
- Source: HuggingFace / GDrive / direct / needs training
- Size: {GB}
- Trained on: {dataset}
- Compatible with target dataset: ✓/✗ (왜?)

Complementarity:
- {이 모델이 다른 후보들과 어떻게 상호보완되는지}
```

**Step A.4: Complementary selection**

핵심: **성능 좋은 모델 N개가 아니라, sub-task를 골고루 커버하는 조합**을 고른다.

선택 기준 (우선순위):
1. **Sub-task coverage** — 모든 sub-task가 최소 1개 모델로 커버되는가
2. **Diversity** — 같은 접근법의 모델 2개보다, 다른 접근법 모델 2개가 낫다
3. **Checkpoint availability** — pretrained 있으면 우선
4. **Venue + recency** — 탑티어 + 최신
5. **모델 수 제한** — objective에 따라 유동적 (단일 모델 개선이면 1-2개, 조합이 필요하면 3-6개)

사용자에게 제안:
```
## Selected Models (complementary set)

| # | Model | Covers | Strength | Weakness (covered by) | Checkpoint |
|---|-------|--------|----------|----------------------|------------|
| 1 | ... | ... | ... | ... | ... |

이 조합으로 진행할까요? 추가/제거할 모델이 있으면 알려주세요.
```

### Track B: Approach search (researcher agent, parallel)

목표: objective를 달성하기 위한 **방법론/접근법**을 탐색. 어떤 종류의 approach가 필요한지는 objective에 따라 동적으로 결정.

**Step B.1: Approach type 결정**

Objective를 분석해서 어떤 종류의 approach가 필요한지 판단:
```
# 판단 기준 (예시):
- 여러 모델의 출력을 합쳐야 하는가? → fusion/ensemble 방법론 탐색
- 단일 모델을 개선해야 하는가? → training strategy, augmentation, architecture 개선 탐색
- 새로운 task를 정의해야 하는가? → task formulation, loss function 탐색
- 도메인 적응이 필요한가? → domain adaptation, transfer learning 탐색
- 데이터가 부족한가? → few-shot, self-supervised, data augmentation 탐색
- ...
```

approach type은 고정이 아니다 — objective에 맞게 유연하게 결정.

**Step B.2: Search relevant methods**

결정된 approach type에 맞춰 검색:
1. Semantic Scholar — "{task} {approach_type}" 관련 논문
2. arXiv MCP — 최근 관련 방법론
3. Papers with Code — target dataset의 SOTA methods

**Step B.3: Per-method analysis**

각 방법론에 대해:
```
Method: {name}
Paper: {title} ({venue} {year})
Approach type: {determined from B.1}
Input requirement: {이 방법이 필요로 하는 것}
Handles imbalance: ✓/✗
Strengths: {이 task에 왜 좋은지}
Weaknesses: {한계}
Applicability: {Track A의 모델들과 어떻게 결합되는지}
```

**초기 baseline으로 쓸 방법 1개**만 정한다. 나머지는 docs/baselines.md에 기록해두고 loop에서 사용.

---

## Phase 4: Download and setup models

사용자가 모델 선택을 확인하면:

**Step 4.1: Clone**
```bash
git clone {repo_url} models/{model_name}
```

**Step 4.2: Checkpoint download**

README.md를 읽고 체크포인트를 다운받는다:
- HuggingFace: `huggingface_hub.hf_hub_download()`
- Google Drive: `gdown`
- Direct URL: `wget`
- 자동화 불가능 (Baidu Pan 등): `DOWNLOAD_MANUAL.md` 작성

**Step 4.3: Pretrain vs use checkpoint 판단**

각 모델에 대해:
```
if checkpoint이 target dataset과 같은 도메인에서 학습됨:
    → pretrained checkpoint 그대로 사용 (inference only)
elif checkpoint이 있지만 도메인이 다름:
    → fine-tune on train dataset (if training code available)
    → 없으면 pretrained 그대로 쓰되, 성능 저하 가능성 기록
elif checkpoint 없음:
    → train from scratch on train dataset (training code 필요)
    → training code 없으면 사용자에게 보고하고 해당 모델 제외
```

**Step 4.4: Register**

`models/model_registry.json`:
```json
{
  "models": [
    {
      "name": "model_a",
      "paper": "Paper Title...",
      "venue": "CVPR 2024",
      "repo": "https://github.com/...",
      "local_path": "models/model_a",
      "checkpoint_path": "models/model_a/checkpoints/best.pth",
      "checkpoint_source": "huggingface",
      "checkpoint_trained_on": "dataset_name",
      "usage_mode": "inference|finetune|train_from_scratch",
      "covers_subtasks": ["subtask_1", "subtask_2"],
      "strengths": "...",
      "weaknesses": "...",
      "framework": "pytorch",
      "status": "ready"
    }
  ]
}
```

---

## Phase 5: Evaluation framework (researcher agent)

Hand off to researcher agent:

"Objective: '{objective}'.
Models: {from model_registry.json — include each model's strengths/weaknesses}.
Baseline approach: {from Track B}.
Design evaluation metrics.
Include sanity checks from .claude/skills/result-analyzer/sanity_checks.md.
Pay special attention to dataset class balance — if imbalanced, primary metric
must NOT be naive accuracy or overall AUC alone."

Output: docs/eval_policy.md

---

## Phase 6: Implement (engineer agent)

Hand off to engineer agent:

"Objective: '{objective}'.
Models are in models/ (see model_registry.json).
Baseline approach: {from Track B — include paper reference and method details}.
Evaluation: see docs/eval_policy.md.

Implement:
1. For each model, implement src/models/{name}_wrapper.py:
   - load(checkpoint_path) → model
   - predict(model, input) → output (score, feature, etc. depending on approach)
   - Read the model's README and inference code to understand the API
2. Implement the pipeline scripts in scripts/:
   - What scripts are needed depends on the approach. Design the pipeline based on:
     - The objective
     - The baseline approach from Track B
     - The models and their outputs
   - Common patterns (adapt as needed):
     - extract outputs → process → apply method → evaluate
   - Each script should be independently runnable
3. Implement src/methods/{baseline_method}.py — baseline approach from Track B
4. Implement src/evaluation/metrics.py — include balanced scoring from eval_policy.md
5. Implement scripts/run_all.sh — full pipeline from data to results
6. Implement scripts/improve_loop.py — iterative improvement
Tests must pass."

---

## Phase 7: Run baseline (runner agent)

Hand off to runner agent:
"Run the full pipeline via scripts/run_all.sh.
Save results to results/runs/."

---

## Phase 7.5: Safety gate — DO NOT SKIP

Verify:
1. `pytest -q` passes
2. docs/eval_policy.md has confirmed primary metric
3. At least 1 completed evaluation in results/
4. models/model_registry.json has at least 1 model with status "ready"
5. Sanity checks from result-analyzer pass on baseline results

If any fails → fix before proceeding.

---

## Phase 8: Autonomous improvement loop

Loop:
1. result-analyzer: analyze results (with sanity checks)
2. literature-scout: search for better methods/approaches
3. method-reviser: implement next method
4. experiment-runner: evaluate
5. result-analyzer: compare, decide next direction
6. Repeat

The loop follows a two-phase structure per method: **reproduce first, then improve.**

#### Phase A cycle (faithful reproduction)
1. method-reviser: implement the paper exactly as described — no modifications yet
2. experiment-runner: run
3. result-analyzer: check if paper's reported metric is reproduced (within 5%)
   - If reproduction failed → diagnose and fix
   - If reproduced → gap analysis: what does this method structurally NOT solve?

#### Phase B cycle (improvement)
1. result-analyzer: identify gaps
2. literature-scout: search for papers that address those gaps + propose synthesis
3. method-reviser: implement the highest-ranked proposal (one modification at a time)
4. experiment-runner: run
5. result-analyzer: compare Phase B vs Phase A
   - If better → make Phase B the new baseline, search for next gap
   - If worse → revert, try next proposal
6. repeat until stall or user interrupts

**Escalation triggers:**
- stall_count >= 2: no improvement in 2+ loops
- Same error 3+ times with identical stack trace
- Sanity check flag fires 3+ consecutive times
- pytest fails after code change → halt immediately

---

## Notes
- 모델은 성능순이 아니라 **상호보완성**으로 선택
- approach/방법론은 objective에 따라 동적으로 결정 (fusion, training strategy, architecture 등)
- baseline 1개로 시작, loop에서 확장
- pretrain checkpoint 있으면 우선 사용, 없으면 학습
- 데이터셋 불균형 문제는 eval framework에서 선제적으로 대응
- `src/methods/`에는 objective에 맞는 방법론 구현 (fusion이든, augmentation이든, loss function이든)
