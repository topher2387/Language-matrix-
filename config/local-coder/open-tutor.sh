#!/bin/bash
set -euo pipefail
export XDG_CONFIG_HOME=/home/topher/Language-matrix-chat/config
export XDG_DATA_HOME=/home/topher/Language-matrix-chat/data
export XDG_STATE_HOME=/home/topher/Language-matrix-chat/state
export OPENCODE_DISABLE_AUTOUPDATE=1
export GH_CONFIG_DIR=/home/topher/.config/gh
cd /home/topher/Language-matrix-chat
if [ "$#" -eq 0 ]; then
  set -- --prompt "$(cat /home/topher/Language-matrix-chat/tutor-request.txt)"
fi
exec /snap/opencode/current/bin/opencode --pure --model language-matrix/kanana-2-30b-a3b --agent chat "$@"
