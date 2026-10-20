#!/bin/bash
set -euo pipefail
cd /home/topher/Language-matrix-coder/north-mini-setup
curl --fail --location --retry 8 --retry-delay 10 --continue-at - --output North-Mini-Code-1.0-UD-Q4_K_M.gguf.part 'https://huggingface.co/unsloth/North-Mini-Code-1.0-GGUF/resolve/e306bb4bf0df610f5471d97a01de2b6e0b24d356/North-Mini-Code-1.0-UD-Q4_K_M.gguf'
echo 'd59f4cb3abec1bd3e5e185b99cdd811e3be3402cbc2bab8223081a460d5724bf  North-Mini-Code-1.0-UD-Q4_K_M.gguf.part' | sha256sum --check > checksum.txt
mv North-Mini-Code-1.0-UD-Q4_K_M.gguf.part North-Mini-Code-1.0-UD-Q4_K_M.gguf
date -u +%FT%TZ > download-completed.txt
