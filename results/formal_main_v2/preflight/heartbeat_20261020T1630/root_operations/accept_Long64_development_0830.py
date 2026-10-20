from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,importlib.util,copy
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261020T1630'
E='results/formal_main_v2/engineering/supervision_delivery_0830'
D='.local/independent_long64_development_0830';L='.local/legacy6_independent_readiness_0830'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):return dict(path=rel,sha256=h(R/rel))
def read(rel):return json.loads((R/rel).read_bytes())
def checked(rel,pin):
 assert h(R/rel)==pin,rel
 return read(rel)
def save(rel,x):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(x,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return ref(rel)
def archive(rel,pin,target):
 m=checked(rel,pin);base=Path(rel).parent;rows=[dict(x) for x in m['files']]
 rows.append(dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size));copies=[]
 assert len({x['path'] for x in rows})==len(rows)
 for x in rows:
  p=Path(x['path'])
  if not p.is_relative_to(base):p=base/p
  assert p.is_relative_to(base) and '..' not in p.parts and not p.is_absolute()
  src=R/p;assert src.is_file() and not src.is_symlink() and src.resolve().is_relative_to((R/base).resolve())
  assert h(src)==x['sha256'] and src.stat().st_size==x['bytes']
  assert src.suffix not in ['.pt','.pth','.bin','.safetensors','.ckpt','.pyc','.npy','.npz'] and src.stat().st_size<100*(1<<20)
  dest=R/E/target/p.relative_to(base);dest.parent.mkdir(parents=True,exist_ok=True)
  assert not dest.exists()
  copies.append((src,dest,dict(path=p.as_posix(),sha256=x['sha256'],bytes=x['bytes'])))
 for x in m.get('execution_audits',[]):assert h(R/x['path'])==x['sha256'] and (R/x['path']).stat().st_size==x['bytes']
 for src,dest,x in copies:
  with dest.open('xb') as f:f.write(src.read_bytes())
 return [dict(source=x,archive=ref(dest.relative_to(R).as_posix())) for src,dest,x in copies]
