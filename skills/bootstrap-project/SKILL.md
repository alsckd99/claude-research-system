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
Collect:
- project name
- objective (one sentence describing what you want to achieve)
- which GPU(s) to use — ask the user: "Which GPU(s) should experiments run on? (e.g. 0 / 0,1 / 0,1,2 / all / cpu)"

Do not ask about metrics — researcher decides metrics from papers.

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

### Phase 4: Implement baseline (delegate to engineer)
Hand off to engineer agent:

"The evaluation framework is ready. Implement a minimal but runnable baseline for this project.
Objective: {objective}
Primary metric: {metric from eval_policy.md}
Follow the coding rules in CLAUDE.md. Tests must pass before handing off to runner."

### Phase 5: Run baseline experiment (delegate to runner)
After engineer finishes and tests pass:

Hand off to runner agent:
"Run the baseline experiment and save results."

### Phase 6: Start autonomous loop
After the first experiment completes, immediately begin the loop without waiting for user input:

1. result-analyzer: analyze the baseline results, write error_analysis.md
2. literature-scout: search for improvement methods based on failure patterns
3. method-reviser: propose and implement the most promising change
4. experiment-runner: run the updated experiment
5. repeat from step 1

Stop condition: loop continues until the user interrupts or `--no-improve-k` is reached.

## Notes
- each project gets its own conda environment named after the project
- metrics are not fixed upfront — researcher reads papers and decides
- no metric selection without literature evidence
- policy_guard reviews eval_policy.md before it takes effect
- the loop starts automatically after the first experiment — no user prompt needed

## Output
- standard project directory structure
- docs/eval_policy.md with literature-backed evaluation setup
- CLAUDE.md with confirmed metrics
- baseline implemented and first experiment run
- autonomous improvement loop running
