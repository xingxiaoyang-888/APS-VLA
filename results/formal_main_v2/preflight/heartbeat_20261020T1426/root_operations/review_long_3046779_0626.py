from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T1426'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_long_review0626_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp)
 jr={'path':B+'/terminal_jobs_snapshot.json','sha256':'991a8b876c5eff0b4c19efab7ec73f5c7acb44dbde87edbbb8d551e1afb92a67'}
 assert sha(R/jr['path'])==jr['sha256']
 jobs=json.loads((R/jr['path']).read_text())['registered_jobs'];job=next(j for j in jobs if str(j['job_id'])=='3046779')
 invref={'path':job['invocation'],'sha256':job['invocation_sha256']}
 assert sha(R/invref['path'])==invref['sha256']=='94f108d569f8b35e5f14abe9c84dc03da38b5f0d1ad311f0fb293fcbf0e4dd4f'
 inv=json.loads((R/invref['path']).read_text())
 pr={'path':'results/formal_main_v2/pulls/20261020T063613Z_083e58f82fa4/receipt.json','sha256':'3d76d0eb99b1418c6a64974e3f7b84d5636f04005880ce8d4a5ff86b530547e3'}
 reviewer=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root_actual_long0626')
 try:
  result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pr,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
  assert result['status']=='passed' and result['scientific_complete'] is True
  rr=write('results/formal_main_v2/downstream_reviews/3046779.json',result)
  sr=write(B+'/3046779_root_terminal.json',{'root_review':rr,'pull':pr,'terminal_jobs_snapshot':jr,'scientific_complete':True,'independent_review_integrated':False,'execution_version':result['execution_version'],'cost':result['cost'],'final_state_values_read':False,'final_release':False,'new_jobs':0})
  assert sha(sp)==ss
  print(json.dumps({'root_review':rr,'root_terminal':sr,'cost':result['cost'],'result_keys':list(result),'state_unchanged':True}),flush=True)
 except Exception as e:
  failure=write(B+'/3046779_root_review_failure_0626.json',{'status':'blocked_review','type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'pull':pr,'terminal_jobs_snapshot':jr,'state_unchanged':sha(sp)==ss,'new_jobs':0})
  print(json.dumps({'failure':failure}),flush=True)
  raise
