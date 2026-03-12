#!/usr/bin/env bash
# claude-research-system: project-scoped install
# Usage: bash install.sh /path/to/your/project
#
# Copies agents/skills/hooks into that project's .claude/ only.
# Nothing is written to ~/.claude/ — other projects are not affected.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${1:-}"

if [ -z "${PROJECT_DIR}" ]; then
  echo "Usage: bash install.sh /path/to/your/project"
  echo ""
  echo "Example:"
  echo "  bash install.sh ~/projects/my-research"
  exit 1
fi

PROJECT_DIR="$(mkdir -p "${PROJECT_DIR}" && cd "${PROJECT_DIR}" && pwd)"
CLAUDE_DIR="${PROJECT_DIR}/.claude"

echo ""
echo "claude-research-system install"
echo "project: ${PROJECT_DIR}"
echo ""

# ──────────────────────────────────────────
# 1. Anthropic API Key
# ──────────────────────────────────────────
echo "[1/3] Anthropic API Key"
echo "  Only needed for background automation (orchestrator/main.py running without Claude Code)."
echo "  If you are using Claude Code directly, skip this — Claude Code is already connected."

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "already set"
else
  echo ""
  read -rp "Anthropic API Key (sk-ant-..., Enter to skip): " ANTHROPIC_API_KEY
  if [ -n "${ANTHROPIC_API_KEY}" ]; then
    echo "export ANTHROPIC_API_KEY=\"${ANTHROPIC_API_KEY}\"" >> ~/.bashrc
    export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
    echo "saved to ~/.bashrc"
  else
    echo "skipped"
  fi
fi

# ──────────────────────────────────────────
# 2. GitHub Token (optional)
# ──────────────────────────────────────────
echo ""
echo "[2/3] GitHub Token (optional — for PR/issue management)"
echo "  github.com -> Settings -> Developer settings -> Personal access tokens"
echo "  -> Tokens (classic)  [use classic, not fine-grained]"
echo "  -> Generate new token (classic) -> check 'repo' -> copy ghp_..."

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "already set"
else
  echo ""
  read -rp "GitHub Token (ghp_..., Enter to skip): " GITHUB_TOKEN
  if [ -n "${GITHUB_TOKEN}" ]; then
    echo "export GITHUB_TOKEN=\"${GITHUB_TOKEN}\"" >> ~/.bashrc
    export GITHUB_TOKEN="${GITHUB_TOKEN}"
    echo "saved to ~/.bashrc"
  else
    echo "skipped"
  fi
fi

# ──────────────────────────────────────────
# 3. Brave Search API Key (optional)
# ──────────────────────────────────────────
echo ""
echo "[3/3] Brave Search API Key (optional — for web/leaderboard search)"
echo "  brave.com/search/api -> Search -> Get started"
echo "  Free tier: 1,000 requests/month at no cost."
echo "  Paper search works without this — Semantic Scholar + arXiv are always available."

if [ -n "${BRAVE_API_KEY:-}" ]; then
  echo "already set"
else
  echo ""
  read -rp "Brave Search API Key (Enter to skip): " BRAVE_API_KEY
  if [ -n "${BRAVE_API_KEY}" ]; then
    echo "export BRAVE_API_KEY=\"${BRAVE_API_KEY}\"" >> ~/.bashrc
    export BRAVE_API_KEY="${BRAVE_API_KEY}"
    echo "saved to ~/.bashrc"
  else
    echo "skipped"
  fi
fi

# ──────────────────────────────────────────
# 4. Copy plugin files into project .claude/
# ──────────────────────────────────────────
echo ""
echo "copying files to ${CLAUDE_DIR} ..."

mkdir -p "${CLAUDE_DIR}/agents"
mkdir -p "${CLAUDE_DIR}/skills/bootstrap-project"
mkdir -p "${CLAUDE_DIR}/skills/literature-scout"
mkdir -p "${CLAUDE_DIR}/skills/experiment-runner"
mkdir -p "${CLAUDE_DIR}/skills/result-analyzer"
mkdir -p "${CLAUDE_DIR}/skills/method-reviser"
mkdir -p "${CLAUDE_DIR}/skills/policy-evolver"
mkdir -p "${CLAUDE_DIR}/skills/data-auditor"
mkdir -p "${CLAUDE_DIR}/skills/ablation-planner"
mkdir -p "${CLAUDE_DIR}/skills/report-writer"
mkdir -p "${CLAUDE_DIR}/skills/system-updater"
mkdir -p "${CLAUDE_DIR}/hooks"

cp "${SCRIPT_DIR}/agents/researcher.md"     "${CLAUDE_DIR}/agents/"
cp "${SCRIPT_DIR}/agents/engineer.md"       "${CLAUDE_DIR}/agents/"
cp "${SCRIPT_DIR}/agents/runner.md"         "${CLAUDE_DIR}/agents/"
cp "${SCRIPT_DIR}/agents/reviewer.md"       "${CLAUDE_DIR}/agents/"
cp "${SCRIPT_DIR}/agents/policy_guard.md"   "${CLAUDE_DIR}/agents/"
cp "${SCRIPT_DIR}/agents/environment_manager.md" "${CLAUDE_DIR}/agents/"

