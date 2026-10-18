#!/bin/bash
#SBATCH --job-name=cti-auto-cpucheck
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=intel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --no-requeue
#SBATCH --output=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/engineering/autonomous_control_cpu_v1/slurm_%j.out
#SBATCH --error=/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/engineering/autonomous_control_cpu_v1/slurm_%j.err
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
exec /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B /share/home/u15016/XXY_CVPR/CTI-VLA/control_repo/results/formal_main_v2/engineering/autonomous_control_cpu_v1/probe.py
