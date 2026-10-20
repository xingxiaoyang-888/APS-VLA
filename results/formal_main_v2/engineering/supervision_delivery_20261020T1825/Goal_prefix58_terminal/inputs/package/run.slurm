#!/bin/bash
#SBATCH --job-name=cti-goal-prefix58
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --exclude=gpu4020
#SBATCH --output=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm/%x_%j.out
#SBATCH --error=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm/%x_%j.err
set -euo pipefail
: "${CTI_PREFIX58_AUTH_SHA256:?Exact NEW root authorization SHA required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
S=$P/snapshots/formal_main_v2_run_564be0995e
cd "$S"
export PYTHONPATH="$S/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7 TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
exec srun /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B "$P/scripts/ops/formal_goal_prefix58_observer_v2/entry.py" --authorization "$P/results/formal_main_v2/engineering/goal_prefix58_20261020T1825/root_authorization.json" --authorization-sha256 "$CTI_PREFIX58_AUTH_SHA256"
