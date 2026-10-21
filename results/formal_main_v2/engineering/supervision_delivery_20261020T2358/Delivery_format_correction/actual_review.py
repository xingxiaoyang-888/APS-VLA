from pathlib import Path
import hashlib,json,sys,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/delivery_format_correction_20261020T2358'
B='results/formal_main_v2/preflight/heartbeat_20261021T0758'
OLD='.local/delivery_independent_20261020T2358'
DOC='docs/正式下游阻塞登记_20261020T2358.md'
STATE='40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a'
H=lambda b:hashlib.sha256(b).hexdigest()
checks=[];refs={}
def ck(ok,label):
 if not ok:raise AssertionError(label)
 checks.append({'check':label,'passed':True})
def read(n,w=None):
 p=R/n
 ck(p.is_file() and not p.is_symlink() and p.resolve()==p,'regular:'+n)
 b=p.read_bytes()
 if w:ck(H(b)==w,'pin:'+n)
 refs[n]={'path':n,'sha256':H(b),'bytes':len(b)}
 return b
def guard(e,a):
 if e in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('No Git, Slurm, subprocess or network execution by supplemental auditor')
 if e=='open':
  p,m,f=a
  if isinstance(p,(str,bytes)) and ((m and any(c in m for c in 'wax+')) or (isinstance(f,int) and f&(1|2|64|512|1024))):
   assert Path(p).resolve().is_relative_to(D),'private output only'
sys.addaudithook(guard)
old=json.loads(read(OLD+'/final_independent_review.json','419c180e8d5bcaa89ba5c5620f7e09dab5302d522d8e4f53e85ff377166af1a5'))
om=json.loads(read(OLD+'/delivery_manifest.json','fa35971d52afc4ce76013aaa734b680dc1cec345dff3c02f787611a8ae5ffc92'))
ck(old['status']=='passed_final_delivery_review' and not old['blockers'] and old['source173_verified'] and old['final_sealed'] and old['state_sha256']==STATE,'original_final_review_eligible_for_exact_inheritance')
ck(old['check_count']==len(old['checks'])==3896 and all(c['passed'] for c in old['checks']),'original_3896_checks_inherited_not_reexecuted')
ck(om['file_count']==len(om['files'])==21,'old21_manifest_complete')
for row in om['files']:
 b=read(row['path'],row['sha256']);ck(len(b)==row['bytes'],'old_package_size:'+row['path'])
stat=json.loads(read(str((D/'static_review.json').relative_to(R)),'71b4442fa3efaf10a603da9820f4689442de521d6bbf02cb1a2f17534242cdf6'))
ck(stat['check_count']==len(stat['checks'])==35 and not stat['blockers'] and all(c['passed'] for c in stat['checks']),'narrow_static35_passed')
for n,v in stat['sources'].items():
 if n!=DOC:read(n,v['sha256'])
