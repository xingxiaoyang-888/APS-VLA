#!/bin/bash
#SBATCH --job-name=cti-goal-remaining5
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
#SBATCH --exclude=gpu4020
#SBATCH --output=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/slurm/%x_%j.out
#SBATCH --error=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/slurm/%x_%j.err
set -euo pipefail
: "${CTI_GOAL_REMAINING5_PAIR_KEY:?Exact remaining-five pair required}"
: "${CTI_GOAL_REMAINING5_AUTH_SHA256:?Exact NEW root authorization SHA required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
S=$P/snapshots/formal_main_v2_run_564be0995e
cd "$S"
export PYTHONPATH="$S/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7 TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
exec srun /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B "$P/scripts/ops/formal_goal_remaining5_gate_v1/entry.py" --pair-key "$CTI_GOAL_REMAINING5_PAIR_KEY" --authorization "$P/results/formal_main_v2/execution/goal_remaining5_v1/$CTI_GOAL_REMAINING5_PAIR_KEY/root_authorization.json" --authorization-sha256 "$CTI_GOAL_REMAINING5_AUTH_SHA256"
