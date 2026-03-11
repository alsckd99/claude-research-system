# claude-research-system

Autonomous ML R&D loop as a Claude Code plugin.
Literature search, experiment running, failure analysis, and policy evolution — all automated.

---

## Install

Clone once, then run for each project you want to use it on:

```bash
git clone https://github.com/alsckd99/claude-research-system ~/claude-research-system
bash ~/claude-research-system/install.sh /path/to/your/project
```

This writes agents/skills/hooks only into `your-project/.claude/` — other projects and `~/.claude/` are not touched.

---

## Start a new project

Inside Claude Code:
```
create a new project — name: my-project, objective: [describe what you want to achieve]
```

Or via CLI:
```bash
python orchestrator/new_project.py \
    --name my-project \
    --objective "describe what you want to achieve" \
    --output ~/projects/my-project
```

Metrics are not set here. The researcher agent reads related papers and determines
the standard evaluation metrics for your task domain.

---

## Run the autonomous loop

```bash
# one-shot analysis
python orchestrator/main.py --project ~/projects/my-project --mode analyze-only

# nightly loop (analyze → experiment → literature → policy)
python orchestrator/main.py --project ~/projects/my-project --mode nightly

# background scheduler
nohup python orchestrator/scheduler.py \
    --project ~/projects/my-project \
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

| Source | MCP | What it covers |
|--------|-----|---------------|
| arXiv | arxiv-mcp-server (dedicated) | search, download, full-text read — papers cached locally |
| Semantic Scholar | fetch MCP (HTTP) | titles, abstracts, citation counts |
| OpenAlex | fetch MCP (HTTP) | open-access metadata, supplementary |
| Brave Search | brave-search MCP (optional) | benchmark leaderboards, GitHub repos, official docs |

arXiv uses a dedicated MCP (`blazickjp/arxiv-mcp-server`) with structured tool calls instead of raw HTTP — more token-efficient and papers are cached at `~/.arxiv-mcp-server/papers`.

---

## References

Design and tooling informed by:

- [blazickjp/arxiv-mcp-server](https://github.com/blazickjp/arxiv-mcp-server) — arXiv MCP used for literature-scout
- [ralph-wiggum plugin](https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum) — Stop hook loop pattern reference
- [feature-dev plugin](https://github.com/anthropics/claude-code/tree/main/plugins/feature-dev) — multi-agent workflow structure reference
- [Claude Code Plugins reference](https://code.claude.com/docs/en/plugins-reference.md) — plugin manifest format
- [Awesome Claude Code](https://github.com/anthropics/awesome-claude-code)
- [Claude Code Docs](https://docs.anthropic.com/claude-code)
