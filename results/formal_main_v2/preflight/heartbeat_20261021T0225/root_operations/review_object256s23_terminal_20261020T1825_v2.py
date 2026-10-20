from pathlib import Path
import copy,hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0225'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p))
def load(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
def save(n,x):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write(chr(10))
 return ref(p)
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root1825objectctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=json.loads(sp.read_bytes());assert s['pending_submission'] is None
 obs=json.loads((R/B/'initial_observation.json').read_bytes());assert h(R/B/'initial_observation.json')=='95f0af6dec82f26d3b9cd15b3b51154289c2d99c22cd08f5e412f1a1342d9573'
 assert obs['root_state_unchanged'] and obs['controller_training_complete_normal'] and not obs['capacity']['occupied']
 raw=R/B/'terminal_jobs_snapshot.json';assert h(raw)=='2bbf7258311d813d592439333db358397c5da12db59d2033044f10403226d9eb'
 source_jobs=json.loads(raw.read_bytes())['registered_jobs']
 jobs=[j for j in source_jobs if j.get('experiment')=='formal_main_v2']
 excluded=[dict(job_id=j['job_id'],experiment=j.get('experiment'),status=j['status']) for j in source_jobs if j.get('experiment')!='formal_main_v2']
 assert len(jobs)==264 and len(excluded)==30
 assert {str(j['job_id']) for j in jobs}=={str(j['job_id']) for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
 assert all(j['status'] in ('COMPLETED','FAILED') for j in jobs)
 jp=save(B+'/terminal_formal_jobs_snapshot_v2.json',dict(registered_jobs=jobs,excluded_nonformal_jobs=excluded,original_snapshot=ref(raw),observation=ref(R/B/'initial_observation.json'),root_state_unchanged=True,reason='Original reviewer requires complete immutable terminal formal jobs; old unrelated experiment histories remain preserved in original snapshot.'))
 job=next(j for j in jobs if str(j['job_id'])=='3052166');assert job['status']=='COMPLETED' and job['exit_code']=='0:0' and job['elapsed_seconds']==2165 and job['method_ids']==['A256_seed23','B256_seed23']
 pull_meta=R/B/'3052166_pull.json';assert h(pull_meta)=='bd9b74eca7870a217f6b43200b2559ae8679e79322b493e75282571b138cf488'
 pr=json.loads(pull_meta.read_bytes())['receipt'];assert h(R/pr['path'])==pr['sha256']=='35879bc6609b98bdb138d887012f47585798260614eb4c4975d57366e5cede04'
 original=load('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root1825originalreview')
 control=load('scripts/ops/formal_object256s23_source_bridge_v1/control.py','09ae3486565e17bd2c41b09adbfaa7a6d99f38754d3e77071f77851c9ac54f6f','root1825sourcecontrol')
 reviewer=control.reviewer_module(original.Evidence(R));invref=dict(path=job['invocation'],sha256=job['invocation_sha256']);assert h(R/invref['path'])==invref['sha256'];inv=json.loads((R/invref['path']).read_bytes())
 try:
  result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pr,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
  assert result['status']=='passed' and result['scientific_complete'] is True and result['completed_trials']==200 and result['explicit_source_control']==control.descriptor()
  rr=save('results/formal_main_v2/downstream_reviews/3052166.json',result)
  sr=save(B+'/3052166_root_terminal.json',dict(root_review=rr,pull=pr,terminal_jobs_snapshot=jp,explicit_source_control=control.descriptor(),scientific_complete=True,independent_review_integrated=False,execution_version=result['execution_version'],cost=result['cost'],final_state_values_read=False,final_release=False,new_jobs=0))
  assert h(sp)==before
  print(json.dumps(dict(status='root_terminal_passed_pending_independent',root_review=rr,root_terminal=sr,pull=pr,cost=result['cost'],successes={k:v['successes'] for k,v in result['reconstructed_summary']['methods'].items()},state_unchanged=True)),flush=True)
 except Exception as exc:
  failure=save(B+'/3052166_root_review_failure_v2.json',dict(status='blocked_review',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),pull=pr,terminal_jobs_snapshot=jp,state_unchanged=h(sp)==before,new_jobs=0));print(json.dumps(dict(failure=failure)),flush=True);raise
