"""Root-only acceptance of already completed evidence. Default private preview.
No Slurm submission, no production changes by author, no weights or sealed values.
"""
from pathlib import Path,PurePosixPath
from datetime import datetime,timezone,timedelta
import argparse,copy,hashlib,importlib.util,json,os,sys,uuid
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
PRIVATE='.local/integration_candidate_20261020T1530'
PAIR='libero_goal_k64_seed17'
PINS={
 'independent':(E+'/terminal_independent/independent_review.json','bc6ec59ace7431daa18056a2f64352be3f909d902644c5b0a0c546249bf879d8'),
 'statistics':(E+'/terminal_independent/development_statistics.json','3ea06d35c1f8f92a30a46449212080c3d952f08e2d1a8f633b568e75d760648a'),
 'paired':(E+'/terminal_independent/paired_development_states.json','2de1dbbe15d4c06cebc94b2f6c37995328f102dc3e2d7cfb10cd74e04ec38698'),
 'matrix':(E+'/terminal_independent/Spatial256_paired_matrix.json','c84e77d62d85b50465f53b0b0ec00b964013664ca67c0a18b84ac5b02de213c5'),
 'root_bootstrap':(B+'/Spatial256_root_bootstrap_recomputation.json','30b0e47cf98498d48a84abb119eec376529f4b78c2de0a47fc1db9a66c50a8ba'),
 'training_root':('results/formal_main_v2/libero_goal/k64/seed17/training/segment_reviews/3043762.json','945c9605a5c1e819ba864f8b5db682dd8ddae65f219786673ae10b1c8fcd2bff'),
 'training_independent':('results/formal_main_v2/libero_goal/k64/seed17/training/segment_reviews/3043762_independent.json','97a69fda379c85a6c07b56c78cddc134004359076cb2ce12b5703b73c73f5cee'),
 'selected_server':(B+'/3043762_selected_server.json','b1ff86ff684df70267a1b71c46a527a3b0f45b360cef66eaf84fa4e05e64df98'),
 'independent_delivery':(B+'/independent_evidence_delivery.json','8ccb8612249ae70f51454bca266adba16b8e91947b6069eb4e845a400ae557c5'),
 'inventory':('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')}
JOBS=[
 ('3050192','libero_spatial',256,23,2276,'a911fc07e5a11ae892c87bc0439b27d2dd5e904f1cb7a1b894833a7ab45ac1bf'),
 ('3050205','libero_spatial',256,41,2353,'0de38a659371c54b5ebfe02aa13227eebacf7ae07bbedbbe22845dbe7f0459b5'),
 ('3050224','libero_object',256,41,2049,'38ca22f9dcda9f328f388af0292196ef54e2349843cb59d0596dba2bc7dc32b5')]
SUMMARY=B+'/completed_evidence_integration_1530.json'
STATS=B+'/accepted_256_development_diagnostics_1530.json'
INTENT=B+'/integration_1530_intent.json'
COMPLETION=B+'/integration_1530_completion.json'
DOCS=['实验进度','完整实验计划','正式主实验阶段结论','正式主实验规划','正式自动连续训练执行登记','正式非Long开发结果']
def require(ok,msg):
 if not ok:raise ValueError(msg)
def path(rel,root=R):
 q=PurePosixPath(rel);require(rel and not q.is_absolute() and '..' not in q.parts and '\\' not in rel,'unsafe path')
 p=root.joinpath(*q.parts)
 for z in [p,*p.parents]:
  if z==root:break
  require(not z.is_symlink(),'symlink path')
 require(p.resolve().is_relative_to(root.resolve()),'escaped root');return p
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for part in iter(lambda:f.read(1<<20),b''):h.update(part)
 return h.hexdigest()
