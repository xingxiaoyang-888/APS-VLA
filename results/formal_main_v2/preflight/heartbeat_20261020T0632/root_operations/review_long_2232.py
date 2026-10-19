from pathlib import Path
import hashlib,importlib.util,json,sys,traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261020T0632'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert sha(p)==pin;spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def ref(p):return {'path':p.relative_to(R).as_posix(),'sha256':sha(p)}
def write(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','root_long_review2232_ctl')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';ss=sha(sp)
 jr={'path':B+'/3043709_terminal_jobs_snapshot.json','sha256':'509955f1a0d3650bcc42cf317b81f83dd88a8e7cd08a52f3029785cb36f14f6b'}
 assert sha(R/jr['path'])==jr['sha256']
 jobs=json.loads((R/jr['path']).read_text())['registered_jobs'];job=next(j for j in jobs if str(j['job_id'])=='3043709')
 invref={'path':job['invocation'],'sha256':job['invocation_sha256']}
 assert sha(R/invref['path'])==invref['sha256']=='2bf41d87718038e41f35d52b90506a3e973a7270869278157fb953d8238a7f84'
 inv=json.loads((R/invref['path']).read_text())
 pr={'path':'results/formal_main_v2/pulls/20261019T223821Z_c4b67281fa45/receipt.json','sha256':'ed05968d82ceb14d333990099496d32aa0fdaf40f7217525636d10ec113f132e'}
 reviewer=mod('scripts/ops/formal_action_deployment_v1/reviewer.py','9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','root_actual_long2232')
 try:
  result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pr,registered_jobs=jobs,expected_contract_ref=inv['action_execution_contract'])
  assert result['status']=='passed' and result['scientific_complete'] is True
  rr=write('results/formal_main_v2/downstream_reviews/3043709.json',result)
  sr=write(B+'/3043709_root_terminal.json',{'root_review':rr,'pull':pr,'terminal_jobs_snapshot':jr,'scientific_complete':True,'independent_review_integrated':False,'execution_version':result['execution_version'],'cost':result['cost'],'final_state_values_read':False,'final_release':False,'new_jobs':0})
  assert sha(sp)==ss
  print(json.dumps({'root_review':rr,'root_terminal':sr,'cost':result['cost'],'result_keys':list(result),'state_unchanged':True}),flush=True)
 except Exception as e:
  failure=write(B+'/3043709_root_review_failure.json',{'status':'blocked_review','type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc(),'pull':pr,'terminal_jobs_snapshot':jr,'state_unchanged':sha(sp)==ss,'new_jobs':0})
  print(json.dumps({'failure':failure}),flush=True)
  raise
