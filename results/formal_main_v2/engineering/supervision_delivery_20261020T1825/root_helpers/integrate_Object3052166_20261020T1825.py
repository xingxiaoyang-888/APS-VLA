from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0225'
IND='.local/remaining_development_inventory_20261020T1825/object3052166/independent_review.json';PIN='8ec84ad5cbe65842c98930afd5ba7655e899de901abc2aee3704e04a1f2181c3';CAN='results/formal_main_v2/downstream_reviews/3052166_independent.json'
def h(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode()
def ref(n):return dict(path=n,sha256=h(R/n))
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def save(n,x,raw=False):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);assert not any(y.is_symlink() for y in [p,*p.parents])
 with p.open('xb') as f:f.write(x if raw else enc(x))
 return ref(n)
def load(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','integrate1825objectctl')
d=rd(IND,PIN);assert d['status']=='passed' and d['totals']==dict(allocated_gpu_seconds=2165,chunks=3554,executed_actions=27703,trials=200) and d['source173_R_and_S_unchanged'] and not d['sealed_final_values_read'] and not d['state_registry_Git_Slurm_mutations'] and not d['synthetic']
v=d['jobs']['3052166'];rr=rd('results/formal_main_v2/downstream_reviews/3052166.json','25de882d1e6e087e2d2f15ac0c4ad1e008d176ddd425d1851b31c136047d3713');obs=rd(B+'/initial_observation.json','95f0af6dec82f26d3b9cd15b3b51154289c2d99c22cd08f5e412f1a1342d9573')
assert rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==v['trials']==200 and v['unique_initial_states']==100 and v['full_original_consumer_reconstruction_passed'] and v['raw_start_result_pairs_exact']
assert {k:w['successes'] for k,w in rr['reconstructed_summary']['methods'].items()}==v['successes']=={'A256_seed23':96,'B256_seed23':96}
assert obs['controller_training_complete_normal'] and not obs['capacity']['occupied'] and not obs['capacity']['unknown']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sn='results/experiment_supervisor/state.json';before=h(R/sn);s=rd(sn);old=copy.deepcopy(s);f=s['formal_main_progress'];a=s['autonomous_training_v1']
 assert (f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'])==(72,360000,5200,6412)
 assert s['pending_submission'] is None and a['reserved_GPU_slots']==0 and a['root_submission_hold'] is None and not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0
 assert len(a['completed_pairs'])==36 and not a['blocked_pairs'] and '3052166' not in f['new_action_development_verified_by_job']
 save(B+'/Object3052166_state_before.json',(R/sn).read_bytes(),True);ir=save(CAN,(R/IND).read_bytes(),True)
 entry=dict(job_id='3052166',suite=v['suite'],seed=v['seed'],visual_tokens=256,completed_trials=200,unique_initial_states=100,successes=v['successes'],B_minus_A_percentage_points=v['B_minus_A_pp'],paired_outcomes=v['discordance'],per_task=v['per_task'],root_review=ref('results/formal_main_v2/downstream_reviews/3052166.json'),independent_review=ir,independent_review_scope='Exact report member selected by job_id',raw_ledger=v['raw_ledger'],GPU_seconds=2165,GPU_cost_scope='Full allocation2165 seconds; previous global snapshot had1917, so only248 added to global cost.',full_action_chunks=v['full_action_chunks'],executed_control_actions=v['executed_control_actions'],offline_validation_diagnostics=v['offline_validation_diagnostics'],t0_token_diagnostics=v['t0_token_diagnostics'],O2A_complete=False,scientific_final_release=False)
 assert entry['suite']=='libero_object' and entry['seed']==23 and entry['B_minus_A_percentage_points']==0
 f['new_action_development_verified_by_job']['3052166']=entry
 assert sum(x['completed_trials'] for x in f['new_action_development_verified_by_job'].values())==5400
 bysuite={}
 for e in f['new_action_development_verified_by_job'].values():
  r=rd(e['root_review']['path'],e['root_review']['sha256']);states=bysuite.setdefault(r['suite'],set())
  for pair in r['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 assert {k:len(x) for k,x in bysuite.items()}=={k:100 for k in ['libero_10','libero_spatial','libero_object','libero_goal']}
 f.update(current_action_development_trial_count=5400,completed_development_trials=6612)
 changes=[]
 for j in s['registered_jobs']:
  o=obs['observation']['rows'][str(j['job_id'])];changed={}
  for k in ('status','elapsed_seconds','exit_code','allocation','node','gpus'):
   if j.get(k)!=o[k]:changed[k]=dict(before=j.get(k),after=o[k]);j[k]=o[k]
  if changed:changes.append(dict(job_id=j['job_id'],fields=changed))
 assert {str(x['job_id']) for x in changes}<= {'3034538','3052166'}
 formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2'];total=sum(j['elapsed_seconds']*j['gpus'] for j in formal)
 assert len(formal)==264 and total==1978478 and total-old['current_round_cost']['allocated_gpu_seconds']==248
 s['current_round_cost'].update(allocated_gpu_seconds=total,allocated_gpu_hours=total/3600,registered_jobs=len(formal),final=True)
 a['occupied_job_ids']=[];a['root_confirmed_normal_training_exit']=dict(controller_job_id='3034538',status='COMPLETED',exit_code='0:0',lease_released=True,observation=ref(B+'/initial_observation.json'),training_pairs=36,training_arms=72,restart_needed=False)
 utc=datetime.now(timezone.utc).isoformat();summary=dict(schema='formal_main_v2',status='Object3052166_root_and_independent_accepted',utc=utc,new_development_trials=200,development=entry,training_arms=72,reviewed_arm_updates=360000,current_action_development_trials=5400,compatible_legacy_Long_trials=600,compatible_development_trials=6000,all_historical_accepted_development_trials=6612,unique_development_initial_states=400,allocated_GPU_seconds=total,allocated_GPU_hours=total/3600,newly_accounted_GPU_seconds=248,new_GPU_submissions=0,registered_job_terminal_changes=changes,controller_normal_exit=True,Goal_original200_HOLD=True,all_new_Goal_scientific_HOLD=True,final_trials=0,final_sealed=True,global_release=False,observation=ref(B+'/initial_observation.json'))
 sr=save(B+'/Object3052166_integration.json',summary);f['integration_20261020T1825_accepted']=sr;f['latest_new_action_development_verified']=sr
 s['last_root_supervision_snapshot']=sr;s['last_supervision_utc']=utc;s['updated_utc']=utc;s['stage']='formal_main_v2_development_and_profiling_preparation';s['current_work']='72/72 training arms root+independent verified; controller exited normally. Development5400 current-action plus600 compatible Long=6000 accepted,400 unique initial states;6612 total historical records retained. Goal original200/new scientific development HOLD. Final0/35200 sealed.'
 s['next_actions']=['Run one independently accepted bounded Goal prefix58 engineering diagnostic when ready; retain original failure and all Goal scientific HOLD.','Review remaining legacy development identities before continuation: Spatial12 retained/588 remaining; Object old600 includes one policy_error, no blanket equivalence.','Prepare fixed development observation collection for Spatial/Object under original collect gate; full O2A/components await complete global identity freeze.','Audit pair-specific startup provenance for Spatial/Object64seed23 before their development; no generic source bridge.','Freeze all72 selectors+16references+all4suite development+final manifest, then root global release only; final35200 remain sealed.']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs'] and a['completed_pairs']==old['autonomous_training_v1']['completed_pairs']
 c.atomic_json(R/sn,s,before)
 save(B+'/Object3052166_integration_receipt.json',dict(status='applied',source=ref(Path(__file__).relative_to(R).as_posix()),summary=sr,state_before_sha256=before,state_after_sha256=h(R/sn),new_scientific_trials=200,new_initial_states=0,new_GPU_jobs=0,final_sealed=True))
 print(json.dumps(dict(status='accepted200',summary=sr,successes=entry['successes'],compatible_development=6000,unique_initial_states=400,GPU_hours=total/3600,controller_restart_needed=False)),flush=True)
