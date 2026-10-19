#!/bin/bash
#SBATCH --job-name=cti-g0
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err

# Submit from the project root after creating results/slurm. Required exports:
# SOURCE_ROOT=/absolute/immutable/source/snapshot RUN_ROOT=/absolute/run/output
# MODE=initial (default): 90-observation parity, then first 3 paired trials.
# MODE=closed_loop: same source/output, resume all remaining closed-loop trials.
# This job intentionally does not accept G0 or start G1 automatically.
set -euo pipefail
: "${SOURCE_ROOT:?Set SOURCE_ROOT to the immutable CTI-VLA source snapshot}"
: "${RUN_ROOT:?Set RUN_ROOT to this G0 run output directory}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
MODE=${MODE:-initial}
if [[ "$MODE" != initial && "$MODE" != closed_loop ]]; then
  printf 'Unsupported MODE: %s\n' "$MODE" >&2
  exit 2
fi
if [[ "$SOURCE_ROOT" != /* || "$RUN_ROOT" != /* ]]; then
  printf 'SOURCE_ROOT and RUN_ROOT must be absolute paths\n' >&2
  exit 2
fi
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
PROJECT_ROOT=$(realpath -e "$PROJECT_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
if [[ "$SOURCE_ROOT" != "$PROJECT_ROOT/"* || "$RUN_ROOT" != "$PROJECT_ROOT/"* ]]; then
  printf 'Source and results must stay inside the CTI-VLA project\n' >&2
  exit 2
fi
if [[ "$SOURCE_ROOT" == "$RUN_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* ]]; then
  printf 'Run outputs must stay outside the immutable source snapshot\n' >&2
  exit 2
fi
if [[ ! -f "$SOURCE_ROOT/scripts/eval_libero.py" || ! -f "$SOURCE_ROOT/scripts/verify_g0_observations.py" ]]; then
  printf 'Source snapshot lacks G0 entry points\n' >&2
  exit 2
fi
if [[ ! -f "$PROJECT_ROOT/configs/libero_runtime/config.yaml" ]]; then
  printf 'Project LIBERO runtime configuration is missing\n' >&2
  exit 2
fi
if [[ "$MODE" == closed_loop && ! -f "$RUN_ROOT/closed_loop/config.json" ]]; then
  printf 'Closed-loop resume requires an existing frozen configuration\n' >&2
  exit 2
fi
mkdir -p "$RUN_ROOT"
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7
export OPENBLAS_NUM_THREADS=7
export MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7
export TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false
export LIBERO_CONFIG_PATH="$PROJECT_ROOT/configs/libero_runtime"
export MUJOCO_GL=egl
# CUDA_VISIBLE_DEVICES remains exactly as assigned by Slurm.
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a
CACHE_DIRECTORY="$PROJECT_ROOT/.local/huggingface-g0"
g0_finish() {
  g0_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"%s"}\n' \
    "$g0_exit_code" "$SLURM_JOB_ID" "$MODE" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap g0_finish EXIT
printf 'G0 mode=%s source=%s run=%s job=%s\n' "$MODE" "$SOURCE_ROOT" "$RUN_ROOT" "$SLURM_JOB_ID"

if [[ "$MODE" == initial ]]; then
  srun python scripts/verify_g0_observations.py \
    --checkpoint "$CHECKPOINT" \
    --checkpoint-manifest "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
    --protocol "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/protocol.json" \
    --panel "$SOURCE_ROOT/configs/manifests/spatial_g0g1_v1/diagnostic_90.json" \
    --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
    --oft-source "$PROJECT_ROOT/external/openvla-oft" \
    --cache-directory "$CACHE_DIRECTORY" \
    --output "$RUN_ROOT/observations"
fi

g0_limit=()
if [[ "$MODE" == initial ]]; then
  g0_limit=(--stop-after 3)
fi
srun python scripts/eval_libero.py \
  "$CHECKPOINT" "$SOURCE_ROOT/configs/assets/openvla_oft_libero_spatial.json" \
  --initial-states "$SOURCE_ROOT/configs/manifests/spatial_initial_states_v1/g0_development_15.json" \
  --test-initial-states "$SOURCE_ROOT/configs/manifests/spatial_initial_states_v1/init_states_test.json" \
  --official-source "$PROJECT_ROOT/external/openvla-oft" \
  --libero-source "$PROJECT_ROOT/external/LIBERO" \
  --libero-config "$PROJECT_ROOT/configs/libero_runtime" \
  --cache-directory "$CACHE_DIRECTORY" \
  --output-directory "$RUN_ROOT/closed_loop" \
  --seed 17 "${g0_limit[@]}"
