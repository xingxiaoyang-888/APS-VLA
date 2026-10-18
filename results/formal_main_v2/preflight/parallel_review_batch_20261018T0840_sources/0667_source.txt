#!/bin/bash
# Root registers one immutable invocation before submitting this wrapper.
#SBATCH --job-name=cti-formal
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Immutable source snapshot required}"
: "${INVOCATION:?Registered invocation JSON required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
H=/share/home/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
INVOCATION=$(realpath -e "$INVOCATION")
case "$SOURCE_ROOT" in "$P"/snapshots/formal_main_v2_*) ;; *) exit 2;; esac
case "$INVOCATION" in "$P"/results/formal_main_v2/invocations/*.json) ;; *) exit 2;; esac
cd "$SOURCE_ROOT"
source "$H/venv/bin/activate"
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
# Preserve scheduler-owned CUDA_VISIBLE_DEVICES.
srun python scripts/server/run_formal_stage.py --invocation "$INVOCATION"
