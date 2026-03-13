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

Already cloned? Pull the latest:
```bash
cd ~/claude-research-system && git pull
```

This writes agents/skills/hooks only into `your-project/.claude/` — other projects and `~/.claude/` are not touched.

---

## Start a new project

```bash
cd /path/to/your/project
claude
```

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
# continuous mode — runs forever in background (survives terminal close)
python orchestrator/scheduler.py --project ~/projects/my-project --mode continuous

# check status / stop
python orchestrator/scheduler.py --project ~/projects/my-project --status
python orchestrator/scheduler.py --project ~/projects/my-project --stop

# foreground (see output directly)
python orchestrator/scheduler.py --project ~/projects/my-project --mode continuous --foreground

# one-shot analysis
python orchestrator/main.py --project ~/projects/my-project --mode analyze-only

# nightly loop
python orchestrator/main.py --project ~/projects/my-project --mode nightly
```

Key behaviors:
- **Background daemon**: terminal을 꺼도 계속 실행됨
- **Skip completed**: 이미 완료된 method는 자동 스킵 (`--no-skip-completed`로 비활성화)
- **No prompts**: 중간에 질문하지 않고 자동 진행
- **Top N visualization**: 시각화에서 상위 N개만 표시 (기본 10)
- **Auto-escalation**: 개선 없으면 자동으로 literature search 트리거

---

## Structure

```
claude-research-system/
├── .claude-plugin/
│   └── plugin.json              ← Claude Code plugin manifest
├── install.sh                   ← API key setup + pip install
├── agents/
│   ├── researcher.md            ← paper search, eval framework design
│   ├── engineer.md              ← code implementation
│   ├── runner.md                ← experiment execution
│   ├── reviewer.md              ← result validation
│   ├── policy_guard.md         ← policy review (protects immutable core)
│   └── environment_manager.md  ← conda, dependency, GPU management
├── skills/
│   ├── bootstrap-project/       ← new project initialization
│   ├── literature-scout/        ← paper search (Semantic Scholar, arXiv, OpenAlex)
│   ├── experiment-runner/       ← run experiments + save results
│   ├── result-analyzer/         ← failure classification + code-level deep analysis
│   ├── method-reviser/          ← evidence-based code changes
│   ├── policy-evolver/          ← incremental eval policy updates
│   ├── data-auditor/            ← dataset quality/distribution analysis
│   ├── ablation-planner/        ← component contribution verification
│   ├── report-writer/           ← experiment report generation
│   └── system-updater/          ← auto-check Claude Code updates
├── hooks/
│   └── hooks.json               ← PreToolUse / PostToolUse / Stop hooks
├── orchestrator/
│   ├── new_project.py           ← project scaffold CLI
│   ├── main.py                  ← autonomous loop orchestrator
│   └── scheduler.py             ← periodic execution scheduler
└── templates/
    └── project-skeleton/        ← minimal project structure
        └── scripts/
            ├── run_experiment.py       ← experiment execution + debug logging
            ├── analyze_failures.py    ← failure pattern detection
            ├── summarize_results.py   ← results summary report
            ├── propose_next_steps.py  ← next action proposals
            ├── validate_config.py     ← config validation
            ├── save_session_state.py  ← session state persistence (hooks)
            ├── visualize_results.py   ← cross-run visualization
            ├── debug_logger.py        ← structured debug logging
            └── generate_decision_report.py ← decision documentation
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
