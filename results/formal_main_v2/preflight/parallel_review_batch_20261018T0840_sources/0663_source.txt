#!/bin/bash
#SBATCH --job-name=cti-d1
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Set immutable D1 snapshot}"
: "${RUN_ROOT:?Set D1 output directory}"
: "${G0_REPORT:?Set accepted G0 report}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
G0_REPORT=$(realpath -e "$G0_REPORT")
for d1_path in "$SOURCE_ROOT" "$RUN_ROOT" "$G0_REPORT"; do
  if [[ "$d1_path" != "$PROJECT_ROOT/"* ]]; then exit 2; fi
done
if [[ "$RUN_ROOT" == "$SOURCE_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1 TOKENIZERS_PARALLELISM=false
# Keep the scheduler's CUDA_VISIBLE_DEVICES unchanged.
d1_finish() {
  d1_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s"}\n' "$d1_exit_code" "$SLURM_JOB_ID" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap d1_finish EXIT
srun python scripts/run_condition_diagnostics.py \
  --checkpoint /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a \
  --checkpoint-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --pairs "$SOURCE_ROOT/configs/manifests/spatial_d1_v1/pairs.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
  --libero-source "$PROJECT_ROOT/external/LIBERO" --evidence-root "$PROJECT_ROOT" \
  --g0-report "$G0_REPORT" --cache-directory "$PROJECT_ROOT/.local/huggingface-d1" \
  --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
  --max-attempts-per-condition 12 --output "$RUN_ROOT"
