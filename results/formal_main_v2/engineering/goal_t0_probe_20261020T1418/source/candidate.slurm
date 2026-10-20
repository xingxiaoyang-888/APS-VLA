#!/bin/bash
# Candidate only. Root must publish exact bytes, audit, register one slot, then submit.
#SBATCH --job-name=cti-goal-t0-probe
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
#SBATCH --output=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm/%x_%j.out
#SBATCH --error=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/results/slurm/%x_%j.err
set -euo pipefail
: "${ROOT_AUTHORIZATION:?Separate root review/registration authorization required}"
: "${ROOT_AUTHORIZATION_SHA256:?Exact root authorization SHA required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
H=/share/home/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT="$P/snapshots/formal_main_v2_run_564be0995e"
BUNDLE_ROOT="$P/results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/source"
CONFIG="$BUNDLE_ROOT/config.json"
ENTRYPOINT="$BUNDLE_ROOT/probe.py"
ROOT_AUTHORIZATION=$(realpath -e "$ROOT_AUTHORIZATION")
case "$ROOT_AUTHORIZATION" in "$P"/results/formal_main_v2/engineering/goal_t0_probe_20261020T1418/*.json) ;; *) exit 2;; esac
printf '%s  %s\n' '4d0eec76dddf7574521231911c29e0df8dbbeb372910d615c00914451a1cb92c' "$ENTRYPOINT" | sha256sum -c -
printf '%s  %s\n' '773594fc7ccaeb51d44b348283634dcb6461945d503893fcdb33ce3b12e118ff' "$CONFIG" | sha256sum -c -
printf '%s  %s\n' "$ROOT_AUTHORIZATION_SHA256" "$ROOT_AUTHORIZATION" | sha256sum -c -
cd "$SOURCE_ROOT"
source "$H/venv/bin/activate"
export PYTHONPATH="$SOURCE_ROOT/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
# CUDA_VISIBLE_DEVICES remains owned by Slurm. Engineering GPU counts against8slots.
srun python -B "$ENTRYPOINT" --config "$CONFIG" --config-sha256 '773594fc7ccaeb51d44b348283634dcb6461945d503893fcdb33ce3b12e118ff' --run-gpu --root-authorization "$ROOT_AUTHORIZATION" --root-authorization-sha256 "$ROOT_AUTHORIZATION_SHA256"
