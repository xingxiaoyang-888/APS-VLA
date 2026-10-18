#!/bin/bash
# Root registers exact entry, launcher, wrapper and all input hashes first.
#SBATCH --job-name=cti-action-probe
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=00:15:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${INVOCATION:?Root registered invocation required}"
: "${INVOCATION_SHA256:?Root invocation SHA required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
H=/share/home/u15016/XXY_CVPR/CTI-VLA
S="$P/snapshots/formal_main_v2_run_564be0995e"
cd "$S"
source "$H/venv/bin/activate"
export PYTHONPATH="$S/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
srun python -B "$P/results/formal_main_v2/engineering/object_action_range_probe_v1/source/launcher.py" --invocation "$INVOCATION" --invocation-sha256 "$INVOCATION_SHA256"
