#!/bin/bash
#SBATCH --job-name=cti-g2
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
: "${SOURCE_ROOT:?Set immutable G2 source snapshot}"
: "${RUN_ROOT:?Set detached cache output directory}"
: "${G1_REPORT:?Set scientifically reviewed G1 acceptance report}"
: "${SPLIT:?Set train or validation}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
MODE=${MODE:-pilot}
if [[ "$MODE" != pilot && "$MODE" != full ]]; then exit 2; fi
if [[ "$SPLIT" != train && "$SPLIT" != validation ]]; then exit 2; fi
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
G1_REPORT=$(realpath -e "$G1_REPORT")
for g2_path in "$SOURCE_ROOT" "$RUN_ROOT" "$G1_REPORT"; do
  if [[ "$g2_path" != "$PROJECT_ROOT/"* ]]; then exit 2; fi
done
if [[ "$RUN_ROOT" == "$SOURCE_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1 TOKENIZERS_PARALLELISM=false
# Preserve scheduler GPU visibility. CLI validates G1 go and protocol identities.
g2_finish() {
  g2_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s","split":"%s","mode":"%s"}\n' "$g2_exit_code" "$SLURM_JOB_ID" "$SPLIT" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap g2_finish EXIT
g2_limit=()
if [[ "$MODE" == pilot ]]; then g2_limit=(--observation-limit 1); fi
srun python scripts/build_training_cache.py \
  --checkpoint /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a \
  --asset-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
  --g1-report "$G1_REPORT" --split "$SPLIT" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g2-$SPLIT" \
  --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
  --output "$RUN_ROOT" "${g2_limit[@]}"