repair_source=read('.local/repair_git_format_20261020T2358_v1.py','4100c380d0284009b17c29dda7a1d86a782575064aa34d743d638a20a2884fa2').decode()
ck("len(staged)==224 and set(staged)==set(expected)" in repair_source and "raw==(R/n).read_bytes()" in repair_source,'root_actual_helper_exact_index_and_worktree_preconditions')
ck("git('restore','--staged','--',*staged[i:i+60])" in repair_source and "assert git('diff','--cached','--name-only').stdout==b''" in repair_source,'root_actual_helper_exact224_index_restore_and_empty_assertion')
ck("for n,v in expected.items():assert h(R/n)==v['sha256']" in repair_source and "(R/DOC).write_bytes(raw[:-1])" in repair_source,'root_actual_helper_no_other_worktree_change')
jr='results/formal_main_v2/control_transport/repair_git_format_20261020T2358_v1.jsonl'
events=[json.loads(s) for s in read(jr,'e8c48d5da53d1034bdcdf42f414d7214e7f20314b6207eb2279fcb5e313f24e4').splitlines()]
ck(len(events)==2 and [e['event'] for e in events]==['control_start','control_end'],'root_repair_closed_transport_only_start_end')
ck(events[0]['entrypoint']=='.local/repair_git_format_20261020T2358_v1.py' and events[0]['entrypoint_sha256']=='4100c380d0284009b17c29dda7a1d86a782575064aa34d743d638a20a2884fa2','root_repair_executed_exact_reviewed_source')
ck(events[0]['bundle_manifest_sha256']=='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149' and events[0]['frozen_files']==173 and events[1]['returncode']==0 and events[1]['source173_and_entrypoint_unchanged'],'root_repair_success_and173_transport_recheck')
rep=json.loads(read(B+'/git_format_repair.json','42c4803ed973c6ccfe47fd884e7379305c48dc7798656e96f0c65090afb616e5'))
fail=json.loads(read(B+'/git_v5_precommit_failure.json','a0d9a437c72247e066a6f578ed9770f698da1dc72edcbe377f16f180082c85b9'))
req_bytes=read(B+'/git_required_files.json','e52831510cbbc626612880054e4f151dd4d6c568eeebfe90a55e4e91979987ea')
req=json.loads(req_bytes)
ig=json.loads(read(B+'/git_index_guard.json','5129c715ea72a2a49125fb2660f52b059860438e670f9af9888272b60ed57fe7'))
arg=json.loads(read(B+'/commit_transport_argument_correction.json','2147a340c8236f21c64052b7b3ea0b617c85dc90958fda7de44311e04d3777f2'))
ck(arg['entrypoint_executed'] is False and arg['GPU_jobs_added']==0 and arg['state_unchanged'],'pre_entry_argument_failure_preserved_no_run')
ck(rep['status']=='single_LF_corrected_exact_index_restored_empty' and rep['document']==DOC and rep['bytes_removed']==1 and rep['unstaged_exact_paths']==224 and rep['worktree_files_deleted']==0 and rep['state_unchanged'] and rep['GPU_jobs_added']==0,'actual_repair_scope_no_delete_GPU_or_state_change')
ck(rep['prior_failure_receipt']==B+'/git_v5_precommit_failure.json' and fail['status']=='failed_before_commit_preserved','original_Git_failure_preserved_and_linked')
ck(fail['error']==DOC+':36: new blank line at EOF.\n','exact_single_EOF_check_failure')
required=req['files']+[{'path':B+'/git_required_files.json','sha256':H(req_bytes),'bytes':len(req_bytes)}]
rmap={r['path']:r for r in required};fmap={r['path']:r for r in fail['exact_staged_files']}
ck(len(required)==len(rmap)==len(fmap)==len(fail['exact_staged_files'])==224 and rmap==fmap,'all224_original_index_refs_equal223_required_plus_self')
ck(ig['ordinary_staged_files_verified']==224 and ig['frozen_files_verified_in_worktree_and_index']==173 and ig['head']=='456014638158b5495df0aa358a55f1c25a4f521c','preserved_index_guard_precommit_scope')
original=fail['original_doc_utf8'].encode()
ck(len(original)==6300 and H(original)==rep['before_sha256']=='d11864b253cdd9b4560db42e2c8d1c090846eddd4622182fc16c82a22ed66aa6','original_saved_doc_exact_before')
ck(original.endswith(b'\n\n') and not original.endswith(b'\n\n\n'),'original_exact_two_trailing_LF')
ck(old['read_refs'][DOC]['sha256']==H(original),'original_full_delivery_review_bound_original_document')
for n,v in rmap.items():
 b=read(n)
 if n==DOC:
  ck(b==original[:-1] and len(b)==6299 and H(b)==rep['after_sha256']=='ad7ecc7406aee39e9afdd0f3323aa27c3a5bbdca3db8bef48b5fed7d8488b966','only_one_final_LF_removed_all_other_document_bytes_unchanged')
 else:
  ck(H(b)==v['sha256'] and len(b)==v['bytes'],'other223_worktree_bytes_unchanged:'+n)
read('results/experiment_supervisor/state.json',STATE)
read(B+'/final_summary.json','75b5126b931377d3122a66f7ef5b7fd77d5655fd065d0fd6b95927797ed7ad76')
read(B+'/final_snapshot_inputs.json','57cc989b0a4544d4d9fc94724a4c0f0aade685c4ca387a39ebe91d25887fed2b')
read(B+'/state_and_document_update.json','82e5336d6950240e04b9d7e7f07b8b37b678315e1945627136966a93ad99ac47')
ck(not (D/'final_independent_review.json').exists(),'new_report_no_overwrite')
immutable_checks=tuple(checks)
report={'schema':'formal_main_v2','kind':'root_final_delivery_format_correction_independent_review','reviewed_by':'independent','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'passed_final_delivery_review','blockers':[],'state_sha256':STATE,'source173_verified':True,'final_sealed':True,'final_release':False,'scope':'Inherit the pinned complete 3896-check actual delivery review without reexecuting it; independently verify narrow repair-source delta, preserved failure and exact224 identities, one final LF removed from one document, all other223 worktree files and state/summary/inputs unchanged. Index restoration is established by reviewed exact root helper, successful approved transport and helper assertions; supplemental auditor does not execute Git. No future Git commit or push completion is claimed.','original_checks_inherited':3896,'original_review':refs[OLD+'/final_independent_review.json'],'original_manifest':refs[OLD+'/delivery_manifest.json'],'static_checks':35,'check_count':len(immutable_checks),'checks':immutable_checks,'document_correction':{'path':DOC,'before_sha256':H(original),'after_sha256':rep['after_sha256'],'before_bytes':6300,'after_bytes':6299,'only_final_LF_removed':True,'semantic_body_unchanged':True},'actual_root_index_repair':{'exact_original_staged_paths':224,'all_paths_and_index_bytes_checked_before_unstage':True,'root_asserted_empty_index_after_exact_unstage':True,'independent_Git_commands':0,'execution_transport':refs[jr],'receipt':refs[B+'/git_format_repair.json']},'inherited_scientific_evidence':{k:old[k] for k in ['training','development','cost','Goal','Object_production_candidate','source173_roots']},'new_GPU_submissions':0,'new_scientific_trials':0,'additional_Slurm_queries':0,'production_state_Git_P_canonical_writes':0,'Git_commit_and_push_pending':True,'read_refs':refs}
out=D/'final_independent_review.json';data=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
with out.open('xb') as f:f.write(data)
print(json.dumps({'path':str(out.relative_to(R)),'sha256':H(data),'bytes':len(data),'status':report['status'],'check_count':len(immutable_checks),'original_checks_inherited':3896}))
