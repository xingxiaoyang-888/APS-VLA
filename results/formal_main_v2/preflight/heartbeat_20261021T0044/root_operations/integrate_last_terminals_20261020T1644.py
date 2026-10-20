from pathlib import Path
from datetime import datetime,timezone
import argparse,copy,hashlib,importlib.util,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0044';V='.local/last_terminals_integration_preview_20261020T1644'
TRAINS=[('libero_goal','3043813','5b102d10e4264b654fe8fe8e26bd9e66c6b82b9e14bc765f5f1bb534ce1d20de','.local/last_two_training_independent_20261020T1644/goal/3043813_independent_review.json','d23ddb4a0636c3da92293ea766a099bbf62dabff6b8379c17d07af73dfb1d670','780c989cb66ad3a32b05a2d160af6acec9b8b5be6a9a1c2dc9c72ce2ea52c904',10000,66792),('libero_object','3044844','6f3bd55f4772812c3e171f700587a753a2153c151c6fad554152fa84371c5ea9','.local/last_two_training_independent_20261020T1644/object/independent_review.json','9d357b032ae9c8c3d1aa4f901875eec4ef4fca7c2912805c52e114813e3b2150','91e425cec060d8bba49da08dac4723e9b9a7277cfb7adfcb303f5161c3ed1c9b',9000,52868)]
DEV='.local/four_development_independent_20261020T1644/independent_review.json';DP='d3170418334cc545bd760472463a7e165a44b233393b81dff76f5eea72c397ce';DC='results/formal_main_v2/downstream_reviews/four64_20261020T1644_independent.json'
DOCS=['实验进度','完整实验计划','正式主实验规划','正式主实验阶段结论','正式自动连续训练执行登记']
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enc(x):return (json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+chr(10)).encode()
def ref(n):p=R/n;return dict(path=n,sha256=h(p))
def read(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def put(n,b):
 p=R/n;assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,n
 else:
  with p.open('xb') as f:f.write(b)
def save(n,v):put(n,enc(v));return ref(n)
def mod(n,pin,name):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');opt=ap.parse_args();c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','integrateLast1644ctl')
d=read(DEV,DP);assert d['status']=='passed' and d['totals']=={'allocated_gpu_seconds':8708,'chunks':12551,'executed_actions':97621,'trials':800} and d['new_held_job_ids']==[] and not d['sealed_final_values_read'] and d['source173_R_and_S_unchanged']
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sn='results/experiment_supervisor/state.json';statebytes=(R/sn).read_bytes();before=h(R/sn);s=json.loads(statebytes);old=copy.deepcopy(s);f=s['formal_main_progress'];a=s['autonomous_training_v1']
 assert (f['root_and_independent_completed_arms'],f['root_and_independent_reviewed_arm_updates'],f['current_action_development_trial_count'],f['completed_development_trials'])==(68,341000,4400,5612)
 assert not f['test_opened'] and not f['global_release_created'] and f['completed_final_trials']==0 and s['pending_submission'] is None and a['reserved_GPU_slots']==0 and a['root_submission_hold'] is None
 training=[];publications={};proposedrefs={}
 for suite,jid,rpin,ipath,ipin,spin,delta,cost in TRAINS:
  pair=suite+'_k64_seed23';rrpath='results/formal_main_v2/'+suite+'/k64/seed23/training/segment_reviews/'+jid+'.json';rr=read(rrpath,rpin);ir=read(ipath,ipin);selected=read(B+'/'+jid+'_selected_server.json',spin)
  assert rr['status']=='passed' and rr['completed_by_arm']==ir['completed_by_arm']=={'A':5000,'B':5000} and ir['status']=='passed_complete_training_only' and rr['pair_allocated_gpu_seconds']==cost
  assert ir['job_id']==jid and ir['suite']==suite and ir['seed']==23 and ir['visual_tokens']==64 and not ir['final_release_authorized'] and ir['same_AB_initialization_and_full40000_order']
  srpath='results/formal_main_v2/'+suite+'/k64/seed23/training/segment_reviews/'+jid+'_independent.json';publications[srpath]=(R/ipath).read_bytes();proposedrefs[srpath]=ipin;checks=[]
  for x in selected['checks']:
   p=Path(x['path']);assert p==Path('/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2')/suite/'k64/seed23'/x['arm']/'best.pt';st=p.stat();assert c.file_sha(p)==x['sha256'] and p.stat()==st
   receipt=read('results/formal_main_v2/'+suite+'/k64/seed23/training/'+x['arm']+'/deployment_receipt.json');assert receipt['checkpoint_sha256']==x['sha256'] and receipt['completed_updates']==5000 and [v['update'] for v in receipt['evaluations']]==list(range(0,5001,500))
   checks.append(dict(arm=x['arm'],path=str(p),expected_sha256=x['sha256'],selected_update=x['selected_update'],validation_metric=x['validation_metric']))
  assert {x['arm'] for x in checks}=={'A','B'}
  prior=f['completed_training_pairs'].get(pair,{})
  assert not prior.get('root_review') and not prior.get('terminal_root_and_independent_review')
  row=copy.deepcopy(prior);row.update(job_id=jid,suite=suite,visual_tokens=64,seed=23,completed_by_arm={'A':5000,'B':5000},trained_arms=2,allowed_next_segment_end=None,root_review=rrpath,root_review_sha256=rpin,independent_review=srpath,independent_review_sha256=ipin,selected_checkpoints=checks,selected_server_review=B+'/'+jid+'_selected_server.json',selected_server_review_sha256=spin,root_and_independent_verification_kind='completed_original_root_and_independent_training_review');f['completed_training_pairs'][pair]=row
  training.append(dict(pair=pair,job_id=jid,root_review=dict(path=rrpath,sha256=rpin),independent_review=dict(path=srpath,sha256=ipin),selected_server=dict(path=B+'/'+jid+'_selected_server.json',sha256=spin),new_reviewed_arm_updates=delta,pair_GPU_seconds=cost,already_in_global_cost=True))
 all_training_refs=[]
 for pair,row in f['completed_training_pairs'].items():
  if 'terminal_root_and_independent_review' in row:refs=[row['terminal_root_and_independent_review'][k] for k in ['root_review','independent_review']]
  else:refs=[dict(path=row[k],sha256=row[k+'_sha256']) for k in ['root_review','independent_review']]
  for x in refs:assert proposedrefs.get(x['path'],h(R/x['path']) if (R/x['path']).exists() else None)==x['sha256'];all_training_refs.append(x)
 assert len(f['completed_training_pairs'])==36
 admissions=[]
 for pair in ['libero_object_k256_seed23','libero_spatial_k64_seed23','libero_object_k64_seed23']:
  assert pair not in a['completed_pairs'] and pair in a['blocked_pairs'];row=f['completed_training_pairs'][pair];refs=[dict(path=row[k],sha256=row[k+'_sha256']) for k in ['root_review','independent_review','selected_server_review']];checks=[]
  for x in row['selected_checkpoints']:
   p=Path(x['path']);st=p.stat();digest=c.file_sha(p);assert digest==x['expected_sha256'] and st==p.stat();checks.append(dict(arm=x['arm'],path=str(p),sha256=digest,bytes=st.st_size,exists=True,stable_during_hash=True))
  assert len(checks)==2 and {x['arm'] for x in checks}=={'A','B'}
  admissions.append(dict(pair=pair,retained_original_block=copy.deepcopy(a['blocked_pairs'][pair]),root_and_independent=refs,selected_actual_bytes=checks,failed_history_not_erased=True,new_machine_review_claimed=False))
  a['completed_pairs'][pair]=dict(decision='complete',completed_by_arm={'A':5000,'B':5000},verification_origin='inherited_root_and_independent_review',new_machine_review_claimed=False,evidence_refs=refs,selected_checkpoint_checks=checks,selected_checkpoints_verified=True,inherited_checkpoint_bytes_rechecked_by_root=True,validation_updates=list(range(0,5001,500)));a['blocked_pairs'].pop(pair)
 assert len(a['completed_pairs'])==36 and not a['blocked_pairs'];assert set(a['completed_pairs'])==set(f['completed_training_pairs'])
 entries=[];cur=f['new_action_development_verified_by_job']
 for jid,v in d['jobs'].items():
  assert jid not in cur and v['trials']==200 and v['unique_initial_states']==100 and v['full_original_consumer_reconstruction_passed'] and v['raw_start_result_pairs_exact']
  rp=v['root_receipt'];rr=read(rp['path'],rp['sha256']);assert rr['status']=='passed' and rr['scientific_complete'] and rr['completed_trials']==200
  assert {k:w['successes'] for k,w in rr['reconstructed_summary']['methods'].items()}==v['successes']
  reg=[x for x in f['nonLong_development_submissions_1530'] if str(x['job_id'])==jid];assert len(reg)==1 and reg[0]['completed_trials_accepted']==0
  entry=dict(job_id=jid,suite=v['suite'],seed=v['seed'],visual_tokens=64,completed_trials=200,unique_initial_states=100,successes=v['successes'],B_minus_A_percentage_points=v['B_minus_A_pp'],paired_outcomes=v['discordance'],per_task=v['per_task'],root_review=rp,independent_review=dict(path=DC,sha256=DP),independent_review_scope='Exact report member selected by job_id',raw_ledger=v['raw_ledger'],GPU_seconds=v['allocated_GPU_seconds'],GPU_cost_scope='Previously counted Slurm allocation; acceptance adds zero GPU cost.',full_action_chunks=v['full_action_chunks'],executed_control_actions=v['executed_control_actions'],offline_validation_diagnostics=v['offline_validation_diagnostics'],t0_token_diagnostics=v['t0_token_diagnostics'],O2A_complete=False,scientific_final_release=False)
  cur[jid]=entry;entries.append(entry);reg[0].update(completed_trials_accepted=200,observed_status='COMPLETED',scientific_terminal_acceptance_pending=False,terminal_root_review=rp,terminal_independent_review=dict(path=DC,sha256=DP))
 assert sum(x['completed_trials'] for x in cur.values())==5200 and '3049679' not in cur
 bysuite={}
 for e in cur.values():
  rr=read(e['root_review']['path'],e['root_review']['sha256']);states=bysuite.setdefault(rr['suite'],set())
  for pair in rr['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 assert {k:len(v) for k,v in bysuite.items()}=={k:100 for k in ['libero_10','libero_spatial','libero_object','libero_goal']}
 f.update(root_and_independent_completed_arms=72,root_and_independent_reviewed_arm_updates=360000,trained_arms=72,current_action_development_trial_count=5200,completed_development_trials=6412)
 publications[DC]=(R/DEV).read_bytes();utc=datetime.now(timezone.utc).isoformat();summary=dict(schema='formal_main_v2',status='72_training_arms_and800_development_trials_root_independent_integrated_pending_postcheck',utc=utc,training=training,all36_root_and_independent_refs=all_training_refs,training_arms=72,reviewed_arm_updates=360000,new_training_arms=4,new_reviewed_updates=19000,new_development_trials=800,current_action_development_trials=5200,compatible_legacy_Long_trials=600,compatible_development_trials=5800,all_historical_accepted_development_trials=6412,unique_development_initial_states=400,development=entries,controller_completion_admissions=admissions,controller_admission_does_not_reinterpret_machine_provenance=True,global_cost_unchanged=True,allocated_GPU_hours=s['current_round_cost']['allocated_gpu_hours'],new_GPU_submissions=0,existing_Object256s23_development_job='3052166',Goal_original200_HOLD=True,all_new_Goal_scientific_HOLD=True,final_trials=0,final_sealed=True,global_release=False)
 summarypath=B+'/last_terminals_integration.json';summaryref=dict(path=summarypath,sha256=hashlib.sha256(enc(summary)).hexdigest());f['last_terminals_integration_20261020T1644']=summaryref;f['latest_new_action_development_verified']=summaryref
 a['root_terminal_completed_pair_admissions_20261020T1644']=summaryref
 s['last_root_supervision_snapshot']=summaryref;s['current_work']='72/72 training arms root and independent verified;360000 reviewed updates. Development5200 current semantics plus600 compatible Long =5800 accepted trials;400 unique initial states. Goal original200 and new Goal scientific development HOLD;Object256s23 development3052166 submitted once. Final0/35200 sealed.'
 s['next_actions']=['Review Object256s23 development3052166 at scheduled supervision; never duplicate its submission.','Finish remaining registered development, full O2A and independent component timing; training completion alone does not release final.','Repair bounded Goal prefix58 observer protection gaps, independently audit, then real engineering GPU acceptance before any new Goal scientific trial.','Freeze72checkpoint identities+16reference identities+all4suite development receipts and final manifest; only global root release can open final35200.']
 assert s['registered_jobs']==old['registered_jobs'] and s['current_round_cost']==old['current_round_cost']
 for k,v in old.items():
  if k not in ['formal_main_progress','autonomous_training_v1','last_root_supervision_snapshot','current_work','next_actions']:assert s[k]==v,k
 for k,v in old['autonomous_training_v1'].items():
  if k not in ['completed_pairs','blocked_pairs']:assert a[k]==v,k
 for pair,row in old['autonomous_training_v1']['completed_pairs'].items():assert a['completed_pairs'][pair]==row
 for pair,row in old['formal_main_progress']['completed_training_pairs'].items():
  if pair not in ['libero_goal_k64_seed23','libero_object_k64_seed23']:assert f['completed_training_pairs'][pair]==row
 publications[summarypath]=enc(summary)
 change=dict(status='exact_root_integration_candidate',source=ref(Path(__file__).relative_to(R).as_posix()),state_before_sha256=before,state_after_sha256=hashlib.sha256(enc(s)).hexdigest(),new_training_arms=4,new_reviewed_updates=19000,new_development_trials=800,new_GPU_jobs=0,registry_cost_and_science_preserved=True,publications={n:hashlib.sha256(raw).hexdigest() for n,raw in publications.items()})
 if not opt.apply:
  put(V+'/state_before.json',statebytes);put(V+'/state_after.json',enc(s));put(V+'/summary.json',enc(summary));put(V+'/intent.json',enc(change));print(json.dumps(dict(status='preview_only',preview=V,intent=ref(V+'/intent.json'))),flush=True)
 else:
  put(B+'/last_terminals_state_before.json',statebytes);put(B+'/last_terminals_integration_intent.json',enc(change))
  for n,raw in publications.items():put(n,raw)
  c.atomic_json(R/sn,s,before)
  receipt=save(B+'/last_terminals_integration_completion.json',dict(status='applied_pending_post_independent_crosscheck',summary=summaryref,state_before_sha256=before,state_after_sha256=h(R/sn),new_training_arms=4,new_development_trials=800,new_GPU_jobs=0,final_sealed=True))
  print(json.dumps(dict(status='applied72_training_and800_development',receipt=receipt,summary=summaryref)),flush=True)
