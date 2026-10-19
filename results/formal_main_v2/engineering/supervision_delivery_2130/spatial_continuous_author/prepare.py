"""Private Spatial1500 continuation preparation. Never authorize, submit or mutate state."""
import argparse, copy, hashlib, importlib.util, json, sys, traceback
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
GATEWAY_SHA='71af9cf0bce935d00934db8c8198f7f9624fd7194f570e36efd95f77da0634c6'
raw=(HERE/'gateway.py').read_bytes()
if hashlib.sha256(raw).hexdigest()!=GATEWAY_SHA:raise ValueError('candidate gateway SHA')
spec=importlib.util.spec_from_file_location('spatial2130_gateway',HERE/'gateway.py')
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);a=g.a

def save(name,value):
 p=HERE/name
 if p.resolve().parent!=HERE:raise ValueError('private flat output only')
 raw=a.canonical(value)
 with p.open('xb') as f:f.write(raw)
 return {'path':p.relative_to(R).as_posix(),'sha256':a.digest(raw),'bytes':len(raw)}

def draft(refs):
 return dict(schema='formal_main_v2',kind='root_cuda_recovered_continuous_admission_authorization',version=a.VERSION,
  status='draft_not_authorized',reviewed_by=None,pair_key=a.PAIR,failed_job_id='3028522',recovery_job_id='3043399',
  completed_before={'A':1500,'B':1500},cursor_before={'A':12000,'B':12000},historical_GPU_seconds=11958,target_updates_per_arm=5000,
  resume=True,single_new_attempt=True,automatic_retry=False,soft_wall_seconds=169200,allocation_time='48:00:00',
  excluded_nodes=['gpu4020'],preserve_existing_reservations=True,consume_reservation=False,controller_admission_changed=False,
  scientific_settings_changed=False,final_release_authorized=False,control_root=str(a.R),runtime_root=str(a.P),source_sha256=a.SOURCE_SHA,
  controller_activation=a.ACTIVATION,normal_execution_authorization=a.AUTHORIZATION,node_exclusion=a.NODE,gateway_files=g.source_files(),
  reviewer_publication={a.REVIEWER:a.REVIEWER_SHA,a.FAILURE:a.FAILURE_SHA},controller_job_id='3034538',independent_review=None,**refs)

def prepare(refs,*,label):
 if not label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in label):raise ValueError('label')
 a.proof_refs(refs)
 auth=draft(refs)
 authref=save('authorization_'+label+'_draft.json',auth)
 # The draft is only an input provenance marker; no authorization is validated.
 marker={'path':authref['path'],'sha256':authref['sha256']}
 c=g.load(R/g.CONTROLLER,g.CONTROLLER_SHA,'spatial2130_controller')
 with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
  before=c.file_sha(R/a.STATE);state=c.read_json(R/a.STATE)
  if c.file_sha(R/a.STATE)!=before:raise ValueError('state changed during observation')
  rows=a.history(state)
  science=a.Science(R);plan=science.prepare(state,auth,marker)
  native=a.NativeIO().preflight(plan)
  if c.file_sha(R/a.STATE)!=before:raise ValueError('state changed during private preparation')
  science.e.unchanged()
  result=dict(schema='formal_main_v2',kind='spatial_continuous_candidate_actual_preparation',
   status='passed_raw_and_server_metadata_only_pending_independent_and_root_admission',pair_key=a.PAIR,
   original_target_recovery=refs,completed_before={'A':1500,'B':1500},cursor_before={'A':12000,'B':12000},
   historical_GPU_seconds=11958,failed_allocation_GPU_seconds=73,full_registry_entries_observed=len(state['registered_jobs']),
   pair_rows=rows,controller_observation={k:state['autonomous_training_v1'].get(k) for k in
    ('activation','controller_job_id','owner_id','reserved_GPU_slots','reservation_root_record','root_submission_hold')},
   blocked_pair_preserved=copy.deepcopy(state['autonomous_training_v1']['blocked_pairs'].get(a.PAIR)),
   plan=plan,server_metadata=native,read_evidence_sha256=science.e.hashes,
   authorization_draft=authref,authorization_validated=False,capacity_or_Slurm_queried=False,
   GPU_submitted=False,state_changed=False,new_trials=0,weights_deserialized=False,
   limitations=['This actual read-only preparation is not a root continuation authorization.',
    'Current capacity/owner lease and full Slurm facts must pass the unchanged locked gateway at future submission.',
    'All reservations and the retained FAILED allocation remain; no autonomous block is cleared.',
    'New softwall/failure is not automatically retried; terminal5000 needs startup-aware raw review and actual selected bytes.'])
 ref=save('actual_prepare_'+label+'.json',result)
 print(json.dumps({'status':result['status'],'receipt':ref,'completed':result['completed_before'],'cost':11958,
   'server_files':len(native['server_files']),'resume_files':len(native['server_resume_checks'])}),flush=True)
 return result

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--root-review',required=True);p.add_argument('--root-review-sha256',required=True)
 p.add_argument('--independent-review',required=True);p.add_argument('--independent-review-sha256',required=True)
 p.add_argument('--pull',required=True);p.add_argument('--pull-sha256',required=True);p.add_argument('--label',required=True)
 args=p.parse_args()
 refs={'root_recovery_review':{'path':args.root_review,'sha256':args.root_review_sha256},
       'independent_recovery_review':{'path':args.independent_review,'sha256':args.independent_review_sha256},
       'terminal_pull':{'path':args.pull,'sha256':args.pull_sha256},'canonical_failure_review':a.FAILURE_REVIEW}
 prepare(refs,label=args.label)
if __name__=='__main__':
 try:main()
 except Exception:traceback.print_exc();raise
