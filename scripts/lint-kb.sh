#!/usr/bin/env bash
# Wrapper around lint_kb.py — the deterministic, zero-LLM knowledge-base checker.
# Usage:
#   bash scripts/lint-kb.sh [VAULT]
# With no argument it lints the sibling knowledge/ directory.
set -euo pipefail
VAULT="${1:-$(cd "$(dirname "$0")/.." && pwd)/knowledge}"
python3 "$(dirname "$0")/lint_kb.py" "$VAULT"
