# claude-research-system

Autonomous ML R&D loop as a Claude Code plugin.
Literature search, experiment running, failure analysis, and policy evolution — all automated.

---

## Install

```bash
claude plugin install https://github.com/alsckd99/claude-research-system
bash install.sh   # API keys + pip packages (one-time)
```

---

## Start a new project

Inside Claude Code:
```
create project deepfake-detector — objective: multimodal deepfake detection, GPU 24GB limit
```

Or via CLI:
```bash
python orchestrator/new_project.py \
    --name deepfake-detector \
    --objective "multimodal deepfake detection" \
    --gpu-memory 24 \
    --output ~/projects/deepfake-detector
```

---

## Run the autonomous loop

```bash
# one-shot analysis
python orchestrator/main.py --project ~/projects/deepfake-detector --mode analyze-only

# nightly loop (analyze → experiment → literature → policy)
python orchestrator/main.py --project ~/projects/deepfake-detector --mode nightly

# background scheduler
nohup python orchestrator/scheduler.py \
    --project ~/projects/deepfake-detector \
    --interval 24h --mode full-loop &
```

Stop condition: `--no-improve-k 3` halts the loop if no metric improvement over the last 3 runs.

---

## Structure

```
claude-research-system/
├── plugin.json                  ← Claude Code plugin manifest
├── install.sh                   ← API key setup + pip install
├── agents/
│   ├── researcher.md            ← paper search, eval framework design
│   ├── engineer.md              ← code implementation
│   ├── runner.md                ← experiment execution
│   ├── reviewer.md              ← result validation
│   └── policy_guard.md         ← policy review (protects immutable core)
├── skills/
│   ├── bootstrap-project/       ← new project initialization
│   ├── literature-scout/        ← paper search (Semantic Scholar, arXiv, OpenAlex)
│   ├── experiment-runner/       ← run experiments + save results
│   ├── result-analyzer/         ← failure classification + root cause analysis
│   ├── method-reviser/          ← evidence-based code changes
│   └── policy-evolver/          ← incremental eval policy updates
├── hooks/
│   └── hooks.json               ← PreToolUse / PostToolUse / Stop hooks
├── orchestrator/
│   ├── new_project.py           ← project scaffold CLI
│   ├── main.py                  ← autonomous loop orchestrator
│   └── scheduler.py             ← periodic execution scheduler
└── templates/
    └── project-skeleton/        ← minimal project structure
```

---

## Paper search coverage

| Source | What it covers |
|--------|---------------|
| Semantic Scholar API | titles, abstracts, citation counts |
| arXiv API | preprints, full metadata |
| OpenAlex API | open-access metadata, supplementary |
| Brave Search MCP | benchmark leaderboards, GitHub repos, official docs (optional) |

PDF full text (including figures and tables) is extracted via `fetch_paper.py` using PyMuPDF.

---

## References

- [Awesome Claude Code](https://github.com/anthropics/awesome-claude-code)
- [Claude Code Docs](https://docs.anthropic.com/claude-code)
