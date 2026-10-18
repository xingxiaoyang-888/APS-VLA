#!/bin/bash
#SBATCH --job-name=cti-g1-step
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail
: "${SOURCE_ROOT:?Set immutable source snapshot}"
: "${RUN_ROOT:?Set independent optional diagnostic directory}"
: "${G1_DIRECTORY:?Set completed original G1}"
: "${ANALYSIS_SUMMARY:?Set completed D4 summary}"
: "${ACTIVATION_RECEIPT:?Set reviewed no-go activation receipt}"
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -m "$RUN_ROOT")
G1_DIRECTORY=$(realpath -e "$G1_DIRECTORY")
ANALYSIS_SUMMARY=$(realpath -e "$ANALYSIS_SUMMARY")
ACTIVATION_RECEIPT=$(realpath -e "$ACTIVATION_RECEIPT")
for step_path in "$SOURCE_ROOT" "$RUN_ROOT" "$G1_DIRECTORY" "$ANALYSIS_SUMMARY" "$ACTIVATION_RECEIPT"; do
  if [[ "$step_path" != "$PROJECT_ROOT/"* ]]; then exit 2; fi
done
if [[ "$RUN_ROOT" == "$SOURCE_ROOT" || "$RUN_ROOT" == "$SOURCE_ROOT/"* || "$RUN_ROOT" == "$G1_DIRECTORY" || "$RUN_ROOT" == "$G1_DIRECTORY/"* || "$G1_DIRECTORY" == "$RUN_ROOT/"* ]]; then exit 2; fi
mkdir -p "$RUN_ROOT"
exec 9>"$RUN_ROOT/.writer.lock"
flock -n 9 || { printf 'An optional diagnostic writer already holds the run lock\n' >&2; exit 2; }
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false
step_finish() {
  step_exit_code=$?
  printf '{"exit_code":%s,"job_id":"%s"}\n' "$step_exit_code" "$SLURM_JOB_ID" > "$RUN_ROOT/job_${SLURM_JOB_ID}.json"
}
trap step_finish EXIT
srun python scripts/run_teacher_step_diagnostic.py \
  --project-root "$PROJECT_ROOT" --output-directory "$RUN_ROOT" \
  --g1-directory "$G1_DIRECTORY" --analysis-summary "$ANALYSIS_SUMMARY" \
  --activation-receipt "$ACTIVATION_RECEIPT" \
  --checkpoint /share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a \
  --data-directory "$PROJECT_ROOT/data/modified_libero_rlds/libero_spatial_no_noops/1.0.0" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g1-step"
