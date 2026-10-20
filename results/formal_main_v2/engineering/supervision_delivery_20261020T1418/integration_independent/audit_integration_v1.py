from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys,os,time,traceback,importlib.util,argparse,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e'
D=R/'.local/integration_independent_20261020T1418';B='results/formal_main_v2/preflight/heartbeat_20261020T2218';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1418/terminal_independent'
SRC='.local/integration_candidate_20261020T1418/integrate_1418_v2.py';PIN='b2c472fded9a1eed04ab769a97592b347e93b86d3c1a73c8ba28e96c3a807efd'
PREVIEW='.local/integration_candidate_20261020T1418/preview_df3ead4d8590';checks=[];inputs={};start=time.perf_counter()
def guard(event,args):
 if event.startswith(('socket.','subprocess.')) or event in ['os.system','os.fork','os.posix_spawn']:raise PermissionError(event)
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(args[0]);mode=args[1];flags=args[2]
  if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):assert p.resolve().is_relative_to(D.resolve()),str(p)
  assert p.suffix not in ['.pt','.pth','.safetensors','.bin'],'weight read'
  assert 'initial_states/final' not in str(p),'sealed values'
sys.addaudithook(guard)
def sha(b):return hashlib.sha256(b).hexdigest()
def raw(rel,pin=None,base=R,track=True):
 p=base/rel;assert p.is_file() and not p.is_symlink(),str(p);b=p.read_bytes();h=sha(b)
 if pin:assert h==pin,(rel,h,pin)
 if track:inputs[str(p)]=dict(path=str(p),sha256=h,bytes=len(b))
 return b
