#!/usr/bin/env bash
# Installs what the shorts pipeline needs at the start of every cloud session.
set -euo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}"
if [ ! -x video/node_modules/.bin/remotion ]; then
  (cd video && npm ci --no-audit --no-fund --loglevel=error)
fi
python3 -c "import yaml, requests" 2>/dev/null || pip install -q -r requirements.txt
python3 -c "import pytest" 2>/dev/null || pip install -q pytest
