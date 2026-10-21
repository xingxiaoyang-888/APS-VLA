"""Consume an already saved clean terminal observation for Spatial3054201; never submits."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
PINS={'scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','scripts/pull_formal_results.py':'b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','scripts/ops/formal_spatial588_predispatch_v1/control.py':'e2e7c3fe7f6dcf4f63b4550c3f5bc8ec50a05aaf462b38ed961ce356cc414683'}
JID='3054201';ISHA='8a9d19ca0c1c099a6837c3f19123a031db5e57f0b3596f9d4031ce39e23d0e3e'
def need(v,m):
 if not v:raise ValueError(m)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
def load(rel):
 p=R/rel;need(h(p)==PINS[rel],'source pin '+rel);sp=importlib.util.spec_from_file_location('_spatial_terminal0110_'+hashlib.sha256(rel.encode()).hexdigest()[:10],p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
def save(rel,data):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
ap=argparse.ArgumentParser();ap.add_argument('--terminal-observation',required=True);ap.add_argument('--terminal-observation-sha256',required=True);a=ap.parse_args()
p=R/a.terminal_observation;need(p.resolve()==p and p.is_file() and not p.is_symlink() and h(p)==a.terminal_observation_sha256,'exact saved root observation required')
need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R),'server transport required');live=json.loads(p.read_bytes());snap=live['observation'];o=snap['rows'][JID]
need(o['status']=='COMPLETED' and o['exit_code']=='0:0' and o['gpus']==1,'saved target is not cleanly terminal; do not pull or poll')
c=load('scripts/ops/formal_autonomous_training_v1/controller.py')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=sp.read_bytes();s=json.loads(before)
 need(hashlib.sha256(before).hexdigest()==live['state_sha256'] and s['pending_submission'] is None,'saved registration/CAS differs or unresolved pending')
 cap=c.capacity(s['registered_jobs'],snap,'3034538');need(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8,'saved capacity anomaly')
 job0=next(j for j in s['registered_jobs'] if str(j['job_id'])==JID)
 need(job0['invocation_sha256']==ISHA and job0['suite']=='libero_spatial' and job0['mode']=='development' and job0['prior_job_ids']==['3022743','3042529'] and job0['resume'] is True,'exact spatial attempt03 only')
 need(not (R/f'results/formal_main_v2/downstream_reviews/{JID}.json').exists(),'root review already exists, do not overwrite/repeat')
 jobs=[]
 for j in s['registered_jobs']:
  v=snap['rows'][str(j['job_id'])]
  if j.get('experiment')!='formal_main_v2' or v['status'] not in c.TERMINAL:continue
  q=copy.deepcopy(j);q.update({k:v[k] for k in ['status','exit_code','elapsed_seconds','allocation','node']});jobs.append(q)
 job=next(j for j in jobs if str(j['job_id'])==JID);folder=B+'/Spatial3054201_terminal'
 need(not (R/folder).exists(),'terminal transaction exists')
 sr=save(folder+'/terminal_jobs_snapshot.json',{'schema':'formal_main_v2','registered_jobs':jobs,'source_state_sha256':hashlib.sha256(before).hexdigest(),'terminal_observation':ref(p),'target_job_id':JID})
 try:
  puller=load('scripts/pull_formal_results.py');pull,path=puller.pull([JID],timeout=300)
  need(pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and not pull['weights_copied'] and not pull['sealed_initial_states_copied'] and not pull['missing'],'complete nonweight terminal pull required')
  need(pull['requested_job_ids']==[JID] and [j['job_id'] for j in pull['selected_jobs']]==[JID],'only exact target pull')
  pullref=ref(path);save(folder+'/pull.json',{'receipt':pullref,'files':len(pull['files']),'state_unchanged':True})
  rawreview=load('scripts/ops/formal_action_deployment_v1/reviewer.py');control=load('scripts/ops/formal_spatial588_predispatch_v1/control.py');reviewer=control.reviewer_module(rawreview.Evidence(R));iv={'path':job['invocation'],'sha256':ISHA}
  result=reviewer.review(R,job=job,invocation_ref=iv,pull_ref=pullref,registered_jobs=jobs,expected_contract_ref=job['action_execution_contract'])
  need(result['status']=='passed' and result['scientific_complete'] is True and result['completed_trials']==result['expected_trials']==600,'full600 review required')
  line=result['execution_lineage'];need(line['original_legacy_prefix_trials']==12 and line['new_action_trials']==588 and line['original_prefix_preserved'] is True and line['eligible_for_current_action_global_freeze'] is False,'legacy/current lineage lost')
  cost=result['cost'];need(cost['current_gpu_seconds']==o['elapsed_seconds'] and cost['all_attempt_gpu_seconds']==o['elapsed_seconds']+395 and [str(v['job_id']) for v in cost['allocations']]==['3022743','3042529',JID],'unique allocation costs or pre-dispatch2sec lost')
  rr=save(f'results/formal_main_v2/downstream_reviews/{JID}.json',result)
  ev=rawreview.Evidence(R);consumer=control.consumer_module(ev);rebuilt=consumer.review_downstream_output(ev,rr,expected_stage='development',suite='libero_spatial',run_root=job['run_root'],require_complete=True)
  clean=lambda v:{k:x for k,x in v.items() if k!='reviewed_utc'};need(clean(rebuilt)==clean(result),'original typed consumer did not reconstruct');ev.unchanged()
  end=save(folder+'/completion.json',{'schema':'formal_main_v2','status':'root_and_typed_consumer_passed_independent_pending','job_id':JID,'root_review':rr,'pull':pullref,'snapshot':sr,'source_pins':PINS,'completed_trials':600,'legacy_compatible_trials':12,'current_wrapper_trials':588,'unique_initial_states':100,'cost':cost,'successes':{k:v['successes'] for k,v in result['reconstructed_summary']['methods'].items()},'accepted_new_trials':0,'new_GPU_jobs':[],'state_unchanged':True,'final_release':False,'profiling_authorized':False})
  need(sp.read_bytes()==before,'state changed');print(json.dumps({'completion':end,'root_review':rr,'cost':cost}))
 except BaseException as e:
  save(folder+'/failure.json',{'status':'terminal_review_blocked','error':str(e),'type':type(e).__name__,'traceback':traceback.format_exc(),'state_unchanged':sp.read_bytes()==before,'accepted_new_trials':0,'new_GPU_jobs':[],'automatic_retry':False});raise
