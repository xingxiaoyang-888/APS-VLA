#!/bin/bash
# Official Object/Goal bases and demonstrations, pinned before formal results.
set -euo pipefail
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
H=/share/home/u15016/XXY_CVPR/CTI-VLA
S="$P/staging/formal_main_v2_assets"
R="$P/results/formal_main_v2/assets"
mkdir -p "$R"
exec 9>"$R/.transfer.lock"
flock -n 9 || exit 2
PY="$H/venv/bin/python"
ENDPOINT=https://hf-mirror.com
for suite in object goal; do
  if [[ "$suite" == object ]]; then revision=4c89574; else revision=c2d0f9f; fi
  "$PY" "$S/scripts/server/download_assets.py" \
    --manifest "$S/configs/assets/openvla_oft_libero_$suite.json" \
    --root "$H/models/openvla-7b-oft-finetuned-libero-$suite-$revision" \
    --kind model --endpoint "$ENDPOINT" --workers 2 \
    --receipt "$R/${suite}_model.json" >"$R/${suite}_model_download.log" 2>&1 &
  model_pid=$!
  "$PY" "$S/scripts/server/download_assets.py" \
    --manifest "$S/configs/assets/libero_${suite}_rlds.json" \
    --root "$H/data/modified_libero_rlds" --kind dataset --endpoint "$ENDPOINT" --workers 2 \
    --receipt "$R/${suite}_dataset.json" >"$R/${suite}_data_download.log" 2>&1 &
  data_pid=$!
  set +e
  wait "$model_pid"
  model_exit=$?
  wait "$data_pid"
  data_exit=$?
  set -e
  printf '{"model_exit":%s,"data_exit":%s}\n' "$model_exit" "$data_exit" >"$R/${suite}_transfer_exit.json"
  # Preserve independent suite progress even if one transfer fails.
done
