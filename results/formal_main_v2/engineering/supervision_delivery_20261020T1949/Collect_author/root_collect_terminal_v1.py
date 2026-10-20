"""Root-only existing collect pull + original review + original consumer transaction.
No training, Slurm mutation, state update, cost addition, timing or final release.
This candidate must be reviewed and then invoked by root through pinned transport.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,os,sys,traceback
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/collect_terminal_20261020T1949'
CHECKS_SHA='737ef40d686992a3adb22d872a2cfead6d74492a986dfe712a57e7bf63a5d276'
B='results/formal_main_v2/preflight/heartbeat_20261021T0349/collect_terminal'
BUNDLE='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'
def core():
 p=D/'checks_v1.py'
 if hashlib.sha256(p.read_bytes()).hexdigest()!=CHECKS_SHA:raise ValueError('checks source pin differs')
 spec=importlib.util.spec_from_file_location('root_collect_terminal_checks_1949',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def execute(c):
 c.need(os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R) and os.environ.get('CTI_SERVER_CONTROL_MANIFEST_SHA256')==BUNDLE,'pinned server transport required')
 value=c.inputs();sources=value['sources']
 controller=c.load('scripts/ops/formal_autonomous_training_v1/controller.py',sources['scripts/ops/formal_autonomous_training_v1/controller.py'],'root_collect_terminal_controller_1949')
 with controller.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  state_path=R/'results/experiment_supervisor/state.json';before=state_path.read_bytes();state=json.loads(before);before_sha=hashlib.sha256(before).hexdigest()
  expected={j['job_id']:j for j in value['selected_registered_jobs']}
  actual={}
  for jid in c.JOB_IDS:
   found=[j for j in state['registered_jobs'] if str(j.get('job_id'))==jid]
   c.need(len(found)==1,'unique target registration');c.validate_job(found[0],expected[jid]);actual[jid]=found[0]
   c.need([j['job_id'] for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('stage_key')==found[0]['stage_key']]==[jid],'no hidden prior or duplicate collect attempt')
   c.need(not (R/f'results/formal_main_v2/downstream_reviews/{jid}.json').exists(),'root review already exists; inspect prior transaction instead of replay')
  output=R/B;c.need(not output.exists(),'non-reentrant root transaction output already exists');output.mkdir(parents=True,exist_ok=False)
  start=dict(schema='formal_main_v2',kind='root_existing_collect_terminal_intent',utc=datetime.now(timezone.utc).isoformat(),job_ids=list(c.JOB_IDS),source_state_sha256=before_sha,input_inventory={'path':str((D/'inputs.json').relative_to(R)),'sha256':c.INPUT_SHA},helper={'path':str(Path(__file__).relative_to(R)),'sha256':c.sha(__file__)},checks={'path':str((D/'checks_v1.py').relative_to(R)),'sha256':CHECKS_SHA},scientific_trials_added=0,cost_increment_gpu_seconds=0,allocation_cost_already_accounted=True,new_jobs=0,final_release=False)
  c.write(output/'intent.json',start)
  try:
   # The unchanged puller internally inventories all registered jobs to exclude
   # overlapping active writers; only the exact two requested outputs transfer.
   puller=c.load('scripts/pull_formal_results.py',sources['scripts/pull_formal_results.py'],'root_collect_terminal_original_puller_1949')
   c.need(puller.ROOT==R and puller.P==str(c.P),'original puller derives real server roots, no F assertion patch')
   jobs=[j for j in state['registered_jobs'] if j.get('experiment')=='formal_main_v2' and j.get('status') in puller.TERMINAL]
   c.need(all(actual[jid] in jobs for jid in c.JOB_IDS),'target immutable terminal snapshot')
   c.validate_files(value,c.P)
   pull,path=puller.pull(list(c.JOB_IDS),timeout=300)
   c.need(pull['status']=='verified_nonweight_snapshot' and pull['final_evidence'] is True and not pull['missing'] and not pull['excluded'] and not pull['skipped'],'complete original nonweight transfer')
   c.need(pull['requested_job_ids']==list(c.JOB_IDS) and sorted(j['job_id'] for j in pull['selected_jobs'])==list(c.JOB_IDS),'only two requested jobs pulled')
   expected_files={x['relative']:(x['sha256'],x['bytes']) for x in value['output_files']}
   c.need(len(pull['files'])==len(expected_files) and {x['relative']:(x['sha256'],x['bytes']) for x in pull['files']}==expected_files,'pulled bytes match original pinned inventory')
   for jid in c.JOB_IDS:
    row=pull['accounting_after']['jobs'][jid];job=actual[jid]
    c.need(all(row[k]==job[k] for k in ('status','exit_code','elapsed_seconds','allocation','node')),'real terminal accounting equals immutable job')
   pullref={'path':str(path.relative_to(R)),'sha256':c.sha(path)}
   snapshot=c.write(output/'terminal_jobs_snapshot.json',dict(schema='formal_main_v2',kind='immutable_terminal_formal_job_snapshot',source_state_sha256=before_sha,registered_jobs=jobs,reason='Original suite acceptance/source provenance requires complete terminal registration; only two collect outputs reviewed'))
   raw=c.inspect_raw(value,R);rawref=c.write(output/'root_raw_observations.json',raw)
   allowref=c.write(output/'observation_npz_delivery_allowlist.json',dict(schema='formal_main_v2',kind='exact_nonweight_original_collect_NPZ_allowlist',job_ids=list(c.JOB_IDS),files=raw['observation_npz_allowlist'],total_bytes=raw['total_original_npz_bytes'],new_scientific_trials=0,sealed_values=False,weights=False))
   reviewer=c.load('scripts/ops/formal_action_deployment_v1/reviewer.py',sources['scripts/ops/formal_action_deployment_v1/reviewer.py'],'root_collect_terminal_original_reviewer_1949')
   consumer=c.load('scripts/ops/formal_action_deployment_v1/consumer.py',sources['scripts/ops/formal_action_deployment_v1/consumer.py'],'root_collect_terminal_original_consumer_1949')
   accepted=[]
   for jid in c.JOB_IDS:
    job=actual[jid];invref={'path':job['invocation'],'sha256':job['invocation_sha256']};inv=c.read(R/invref['path'])
    result=reviewer.review(R,job=job,invocation_ref=invref,pull_ref=pullref,registered_jobs=jobs,expected_contract_ref=job['action_execution_contract'])
    c.need(result['status']=='passed' and result['scientific_complete'] is True and result['stage']=='collect' and result['observations']==30 and result['completed_collection_trajectories']==10 and result['unfinished_attempts_unknown_cost']==0,'original collector review requires full fixed30 panel')
    c.need(result['cost']['current_gpu_seconds']==job['elapsed_seconds'] and result['cost']['all_attempt_gpu_seconds']==job['elapsed_seconds'] and [x['job_id'] for x in result['cost']['allocations']]==[jid],'exact one allocation, no repeated cost')
    rr=c.write(R/f'results/formal_main_v2/downstream_reviews/{jid}.json',result)
    evidence=reviewer.Evidence(R)
    rebuilt=consumer.review_downstream_output(evidence,rr,expected_stage='collect',suite=job['suite'],run_root=job['run_root'],require_complete=True)
    clean=lambda x:{k:v for k,v in x.items() if k!='reviewed_utc'}
    c.need(clean(rebuilt)==clean(result),'original consumer exact reconstruction');evidence.unchanged()
    proof=c.write(output/f'{jid}_original_consumer_reconstruction.json',dict(schema='formal_main_v2',kind='root_original_collect_consumer_reconstruction',status='passed',root_review=rr,invocation=invref,pull=pullref,terminal_jobs_snapshot=snapshot,reviewer_source={'path':'scripts/ops/formal_action_deployment_v1/reviewer.py','sha256':sources['scripts/ops/formal_action_deployment_v1/reviewer.py']},consumer_source={'path':'scripts/ops/formal_action_deployment_v1/consumer.py','sha256':sources['scripts/ops/formal_action_deployment_v1/consumer.py']},rebuilt_equal_except_reviewed_utc=True,canonical_rebuilt_without_time_sha256=c.sig(clean(rebuilt)),evidence_sha256=rebuilt['evidence_sha256'],actual_runtime_review=rebuilt['actual_runtime_review'],cost=rebuilt['cost'],cost_increment_gpu_seconds=0,independent_review_pending=True,new_scientific_trials=0,final_release=False))
    accepted.append(dict(job_id=jid,suite=job['suite'],root_review=rr,consumer_reconstruction=proof,observations=30,new_scientific_trials=0,allocation_gpu_seconds=job['elapsed_seconds'],cost_increment_gpu_seconds=0))
   c.validate_files(value,c.P);c.validate_files(value,R)
   c.need(state_path.read_bytes()==before,'supervisor state changed during root evidence-only transaction')
   receipt=c.write(output/'completion.json',dict(schema='formal_main_v2',kind='root_collect_terminal_evidence_delivery',status='passed_original_review_and_consumer',job_ids=list(c.JOB_IDS),reviewed=accepted,pull=pullref,terminal_jobs_snapshot=snapshot,root_raw_validation=rawref,npz_allowlist=allowref,files=len(pull['files']),original_npz_files=60,original_npz_bytes=raw['total_original_npz_bytes'],source_state_sha256=before_sha,state_unchanged=True,new_jobs=0,new_scientific_trials=0,cost_increment_gpu_seconds=0,all_allocations_previously_accounted=True,independent_review_pending=True,O2A_or_components=False,final_release=False))
   print(json.dumps({'completion':receipt,'reviewed':accepted,'new_scientific_trials':0,'state_unchanged':True},ensure_ascii=False))
  except BaseException as exc:
   failure=c.write(output/'failure.json',dict(status='blocked_collect_terminal_review',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),source_state_sha256=before_sha,state_unchanged=state_path.read_bytes()==before,new_jobs=0,new_scientific_trials=0,cost_increment_gpu_seconds=0,retry_automatic=False,partial_outputs_preserved=True))
   print(json.dumps({'failure':failure}),flush=True);raise
  finally:c.need(state_path.read_bytes()==before,'root helper must never mutate supervisor state')

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root-execute-existing-collect-terminal',action='store_true',required=True);ap.parse_args();execute(core())
if __name__=='__main__':main()
