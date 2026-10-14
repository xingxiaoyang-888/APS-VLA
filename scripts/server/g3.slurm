#!/bin/bash
#SBATCH --job-name=cti-g3
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Set immutable G3 source snapshot}"
: "${RUN_ROOT:?Set non-weight training report directory}"
: "${G1_REPORT:?Set scientifically reviewed G1 report}"
: "${TRAIN_INDEX:?Set complete train cache index}"
: "${VALIDATION_INDEX:?Set complete effective-validation cache index}"
: "${CHECKPOINT_DIRECTORY:?Set new server-only scorer checkpoint directory}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
MODEL_ROOT=/share/home/u15016/XXY_CVPR/CTI-VLA
SEED=${SEED:-17}
RESUME=${RESUME:-0}
if [[ "$SEED" != 17 && "$SEED" != 23 && "$SEED" != 41 ]]; then exit 2; fi
if [[ "$RESUME" != 0 && "$RESUME" != 1 ]]; then exit 2; fi
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
G1_REPORT=$(realpath -e "$G1_REPORT")
TRAIN_INDEX=$(realpath -e "$TRAIN_INDEX")
VALIDATION_INDEX=$(realpath -e "$VALIDATION_INDEX")
CHECKPOINT_DIRECTORY=$(realpath -m "$CHECKPOINT_DIRECTORY")
for g3_path in "$SOURCE_ROOT" "$RUN_ROOT" "$G1_REPORT" "$TRAIN_INDEX" "$VALIDATION_INDEX"; do
  if [[ "$g3_path" != "$PROJECT_ROOT/"* ]]; then exit 2; fi
done
if [[ "$CHECKPOINT_DIRECTORY" != "$MODEL_ROOT/checkpoints/"* ]]; then exit 2; fi
if [[ "$RUN_ROOT" == "$SOURCE_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* ]]; then exit 2; fi
mkdir -p "$RUN_ROOT" "$CHECKPOINT_DIRECTORY"
exec 9>"$RUN_ROOT/.writer.lock"
flock -n 9 || { printf 'G3 report directory already has an active writer\n' >&2; exit 3; }
exec 8>"$CHECKPOINT_DIRECTORY/.writer.lock"
flock -n 8 || { printf 'G3 checkpoint directory already has an active writer\n' >&2; exit 3; }
if [[ "$RESUME" == 0 && -e "$RUN_ROOT/training_report.json" ]]; then
  printf 'Use a new report directory for a fresh training run\n' >&2
  exit 3
fi
cd "$SOURCE_ROOT"
source "$MODEL_ROOT/venv/bin/activate"
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7 TOKENIZERS_PARALLELISM=false
g3_finish() {
  g3_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s","seed":%s,"resume":%s}\n' "$g3_exit_code" "$SLURM_JOB_ID" "$SEED" "$RESUME" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap g3_finish EXIT
g3_resume=()
if [[ "$RESUME" == 1 ]]; then g3_resume=(--resume); fi
srun python scripts/train_selector.py \
  --checkpoint "$MODEL_ROOT/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a" \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
  --g1-report "$G1_REPORT" --train-index "$TRAIN_INDEX" --validation-index "$VALIDATION_INDEX" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g3-$SEED" \
  --checkpoint-directory "$CHECKPOINT_DIRECTORY" --output "$RUN_ROOT/training_report.json" \
  --seed "$SEED" --learning-rate 0.0003 --max-epochs 30 "${g3_resume[@]}"
