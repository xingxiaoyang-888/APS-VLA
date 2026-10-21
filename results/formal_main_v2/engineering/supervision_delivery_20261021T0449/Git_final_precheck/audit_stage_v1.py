"""Read-only final staged delivery audit. No science execution or live scheduler access."""
from pathlib import Path,PurePosixPath
import ast,collections,datetime,fcntl,hashlib,importlib.util,json,os,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/git_final_precheck_20261021T0449'
B='results/formal_main_v2/preflight/heartbeat_20261021T1249'
E='results/formal_main_v2/engineering/supervision_delivery_20261021T0449'
INDEX='7b84527592221abab8dffc3096a623432c8d92560c89f57dc04cc5b13046f6a6'
STATE='0621504d45ef43e44f6d46c01d0a8c4d0c9acdfdd29d05df9101d75979fc5d6e'
SUMMARY='281cb598d6dda4b50420be5439256607fdb5e9c70bf59a8dafba1e68b7546391'
REQ='daf0c53e281d7f637b2a20ba53dc7182d400242b1b5978b006b3aee3a2d01e19'
GUARD='scripts/ops/check_nonweight_archive_stage.py';GSH='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
INV='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json';ISH='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926'
FIN='.local/finish_delivery_20261021T0449_v2.py';FSH='c2e24fb9991381826561aecfa198b05309ac0d4ba83bab9431d8e9d6c942e3bb'
PUSH='.local/push_delivery_20261021T0449.py';PSH='6c4c54551f36440e2525b48c3d77eb99b7331a1c8b8dfe036160099e9550ac32'
PINS={
 'libero_goal_k256_seed23':'3057505','libero_goal_k256_seed41':'3057510',
 'libero_goal_k64_seed17':'3057515','libero_goal_k64_seed23':'3057526','libero_goal_k64_seed41':'3057533'}
ADD=[
 {'path':'.local/goal_remaining5_independent_20261021T0449/scope_bootstrap.py','sha256':'9ff5d967b8e058c5aff977fdbfac8abdcab741603fdd025d1ba8058d762c38d4','bytes':6358},
 {'path':'.local/goal_remaining5_independent_20261021T0449/scope_bootstrap_v2.py','sha256':'f37d20dc0e319893b3489c402516368d8808307955124fadfa023038e78c0e69','bytes':7442}]
checks=[];blockers=[]
def check(ok,label,detail=None):
 row={'check':label,'passed':bool(ok)}
 if detail is not None:row['detail']=detail
 checks.append(row)
 if not ok:blockers.append(row)
 assert ok,(label,detail)
def sha(b):return hashlib.sha256(b).hexdigest()
def read(n):
 p=R/n;assert p.resolve()==p and all(not q.is_symlink() for q in [p,*p.parents])
 old=p.stat();b=p.read_bytes();new=p.stat()
 assert (old.st_ino,old.st_size,old.st_mtime_ns)==(new.st_ino,new.st_size,new.st_mtime_ns)
 return b
def ref(n):b=read(n);return dict(path=n,sha256=sha(b),bytes=len(b))
def rd(n):return json.loads(read(n))
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def save(n,v):
 with (D/n).open('xb') as f:f.write(enc(v))
def source_path(root,name):
 p=Path(name)
 if p.is_absolute():out=p
 elif name.startswith('.local/'):out=R/p
 else:out=root/p
 assert out.resolve()==out and root in out.parents
 return out
def exclusion(n):
 parts=PurePosixPath(n).parts
 check(not any(x.lower() in ('raw_runtime','blobs','weights','checkpoint','checkpoints','sealed','test') for x in parts),'whole_raw_and_protected_path_exclusion',n)
 check(not any('sealed' in x.lower() for x in parts),'sealed_name_exclusion',n)
 check('attempt01' not in parts and 'original_run' not in parts and not n.startswith('results/slurm/'),'real_attempt_results_and_live_logs_exclusion',n)
def meta_ref(row,required):
 n=row['path'];check(n in required,'referenced_control_file_delivered',n)
 got=ref(n);check(got['sha256']==row['sha256'] and ('bytes' not in row or got['bytes']==row['bytes']),'control_ref_exact',n)
 return rd(n)