cp=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cp)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363'
spec=importlib.util.spec_from_file_location('accept0830',cp);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 sp=R/'results/experiment_supervisor/state.json';before=h(sp);s=read('results/experiment_supervisor/state.json');old=copy.deepcopy(s);f=s['formal_main_progress']
 assert s['pending_submission'] is None and f['root_and_independent_completed_arms']==62
 assert f['completed_development_trials']==2612 and f['current_action_development_trial_count']==1400
 assert f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created']
 root=checked('results/formal_main_v2/downstream_reviews/3047443.json','20f91c0060f086bcf402cc0b9b4e9863397c27876f4809dd9bef211aa0c87c25')
 ind=checked(D+'/job3047443/independent_review.json','0a04480cfae7c48beb8b4a81b99c5611d2273bd6f7c685a522beb096a7fd71d1')
 assert root['status']==ind['status']=='passed' and root['scientific_complete'] and ind['scientific_complete'] and ind['blockers']==[]
 assert root['completed_trials']==ind['completed_trials']==200 and ind['unique_initial_states']==100
 assert ind['successes']=={'A64_seed41':90,'B64_seed41':94} and ind['root_review']==ref('results/formal_main_v2/downstream_reviews/3047443.json')
 assert ind['cost']['all_attempt_GPU_seconds']==root['cost']['all_attempt_gpu_seconds']==3039
 assert ind['action_checks']['future_head_calls']==0 and ind['action_checks']['executed_actions_exactly_match_chunk_prefixes']
 assert not ind['final_state_values_read'] and not ind['legacy_terminal_trials_reused'] and not ind['O2A_latency_verified']
 for name,pin in ind['evidence_sha256'].items():assert h(R/name)==pin
 panel=checked(D+'/shared_development_panel_all_eight_jobs.json','655f1225960b32d3f64c3b2e2496fc31354cc91180e1d7ec4579998fe99b9eca')
 stats=checked(D+'/Long64_three_seed_statistics.json','510cfc9c907b0d721df0ce39b6d528adddaf7b04575e848ec21e5622ba6f98d4')
 rv=checked(B+'/Long64_root_statistics_verification.json','796e79da6edcae3f8dcc0425f7d87da9117c3821d26af5d8fa3b943dfc2e9e37')
 assert stats['status']==rv['status']=='passed' and rv['all30000_reported_draw_values_verified'] and rv['raw_trial_outcomes_verified']==600
 assert stats['total_trials']==600 and stats['unique_initial_states']==100 and stats['cost']['actual_development_GPU_seconds']==9102
 legacy=checked(L+'/independent_readiness.json','b786128f4f202c93da6a80f44c7c1fbeeacadef78724b76d9bef294615b7a3d5')
 assert legacy['historical_installation_evidence']['installation_attempt4_exit_zero_and_import_success']
 assert legacy['RNG_requirement_interpretation']['old_full_RNG_dump_required_by_0917'] is False
 assert not legacy['production_reuse_authorized'] and legacy['new_GPU_jobs']==legacy['new_scientific_trials']==0
 copies=archive(D+'/manifest.json','e14cb0e58f94254a7511b0ec10bec425b83a139ed41ac5222f6762f277d2e471','Long64_terminal_independent')
 lcopies=archive(L+'/manifest.json','83cefea686152fbd8bed4b32dbe6812a79c6d0433970a7484e0ff7cf34738e22','Long_legacy6_provenance_independent')
 ipath='results/formal_main_v2/downstream_reviews/3047443_independent.json'
 with (R/ipath).open('xb') as w:w.write((R/D/'job3047443/independent_review.json').read_bytes())
 delivery=save(B+'/Long64_terminal_independent_delivery.json',dict(copies=copies,source_manifest=ref(D+'/manifest.json'),new_GPU_execution=False,private_paths_preserved_in_unchanged_original_receipts=True))
 ldelivery=save(B+'/Long_legacy6_provenance_independent_delivery.json',dict(copies=lcopies,source_manifest=ref(L+'/manifest.json'),root_acceptance_of_full_bridge=False,production_reuse_authorized=False,no_new_GPU_execution=True,old_RNG_dump_not_registered_requirement=True))
 newdev=dict(job_id='3047443',suite='libero_10',visual_tokens=64,seed=41,completed_trials=200,unique_initial_states=100,root_review=ref('results/formal_main_v2/downstream_reviews/3047443.json'),independent_review=ref(ipath),successes=ind['successes'],B_minus_A_percentage_points=4.0,paired_outcomes=ind['paired_outcomes'],per_task=ind['per_task'],initial_observation_token_overlap_mean=ind['initial_observation_token_overlap_mean'],token_overlap_scope=ind['token_overlap_scope'],action_semantics_sha256=ind['action_semantics_sha256'],GPU_seconds=3039,O2A_complete=False,whole_suite_development_complete=False,no_legacy_semantics_equivalence_claimed=True)
 assert '3047443' not in f['new_action_development_verified_by_job']
 f['new_action_development_verified_by_job']['3047443']=newdev;f['latest_new_action_development_verified']=newdev
 rows=[x for x in f['Long_remaining16_development_submissions'] if x['job_id']=='3047443'];assert len(rows)==1 and rows[0]['completed_trials_accepted']==0
 rows[0].update(status='passed_root_and_independent_terminal',completed_trials_accepted=200,root_terminal_review=newdev['root_review'],independent_terminal_review=newdev['independent_review'],terminal_GPU_seconds=3039,successes=ind['successes'],B_minus_A_percentage_points=4.0)
 assert len(f['Long_remaining16_development_submissions'])==8 and all(x['completed_trials_accepted']==200 for x in f['Long_remaining16_development_submissions'])
 assert len(f['new_action_development_verified_by_job'])==8
 f['completed_development_trials']=2812;f['current_action_development_trial_count']=1600;f['current_action_development_unique_initial_states']=100;f['historical_other_action_semantics_development_trials']=1212
 stref=ref(E+'/Long64_terminal_independent/Long64_three_seed_statistics.json')
 f['Long64_three_seed_development_statistics']=dict(statistics=stref,root_reconstruction=ref(B+'/Long64_root_statistics_verification.json'),development_only=True,mean_difference_percentage_points=100*rv['point_difference'],CI95_B_minus_A_percentage_points=[100*x for x in rv['CI95_B_minus_A']],unique_initial_state_clusters=100,final_or_latency_conclusion=False)
 f['Long_remaining16_development_status']=dict(status='all8_pairs1600_trials_root_and_independent_accepted',unique_initial_states=100,whole_suite_development_complete=False,old6_method600_not_yet_admitted_to_new_semantics=True)
 f['Long_legacy6_equivalence_followup']['previous_status_preserved']=old['formal_main_progress']['Long_legacy6_equivalence_followup']['status']
 f['Long_legacy6_equivalence_followup'].update(status='historical_installation_factory_provenance_recovered_full_typed_bridge_review_pending',independent_provenance_delivery=ldelivery,source=ref(E+'/Long_legacy6_provenance_independent/independent_readiness.json'),old_RNG_dump_not_registered_requirement=True,absence_of_runtime_capture_not_rewritten_as_historical_measurement=True,production_reuse_authorized=False)
 now=datetime.now(timezone.utc).isoformat()
 receipt=save(B+'/Long_development_acceptance.json',dict(schema='formal_main_v2',kind='root_acceptance_of_Long64seed41_and_all3seed_statistics',utc=now,root_training_completed=62,new_development_trials=200,new_development_GPU_seconds=3039,Long64_all3seed_development_GPU_seconds=9102,all_archived_development_trials=2812,current_action_trials=1600,current_action_unique_initial_states=100,old_other_action_trials=1212,root_and_independent=newdev,Long64_statistics=stref,root_statistics_verification=ref(B+'/Long64_root_statistics_verification.json'),independent_delivery=delivery,legacy_historical_provenance_correction=ldelivery,old600_reused=False,old600_repeated=False,new_GPU_submissions=0,final_sealed=True,state_before_sha256=before))
 f['latest_incremental_review']=receipt;f['incremental_review_history'].append(receipt)
 s['updated_utc']=now;s['updated_date']='2026-10-20'
 assert s['autonomous_training_v1']==old['autonomous_training_v1'] and s['registered_jobs']==old['registered_jobs'] and s['current_round_cost']==old['current_round_cost']
 assert f['completed_training_pairs']==old['formal_main_progress']['completed_training_pairs']
 c.atomic_json(sp,s,before)
 print(json.dumps(dict(status='accepted',receipt=receipt,new_development=200,current_action_trials=1600,independent_files=len(copies),historical_provenance_files=len(lcopies),GPU_submissions=0)))
