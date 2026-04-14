#!/usr/bin/env bash
set -euo pipefail
ROOT="/root/.openclaw/workspace-resume-intake"
"$ROOT/.venv/bin/python" "$ROOT/scripts/extract_resume_text.py" "$@"
