from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=sha(p))
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_dev_review20261020T1418_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp)
 jr=dict(path=B+'/terminal_jobs_snapshot.json',sha256='4417ed6bc2d89611d6507d1ad2cabc544c89faa8b1eb0340cca563706322ba1a')
 assert sha(R/jr['path'])==jr['sha256']
 jobs=json.loads((R/jr['path']).read_text())['registered_jobs']
 pr=dict(path='results/formal_main_v2/pulls/20261020T142621Z_02800e667ffb/receipt.json',sha256='20139adbe331ea4d217e7011f22b4e3d6e008f6c59e87ff1d00a0735ef290493')
 reviewer=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root_actual_dev20261020T1418')
 for jid,pin in [('3049132', 'c8ca5e215f8af91ec2a5f1dd14aa522892495cf0e5e794a199d42f8d797a6d17'), ('3049172', '081c58942b8304aa5c882292c5ea994e1417c175a9aab874a461d984b0d57018'), ('3049622', '42e829fb4443b15329d17eaf8e0c1023ed0e47a4b98efc388aeb1eefc064353e'), ('3049632', '7a1469b5363a998d6737b1ffd0d32cf8d7d7e7ec520f0cb4f1d94becb9fde1e5'), ('3049657', '56f6e686633f00f77ab1aadfa326a71ad385823103c39c5a10f72fb284a05c32'), ('3049679', 'c07489c5e56cc3255b60f5eb6df34146e37e4b60fa7151cc97f8008f402b8803')]:
  job=next(j for j in jobs if str(j['job_id'])==jid)
  invref=dict(path=job['invocation'],sha256=job['invocation_sha256'])
  assert sha(R/invref['path'])==invref['sha256']==pin
  inv=json.loads((R/invref['path']).read_text())
  try:
   result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pr,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
   assert result['status']=='passed' and result['scientific_complete'] is True
   rr=write('results/formal_main_v2/downstream_reviews/'+jid+'.json',result)
   sr=write(B+'/'+jid+'_root_terminal.json',dict(root_review=rr,pull=pr,terminal_jobs_snapshot=jr,scientific_complete=True,independent_review_integrated=False,execution_version=result['execution_version'],cost=result['cost'],final_state_values_read=False,final_release=False,new_jobs=0))
   assert sha(sp)==ss
   print(json.dumps(dict(root_review=rr,root_terminal=sr,cost=result['cost'],state_unchanged=True)),flush=True)
  except Exception as e:
   failure=write(B+'/'+jid+'_root_review_failure_20261020T1418.json',dict(status='blocked_review',type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),pull=pr,terminal_jobs_snapshot=jr,state_unchanged=sha(sp)==ss,new_jobs=0))
   print(json.dumps(dict(failure=failure)),flush=True)
   raise
