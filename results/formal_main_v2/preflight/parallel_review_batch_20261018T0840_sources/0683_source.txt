#!/bin/bash
set -euo pipefail
cd /ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
exec 9>results/g1_future_long/assets/.model-resume.lock
flock -n 9 || exit 2
set +e
/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python scripts/server/download_assets.py \
  --manifest configs/assets/openvla_oft_libero_long.json \
  --root /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-10-95220f9 \
  --kind model --endpoint https://hf-mirror.com --workers 4 \
  --receipt results/g1_future_long/assets/server_model.json
result=$?
printf '{"exit_code":%s,"reason":"resume same pinned model with four transfer workers"}\n' "$result" >results/g1_future_long/assets/model_resume_exit.json
exit "$result"
