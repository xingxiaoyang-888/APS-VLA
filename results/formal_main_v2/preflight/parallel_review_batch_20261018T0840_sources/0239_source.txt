#!/bin/bash
#SBATCH --job-name=cti-g1f
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
: "${SOURCE_ROOT:?immutable snapshot required}"
: "${RUN_ROOT:?run root required}"
: "${MODE:?acceptance or train required}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
if [[ "$SOURCE_ROOT" != "$PROJECT_ROOT/snapshots/"* || "$RUN_ROOT" != "$PROJECT_ROOT/results/"* ]]; then exit 2; fi
if [[ "$MODE" != acceptance && "$MODE" != train ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
exec 9>"$RUN_ROOT/.writer.lock"
flock -n 9 || { printf 'Another G1-F process owns this run directory\n' >&2; exit 2; }
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s"}\n' "$code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap finish EXIT
extras=()
if [[ "$MODE" == train ]]; then
  : "${ACCEPTANCE_REPORT:?real F01 acceptance required}"
  extras=(--acceptance-report "$ACCEPTANCE_REPORT")
fi
srun python scripts/run_g1_future.py \
  --mode "$MODE" \
  --config "$SOURCE_ROOT/configs/experiments/g1_future_v1.json" \
  --windows "$SOURCE_ROOT/configs/manifests/spatial_future_v1/windows.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
  --checkpoint /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --g0-report "$PROJECT_ROOT/results/g0_20261014_v1/g0_acceptance.json" \
  --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g1f" \
  --feature-cache "$PROJECT_ROOT/data/g1_future_v1_features" \
  --training-checkpoints /share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_v1 \
  --output "$RUN_ROOT" "${extras[@]}"
