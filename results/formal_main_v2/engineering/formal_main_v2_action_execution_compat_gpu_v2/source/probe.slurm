#!/bin/bash
# One preregistered engineering attempt; this wrapper does not release trials.
#SBATCH --job-name=cti-action-exec16
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${INVOCATION:?Root invocation required}"
: "${INVOCATION_SHA256:?Root invocation SHA required}"
: "${WRAPPER_SHA256:?Root wrapper SHA required}"
P=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
H=/share/home/u15016/XXY_CVPR/CTI-VLA
S="$P/snapshots/formal_main_v2_run_564be0995e"
test "$(sha256sum "$0" | cut -d' ' -f1)" = "$WRAPPER_SHA256"
cd "$S"
export PYTHONPATH="$S/src" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$P/configs/libero_runtime"
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# Verify the launcher before executing its bytes; no mutable script is trusted
# merely because it is located beneath the project directory.
srun "$H/venv/bin/python" -B - "$INVOCATION" "$INVOCATION_SHA256" "$WRAPPER_SHA256" <<'PY'
from pathlib import Path
import hashlib,json,os,re,sys
p='/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA'
stage='formal_main_v2_action_execution_compat_gpu_v2'
invocation,expected,wrapper=sys.argv[1:]
if invocation != p+'/results/formal_main_v2/invocations/'+stage+'_attempt01.json' or not re.fullmatch('[0-9a-f]{64}',expected):
    raise ValueError('unregistered invocation')
ip=Path(invocation)
if ip.resolve()!=ip.absolute() or any(x.is_symlink() for x in (ip,*ip.parents)):raise ValueError('invocation alias')
data=ip.read_bytes()
if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('invocation SHA differs')
inv=json.loads(data)
launcher=p+'/results/formal_main_v2/engineering/'+stage+'/source/launcher.py'
if inv.get('stage_key')!=stage or inv.get('wrapper_sha256')!=wrapper or inv.get('watched_files',{}).get(launcher)!=inv.get('launcher_sha256'):
    raise ValueError('wrapper/launcher not bound')
lp=Path(launcher)
if lp.resolve()!=lp.absolute() or any(x.is_symlink() for x in (lp,*lp.parents)):raise ValueError('launcher alias')
if hashlib.sha256(lp.read_bytes()).hexdigest()!=inv['launcher_sha256']:raise ValueError('launcher SHA differs')
os.execv(sys.executable,[sys.executable,'-B',launcher,'--invocation',invocation,'--invocation-sha256',expected])
PY