def rawjson(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def rd(rel,pin=None):
 p=path(rel)
 if pin:require(sha(p)==pin,'SHA mismatch '+rel)
 return json.loads(p.read_bytes())
def ref(rel,pin=None):return dict(path=rel,sha256=pin or sha(path(rel)))
def pref(k):return ref(*PINS[k])
def mod(rel,pin,name):
 require(sha(path(rel))==pin,'module SHA mismatch');sp=importlib.util.spec_from_file_location(name,path(rel));m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def inputs():
 d={k:rd(*v) for k,v in PINS.items()};j=d['independent'];st=d['statistics'];rb=d['root_bootstrap']
 require(j['status']=='passed' and j['totals']['trials']==600 and j['totals']['allocated_gpu_seconds']==6678,'terminal totals')
 require(set(j['jobs'])=={x[0] for x in JOBS} and j['new_held_job_ids']==[],'exact terminal scope')
 require(j['source173_R_and_S_unchanged'] and not j['checkpoint_bytes_read'] and not j['sealed_final_values_read'] and j['new_GPU_jobs']==0,'audit scope')
 require(j['paired_states']['sha256']==PINS['paired'][1],'paired rows')
 require(st['new_GPU_jobs']==0 and not st['sealed_final_values_read'] and not st['final_release'] and not st['latency_executed'],'stats scope')
 require(st['status']=='passed_Spatial_three_seeds_Object_explicit_missing23','stats status')
 x=st['suites']['libero_spatial']; require(x['available_seeds']==[17,23,41] and x['missing_seeds']==[] and x['unique_initial_states']==100 and x['trial_count']==600 and x['bootstrap_repeats']==10000 and x['bootstrap_seed']==20261016,'Spatial full fixed three seeds')
 x=st['suites']['libero_object'];require(x['available_seeds']==[17,41] and x['missing_seeds']==[23] and x['unique_initial_states']==100 and x['trial_count']==400 and not x['bootstrap_computed'],'Object missing23 retained')
 require(rb['status']=='passed' and rb['method_trials']==600 and rb['unique_initial_states']==100 and rb['seeds']==[17,23,41] and rb['bootstrap_repeats']==10000 and rb['new_GPU_jobs']==0 and not rb['sealed_final_values_read'],'root recomputation scope')
 for key in ['means_percent','seed_sample_SD_pp','bootstrap_interval95_pp']:
  for k,v in rb[key].items():
   w=st['suites']['libero_spatial'][key][k]
   require(all(abs(a-b)<1e-9 for a,b in zip(v,w)) if isinstance(v,list) else abs(v-w)<1e-9,'root recomputation differs')
 entries=[]
 for jid,suite,budget,seed,secs,pin in JOBS:
  rel='results/formal_main_v2/downstream_reviews/'+jid+'.json';rr=rd(rel,pin);v=j['jobs'][jid]
  require(rr['status']==v['status']=='passed' and rr['scientific_complete'] and rr['suite']==v['suite']==suite,'review')
  require(rr['completed_trials']==v['trials']==200 and v['unique_initial_states']==100 and v['allocated_GPU_seconds']==secs and v['seed']==seed and v['A_B_visual_tokens']==budget,'identity')
  require(v['root_receipt']==ref(rel,pin) and v['raw_start_result_pairs_exact'] and v['full_original_consumer_reconstruction_passed'],'original consumer')
  rs=rr['reconstructed_summary'];successes={k:x['successes'] for k,x in rs['methods'].items()};a=f'A{budget}_seed{seed}';b=f'B{budget}_seed{seed}'
  require(successes==v['successes'] and set(successes)=={a,b} and (v['A_success'],v['B_success'])==(successes[a],successes[b]),'success reconstruction')
  pair=rs['paired_AB'][f'k{budget}_seed{seed}'];require(pair['completed_pairs']==len(pair['results'])==100 and abs(pair['B_minus_A_success_rate']*100-v['B_minus_A_pp'])<1e-9,'paired summary')
  lr=v['raw_ledger'];require(sha(path(lr['path']))==sha(path(lr['path'],P))==lr['sha256'],'R/P ledger')
  t=v['t0_token_diagnostics'];require(t['paired_observations']==len(t['rows'])==100 and t['all_t0_observation_hashes_equal'],'t0 rows')
  for dg in v['offline_validation_diagnostics'].values():rd(dg['validation_ref']['path'],dg['validation_ref']['sha256'])
  entries.append(dict(job_id=jid,suite=suite,seed=seed,visual_tokens=budget,completed_trials=200,unique_initial_states=100,successes=successes,
   B_minus_A_percentage_points=v['B_minus_A_pp'],paired_outcomes=v['discordance'],per_task=v['per_task'],root_review=ref(rel,pin),independent_review=pref('independent'),
   independent_review_scope='Exact report member selected by job_id; post-integration review not yet claimed.',raw_ledger=lr,GPU_seconds=secs,
   GPU_cost_scope='Existing allocation included once in global Slurm total; acceptance adds zero GPU.',
   initial_observation_token_overlap_mean=t['mean_intersection_over_budget'],initial_observation_token_Jaccard_mean=t['mean_Jaccard'],
   token_overlap_scope='100 equal-hash t0 observations only; divergent later trajectories not paired.',offline_validation_diagnostics=v['offline_validation_diagnostics'],
   action_semantics_sha256=rr['action_semantics_sha256'],reference_trials=0,AB_trials=200,full_action_chunks=v['full_action_chunks'],executed_control_actions=v['executed_control_actions'],
   no_legacy_semantics_equivalence_claimed=True,whole_suite_development_complete=False,O2A_complete=False))
 inventory=d['inventory'];require(len(inventory['files'])==173,'frozen source count')
 for rel,pin in inventory['files'].items():require(sha(path(rel))==sha(path('snapshots/formal_main_v2_run_564be0995e/'+rel,P))==pin,'frozen source changed')
 d['entries']=entries
 verify_training(d)
 return d

def verify_training(d):
 rr=d['training_root'];v=d['training_independent'];ss=d['selected_server']
 require(rr['status']=='passed' and v['status']=='passed_complete_training_only','training dual review')
 for x in [rr,v]:
  require(x['job_id']=='3043762' and x['suite']=='libero_goal' and x['seed']==17 and x['visual_tokens']==64 and x['completed_by_arm']=={'A':5000,'B':5000} and not x['resume_required'] and x['allowed_next_segment_end'] is None,'training identity')
 require(rr['continuation']=='formal_training_complete_no_extension' and rr['pair_allocated_gpu_seconds']==60721 and rr['ab_same_registered_boundary'] and not rr['sealed_states_opened'],'root final gate')
 require(v['all173_R_and_S_match'] and v['same_AB_initialization_and_full40000_order'] and v['machine_status_not_claimed_as_independence'] and not v['final_release_authorized'] and not v['scientific_closed_loop_claimed'],'independent scope')
 t=v['parallel_root_reconstruction'];require(t['path']==PINS['training_root'][0] and t['sha256']==PINS['training_root'][1] and t['fresh_pair'] and t['new_reviewed_arm_updates']==10000 and t['prior_reviewed_updates_per_arm']==0 and t['selected_server_proof']==pref('selected_server'),'independent root reconstruction')
 require(v['cost']['all_pair_allocated_GPU_seconds']==60721 and v['cost']['allocations']==[{'GPU_seconds':60721,'job_id':'3043762'}] and not v['cost']['nested_phases_added'],'training cost')
 require(ss['status']=='verified_actual_server_bytes' and ss['root_review']==pref('training_root') and ss['job_id']=='3043762' and not ss['weights_copied'],'actual selected server proof')
 require({x['arm'] for x in ss['checks']}=={'A','B'} and len(ss['checks'])==2,'selected two arms')
 selected=[]
 for x in ss['checks']:
  arm=x['arm'];a=v['arms'][arm];rel='results/formal_main_v2/libero_goal/k64/seed17/training/'+arm+'/deployment_receipt.json'
  require(rel in rr['files'],'receipt bound by original root')
  require(sha(path(rel))==sha(path(rel,P))==rr['files'][rel],'R/P original receipt')
  rec=rd(rel,rr['files'][rel]); require(rec['training_complete'] and rec['completed_updates']==rec['planned_updates']==5000 and rec['base_frozen'] and rec['checkpoint_unchanged'],'deployment receipt gate')
  require(x['path']=='/share/home/u15016/XXY_CVPR/CTI-VLA/checkpoints/formal_main_v2/libero_goal/k64/seed17/'+arm+'/best.pt' and x['sha256']==rec['checkpoint_sha256']==a['best_sha256'] and x['selected_update']==a['earliest_selected_update'] and x['validation_metric']==a['selected_teacher_l1'],'selected original identity')
  require(a['completed_updates']==5000 and a['sample_uses']==a['cursor']==40000 and a['unique_windows']==33859 and a['replayed_or_uncommitted_samples']==0,'training uses')
  require([z['update'] for z in a['validation']]==list(range(0,5001,500)),'11 validation nodes')
  for z in a['validation']:rd(z['path'],z['sha256'])
  selected.append(dict(arm=arm,path=x['path'],expected_sha256=x['sha256'],selected_update=x['selected_update'],validation_metric=x['validation_metric']))
 d['selected']=selected

def precondition(s):
 f=s['formal_main_progress'];c=s['autonomous_training_v1']
 require(f['root_and_independent_completed_arms']==64 and f['root_and_independent_reviewed_arm_updates']==321000,'training acceptance changed; re-audit')
 require(f['completed_development_trials']==5012 and f['current_action_development_trial_count']==3800,'development changed or duplicate apply')
 require(f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'],'final sealed')
 require('integration_20261020T1530_accepted' not in f,'integration already applied')
 require(c['controller_job_id']=='3034538','controller changed')
 cp=f['completed_training_pairs'][PAIR]
 require(cp['completed_by_arm']=={'A':5000,'B':5000} and cp['trained_arms']==2 and cp['machine_verification'] and cp['verification_kind']=='machine_automatic_not_independent','prior machine proof')
 require('root_review' not in cp and 'independent_review' not in cp,'duplicate training acceptance')
 require(f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600,'legacy counts')
 require('3049679' not in f['new_action_development_verified_by_job'],'held Goal already accepted')
 held=[x for x in f['nonLong_development_submissions_1317'] if x['job_id']=='3049679']
 require(len(held)==1 and held[0]['completed_trials_accepted']==0 and held[0]['terminal_review_status']=='HOLD_initial_observation_mismatch','Goal hold')
 require('downstream_blockers_20261020T1418' in f,'original downstream blocker record absent')
 for jid,*_ in JOBS:
  require(jid not in f['new_action_development_verified_by_job'],'duplicate development acceptance')
  p=[x for x in f['nonLong_development_submissions_1418'] if x['job_id']==jid]
  require(len(p)==1 and p[0]['completed_trials_accepted']==0 and p[0]['scientific_terminal_acceptance_pending'],'original pending development record')
 # Pending root submissions, reserved slots, holds, machine proofs and later dispatches are preserved exactly.

def accept_terminals(s,d):
 f=s['formal_main_progress'];cur=f['new_action_development_verified_by_job']
 for e in d['entries']:
  jid=e['job_id'];require(jid not in cur,'already accepted')
  p=[x for x in f['nonLong_development_submissions_1418'] if x['job_id']==jid]
  require(len(p)==1 and p[0]['completed_trials_accepted']==0,'original pending development')
  p[0].update(completed_trials_accepted=200,observed_status='COMPLETED',scientific_terminal_acceptance_pending=False,terminal_root_review=e['root_review'],terminal_independent_review=e['independent_review'])
  cur[jid]=copy.deepcopy(e)
 require(sum(x['completed_trials'] for x in cur.values())==4400,'current accepted total')
 bysuite={}
 for e in cur.values():
  v=rd(e['root_review']['path'],e['root_review']['sha256']);states=bysuite.setdefault(v['suite'],set())
  for pair in v['reconstructed_summary']['paired_AB'].values():states.update(x['state_trial_id'] for x in pair['results'])
 expected={x:100 for x in ['libero_10','libero_spatial','libero_object','libero_goal']}
 require({k:len(v) for k,v in bysuite.items()}==expected,'unique initials')
 f.update(completed_development_trials=5612,current_action_development_trial_count=4400,current_action_development_unique_initial_states=400,current_action_development_unique_initial_states_by_suite=expected)
 return expected

def preserve_unrelated(old,after):
 require(set(old)==set(after),'top-level keys changed')
 for k in old:
  if k not in {'formal_main_progress','current_round_cost'}:require(old[k]==after[k],'unrelated state field overwritten: '+k)
 before=old['formal_main_progress'];new=after['formal_main_progress']
 allowed={'root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','completed_training_pairs','completed_development_trials','current_action_development_trial_count','current_action_development_unique_initial_states','current_action_development_unique_initial_states_by_suite','new_action_development_verified_by_job','nonLong_development_submissions_1418','latest_new_action_development_verified','Spatial256_three_seed_development_statistics','Object256_partial_development_statistics','integration_20261020T1530_accepted'}
 require(set(new)-set(before)<=allowed and set(before)<=set(new),'unexpected formal keys')
 for k in before:
  if k not in allowed:require(before[k]==new[k],'unrelated formal state overwritten: '+k)
 for k,v in before['completed_training_pairs'].items():
  if k!=PAIR:require(new['completed_training_pairs'][k]==v,'other training pair changed')
 require(set(before['completed_training_pairs'])==set(new['completed_training_pairs']),'training pair set changed')
 for k,v in before['completed_training_pairs'][PAIR].items():require(new['completed_training_pairs'][PAIR][k]==v,'prior target machine evidence changed')
 for k,v in before['new_action_development_verified_by_job'].items():require(new['new_action_development_verified_by_job'][k]==v,'old development record changed')
 for k,v in old['current_round_cost'].items():
  if k not in {'allocated_gpu_seconds','allocated_gpu_hours'}:require(after['current_round_cost'][k]==v,'other cost field changed')

def prepare(s,before,d,obs,cap,now):
 old=copy.deepcopy(s);s=copy.deepcopy(s);precondition(s)
 require(not cap['unknown'] and not cap['findings'] and len(cap['occupied'])<=8,'fresh capacity')
 require(obs['rows']['3034538']['status']=='RUNNING' and obs['rows']['3034538']['gpus']==0,'controller health')
 ids=[str(j['job_id']) for j in s['registered_jobs']];require(len(ids)==len(set(ids)),'duplicate registered job allocation')
 for jid,suite,budget,seed,secs,pin in JOBS:
  x=[j for j in s['registered_jobs'] if str(j['job_id'])==jid];require(len(x)==1 and x[0]['suite']==suite and set(x[0]['method_ids'])=={f'A{budget}_seed{seed}',f'B{budget}_seed{seed}'},'registered terminal identity')
 for jid,secs in [(j[0],j[4]) for j in JOBS]+[('3043762',60721)]:
  row=obs['rows'][jid];require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==secs,'terminal Slurm accounting')
 seconds=sum(obs['rows'][str(j['job_id'])]['elapsed_seconds']*obs['rows'][str(j['job_id'])]['gpus'] for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2')
 require(seconds>=s['current_round_cost']['allocated_gpu_seconds'],'GPU accounting regressed')
 expected=accept_terminals(s,d);f=s['formal_main_progress'];pair=f['completed_training_pairs'][PAIR]
 pair.update(job_id='3043762',suite='libero_goal',visual_tokens=64,seed=17,root_review=PINS['training_root'][0],root_review_sha256=PINS['training_root'][1],independent_review=PINS['training_independent'][0],independent_review_sha256=PINS['training_independent'][1],selected_checkpoints=d['selected'],selected_server_review=PINS['selected_server'][0],selected_server_review_sha256=PINS['selected_server'][1],root_and_independent_verification_kind='completed_original_root_and_independent_training_review')
 f['root_and_independent_completed_arms']=66;f['root_and_independent_reviewed_arm_updates']=331000
 suites={}
 for suite,v in d['statistics']['suites'].items():
  suites[suite]={k:v[k] for k in ['available_seeds','missing_seeds','unique_initial_states','trial_count','means_percent','seed_sample_SD_pp','bootstrap_computed']}
  if 'bootstrap_interval95_pp' in v:suites[suite]['bootstrap_interval95_pp']=v['bootstrap_interval95_pp']
 stats=dict(schema='formal_main_v2',kind='accepted_256_development_diagnostics',new_trials=600,suites=suites,full_seed_task_tokens_offline_validation=pref('statistics'),terminal_review=pref('independent'),Spatial_paired_matrix=pref('matrix'),root_bootstrap_recomputation=pref('root_bootstrap'),root_bootstrap_provenance='Root reran the archived independent algorithm; deterministic output identity does not claim a separately invented algorithm.',accepted_jobs_GPU_seconds=6678,costs_already_in_global_Slurm_total=True,development_only=True,action_error_scope='Selected checkpoint offline hard validation teacher/demo L1, not closed-loop action error.',no_equivalence_or_O2A_claim=True,final_results=False)
 statref=ref(STATS,hashlib.sha256(rawjson(stats)).hexdigest())
 f['latest_new_action_development_verified']=statref;f['Spatial256_three_seed_development_statistics']=statref;f['Object256_partial_development_statistics']=statref
 s['current_round_cost'].update(allocated_gpu_seconds=seconds,allocated_gpu_hours=seconds/3600)
 summary=dict(schema='formal_main_v2',kind='completed_training_and_development_evidence_integration',utc=now,state_before_sha256=before,
  new_training_groups_accepted=2,root_independent_complete=66,total_training_arms=72,new_reviewed_arm_updates=10000,root_independent_updates=331000,
  new_development_trials=600,current_action_development_trials=4400,raw_historical_and_current_accepted_development_trials=5612,
  current_action_unique_initial_states=400,unique_current_initial_states_by_suite=expected,explicit_legacy_equivalent_Long_trials=600,compatible_current_and_explicit_legacy_trials=5000,
  accepted_training_root=pref('training_root'),accepted_training_independent=pref('training_independent'),selected_server_proof=pref('selected_server'),accepted_jobs=d['entries'],diagnostics=statref,
  original_downstream_blockers_retained=f['downstream_blockers_20261020T1418'],held_Goal256_job='3049679',held_trials=200,held_trials_in_success_rate_denominator=False,Object256seed23_bridge_scientifically_admitted=False,
  new_GPU_jobs_by_integration=0,new_dispatches_created=0,new_dispatch_trials_accepted=0,controller_and_pending_and_reservations_and_registry_preserved=True,
  active_GPU_jobs=len(cap['occupied']),capacity=cap,scheduler=obs,allocated_GPU_seconds=seconds,allocated_GPU_hours=seconds/3600,
  all_registered_allocations_counted_once=True,acceptance_allocation_seconds_not_added_again=67399,cost_is_final=False,
  final_completed=0,final_expected=35200,final_release=False,source173_unchanged=True,scientific_settings_changed=False,automatic_expansion=False,post_integration_independent_review_pending=True)
 summaryref=ref(SUMMARY,hashlib.sha256(rawjson(summary)).hexdigest());f['integration_20261020T1530_accepted']=summaryref
 preserve_unrelated(old,s)
 return s,summary,{SUMMARY:rawjson(summary),STATS:rawjson(stats),B+'/root_operations/integrate_1530_v1.py':Path(__file__).read_bytes()}

def prepend(raw,text):
 first,sep,rest=raw.partition(b'
');require(bool(sep),'document heading');return first+b'

'+text.encode()+b'

'+rest

def documents(d,summary,stamp):
 hours=summary['allocated_GPU_hours'];occupied=summary['active_GPU_jobs']
 brief=f"{stamp}：Goal64 seed17 A/B 已完成原 root 与独立终验，新增2组及10000已审更新，累计66/72组、331000更新。新增三批600条开发已验收（3050192/3050205/3050224）：当前动作4400条；含其他旧语义的全部验收5612条，显式兼容Long旧600另合为5000条。四套件仍为400个唯一开发初态。当前{occupied}个GPU作业占槽，累计{hours:.3f}GPU小时，全部登记Slurm分配只计一次。此完成结果事务不提交作业，也不把之后的新派发或工程探针计为完成。Goal256 seed17原200条HOLD保留，Object256 seed23兼容桥仍未科学准入；最终0/35200，封存门槛不变。见[本轮接纳收据](../{SUMMARY})。"
 lines=['本轮均为开发诊断；选模继续只用原validation。完整历史结果保留。','', '| 套件 | tokens | seed | A/100 | B/100 | B−A pp | t0交集/预算 | t0 Jaccard |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for e in d['entries']:
  n=e['seed'];lines.append(f"| {e['suite']} | 256 | {n} | {e['successes'][f'A256_seed{n}']} | {e['successes'][f'B256_seed{n}']} | {e['B_minus_A_percentage_points']:+.0f} | {e['initial_observation_token_overlap_mean']:.6f} | {e['initial_observation_token_Jaccard_mean']:.6f} |")
 lines+=['', 'Spatial256三seed：17为98/99，23为99/97，41为97/99。均值A98.000%、B98.333%、B−A +0.333pp；种子样本SD分别1.000、1.155、2.082pp。固定10000次任务内初态簇bootstrap（seed20261016），每簇携带完整三seed。95%区间A[95.667,99.667]%、B[96.667,99.667]%、B−A[−0.667,+1.333]pp。100个唯一初态不能当作300个；区间跨零不意味着等效。', '', 'Object256仅已有17和41：98/99、97/98，描述均值A97.5%、B98.5%，B−A +1pp。seed23下游来源兼容仍待准入，不补造三seed均值或置信区间。', '', '没有同checkpoint完整O2A结果，本轮不宣称剪枝折中改善、等效或实测加速，也未按Dense区间完成−2pp实用目标判断。未来误差和硬验证L1只作诊断。', '', f'三批开发6678GPU秒、Goal64训练60721GPU秒均属于已有Slurm分配；接受证据不增加这些成本第二次。[完整逐任务/逐seed/离线L1](../{E}/terminal_independent/development_statistics.json)，[root重算](../{PINS["root_bootstrap"][0]})。root重用并独立执行审计方算法，输出字节相同源自确定性计算，不声称算法另行独立实现。']
 details=['# 正式Spatial轻度剪枝开发结果','',brief,'']+lines
 g=d['statistics']['suites']['libero_spatial']
 details+=['','| seed | task_id | A/10 | B/10 | B−A pp |','|---|---:|---:|---:|---:|']
 for t in g['per_task']:details.append(f"| {t['seed']} | {t['task_id']} | {t['A_successes']} | {t['B_successes']} | {t['B_minus_A_pp']:+.0f} |")
 details+=['','| seed/臂 | 选中update | 硬验证teacher L1 | 硬验证示范L1 | 验证窗口 |','|---|---:|---:|---:|---:|']
 for v in g['per_seed']:
  for arm,dg in v['offline_validation_diagnostics'].items():details.append(f"| {v['seed']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |")
 details+=['','L1属于原硬剪枝validation，不是闭环动作误差；t0 token重合仅在相同观测上比较。开发成功/失败不重选checkpoint。','']
 out={};pins={}
 for name in DOCS:
  rel='docs/'+name+'.md';raw=path(rel).read_bytes();pins[rel]=hashlib.sha256(raw).hexdigest()
  out[rel]=prepend(raw,brief+ ('

'+'
'.join(lines) if name=='正式非Long开发结果' else ''))
 out['docs/正式Spatial轻度剪枝开发结果.md']='
'.join(details).encode()
 return out,pins

def write_new(rel,raw):
 p=path(rel);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def replace_document(rel,raw,pin):
 p=path(rel);require(sha(p)==pin,'document CAS '+rel);tmp=p.with_name(p.name+'.'+uuid.uuid4().hex+'.partial')
 with tmp.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 require(sha(p)==pin,'document changed before replace');os.replace(tmp,p)
def assert_transaction_available(outputs,docs,pins):
 for rel in [INTENT,COMPLETION,B+'/integration_1530_state_before.json',*outputs]:require(not path(rel).exists(),'prior transaction exists; root must reconcile '+rel)
 for rel in docs:
  if rel not in pins:require(not path(rel).exists(),'new document exists')
def run(args):
 c=mod('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','integration1530controller')
 d=inputs()
 with c.exclusive_lock(path('results/experiment_supervisor/.writer.lock')):
  sp=path('results/experiment_supervisor/state.json');before_raw=sp.read_bytes();before=hashlib.sha256(before_raw).hexdigest();s=json.loads(before_raw);precondition(s)
  obs=c.Slurm(timeout=45).observe(s['registered_jobs']);cap=c.capacity(s['registered_jobs'],obs,s['autonomous_training_v1']['controller_job_id'])
  now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M CST')
  after,summary,outputs=prepare(s,before,d,obs,cap,now);docs,pins=documents(d,summary,stamp);assert_transaction_available(outputs,docs,pins)
  require(sha(sp)==before,'state changed while locked')
  if not args.apply:
   base=PRIVATE+'/preview_'+uuid.uuid4().hex[:12]
   for rel,raw in {**outputs,**docs}.items():write_new(base+'/'+rel,raw)
   write_new(base+'/state_before.json',before_raw);write_new(base+'/state_candidate.json',rawjson(after))
   receipt=dict(status='private_preview_only_not_applied',state_before_sha256=before,preview_root=base,canonical_state_unchanged=sha(sp)==before,canonical_docs_unchanged=all(sha(path(p))==v for p,v in pins.items()),new_GPU_jobs=0,accepted_training_increment=2,accepted_update_increment=10000,accepted_development_increment=600,training66=True,updates331000=True,current_action4400=True,total_accepted5612=True,compatible5000=True,unique400=True,machine_completion_preserved=s['formal_main_progress']['trained_arms'],pending_reservations_registry_preserved=True,GPU_hours=summary['allocated_GPU_hours'],occupied=len(cap['occupied']))
   write_new(base+'/receipt.json',rawjson(receipt));print(json.dumps(receipt,ensure_ascii=False));return
  intent=dict(schema='formal_main_v2',kind='root_completed_evidence_integration_intent',utc=now,state_before_sha256=before,source=ref(str(Path(__file__).relative_to(R))),state_candidate_sha256=hashlib.sha256(rawjson(after)).hexdigest(),writes={rel:hashlib.sha256(raw).hexdigest() for rel,raw in {**outputs,**docs}.items()},previous_document_sha256=pins,inputs={k:pref(k) for k in PINS},requires_manual_reconciliation_after_interruption=True)
  write_new(INTENT,rawjson(intent));write_new(B+'/integration_1530_state_before.json',before_raw)
  for rel,raw in outputs.items():write_new(rel,raw)
  for rel,raw in docs.items():
   if rel in pins:replace_document(rel,raw,pins[rel])
   else:write_new(rel,raw)
  c.atomic_json(sp,after,before)
  result=dict(status='root_integrated_post_independent_review_pending',state_before_sha256=before,state_after_sha256=sha(sp),summary=ref(SUMMARY),documents={rel:ref(rel) for rel in docs},controller_pending_reservations_registry_unchanged=True,new_GPU_jobs_by_integration=0,new_training_groups_accepted=2,new_development_trials_accepted=600,new_dispatch_trials_accepted=0,held_Goal_trials_unaccepted=200)
  write_new(COMPLETION,rawjson(result));print(json.dumps(result,ensure_ascii=False))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true',help='Root explicit application after independent review; default private preview.');run(ap.parse_args())
if __name__=='__main__':main()
