#!/bin/bash
#SBATCH --job-name=cti-g1f-eval
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
: "${SOURCE_ROOT:?Set verified evaluation snapshot}"
: "${RUN_ROOT:?Set experiment results root}"
: "${MODE:?closed_loop, collect or profile}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -e "$RUN_ROOT")
if [[ "$SOURCE_ROOT" != "$PROJECT_ROOT/snapshots/"* || "$RUN_ROOT" != "$PROJECT_ROOT/results/"* ]]; then exit 2; fi
if [[ "$MODE" != closed_loop && "$MODE" != collect && "$MODE" != profile ]]; then exit 2; fi
exec 9>"$RUN_ROOT/.${MODE}.writer.lock"
flock -n 9 || { printf 'An existing process owns this evaluation stage\n' >&2; exit 2; }
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$PROJECT_ROOT/configs/libero_runtime"
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a
TRAINED=/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_v1
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s"}\n' "$code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap finish EXIT
common=(--project-root "$PROJECT_ROOT" --checkpoint "$CHECKPOINT" --cache-directory "$PROJECT_ROOT/.local/huggingface-g1f-eval")
pair=(--f01-report "$RUN_ROOT/acceptance/f01_acceptance.json" --checkpoint-a "$TRAINED/A/best.pt" --checkpoint-b "$TRAINED/B/best.pt" --receipt-a "$RUN_ROOT/training/A/deployment_receipt.json" --receipt-b "$RUN_ROOT/training/B/deployment_receipt.json")
if [[ "$MODE" == closed_loop ]]; then
  srun python scripts/eval_future_selector_libero.py "${common[@]}" "${pair[@]}" \
    --libero-config "$PROJECT_ROOT/configs/libero_runtime" --output-directory "$RUN_ROOT/closed_loop"
elif [[ "$MODE" == collect ]]; then
  srun python scripts/collect_future_profile_panel.py "${common[@]}" \
    --libero-config "$PROJECT_ROOT/configs/libero_runtime" \
    --g0-report "$PROJECT_ROOT/results/g0_20261014_v1/g0_acceptance.json" --output "$RUN_ROOT/profile_panel"
else
  # Slurm allocates one full L40 exclusively to this job; no concurrent project process is launched.
  srun python scripts/profile_future_observation_to_action.py "${common[@]}" "${pair[@]}" \
    --panel "$RUN_ROOT/profile_panel/panel.json" --output "$RUN_ROOT/latency" --uncontended-gpu
fi
