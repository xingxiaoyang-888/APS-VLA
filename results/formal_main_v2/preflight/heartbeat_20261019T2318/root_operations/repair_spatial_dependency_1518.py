from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,sys,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n))
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def record(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
 return ref(n)
def same_copy(src,dst):
 assert src.is_file() and not src.is_symlink() and not dst.exists();before=src.stat();raw=src.read_bytes();assert src.stat()==before
 dst.parent.mkdir(parents=True,exist_ok=True)
 with dst.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 assert h(dst)==hashlib.sha256(raw).hexdigest() and src.stat()==before
 return dict(source=str(src),destination=str(dst),sha256=h(dst),bytes=len(raw),source_retained=True)
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';c=load(cp,'repair1518controller')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 statepath=R/'results/experiment_supervisor/state.json';state_sha=h(statepath);s=json.loads(statepath.read_text());assert s['pending_submission'] is None
 jobs=[j for j in s['registered_jobs'] if str(j['job_id'])=='3042529'];assert len(jobs)==1 and jobs[0]['status']=='FAILED' and jobs[0]['elapsed_seconds']==2
 dn='.local/spatial_failure_diagnosis_1518/independent_diagnosis.json';assert h(R/dn)=='6260bb423a9c988cbddc2428c9ea996d89ae5c2ab449995509b6d3e09956d4f8';diag=json.loads((R/dn).read_text());assert diag['status']=='confirmed_dependency_publication_failure_no_new_scientific_results'
 assert diag['new_terminal_trials']==0 and not diag['child_started']
 invrel=jobs[0]['invocation'];assert h(P/invrel)==h(R/invrel)==jobs[0]['invocation_sha256'];inv=json.loads((P/invrel).read_text())
 expected='results/formal_main_v2/downstream_reviews/3022743.json';pin='9e14b86a1e556c53ef1cbd8c7bdc1733c3d5eb744f62ffee8df9395645816650'
 assert h(R/expected)==pin and (R/expected).stat().st_size==360831 and not (P/expected).exists()
 inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';assert h(R/inventory)=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926';files=json.loads((R/inventory).read_text())['files'];assert len(files)==173
 for n,checksum in files.items():assert h(R/n)==h(S/n)==checksum
 parentrel='scripts/ops/formal_action_deployment_v1/wrapper.py';assert h(P/parentrel)==h(R/parentrel)=='d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33'
 parent=load(P/parentrel,'real_spatial_parent_preflight1518');prefix=P/inv['run_root'].removeprefix(str(P)+'/')/'trials.jsonl'
 before_prefix=h(prefix);assert before_prefix==diag['old_prefix_sha256'] and prefix.stat().st_size==diag['old_prefix_bytes']
 try:parent.verify(inv,project=P)
 except ValueError as ex:assert str(ex)=='Noncanonical or missing evidence';before_error=str(ex)
 else:raise AssertionError('failure unexpectedly disappeared before exact repair')
 repair=same_copy(R/expected,P/expected)
 result=parent.verify(inv,project=P)
 assert isinstance(result,dict) and {'args','original_plan','effective_plan','execution_contract','readiness','contract','original_wrapper','runtime'}==set(result)
 assert h(prefix)==before_prefix and h(statepath)==state_sha
 for n,checksum in files.items():assert h(R/n)==h(S/n)==checksum
 copied=[]
 for n in ['results/formal_main_v2/job_receipts/3042529.json','results/slurm/cti-formal-downstream_3042529.out','results/slurm/cti-formal-downstream_3042529.err']:
  copied.append(same_copy(P/n,R/n))
 receipt=record(B+'/Spatial_dependency_repair.json',dict(schema='formal_main_v2',kind='root_bounded_missing_dependency_publication',status='exact_original_bytes_published_actual_P_CPU_verify_passed',utc=datetime.now(timezone.utc).isoformat(),failed_job_id='3042529',independent_diagnosis=ref(dn),before_error=before_error,missing_dependency=repair,actual_unmodified_parent_source=ref(parentrel),invocation=ref(invrel),actual_P_wrapper_verify_passed=True,no_in_memory_reference_redirection=True,child_started=False,models_loaded=False,new_trials=0,old_terminal_trials_preserved=12,prefix_sha256=before_prefix,prefix_bytes=prefix.stat().st_size,new_GPU_submissions=0,automatic_retry=False,new_attempt_requires_new_exact_authorization=True,all173_R_S_unchanged=True,state_unchanged=True,failed_GPU_seconds_retained=2,nonweight_failure_logs_mirrored=copied))
 print(json.dumps(dict(status='missing_dependency_repaired_actual_CPU_preflight_passed',receipt=receipt,submitted=False,new_trials=0)))
