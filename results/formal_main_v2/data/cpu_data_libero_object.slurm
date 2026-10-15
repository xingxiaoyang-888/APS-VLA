#!/bin/bash
set -euo pipefail
cd /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_data_1c6b2f6
export PYTHONPATH=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_data_1c6b2f6/src PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
exec /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python scripts/data/build_formal_data.py --suite libero_object --project-root /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA --data-directory /share/home/u15016/XXY_CVPR/CTI-VLA/data/modified_libero_rlds/libero_object_no_noops/1.0.0
