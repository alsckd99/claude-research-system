# Skill: bootstrap-project

## Trigger
- "새 프로젝트 만들어줘", "프로젝트 시작해줘"
- project directory is empty

## Purpose
Create a minimal research-os project structure at the given path.
Metrics are not decided by the user — the researcher agent reads papers and decides.

## Steps

### Phase 0: Create conda environment
```bash
conda env create -f environment.yml
```
All subsequent python, pytest, and make commands go through `conda run -n {project_name}`.

### Phase 1: Create project structure
Collect: project name, objective (one sentence), constraints (GPU memory, latency).
Do not ask about metrics — researcher decides later.

Create:
- docs/, configs/, experiments/runs/, experiments/reports/, src/, tests/, scripts/
- CLAUDE.md with Primary Metric set to TBD
- docs/eval_policy.md as empty template
- docs/baselines.md, experiments/registry.json
- src/ skeleton, tests/test_smoke.py, Makefile

### Phase 2: Design evaluation framework (delegate to researcher)
Immediately after structure is created, hand off to researcher agent:

"This project's objective is '{objective}'.
Search for relevant papers and design the standard evaluation metric framework for this task.
Write docs/eval_policy.md with one primary metric and secondary metrics, each backed by paper citations."

### Phase 3: Apply evaluation framework
After researcher finishes:
- fill in TBD fields in CLAUDE.md with confirmed metrics
- update evaluation section in configs/base.yaml
- write next_actions.md: "next step: implement baseline"

## Notes
- each project gets its own conda environment named after the project
- metrics are not fixed upfront — researcher reads papers and decides
- no metric selection without literature evidence
- policy_guard reviews eval_policy.md before it takes effect

## Output
- standard project directory structure
- docs/eval_policy.md with literature-backed evaluation setup
- CLAUDE.md with confirmed metrics
- experiments/reports/next_actions.md
