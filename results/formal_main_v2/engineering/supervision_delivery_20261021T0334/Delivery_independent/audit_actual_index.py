from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,os,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/delivery_independent_20261021T0334/final'
B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
STATE='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d';SUMMARY='35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02'
INDEX='febbc0259aa99fcc2421d108f515de191e9a167a991172af586b0c141989f469';BASE='328e3b918379a985ef299cee4891138a55874827'
required=B+'/git_required_files_v1.json';guardpath=B+'/git_index_guard_v1.json';whitepath=B+'/git_whitespace_diagnostic_v1.json'
pins={
required:'a60bad6f551ca8dc63668feb5f1e9b0c69f05d70b2b20c18826617611f36a38e',
guardpath:'036a365f8ee7f6d3cb387f4f9fce12d98d6fada91e4b576289c5ef429a20bbf8',
whitepath:'83395cbaf5cbebe654f352914cdd7b569643698a8b687ae84b6ea7e5b6f4dd9e',
B+'/git_external_nonweight_allowlist_v1.json':'37e8e138d886778785ecbe9c889c7d191022c650365b8ab082c45183691e904d',
B+'/git_ignored_allowlist_v1.json':'19ef9f43f3da8a788f678faec9118b6c1b3faf6a7879e202eb00776047fff85d'}
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(n,b):
 assert b,n
 checks.append(dict(name=n,passed=True))
