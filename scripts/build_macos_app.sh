#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m PyInstaller --noconfirm --clean macos_ai_agent.spec

echo
echo "Built: dist/macOS AI Agent.app"
