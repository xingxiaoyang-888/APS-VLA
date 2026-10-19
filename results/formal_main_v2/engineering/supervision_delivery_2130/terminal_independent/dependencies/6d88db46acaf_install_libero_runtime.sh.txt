#!/bin/bash
# CPU dependency preparation only. Run from the registered CTI-VLA server root.
set -euo pipefail
ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
PY=/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python
cd "$ROOT"
mkdir -p results/setup
export PIP_CACHE_DIR="$ROOT/.local/pip-cache"
trap 'printf "%s\n" "$?" > results/setup/install_runtime_local.exit' EXIT
"$PY" - <<'PY'
import hashlib, json
from pathlib import Path
manifest = json.loads(Path('configs/assets/libero_wheels_transfer.json').read_text())
for row in manifest['files']:
    path = Path('external/wheels-libero') / row['path']
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b''): h.update(block)
    assert path.stat().st_size == row['size'] and h.hexdigest() == row['sha256'], str(path)
print('Verified transferred runtime packages:', len(manifest['files']), flush=True)
PY
# Direct paths prevent the resolver choosing an equally versioned remote wheel.
"$PY" -m pip install external/wheels-libero/*.whl external/wheels-libero/*.tar.gz --index-url https://pypi.tuna.tsinghua.edu.cn/simple --timeout 30 --retries 3 -r configs/requirements-libero.txt
"$PY" -m pip install --no-deps --no-build-isolation -e external/LIBERO
"$PY" -m pip check
"$PY" -m pip freeze > results/setup/after_libero_freeze.txt
LIBERO_CONFIG_PATH="$ROOT/configs/libero_runtime" "$PY" -c 'import tensorflow, mujoco, robosuite, cv2; from libero.libero import benchmark; print("runtime_imports_passed", benchmark.get_benchmark_dict().keys())'
