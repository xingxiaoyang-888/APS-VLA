"""One bounded existing-job terminal review. Never submits or updates state."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,os,sys,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0454'
PINS={'scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','scripts/pull_formal_results.py':'b1b141ddb75fd8641d6f5e7f68dbfea462e1fe907ced2f2a98338a1145d77061','scripts/ops/formal_action_deployment_v1/reviewer.py':'9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd','scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py':'873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb','scripts/ops/formal_spatial64s23_source_bridge_v1/control.py':'edab3f3917b57daf1867134bc8179a73673bfc4a1e61bfda5118d76fd64458f3','scripts/ops/formal_object64s23_source_bridge_v1/control.py':'cf1058afd83073e0ef30c977e88c34f124f56adcfe9487b837ecaedaf6578767'}
TARGETS={'3053875':('libero_spatial','bf18ea0e4c3f1782005f26195058dae9cc5e63c7c7b7e7f3434514293831fbb4'),'3053894':('libero_object','b9a415b055f6d3d46035e9c9d4d03302762699577bc53808a6f122c889cd824d')}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':str(p.relative_to(R)),'sha256':h(p)}
def load(rel):
 p=R/rel;need(h(p)==PINS[rel],'pinned source changed '+rel);sp=importlib.util.spec_from_file_location('_root2054_'+hashlib.sha256(rel.encode()).hexdigest()[:10],p);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m

def save(rel,data):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return ref(p)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--job-id',choices=list(TARGETS),required=True);args=ap.parse_args();jid=args.job_id;suite,invSHA=TARGETS[jid]
 need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R) and os.environ.get('CTI_SERVER_CONTROL_MANIFEST_SHA256')=='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149','pinned transport required')
 c=load('scripts/ops/formal_autonomous_training_v1/controller.py');g=load('scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  sp=R/'results/experiment_supervisor/state.json';before=sp.read_bytes();s=json.loads(before);need(s['pending_submission'] is None,'unresolved pending')
  found=[j for j in s['registered_jobs'] if j['job_id']==jid];need(len(found)==1,'unique registration required');original=found[0]
  need(original['experiment']=='formal_main_v2' and original['suite']==suite and original['mode']=='development' and original['method_ids']==['A64_seed23','B64_seed23'] and original['invocation_sha256']==invSHA,'exact existing pair identity')
  need(not (R/f'results/formal_main_v2/downstream_reviews/{jid}.json').exists(),'existing root terminal review: inspect prior proof, do not rerun')
  need(sum(j.get('stage_key')==original['stage_key'] for j in s['registered_jobs'])==1 and original['prior_job_ids']==[] and original['resume'] is False,'only first exact attempt')
  snap=c.Slurm().observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],snap,s['autonomous_training_v1']['controller_job_id'])
  need(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8,'registration/capacity anomaly')
  for j in s['registered_jobs']:g.check_observed_identity(j,snap['rows'][j['job_id']],snap['queue'].get(j['job_id']),c.TERMINAL)
  o=snap['rows'][jid];need(o['status']=='COMPLETED' and o['exit_code']=='0:0','target not cleanly terminal; no retry or new execution')
  jobs=[]
  for j in s['registered_jobs']:
   observed=snap['rows'][j['job_id']]
   if j.get('experiment')!='formal_main_v2' or observed['status'] not in c.TERMINAL:continue
   copyj=copy.deepcopy(j);copyj.update({k:observed[k] for k in ['status','exit_code','elapsed_seconds','allocation','node']});jobs.append(copyj)
  job=next(j for j in jobs if j['job_id']==jid)
  folder=B+'/terminal_'+jid;need(not (R/folder).exists(),'immutable terminal transaction already exists')
  evidence=save(folder+'/terminal_jobs_snapshot.json',{'schema':'formal_main_v2','registered_jobs':jobs,'source_state_sha256':hashlib.sha256(before).hexdigest(),'observation':snap,'capacity':cap,'target_job_id':jid,'excluded_nonterminal_or_nonformal_ids':[j['job_id'] for j in s['registered_jobs'] if j['job_id'] not in {x['job_id'] for x in jobs}]})
  try:
   puller=load('scripts/pull_formal_results.py');pull,path=puller.pull([jid],timeout=300)
   need(pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and not pull['weights_copied'] and not pull['sealed_initial_states_copied'] and not pull['missing'],'complete nonweight evidence required')
   need(pull['requested_job_ids']==[jid] and [j['job_id'] for j in pull['selected_jobs']]==[jid],'only exact existing output')
   pullref=ref(path);save(folder+'/pull.json',{'receipt':pullref,'files':len(pull['files']),'state_unchanged':True})
   original_reviewer=load('scripts/ops/formal_action_deployment_v1/reviewer.py');control=load('scripts/ops/formal_'+suite.replace('libero_','')+'64s23_source_bridge_v1/control.py')
   reviewer=control.reviewer_module(original_reviewer.Evidence(R));invref={'path':job['invocation'],'sha256':invSHA};need(h(R/invref['path'])==invSHA,'invocation drift')
   result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pullref,registered_jobs=jobs,expected_contract_ref=job['action_execution_contract'])
   need(result['status']=='passed' and result['scientific_complete'] is True and result['completed_trials']==200 and result['explicit_source_control']==control.descriptor(),'source-specific terminal review failed')
   need(result['cost']['current_gpu_seconds']==o['elapsed_seconds'] and result['cost']['all_attempt_gpu_seconds']==o['elapsed_seconds'] and [x['job_id'] for x in result['cost']['allocations']]==[jid],'allocation duplication')
   rr=save(f'results/formal_main_v2/downstream_reviews/{jid}.json',result)
   ev=original_reviewer.Evidence(R);consumer=control.consumer_module(ev);rebuilt=consumer.review_downstream_output(ev,rr,expected_stage='development',suite=suite,run_root=job['run_root'],require_complete=True)
   clean=lambda r:{k:v for k,v in r.items() if k!='reviewed_utc'}
   need(clean(rebuilt)==clean(result),'source-specific consumer did not exactly reconstruct');ev.unchanged()
   out=save(folder+'/completion.json',{'schema':'formal_main_v2','kind':'root_existing_k64seed23_terminal_review','status':'root_and_original_consumer_passed_independent_pending','job_id':jid,'suite':suite,'root_review':rr,'pull':pullref,'snapshot':evidence,'source_control':control.descriptor(),'source_pins':PINS,'full_consumer_rebuilt':True,'completed_trials':200,'unique_development_initial_states':100,'successes':{k:v['successes'] for k,v in result['reconstructed_summary']['methods'].items()},'cost':result['cost'],'new_GPU_jobs':0,'accepted_new_trials':0,'state_unchanged':True,'final_release':False})
   need(sp.read_bytes()==before,'root terminal review cannot mutate state');print(json.dumps({'completion':out,'root_review':rr,'successes':{k:v['successes'] for k,v in result['reconstructed_summary']['methods'].items()},'cost':result['cost']},ensure_ascii=False))
  except BaseException as error:
   save(folder+'/failure.json',{'status':'terminal_review_blocked','exception':type(error).__name__,'error':str(error),'traceback':traceback.format_exc(),'state_unchanged':sp.read_bytes()==before,'accepted_new_trials':0,'new_GPU_jobs':0,'automatic_retry':False});raise
if __name__=='__main__':main()
