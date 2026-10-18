#!/bin/bash
#SBATCH --job-name=cti-g1f-profile-repeat1
#SBATCH --account=p_p15016
#SBATCH --qos=cpu-500_core-l40-8_card-a800-8_card
#SBATCH --partition=L40
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=7
#SBATCH --gres=gpu:l40:1
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --no-requeue
#SBATCH --output=results/slurm/%x_%j.out
#SBATCH --error=results/slurm/%x_%j.err
set -euo pipefail

# One registered repeat only. No model/runtime edits, extra hooks, data choice,
# tail deletion or dependency on jobs running on another node.
PROJECT_ROOT=/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA
SOURCE_ROOT="$PROJECT_ROOT/snapshots/g1_future_eval_v1"
RUN_ROOT="$PROJECT_ROOT/results/g1_future_v1"
REGISTRATION="$RUN_ROOT/latency_repeat1_registration.json"
OUTPUT="$RUN_ROOT/latency_repeat1"
CLAIM="$RUN_ROOT/latency_repeat1_attempt.json"
CHECK_ONLY=${CHECK_ONLY:-0}
if [[ "$CHECK_ONLY" != 0 && "$CHECK_ONLY" != 1 ]]; then exit 2; fi
if [[ "$CHECK_ONLY" == 0 ]]; then : "${SLURM_JOB_ID:?Execution requires Slurm; CHECK_ONLY=1 is read-only CPU preflight}"; fi

SOURCE_ROOT=$(realpath -e "$SOURCE_ROOT")
RUN_ROOT=$(realpath -e "$RUN_ROOT")
cd "$SOURCE_ROOT"
source /share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/activate
export PYTHONPATH="$SOURCE_ROOT/src"
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=7 OPENBLAS_NUM_THREADS=7 MKL_NUM_THREADS=7
export TF_NUM_INTRAOP_THREADS=7 TF_NUM_INTEROP_THREADS=1
export TOKENIZERS_PARALLELISM=false MUJOCO_GL=egl
export LIBERO_CONFIG_PATH="$PROJECT_ROOT/configs/libero_runtime"
# CUDA_VISIBLE_DEVICES is owned by Slurm and is deliberately not overridden.
CHECKPOINT=/share/home/u15016/XXY_CVPR/CTI-VLA/models/openvla-7b-oft-finetuned-libero-spatial-6d0231a
TRAINED=/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/g1_future_v1

python - "$PROJECT_ROOT" "$SOURCE_ROOT" "$RUN_ROOT" "$REGISTRATION" <<'PY'
import hashlib, json, pathlib, sys
project, source, run, registration = map(pathlib.Path, sys.argv[1:])
def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
reg = read(registration)
unsigned = {k: v for k, v in reg.items() if k != 'content_signature'}
signature = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
if reg.get('content_signature') != signature or reg.get('schema') != 'g1f-latency-repeat-registration-v1':
    raise SystemExit('Repeat registration signature/schema mismatch')
if reg['source_root'] != str(source) or reg['output_directory'] != str(run / 'latency_repeat1') or reg['maximum_additional_attempts'] != 1:
    raise SystemExit('Only the registered immutable source/output and one attempt are allowed')
if reg['reporting'] != {'retain_first_run': True, 'report_runs_side_by_side': True, 'select_faster_run': False,
                        'remove_spikes': False, 'additional_repeats_after_this': 0}:
    raise SystemExit('Two-run reporting policy changed')
original = run / 'latency'
fixed = {'config.json': '808522465d3ffacdc2ae631d1fe0a2d9901864d353081431fb71de61ef5f65d0',
         'calls.jsonl': '148aba4255de10b4e55b02945e3ef20e14e68ce53b31f3633ec8fdd7707c80e0',
         'measurements.json': 'a0ef3375c4f71fe45e8fe52d4e6da9bae068fc8e175a074cf960fb66a9eea85c',
         'summary.json': '0c3133235300aac69385caa10638895ddfc01cfc8fa65ddd9963aef1e445867f'}
