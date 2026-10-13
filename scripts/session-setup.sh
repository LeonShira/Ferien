#!/usr/bin/env bash
# Installs what the shorts pipeline needs at the start of every cloud session.
set -euo pipefail
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}"
if [ ! -x video/node_modules/.bin/remotion ]; then
  (cd video && npm ci --no-audit --no-fund --loglevel=error)
fi
# Install into the same interpreter that runs `python -m shorts`; a bare `pip` can
# belong to a different Python on some images.
PY="$(command -v python || command -v python3)"
"$PY" -c "import yaml, requests, kokoro_onnx, soundfile, faster_whisper, pytest" 2>/dev/null \
  || "$PY" -m pip install -q -r requirements.txt
# Local narration model (~350 MB), cached across runs in the same container.
"$PY" -c "from shorts import tts; [tts._download(u, tts.CACHE / n) for n, u in tts.KOKORO_FILES.items() if not (tts.CACHE / n).exists()]"
