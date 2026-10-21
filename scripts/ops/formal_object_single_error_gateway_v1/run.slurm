#!/bin/bash
set -euo pipefail
test "$#" -eq 1
[[ "$1" =~ ^[a-f0-9]{64}$ ]]
cd /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e
export PYTHONPATH="$PWD/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7 TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl LIBERO_CONFIG_PATH=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/configs/libero_runtime
exec srun /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/scripts/ops/formal_object_single_error_v1/entry.py --run --invocation /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/formal_main_v2/invocations/object_single_error_task08_state0049_dense_attempt01.json --invocation-sha256 "$1"
