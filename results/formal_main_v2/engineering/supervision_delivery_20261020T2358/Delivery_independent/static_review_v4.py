from pathlib import Path
import ast,hashlib,json,sys
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261020T2358'
pins={
'.local/final_snapshot_20261020T2358_v4.py':'0bf4af47d39b94fb4bccce5f54a58d46d34f1bd1f748e2ee93f63cef067d1609',
'.local/deliver_20261020T2358_v4.py':'c843e21b112b743263df195754753a22728b25ae81ff599755ec41843acf6c23',
'.local/final_snapshot_20261020T2358_v3.py':'c780b7ffb3d1dae09155363a2cb07b7b3481a76fdc936cda4d222645bdcfd24c',
'.local/deliver_20261020T2358_v3.py':'f445ccd3f5c20e606e5ea497c4c05b5560eaf6e9e2f81b04f5be13c6bb10c6f5',
'.local/github_push_20261020T2358.py':'245936cf9c3f7a197acf2018307680b470fbb11d12709747f1eb2b635c9a4008',
'scripts/ops/formal_autonomous_training_v1/controller.py':'acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363',
'scripts/ops/check_nonweight_archive_stage.py':'ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6',
'scripts/ops/server_github_sync.py':'218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729',
'scripts/ops/nonweight_archive.py':'f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'}
H=lambda b:hashlib.sha256(b).hexdigest()
checks=[];sources={}
def ck(b,name):
 if not b:raise AssertionError(name)
 checks.append({'check':name,'passed':True})