def rf(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
def rd(n):return json.loads((R/n).read_bytes())
def module(n,pin,label):
 ck('source:'+n,h(R/n)==pin)
 sp=importlib.util.spec_from_file_location(label,R/n);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
def save(n,v):
 with (D/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write('\n')
ck('physical_index_pinned_before',h(R/'.git/index')==INDEX)
ck('state_summary_pinned_before',h(R/'results/experiment_supervisor/state.json')==STATE and h(R/B/'final_summary.json')==SUMMARY)
for n,pin in pins.items():ck('receipt_pin:'+n,h(R/n)==pin)
aref='.local/delivery_independent_20261021T0334/final/actual_integration_review.json';sref='.local/delivery_independent_20261021T0334/final/finish_push_source_review.json'
ck('actual_integration_inherited_exact',h(R/aref)=='82534256a3c087a3471ea04d5730dd64935016f244e83d57f87434289bfab38a')
ck('finish_push_source_review_exact',h(R/sref)=='e8d79e23019e895a3e2a65874e5866b25b91e2aef74c5b9b6ce994be6396a58c')
a=rd(aref);sr=rd(sref)
ck('prior_integration_scope_passed',a['status']=='passed_actual_integration_pending_index' and not a['blockers'] and a['state_sha256']==STATE and a['summary_sha256']==SUMMARY and a['source173_verified'] and a['final_sealed'])
ck('source_review_passed_only_future_operations',sr['status']=='passed_source_review_only' and not sr['blockers'] and sr['future_commit_or_push_verified'] is False)
guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','actual_delivery_guard')
codec=guard.load_codec()
reqrows=guard.required_value(rd(required),codec);reqmap={x['path']:x for x in reqrows}
ck('234_required_unique_exact_no_self',len(reqrows)==len(reqmap)==234 and len({n.casefold() for n in reqmap})==234 and required not in reqmap)
allow=rd(B+'/git_external_nonweight_allowlist_v1.json');ignored=rd(B+'/git_ignored_allowlist_v1.json');g=rd(guardpath);wh=rd(whitepath)
ck('original_archive_and_173_guard_passed_exact_required',g['status']=='verified_index_archive_delivery' and g['required_files']==rf(required) and g['required_count']==234 and g['frozen_files_verified_in_worktree_and_index']==173 and g['archive_verification']=='verified' and g['restore_verification']=='restored_verified' and g['head']==BASE and g['allowed_raw_deletions']==[] and g['git_write_commands'] is False)
ck('no_cached_whitespace_errors',wh==dict(returncode=0,stdout='',stderr=''))
ck('explicit_26_metadata_24_real_9_CPU_archives_only',len(allow['pulled_nonweight_files'])==26 and len(allow['archived_Goal_real_volumes'])==24 and len(allow['archived_Goal_test_fixtures'])==9 and allow['loose_P_passive_blobs_excluded']==15522 and allow['excluded_passive_payload_types']==dict(binary=15515,RNG_json=7) and allow['R_raw_observation_payloads_only_archived'] and allow['source_goal_observation_blob_count']==19540 and allow['no_weights_or_final_values'])
tarrows=allow['archived_Goal_real_volumes']+allow['archived_Goal_test_fixtures'];tarset={x['path'] for x in tarrows}
for x in allow['pulled_nonweight_files']+tarrows+allow['pull_receipts']:
 ck('explicit_delivery_member:'+x['path'],reqmap.get(x['path'])==x)
for x in tarrows:ck('archive_under_real_size_bound:'+x['path'],x['bytes']<90*(1<<20))
ck('exact_targz_allowlist',tarset=={n for n in reqmap if n.endswith('.tar.gz')} and len(tarset)==33)
ck('all15522_loose_and_R_raw_excluded',not any('/observer/blobs/' in n or '/raw_runtime/' in n or n.endswith('.bin') or n.endswith('.rng.json') for n in reqmap))
ignrows=ignored['files'];ck('33_individually_pinned_ignored_rows',len(ignrows)==len({x['path'] for x in ignrows})==33 and all(reqmap.get(x['path'])==x for x in ignrows))
trace='results/formal_main_v2/control_transport/stage_delivery_20261021T0334_v4.jsonl';events=[json.loads(x) for x in (R/trace).read_bytes().splitlines()]
ck('original_stage_trace_completed_and_guard_unchanged',len(events)==2 and events[-1]['event']=='control_end' and events[-1]['returncode']==0 and events[-1]['source173_and_entrypoint_unchanged'])
allselected=set(reqmap)|{required,guardpath,whitepath}
checked_files=[];frozen_names=[]
with guard.index_reader(R) as index:
 ck('HEAD_unchanged_not_committed',index.before[2].decode()==BASE)
 ck('staged237_exact_required_plus3',len(index.changed)==237 and set(index.changed)==allselected and all(v in ('A','M') for v in index.changed.values()))
 base={}
 for row in index.git('ls-tree','-r','-z',BASE).split(b'\0'):
  if not row:continue
  hdr,rawname=row.split(b'\t',1);mode,kind,oid=hdr.decode().split()
  base[rawname.decode()]=dict(mode=mode,kind=kind,oid=oid)
 expected={n for n in allselected if n not in base or index.entries[n]['oid']!=base[n]['oid'] or index.entries[n]['mode']!=base[n]['mode']}
 ck('all_staged_changes_exact_expected_no_extra',expected==set(index.changed))
 for n in sorted(allselected):
  data,actual=guard.same_local_index(index,n,codec,reqmap.get(n))
  ck('actual_index_bytes:'+n,actual==rf(n))
  checked_files.append(actual)
 frozen_inventory='results/formal_main_v2/source/formal_main_v2_run_564be0995e.json'
 invdata,invref=guard.same_local_index(index,frozen_inventory,codec)
 ck('frozen_inventory_exact',invref['sha256']=='5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926')
 frozen=json.loads(invdata)['files'];ck('173_frozen_count',len(frozen)==173)
 for n,pin in frozen.items():
  data,actual=guard.same_local_index(index,n,codec)
  ck('173_worktree_index_unstaged_exact:'+n,actual['sha256']==pin and n not in index.changed);frozen_names.append(n)
 ck('original_guard_staged_logical_inventory_preserved',len(index.entries)==g['index_files_checked_for_size_and_mode']+2)
 index.unchanged()
 logical_index_sha=hashlib.sha256(index.before[0]).hexdigest()
 staged_sha=hashlib.sha256(index.before[1]).hexdigest()
# Check new downstream note still records the design as a HOLD, without admitting the remaining five.
note=(R/'docs/正式下游阻塞登记_20261021T0334.md').read_text()
ck('new_doc_remaining5_HOLD_and_terminal_counts',all(x in note for x in ['7800','7801','1000','HOLD','35200']) and '5800' not in note)
ck('final_scope_state_and_summary_stable',h(R/'results/experiment_supervisor/state.json')==STATE and h(R/B/'final_summary.json')==SUMMARY and h(R/'.git/index')==INDEX)
save('actual_index_review.json',dict(schema='formal_main_v2',kind='actual_readonly_delivery_index_review',status='passed',blockers=[],state_sha256=STATE,summary_sha256=SUMMARY,index_sha256=INDEX,logical_index_sha256=logical_index_sha,staged_changes_sha256=staged_sha,required_files=rf(required),original_index_guard=rf(guardpath),required_count=234,staged_count=237,checked_files=checked_files,frozen173_count=len(frozen_names),source173_verified=True,original_archive_restore_inherited=True,new_archive_reconstruction=False,new_Slurm_queries=0,Git_writes=False,source_scientific_review_rerun=False,check_count=len(checks),checks=checks,utc=datetime.now(timezone.utc).isoformat()))
r=dict(schema='formal_main_v2',kind='formal_main_v2_actual_delivery_independent_review',status='passed_actual_delivery',blockers=[],reviewed_by='independent',reviewed_by_agent='/root/goal_cpu_gate_2054',state_sha256=STATE,summary_sha256=SUMMARY,required_files=rf(required),index_sha256=INDEX,source173_verified=True,final_sealed=True,actual_integration_review=rf(aref),actual_index_review=rf('.local/delivery_independent_20261021T0334/final/actual_index_review.json'),finish_push_source_review=rf(sref),inherited_scientific_terminal_reviews=a['inherited_scientific_terminal_reviews'],scope='New audit covers actual root acceptance integration, exact state/docs/cost deltas, original scientific evidence bindings, actual Git index bytes and limited finish/push source. Exact original Object/Goal scientific terminal reviews are inherited; Goal runtime was authored by this agent, and its scientific terminal review was independently performed by the named other agent. No scientific terminal consumer rerun is claimed here.',counts=a['counts'],cost=a['cost'],Git=dict(staged_files=237,required_files=234,nonweight_metadata_log_files=26,real_Goal_archive_volumes=24,CPU_fixture_archives=9,loose_P_passive_payloads_excluded=15522,raw_R_observation_payloads_only_archived=19540,all_staged_index_bytes_verified=True,weights_added=False,HEAD_before=BASE,commit_or_push_executed_by_auditor=False,remote_sync_claimed=False),Goal_old200_HOLD=True,Goal_remaining1000_HOLD=True,O2A_released=False,global_release=False,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,Git_writes=False,checks=dict(actual_integration=a['check_count'],bounded_finish_push_source=sr['check_count'],actual_index=len(checks),total=a['check_count']+sr['check_count']+len(checks)),future_commit_or_push_verified=False,utc=datetime.now(timezone.utc).isoformat())
save('final_independent_review.json',r)
print(json.dumps(dict(status=r['status'],report_sha256=h(D/'final_independent_review.json'),index_review_sha256=h(D/'actual_index_review.json'),checks=r['checks'])))
