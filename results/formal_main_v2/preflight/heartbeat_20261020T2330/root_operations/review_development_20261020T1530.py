from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
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
 jr=dict(path=B+'/terminal_jobs_snapshot.json',sha256='fbec27e002492f85b7922644826aad25d141977417b0257eb4aa7ac9c46093af')
 assert sha(R/jr['path'])==jr['sha256']
 jobs=json.loads((R/jr['path']).read_text())['registered_jobs']
 pr=dict(path='results/formal_main_v2/pulls/20261020T153411Z_ee5de4901f52/receipt.json',sha256='d2e3853021dc69de491ac500b88492c1f062ee84dd910bc39ebae51b39599d0f')
 reviewer=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root_actual_dev20261020T1530')
 for jid,pin in [('3050192', 'ffc1c4e22dc8c780a9172d0d51f6858430fba2f44e2ee8989d9a75e2726a1d5c'), ('3050205', '42ad708c34905405380aff051cd735ca9d0e9a806d74987209425175dd3010b4'), ('3050224', 'db5a8c2b13d27684e64aac8668ddab964904bb55177dcea3a67f6ead2850eb6c')]:
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
   failure=write(B+'/'+jid+'_root_review_failure_20261020T1530.json',dict(status='blocked_review',type=type(e).__name__,message=str(e),traceback=traceback.format_exc(),pull=pr,terminal_jobs_snapshot=jr,state_unchanged=sha(sp)==ss,new_jobs=0))
   print(json.dumps(dict(failure=failure)),flush=True)
   raise
