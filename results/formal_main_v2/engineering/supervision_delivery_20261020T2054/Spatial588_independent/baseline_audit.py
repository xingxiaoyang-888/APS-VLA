from pathlib import Path
from types import ModuleType
import json,hashlib,collections,sys,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');D=Path(__file__).resolve().parent
checks=[]
def ck(ok,label):
 if not ok:raise AssertionError(label)
 checks.append(label)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(rel,pin):
 p=R/rel;ck(digest(p)==pin,'pinned '+rel);return json.loads(p.read_text())
state_before=digest(R/'results/experiment_supervisor/state.json')
source=read('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
ck(len(source['files'])==173,'exact173 files')
for rel,pin in source['files'].items():
 for root in (R,Path(source['source_root_server'])):
  p=root/rel;ck(not p.is_symlink() and digest(p)==pin,'frozen '+str(root/rel))
base='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
ledgerrel=base+'/trials.jsonl';ledgerpin='3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9'
for root in (R,P):ck(digest(root/ledgerrel)==ledgerpin,'unchanged prefix '+str(root))
raw=(R/ledgerrel).read_bytes();rows=[json.loads(line) for line in raw.splitlines()]
ck(len(raw)==592887 and raw.endswith(b'\n'),'prefix byte length and LF')
ck(collections.Counter(r['event'] for r in rows)=={'invocation':1,'start':12,'result':12},'only one actual invocation and12completed trials')
ck([r['slurm_job_id'] for r in rows if r['event']=='invocation']==['3022743'],'failed3042529 is absent from executed history')
results=[r for r in rows if r['event']=='result'];ck(all(r['status']=='completed' for r in results),'12completed raw statuses')
config=json.loads((R/(base+'/config.json')).read_text());panel=json.loads((R/(base+'/panel.json')).read_text())
adrel='scripts/ops/formal_evaluation_adapter.py';ck(digest(R/adrel)=='b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd','original adapter SHA')
ad=ModuleType('_independent_original_adapter');ad.__file__=str(R/adrel);exec(compile((R/adrel).read_bytes(),str(R/adrel),'exec'),ad.__dict__)
sys.path.insert(0,str(R/'src'));from cti_vla.evaluation import formal_trials
methods=['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17']
checked=ad.checked_ledger(R/ledgerrel,ad.signature(config),panel=panel,identifiers=methods,validators=formal_trials)
ck(checked['invocation_job_ids']==['3022743'] and len(checked['terminal_trial_ids'])==12,'original checked_ledger accepted exact historical prefix')
expected={formal_trials._identity(panel,s,m)['trial_id'] for s in panel['states'] for m in methods}
ck(len(panel['states'])==100 and len(expected)==600 and set(checked['terminal_trial_ids'])<expected,'fixed600 population remains')
ck(len(expected-set(checked['terminal_trial_ids']))==588,'remaining588 exact set')
receipt=read('results/formal_main_v2/job_receipts/3042529.json','86676fe6e84440069e61f4609008c4e5a9a7c88e883444519479d45767bd011e')
ck(receipt['job_id']=='3042529' and receipt['status']=='failed' and receipt['exit_code']==1,'original failed wrapper status')
ck(receipt['original_scientific_wrapper_executed'] is False and receipt['adapter_artifacts']==[] and receipt['adapter_receipts']==[] and receipt['action_execution_artifacts']==[],'no child or adapters were claimed')
ck(receipt['error_type']=='ValueError' and receipt['error']=='Noncanonical or missing evidence','exact retained pre-dispatch failure')
ck(receipt['run_root']==str(P/base),'failed attempt same run root')
repair=read('results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_dependency_repair.json','cb01f132002151d83eef8e5ba4c3f4228110eb8fc9a911546fb7946a82122569')
ck(repair['actual_P_wrapper_verify_passed'] is True and repair['child_started'] is False and repair['failed_GPU_seconds_retained']==2,'bounded missing dependency repair retained')
for rec in repair['nonweight_failure_logs_mirrored']:
 ck(digest(Path(rec['source']))==digest(Path(rec['destination']))==rec['sha256'],'same raw failure bytes '+rec['source'])
review=read('results/formal_main_v2/downstream_reviews/3022743.json','9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650')
ck(review['scientific_complete'] is False and review['completed_trials']==12 and review['job_id']=='3022743','real prefix root review is3022743')
ck(digest(P/'results/formal_main_v2/downstream_reviews/3022743.json')=='9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650','missing dependency actualP repaired bytes')
state=json.loads((R/'results/experiment_supervisor/state.json').read_text());jobs={str(j['job_id']):j for j in state['registered_jobs'] if str(j['job_id']) in ('3022743','3042529')}
ck(set(jobs)=={'3022743','3042529'},'both actual attempts stay registered')
ck([(jobs[j]['status'],jobs[j]['exit_code'],jobs[j]['elapsed_seconds'],jobs[j]['gpus']) for j in ('3022743','3042529')]==[('COMPLETED','0:0',393,1),('FAILED','1:0',2,1)],'395 total GPU seconds including2failure')
for jid in jobs:
 j=jobs[jid];ck(digest(R/j['invocation'])==j['invocation_sha256'],'registered invocation immutable '+jid)
 ck(j['execution_manifest_sha256']=='efc2fc4435442ba6458a033876c813a33de2afd69e952fae8ef86afd8727be03','unchanged original600 manifest '+jid)
ck(digest(R/'results/experiment_supervisor/state.json')==state_before,'state unchanged throughout independent audit')
result={'schema':'formal_main_v2','kind':'independent_spatial588_baseline_audit','status':'passed','review_role':'independent','checks':checks,'check_count':len(checks),'immutable_source_count':173,'source_sha256':source['source_sha256'],'all_attempt_job_ids':['3022743','3042529'],'actual_executed_invocation_ids':['3022743'],'prior_GPU_seconds':395,'failed_GPU_seconds':2,'prefix_bytes':len(raw),'prefix_sha256':ledgerpin,'retained_completed_trials':12,'registered_trial_population':600,'remaining_trial_ids':sorted(expected-set(checked['terminal_trial_ids'])),'new_GPU_submissions':0,'new_scientific_trials':0,'final_release':False,'candidate_implementation_not_yet_reviewed':True,'production_authorized':False,'state_sha256':state_before,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(D/'baseline_audit.json').write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'passed','check_count':len(checks),'report_path':str(D/'baseline_audit.json'),'sha256':digest(D/'baseline_audit.json'),'new_GPU_submissions':0}))
