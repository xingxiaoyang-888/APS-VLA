from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=sha(p))
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_dev_review20261020T1530_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp)
 private=R/'.local/four_development_independent_20261020T1644/terminal_jobs_snapshot.json';assert sha(private)=='a4b3fee06df29386476d63d2d7864f3082eda1f412848b341a9a8bda3294231a'
 jp=R/B/'four_development_terminal_jobs_snapshot.json'
 with jp.open('xb') as f:f.write(private.read_bytes())
 jr=ref(jp);jobs=json.loads(jp.read_text())['registered_jobs'];pr=dict(path='results/formal_main_v2/pulls/20261020T174830Z_45bc1fa22551/receipt.json',sha256='f92b3cbe59584160b698c32b192b395284238dd8e0249151d1029f9d13c038cd');assert sha(R/pr['path'])==pr['sha256']
 reviewer=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root_dev_last1644')
 current=json.loads(sp.read_text())['registered_jobs']
 for jid in ['3050870','3050890','3050901','3050916']:
  job=next(j for j in jobs if str(j['job_id'])==jid);live=next(j for j in current if str(j['job_id'])==jid)
  for key in ['invocation','invocation_sha256','source_sha256','stage_key','run_root','method_ids','suite']:assert job[key]==live[key]
  invref=dict(path=job['invocation'],sha256=job['invocation_sha256']);assert sha(R/invref['path'])==invref['sha256'];inv=json.loads((R/invref['path']).read_text())
  try:
   result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pr,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
   assert result['status']=='passed' and result['scientific_complete'] is True
   rr=write('results/formal_main_v2/downstream_reviews/'+jid+'.json',result)
   sr=write(B+'/'+jid+'_root_terminal.json',dict(root_review=rr,pull=pr,terminal_jobs_snapshot=jr,scientific_complete=True,independent_review_integrated=False,execution_version=result['execution_version'],cost=result['cost'],final_state_values_read=False,final_release=False,new_jobs=0))
   assert sha(sp)==ss
   print(json.dumps(dict(job_id=jid,root_review=rr,root_terminal=sr,cost=result['cost'],state_unchanged=True)),flush=True)
  except Exception as e:
   failure=write(B+'/'+jid+'_root_review_failure.json',dict(status='blocked_review',type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),pull=pr,terminal_jobs_snapshot=jr,state_unchanged=sha(sp)==ss,new_jobs=0));print(json.dumps(dict(failure=failure)),flush=True);raise
