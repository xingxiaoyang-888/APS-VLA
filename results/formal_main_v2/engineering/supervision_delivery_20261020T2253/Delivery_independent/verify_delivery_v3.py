"""Frozen final delivery audit. No live Slurm/GPU/production mutations; no repeated raw blob scan."""
from pathlib import Path
import ast,collections,hashlib,json,math,os,re,sys,time,traceback
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA');S=P/'snapshots/formal_main_v2_run_564be0995e';D=R/'.local/delivery_independent_20261020T2253';B='results/formal_main_v2/preflight/heartbeat_20261021T0653';E='results/formal_main_v2/engineering/supervision_delivery_20261020T2253';AUTH='d0143bc88b855ad9f4d6b6008e8373272d55c953d36bba88fbd8840a1090f7d5';G='results/formal_main_v2/downstream_gateway/'+AUTH;J='3054201'
STATE='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10';SUMMARY='f4d17e968396671b9e8072de1503133652b437e1dd9eee040f74c5d37a56b12d';UPDATE='e20926b5a6fead9d6fa64f50012450e63392ba37ba6d30c16653a92e6f8993f4'
checks=[];refs={};start=time.perf_counter();ct=time.process_time()
def ck(n,v):
 checks.append({'name':n,'passed':bool(v)})
 if not v:raise AssertionError(n)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for z in iter(lambda:f.read(8<<20),b''):h.update(z)
 return h.hexdigest()
def watch(p,pin=None):
 h=sha(p)
 if pin is not None:ck('SHA:'+str(p),h==pin)
 if str(p) in refs:ck('same_evidence:'+str(p),refs[str(p)]['sha256']==h)
 refs[str(p)]={'path':str(p),'sha256':h,'bytes':p.stat().st_size};return refs[str(p)]
def rd(p,pin=None):watch(p,pin);return json.loads(p.read_bytes())
def rr(ref):
 p=Path(ref['path']);return rd(p if p.is_absolute() else R/p,ref['sha256'])
