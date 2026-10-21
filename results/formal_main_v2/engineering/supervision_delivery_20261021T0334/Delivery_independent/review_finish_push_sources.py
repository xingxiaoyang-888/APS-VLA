from pathlib import Path
from datetime import datetime,timezone
import ast,difflib,hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/delivery_independent_20261021T0334/final'
files={
'.local/finish_delivery_20261021T0334.py':'3f21f06b7337ac1546705d625fee070c1bb31a69a0fd3777931c16a704a5b6db',
'.local/finish_delivery_20261021T0334_v2.py':'c77938fedc0f73c1e46ce0fd72f3701a3119ce128ab8615de951e3eb458f70c8',
'.local/push_delivery_20261021T0334.py':'8dc5ce27b5641810a4b447cd2e457b7a754979e56c6e4464ed2ae4a11c6e9545',
'scripts/ops/server_github_sync.py':'218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729',
'scripts/ops/check_nonweight_archive_stage.py':'ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6'}
checks=[]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ck(name,b):
 assert b,name
 checks.append(dict(name=name,passed=True))
def save(name,value):
 with (D/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
for n,pin in files.items():ck('exact_source:'+n,h(R/n)==pin);ast.parse((R/n).read_text())
old=(R/'.local/finish_delivery_20261021T0334.py').read_text();new=(R/'.local/finish_delivery_20261021T0334_v2.py').read_text()
expected=old.replace('/stage_precheck_review.json','/independent_stage_precheck.json').replace("for n in [Path(__file__).relative_to(R).as_posix(),push]:","for n in ['.local/finish_delivery_20261021T0334.py',Path(__file__).relative_to(R).as_posix(),push]:")
ck('finish_v2_only_actual_precheck_filename_and_preserved_v1',new==expected)
ck('finish_shared_lock_HEAD_state_summary_index_guards',all(x in new for x in ["with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):", "assert git('rev-parse','HEAD').stdout.decode().strip()==BASE","assert h(R/STATE)==STATE_SHA and h(R/B/'final_summary.json')==SUMMARY_SHA","assert h(R/'.git/index')==audit['index_sha256']","assert ref(old)==audit['required_files']"]))
ck('finish_actual_independent_reviews_required',all(x in new for x in ["audit['status']=='passed_actual_delivery'","pre['status']=='passed_git_stage_precheck'","not audit['blockers']","not pre['blockers']"]))
ck('required_v1_exact_no_duplicate_and_index_bytes',all(x in new for x in ["assert n not in rows and ref(n)==x and git('show',':'+n).stdout==(R/n).read_bytes();rows[n]=x","assert len(rows)==len({n.casefold() for n in rows}) and required not in rows"]))
ck('exact_package_manifest_member_SHA_bytes_and_path',all(x in new for x in ["v=rd(private+'/delivery_manifest.json',pin)","'..' not in Path(n).parts","h(R/src)==x['sha256']","(R/src).stat().st_size==x['bytes']<100*(1<<20)","guard.lexical(dst)"]))
ck('new_publication_exclusive_and_no_symlinks',"not q.exists()" in new and "p.resolve()==p and q.resolve()==q" in new and "q.open('xb')" in new)
ck('stage_trace_must_completed_unchanged',all(x in new for x in ["events[-1]['event']=='control_end'","events[-1]['returncode']==0","events[-1]['source173_and_entrypoint_unchanged']"]))
ck('finish_exact_manifest_additions_lexical_no_force',all(x in new for x in ["guard.lexical(n);rows[n]=ref(n)","assert git('check-ignore','-q','--',n,check=False).returncode==1","git('add','--',n)"]) and "git('add','-f'" not in new)
ck('finish_preserves_original_archive_and173_guard',all(x in new for x in ["checked=guard.check(R,SNAP,SSHA,raw,required)","checked['frozen_files_verified_in_worktree_and_index']==173","git('diff','--cached','--check')"]))
ck('finish_last_exact_expected_set_and_bytes',all(x in new for x in ["assert staged==expected","for n in staged:assert git('show',':'+n).stdout==(R/n).read_bytes()"]))
ck('finish_scope_commit_only_no_push_slurm',['sbatch','scontrol','sacct','squeue','git(\'push'].count(new)==0 if False else not any(x in new for x in ['sbatch','scontrol','sacct','squeue',"git('push"]))
push=(R/'.local/push_delivery_20261021T0334.py').read_text();sync=(R/'scripts/ops/server_github_sync.py').read_text()
ck('push_exact_state_summary_HEAD_emptyindex_and_lock',all(x in push for x in ["with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):",'54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d','35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02',"==a.expected_head","assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)"]))
ck('push_stdin_ephemeral_auth_and_exact_helper',all(x in push for x in ["auth=sys.stdin.buffer.read()","input=auth,capture_output=True","del auth,value","218bf59be0f28ed145a38ed4196cf02b5a6134fcf8a4531abf127f838cc5f729"]))
ck('push_result_exact_remote_match_not_future_claim',all(x in push for x in ["result['remote_head_after']==result['local_head']==a.expected_head","result['credentials_persisted'] is False","q.open('xb')"]))
ck('sync_exact_authorized_GitHub_repository_and_memory_auth',all(x in sync for x in ["URL='https://github.com/xingxiaoyang-888/DIWA.git'","remote','get-url','origin'","value=json.load(sys.stdin)","GIT_CONFIG_KEY_1='credential.helper',GIT_CONFIG_VALUE_1=''","GIT_TERMINAL_PROMPT='0'"]))
ck('sync_nonforce_ancestry_and_remote_after_verified',all(x in sync for x in ["merge-base','--is-ancestor',before,local","run(['push','--porcelain','origin','HEAD:refs/heads/main'])","after=run(['ls-remote','origin','refs/heads/main'])","if args.operation=='push':assert after==local"]) and "'--force'" not in sync and "'-f'" not in sync)
ck('sync_error_redacts_secret_and_disables_trace',all(x in sync for x in ["for secret in (value['password'],auth)","k.startswith(('GIT_TRACE','GCM_TRACE','GIT_CONFIG_'))","k!='GIT_CURL_VERBOSE'"]))
# These are source checks only: do not execute either production entry.
record=dict(schema='formal_main_v2',kind='bounded_finish_and_push_source_review',status='passed_source_review_only',blockers=[],reviewed_by='independent',sources=[dict(path=n,sha256=pin,bytes=(R/n).stat().st_size) for n,pin in files.items()],check_count=len(checks),checks=checks,scope='Read exact sources and bounded v1-v2 diff. Finish may append only frozen audit packages and exact operational evidence after actual index audit; original guard and 173 checks repeat before commit. Push uses stdin memory auth, non-force ancestry and remote HEAD verification. No production entry executed by this audit.',future_commit_or_push_verified=False,credentials_read=False,Git_writes=False,state_writes=False,Slurm_queries=0,GPU_submissions=0,utc=datetime.now(timezone.utc).isoformat())
save('finish_push_source_review.json',record)
save('audit_reader_correction.json',dict(original_source=dict(path='.local/delivery_independent_20261021T0334/final/audit_actual_integration.py',sha256='514ca0443e2940c19616a586333375565f3cc0e36eff012f799791db193307da'),executed_source=dict(path='.local/delivery_independent_20261021T0334/final/audit_actual_integration_v2.py',sha256='53129416ab44e7a25490ffa8368d35a7e8b0bce1d212f5485f65c14d19b3d57d'),reason='Unexecuted v1 audit helper attempted JSON decoding for a Python typed-bridge source; v2 uses the same exact ref SHA/bytes check without decoding. Production bytes and scientific state were untouched.',original_executed=False,production_changes=False))
print(json.dumps(dict(status=record['status'],checks=len(checks),sha256=h(D/'finish_push_source_review.json'))))
