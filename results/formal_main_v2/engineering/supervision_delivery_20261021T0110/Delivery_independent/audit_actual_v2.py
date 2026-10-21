"""Read-only actual root-delivery audit; excludes this author's Goal runtime algorithm.
Requires immutable final inputs/state and saved state-before. Never calls Git/Slurm or writes P/state.
"""
from pathlib import Path
from collections import Counter
import argparse,ast,difflib,hashlib,json,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
D=Path(__file__).parent
B='results/formal_main_v2/preflight/heartbeat_20261021T0910'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
checks=[];evidence={}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def ck(n,v,detail=None):
 checks.append(dict(name=n,passed=bool(v),detail=detail))
 if not v:raise AssertionError(n)
def raw(n,pin=None):
 p=R/n;ck('relative_no_symlink/'+n,not Path(n).is_absolute() and '..' not in Path(n).parts and p.resolve()==p)
 b=p.read_bytes();h=sha(b);ck('sha/'+n,pin is None or h==pin);evidence[n]=dict(sha256=h,bytes=len(b));return b
def rd(n,pin=None):return json.loads(raw(n,pin))
def rr(v):
 b=raw(v['path'],v['sha256'])
 if 'bytes' in v:ck('ref_size/'+v['path'],len(b)==v['bytes'])
 return json.loads(b)
def text(n,pin=None):return raw(n,pin).decode()
def changed(a,b):return {k for k in a.keys()|b.keys() if a.get(k,object())!=b.get(k,object())}
def save(n,v):
 with (D/n).open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
ap=argparse.ArgumentParser()
for n in ['inputs-sha256','summary-sha256','state-sha256','before-state','before-sha256','receipt-sha256']:
 ap.add_argument('--'+n,required=True)
