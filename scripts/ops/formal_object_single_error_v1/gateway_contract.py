"""Exact gateway contract, without a Slurm submit implementation or mutation."""
import re,json
from datetime import datetime,timezone
import fixed as F
import constants as C

MODE='object_single_error_linked'
NAME='cti_object_linked_t8s49d1'
TERMINAL={'COMPLETED','FAILED','TIMEOUT','PREEMPTED','CANCELLED','NODE_FAIL','OUT_OF_MEMORY'}
ACTIVE={'PENDING','RUNNING','CONFIGURING','COMPLETING','SUSPENDED','RESIZING','REQUEUED'}
FIELDS=('job_name','slurm_comment','account','partition','slurm_output')
def token(plan):
 return F.sig(dict(scope_sha256=F.SCOPE_SHA,plan_sha256=F.sig(plan),old_failure=F.RESULT,
  attempt=1,output=F.OUT,mode=MODE))
def duplicate(row):
 # Even a corrupt/incomplete terminal record is a permanent blocker.
 return (row.get('mode')==MODE or row.get('logical_trial_id')==F.CELL
  or row.get('stage_key')==C.STAGE_KEY or row.get('linked_failure_sha256')==F.RESULT['sha256']
  or row.get('run_root') in (F.OUT,str(F.P/F.OUT))
  or row.get('job_name')==NAME
  or str(row.get('slurm_comment','')).startswith('cti-object-single-error:'))
def validate_identity(record,actual):
 F.require(record.get('job_id')==actual.get('job_id') and str(actual.get('job_id','')).isdigit(),'Slurm/registration job ID differs')
 for field in FIELDS:
  F.require(type(record.get(field)) is str and bool(record[field]) and actual.get(field)==record[field],
   'actual Slurm/registered '+field+' differs')
 F.require(actual.get('gpus')==record.get('gpus')==1,'one actual registered GPU per job')
 F.require(actual.get('state') in ACTIVE|TERMINAL,'unknown actual Slurm state blocks')
 return actual
