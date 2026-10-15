"""Root's independent non-weight engineering gate review."""
from pathlib import Path
import datetime,hashlib,json,math,sys
r=Path('F:/CTI-VLA');sys.path.insert(0,str(r/'src'))
from cti_vla.evaluation.future_budget_reuse import require_budget_f01
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
out=r/'results/g1_future_long_k64_v1'; acc=out/'acceptance'
source=read(out/'source_g1_future_long_k64_v1.json')
assert all(sha(r/k)==v for k,v in source['files'].items())
cfg=read(r/'configs/experiments/g1_future_long_k64_seed17_v1.json')
report=read(acc/'f01_acceptance.json'); sub=read(out/'submission_acceptance.json')
assert report['job_id']==sub['job_id'] and sub['source_sha256']==source['source_sha256']
check=require_budget_f01(acc/'f01_acceptance.json',config=cfg,source_root=r,
    window_manifest_sha256=sha(r/'configs/manifests/long_future_v1/windows.json'),
    input_acceptance_sha256=sha(r/'results/g1_future_long_v1/inputs/input_acceptance.json'))
for key in ('action_gradient_norm','future_gradient_norm','future_head_gradient_norm'):
    assert math.isfinite(report[key]) and report[key]>0,(key,report[key])
assert report['dense_max_abs']<=.002 and report['hard_max_abs']<=.002
assert report['soft_gate_mass_per_camera'] and all(abs(v-32)<.01 for row in report['soft_gate_mass_per_camera'] for v in row)
assert report['visual_tokens']==64 and report['per_camera_budgets']==[32,32]
assert report['vla_parameter_sha256']==read(r/'results/g1_future_long_v1/acceptance/f01_acceptance.json')['vla_parameter_sha256']
index=read(acc/'acceptance_cache_index.json')
assert len(index)==2 and all(x['identity']['window']['split']=='train' for x in index)
reuse=read(acc/'input_cache_reuse_receipt.json')
assert reuse['inherited_old128_F01'] is False and reuse['new_GPU_calls']==0
jobs=read(out/'slurm_accounting.json')['jobs']; row=next(x for x in jobs if x['job_id']==sub['job_id'])
assert row['state']=='COMPLETED' and row['exit_code']=='0:0' and row['allocated_gpus']==1
value={'status':'passed','reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'job_id':sub['job_id'],'new64_F01_measured':True,'old128_F01_not_substituted':True,
    'all_budget_gradient_parity_input_source_checks_passed':True,'shared_gate_seed17_only_measured':True,
    'input_cache_reused_without_production':True,'checkpoint_unchanged':True,
    'report_sha256':sha(acc/'f01_acceptance.json'),'source_sha256':source['source_sha256'],
    'gradients':{k:report[k] for k in ('action_gradient_norm','future_gradient_norm','future_head_gradient_norm')},
    'parity':{k:report[k] for k in ('dense_max_abs','hard_max_abs')},'cost':row,
    'review_script_sha256':sha(Path(__file__))}
(acc/'root_review.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(value))