cp "${SCRIPT_DIR}/skills/bootstrap-project/SKILL.md"  "${CLAUDE_DIR}/skills/bootstrap-project/"
cp "${SCRIPT_DIR}/skills/literature-scout/SKILL.md"   "${CLAUDE_DIR}/skills/literature-scout/"
cp "${SCRIPT_DIR}/skills/experiment-runner/SKILL.md"  "${CLAUDE_DIR}/skills/experiment-runner/"
cp "${SCRIPT_DIR}/skills/result-analyzer/SKILL.md"    "${CLAUDE_DIR}/skills/result-analyzer/"
cp "${SCRIPT_DIR}/skills/result-analyzer/sanity_checks.md" "${CLAUDE_DIR}/skills/result-analyzer/"
cp "${SCRIPT_DIR}/skills/method-reviser/SKILL.md"     "${CLAUDE_DIR}/skills/method-reviser/"
cp "${SCRIPT_DIR}/skills/policy-evolver/SKILL.md"     "${CLAUDE_DIR}/skills/policy-evolver/"
cp "${SCRIPT_DIR}/skills/data-auditor/SKILL.md"      "${CLAUDE_DIR}/skills/data-auditor/"
cp "${SCRIPT_DIR}/skills/ablation-planner/SKILL.md"  "${CLAUDE_DIR}/skills/ablation-planner/"
cp "${SCRIPT_DIR}/skills/report-writer/SKILL.md"     "${CLAUDE_DIR}/skills/report-writer/"
cp "${SCRIPT_DIR}/skills/system-updater/SKILL.md"   "${CLAUDE_DIR}/skills/system-updater/"

cp "${SCRIPT_DIR}/hooks/hooks.json" "${CLAUDE_DIR}/hooks/"

# settings.json (permissions)
cat > "${CLAUDE_DIR}/settings.json" << 'SETTINGS_EOF'
{
  "permissions": {
    "allow": [
      "Bash(python*)", "Bash(pytest*)", "Bash(ruff*)", "Bash(black*)",
      "Bash(conda*)", "Bash(uv*)",
      "Bash(git add*)", "Bash(git commit*)", "Bash(git status)",
      "Bash(git diff*)", "Bash(git log*)", "Bash(git branch*)", "Bash(git pull)",
      "Bash(make*)", "Bash(mkdir*)", "Bash(cp*)", "Bash(mv*)", "Bash(jq*)"
    ],
    "deny": [
      "Bash(curl*)", "Bash(wget*)",
      "Bash(git push --force*)", "Bash(git reset --hard*)",
      "Bash(rm -rf*)", "Bash(git clean -f*)"
    ]
  }
}
SETTINGS_EOF

echo "done — files written to ${CLAUDE_DIR}"

# ──────────────────────────────────────────
# 5. MCP servers (project-scoped)
# ──────────────────────────────────────────
echo ""
echo "registering MCP servers (project-scoped)..."

if command -v claude &>/dev/null; then
  cd "${PROJECT_DIR}"

  claude mcp add --scope project arxiv -- uvx arxiv-mcp-server 2>/dev/null \
    && echo "arxiv MCP registered" || echo "arxiv MCP already registered"

  claude mcp add --scope project fetch -- npx -y @modelcontextprotocol/server-fetch 2>/dev/null \
    && echo "fetch MCP registered" || echo "fetch MCP already registered"

  if [ -n "${GITHUB_TOKEN:-}" ]; then
    GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_TOKEN}" \
    claude mcp add --scope project github -- npx -y @modelcontextprotocol/server-github 2>/dev/null \
      && echo "github MCP registered" || echo "github MCP already registered"
  fi

  if [ -n "${BRAVE_API_KEY:-}" ]; then
    claude mcp add --scope project brave-search \
      -e BRAVE_API_KEY="${BRAVE_API_KEY}" \
      -- npx -y @modelcontextprotocol/server-brave-search 2>/dev/null \
      && echo "brave-search MCP registered" || echo "brave-search MCP already registered"
  fi

  cd "${SCRIPT_DIR}"
else
  echo "claude CLI not found — skipping MCP registration"
fi

# ──────────────────────────────────────────
# 6. Python packages
# ──────────────────────────────────────────
echo ""
echo "installing Python packages..."
pip3 install -q anthropic pyyaml requests && echo "anthropic, pyyaml, requests OK"
pip3 install -q pymupdf && echo "pymupdf OK" || echo "pymupdf failed — PDF text extraction will be skipped"

if command -v uv &>/dev/null; then
  uv tool install arxiv-mcp-server && echo "arxiv-mcp-server OK" \
    || echo "arxiv-mcp-server failed — install manually: uv tool install arxiv-mcp-server"
else
  echo "uv not found — install uv, then: uv tool install arxiv-mcp-server"
fi

# ──────────────────────────────────────────
echo ""
echo "installed at ${CLAUDE_DIR}"
echo "other projects are not affected"
echo ""
echo "next: cd ${PROJECT_DIR} && claude"
echo ""
[ -z "${ANTHROPIC_API_KEY:-}" ] && echo "note: run 'source ~/.bashrc' to apply API key"
echo ""
