#!/bin/bash
# Fixed upstream hashes; mirror is only the transport endpoint. No GPU work.
set -euo pipefail
PROJECT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
cd "$PROJECT"
mkdir -p results/g1_future_long/assets
exec 9>results/g1_future_long/assets/.writer.lock
flock -n 9 || exit 2
PYTHON=/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python
MODEL=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-10-95220f9
ENDPOINT=https://hf-mirror.com
"$PYTHON" scripts/server/download_assets.py --manifest configs/assets/openvla_oft_libero_long.json \
  --root "$MODEL" --kind model --endpoint "$ENDPOINT" --workers 2 \
  --receipt results/g1_future_long/assets/server_model.json >results/g1_future_long/assets/model_download.log 2>&1 &
model_pid=$!
"$PYTHON" scripts/server/download_assets.py --manifest configs/assets/libero_long_rlds.json \
  --root data/modified_libero_rlds --kind dataset --endpoint "$ENDPOINT" --workers 2 \
  --receipt results/g1_future_long/assets/server_dataset.json >results/g1_future_long/assets/data_download.log 2>&1 &
data_pid=$!
set +e
wait "$model_pid"
model_exit=$?
wait "$data_pid"
data_exit=$?
printf '{"model_exit":%s,"data_exit":%s}\n' "$model_exit" "$data_exit" > results/g1_future_long/assets/transfer_exit.json
test "$model_exit" = 0 && test "$data_exit" = 0
