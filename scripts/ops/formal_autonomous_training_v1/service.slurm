#!/bin/bash
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
exec /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/scripts/ops/formal_autonomous_training_v1/controller.py --activation "$1" --activation-sha256 "$2"
