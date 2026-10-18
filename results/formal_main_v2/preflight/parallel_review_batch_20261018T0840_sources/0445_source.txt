#!/bin/bash
#SBATCH --job-name=cti-g1
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Set immutable CTI-VLA source snapshot}"
: "${RUN_ROOT:?Set G1 output directory}"
: "${G0_REPORT:?Set fully passed G0 acceptance report}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
MODE=${MODE:-pilot}
if [[ "$MODE" != pilot && "$MODE" != full ]]; then exit 2; fi
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
G0_REPORT=$(realpath -e "$G0_REPORT")
for g1_path in "$SOURCE_ROOT" "$RUN_ROOT" "$G0_REPORT"; do
  if [[ "$g1_path" != "$PROJECT_ROOT/"* ]]; then
    printf 'All inputs and outputs must stay inside CTI-VLA: %s\n' "$g1_path" >&2
    exit 2
  fi
done
if [[ "$RUN_ROOT" == "$SOURCE_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false
# Preserve Slurm CUDA_VISIBLE_DEVICES. CLI rejects a missing or failed G0.
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a
g1_finish() {
  g1_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s"}\n' "$g1_exit_code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap g1_finish EXIT
g1_limit=()
if [[ "$MODE" == pilot ]]; then g1_limit=(--observation-limit 1); fi
srun python scripts/run_teacher_diagnostics.py \
  --checkpoint "$CHECKPOINT" \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
  --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g1" \
  --g0-report "$G0_REPORT" --output "$RUN_ROOT" "${g1_limit[@]}"