def publish(name,x):
 p=D/name;assert p.parent==D and not p.exists()
 b=(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
 with p.open('xb') as f:f.write(b)
 return {'path':p.relative_to(R).as_posix(),'bytes':len(b),'sha256':H(b)}
def guarded(event,args):
 if event in ('subprocess.Popen','os.system','socket.connect','socket.bind'):raise RuntimeError('Static auditor cannot execute subprocess or network')
 if event=='open':
  path,mode,flags=args
  if isinstance(path,(str,bytes)) and ((mode and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (1|2|64|512|1024))):
   if not Path(path).resolve().is_relative_to(D):raise RuntimeError('Static auditor write escaped private directory')
sys.addaudithook(guarded)
texts={}
for rel,want in pins.items():
 p=R/rel;ck(p.is_file() and p.resolve()==p,'regular:'+rel);b=p.read_bytes();ck(H(b)==want,'sourceSHA:'+rel);ast.parse(b)
 texts[rel]=b.decode();sources[rel]={'path':rel,'sha256':want,'bytes':len(b)}
snap=texts['.local/final_snapshot_20261020T2358_v4.py'];deliver=texts['.local/deliver_20261020T2358_v4.py'];push=texts['.local/github_push_20261020T2358.py']
ctl=texts['scripts/ops/formal_autonomous_training_v1/controller.py'];guard=texts['scripts/ops/check_nonweight_archive_stage.py'];sync=texts['scripts/ops/server_github_sync.py']
for label,text in [('snapshot',snap),('delivery',deliver),('push',push)]:
 ck('sbatch' not in text and 'squeue' not in text and 'sacct' not in text and 'scancel' not in text,'no_Slurm_calls:'+label)
 ck("with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):" in text,'shared_writer_lock:'+label)
ck("before=='a0d4d98f112adc082a04789c764d8c6006a2133cb61834f4b0e2097f5b64fb10'" in snap and 'c.atomic_json(sp,s,expected_sha=before)' in snap,'snapshot_exact_baseline_CAS')
ck('state changed outside writer transaction' in ctl and 'state changed before atomic publication' in ctl and 'os.replace(tmp,p)' in ctl and 'os.fsync' in ctl,'controller_double_CAS_atomic_replace_fsync')
ck("(72,360000,5800,7012,0)" in snap and "len(ctl['completed_pairs'])==36" in snap and "s['registered_jobs']==original['registered_jobs']" in snap,'snapshot72_36_360000_frozen_count_and_registry')
ck("cost==1987496==obsdoc['allocated_GPU_seconds']" in snap and "len(ids)==len(set(ids))==271" in snap and "cost_final_for_current_registered_set=False" in snap,'single_observation271_unique_alloc_cost1987496_lowerbound')
ck("new_GPU_jobs=[]" in snap and "new_development_accepted=0" in snap and "maximum_new_attempts=1" in snap and "GPU_execution_authorized=False" in snap,'zero_new_GPU_science_goal_design_only')
ck("new_output_path=None,submission_token=None" in snap and "production_runtime_installed=False" in snap,'no_Goal_output_token_runtime_authority')
ck("not adopted['whole600_admitted']" in snap and "adopted['legacy_equivalent_trials']==599" in snap and "'legacy599_root_adopted'" in snap,'Object599_legacy_only_whole600_HOLD')
ck("'--inputs-sha256',required=True" in snap and "link in i['evidence'].values()" in snap,'snapshot_typed_input_and_independent_refs_pinned')
ck("git('rev-parse','HEAD').stdout.decode().strip()==BASE" in deliver and "git('diff','--cached','--name-only').stdout==b''" in deliver,'commit_fixed_base_empty_index')
for token in ("audit['status']=='passed_final_delivery_review'","audit['blockers']==[]","audit['source173_verified'] is True","audit['final_sealed'] is True","audit['state_sha256']==h(R/'results/experiment_supervisor/state.json')"):
 ck(token in deliver,'mandatory_precommit_audit:'+token)
ck("assert len(old)==61" in deliver and "git('show','HEAD:'+name)" in deliver,'prior61_files_verified_and_excluded')
ck("if receipt.get('status')!='immutable_nonweight_package_archived':continue" in deliver and "assert len(files)==receipt['file_count']" in deliver and "h(R/mrel)==original['sha256']" in deliver,'ignored_files_from_exact_archived_manifest_receipts')
ck("for n,v in force_refs.items():assert ref(n)==v" in deliver and "git('add','-f','--',*selected[i:i+60])" in deliver,'explicit_force_add_verified_files_not_directory_glob')
ck("assert not unknown,unknown" in deliver and "guard.lexical(n)" in deliver and "not any(x.is_symlink()" in deliver,'unknown_paths_links_lexical_forbidden')
ck("p.stat().st_size<100*(1<<20)" in deliver and "'.pt','.pth','.ckpt','.safetensors','.bin'" in deliver,'size_weight_suffix_block')
ck("guard.check(R,SNAP,SSHA,RAW,required)" in deliver and "checked['frozen_files_verified_in_worktree_and_index']==173" in deliver,'nonweight_archive_and173_index_check_required')
ck("require(name not in index.changed, \"Frozen scientific file is staged: \" + name)" in guard and "same_local_index(index, name, codec, row)" in guard,'stage_guard_frozen_not_staged_and_all_required_bytes')
ck('index.unchanged()' in guard and 'codec.restore(clone' in guard and 'compare_originals(root, clone, row, codec)' in guard,'stage_guard_archive_restore_and_immutable_index')
ck("m=re.fullmatch" in deliver and "n.startswith((E+'/',B+'/root_operations/'))" in deliver and "git('diff','--cached','--check','--','.'" in deliver,'whitespace_exceptions_only_exact_archived_sources_then_rest_checked')
ck("git('commit','-m'" in deliver and "git('push'" not in deliver,'commit_helper_does_not_claim_or_perform_push')
ck("auth=json.load(sys.stdin)" in push and 'del auth' in push and "with out.open('x')" in push,'push_credentials_stdin_memory_and_immutable_nonsecret_receipt')
ck("value['local_head']==value['remote_head_after']==args.expected_head" in push and "value['credentials_persisted'] is False" in push,'push_requires_exact_local_remote_HEAD_and_no_persistence')
ck("URL='https://github.com/xingxiaoyang-888/DIWA.git'" in sync and "'credential.helper'" in sync and "GIT_CONFIG_VALUE_1=''" in sync,'github_exact_repo_inmemory_auth_no_credential_helper')
ck("['merge-base','--is-ancestor',before,local]" in sync and "['push','--porcelain','origin','HEAD:refs/heads/main']" in sync and '--force' not in sync,'github_nonforce_ancestor_checked_and_remote_ref_pinned')
ck("err=err.replace(secret,'[redacted]')" in sync and "after==local" in sync,'github_error_redaction_and_postpush_remote_check')
snap3=texts['.local/final_snapshot_20261020T2358_v3.py'];deliver3=texts['.local/deliver_20261020T2358_v3.py']
ck(snap==snap3.replace('旧第9次query原始数组缺失','旧 query index9（零基索引、第10次调用、step72）的原始数组缺失'),'v4_only_corrects_query_index_wording')
ck(deliver==deliver3.replace("'.local/final_snapshot_20261020T2358_v3.py'","'.local/final_snapshot_20261020T2358_v3.py','.local/final_snapshot_20261020T2358_v4.py'").replace("'.local/deliver_20261020T2358_v3.py'","'.local/deliver_20261020T2358_v3.py','.local/deliver_20261020T2358_v4.py'"),'v4_only_archives_two_additional_exact_helper_sources')
tree=ast.parse(snap)
writes=[ast.unparse(n) for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('write_bytes','write_text','open')]
ck(not any("P/" in w or "S/" in w for w in writes),'snapshot_write_targets_R_only_source_review')
for rel,want in pins.items():ck(H((R/rel).read_bytes())==want,'stable_entry:'+rel)
report={'schema':'formal_main_v2','kind':'root_final_delivery_helpers_static_independent_review','status':'passed_static_review_actual_snapshot_pending','reviewed_by':'independent_goal_cpu_gate_2054','utc':datetime.now(timezone.utc).isoformat(),'source_refs':sources,'check_count':len(checks),'checks':list(checks),'static_blockers':[],'wording_note':'Append-only snapshot v4 corrects old query index9 as zero-based index9, tenth policy call at step72; v3 retained. Scientific observations and all controls unchanged.','actual_state_summary_verified':False,'future_Git_operations_verified':False,'future_remote_push_verified':False,'new_GPU_jobs':0,'new_scientific_trials':0,'Slurm_queries':0,'state_Git_P_canonical_writes':0,'required_next':'After root publishes exact inputs/state/summary/doc snapshots, independently verify counts, provenance, typed HOLDs and immutable source173; only then issue passed_final_delivery_review tied to the actual state SHA.'}
ref=publish('static_review_v4.json',report);print(json.dumps({'report':ref,'status':report['status'],'check_count':report['check_count']}))
