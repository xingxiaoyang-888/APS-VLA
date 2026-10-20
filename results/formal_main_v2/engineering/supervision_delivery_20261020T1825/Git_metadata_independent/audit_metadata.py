from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import os,subprocess,json,hashlib,fcntl,ast,re
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/git_metadata_audit_20261020T1825'
B='results/formal_main_v2/preflight/heartbeat_20261021T0225/'
E='results/formal_main_v2/engineering/supervision_delivery_20261020T1825/'
GUARD='scripts/ops/check_nonweight_archive_stage.py'
GPIN='ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'
BUNDLE='3726e3249403e3afa1d4fd1688b9f08ec9d85087812efdf297d393382c18b149'
ENV=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
checks=[]
def check(ok,label):
 if not ok: raise AssertionError(label)
 checks.append(label)
def sha(b):return hashlib.sha256(b).hexdigest()
def git(*args):
 check(args[0] in ['diff','show','rev-parse','ls-files'],'read_only_git_'+args[0])
 return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,env=ENV,capture_output=True,check=True).stdout

def save(name,v):
 with (D/name).open('x',encoding='utf-8') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def canonical(p):
 q=PurePosixPath(p)
 return isinstance(p,str) and p and not q.is_absolute() and str(q)==p and '..' not in q.parts and '\\' not in p
expected={
'results/formal_main_v2/control_transport/archive_sealed_packages_20261020T1825.jsonl':('4a85808e5e25ef6615804b5031cf5981439562649d1c890003e8fddb917895dc',1059,'completed_server_transport_metadata'),
'results/formal_main_v2/control_transport/sealed_packages_archive_part2_20261020T1825.jsonl':('d5ce0180c68008a3cf26bd51d5f4e9265f820833718f3eca14180345724ac79d',1071,'completed_server_transport_metadata'),
'results/formal_main_v2/control_transport/sealed_packages_archive_part3_20261020T1825.jsonl':('e241dbfd1c552726f117f390d64ed1cdfe09c573aba67e8ef421c7d449b1c8bf',1071,'completed_server_transport_metadata'),
B+'sealed_packages_archive.json':('4ee4615a38712267c93222fa767a0df90f9cdbf1cc020b7b5349fd6a8995e4a4',141252,'nonweight_audit_package_copy_manifest_metadata'),
B+'sealed_packages_archive_Goal_terminal.json':('69890b9366986b908bb2c9018c3c0415503cb63ed9f06845626ada4da4b85106',26235,'nonweight_audit_package_copy_manifest_metadata'),
B+'sealed_packages_archive_part2.json':('750b03453cfda53e8c7d7fcc9079fe21e655d6343ef7443a331a318433fb5c34',32620,'nonweight_audit_package_copy_manifest_metadata'),
B+'sealed_packages_archive_part3.json':('5668c5a94de3c7be817a223d9875af391b58900ef6011e2b25b4afbe7ee525df',30328,'nonweight_audit_package_copy_manifest_metadata')}
sources={
'archive_sealed_packages_20261020T1825.py':('ee5f802031a736fc695071e811df41a6fe013bfeef67863bbc484e15c2f188cc',3828),
'archive_sealed_packages_part2_20261020T1825.py':('87e0ca256d05f7e5f9816dd34221ce84c66df0816d6f7383c0e90c96f2e21d30',3539),
'archive_sealed_packages_part3_20261020T1825.py':('bc9a91155c94480a44c89f801db024f813d3caa0423d308f12e36bef660b15e9',3356)}
for n,(pin,size) in sources.items():
 for pre in [B+'root_operations/',E+'root_helpers/']:expected[pre+n]=(pin,size,'audited_nonweight_package_copy_source_not_executed_here')