if reg['first_run_files'] != fixed or any(sha(original / name) != value for name, value in fixed.items()):
    raise SystemExit('Original run was modified; never replace or repair it for this repeat')
config = read(original / 'config.json')
expected = {'warmup_calls': 50, 'repeats': 5, 'component_repeats': 1, 'order_seed': 1017,
            'instruction_modes': ['cold', 'hot'], 'synthetic': False}
if config['config'] != expected or reg['profile_config'] != expected:
    raise SystemExit('Repeat timing protocol differs from the first run')
if config['methods'] != ['dense', 'uniform128', 'future_A', 'future_B'] or config['panel']['observations'] != 5 or config['panel']['episodes'] != 3:
    raise SystemExit('Repeat requires the same four methods and five raw observations')
if config['panel']['panel_sha256'] != reg['panel_sha256'] or config['checkpoint_hashes'] != reg['watched_artifacts'] or config['source_files'] != reg['runtime_source_files']:
    raise SystemExit('Registration differs from first-run inputs/weights/source')
for name, expected_sha in config['checkpoint_hashes'].items():
    if sha(pathlib.Path(name)) != expected_sha:
        raise SystemExit('Frozen input/checkpoint changed: ' + name)
for relative, expected_sha in config['source_files'].items():
    if sha(source / relative) != expected_sha:
        raise SystemExit('Immutable runtime changed: ' + relative)
if (run / 'latency_repeat1').exists() or (run / 'latency_repeat1_attempt.json').exists():
    raise SystemExit('The sole repeat is already claimed or has output; no retry/overwrite')
print(json.dumps({'status': 'repeat1_preflight_passed', 'planned_full_pipeline_calls': 440,
                  'gpu_queries': 0, 'first_run_preserved': True}), flush=True)
PY

# This original prepare-only path verifies every referenced dense receipt/NPZ.
python scripts/profile_future_observation_to_action.py \
  --panel "$RUN_ROOT/profile_panel/panel.json" --order-seed 1017 --prepare-only
if [[ "$CHECK_ONLY" == 1 ]]; then exit 0; fi

exec 9>"$RUN_ROOT/.profile_repeat1.writer.lock"
flock -n 9 || { printf 'Another process owns the sole profiling repeat\n' >&2; exit 2; }
# Atomic durable claim survives failure or a hard kill. No automatic restart.
python - "$CLAIM" "$REGISTRATION" "$SLURM_JOB_ID" <<'PY'
import datetime, hashlib, json, os, pathlib, sys
path, registration, job = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
record = {'attempt': 1, 'job_id': job, 'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'registration_sha256': hashlib.sha256(registration.read_bytes()).hexdigest(),
          'automatic_retry_allowed': False}
with path.open('x', encoding='utf-8') as stream:
    stream.write(json.dumps(record, sort_keys=True) + '\n')
    stream.flush()
    os.fsync(stream.fileno())
PY
finish() {
  code=$?
  printf '{"exit_code":%s,"job_id":"%s","mode":"profile_repeat1","additional_retries_allowed":0}\n' \
    "$code" "$SLURM_JOB_ID" > "$RUN_ROOT/job_${SLURM_JOB_ID}_profile_repeat1.json"
}
trap finish EXIT

srun python scripts/profile_future_observation_to_action.py \
  --project-root "$PROJECT_ROOT" --checkpoint "$CHECKPOINT" \
  --cache-directory "$PROJECT_ROOT/.local/huggingface-g1f-eval" \
  --f01-report "$RUN_ROOT/acceptance/f01_acceptance.json" \
  --checkpoint-a "$TRAINED/A/best.pt" --checkpoint-b "$TRAINED/B/best.pt" \
  --receipt-a "$RUN_ROOT/training/A/deployment_receipt.json" \
  --receipt-b "$RUN_ROOT/training/B/deployment_receipt.json" \
  --panel "$RUN_ROOT/profile_panel/panel.json" --order-seed 1017 \
  --output "$OUTPUT" --uncontended-gpu
