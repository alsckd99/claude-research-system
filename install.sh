#!/usr/bin/env bash
# research-os first-time setup
# Run once after: claude plugin install <path-or-url>
# Sets API keys and installs required Python packages.

set -euo pipefail

# ──────────────────────────────────────────
# 1. Anthropic API Key
# ──────────────────────────────────────────
echo "[1/3] Anthropic API Key"

if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "already set"
else
  echo "Get your key at https://console.anthropic.com -> API Keys"
  echo ""
  read -rp "Anthropic API Key (sk-ant-..., Enter to skip): " ANTHROPIC_API_KEY
  if [ -n "${ANTHROPIC_API_KEY}" ]; then
    echo "export ANTHROPIC_API_KEY=\"${ANTHROPIC_API_KEY}\"" >> ~/.bashrc
    export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
    echo "saved to ~/.bashrc"
  else
    echo "skipped — set later: export ANTHROPIC_API_KEY='sk-ant-...'"
  fi
fi

# ──────────────────────────────────────────
# 2. GitHub Token (optional)
# ──────────────────────────────────────────
echo ""
echo "[2/3] GitHub Token (optional — for PR/issue management)"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  echo "already set"
else
  echo "github.com -> Settings -> Developer settings -> Personal access tokens (scopes: repo)"
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

if [ -n "${BRAVE_API_KEY:-}" ]; then
  echo "already set"
else
  echo "brave.com/search/api — paper search works without this (Semantic Scholar + arXiv always available)"
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
# 4. Python packages
# ──────────────────────────────────────────
echo ""
echo "installing Python packages..."
pip3 install -q anthropic pyyaml requests && echo "anthropic, pyyaml, requests OK"
pip3 install -q pymupdf && echo "pymupdf OK (PDF text extraction)" || echo "pymupdf failed — PDF text extraction will be skipped"

# ──────────────────────────────────────────
echo ""
echo "done. run: source ~/.bashrc"
echo ""
