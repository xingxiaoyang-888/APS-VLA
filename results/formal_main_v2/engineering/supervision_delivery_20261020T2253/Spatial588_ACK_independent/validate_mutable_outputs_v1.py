"""Read-only post-ACK identity validation for exactly Spatial588 job 3054201.
No scientific acceptance, output copying, scheduler access, or state mutation.
The old R proof stays byte exact; only two known P outputs may have progressed.
"""
from pathlib import Path
import copy,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
REL='results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'
JOB='3054201'
PINS={
 'trials.jsonl':{'bytes':592887,'sha256':'3a175dbc5dd7a23cd2c3c8385cb6ff3c525f09d4e607ff32a69a10869672a2f9'},
 'closed_loop_report.json':{'bytes':29737,'sha256':'f21c2e9d60ff246e51dbd4a04f09c147d49b94f9db8b9264bd0cb288fa0a1c9d'},
 'config.json':{'bytes':19373,'sha256':'41458e92e1b4f8d6ef7ca3230c5154c9b87c83d107ca51c334ad8850018f699d'},
 'panel.json':{'bytes':222649,'sha256':'07718b648bfb767472506c48b0ef1837a5e6af992c2460e7567c275064809c91'}}
MUTABLE_ABSOLUTES=frozenset(str(P/REL/n) for n in ['trials.jsonl','closed_loop_report.json'])
def digest(b):return hashlib.sha256(b).hexdigest()
def record(b):return {'bytes':len(b),'sha256':digest(b)}
def require(ok,message):
 if not ok:raise ValueError(message)