def rd(rel,pin=None,base=R):return json.loads(raw(rel,pin,base))
def rr(ref,base=R):return rd(ref['path'],ref['sha256'],base)
def ref(rel,base=R):b=raw(rel,base=base);return dict(path=rel,sha256=sha(b))
def ck(name,v):assert v,name;checks.append(name)
def out(name,v):
 p=D/name;assert not p.exists(),str(p);p.write_bytes((json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode());return dict(path=str(p.relative_to(R)),sha256=sha(p.read_bytes()),bytes=p.stat().st_size)
def same_float(a,b):return abs(a-b)<1e-9

def main(mode):
 source=raw(SRC,PIN);t=source.decode();old=raw('.local/integration_candidate_20261020T1418/integrate_1418_v1.py','344eecea170003398fcbf6d197d9184154aee4efa449156bc86ab36e6fd47c05').decode()
 guardline=" row=obs['rows']['3043762'];require(row['status']=='COMPLETED' and row['exit_code']=='0:0' and row['gpus']==1 and row['elapsed_seconds']==60721,'unaccepted training terminal identity')\n"
 expect=old.replace(" expected=accept_terminals(s,d);",guardline+" expected=accept_terminals(s,d);").replace("B+'/root_operations/integrate_1418_v1.py'","B+'/root_operations/integrate_1418_v2.py'")
 ck('only_recorded_training_terminal_guard_and_archive_name_changes',t==expect)
 ck('source_explicit_apply_default_private_and_writer_CAS',"ap.add_argument('--apply',action='store_true'" in t and "with c.exclusive_lock(path('results/experiment_supervisor/.writer.lock'))" in t and "c.atomic_json(sp,after,before)" in t and "state changed while locked" in t)
 ck('source_controller_registry_and_training_preservation',"s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs']" in t and "f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs']" in t and "f['automatic_machine_verified_pairs']==old['formal_main_progress']['automatic_machine_verified_pairs']" in t)
 ck('source_intent_before_mutation_and_documents_CAS',t.index("write_new(B+'/integration_1418_intent.json'")<t.index('for rel,raw in outputs.items():write_new')<t.index('c.atomic_json(sp,after,before)') and 'document CAS ' in t and 'document changed before replace' in t)
 modspec=importlib.util.spec_from_file_location('independent_readonly_integration_candidate',R/SRC);m=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(m)
 dispatch=rd(B+'/dispatch_root_report.json','69089fa48014bda5a438879d1e63e24990488b9539e08697ae15ee7fda153304')
 sub=rd('.local/integration_independent_20261020T1418/submission_independent_review.json','ea7336b1f5c449e42614a282a371355532796f6f82d7084ec92c81f3ea7402a5')
 ds=rd('.local/integration_independent_20261020T1418/Goal_dense_statistics_independent_review.json','751d744e09d3cd5c6afb2ff3e03bdc6ef369bb9c7e39ca1426eff681900d75bd')
 terminal=rd(E+'/independent_review.json','ad8c588b38df5d774f7da678ff75b2931743156de8b1e4d373f1f5358c22fead')
 stats=rd(E+'/development_statistics.json','26db7c37f100857e7e789dc7fbea74e0c2c2728e864a8b35f8fdde7ddc97c1cd')
 ck('prior_true_submission_and_full_1000_terminal_review',sub['status']==terminal['status']==ds['status']=='passed' and sub['planned_trials']==600 and terminal['totals']['trials']==1000 and terminal['held_job_ids']==['3049679'] and not terminal['state_registry_Git_Slurm_mutations'])
 base=R/PREVIEW if mode=='preview' else R
 summary=rd(B+'/summary_after_dispatch.json','071344486b97e868fe4b5741fb353b7be1a960e0fbaecf4753a27b60699c4d8e' if mode=='preview' else None,base)
 if mode=='preview':
  receipt=rd('receipt.json','9442a2b0c7efa4946523b8192874955a24d538ab7e2c8b37aa6204c2bc56b379',base)
  state=rd('state_candidate.json','04a51f6a54e5efb0fab068d9a3e988a5c46bbd08c12320e7bb23c389a20679ce',base)
  ck('actual_private_preview_preserved_canonical_docs_state',receipt['status']=='private_preview_only_not_applied' and receipt['canonical_state_unchanged'] and receipt['canonical_docs_unchanged'] and receipt['new_GPU_jobs']==0 and receipt['state_before_sha256']==summary['state_before_sha256'])
  tl=raw('results/formal_main_v2/control_transport/integration_candidate_preview_20261020T1418_v2.jsonl');logs=[json.loads(x) for x in tl.splitlines() if x.strip()];ck('preview_exact_transport_success',logs[-1]['returncode']==0 and logs[-1]['source173_and_entrypoint_unchanged'])
 else:
  intent=rd(B+'/integration_1418_intent.json');receipt=rd(B+'/integration_1418_completion.json');before=rd(B+'/integration_1418_state_before.json')
  ck('intent_exact_entrypoint_dispatch_and_before_snapshot',intent['source']==dict(path=SRC,sha256=PIN) and intent['dispatch']==summary['dispatch'] and intent['state_before_sha256']==summary['state_before_sha256']==receipt['state_before_sha256'])
  d=m.inputs();state,re_summary,re_outputs=m.prepare(before,intent['state_before_sha256'],d,dispatch,intent['dispatch'],summary['scheduler'],summary['capacity'],summary['utc'])
  ck('exact_pure_reconstruction_matches_committed_state_and_summary',m.rawjson(re_summary)==raw(B+'/summary_after_dispatch.json') and sha(m.rawjson(state))==intent['state_candidate_sha256']==receipt['state_after_sha256'])
  for rel,pin in intent['writes'].items():raw(rel,pin)
  ck('committed_outputs_exact_intent',receipt['status']=='root_integrated_post_independent_review_pending' and receipt['controller_registry_unchanged'] and receipt['new_GPU_jobs_by_integration']==0 and receipt['new_development_trials_accepted']==1000 and receipt['held_trials']==200 and receipt['new_dispatch_trials_accepted']==0)
  ck('original_controller_registry_training_not_overwritten',state['autonomous_training_v1']==before['autonomous_training_v1'] and state['registered_jobs']==before['registered_jobs'] and state['formal_main_progress']['completed_training_pairs']==before['formal_main_progress']['completed_training_pairs'] and state['formal_main_progress']['automatic_machine_verified_pairs']==before['formal_main_progress']['automatic_machine_verified_pairs'])
  f0=before['formal_main_progress'];ck('exact_counts_increment_1000_no_preexisting_mutation',f0['completed_development_trials']==4012 and f0['current_action_development_trial_count']==2800 and all(state['formal_main_progress']['new_action_development_verified_by_job'][k]==v for k,v in f0['new_action_development_verified_by_job'].items()))
  live=rd('results/experiment_supervisor/state.json');ck('live_core_matches_applied_core',all(live['formal_main_progress'][k]==state['formal_main_progress'][k] for k in ['new_action_development_verified_by_job','current_action_development_trial_count','completed_development_trials','Goal128_three_seed_development_statistics','downstream_blockers_20261020T1418','nonLong_development_submissions_1418']) and live['autonomous_training_v1']['controller_job_id']=='3034538')
 raw(B+'/root_operations/integrate_1418_v2.py',PIN,base)
 f=state['formal_main_progress'];a=state['autonomous_training_v1'];cur=f['new_action_development_verified_by_job']
 ck('training_64_not_auto66_and_321000_updates',f['root_and_independent_completed_arms']==summary['root_independent_complete']==64 and f['root_and_independent_reviewed_arm_updates']==summary['root_independent_updates']==321000 and summary['new_training_groups_accepted']==0)
 tr=summary['scheduler']['rows']['3043762'];ck('fresh_3043762_completed_unaccepted',summary['completed3043762_not_accepted_here'] and tr['status']=='COMPLETED' and tr['exit_code']=='0:0' and tr['gpus']==1 and tr['elapsed_seconds']==60721)
 ck('final0_35200_and_controller_owner_preserved',f['completed_final_trials']==summary['final_completed']==0 and summary['final_expected']==35200 and not f['test_opened'] and not f['global_release_created'] and not summary['final_release'] and a['controller_job_id']==summary['controller']=='3034538' and a['owner_id']==summary['controller_owner_id']=='6b3beba5cdeb41df9d749b0b2054d485')
 ck('exact3_dispatches_600_pending_science',summary['new_submissions']==dispatch['submissions']==f['nonLong_development_submissions_1418'] and [x['job_id'] for x in summary['new_submissions']]==[x['job_id'] for x in sub['jobs']]==['3050192','3050205','3050224'] and all(x['completed_trials_accepted']==0 for x in summary['new_submissions']) and summary['new_planned_trials']==600 and summary['new_submitted_trials_accepted']==0)
 ck('no_pending_or_reservation_cleared',state['pending_submission'] is None and a['reserved_GPU_slots']==0 and a['root_submission_hold'] is None)
 accepted=summary['accepted_jobs'];ck('five_200trial_precise_members',len(accepted)==5 and {v['job_id'] for v in accepted}==set(terminal['jobs']) and sum(v['completed_trials'] for v in accepted)==1000 and all(v['reference_trials']==0 and v['AB_trials']==200 for v in accepted))
 for entry in accepted:
  jid=entry['job_id'];j=terminal['jobs'][jid];rrr=rr(entry['root_review']);ck(jid+'_accepted_exact_original_report',cur[jid]==entry and entry['completed_trials']==j['trials']==rrr['completed_trials']==200 and entry['successes']==j['successes']=={k:x['successes'] for k,x in rrr['reconstructed_summary']['methods'].items()} and entry['per_task']==j['per_task'] and entry['paired_outcomes']==j['discordance'] and entry['B_minus_A_percentage_points']==j['B_minus_A_pp'] and entry['root_review']==j['root_receipt'])
  ck(jid+'_immutable_offline_and_token_diag',entry['offline_validation_diagnostics']==j['offline_validation_diagnostics'] and entry['initial_observation_token_overlap_mean']==j['t0_token_diagnostics']['mean_intersection_over_budget'] and entry['initial_observation_token_Jaccard_mean']==j['t0_token_diagnostics']['mean_Jaccard'] and j['t0_token_diagnostics']['all_t0_observation_hashes_equal'] and entry['visual_tokens']==j['A_B_visual_tokens'])
  hist=next(x for group in ['nonLong_development_submissions_1220','nonLong_development_submissions_1317'] for x in f[group] if x['job_id']==jid);ck(jid+'_original_pending_record_closed_once',hist['completed_trials_accepted']==200 and not hist['scientific_terminal_acceptance_pending'] and hist['terminal_root_review']==entry['root_review'])
 ck('5000_training_acceptance_does_not_advance_from_new_development',sum(v['completed_trials'] for v in cur.values())==3800==f['current_action_development_trial_count']==summary['current_action_development_trials'] and f['completed_development_trials']==summary['raw_historical_and_current_accepted_development_trials']==5012 and f['historical_other_action_semantics_development_trials']==1212 and f['Long22_development_statistics']['explicit_legacy_equivalent_trials']==600 and summary['compatible_current_and_explicit_legacy_trials']==4400)
 uniq={}
 for entry in cur.values():
  rrr=rr(entry['root_review']);bucket=uniq.setdefault(rrr['suite'],set())
  for pair in rrr['reconstructed_summary']['paired_AB'].values():bucket.update(x['state_trial_id'] for x in pair['results'])
 ck('four_suites400_unique_not_seed_inflated',{k:len(v) for k,v in uniq.items()}==summary['unique_current_initial_states_by_suite']==f['current_action_development_unique_initial_states_by_suite']=={k:100 for k in ['libero_10','libero_spatial','libero_object','libero_goal']} and f['current_action_development_unique_initial_states']==400)
 block=rr(summary['blockers'],base);goal=block['Goal256_seed17'];obj=block['Object256_seed23'];held=next(x for x in f['nonLong_development_submissions_1317'] if x['job_id']=='3049679')
 ck('whole200Goalheld_not_in_denominator',summary['held_trials']==goal['retained_trials']==held['retained_unaccepted_trials']==200 and goal['accepted_trials']==held['completed_trials_accepted']==0 and '3049679' not in cur and not summary['held_trials_in_success_rate_denominator'] and goal['actual_GPU_seconds']==held['GPU_seconds_retained']==2034 and goal['status']=='HOLD' and not goal['proposal_run'] and not goal['scientific_retry_authorized'])
 rr(goal['root_failure']);gd=rr(goal['independent_diagnosis']);ck('Goal_original_guard_preserved_not_bypassed',gd['original_guard_reproduced']['message']=='Paired initial observation differs across methods/attempts' and not gd['existing_raw_arrays_available'] and block['no_gate_waiver'])
 of=rr(obj['evidence']);ck('Object23_original_metadata_block_preserved',obj['status']=='HOLD_original_downstream_metadata_consumer' and obj['root_training_completion_unchanged'] and not obj['fake_metadata_repair_allowed'] and obj['new_GPU_seconds']==obj['new_scientific_trials']==0 and of['missing_in_ordinary_metadata_history']==['3028460'])
 diag=rr(summary['diagnostics'],base);ck('Goal_stats_acceptance_root_and_independent_bound',diag['new_trials']==1000 and diag['development_only'] and not diag['final_results'] and diag['no_equivalence_or_O2A_claim'] and diag['full_seed_task_outcomes_tokens_and_offline_validation_L1']['sha256']=='26db7c37f100857e7e789dc7fbea74e0c2c2728e864a8b35f8fdde7ddc97c1cd' and diag['root_bootstrap_recomputation']['sha256']=='4fa41c33af982608618ed7eeb85abbd646abedd2302c2c0a185cf4db65033dd1')
 for suite,g in stats['suites'].items():
  dg=diag['suites'][suite];ck(suite+'_all_existing_seed_stats_exact',all(g[k]==v for k,v in dg.items()))
  if suite!='libero_goal':ck(suite+'_no_fake_seed17_or_three_seed_CI',g['available_seeds']==[23,41] and g['missing_seeds']==[17] and not g['bootstrap_computed'])
 ids=[str(x['job_id']) for x in state['registered_jobs'] if x.get('experiment')=='formal_main_v2'];obs=summary['scheduler']['rows'];ck('all_registered_cost_ids_unique',len(ids)==len(set(ids)) and all(j in obs for j in ids))
 secs=sum(obs[j]['elapsed_seconds']*obs[j]['gpus'] for j in ids);ck('all_Slurm_allocations_once_no_free_shared_or_failed_cost',secs==summary['allocated_GPU_seconds']==state['current_round_cost']['allocated_gpu_seconds'] and same_float(secs/3600,summary['allocated_GPU_hours']) and not summary['cost_is_final'] and diag['costs_already_in_global_Slurm_total'] and diag['accepted_jobs_GPU_seconds']==11116 and diag['held_job_GPU_seconds']==2034)
 cap=summary['capacity'];ck('six_snapshot_GPU_slots_including3dev3training',len(cap['occupied'])==summary['active_GPU_jobs']==6 and not cap['unknown'] and not cap['findings'] and all(obs[j]['status']=='RUNNING' and obs[j]['gpus']==1 for j in cap['occupied']) and obs['3034538']['status']=='RUNNING' and obs['3034538']['gpus']==0)
 docs={};briefparts=['64/72','1000条','200条','2034GPU秒','97.333%/B96.000%','−1.333pp','[−3.667,+0.667]','600条','3800条','4400条','400唯一初态','5012条','最终0/35200']
 for name in m.DOCS:
  rel='docs/'+name+'.md';b=raw(rel,base=base);text=b.decode();new=text.split('\n\n')[1];ck('doc_'+name+'_exact_new_progress',all(x in new for x in briefparts) and f'{secs/3600:.3f}GPU小时' in new);docs[rel]=sha(b)
 goaltext=raw('docs/正式Goal主预算开发结果.md',base=base).decode().split('下面保留此前')[0];g=stats['suites']['libero_goal']
 ck('Goal_doc_dense_intervals_recomputed_originals',all(x in goaltext for x in ['[−2.667,+3.667]','[−4.333,+2.000]','均未满足','不能解释为等效','没有同checkpoint完整O2A','10000次','100初态不因seed重复增至300','ddof=1','600条','参考共享400条']) and ds['unique_initials']==100 and ds['shared_dense_trials']==100 and ds['checks_passed']==425)
 for row in g['per_seed']:
  fmt=f"| {row['seed']} | {row['A_successes']} | {row['B_successes']} | {row['B_minus_A_pp']:+.0f} | {row['token_intersection_over_128']:.6f} | {row['token_Jaccard']:.6f} |";ck('Goal_doc_seed'+str(row['seed']),fmt in goaltext)
  for arm,dg in row['offline_validation_diagnostics'].items():
   fmt=f"| {row['seed']}/{arm} | {dg['selected_update']} | {dg['hard_validation_teacher_L1_task_equal']:.8f} | {dg['hard_validation_demonstration_L1_task_equal']:.8f} | {dg['validation_windows']} |";ck('Goal_doc_offline_'+str(row['seed'])+arm,fmt in goaltext)
 for row in g['per_task']:
  fmt=f"| {row['seed']} | {row['task_id']} | {row['A_successes']} | {row['B_successes']} | {row['B_minus_A_pp']:+.0f} |";ck('Goal_doc_task_'+str(row['seed'])+'_'+str(row['task_id']),fmt in goaltext)
 nt=raw('docs/正式非Long开发结果.md',base=base).decode().split('下面保留历史记录')[0]
 for en in accepted:
  seed=en['seed'];bud=en['visual_tokens'];fmt=f"| {en['suite']} | {bud} | {seed} | {en['successes'][f'A{bud}_seed{seed}']} | {en['successes'][f'B{bud}_seed{seed}']} | {en['B_minus_A_percentage_points']:+.0f} | {en['initial_observation_token_overlap_mean']:.6f} | {en['initial_observation_token_Jaccard_mean']:.6f} |";ck('new_nonLong_doc_'+en['job_id'],fmt in nt)
 bt=raw('docs/正式下游阻塞登记_20261020T1418.md',base=base).decode();ck('block_doc_entire_quarantine_and_unrun_engineering_only',all(x in bt for x in ['原200条整批HOLD','不能据此删除单条或接受其余199条','尚未运行','最多1GPU/30分钟','3028460','不得伪造普通metadata','不改变损失、跨度、任务、seed']))
 inv=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck('173_frozen_count',len(inv['files'])==173)
 for rel,pin in inv['files'].items():raw(rel,pin,track=False);raw(rel,pin,base=S,track=False)
 ck('173_actual_R_S_bytes_unchanged',True)
 ev=out(mode+'_integration_check_evidence.json',dict(schema='formal_main_v2',status='passed',mode=mode,checks=checks,inputs=list(inputs.values()),document_hashes=docs,summary_ref=ref(B+'/summary_after_dispatch.json',base),reconstructed_cost_seconds=secs))
 rep=out(mode+'_integration_independent_review.json',dict(schema='formal_main_v2',kind='independent_'+mode+'_integration_review',status='passed',mode=mode,utc=datetime.now(timezone.utc).isoformat(),reviewer='/root/devplans_audit_20261020_1418',source_ref=dict(path=str(Path(__file__).relative_to(R)),sha256=sha(Path(__file__).read_bytes())),root_integration_source=dict(path=SRC,sha256=PIN),check_evidence=ev,checks_passed=len(checks),blocking_findings=[],accepted_new_development_trials=1000,held_Goal256_trials=200,new_development_submissions=3,new_planned600_accepted=0,training_accepted64_72=True,current_action_trials=3800,raw_accepted_trials=5012,compatible_current_and_explicit_legacy=4400,unique_initials=400,Goal_unique_initials=100,shared_dense_bootstrap_independent=dict(path='.local/integration_independent_20261020T1418/Goal_dense_statistics_independent_review.json',sha256='751d744e09d3cd5c6afb2ff3e03bdc6ef369bb9c7e39ca1426eff681900d75bd'),GPU_seconds_snapshot=secs,GPU_hours_snapshot=secs/3600,GPU_slots_snapshot=6,final_completed=0,final_expected=35200,final_release=False,source173_R_S_unchanged=True,actual_root_apply_verified=mode=='applied',new_GPU_jobs=0,new_GPU_seconds=0,new_scheduler_queries=0,checkpoint_bytes_read=False,sealed_final_values_read=False,state_Git_Slurm_modified=False,CPU_wall_seconds=time.perf_counter()-start,limitations=['This audit does not submit or mutate canonical state.','Original terminal full raw audits reused, not re-executed.','Saved scheduler observations only; no live GPU polling.','No new train acceptance, no O2A, no final release.']))
 print(json.dumps(dict(status='passed',mode=mode,report=rep,checks=len(checks),cost=secs)))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preview','applied'],required=True);args=p.parse_args()
 try:main(args.mode)
 except Exception as e:out(args.mode+'_integration_failure_v1.json',dict(status='failed',error=repr(e),traceback=traceback.format_exc(),checks_completed=checks));raise
