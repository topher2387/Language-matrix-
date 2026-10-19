#!/bin/bash
set -euo pipefail
export XDG_CONFIG_HOME=/home/topher/Language-matrix-coder/config
export XDG_DATA_HOME=/home/topher/Language-matrix-coder/data
export XDG_STATE_HOME=/home/topher/Language-matrix-coder/state
export OPENCODE_DISABLE_AUTOUPDATE=1
export GH_CONFIG_DIR=/home/topher/.config/gh
cd /home/topher/Language-matrix-coder
exec /snap/opencode/current/bin/opencode attach http://127.0.0.1:4097 --dir /home/topher/Language-matrix-qwen-fixture-cli "$@"
