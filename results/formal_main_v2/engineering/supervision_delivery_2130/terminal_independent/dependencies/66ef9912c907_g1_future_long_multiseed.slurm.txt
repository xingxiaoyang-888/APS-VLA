#!/bin/bash
#SBATCH --job-name=cti-g1f-long-seeds
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
: "${SOURCE_ROOT:?Verified immutable multiseed source snapshot required}"
: "${RUN_ROOT:?Registered seed result root required}"
: "${TRAIN_SEED:?23 or 41 required}"
: "${MODE:?train or closed_loop required}"
PROJECT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
if [[ "$TRAIN_SEED" != 23 && "$TRAIN_SEED" != 41 ]]; then exit 2; fi
if [[ "$MODE" != train && "$MODE" != closed_loop ]]; then exit 2; fi
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -e "$RUN_ROOT")
if [[ "$SOURCE_ROOT" != "$PROJECT/snapshots/g1_future_long_multiseed_v1" ||
      "$RUN_ROOT" != "$PROJECT/results/g1_future_long_multiseed_v1/seed$TRAIN_SEED" ]]; then exit 2; fi
PARENT="$PROJECT/results/g1_future_long_v1"
REGISTRATION="$RUN_ROOT/reuse_registration.json"
test -f "$REGISTRATION"
exec 9>"$RUN_ROOT/.${MODE}.writer.lock"
flock -n 9 || { printf 'Registered stage already has a writer\n' >&2; exit 2; }
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s","training_seed":%s,"suite":"libero_10"}\n' \
    "$code" "$SLURM_JOB_ID" "$MODE" "$TRAIN_SEED" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap finish EXIT
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$PROJECT/configs/libero_runtime"
# Preserve the scheduler's CUDA_VISIBLE_DEVICES.
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-10-95220f9
TRAINED="/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_long_multiseed_v1/seed$TRAIN_SEED"
common=(--suite libero_10 --stats-key libero_10_no_noops \
  --config "$SOURCE_ROOT/configs/experiments/g1_future_long_seed${TRAIN_SEED}_v1.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/long_future_v1/protocol.json" \
  --project-root "$PROJECT" --checkpoint "$CHECKPOINT" \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_long.json" \
  --cache-directory "$PROJECT/.local/huggingface-g1f-long-seed$TRAIN_SEED" \
  --input-acceptance-report "$PARENT/inputs/input_acceptance.json" \
  --engineering-reuse-registration "$REGISTRATION")
if [[ "$MODE" == train ]]; then
  # Explicitly fresh training; a partial run requires root review and a new registration.
  test ! -e "$RUN_ROOT/training"
  test ! -e "$TRAINED"
  srun python scripts/run_g1_future.py "${common[@]}" --mode train \
    --windows "$SOURCE_ROOT/configs/manifests/long_future_v1/windows.json" \
    --data-directory "$PROJECT/data/modified_libero_rlds/libero_10_no_noops/1.0.0" \
    --feature-cache "$PROJECT/data/g1_future_long_v1_features" \
    --training-checkpoints "$TRAINED" \
    --acceptance-report "$PARENT/acceptance/f01_acceptance.json" \
    --output "$RUN_ROOT/training"
else
  test -f "$RUN_ROOT/training/train_finalization.json"
  test ! -e "$RUN_ROOT/closed_loop"
  srun python scripts/eval_future_selector_libero.py "${common[@]}" \
    --window-manifest "$SOURCE_ROOT/configs/manifests/long_future_v1/windows.json" \
    --panel "$SOURCE_ROOT/configs/manifests/long_initial_states_v1/development_panel_30.json" \
    --f01-report "$PARENT/acceptance/f01_acceptance.json" \
    --checkpoint-a "$TRAINED/A/best.pt" --checkpoint-b "$TRAINED/B/best.pt" \
    --receipt-a "$RUN_ROOT/training/A/deployment_receipt.json" \
    --receipt-b "$RUN_ROOT/training/B/deployment_receipt.json" \
    --official-source "$PROJECT/external/openvla-oft" --libero-source "$PROJECT/external/LIBERO" \
    --libero-config "$PROJECT/configs/libero_runtime" --dense-reference "$PARENT/closed_loop" \
    --seed 17 --output-directory "$RUN_ROOT/closed_loop"
fi
