#!/bin/bash
#SBATCH --job-name=cti-g1f-long
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Set verified immutable Long source snapshot}"
: "${RUN_ROOT:?Set registered Long result root}"
: "${MODE:?inputs, acceptance, train, or closed_loop}"
PROJECT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
if [[ "$SOURCE_ROOT" != "$PROJECT/snapshots/"* || "$RUN_ROOT" != "$PROJECT/results/g1_future_long_v1" ]]; then exit 2; fi
if [[ "$MODE" != inputs && "$MODE" != acceptance && "$MODE" != train && "$MODE" != closed_loop ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
exec 9>"$RUN_ROOT/.${MODE}.writer.lock"
flock -n 9 || { printf 'Long stage already has a writer\n' >&2; exit 2; }
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$PROJECT/configs/libero_runtime"
# Preserve CUDA_VISIBLE_DEVICES assigned by Slurm.
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-10-95220f9
TRAINED=/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_long_v1
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s","suite":"libero_10"}\n' "$code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap finish EXIT
common=(--suite libero_10 --stats-key libero_10_no_noops \
  --config "$SOURCE_ROOT/configs/experiments/g1_future_long_v1.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/long_future_v1/protocol.json" \
  --checkpoint "$CHECKPOINT" --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_long.json" \
  --cache-directory "$PROJECT/.local/huggingface-g1f-long")
if [[ "$MODE" == inputs ]]; then
  srun python scripts/verify_long_inputs.py "${common[@]}" \
    --project-root "$PROJECT" --windows "$SOURCE_ROOT/configs/manifests/long_future_v1/windows.json" \
    --data-directory "$PROJECT/data/modified_libero_rlds/libero_10_no_noops/1.0.0" \
    --oft-source "$PROJECT/external/openvla-oft" --output "$RUN_ROOT/inputs"
elif [[ "$MODE" == acceptance || "$MODE" == train ]]; then
  extra=()
  if [[ "$MODE" == train ]]; then extra=(--acceptance-report "$RUN_ROOT/acceptance/f01_acceptance.json"); fi
  stage=acceptance
  if [[ "$MODE" == train ]]; then stage=training; fi
  srun python scripts/run_g1_future.py "${common[@]}" \
    --mode "$MODE" --windows "$SOURCE_ROOT/configs/manifests/long_future_v1/windows.json" \
    --data-directory "$PROJECT/data/modified_libero_rlds/libero_10_no_noops/1.0.0" \
    --input-acceptance-report "$RUN_ROOT/inputs/input_acceptance.json" \
    --feature-cache "$PROJECT/data/g1_future_long_v1_features" --training-checkpoints "$TRAINED" \
    --output "$RUN_ROOT/$stage" "${extra[@]}"
else
  srun python scripts/eval_future_selector_libero.py "${common[@]}" \
    --project-root "$PROJECT" --window-manifest "$SOURCE_ROOT/configs/manifests/long_future_v1/windows.json" \
    --panel "$SOURCE_ROOT/configs/manifests/long_initial_states_v1/development_panel_30.json" \
    --input-acceptance-report "$RUN_ROOT/inputs/input_acceptance.json" --f01-report "$RUN_ROOT/acceptance/f01_acceptance.json" \
    --checkpoint-a "$TRAINED/A/best.pt" --checkpoint-b "$TRAINED/B/best.pt" \
    --receipt-a "$RUN_ROOT/training/A/deployment_receipt.json" --receipt-b "$RUN_ROOT/training/B/deployment_receipt.json" \
    --official-source "$PROJECT/external/openvla-oft" --libero-source "$PROJECT/external/LIBERO" \
    --libero-config "$PROJECT/configs/libero_runtime" --controls dense --seed 17 --output-directory "$RUN_ROOT/closed_loop"
fi