def validate_snapshots(old,new):
 require(set(old)==set(PINS) and set(new)==set(PINS),'exact four evidence files required')
 for name,pin in PINS.items():require(record(old[name])==pin,'old R proof identity:'+name)
 for name in ['config.json','panel.json']:require(new[name]==old[name],'immutable P identity:'+name)
 config=json.loads(old['config.json']);panel=json.loads(old['panel.json'])
 old_report=json.loads(old['closed_loop_report.json']);report=json.loads(new['closed_loop_report.json'])
 ledger=new['trials.jsonl'];prefix=old['trials.jsonl']
 require(ledger.startswith(prefix),'original 592887-byte ledger prefix changed')
 require(ledger.endswith(b'\n'),'in-flight partial JSONL line; stop, do not truncate')
 old_rows=[json.loads(line) for line in prefix.splitlines()]
 rows=[json.loads(line) for line in ledger.splitlines()]
 require(len(old_rows)==25 and sum(x.get('event')=='result' for x in old_rows)==12,'original twelve-result proof')
 require(rows[:25]==old_rows,'old rows exact')
 require(len(rows)>25,'new invocation marker not yet present')
 marker=rows[25]
 require(set(marker)=={'created_utc','event','run_signature','slurm_job_id'} and marker['event']=='invocation' and marker['slurm_job_id']==JOB and marker['run_signature']==old_rows[0]['run_signature'],'unique new invocation identity')
 require(sum(x.get('event')=='invocation' for x in rows)==2,'unexpected extra invocation')
 require(old_rows[0]['slurm_job_id']=='3022743','old executed job identity')
 methods=[x['identity']['method_id'] for x in config['manifest']['methods']]
 require(methods==['dense','uniform256','uniform128','uniform64','A128_seed17','B128_seed17'],'fixed six-method order')
 require(panel['suite']=='libero_spatial' and panel['split']=='development' and len(panel['states'])==100,'fixed 100-state development panel')
 expected=[(s,m) for s in panel['states'] for m in methods]
 # Validate every start/result identity, including the old twelve, without judging outcomes.
 stream=[x for x in rows if x['event']!='invocation'];cursor=0;active=False;new_results=0
 identity_keys=['trial_id','state_trial_id','initial_state_sha256','task_id','task_name','source_state_index','method','suite','split','environment_seed','runtime_seed','action_chunk','configured_wait_steps','run_signature']
 for row in stream:
  require(cursor<len(expected),'extra trial outside fixed 600 identities')
  state,method=expected[cursor]
  want={'trial_id':state['trial_id']+':'+method,'state_trial_id':state['trial_id'],'method':method,'suite':'libero_spatial','split':'development','environment_seed':0,'runtime_seed':17,'action_chunk':8,'configured_wait_steps':10,'run_signature':marker['run_signature']}
  want.update({k:state[k] for k in ['initial_state_sha256','task_id','task_name','source_state_index']})
  require(all(row.get(k)==want[k] for k in identity_keys),'trial identity or order changed at '+str(cursor))
  if not active:
   require(row['event']=='start','expected start')
   active=True
  else:
   require(row['event']=='result','expected result, duplicate start, or unknown event')
   if cursor>=12:new_results+=1
   cursor+=1;active=False
 require(cursor>=12 and cursor<=600 and new_results<=588,'bounded continuation')
 require(len(stream)==2*cursor+int(active),'start-result pairing')
 expected_provenance=copy.deepcopy(old_report['provenance'])
 expected_provenance['runtime']['slurm_job_id']=JOB
 require(report['provenance']==expected_provenance,'report provenance changed beyond exact new Slurm identity')
 for key in ['schema','kind','expected_trials','inference_unit','split','suite','test_opened','unique_initial_states']:
  require(report[key]==old_report[key],'report immutable field:'+key)
 require(report['suite']=='libero_spatial' and report['split']=='development' and report['test_opened'] is False and report['expected_trials']==600,'report development identity')
 # Read report before ledger: a valid in-progress report may lag the ledger.
 require(type(report['completed_trials']) is int and 12<=report['completed_trials']<=cursor,'report count not bounded by observed result prefix')
 require(report['status']=='incomplete','terminal report requires a separate root terminal reconciliation')
 require(report['checkpoint_unchanged'] is None,'in-progress report checkpoint field')
 require(isinstance(report['trials_jsonl_sha256'],str) and len(report['trials_jsonl_sha256'])==64,'report ledger hash field')
 return {'status':'passed_identity_only_not_scientific_acceptance','old_prefix_bytes':592887,'old_prefix_results':12,'current_observed_unreviewed_results':new_results,'last_start_without_result_allowed':active,'new_invocation_count':1,'new_job_id':JOB,'old_job_id':'3022743','new_invocation_marker':marker,'original_R_proofs':{k:record(v) for k,v in old.items()},'observed_P_snapshots':{k:record(v) for k,v in new.items()},'report_count_observed':report['completed_trials'],'report_status':report['status'],'report_current_ledger_SHA_equality_not_required':True,'reason':'Known submitted job may append its ledger and atomically refresh report between independent reads. Outcome/action/reduction validation is deferred to exact original terminal consumer.','scientific_results_admitted':0,'legacy_results_counted_current':0,'new_submissions':0}
def validate_mutable_outputs(preflight):
 files=preflight['runtime_preflight']['checked_files']
 require(MUTABLE_ABSOLUTES.issubset(files),'exact mutable outputs absent from original preflight')
 for name in PINS:
  absolute=str(P/REL/name)
  require(files[absolute]==PINS[name],'original preflight row changed:'+name)
 old={name:(R/REL/name).read_bytes() for name in PINS}
 # Only retry an incomplete OS read up to three immediate attempts, never poll GPU/Slurm.
 # Read report first so its result count cannot legitimately outrun the following ledger snapshot.
 for attempt in range(3):
  new={name:(P/REL/name).read_bytes() for name in ['closed_loop_report.json','config.json','panel.json','trials.jsonl']}
  if new['trials.jsonl'].endswith(b'\n'):break
 require(new['trials.jsonl'].endswith(b'\n'),'partial JSONL after bounded reads')
 return validate_snapshots(old,new)