def save(name,obj):
 p=D/name
 with p.open('x') as f:json.dump(obj,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return {'path':str(p.relative_to(R)),'sha256':sha(p)}
def guard(ev,args):
 if ev in ('subprocess.Popen','os.system','os.posix_spawn','socket.connect','socket.bind'):raise RuntimeError('No scheduler/process/network commands in delivery audit')
 if ev=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
  if any('sealed' in n.lower() for n in p.parts) or ('final' in p.parts and p.name=='panel.json'):raise RuntimeError('Cannot read sealed values')
  mode,flags=args[1:3];w=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
  if w and not p.is_relative_to(D):raise RuntimeError('Only private delivery audit writes allowed')
def main():
 sys.dont_write_bytecode=True;os.environ['CUDA_VISIBLE_DEVICES']='';sys.addaudithook(guard)
 st=rd(R/'results/experiment_supervisor/state.json',STATE);q=rd(R/B/'final_summary.json',SUMMARY);update=rd(R/B/'state_and_document_update.json',UPDATE);f=st['formal_main_progress'];ctl=st['autonomous_training_v1']
 ck('summary_state_CAS_binding',update['state_after']==STATE and update['summary']==st['last_root_supervision_snapshot']=={'path':B+'/final_summary.json','sha256':SUMMARY})
 ck('science_not_added',q['new_development_accepted']==update['new_development_accepted']==0 and q['new_unique_initial_states']==0 and q['compatible_development_trials']==6400 and q['planned_development_trials']==8800 and q['all_historical_accepted_development_trials']==f['completed_development_trials']==7012)
 ck('final_closed_and_sealed',q['final_sealed'] and q['final_trials']==f['completed_final_trials']==0 and not f['test_opened'] and not f['global_release_created'] and not q['global_release'] and not q['O2A_released'] and q['final_total']==35200)
 precheck=rd(D/'precheck_review.json','d1f61d0946926cf422116c4a4bdf376f45fb4d6e2d0240c51bb075be46bd66ac');ck('archived_evidence_precheck_passed',precheck['status']=='passed_archived_evidence_precheck' and not precheck['blockers'] and precheck['check_count']==733)
 for path,record in precheck['files'].items():watch(Path(path),record['sha256']);ck('precheck_size '+path,Path(path).stat().st_size==record['bytes'])
 pairs=f['completed_training_pairs'];ck('36_pairs72arms',len(pairs)==36 and f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000)
 train_updates=0;selected=[];pairsigs=set()
 for pair,pv in pairs.items():
  match=re.fullmatch(r'(libero_(?:10|spatial|object|goal))_k(256|128|64)_seed(17|23|41)',pair);ck('registered_pair_key_'+pair,match is not None);sig=(match[1],int(match[2]),int(match[3]));ck('unique_scientific_pair_'+pair,sig not in pairsigs);pairsigs.add(sig)
  ck('state_completed_pair_'+pair,pv['trained_arms']==2 and pv['allowed_next_segment_end'] is None)
  if 'root_review' in pv:
   root=rd(R/pv['root_review'],pv['root_review_sha256']);ind=rd(R/pv['independent_review'],pv['independent_review_sha256']);ck('direct_original_root_independent_'+pair,root['status']=='passed' and ind['status'] in ['passed','passed_complete_training_only'] and root['completed_by_arm']=={'A':5000,'B':5000} and root['allowed_next_segment_end'] is None and root['continuation']=='formal_training_complete_no_extension')
   train_updates+=sum(root['completed_by_arm'].values());selected.extend(pv['selected_checkpoints']);ck('selected_AB_'+pair,{x['arm'] for x in pv['selected_checkpoints']}=={'A','B'})
  else:
   terminal=pv['terminal_root_and_independent_review'];root=rr(terminal['root_review']);ind=rr(terminal['independent_review']);changes=[x for x in root['changes'] if x['pair_key']==pair]
   ck('machine_origin_preserved_plus_actual_independent_'+pair,pv['verification_kind']=='machine_automatic_not_independent' and terminal['machine_origin_unchanged'] and root['status']=='accepted_training_integrity_not_scientific_efficacy' and ind['status']=='passed' and ind['pair_key']==pair and ind['completed_by_arm']==terminal['completed_by_arm']==pv['completed_by_arm']=={'A':5000,'B':5000} and ind['allowed_next_training_update'] is None and ind['original_raw_validator_rebuilt_exactly'])
   ck('root_explicit_pair_adoption_'+pair,len(changes)==1 and changes[0]['common_update']==5000 and changes[0]['independent_review']==terminal['independent_review'] and not root['scientific_success_or_latency_inferred'])
   train_updates+=sum(ind['completed_by_arm'].values());best=[x for x in ind['actual_checkpoint_checks'] if x['filename']=='best.pt'];selected.extend(best);ck('actual_independent_selected_AB_'+pair,{x['arm'] for x in best}=={'A','B'} and all(x['sha256']==ind['arms'][x['arm']]['best_checkpoint_sha256'] for x in best))
 ck('entire_registered_matrix',pairsigs=={(suite,k,seed) for suite in ['libero_10','libero_spatial','libero_object','libero_goal'] for k in [256,128,64] for seed in [17,23,41]} and train_updates==360000 and len(selected)==72)
 dev=0;devjobs=f['new_action_development_verified_by_job'];ck('no_engineering_in_science',J not in devjobs)
 for jid,x in devjobs.items():
  root=rr(x['root_review']);ind=rr(x['independent_review']);ck('verified_dev_'+jid,root['status']=='passed' and ind['status']=='passed' and root['completed_trials']==x['completed_trials'] and root['scientific_complete'] and not root['final_release'] and not root['final_state_values_read']);dev+=root['completed_trials']
 long=f['Long_legacy6_equivalence_followup'];rr(long['root_acceptance']);rr(long['real_development_compatibility_proof']);ck('Long600_only_compatible_legacy',long['original600_reused'] and long['production_reuse_authorized'] and not long['original600_rerun'] and long['actual_new_wrapper_trials_added']==0 and q['compatible_legacy_Long_trials']==600)
 ck('current5800_plus600_compatible6400',dev==f['current_action_development_trial_count']==q['current_action_development_trials']==5800 and dev+600==6400 and q['unique_development_initial_states']==400 and q['accepted_fixed_observations_including_Long']==90)
 prev=rr(f['downstream_followups_20261020T2054']);ck('previous_science_counts_preserved',prev['compatible_development_trials']==6400 and prev['current_action_development_trials']==5800 and prev['final_trials']==0)
 ackm=rd(R/E/'Spatial588_ACK_independent/delivery_manifest_final_original.json','a53172b5d1258669fe2ade1a8568f019386294ed1caa3c9a6562152a13f2c9f8')
 ck('ACK31_file_package_declared',ackm['file_count']==31)
 # Independently parse original frozen sacct and raw squeue, counting each allocation once.
 obdoc=rr(q['cost_basis']);obs=obdoc['observation'];raw={};queue={}
 for line in obs['raw_sacct'].splitlines():
  p=line.split('|');jid=p[0];ck('unique_sacct_allocation '+jid,jid not in raw and len(p)==8);gpu=re.search(r'(?:^|,)gres/gpu=(\d+)(?:,|$)',p[4]);raw[jid]={'seconds':int(p[3]),'gpus':int(gpu.group(1)) if gpu else 0,'status':p[1],'exit_code':p[2]}
 for line in obs['raw_squeue'].splitlines():
  p=line.split('|');ck('unique_raw_squeue '+p[0],len(p)==3 and p[0] not in queue);queue[p[0]]={'status':p[1],'comment':p[2]}
 ck('queue_exact_parsed',queue==obs['queue'])
 formal=[j for j in st['registered_jobs'] if j.get('experiment')=='formal_main_v2'];ids=[str(j['job_id']) for j in formal];ck('271_unique_formal_allocations',len(ids)==len(set(ids))==q['registered_formal_allocations']==271)
 costrows=[]
 for j in formal:
  jid=str(j['job_id']);x=raw[jid];row=obs['rows'][jid];ck('cost_observation '+jid,x['seconds']==row['elapsed_seconds'] and x['gpus']==row['gpus'] and x['status']==row['status'] and x['exit_code']==row['exit_code']);costrows.append({'job_id':jid,'seconds':x['seconds'],'gpus':x['gpus'],'GPU_seconds':x['seconds']*x['gpus']})
 total=sum(x['GPU_seconds'] for x in costrows);ck('cost_sum_once',total==1986011==q['allocated_GPU_seconds']==st['current_round_cost']['allocated_gpu_seconds'] and math.isclose(q['allocated_GPU_hours'],total/3600,abs_tol=1e-12) and not q['cost_final_for_current_registered_set'] and not st['current_round_cost']['final'])
 oldst=rd(R/B/'state_before_Goal_terminal.json','63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f');oldids={str(j['job_id']) for j in oldst['registered_jobs'] if j.get('experiment')=='formal_main_v2'}
 ck('only_one_new_allocation',set(ids)-oldids=={J} and oldids<=set(ids) and q['new_GPU_jobs']==update['new_GPU_jobs']==[J] and q['newly_accounted_GPU_seconds']==1332 and total-oldst['current_round_cost']['allocated_gpu_seconds']==623+709)
 ck('Goal_exact_terminal_cost',raw['3054127']=={'seconds':840,'gpus':1,'status':'COMPLETED','exit_code':'0:0'} and oldst['current_round_cost']['allocated_gpu_seconds']==1984679)
 ck('Spatial_snapshot_709_not_future',raw[J]=={'seconds':709,'gpus':1,'status':'RUNNING','exit_code':'0:0'})
 ck('original_cost_preserved',raw['3022743']['seconds']*raw['3022743']['gpus']==393 and raw['3042529']['seconds']*raw['3042529']['gpus']==2 and sum(raw[j]['seconds']*raw[j]['gpus'] for j in ['3021394','3021603','3021844'])==6713)
 ck('controller_terminal_no_restart',raw['3034538']['status']=='COMPLETED' and raw['3034538']['exit_code']=='0:0' and raw['3034538']['gpus']==0 and q['controller_lease_released'] and not q['controller_restarted'])
 ck('capacity_clean_only_one',st['pending_submission'] is None and ctl['reserved_GPU_slots']==0 and ctl['root_submission_hold'] is None and ctl['occupied_job_ids']==q['active_registered_GPU_jobs']==q['capacity']['occupied']==[J] and not q['capacity']['unknown'] and not q['capacity']['findings'] and len(q['capacity']['occupied'])<=8 and q['actual_running_allocated_GPUs']==1)
 # Retained ACK and immutable entrypoint remain the only launch; reconciliation did not submit.
 dispatch=rr(q['Spatial588']['dispatch']);ack=rr(q['Spatial588']['original_ACK']);committed=rr(dispatch['committed']);pre=rd(R/G/'preflight.json','77de2bf6f02d5ea8ca7629a286898105f5c0358c66e2b397717f64ea318254b1');failure=rd(R/G/'failed_transaction.json','18897d313b1460cf14bbef535171090ff3a72bd29adf03018a65bd02ec1525ff');jobdoc=rd(R/'results/formal_main_v2/submissions/3054201.json','a3207f9b5b7a31ea5eab8ed7d8cab07c77aaf4b62f5eada3e1a17b27cdb58b36')
 token='cti-downstream-gateway-v1:'+AUTH;jobs=[j for j in formal if str(j['job_id'])==J];ck('one_new_job_matches_committed',len(jobs)==1 and jobs[0]==jobdoc==committed['job']);job=jobs[0]
 ck('exact_original_ACK',ack['returncode']==0 and ack['stdout']==J+'\n' and ack['stderr']=='' and ack['actual_sbatch_argv']==pre['actual_sbatch_argv']==job['downstream_gateway']['actual_sbatch_argv'])
 ck('token_exact_and_unique',committed['request_token']==pre['request_token']==obdoc['request_token']==queue[J]['comment']==token and len([j for j in st['registered_jobs'] if j.get('downstream_gateway',{}).get('request_token')==token])==1)
 ck('single_launch_original_guard', '--no-requeue' in ack['actual_sbatch_argv'] and '--gres=gpu:l40:1' in ack['actual_sbatch_argv'] and '--exclude=gpu4020' in ack['actual_sbatch_argv'] and '--time=04:00:00' in ack['actual_sbatch_argv'] and job['gpus']==1 and job['mode']=='development' and job['suite']=='libero_spatial' and job['resume'] is True)
 ck('failure_retained_reconciled_no_submit',failure['error']=='post-submit accounting incomplete' and failure['status']=='stopped_requires_root_reconciliation_no_retry' and not failure['automatic_retry'] and committed['status']==dispatch['status']=='submitted_once_reconciled_known_ack' and committed['submitted_once_original_ACK'] and dispatch['submitted_once_original_ACK'] and committed['original_failure_retained'] and committed['submission_calls_this_reconciliation']==dispatch['submission_calls_this_reconciliation']==obdoc['submission_calls_this_reconciliation']==0)
 ck('reconciliation_CAS_and_reservation',committed['state_sha256']==dispatch['state_sha256']==update['state_before'] and failure['state_sha256']==obdoc['state_before'] and committed['reservation_consumed'] and ctl['downstream_reservations_consumed'][AUTH]['job_id']==J and ctl['downstream_reservations_consumed'][AUTH]['request_token']==token)
 cap0=pre['capacity'];cg=cap0['completed_training_development_gate'];ck('actual_zero_prior_slot_and_lease',not cap0['occupied'] and not cap0['unknown'] and not cap0['findings'] and cg['lifecycle_lease_available_measured'] and cg['original_lock_inode_preserved'] and cg['controller_status']=='COMPLETED' and cg['controller_exit_code']=='0:0' and not cg['controller_restarted'] and cg['root_arms']==72 and cg['root_pairs']==36)
 auth=rr(dispatch['authorization']);ck('exact_auth_one_attempt_no_expansion',auth['maximum_attempts']==1 and auth['automatic_retry'] is False and auth['final_release_authorized_by_gateway'] is False and auth['status']=='approved_for_exactly_one_registered_downstream_submission')
 for key in ['plan','prepared_invocation','root_reservation','runtime_readiness','scientific_plan','independent_review']:rr(auth[key])
 inv=rd(R/job['invocation'],job['invocation_sha256']);watch(P/job['invocation'],job['invocation_sha256']);ck('invocation_preflight_identity',pre['invocation_sha256']==job['invocation_sha256']==auth['prepared_invocation']['sha256']=='8a9d19ca0c1c099a6837c3f19123a031db5e57f0b3596f9d4031ce39e23d0e3e')
 hist=job['typed_predispatch_history'];ck('history_all_attempts_not_all_executed',hist['all_prior_job_ids']==job['prior_job_ids']==['3022743','3042529'] and hist['executed_prior_job_ids']==['3022743'] and hist['predispatch_failed_job_ids']==['3042529'] and not hist['failed_ledger_invocation_fabricated'] and not hist['ordinary_failure_review_fabricated'] and hist['prior_GPU_seconds']==395)
 ck('legacy12_current588_separate_no_admission',hist['scope']['retained_prefix_trials']==q['Spatial588']['retained_legacy_trials']==12 and hist['scope']['remaining_trials']==q['Spatial588']['remaining_current_trials_requested']==588 and hist['scope']['expected_trials']==600 and q['Spatial588']['completed_new_trials_accepted']==0 and q['Spatial588']['mixed600_batch_not_yet_accepted'] and q['Spatial588']['resubmissions']==0 and not q['Spatial588']['automatic_retry'])
 mp=obdoc['mutable_output_proof'];ck('mutable_P_identity_only_not_outcome_claim',mp['status']=='passed_identity_only_not_scientific_acceptance' and mp['old_prefix_results']==12 and mp['old_prefix_bytes']==592887 and mp['new_invocation_count']==1 and mp['new_job_id']==J and mp['old_job_id']=='3022743' and mp['legacy_results_counted_current']==0 and mp['scientific_results_admitted']==obdoc['scientific_results_admitted']==0 and mp['report_current_ledger_SHA_equality_not_required'])
 # Original R prefix remains immutable; do not inspect the running P ledger/report.
 for rel,record in mp['original_R_proofs'].items():
  pp=R/'results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01'/rel;watch(pp,record['sha256']);ck('original_prefix_size '+rel,pp.stat().st_size==record['bytes'])
 ari=rd(R/'.local/spatial588_ack_independent_20261020T2253/independent_review.json','60eb3a6e0f79f9a4943a3e6904a65a2d9f94684ff932ab923064faddd8da8568');ck('separate_ACK_reconcile_code_review',ari['status']=='passed' and not ari['blockers'] and ari['job_id']==J and ari['new_GPU_submissions']==0 and ari['scientific_results_admitted']==0)
 arpost=rd(R/'.local/spatial588_ack_independent_20261020T2253/post_registration_independent_review.json','62b31fedd7ace383a22610d5de7b4ee4e7b2542cd565d3c7c1efae18523e191c')
 ck('ACK_postregistration_final_state_exact',arpost['status']=='passed' and arpost['state_sha256']==STATE and arpost['reconstructed_committed_state_sha256']==update['state_before'] and arpost['registered_once'] and arpost['new_GPU_submissions']==arpost['new_Slurm_queries']==0 and arpost['allocated_GPU_seconds_at_root_snapshot']==total and arpost['job_GPU_seconds_at_root_snapshot']==709 and arpost['reserved_GPU_slots']==0 and arpost['pending_submission'] is None and len(arpost['checks'])==34)
 # Goal terminal evidence accepted only as engineering; prior independent full blob audit retained, not repeated.
 gr=rr(q['Goal_paired_input_engineering']['acceptance']);ck('Goal_hold_engineering_complete',gr['new_Goal_science_HOLD'] and q['Goal_original200_and_new_science_HOLD'] and q['Goal_paired_input_engineering']['terminal_evidence_reviewed'] and gr['prefix_trials']==58 and gr['accepted_queries']==940 and gr['executed_steps']==7302 and gr['GPU_seconds']==840 and gr['new_scientific_trials']==0 and not any(gr[k] for k in ['old200_adopted','old_cause_identified','old_failure_repaired','final_release','automatic_retry','O2A_admitted']))
 for key in ['independent_review','independent_archive_review','root_review','archive_manifest']:rr(gr[key])
 ck('Goal_not_in_development', '3054127' not in f['new_action_development_verified_by_job'])
 ob=rr(q['Object599']['independent_review']);ck('Object599_proof_not_production',ob['status']=='passed' and q['Object599']['independent_compatibility_passed'] and not q['Object599']['production_adopted'] and not q['Object599']['single_failure_GPU_authorized'] and not q['Object599']['single_failure_CPU_candidate_independent_review_completed'] and q['Object599']['original_policy_error_retained'] and ob['all_original_GPU_seconds']==6713)
 # Preserve the separately labelled author-only Object correction CPU package without granting it independence or production use.
 om=rr(q['Object599']['single_failure_CPU_candidate_manifest']);obase=R/E/'Object_single_error_candidate';ck('Object_candidate_scope_HOLD',om['file_count']==18 and om['independent_review_not_yet_run'] and not om['production_admitted'] and not om['actual_P_verified'] and om['Slurm_submissions']==om['new_scientific_trials']==0)
 expected=set()
 for row in om['files']:
  rel=Path(row['path']).relative_to(om['root']);pp=obase/rel;expected.add(str(rel));watch(pp,row['sha256']);ck('Object_candidate_size '+str(rel),pp.stat().st_size==row['bytes'])
 ck('Object_exact_candidate_archive', {str(p.relative_to(obase)) for p in obase.rglob('*') if p.is_file()}==expected|{'delivery_manifest_original.json'})
 # Recheck the immutable scientific source byte-for-byte in all three retained locations.
 invsrc=rd(R/'results/formal_main_v2/source/formal_main_v2_run_564be0995e.json','5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926');ck('source_count_173',len(invsrc['files'])==173)
 for base in [R,S,R/'snapshots/formal_main_v2_run_564be0995e']:
  for rel,pin in invsrc['files'].items():watch(base/rel,pin)
 stats=rr(q['development_k64_statistics']);statsind=rr(q['development_k64_statistics_independent']);ck('k64_prior_independent_raw_proof_preserved',statsind['status']=='passed' and not statsind['blockers'] and statsind['root_statistics_sha256']==q['development_k64_statistics']['sha256'] and statsind['check_count']==235 and not statsind['root_intermediate_pairs_used_for_reconstruction'])
 ck('k64_statistics_development_scope',stats['development_only'] and stats['same_initial_state_carries_all_three_seeds'] and stats['task_stratified_bootstrap_repeats']==10000 and stats['bootstrap_seed']==20261016 and all(v['unique_state_clusters']==100 and v['trials']==600 for v in stats['suite_results'].values()))
 for rel,record in update['document_changes'].items():
  pp=R/rel;watch(pp,record['after_sha256']);text=pp.read_text();ck('document_current_front_matter '+rel, all(x in text[:3500] for x in ['6400/8800','最终0/35200','3054127','3054201','1986011','HOLD','12 legacy与588 current','尚不接纳完整600']))
  # Common latest section was prepended; require old document bytes survive exactly at its original start.
  rawb=pp.read_bytes();oldpin=record['before_sha256'];ck('document_history_preserved '+rel,any(hashlib.sha256(rawb[i:]).hexdigest()==oldpin for i in sorted({i for m in re.finditer(b'(?m)^#',rawb) for i in [m.start(),max(0,m.start()-1)]})))
 blocker=update['new_blocker_document'];watch(R/blocker['path'],blocker['sha256']);txt=(R/blocker['path']).read_text();ck('blocker_doc_no_overclaim',all(x in txt for x in ['前72步动作','不能归因','尚未不同agent独审','task8','599','6713','不能用普通resume','不增加成功率分母']))
 # Static-only review of root Git delivery. Execution must still verify the exact index under writer lock.
 gp=R/'.local/deliver_20261020T2253_v4.py';watch(gp,'3fac309a6515f8ab7f7c124a4bec944c8f61b3881c337f3b20a30d85011bc63b');git=gp.read_text();ast.parse(git)
 for phrase in ["with c.exclusive_lock", "git('diff','--cached','--name-only').stdout==b''", "audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')", "assert not unknown", "p.stat().st_size<100*(1<<20)", "guard.check(R,SNAP,SSHA,RAW,required)", "frozen_files_verified_in_worktree_and_index", "BASE='5d379b52e79dc630efa7b9c6b52a0fe965742e2e'", "'.pt','.pth','.ckpt','.safetensors','.bin','.h5','.hdf5','.pkl','.pickle','.npy','.npz'"]:ck('Git_static_guard '+phrase,phrase in git)
 # Reconstruct ignored artifact allowlists in memory, without staging. Full blob members were verified earlier; only their immutable compressed-part hashes are reused here, not rescanned.
 for phrase in ["force_refs", "gm['blob_count']==10741", "len(gm['parts'])==15", "len(gm['metadata'])==12", "selected=sorted(set(selected)|set(force_refs))", "for n,v in force_refs.items():assert ref(n)==v", "no_glob_add_of_ignored_outputs"]:ck('Git_v4_exact_allowlists '+phrase,phrase in git)
 gm=rr(gr['archive_manifest']);allowlisted={}
 for row in gm['parts']:
  pp=R/row['path'];ck('known_verified_archive_part_size '+row['path'],pp.is_file() and not pp.is_symlink() and pp.stat().st_size==row['compressed_bytes']);allowlisted[row['path']]={'sha256':row['sha256'],'bytes':row['compressed_bytes']}
 for row in gm['metadata']:
  pp=R/row['destination'];watch(pp,row['sha256']);ck('Goal_metadata_exact '+row['destination'],pp.stat().st_size==row['bytes']);allowlisted[row['destination']]={'sha256':row['sha256'],'bytes':row['bytes']}
 for ap in sorted((R/B).glob('*_archive.json')):
  ar=rd(ap)
  if ar.get('status')!='immutable_nonweight_package_archived':continue
  dest=ar['destination'];ck('archive_inside_current_delivery '+dest,dest.startswith(E+'/'));orig=ar['manifest'];parent=Path(orig['path']).parent.as_posix();mrel=dest+'/'+Path(orig['path']).stem+'_original.json';m=rd(R/mrel,orig['sha256']);files=m['files']
  if isinstance(files,dict):files=[dict(v,path=k) for k,v in files.items()]
  ck('force_package_exact_count '+dest,len(files)==ar['file_count'])
  for row in files:
   n=row.get('source',row.get('path'))
   if n.startswith(parent+'/'):n=n[len(parent)+1:]
   ck('force_safe_path '+n,n and not Path(n).is_absolute() and '..' not in Path(n).parts)
   pp=R/dest/n;watch(pp,row['sha256']);ck('force_exact_size '+str(pp),pp.stat().st_size==row['bytes']);allowlisted[str(pp.relative_to(R))]={'sha256':row['sha256'],'bytes':row['bytes']}
 ck('all15parts_and12metadata_forced',sum(n.endswith('.tar.gz') and '/observer/' in n for n in allowlisted)>=15 and all(row['path'] in allowlisted for row in gm['parts']) and all(row['destination'] in allowlisted for row in gm['metadata']))
 ck('Git_no_push_force_amend',not any(x in git for x in ["git('push'",'--force','--amend','reset --hard']))
 watch(R/'scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6');watch(R/'.local/final_snapshot_20261020T2253_v2.py','39d3a148df81b20ea8259108314582472510f4da1f99b75c13fca41d9e4691aa')
 for path,record in refs.items():ck('stable '+path,sha(Path(path))==record['sha256'])
 ev=save('evidence.json',{'files':list(refs.values()),'allocation_costs_once':costrows,'prior_archive_precheck_sha256':'d1f61d0946926cf422116c4a4bdf376f45fb4d6e2d0240c51bb075be46bd66ac','selected_checkpoint_metadata_count':len(selected),'no_checkpoint_bytes_read':True,'no_running_P_ledger_or_report_read':True})
 report={'schema':'formal_main_v2','status':'passed_final_delivery_review','blockers':[],'state_sha256':STATE,'summary_sha256':SUMMARY,'source173_verified':True,'source173_locations':['R','P/frozen_snapshot','R/frozen_snapshot_mirror'],'final_sealed':True,'final_release':False,'final_trials':0,'compatible_development_trials':6400,'planned_development_trials':8800,'current_action_trials':5800,'compatible_Long600':True,'training_arms':72,'training_pairs':36,'training_updates':360000,'registered_formal_allocations':271,'allocated_GPU_seconds':total,'allocated_GPU_hours':total/3600,'active_registered_GPU_jobs_snapshot':[J],'new_GPU_jobs':[J],'new_scientific_trials':0,'Goal_original200_and_new_science_HOLD':True,'Object599_production_adoption_HOLD':True,'Object_correction_candidate_independent_or_production_admission':False,'Spatial_legacy12_current588_separate':True,'Spatial_mixed600_not_yet_admitted':True,'ACK_reconciled_once_no_resubmission':True,'snapshot_utc':q['utc'],'no_live_Slurm_queries':True,'no_new_blob_full_scan':True,'state_Git_Slurm_P_mutations':0,'new_GPU_seconds':0,'evidence':ev,'check_count':len(checks),'checks':checks,'Git_static_review':'Exact v4 scoped staging with pinned explicit ignored-file allowlists passed; actual index/173 check remains mandatory at root execution','scope_limit':'Object single-error CPU candidate archived with author evidence only; no independent code admission. ACK validator code review receipt inherited; final registration/ACK/cost reconstructed here. Goal blob audit inherited from this same agent verified prior pass, not rescanned.','CPU_seconds':time.process_time()-ct,'wall_seconds':time.perf_counter()-start}
 print(json.dumps({'review':save('independent_delivery_review.json',report),'state_sha256':STATE,'check_count':len(checks),'GPU_seconds':total}))
if __name__=='__main__':
 try:main()
 except BaseException as e:save('failure_'+str(time.time_ns())+'.json',{'error':str(e),'traceback':traceback.format_exc(),'checks':checks});raise