def inspect_snapshot(snapshot,plan,*,now=None):
 required={'schema','kind','observed_utc','state_sha256','state','state_raw','registered_projection','slurm_projection',
  'query_receipt','writer_lock_path','expected_state_sha256','reserved_gpu_slots','output_exists','attempt_claim_exists'}
 F.require(set(snapshot)==required and snapshot['kind']=='Object_single_error_pre_submission_snapshot','complete fresh normalized snapshot required')
 F.require(json.loads(snapshot['state_raw'])==snapshot['state'] and F.sha(snapshot['state_raw'].encode())==snapshot['state_sha256']==snapshot['expected_state_sha256'],'actual state/CAS snapshot differs')
 F.require(snapshot['writer_lock_path']=='results/experiment_supervisor/.writer.lock','shared writer lock required')
 t=datetime.fromisoformat(snapshot['observed_utc'].replace('Z','+00:00'));current=now or datetime.now(timezone.utc)
 F.require(0<=(current-t).total_seconds()<=30,'fresh all-mode Slurm snapshot required')
 F.require(snapshot['query_receipt'].get('status')=='complete' and snapshot['query_receipt'].get('unknown_ids')==[]
  and re.fullmatch('[0-9a-f]{64}',snapshot['query_receipt'].get('raw_sha256','')),'unknown or partial Slurm query blocks')
 state=snapshot['state']
 for key,value in state.items():
  if 'pending' in key.lower():F.require(value in (None,{},[]),'unreconciled root pending blocks')
 auto=state.get('autonomous_training_v1',{})
 terminal=auto.get('root_confirmed_normal_training_exit',{})
 F.require(auto.get('pending_submission') in (None,{}) and auto.get('controller_job_id')=='3034538'
  and all(terminal.get(k)==v for k,v in dict(controller_job_id='3034538',status='COMPLETED',exit_code='0:0',
   lease_released=True,restart_needed=False,training_arms=72,training_pairs=36).items()),'actual registered controller terminal schema required')
 controller=[r for r in state.get('registered_jobs',[]) if str(r.get('job_id'))=='3034538']
 F.require(len(controller)==1 and controller[0].get('mode')=='controller' and controller[0].get('status')=='COMPLETED'
  and controller[0].get('exit_code')=='0:0' and controller[0].get('gpus')==0,'original controller allocation must be terminal')
 # This is a read-only projection contract, not a lease acquisition or proof.
 # A future separately reviewed atomic gateway must independently probe the real
 # lifecycle lease and global pending/ACK journal under the shared writer lock.
 records=snapshot['registered_projection'];actual=snapshot['slurm_projection']
 F.require(type(records) is list and type(actual) is list,'complete normalized register and Slurm projections required')
 F.require(not any(duplicate(r) for r in records+actual),'prior or incompletely recorded linked attempt forbids any resubmission')
 F.require(not snapshot['output_exists'] and not snapshot['attempt_claim_exists'],'preexisting output or execution claim forbids retry')
 by={r['job_id']:r for r in records};F.require(len(by)==len(records),'duplicate registered job IDs')
 observed={r['job_id']:r for r in actual};F.require(len(observed)==len(actual),'duplicate Slurm IDs')
 required_ids={r['job_id'] for r in records if r.get('status') not in TERMINAL}
 F.require(required_ids==set(observed),'unmatched/missing/unknown active CTI allocations block')
 gpu=0
 for jid,row in observed.items():
  validate_identity(by[jid],row);F.require(row['state'] in ACTIVE,'stale terminal must be reconciled before submit')
  F.require(by[jid].get('pair_id')!=F.PAIR,'same scientific pair already active')
  gpu+=row['gpus']
 reserved=snapshot['reserved_gpu_slots'];F.require(type(reserved) is int and 0<=reserved<=8,'reserved capacity invalid')
 F.require(gpu+reserved<8,'all modes plus reservation already use8slots')
 return dict(schema='formal_main_v2',kind='Object_single_error_pre_submission_contract',status='checked_no_submit',
  mode=MODE,logical_trial_id=F.CELL,pair_id=F.PAIR,stage_key=C.STAGE_KEY,
  output=F.OUT,submission_token=token(plan),slurm_comment='cti-object-single-error:'+token(plan),
  job_name=NAME,active_GPU_slots=gpu,reserved_GPU_slots=reserved,next_GPU_slots=gpu+reserved+1,
  observed_utc=snapshot['observed_utc'],expected_state_sha256=snapshot['state_sha256'],
  atomic_gateway_implementation_missing=True,live_controller_lease_probe_missing=True,submit_authorized=False)

def bound_registration(invocation,state,*,job_id,invocation_sha256):
 rows=[r for r in state.get('registered_jobs',[]) if str(r.get('job_id'))==job_id]
 F.require(len(rows)==1,'exactly one root registered actual job required')
 row=rows[0]
 F.require(type(invocation_sha256) is str and re.fullmatch('[0-9a-f]{64}',invocation_sha256)
  and row.get('invocation_sha256')==invocation_sha256,'actual immutable invocation bytes differ from root registration')
 expected=dict(mode=MODE,stage_key=C.STAGE_KEY,logical_trial_id=F.CELL,pair_id=F.PAIR,
  run_root=str(F.P/F.OUT),linked_failure_sha256=F.RESULT['sha256'],gpus=1,
  invocation=C.INVOCATION,submission_token=invocation['submission_token'])
 F.require(all(row.get(k)==v for k,v in expected.items()),'typed root registration differs')
 F.require(row.get('status') in ACTIVE|{'SUBMITTED'},'terminal or unknown registration cannot execute')
 for field in FIELDS:F.require(row.get(field)==invocation[field] and bool(row[field]),'bound actual submission identity differs')
 F.require(row['submission_token']==token(C.read_ref(F.P,invocation['plan'],path=C.PLAN))
  and row['job_name']==NAME and row['slurm_comment']=='cti-object-single-error:'+row['submission_token'],'token/comment/actual exact plan differ')
 F.require(not any(duplicate(r) for r in state.get('registered_jobs',[]) if str(r.get('job_id'))!=job_id),
  'another partial/terminal same linked attempt exists')
 F.require(row.get('original_sbatch_ACK')==job_id+'\n' and row.get('ACK_reconciled_by_token_comment') is True,
  'unique actual sbatch ACK/token/comment reconciliation required')
 return row

def submit(*args,**kwargs):
 raise RuntimeError('HOLD: this package deliberately has no atomic Slurm gateway; root must integrate and independently review one exact gateway')
