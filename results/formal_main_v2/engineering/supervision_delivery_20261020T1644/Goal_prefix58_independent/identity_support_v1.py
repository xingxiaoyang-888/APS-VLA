"""Read-only metadata support for independent Goal observer audit; no simulator or weights."""
from pathlib import Path
import hashlib,json,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=Path(__file__).parent;A=R/'.local/goal_prefix58_candidate_20261020T1644'
t0=time.process_time();checks=[]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(1<<20),b''):h.update(x)
 return h.hexdigest()
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def read_ref(ref):
 p=Path(ref['path']);ck('nonweight metadata '+p.name,p.suffix in ('.json','.jsonl','.py') and p.name!='state.json');ck('exact pin '+p.name,p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256']);return p
ck('candidate pinned',sha(A/'delivery_manifest.json')=='9a2f425a7d6e715c6a108a400bd1a92fe713e2b368bdc3a2ab2e0e3a4da76595')
ck('main independent report pinned',sha(D/'attempt02/independent_review.json')=='24398f0dfb160bb2ee1aa3ef5cfada40427798eb867dd56f9d7479e51a8bb604')
pins=json.loads((A/'inputs/pinned_inputs.json').read_text());proposal=json.loads((A/'inputs/proposed_single_attempt_registration.json').read_text());prefix=json.loads((A/'inputs/original_prefix58.json').read_text())['rows']
needed=['original_invocation','panel','ledger','original_action_identity','original_action_events','original_action_completion','libero_runtime_source','formal_trials_source','formal_entry_source','original_effective_plan','original_config','source_inventory','env_wrapper_source']
verified={k:read_ref(pins[k]) for k in needed}
inv=json.loads(verified['original_invocation'].read_text());ck('original development suite stage',inv['suite']=='libero_goal' and inv['stage']=='development');ck('A B method order',inv['method_ids']==['A256_seed17','B256_seed17'])
binding={k:v['identity']['checkpoint_sha256'] for k,v in inv['source_provenance']['method_bindings'].items()};ck('both original selected checkpoint metadata match proposal',binding==proposal['checkpoint_identities'])
ck('new proposed GPU scope stays inactive',proposal['status']=='proposal_only_not_authorized_not_run' and proposal['scientific_trials_accepted']==0 and proposal['sealed_values_access'] is False and proposal['original200_HOLD_unchanged'] is True)
ck('fixed original settings',proposal['same_settings']=={'action_chunk':8,'camera':[256,256],'envseed':0,'max_control_steps':300,'seed':17,'suite':'libero_goal','tokens':256,'wait_steps':10})
ck('single bounded no-retry proposal',proposal['GPU_jobs']==1 and proposal['GPUs']==1 and proposal['maximum_attempts']==1 and proposal['hard_Slurm_wall_seconds']==1800 and proposal['automatic_retry'] is False and proposal['historical_actual_actions_replayed'] is False)
rows=[json.loads(x) for x in verified['ledger'].read_text().splitlines() if x.strip()]
results=[x for x in rows if x.get('event')=='result'];starts=[x for x in rows if x.get('event')=='start']
identity=('trial_id','state_trial_id','task_id','task_name','source_state_index','initial_state_sha256','method')
ck('original actual 200 retained ledger',len(results)==200 and len(starts)==200)
ck('prefix exact from original result order',[{k:r[k] for k in identity} for r in results[:58]]==[{k:r[k] for k in identity} for r in prefix])
ck('prefix exact from original start order',[{k:r[k] for k in identity} for r in starts[:58]]==[{k:r[k] for k in identity} for r in prefix])
for i,(recorded,original) in enumerate(zip(prefix,results[:58]),1):
 ck('original prefix control/query/wait '+str(i),all(recorded[k]==original[k] for k in ('control_steps','policy_calls','wait_steps')))
 ck('original prefix postquery hash '+str(i),recorded['t0_postquery_hash']==original['chunks'][0]['observation_sha256'])
actual_calls=sum(r['policy_calls'] for r in results[:56]);actual_actions=sum(r['control_steps'] for r in results[:56]);ck('actual first56 counters',actual_calls==916 and actual_actions==7124)
prepare=json.loads((A/'prepare_v1.json').read_text());ck('author preparation only and no GPU claim',prepare['CPU_only'] and prepare['GPU_calls']==0 and not prepare['actual_GPU_entry_implemented'] and not prepare['actual_GPU_authorized'])
ck('author prepare exact58 metadata',prepare['exact_prefix_identities']==[{k:r[k] for k in identity} for r in prefix])
# Static original execution/model loading source remains byte-exact; no old evaluate/run is invoked here.
report={'kind':'independent_goal_prefix58_metadata_binding','status':'passed_metadata_only','checks':checks,'passed_check_count':len(checks),'verified_inputs':{k:pins[k] for k in needed},'original_checkpoint_metadata':binding,'weights_rehashed_or_loaded':False,'original_prefix_source_identity':{'source':str((A/'inputs/original_prefix58.json').relative_to(R)),'sha256':sha(A/'inputs/original_prefix58.json')},'original_pre_anomaly_counters':{'trials':56,'policy_queries':actual_calls,'policy_controls':actual_actions,'dummy_controls':sum(r['wait_steps'] for r in results[:56])},'t0_anomaly_hashes':[r['chunks'][0]['observation_sha256'] for r in results[56:58]],'new_GPU_jobs':0,'new_scientific_trials':0,'HOLD_unchanged':True,'CPU_seconds':time.process_time()-t0,'limits':'Metadata byte bindings and original start/result order checked; this is not a fresh hash of checkpoint tensors or proof of real model output determinism. Real original-chain outer entry remains missing.'}
p=D/'identity_support.json'
with p.open('x') as f:json.dump(report,f,sort_keys=True,indent=2,ensure_ascii=False);f.write('\n')
print(json.dumps({'checks':len(checks),'report_sha256':sha(p),'CPU_seconds':report['CPU_seconds']}))
