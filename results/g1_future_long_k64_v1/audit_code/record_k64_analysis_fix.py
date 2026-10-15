from pathlib import Path
import datetime,hashlib,json
r=Path('F:/CTI-VLA');out=r/'results/g1_future_long_k64_v1'
path='scripts/analyze_g1_future_budgets.py'
inventory=json.loads((out/'source_g1_future_long_k64_v1.json').read_text(encoding='utf-8'))
check=json.loads((r/'.local/k64_cost_scope_check/summary.json').read_text(encoding='utf-8'))
account=json.loads((out/'slurm_accounting.json').read_text(encoding='utf-8'))
assert next(j for j in account['jobs'] if j['job_id']=='3001540')['elapsed_seconds']==359
value={'status':'bounded_analysis_only_fix_verified','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'file':path,'before_sha256':inventory['files'][path],
    'after_sha256':hashlib.sha256((r/path).read_bytes()).hexdigest(),
    'issue':'Root submission names observation collection mode collect; analysis allowed collection but omitted collect.',
    'change':'Accept the already registered collect scope as well; do not drop or rename original accounting rows.',
    'frozen_server_source_changed':False,'training_and_deployment_source_changed':False,
    'scientific_configuration_changed':False,'GPU_calls':0,
    'validation':'Actual five-allocation accounting and original128 evidence replay through analyzer completed; new64 scientific results correctly pending.',
    'collection_job':'3001540','collection_allocated_gpu_seconds':359,
    'preflight_summary_sha256':hashlib.sha256((r/'.local/k64_cost_scope_check/summary.json').read_bytes()).hexdigest(),
    'reproduction':'Production snapshot192daa57 at source commit a980996 remains immutable; only later local result-analysis CLI differs.'}
(out/'analysis_scope_fix.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value))
