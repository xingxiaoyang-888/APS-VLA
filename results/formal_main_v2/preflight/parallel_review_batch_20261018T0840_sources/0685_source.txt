#!/bin/bash
#SBATCH --job-name=cti-migration-smoke
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SLURM_SUBMIT_DIR/src"
export OMP_NUM_THREADS=7
export OPENBLAS_NUM_THREADS=7
export TOKENIZERS_PARALLELISM=false
mkdir -p results/smoke
srun python scripts/smoke_openvla.py \
  /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a \
  configs/assets/openvla_oft_libero_spatial.json \
  --cache-directory .local/huggingface \
  --shard data/modified_libero_rlds/libero_spatial_no_noops/1.0.0/libero_spatial-train.tfrecord-00000-of-00016 \
  --seed 17 \
  --output "results/smoke/openvla_${SLURM_JOB_ID}.json"
