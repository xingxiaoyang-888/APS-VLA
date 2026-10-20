"""Independent read-only audit of completed-evidence integration candidate. Never applies."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys,ast
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=R/'.local/completed_integration_independent_20261020T1530'
V=R/'.local/integration_candidate_20261020T1530/preview_95f917f55464'
B='results/formal_main_v2/preflight/heartbeat_20261020T2330'
SRC=R/'.local/integration_candidate_20261020T1530/integrate_1530_v2.py'
SRC_SHA='c05d049e4d56d82708a64e05802ca9281f91f191d3e510ccbbc54550a8d25219'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1530'
checks=[];evidence={}
def audit(event,args):
 if event=='open':
  target,mode,flags=args
  if isinstance(target,(str,bytes,os.PathLike)) and (isinstance(mode,str) and any(c in mode for c in 'wax+') or isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)):
   assert Path(target).resolve().is_relative_to(D), 'write outside private audit'
 elif event.startswith('subprocess') or event in ['os.system','os.posix_spawn']:raise RuntimeError('no subprocess')
 elif event in ['os.mkdir','os.remove','os.rmdir','os.rename','os.replace']:
  for p in args[:2] if event in ['os.rename','os.replace'] else args[:1]:
   assert Path(p).resolve().is_relative_to(D),'mutation outside private audit'
sys.addaudithook(audit)
def check(name,value):
 if not value:raise AssertionError(name)
 checks.append(name)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def read(p,pin=None):
 p=Path(p);h=sha(p)
 if pin:check('exact_input:'+str(p),h==pin)
 if p.is_relative_to(R):evidence[str(p.relative_to(R))]=h
 else:evidence[str(p)]=h
 return json.loads(p.read_bytes())
def rdref(r):return read(R/r['path'],r['sha256'])
def put(n,v):
 p=D/n
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size}
check('candidate_source_pin',sha(SRC)==SRC_SHA);ast.parse(SRC.read_text());source=SRC.read_text()
check('root_only_explicit_apply',"if not args.apply:" in source and "ap.add_argument('--apply',action='store_true'" in source)
check('writer_lock_and_CAS_source',"with c.exclusive_lock(path('results/experiment_supervisor/.writer.lock')):" in source and 'c.atomic_json(sp,after,before)' in source and "write_new(INTENT,rawjson(intent))" in source)
check('no_source_submission_calls',not any(t in source for t in ['.submit(','sbatch','scancel','--sbatch']))
author_manifest=read(SRC.parent/'manifest.json','7d5b7b077b92ef7ee53c1c8995c88e4ca09245163c3f6d30c2cdf560b9bb182b')
check('author_package23',author_manifest['file_count']==len(author_manifest['files'])==23 and not author_manifest['canonical_mutations'])
for r in author_manifest['files']:check('author_package_file:'+r['relative_path'],sha(R/r['path'])==r['sha256'] and (R/r['path']).stat().st_size==r['bytes'])
selfcheck=read(SRC.parent/'cpu_selfcheck_v1.json','3464e91ca1d46d9802569e05b500d4586d937f60dafd7593ff905a224e9331f1')
check('author_functional_selfchecks62',selfcheck['status']=='passed' and selfcheck['count']==len(selfcheck['checks'])==62 and selfcheck['source']['sha256']==SRC_SHA and not selfcheck['canonical_mutations'] and not selfcheck['Slurm_mutations'])
receipt=read(V/'receipt.json','9dd2f9315a7ca0746f3a837704e532d16e952d6a9d145bf18aad958aef65ea62')
old=read(V/'state_before.json','dbe412a09e4e6604bcd0d7b926f7a7eaf6e96a655391a7cc7ec3c29575d90c47');new=read(V/'state_candidate.json','b3aa0a4e12dd73bd9a4816f2a0d18b873e35457ba625514db374c61d64fa8d3a')
summary=read(V/B/'completed_evidence_integration_1530.json','38fa3ca0eb982d3ad19f74da6e0c6534b7028a83970cbd5c31596e338cad6bda')
stats=read(V/B/'accepted_256_development_diagnostics_1530.json');f=old['formal_main_progress'];g=new['formal_main_progress']
check('top_level_keyset',set(old)==set(new))
for k in old:
 if k not in ['formal_main_progress','current_round_cost']:check('unchanged_top:'+k,new[k]==old[k])
allowed={'root_and_independent_completed_arms','root_and_independent_reviewed_arm_updates','completed_training_pairs','completed_development_trials','current_action_development_trial_count','current_action_development_unique_initial_states','current_action_development_unique_initial_states_by_suite','new_action_development_verified_by_job','nonLong_development_submissions_1418','latest_new_action_development_verified','Spatial256_three_seed_development_statistics','Object256_partial_development_statistics','integration_20261020T1530_accepted'}
check('formal_keyset',set(g)-set(f)<=allowed and set(f)<=set(g))
for k in f:
 if k not in allowed:check('unchanged_formal:'+k,f[k]==g[k])
check('counters_66_331000',f['root_and_independent_completed_arms']==64 and g['root_and_independent_completed_arms']==66 and f['root_and_independent_reviewed_arm_updates']==321000 and g['root_and_independent_reviewed_arm_updates']==331000)
check('machine68_330000_preserved',g['trained_arms']==f['trained_arms']==68 and g['machine_and_prior_verified_arm_updates']==f['machine_and_prior_verified_arm_updates']==330000)
check('final_still_sealed',g['completed_final_trials']==0 and not g['test_opened'] and not g['global_release_created'] and g['expected_final_trials']==35200)
for k in f['completed_training_pairs']:
 a=f['completed_training_pairs'][k];b=g['completed_training_pairs'][k]
 if k=='libero_goal_k64_seed17':
  for n,v in a.items():check('training_original_field:'+n,b[n]==v)
 else:check('training_other_pair:'+k,a==b)
cp=g['completed_training_pairs']['libero_goal_k64_seed17']
tr=read(R/cp['root_review'],'945c9605a5c1e819ba864f8b5db682dd8ddae65f219786673ae10b1c8fcd2bff')
ti=read(R/cp['independent_review'],'97a69fda379c85a6c07b56c78cddc134004359076cb2ce12b5703b73c73f5cee')
ss=read(R/cp['selected_server_review'],'b1ff86ff684df70267a1b71c46a527a3b0f45b360cef66eaf84fa4e05e64df98')
check('training_exact_dual_receipts',cp['root_review_sha256']==sha(R/cp['root_review']) and cp['independent_review_sha256']==sha(R/cp['independent_review']) and cp['selected_server_review_sha256']==sha(R/cp['selected_server_review']))
check('training_complete_identity',cp['job_id']=='3043762' and cp['suite']=='libero_goal' and cp['seed']==17 and cp['visual_tokens']==64 and tr['completed_by_arm']==ti['completed_by_arm']=={'A':5000,'B':5000} and ti['status']=='passed_complete_training_only')
check('training_not_development',not ti['final_release_authorized'] and not ti['scientific_closed_loop_claimed'] and ti['parallel_root_reconstruction']['new_reviewed_arm_updates']==10000)
check('two_selected_checkpoints',len(cp['selected_checkpoints'])==2)
for v in cp['selected_checkpoints']:
 arm=v['arm'];a=ti['arms'][arm];sv=next(x for x in ss['checks'] if x['arm']==arm)
 check('selected_original:'+arm,v['path']==sv['path'] and v['expected_sha256']==sv['sha256']==a['best_sha256'] and v['selected_update']==a['earliest_selected_update']==sv['selected_update'] and v['validation_metric']==a['selected_teacher_l1']==sv['validation_metric'])
 check('training_nodes_uses:'+arm,[x['update'] for x in a['validation']]==list(range(0,5001,500)) and a['sample_uses']==a['cursor']==40000 and a['unique_windows']==33859)
oldjobs=f['new_action_development_verified_by_job'];newjobs=g['new_action_development_verified_by_job'];newids={'3050192','3050205','3050224'}
check('exact_new_development_ids',set(newjobs)-set(oldjobs)==newids and set(oldjobs)<=set(newjobs))
for k,v in oldjobs.items():check('old_dev_untouched:'+k,newjobs[k]==v)
ind=read(R/E/'terminal_independent/independent_review.json','bc6ec59ace7431daa18056a2f64352be3f909d902644c5b0a0c546249bf879d8')
fullstats=read(R/E/'terminal_independent/development_statistics.json','3ea06d35c1f8f92a30a46449212080c3d952f08e2d1a8f633b568e75d760648a')
for jid in sorted(newids):
 e=newjobs[jid];v=ind['jobs'][jid];rr=rdref(e['root_review']);check('newdev_root_ind:'+jid,e['independent_review']=={'path':E+'/terminal_independent/independent_review.json','sha256':'bc6ec59ace7431daa18056a2f64352be3f909d902644c5b0a0c546249bf879d8'} and rr['status']=='passed' and rr['scientific_complete'] and e['completed_trials']==rr['completed_trials']==200)
 for field,sourcefield in [('successes','successes'),('B_minus_A_percentage_points','B_minus_A_pp'),('per_task','per_task'),('GPU_seconds','allocated_GPU_seconds'),('raw_ledger','raw_ledger'),('offline_validation_diagnostics','offline_validation_diagnostics'),('full_action_chunks','full_action_chunks'),('executed_control_actions','executed_control_actions')]:check('newdev_exact:'+jid+':'+field,e[field]==v[sourcefield])
 check('newdev_token:'+jid,e['initial_observation_token_overlap_mean']==v['t0_token_diagnostics']['mean_intersection_over_budget'] and e['initial_observation_token_Jaccard_mean']==v['t0_token_diagnostics']['mean_Jaccard'])
 check('newdev_not_final_or_latency:'+jid,e['reference_trials']==0 and e['AB_trials']==200 and not e['whole_suite_development_complete'] and not e['O2A_complete'])
 p=next(x for x in g['nonLong_development_submissions_1418'] if x['job_id']==jid)
 check('pending_to_accepted:'+jid,p['completed_trials_accepted']==200 and not p['scientific_terminal_acceptance_pending'] and p['terminal_root_review']==e['root_review'] and p['terminal_independent_review']==e['independent_review'])
total=0;unique={}
for jid,e in newjobs.items():
 rr=rdref(e['root_review']);total+=rr['completed_trials'];u=unique.setdefault(rr['suite'],set())
 for pair in rr['reconstructed_summary']['paired_AB'].values():u.update(v['state_trial_id'] for v in pair['results'])
check('trial_total_recomputed',total==4400==g['current_action_development_trial_count'] and sum(newjobs[j]['completed_trials'] for j in newids)==600)
check('400_unique_recomputed',{k:len(v) for k,v in unique.items()}==g['current_action_development_unique_initial_states_by_suite'] and set(unique)=={'libero_10','libero_spatial','libero_object','libero_goal'} and all(len(v)==100 for v in unique.values()) and g['current_action_development_unique_initial_states']==400)
check('historical_and_compatible_counts',g['historical_other_action_semantics_development_trials']==1212 and total+1212==g['completed_development_trials']==5612 and g['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600 and total+600==summary['compatible_current_and_explicit_legacy_trials']==5000)
check('Goal200_whole_hold', '3049679' not in newjobs and f['nonLong_development_submissions_1317']==g['nonLong_development_submissions_1317'] and next(x for x in g['nonLong_development_submissions_1317'] if x['job_id']=='3049679')['completed_trials_accepted']==0 and not summary['held_trials_in_success_rate_denominator'] and summary['held_trials']==200)
check('Object_bridge_not_admitted',summary['Object256seed23_bridge_scientifically_admitted'] is False and f['downstream_blockers_20261020T1418']==g['downstream_blockers_20261020T1418'])
for suite,v in stats['suites'].items():
 for k,x in v.items():check('statistics_exact:'+suite+':'+k,x==fullstats['suites'][suite][k])
check('statistics_provenance',stats['development_only'] and stats['no_equivalence_or_O2A_claim'] and not stats['final_results'] and stats['accepted_jobs_GPU_seconds']==6678 and stats['costs_already_in_global_Slurm_total'])
check('Object_only_two_seeds',stats['suites']['libero_object']['available_seeds']==[17,41] and stats['suites']['libero_object']['missing_seeds']==[23] and not stats['suites']['libero_object']['bootstrap_computed'])
rb=rdref(stats['root_bootstrap_recomputation']);v=fullstats['suites']['libero_spatial']
for k in ['means_percent','seed_sample_SD_pp','bootstrap_interval95_pp']:
 for n,x in rb[k].items():
  y=v[k][n];check('bootstrap_root_exact:'+k+':'+n,all(abs(a-b)<1e-9 for a,b in zip(x,y)) if isinstance(x,list) else abs(x-y)<1e-9)
check('bootstrap_scope',rb['bootstrap_seed']==20261016 and rb['bootstrap_repeats']==10000 and rb['unique_initial_states']==100 and rb['method_trials']==600)
for k in ['latest_new_action_development_verified','Spatial256_three_seed_development_statistics','Object256_partial_development_statistics']:
 r=g[k];check('summary_ref:'+k,r['path']==B+'/accepted_256_development_diagnostics_1530.json' and r['sha256']==sha(V/r['path']))
r=g['integration_20261020T1530_accepted'];check('integration_summary_ref',r['path']==B+'/completed_evidence_integration_1530.json' and r['sha256']==sha(V/r['path']))
registry={str(j['job_id']):j for j in old['registered_jobs']};check('registered_unique',len(registry)==len(old['registered_jobs']))
rawrows={}
for line in summary['scheduler']['raw_sacct'].splitlines():
 row=line.split('|');jid=row[0]
 if jid in registry:
  check('raw_sacct_unique:'+jid,jid not in rawrows);fields=dict(q.split('=',1) for q in row[4].split(',') if '=' in q);ng=int(fields.get('gres/gpu','0'));rawrows[jid]={'seconds':int(row[3]),'gpus':ng,'status':row[1],'exit':row[2]}
sec=sum(rawrows[jid]['seconds']*rawrows[jid]['gpus'] for jid,j in registry.items() if j.get('experiment')=='formal_main_v2')
check('raw_sacct_formal_total',sec==summary['allocated_GPU_seconds']==new['current_round_cost']['allocated_gpu_seconds']==1961416 and abs(new['current_round_cost']['allocated_gpu_hours']-sec/3600)<1e-12)
for jid,expect in {'3043762':60721,'3050192':2276,'3050205':2353,'3050224':2049,'3049679':2034}.items():check('allocation_original_once:'+jid,rawrows[jid]['seconds']==expect and rawrows[jid]['gpus']==1 and rawrows[jid]['status']=='COMPLETED' and rawrows[jid]['exit']=='0:0')
check('no_phase_cost_double_add',summary['acceptance_allocation_seconds_not_added_again']==60721+6678==67399 and summary['all_registered_allocations_counted_once'])
check('no_submission_or_gate_release',summary['new_GPU_jobs_by_integration']==summary['new_dispatches_created']==summary['new_dispatch_trials_accepted']==0 and summary['final_completed']==0 and summary['final_release'] is False)
inv=read(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');check('frozen_count',len(inv['files'])==173)
for rel,pin in inv['files'].items():check('frozen_R_and_S:'+rel,sha(R/rel)==sha(P/'snapshots/formal_main_v2_run_564be0995e'/rel)==pin)
newdoc='docs/正式Spatial轻度剪枝开发结果.md';docs=[]
for p in sorted((V/'docs').iterdir()):
 rel=str(p.relative_to(V));text=p.read_text();docs.append({'path':rel,'sha256':sha(p)})
 for term in ['66/72','331000','4400','5612','5000','400','0/35200','HOLD','仍未科学准入']:check('doc_summary:'+p.name+':'+term,term in text)
 if rel!=newdoc:
  previous=(R/rel).read_bytes();h,sep,tail=previous.partition(b'\n');check('doc_original_history_exact:'+p.name,p.read_bytes().startswith(h+b'\n\n') and p.read_bytes().endswith(tail))
 else:check('new_document_not_canonical',not (R/rel).exists())
spatial=(V/newdoc).read_text()
for t in v['per_task']:
 line=f"| {t['seed']} | {t['task_id']} | {t['A_successes']} | {t['B_successes']} | {t['B_minus_A_pp']:+.0f} |";check('per_task_document:'+str(t['seed'])+':'+str(t['task_id']),line in spatial)
for x in v['per_seed']:
 for arm,dg in x['offline_validation_diagnostics'].items():
  line=f"| {x['seed']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |";check('offline_diagnostic_doc:'+str(x['seed'])+arm,line in spatial)
check('same_root_operation_source',sha(V/B/'root_operations/integrate_1530_v2.py')==SRC_SHA)
report={'schema':'formal_main_v2','kind':'independent_preapply_completed_evidence_integration_review','status':'passed_private_preview_only','utc':datetime.now(timezone.utc).isoformat(),'reviewer_role':'separate from integration author; prior training and development evidence author is this reviewer','integration_author_source':{'path':str(SRC.relative_to(R)),'sha256':SRC_SHA},'reviewed_preview':str(V.relative_to(R)),'preview_state_before_sha256':sha(V/'state_before.json'),'preview_state_after_sha256':sha(V/'state_candidate.json'),'checks_passed':len(checks),'checks':checks,'new_training_groups':2,'completed_groups':66,'reviewed_updates':331000,'new_development_trials':600,'current_action_trials':4400,'raw_accepted_trials':5612,'compatible_with_explicit_Long600':5000,'unique_initial_states':400,'machine68_and330000_preserved':True,'raw_sacct_recomputed_GPU_seconds':sec,'accepted_existing_allocation_seconds_not_added_again':67399,'Goal256_200_HOLD_excluded':True,'Object256seed23_bridge_scientifically_admitted':False,'controller_pending_reservations_registry_unchanged':True,'source173_R_and_S_unchanged':True,'final_sealed':True,'applied':False,'GPU_jobs_submitted':0,'post_apply_review_performed':False,'top_level_narrative_note':'By explicit root instruction this pure acceptance transaction preserves current_work/next_actions/last_root_*; root must refresh these old narrative summaries in the final dispatch/Git summary transaction. This is not a new training or release gate.','documents':docs,'evidence_sha256':evidence}
r=put('preapply_review.json',report)
m=put('manifest.json',{'schema':'formal_main_v2','kind':'independent_preapply_completed_evidence_integration_delivery','files':[{'path':str(Path(__file__).relative_to(R)),'sha256':sha(Path(__file__))},r],'source_candidate_sha256':SRC_SHA,'private_only':True,'post_apply_pending':True})
print(json.dumps({'report':r,'manifest':m,'checks_passed':len(checks),'counts':[66,331000,4400,5612,5000,400],'GPU_seconds':sec}))
