#!/bin/bash
#SBATCH --job-name=cti-long-o2a
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Frozen source required}"
: "${RUN_ROOT:?Registered result root required}"
: "${MODE:?collect or profile required}"
PROJECT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -e "$RUN_ROOT")
test "$SOURCE_ROOT" = "$PROJECT/snapshots/g1_future_long_k64_v1"
test "$RUN_ROOT" = "$PROJECT/results/g1_future_long_k64_v1"
case "$MODE" in collect|profile) ;; *) exit 2;; esac
exec 9>"$RUN_ROOT/.${MODE}.writer.lock"
flock -n 9 || exit 2
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s","suite":"libero_10"}\n' \
    "$code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap finish EXIT
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$PROJECT/configs/libero_runtime"
# CUDA_VISIBLE_DEVICES remains assigned by Slurm.
BASE=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-10-95220f9
PARENT="$PROJECT/results/g1_future_long_v1"
common=(--registration "$SOURCE_ROOT/configs/experiments/g1_future_long_k64_v1.json" \
  --development-panel "$SOURCE_ROOT/configs/manifests/long_initial_states_v1/development_panel_30.json" \
  --dense-reference "$PARENT/closed_loop" \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_long.json" \
  --checkpoint "$BASE" --cache-directory "$PROJECT/.local/huggingface-long-o2a" \
  --project-root "$PROJECT")
if [[ "$MODE" == collect ]]; then
  test ! -e "$RUN_ROOT/profile_panel"
  srun python scripts/collect_long_future_profile_panel.py "${common[@]}" \
    --input-acceptance "$PARENT/inputs/input_acceptance.json" \
    --official-source "$PROJECT/external/openvla-oft" --libero-source "$PROJECT/external/LIBERO" \
    --libero-config "$PROJECT/configs/libero_runtime" --output "$RUN_ROOT/profile_panel"
else
  test ! -e "$RUN_ROOT/profiling"
  test -f "$RUN_ROOT/profile_methods.json"
  srun python scripts/profile_long_future_observation_to_action.py "${common[@]}" \
    --panel "$RUN_ROOT/profile_panel/panel.json" --methods "$RUN_ROOT/profile_methods.json" \
    --uncontended-gpu --output "$RUN_ROOT/profiling"
fi