for n in ['git-helper','git-helper-sha256','archive-helper','archive-helper-sha256']:ap.add_argument('--'+n,required=True)
ap.add_argument('--report-name',default='actual_review.json')
args=ap.parse_args()
def main():
 prior=rd('.local/delivery_independent_20261021T0110/preliminary_review_v2.json','9ced39d326b90872b72ba00be05d90289d159c216a9b142519380fc896d69248')
 ck('independent_preliminary5996',prior['status']=='passed_preliminary_root_delivery_scope_pending_final_snapshot' and len(prior['checks'])==5996 and all(x['passed'] for x in prior['checks']))
 for n,v in prior['evidence'].items():
  b=raw(n,v['sha256']);ck('preliminary_evidence_unchanged/'+n,len(b)==v['bytes'])
 oldsrc=text('.local/final_snapshot_20261021T0110_v1.py','49cc46f515e495005a661059d091aa2b5ae4d8432689d4da470c5efa56c44d70')
 newsrc=text('.local/final_snapshot_20261021T0110_v2.py','cfe25974a9b7ba9c53cda1eda4464fc8a5b3c190bdc4015a24e468bfedb11320')
 ck('snapshot_v2_only_scientific_HOLD_fix',newsrc==oldsrc.replace('summary["Goal_original200_and_new_science_HOLD"]=g.get("job_id") is None','summary["Goal_original200_and_new_science_HOLD"]=True'))
 ast.parse(newsrc)
 i=rd(B+'/final_snapshot_inputs.json',args.inputs_sha256)
 summary=rd(B+'/final_summary.json',args.summary_sha256)
 s=rd('results/experiment_supervisor/state.json',args.state_sha256)
 before=rd(args.before_state,args.before_sha256)
 receipt=rd(B+'/state_and_document_update.json',args.receipt_sha256)
 ck('inputs_schema',i['schema']=='formal_main_v2' and i['kind']=='root_delivery_inputs')
 for v in i['evidence'].values():
  b=raw(v['path'],v['sha256'])
  if 'bytes' in v:ck('input_evidence_size/'+v['path'],len(b)==v['bytes'])
 ck('actual_CAS_before_after',i['state_before_sha256']==args.before_sha256==receipt['state_before'] and receipt['state_after']==args.state_sha256)
 ck('snapshot_summary_ref',receipt['summary']==s['last_root_supervision_snapshot'] and receipt['summary']['sha256']==args.summary_sha256 and receipt['summary']['path']==B+'/final_summary.json')
 ck('only_expected_top_state_changes',changed(before,s)<={'last_root_supervision_snapshot','current_round_cost','autonomous_training_v1','formal_main_progress','updated_utc','last_supervision_utc','current_work','next_actions','next_allowed_action'},sorted(changed(before,s)))
 ck('registrations_immutable_during_snapshot',before['registered_jobs']==s['registered_jobs'])
 ctl=s['autonomous_training_v1'];f=s['formal_main_progress']
 ck('only_controller_occupied_projection_changed',changed(before['autonomous_training_v1'],ctl)<={'occupied_job_ids'})
 ck('only_progress_snapshot_projection_changed',changed(before['formal_main_progress'],f)<={'parallel_execution','downstream_followups_20261021T0110'})
 ck('only_parallel_projection_changed',changed(before['formal_main_progress']['parallel_execution'],f['parallel_execution'])<={'actual_running_allocated_GPUs','registered_requested_active_GPU_jobs','status','latest_root_observation'})
 ck('pending_and_capacity_reservations_clear',s.get('pending_submission') is None and ctl.get('pending_submission') is None and ctl['reserved_GPU_slots']==0 and ctl.get('root_submission_hold') is None)
 ck('training72pairs36updates360000',f['root_and_independent_completed_arms']==f['trained_arms']==72 and len(f['completed_training_pairs'])==36 and f['root_and_independent_reviewed_arm_updates']==360000)
 ck('development_counts_exact',(f['current_action_development_trial_count'],f['complete_development_batches_compatible_legacy_trials'],f['complete_development_batches_accepted_trials'],f['completed_development_trials'],f['current_action_development_unique_initial_states'])==(6388,612,7000,7600,400))
 ck('current_job_ledger_sum',sum(v['completed_trials'] for v in f['new_action_development_verified_by_job'].values())==6388)
 ck('new_Spatial_exact588',f['new_action_development_verified_by_job']['3054201']['completed_trials']==588)
 ck('no_final_evaluation_opened',f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and not summary['global_release'] and not summary['O2A_released'] and summary['final_sealed'])
 ck('summary_denominators',(summary['current_action_development_trials'],summary['compatible_legacy_Long_trials'],summary['compatible_legacy_Spatial_trials'],summary['compatible_development_trials'],summary['all_historical_accepted_development_trials'],summary['unique_development_initial_states'],summary['new_unique_initial_states'],summary['new_development_accepted'])==(6388,600,12,7000,7600,400,0,588))
 ck('Spatial_typed_current_legacy_distinction',summary['Spatial588']['completed_new_trials_accepted']==588 and summary['Spatial588']['legacy_compatible_trials']==12 and summary['Spatial588']['complete_mixed_panel_trials']==600 and summary['Spatial588']['cost_GPU_seconds']==7030 and summary['Spatial588']['current_allocation_GPU_seconds']==6635 and not summary['Spatial588']['profiling_authorized'] and not summary['Spatial588']['final_release'])
 ck('Object599_separate_no_new_result',summary['Object599']['legacy599_root_adopted'] and not summary['Object599']['whole600_production_adopted'] and not summary['Object599']['new_trial_accepted'] and summary['Object599']['single_failure_job_id']=='3054409')
 ck('Object_linked_attempt_no_terminal_admission',summary['Object_single_error_linked_attempt']['scientific_terminal_not_yet_accepted'])
 ck('Goal_old200_cause_and_science_HOLD',summary['Goal_original200_and_new_science_HOLD'] and summary['Goal_original200_and_remaining1000_HOLD'] and not summary['Goal_full200']['old200_adopted'] and not summary['Goal_full200']['old_cause_explained'] and summary['Goal_full200']['new_development_accepted']==0 and summary['Goal_full200']['remaining1000_scientific_HOLD'])
 ck('input_Goal_projection_exact',summary['Goal_full200']==i['Goal_full200'])
 o=rr(i['operation_observation']);rows=o['observation']['rows']
 ck('only_archived_operation_observation',o['kind']=='root_actual_operation_observation_projection' and o['new_queries']==0 and o['source_receipt'] in list(i['evidence'].values()))
 rr(o['source_receipt'])
 ck('summary_observation_ref_exact',summary['cost_basis']==s['current_round_cost']['observation'] and summary['cost_basis']['sha256']==i['operation_observation']['sha256'])
 formal=[j for j in s['registered_jobs'] if j.get('experiment')=='formal_main_v2']
 ids=[str(j['job_id']) for j in formal]
 ck('unique_registered_allocations',len(ids)==len(set(ids)) and set(ids)<=set(rows))
 oldstate=rd(B+'/Spatial3054201_state_before.json','3281eaab5f761b3aa61bf702b3b3d4b36386569667d17ff343e7199e4f159796')
 oldids={str(j['job_id']) for j in oldstate['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
 newids=sorted(set(ids)-oldids)
 ck('exact_only_approved_new_jobs',newids==sorted(i['new_GPU_jobs'])==sorted(summary['new_GPU_jobs']) and '3054409' in newids and 1<=len(newids)<=2)
 g=summary['Goal_full200'];ck('optional_Goal_job_explicit',g.get('job_id') is None or g['job_id'] in newids)
 cost=0
 for j in ids:
  row=rows[j];ck('allocated_cost_nonnegative/'+j,isinstance(row['elapsed_seconds'],int) and row['elapsed_seconds']>=0 and isinstance(row['gpus'],int) and row['gpus']>=0)
  cost+=row['elapsed_seconds']*row['gpus']
 occupied=o['occupied']
 ck('capacity8_unique_all_modes',len(occupied)==len(set(occupied))<=8 and set(occupied)<=set(ids))
 ck('controller_remains_normal_complete',rows['3034538']['status']=='COMPLETED' and rows['3034538']['exit_code']=='0:0' and o['controller_lease_released'])
 ck('exact_total_once',cost==o['allocated_GPU_seconds']==summary['allocated_GPU_seconds']==s['current_round_cost']['allocated_gpu_seconds'] and len(ids)==summary['registered_formal_allocations']==s['current_round_cost']['registered_jobs'])
 ck('cost_hours_exact',summary['allocated_GPU_hours']==s['current_round_cost']['allocated_gpu_hours']==cost/3600)
 ck('cost_timestamp_and_lower_bound',summary['cost_observed_utc']==o['utc'] and summary['cost_final_for_current_registered_set']==s['current_round_cost']['final']==(not occupied) and o['utc'] in s['current_round_cost']['scope'])
 ck('active_projection_exact',ctl['occupied_job_ids']==summary['active_registered_GPU_jobs']==summary['capacity']['occupied']==occupied and summary['capacity']['unknown']==summary['capacity']['findings']==[])
 running=sum(rows[j]['gpus'] for j in occupied if rows[j]['status']=='RUNNING')
 ck('parallel_running_exact',running==summary['actual_running_allocated_GPUs']==f['parallel_execution']['actual_running_allocated_GPUs'] and f['parallel_execution']['registered_requested_active_GPU_jobs']==len(occupied))
 prev=rr(summary['previous_snapshot'])
 ck('incremental_cost_not_readded',summary['newly_accounted_GPU_seconds']==cost-prev['allocated_GPU_seconds'])
 ck('actual_science_admission_receipt',receipt['new_development_accepted']==588 and receipt['new_GPU_jobs']==newids and receipt['source173_verified'] and receipt['final_sealed'])
 for n,v in receipt['document_changes'].items():
  b=raw(n,v['after_sha256']);ck('document_no_extra_EOF_LF/'+n,b.endswith(b'\n') and not b.endswith(b'\n\n'))
  ck('document_does_not_presume_remote_push/'+n,b'7000/8800' in b and b'588' in b)
 blocker=raw(receipt['new_blocker_document']['path'],receipt['new_blocker_document']['sha256'])
 ck('new_blocker_scope',i['Goal_markdown'] in blocker.decode() and i['blocker_details_markdown'].rstrip() in blocker.decode() and blocker.endswith(b'\n') and not blocker.endswith(b'\n\n'))
 snap=rd('results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 ck('source173',len(snap['files'])==173)
 for n,w in snap['files'].items():
  for label,base in [('R',R),('Rmirror',R/'snapshots/formal_main_v2_run_564be0995e'),('S',P/'snapshots/formal_main_v2_run_564be0995e')]:ck('frozen173/'+label+'/'+n,sha((base/n).read_bytes())==w)
 git_src=text(args.git_helper,args.git_helper_sha256);archive_src=text(args.archive_helper,args.archive_helper_sha256)
 ast.parse(git_src);archive_ast=ast.parse(archive_src)
 ck('Git_final_audit_same_writer_lock',all(t in git_src for t in ["with c.exclusive_lock","audit['status']=='passed_final_delivery_review'","audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')","git('diff','--cached','--name-only').stdout==b''","frozen_files_verified_in_worktree_and_index']==173"]))
 ck('Git_precise_raw_runtime_exclusion',"':(exclude)results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01'" in git_src)
 ck('Git_no_whole_raw_glob',all(t not in git_src for t in ["git('add','-A'","git('add','.'","git('add','--all'"]))
 ck('archive_immutable_same_lock_exact_no_weights',all(t in archive_src for t in ['len(files)==count','with c.exclusive_lock','not_runtime_admission=True',"h(src)==row['sha256']","assert not raws"]))
 allowed=ast.literal_eval(next(n.value for n in archive_ast.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ALLOWED' for t in n.targets)))
 archives=[]
 for apath in sorted((R/B).glob('*_archive.json')):
  rec=rd(apath.relative_to(R).as_posix())
  if rec.get('status')!='immutable_nonweight_package_archived':continue
  mr=rec['manifest'];parent=next(k for k,v in allowed.items() if rec['destination']==E+'/'+v)
  ck('manifest_owner/'+mr['path'],mr['path'].startswith(parent+'/'))
  manifest=rr(mr);archived_manifest=rec['destination']+'/'+Path(mr['path']).stem+'_original.json'
  ck('manifest_archive_original/'+archived_manifest,raw(archived_manifest,mr['sha256'])==(R/mr['path']).read_bytes())
  files=manifest['files']
  if isinstance(files,dict):files=[dict(v,path=k) for k,v in files.items()]
  ck('archive_count/'+mr['path'],len(files)==rec['file_count']==manifest.get('file_count',len(files)))
  declared=manifest.get('source_root',str((R/mr['path']).parent))
  if declared is not None:
   declared=Path(declared)
   ck('manifest_declared_no_parent_traversal/'+mr['path'],'..' not in declared.parts)
   declared=declared if declared.is_absolute() else R/declared
   ck('manifest_declared_allowed_root/'+mr['path'],declared.resolve()==declared and declared.is_relative_to(R/parent))
   prefix=declared.relative_to(R/parent)
  else:prefix=Path('.')
  expected=[]
  for v in files:
   n=v.get('source',v.get('path'))
   if n.startswith(parent+'/'):n=n[len(parent)+1:]
   elif declared is not None:n=(prefix/n).as_posix()
   ck('archive_safe_relative/'+n,n and not Path(n).is_absolute() and '..' not in Path(n).parts)
   src=parent+'/'+n;dest=rec['destination']+'/'+n
   a=raw(src,v['sha256']);b=raw(dest,v['sha256'])
   ck('archive_exact_bytes/'+dest,len(a)==len(b)==v['bytes'] and a==b)
   ck('archive_nonweight_allowlist/'+dest,Path(dest).suffix.lower() not in ('.pt','.pth','.ckpt','.safetensors','.bin','.h5','.hdf5','.npy','.npz','.pkl','.pickle','.init','.pruned_init') and len(b)<100*(1<<20))
   expected.append(dict(path=dest,source=src,sha256=v['sha256'],bytes=v['bytes']))
  if 'copied_files' in rec:ck('archive_receipt_exact_mapping/'+mr['path'],rec['copied_files']==expected)
  ck('archive_receipt_no_admission/'+mr['path'],rec['state_unchanged'] and rec['GPU_jobs_added']==0 and rec['not_runtime_admission'])
  archives.append(dict(manifest=mr,file_count=len(files),destination=rec['destination']))
 goal_manifest=rd(E+'/Downstream_runtime_independent/Goal_full200_manifest_original.json','738f4f054fd2e4387e2f4cbfb34d232befb8237b182722fc3cf0558b7558d7de')
 goal_review=rd(E+'/Downstream_runtime_independent/Goal_full200/final_independent_review.json','ad163d3e4dd8d323a3d994d9a070b597920458906af54092b65dc5d91f1ea8f0')
 ck('Goal_separate_agent_review_provenance_not_self_review',goal_manifest['production_admitted'] is False and goal_manifest['GPU_execution_authorized'] is False and goal_manifest['old200_HOLD'] is True and goal_manifest['package_manifest_sha256']=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec' and goal_review.get('reviewed_by')=='independent')
 ck('Goal_source_audit_bound_in_inputs',any(pin in json.dumps(i) for pin in ['738f4f054fd2e4387e2f4cbfb34d232befb8237b182722fc3cf0558b7558d7de','ad163d3e4dd8d323a3d994d9a070b597920458906af54092b65dc5d91f1ea8f0','e3f11199241a6082f36c3556c0698e7c8b8043d2bc1f4256e2bc3da037549259']))
 ck('final_state_still_exact_after_readonly_audit',sha((R/'results/experiment_supervisor/state.json').read_bytes())==args.state_sha256)
 return dict(schema='formal_main_v2',kind='root_delivery_independent_review',status='passed_final_delivery_review',reviewed_by='independent',reviewer_agent='/root/goal_cpu_gate_2054',blockers=[],state_sha256=args.state_sha256,source173_verified=True,final_sealed=True,scope='Root final state/docs/counts/cost and exact evidence delivery only. Own Goal runtime algorithm excluded; its separate-agent review is provenance only. Prior 5996 independent checks inherited by exact immutable evidence, not claimed as newly rerun.',checks=list(checks),inherited_preliminary_checks=5996,source173_current_checks=519,archive_verifications=archives,actual_registered_allocations=len(ids),actual_allocated_GPU_seconds=cost,active_GPU_jobs_at_saved_observation=occupied,new_GPU_jobs=newids,current_trials=6388,compatible_legacy_trials=612,complete_batch_trials=7000,historical_catalog_trials=7600,unique_initial_states=400,new_science_trials_accepted_by_root=588,own_new_science_admissions=0,new_live_Slurm_queries=0,new_GPU_submissions=0,state_writes=0,Git_operations=0,P_writes=0,future_Git_commit_or_push_verified=False,evidence=evidence)
try:
 value=main()
except BaseException as exc:
 value=dict(schema='formal_main_v2',kind='root_delivery_independent_review',status='failed_actual_delivery_review',blockers=[str(exc)],checks=list(checks),traceback=traceback.format_exc(),state_sha256=args.state_sha256,final_review_issued=False,evidence=evidence)
 save(args.report_name,value)
 print(json.dumps(dict(status=value['status'],error=str(exc),checks=len(checks))))
 raise
save(args.report_name,value)
print(json.dumps(dict(status=value['status'],checks=len(value['checks']),report_sha256=sha((D/args.report_name).read_bytes()))))
