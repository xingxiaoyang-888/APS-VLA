#!/bin/bash
# Root must register the script SHA and this CPU-only job before submission.
#SBATCH --job-name=cti-fs-probe
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=intel
#SBATCH --nodes=2
#SBATCH --ntasks=2
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:03:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${CTI_FS_PROBE_EXPECTED_SHA:?Root-registered probe script SHA256 is required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
PROBE="$P/scripts/ops/formal_shared_fs_probe.py"
[[ "$CTI_FS_PROBE_EXPECTED_SHA" =~ ^[0-9a-f]{64}$ ]]
test "${SLURM_NNODES:-${SLURM_JOB_NUM_NODES:-0}}" = 2
test "${SLURM_NTASKS:-0}" = 2
cd "$P"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# Each rank executes the exact bytes it SHA-verified, not a second mutable read.
# No virtualenv/model imports, GPUs, datasets, or existing training are used.
srun --nodes=2 --ntasks=2 --ntasks-per-node=1 --cpus-per-task=1 --cpu-bind=cores --kill-on-bad-exit=0 \
  /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python -B -c 'import hashlib,pathlib,sys; p=pathlib.Path(sys.argv[1]); expected=sys.argv[2]; source=p.read_bytes(); actual=hashlib.sha256(source).hexdigest(); (actual==expected) or sys.exit("Root-registered probe SHA mismatch"); sys.argv=[str(p),"--expected-script-sha256",expected]; exec(compile(source,str(p),"exec"),{"__name__":"__main__","__file__":str(p)})' \
  "$PROBE" "$CTI_FS_PROBE_EXPECTED_SHA"
