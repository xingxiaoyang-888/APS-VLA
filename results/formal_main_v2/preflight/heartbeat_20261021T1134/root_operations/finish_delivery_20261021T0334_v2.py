from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T1134';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0334'
BASE='328e3b918379a985ef299cee4891138a55874827';STATE='results/experiment_supervisor/state.json';STATE_SHA='54ee7389fe300b4ec553998d91b9bf727ca3231c2066e35a86716559a3c1406d';SUMMARY_SHA='35a12c33d2bf81331e96aad4fe2879ae06fa7269a518fc14933fea8dc65aac02'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SSHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def save(n,v):
 p=R/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write((json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode());return ref(n)
def cp(src,dst):
 p=R/src;q=R/dst;assert p.resolve()==p and q.resolve()==q and not p.is_symlink() and not q.exists();q.parent.mkdir(parents=True,exist_ok=True);q.open('xb').write(p.read_bytes());return ref(dst)
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(n,pin,label):
 p=R/n;assert h(p)==pin;sp=importlib.util.spec_from_file_location(label,p);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
def package(private,pin,dest):
 v=rd(private+'/delivery_manifest.json',pin);added=[];mapping=[];seen=set()
 for x in v['files']:
  n=x['path'];n=Path(n).relative_to(private).as_posix() if n.startswith(private+'/') else n
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and n not in seen;seen.add(n)
  src=private+'/'+n;assert h(R/src)==x['sha256'] and (R/src).stat().st_size==x['bytes']<100*(1<<20)
  dst=dest+'/'+n;guard.lexical(dst);mapping.append(dict(source=src,**cp(src,dst)));added.append(dst)
 n=dest+'/delivery_manifest_original.json';cp(private+'/delivery_manifest.json',n);added.append(n)
 n=dest+'/root_publication_mapping.json';save(n,dict(source_manifest=ref(private+'/delivery_manifest.json'),files=mapping));added.append(n)
 return added
ap=argparse.ArgumentParser();ap.add_argument('--final-manifest-sha256',required=True);ap.add_argument('--final-report-sha256',required=True);ap.add_argument('--stage-precheck-manifest-sha256',required=True);ap.add_argument('--stage-precheck-report-sha256',required=True);a=ap.parse_args()
assert os.environ.get('CTI_SERVER_CONTROL_ROOT')==str(R)
fp='.local/delivery_independent_20261021T0334/final';sp='.local/git_stage_precheck_independent_20261021T0334'
audit=rd(fp+'/final_independent_review.json',a.final_report_sha256);assert audit['status']=='passed_actual_delivery' and not audit['blockers']
assert audit['state_sha256']==STATE_SHA and audit['summary_sha256']==SUMMARY_SHA
pre=rd(sp+'/independent_stage_precheck.json',a.stage_precheck_report_sha256);assert pre['status']=='passed_git_stage_precheck' and not pre['blockers']
ctl=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','finish0334ctl')
guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','finish0334guard')
with ctl.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASE
 assert h(R/STATE)==STATE_SHA and h(R/B/'final_summary.json')==SUMMARY_SHA
 assert h(R/'.git/index')==audit['index_sha256']
 old=B+'/git_required_files_v1.json';assert ref(old)==audit['required_files']
 rows={}
 for x in rd(old)['files']:
  n=x['path'];assert n not in rows and ref(n)==x and git('show',':'+n).stdout==(R/n).read_bytes();rows[n]=x
 added=[old,B+'/git_index_guard_v1.json',B+'/git_whitespace_diagnostic_v1.json']
 added+=package(fp,a.final_manifest_sha256,E+'/Delivery_independent')
 added+=package(sp,a.stage_precheck_manifest_sha256,E+'/Git_stage_precheck')
 push='.local/push_delivery_20261021T0334.py';assert h(R/push)=='8dc5ce27b5641810a4b447cd2e457b7a754979e56c6e4464ed2ae4a11c6e9545'
 for n in ['.local/finish_delivery_20261021T0334.py',Path(__file__).relative_to(R).as_posix(),push]:
  dst=B+'/root_operations/'+Path(n).name;cp(n,dst);added.append(dst)
 trace='results/formal_main_v2/control_transport/stage_delivery_20261021T0334_v4.jsonl'
 events=[json.loads(x) for x in (R/trace).read_bytes().splitlines()]
 assert len(events)==2 and events[-1]['event']=='control_end' and events[-1]['returncode']==0 and events[-1]['source173_and_entrypoint_unchanged']
 added.append(trace)
 extra=B+'/git_delivery_audit_bindings.json'
 save(extra,dict(status='actual_delivery_and_exact_stage_precheck_passed',root_summary=ref(B+'/final_summary.json'),state=ref(STATE),independent_delivery=ref(E+'/Delivery_independent/final_independent_review.json'),stage_precheck=ref(E+'/Git_stage_precheck/independent_stage_precheck.json'),inherited_scientific_audits=[ref(E+'/Object_independent/independent_review.json'),ref(E+'/Goal_independent/independent_terminal_review.json')],scientific_terminal_consumers_not_rerun_by_delivery_audit=True,root_publication_recovery=ref(B+'/root_publication_recovery.json'),real_archive_volumes=24,archive_members=35076,raw_payloads_not_staged=True,new_GPU_submissions=0,final_sealed=True));added.append(extra)
 required=B+'/git_required_files_v2.json'
 for n in added:
  guard.lexical(n);rows[n]=ref(n)
 assert len(rows)==len({n.casefold() for n in rows}) and required not in rows
 save(required,dict(schema='cti_nonweight_archive_stage_v1',kind='required_files',files=[rows[n] for n in sorted(rows)]))
 for n in added+[required]:
  assert git('check-ignore','-q','--',n,check=False).returncode==1
  git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 raw=[x['path'] for x in rd(SNAP)['files']]
 checked=guard.check(R,SNAP,SSHA,raw,required)
 assert checked['status']=='verified_index_archive_delivery' and checked['frozen_files_verified_in_worktree_and_index']==173
 guardname=B+'/git_index_guard_v2.json';save(guardname,checked);git('add','--',guardname)
 git('diff','--cached','--check')
 delivery=B+'/git_delivery_v1.json';save(delivery,dict(status='exact_nonweight_Git_delivery_verified',utc=datetime.now(timezone.utc).isoformat(),baseline=BASE,root_complete_arms=72,accepted_complete_development_trials=7800,new_current_trials=201,new_legacy_rows_into_complete_view=599,unique_initial_states=400,allocated_GPU_seconds=1994468,active_GPUs=0,source_frozen_files=173,exact_Goal_archive_volumes=24,exact_Goal_archive_members=35076,scientific_state_unchanged_since_root_acceptance=True,independent_delivery=ref(E+'/Delivery_independent/final_independent_review.json'),required_files=ref(required),index_guard=ref(guardname),weights_added=False,final_sealed=True,all_project_writes_server_only=True,new_GPU_submissions=0));git('add','--',delivery)
 assert h(R/STATE)==STATE_SHA and h(R/B/'final_summary.json')==SUMMARY_SHA
 expected=set()
 for n in set(rows)|{required,guardname,delivery}:
  prior=git('show',BASE+':'+n,check=False)
  if prior.returncode or prior.stdout!=(R/n).read_bytes():expected.add(n)
 staged=set(git('diff','--cached','--name-only','-z').stdout.decode().strip('\0').split('\0'))
 assert staged==expected
 for n in staged:assert git('show',':'+n).stdout==(R/n).read_bytes()
 result=git('commit','-m','Accept Object linked correction and new Goal200 with exact raw evidence archives')
 head=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_20261021T0334.json',dict(status='committed_not_yet_pushed',commit=head,baseline=BASE,files=len(staged),root_complete=72,complete_development=7800,summary_sha256=SUMMARY_SHA,state_sha256=STATE_SHA,final_sealed=True))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=head,files=len(staged),summary=result.stdout.decode().splitlines()[:2])))