check(sha(read(GUARD))==GSH,'original_guard_pin')
sp=importlib.util.spec_from_file_location('final0449_readonly_guard',R/GUARD);guard=importlib.util.module_from_spec(sp);sys.modules[sp.name]=guard;sp.loader.exec_module(guard)
check(sha(read(INV))==ISH,'original_173_inventory_pin')
# A shared lock only holds the current read snapshot; no state/index write or lock metadata is made.
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 check(sha(read('.git/index'))==INDEX,'physical_index_initial_pin')
 check(sha(read('results/experiment_supervisor/state.json'))==STATE,'state_initial_pin')
 check(sha(read(B+'/final_summary.json'))==SUMMARY,'summary_initial_pin')
 check(sha(read(B+'/git_required_files_v1.json'))==REQ,'required_initial_pin')
 rawreq=rd(B+'/git_required_files_v1.json');reqrows=rawreq['files'];required={r['path']:r for r in reqrows}
 check(rawreq['schema']=='cti_nonweight_archive_stage_v1' and rawreq['kind']=='required_files','required_original_schema')
 check(len(reqrows)==len(required)==len({n.casefold() for n in required})==710,'required_unique_exact710_no_alias')
 check(B+'/git_required_files_v1.json' not in required,'required_not_self_referencing')
 extras={B+'/git_required_files_v1.json',B+'/git_index_guard_v1.json',B+'/git_whitespace_diagnostic_v1.json'}
 for n in required:
  guard.lexical(n);exclusion(n)
 with guard.index_reader(R) as idx:
  check(idx.before[2].decode()=='0b46f1169042e407c128e226b8cc7eabb468e873','HEAD_unchanged_precommit')
  check(set(idx.changed)==set(required)|extras and len(idx.changed)==713,'staged_exact713_required_plus_three_diagnostics')
  check(set(idx.changed.values())<={'A','M'},'no_staged_deletion_or_type_change')
  staged=[]
  for n in sorted(set(required)|extras):
   guard.lexical(n);exclusion(n);b=read(n);ib=idx.blob(n)
   check(b==ib and len(b)<100*(1<<20),'all_staged_worktree_index_exact_under_limit',n)
   row=dict(path=n,sha256=sha(b),bytes=len(b))
   if n in required:check(row==required[n],'required_SHA_bytes_exact',n)
   staged.append(dict(**row,index_oid=idx.entries[n]['oid'],mode=idx.entries[n]['mode'],status=idx.changed[n]))
  inventory=rd(INV);check(len(inventory['files'])==173,'frozen173_count')
  for n,pin in inventory['files'].items():
   check(n not in idx.changed and sha(read(n))==sha(idx.blob(n))==pin,'frozen173_worktree_and_index',n)
  old=E+'/Git_static_precheck';oldm=rd(old+'/delivery_manifest_original.json')
  check(sha(read(old+'/delivery_manifest_original.json'))=='744e7a5426bb9d1b4fc29cecf1f01453d74346c865e5319ba71e4e7c9e66ca57','inherited_precheck_manifest_pin')
  for r in oldm['files']:
   n=old+'/'+r['path'];check(n in required and ref(n)==dict(r,path=n),'inherited_precheck_member_delivered_exact',n)
  pre=rd(old+'/independent_precheck.json')
  check(sha(read(old+'/independent_precheck.json'))=='10f50efa57479dedab60af4ae08937c40f42107e8eb53d3e9054658f5db52d5f' and pre['check_count']==len(pre['checks'])==2352 and not pre['blockers'],'inherit_2352_archive_static_checks_only')
  captured=rd(old+'/captured_inventory.json')['files']
  for r in captured:check(r['path'] in required and required[r['path']]==r,'previous389_files_staged_unchanged',r['path'])
  ars=rd(old+'/CPU_tar_member_review.json')
  check(ars['archive_count']==19 and ars['total_members']==7770,'inherit19_tars_7770_exact_members_no_replay')
  allowed=rd(B+'/git_external_nonweight_allowlist_v1.json')
  archive_refs=[a['archive'] for a in ars['archives']]
  check(allowed['CPU_archives']==archive_refs and allowed['CPU_member_count']==7770,'exact_CPU_archive_allowlist_matches_prior_review')
  check({n for n in required if n.endswith('.tar.gz')}=={a['path'] for a in archive_refs},'no_unreviewed_tar_or_archive_expansion')
  for a in ars['archives']:
   for k in ('archive','member_manifest'):
    r=a[k];check(required[r['path']]==r,'tar_and_member_inventory_exact_staged_bytes',r['path'])
  ign=rd(B+'/git_ignored_allowlist_v1.json')['files']
  check(len(ign)==len({r['path'] for r in ign})==19 and ign==sorted(archive_refs,key=lambda r:r['path']),'ignored_allowlist_exact19_CPU_archives')
  got=idx.git('check-ignore','--no-index','-z','--stdin',data=('\0'.join(sorted(set(required)|extras))+'\0').encode())
  ignored_actual={x.decode() for x in got.split(b'\0') if x}
  check(ignored_actual=={r['path'] for r in ign},'actual_ignore_rules_match_exact19_forced_paths')
  # The completed original guard is inherited at its exact required list. Its
  # archive restoration is not repeated; all resulting metadata and bytes are pinned.
  g=rd(B+'/git_index_guard_v1.json')
  check(g['status']=='verified_index_archive_delivery' and g['required_files']==ref(B+'/git_required_files_v1.json') and g['required_count']==710,'original_index_guard_binds_same_required710')
  check(g['checker_sha256']==GSH and g['frozen_files_verified_in_worktree_and_index']==173 and g['archive_verification']=='verified' and g['restore_verification']=='restored_verified' and g['allowed_raw_deletions']==[],'original_archive_restore_guard_inherited_exact')
  check(g['head']==idx.before[2].decode(),'original_guard_same_HEAD')
  for r in g['archive_index_files'].values():
   guard.lexical(r['path']);check(sha(idx.blob(r['path']))==r['sha256'] and len(idx.blob(r['path']))==r['bytes'],'original_guard_archive_index_ref',r['path'])
  for r in g['raw_paths_restored_exactly']:check(r['path'] not in idx.entries,'original_archived_raw_absent_from_index',r['path'])
  check(rd(B+'/git_whitespace_diagnostic_v1.json')=={'returncode':0,'stderr':'','stdout':''},'saved_whitespace_diagnostic_zero')
  check(not idx.git('diff','--cached','--check','--no-ext-diff'),'current_whitespace_check_zero')
  # New small archived packages: this validates publication identity only.
  newpins={
   'Goal_ACK_independent':'496077f29e8c36635b0abc983fc2b14e00d2fc7a9bcf9644611c36dec963b063',
   'Goal_authorization_helper_independent':'2206fddb7bfdd1f06b1648cc7f8366a2b457f63f511363651eea06d3e36c7779',
   'Goal_fixed30_design':'7100bf88f63840006fb726b9447cdc7414e5500d96f365904a57c270c5c4ebc9',
   'Goal_published_interface_independent':'d05b2fd96eec3e5e3f8db9e20835c32b6e360a45e8879097ee2a181489421050'}
  newmaps=[]
  for name,pin in newpins.items():
   base=E+'/'+name;mp=base+'/delivery_manifest_original.json'
   check(sha(read(mp))==pin,'new_package_original_manifest_pin',name);m=rd(mp);v=m.get('source_root',m.get('root'));root=Path(v);root=root if root.is_absolute() else R/root
   check(R/'.local' in root.parents,'new_package_private_source_root',name)
   check(len(m['files'])==m['file_count'],'new_package_manifest_count',name)
   expected=[]
   for r in m['files']:
    src=source_path(root,r['path']);rel=src.relative_to(root).as_posix();n=base+'/'+rel
    check(n in required and required[n]==dict(r,path=n) and sha(src.read_bytes())==r['sha256'] and src.stat().st_size==r['bytes'],'new_package_member_original_source_staged_same',n)
    expected.append(dict(source=src.relative_to(R).as_posix(),**required[n]))
   sm=rd(base+'/source_map.json');check(sm['manifest_sha256']==pin and sm['files']==expected,'new_package_source_map_exact',name)
   newmaps.append(dict(package=name,manifest=ref(mp),files=len(expected)))
  # All historical control logs remain closed, including first failures.
  tm=rd(B+'/root_transport_manifest.json');bysha=collections.defaultdict(list)
  for r in reqrows:bysha[r['sha256']].append(r['path'])
  traces=[];missing=[]
  for r in tm['files']:
   check(required.get(r['path'])==r,'control_log_exact_required_ref',r['path'])
   events=[json.loads(l) for l in read(r['path']).splitlines()]
   check(events[0]['event']=='control_start' and events[-1]['event']=='control_end','control_trace_closed_not_live',r['path'])
   a,z=events[0],events[-1]
   check(a['bundle_manifest_sha256']=='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149' and a['frozen_files']==173 and z['source173_and_entrypoint_unchanged'] is True,'control_transport_exact_and_frozen',r['path'])
   matches=bysha[a['entrypoint_sha256']]
   if not matches:missing.append(dict(trace=r['path'],entrypoint=a['entrypoint'],sha256=a['entrypoint_sha256']))
   traces.append(dict(path=r['path'],entrypoint=a['entrypoint'],entrypoint_sha256=a['entrypoint_sha256'],returncode=z['returncode'],delivered_source_paths=matches))
  check(len(traces)==78,'all78_completed_control_traces_checked')
  check({x['sha256'] for x in missing}=={x['sha256'] for x in ADD} and len(missing)==2,'only_two_identity_sources_require_exact_finish_addition')
  for a in ADD:
   check(ref(a['path'])==a,'two_pending_entry_sources_real_original_bytes',a['path'])
   ast.parse(read(a['path']).decode());check(True,'two_pending_entry_sources_are_Python_not_payload',a['path'])
  # These are closed saved transaction records, never the live production attempt.
  receipt=rd(B+'/Goal_remaining5_submissions_root_receipt.json');ackreview=rd(E+'/Goal_ACK_independent/independent_review.json')
  check(sha(read(E+'/Goal_ACK_independent/independent_review.json'))=='8567a9f95a3c92004105a50a5779db76710612013d4d8c853dc4d2dc741fcbf5' and ackreview['status'].startswith('passed') and not ackreview['blockers'],'inherited_independent_real_ACK_review_exact')
  check(receipt['new_scientific_trials_accepted']==0 and receipt['duplicate_submissions']==0 and receipt['release_count_per_job']==1,'root_submission_receipt_no_results_or_repeat')
  check({x['pair_key']:x['job_id'] for x in receipt['jobs']}==PINS,'five_exact_pair_job_mapping')
  state=rd('results/experiment_supervisor/state.json');summary=rd(B+'/final_summary.json');obs=meta_ref(receipt['observation'],required)
  pairs=[];top={'dispatch_admission.json','effective_plan.json','execution_contract.json','execution_manifest.json','held_dispatch_record.json','independent_readiness.json','invocation_template.json','plan_independent_review.json','plan_root_review.json','reservation.json','root_authorization.json','root_readiness.json','runtime_readiness.json','scientific_plan.json','source_provenance.json','specification.json'}
  events={'committed.json','failed_transaction.json','held_capacity_before_registration.json','held_identity.json','pending.json','post_release_observation.json','preflight.json','registered_held.json','release_attempt.json','release_result.json','released_identity.json','sbatch_result.json'}
  exactmeta=set()
  for job in receipt['jobs']:
   key=job['pair_key'];jid=PINS[key];x='results/formal_main_v2/execution/goal_remaining5_v1/'+key
   exactmeta|={x+'/'+n for n in top}|{x+'/dispatch_attempt01/'+n for n in events}
   for k in ('admission','authorization','committed','held_dispatch','independent_submission_review','original_ACK','original_accounting_delay'):meta_ref(job[k],required)
   auth=rd(x+'/root_authorization.json');authsha=ref(x+'/root_authorization.json')['sha256'];token='cti-goal-remaining5-v1:'+key+':'+authsha
   pending=rd(x+'/dispatch_attempt01/pending.json');ack=rd(x+'/dispatch_attempt01/sbatch_result.json');held=rd(x+'/held_dispatch_record.json')
   commit=rd(x+'/dispatch_attempt01/committed.json');rel=rd(x+'/dispatch_attempt01/release_result.json');relatt=rd(x+'/dispatch_attempt01/release_attempt.json');reg=rd(x+'/dispatch_attempt01/registered_held.json');fail=rd(x+'/dispatch_attempt01/failed_transaction.json')
   check(ack['returncode']==0 and ack['stdout']==jid+'\n' and ack['actual_sbatch_argv']==pending['actual_sbatch_argv']==held['actual_sbatch_argv'],'same_original_ACK_and_exact_sbatch_argv',key)
   check(pending['submission_token']==pending['slurm_comment']==held['request_token']==token and '--comment='+token in ack['actual_sbatch_argv'],'pair_AUTH_token_comment_bound',key)
   check('--hold' in ack['actual_sbatch_argv'] and '--no-requeue' in ack['actual_sbatch_argv'] and held['job_id']==commit['job_id']==jid,'held_unique_job_identity',key)
   check(rel['returncode']==0 and rel['argv']==relatt['argv']==['scontrol','release',jid] and relatt['submission_token']==token and relatt['state_sha256']==reg['state_sha256']==held['state_after_sha256'],'original_release_after_registration',key)
   check(fail['status']=='HOLD_reconcile_original_ACK_only' and fail['automatic_retry'] is False,'accounting_delay_failure_retained',key)
   check(auth['pair_key']==key and auth['maximum_attempts']==1 and auth['maximum_trials']==200 and auth['scientific_release'] is False and auth['original_goal200_HOLD'] is True,'authorization_is_bounded_development_only',key)
   selected=[j for j in state['registered_jobs'] if j['job_id']==jid]
   check(len(selected)==1 and selected[0]['pair_key']==key and selected[0]['submission_token']==token and selected[0]['method_ids']==job['method_ids'],'unique_registered_job_metadata',key)
   check(selected[0]['scientific_trials']==0 and job['completed_trials_accepted']==0 and job['scientific_terminal_acceptance_pending'] is True,'no_inflight_science_accepted',key)
   for name,pin in held['source_files'].items():check(name in required and required[name]['sha256']==pin,'held_source_closure_in_index',name)
   pairtr=[t for t in traces if t['path'].endswith(('submit_goal_r5_k'+key.split('_k')[1].replace('_seed','s')+'_20261021T0449.jsonl','reconcile_goal_r5_k'+key.split('_k')[1].replace('_seed','s')+'_20261021T0449.jsonl'))]
   check(len(pairtr)==2 and sorted(t['returncode'] for t in pairtr)==[0,1],'exact_one_submit_failure_and_one_ACK_reconcile_trace',key)
   pairs.append(dict(pair_key=key,job_id=jid,authorization_sha256=authsha,original_ACK=job['original_ACK'],same_token_and_source=True,first_failure_retained=True,release_count_in_inherited_review=1,raw_results_read=False))
  check({r['path'] for r in allowed['closed_dispatch_metadata']}==exactmeta and len(exactmeta)==140,'exact140_closed_dispatch_metadata_allowlist')
  check({n for n in required if n.startswith('results/formal_main_v2/execution/goal_remaining5_v1/')}==exactmeta,'no_extra_attempt_execution_payload_in_required')
  check(summary['new_current_development_trials_accepted']==summary['new_complete_batch_rows_accepted']==0 and summary['compatible_development_trials']==7800 and summary['current_action_development_trials']==6589,'summary_preserves_science_counts')
  check(summary['final_sealed'] is True and summary['global_release'] is False and summary['O2A_released'] is False and summary['Goal_old200_HOLD'] is True,'final_and_old_Goal_HOLD_preserved')
  check(summary['registered_formal_allocations']==278 and summary['allocated_GPU_seconds']==1995402 and summary['cost_final_for_current_registered_set'] is False and obs['formal_GPU_seconds']==1995402,'saved_cost_scope_only_running_lower_bound')
  check(state['pending_submission'] is None and state['autonomous_training_v1']['reserved_GPU_slots']==0,'saved_pending_and_reservation_closed')
  check(set(summary['active_registered_GPU_jobs'])==set(PINS.values()),'saved_activity_projection_exact_five_no_live_poll')
  # Limited static review of root's exact-two-source closure correction and finish.
  check(sha(read(FIN))==FSH and sha(read(PUSH))==PSH,'finish_v2_and_push_exact_pins')
  fs=read(FIN).decode();ps=read(PUSH).decode();ast.parse(fs);ast.parse(ps)
  predicates={
   'shared_writer_lock':'with ctl.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):' in fs,
   'fixed_old_index_and_HEAD':'h(R/".git/index")==INDEX' in fs and 'git("rev-parse","HEAD").stdout.decode().strip()==BASE' in fs,
   'fixed_state_summary':'h(R/STATE)==ST and h(R/B/"final_summary.json")==SUM' in fs,
   'exact2_sources':[a['sha256'] in fs for a in ADD]==[True,True] and 'E+"/Goal_identity_entry_sources/"+name' in fs,
   'samebyte_copy_no_source_execution':'assert h(R/src)==pin' in fs and 'cp(src,out)' in fs and 'scientific_identity_audit_not_rerun=True' in fs,
   'preserve_old_required_and_diagnostics':'added=[old,B+"/git_index_guard_v1.json",B+"/git_whitespace_diagnostic_v1.json"]' in fs,
   'required_v2_new_unique_nonself':'required=B+"/git_required_files_v2.json";assert required not in rows' in fs and 'len(rows)==len({n.casefold() for n in rows})' in fs,
   'original_guard_again':'checked=guard.check(R,SNAP,SSHA,raw,required)' in fs and 'checked["frozen_files_verified_in_worktree_and_index"]==173' in fs,
   'no_raw_additions':'"/raw_runtime/" not in n' in fs and '"/observer/blobs/" not in n' in fs and '"/attempt01/" not in n' in fs,
   'exact_final_staged_set':'assert expected==staged' in fs and 'git("show",":"+n).stdout==(R/n).read_bytes()' in fs,
   'whitespace_before_commit':'git("diff","--cached","--check")' in fs,
   'xb_new_files':'p.open("xb")' in fs,
   'push_stdin_auth_pinned_helper':'auth=sys.stdin.buffer.read()' in ps and '218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729' in ps,
   'push_verified_remote_and_no_persist':'result["remote_head_after"]==result["local_head"]==a.expected_head' in ps and 'result["credentials_persisted"] is False' in ps,
  }
  for k,v in predicates.items():check(v,'limited_finish_source_review_'+k)
  check('--force' not in fs+ps and 'reset' not in fs and 'scancel' not in fs+ps,'no_force_reset_or_job_control_added')
  idx.unchanged()
  check(sha(read('.git/index'))==INDEX and sha(read('results/experiment_supervisor/state.json'))==STATE and sha(read(B+'/final_summary.json'))==SUMMARY,'final_index_state_summary_unchanged')
  save('staged_file_inventory.json',{'files':staged,'file_count':len(staged),'required':ref(B+'/git_required_files_v1.json'),'index_sha256':INDEX,'head':idx.before[2].decode()})
  save('control_source_review.json',{'traces':traces,'trace_count':len(traces),'exact_missing_current_staged_sources':missing,'mandatory_finish_exact_source_refs':ADD,'finish_source':ref(FIN),'finish_not_executed_by_reviewer':True,'new_small_archived_packages':newmaps,'pairs':pairs})
  report={'schema':'formal_main_v2','kind':'bounded_final_Git_stage_precheck','status':'passed_exact713_index_with_explicit_finish_v2_source_completion','blockers':[],'reviewed_by':'goal_cpu_gate_2054_Git_delivery_scope_only','review_scope':'713 current staged files and original required710; exact metadata/source/archive delivery, not independent scientific audit of author runtime. Limited finish_v2 source review, not execution.','state_sha256':STATE,'summary_sha256':SUMMARY,'index_sha256':INDEX,'required_files':ref(B+'/git_required_files_v1.json'),'staged_files':713,'required_count':710,'source173_verified':True,'final_sealed':True,'inherited_static_check_count':2352,'inherited_CPU_tar_count':19,'inherited_CPU_members':7770,'original_archive_restore_guard':ref(B+'/git_index_guard_v1.json'),'source_closure_complete_in_current_index':False,'mandatory_finish_exact_source_additions':ADD,'approved_finish_entrypoint':ref(FIN),'approved_push_source':ref(PUSH),'finish_execution_verified':False,'final_commit_or_remote_push_verified':False,'whole_raw_runtime_observer_blobs_attempt_results_excluded':True,'ignored_allowlist_exact19':True,'closed_ACK_jobs':[v for v in PINS.values()],'normal_GPU_jobs_polled':False,'new_Slurm_queries_or_submissions':0,'scientific_results_read':False,'scientific_tests_reexecuted':False,'Git_or_state_writes':False,'checkpoint_or_sealed_values_read':False,'checks':checks,'check_count':len(checks),'limitations':['Two original identity control entrypoints are not yet staged. Exact source SHA/bytes were verified and only finish_v2 at the pinned SHA is approved to copy them into Goal_identity_entry_sources with its source_map and final required_v2.','After exact additions, root must rerun the unchanged nonweight/index/archive/frozen173 guard and final staged-set checks before commit, as implemented in finish_v2.','No claim is made that future finish, commit or nonforce push has occurred. Runtime scientific review and ACK transactional science gates are inherited by precise existing reports, not rerun or self-audited here.']}
  save('independent_stage_precheck.json',report)
  print(json.dumps({'status':report['status'],'check_count':len(checks),'report':ref(str((D/'independent_stage_precheck.json').relative_to(R))),'staged_files':713,'mandatory_exact_source_additions':len(ADD)},sort_keys=True))