with (R/'results/experiment_supervisor/.writer.lock').open('rb') as lk:
 fcntl.flock(lk,fcntl.LOCK_SH)
 state_before=sha((R/'results/experiment_supervisor/state.json').read_bytes())
 head=git('rev-parse','HEAD').decode().strip()
 index_file=Path(git('rev-parse','--git-path','index').decode().strip());index_file=index_file if index_file.is_absolute() else R/index_file
 index_before=sha(index_file.read_bytes())
 names_raw=git('diff','--cached','--name-only','-z');names=[x for x in names_raw.decode().split('\0') if x]
 entries_raw=git('ls-files','--stage','-z')
 selected=[x for x in names if 'sealed' in x.lower()]
 check(len(names)==731,'exact_731_staged_paths')
 check(len(selected)==13 and set(selected)==set(expected),'exact_13_metadata_paths_no_scope_expansion')
 check(sha((R/GUARD).read_bytes())==GPIN,'original_index_guard_pin')
 all_files=[];details=[]
 for p in sorted(selected):
  pin,size,kind=expected[p];f=R/p;raw=f.read_bytes();idx=git('show',':'+p)
  check(f.resolve()==f and not any(x.is_symlink() for x in [f,*f.parents]),p+':regular_nonaliased_source')
  check(len(raw)==size and sha(raw)==pin,p+':exact_reviewed_bytes')
  check(raw==idx,p+':index_blob_matches_retained_server_original')
  status=git('diff','--cached','--name-status','--no-renames','--',p).decode().rstrip('\n')
  check(status=='A\t'+p,p+':only_new_index_addition')
  text=raw.decode('utf-8');check('\x00' not in text,p+':UTF8_text_no_binary_payload')
  row=dict(path=p,sha256=pin,bytes=size,classification=kind);all_files.append(row)
  detail=dict(path=p,classification=kind,index_status='A')
  if p.endswith('.json'):
   value=json.loads(text)
   check(set(value)=={'bytes','file_count','final_values_read','rows','schema','state_sha256','state_unchanged','status','utc','weights_copied'},p+':only_manifest_schema')
   check(value['schema']=='formal_main_v2' and value['status']=='nonweight_packages_archived_exactly',p+':copy_receipt_kind')
   check(value['final_values_read'] is False and value['weights_copied'] is False and value['state_unchanged'] is True,p+':producer_scope_flags')
   check(re.fullmatch('[0-9a-f]{64}',value['state_sha256']) is not None,p+':state_digest_not_state_payload')
   for item in value['rows']:
    check(set(item)=={'bytes','path','sha256','source'},p+':mapping_fields_only')
    check(canonical(item['source']) and canonical(item['path']),p+':relative_source_target_metadata')
    check(type(item['bytes']) is int and item['bytes']>=0 and re.fullmatch('[0-9a-f]{64}',item['sha256']) is not None,p+':size_digest_only')
   check(value['file_count']==len(value['rows']) and value['bytes']==sum(x['bytes'] for x in value['rows']),p+':metadata_totals')
   detail.update(mapping_rows=len(value['rows']),scalar_payload_explanation='Only source/target paths, byte counts and digests; referenced inputs are not embedded or opened by this audit.')
  elif p.endswith('.jsonl'):
   values=[json.loads(x) for x in text.splitlines()]
   check(len(values)==2 and values[0]['event']=='control_start' and values[1]['event']=='control_end',p+':closed_transport_only')
   a,b=values;name=Path(a['entrypoint']).name
   check(name in sources and a['entrypoint_sha256']==sources[name][0],p+':entrypoint_matches_reviewed_source')
   check(a['bundle_manifest_sha256']==BUNDLE and a['frozen_files']==173 and b['source173_and_entrypoint_unchanged'] is True and b['returncode']==0,p+':completed_pinned_transport')
   check(a['command']==['/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python','-B',str(R/a['entrypoint'])],p+':command_contains_no_payload_arguments')
   check(all(not isinstance(v,(dict,list)) for k,v in a.items() if k!='command') and all(not isinstance(v,(dict,list)) for v in b.values()),p+':process_metadata_only')
   detail.update(entrypoint=a['entrypoint'],entrypoint_sha256=a['entrypoint_sha256'],returncode=0)
  else:
   tree=ast.parse(text)
   check(not any(isinstance(n,ast.Constant) and isinstance(n.value,(bytes,float)) for n in ast.walk(tree)),p+':no_embedded_binary_or_float_observation_values')
   check(max([len(n.value) for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)] or [0])<512,p+':bounded_source_constants')
   detail.update(semantic_review='Complete source read: copies pinned private audit packages and helper source, hashes bytes, records source/target metadata and state-unchanged receipt. No embedded final initial states, weight tensors, test data, policy execution or GPU submission. Source is inspected only, not executed.')
  details.append(detail)
 check(sha(index_file.read_bytes())==index_before,'git_index_bytes_unchanged')
 check(git('ls-files','--stage','-z')==entries_raw and git('diff','--cached','--name-only','-z')==names_raw,'entire_index_entries_and_staged_names_unchanged')
 check(sha((R/'results/experiment_supervisor/state.json').read_bytes())==state_before,'state_bytes_unchanged_under_shared_lock')
 check(sha((R/GUARD).read_bytes())==GPIN,'original_guard_bytes_unchanged')
 snapshot=dict(head=head,index_file_sha256=index_before,index_entries_sha256=sha(entries_raw),staged_names_sha256=sha(names_raw),staged_count=len(names),staged_paths=names,state_sha256=state_before,metadata_file_count=len(selected))
 save('staged_snapshot.json',snapshot)
 save('content_review.json',{'status':'all_13_inspected_text_metadata_or_source','files':details,'referenced_payloads_opened':False,'synthetic_48_blob_archive_reaudited':False})
 report={'schema':'formal_main_v2','status':'approved_bounded_lossless_metadata_archive','scope':'Only these exact 13 newly staged text metadata/source files; no blanket exemption for sealed/test paths.','files':all_files,'file_count':len(all_files),'total_original_bytes':sum(x['bytes'] for x in all_files),'findings':{'source_files':6,'transport_logs':3,'copy_manifest_receipts':4,'all_index_status_A':True,'all_staged_bytes_equal_server_originals':True,'no_final_initial_state_values_in_reviewed_files':True,'no_weight_payload_in_reviewed_files':True,'no_test_data_in_reviewed_files':True,'path_component_sealed_refers_to_immutable_audit_package_delivery':True},'approved_operation_conditions':['Bind this audit SHA and require current 731 staged-name set and all 13 original blob SHA/bytes and status A to match before mutating index.','Do not rerun v3 or the archived source helpers. Keep all 13 server originals at their existing paths and byte-identical.','Archive only the 13 exact files under their original canonical R-relative paths. No absolute paths, path aliases, duplicates, links, traversal or extra members. Read back each regular member and verify original bytes, SHA256 and size.','Remove only these 13 added entries from the Git index; preserve all other staged evidence. No source deletion, state change or guard modification.','Keep original git_required_files.json as failure history. Build separate final required list that retains all other required entries and binds archive, per-member manifest and audit evidence.','Use archive, manifest and delivery filenames that the unchanged lexical guard accepts; no weakening, renamed payload claims or unchecked expansion.','Run the original pinned stage guard against the final exact index including frozen173 checks; archive validation does not waive those checks.'],'risks_and_limits':['Approval describes the concrete 13 text files, not all payloads referenced in their manifests. Existing payload reviews remain authoritative.','Archived original paths cease to be directly indexed Git files; reproducibility requires committed archive plus exact-member manifest and retained server originals.','The original stage guard cannot independently inspect arbitrary tar members; root must retain exact member readback proof. Any differing input, new member, non-A status or missing required evidence must stop delivery.'],'original_guard':{'path':GUARD,'sha256':GPIN},'snapshot':{'path':str((D/'staged_snapshot.json').relative_to(R)),'sha256':sha((D/'staged_snapshot.json').read_bytes())},'read_only_boundaries':{'index_unchanged':True,'state_unchanged':True,'canonical_files_written':False,'Slurm_writes':0,'GPU_jobs':0,'original_source_helpers_executed':False},'utc':datetime.now(timezone.utc).isoformat()}
 save('audit.json',report)
 save('checks.json',{'status':'passed','check_count':len(checks),'checks':checks})
print(json.dumps({'audit':str((D/'audit.json').relative_to(R)),'sha256':sha((D/'audit.json').read_bytes()),'files':13,'bytes':report['total_original_bytes'],'checks':len(checks)}))
