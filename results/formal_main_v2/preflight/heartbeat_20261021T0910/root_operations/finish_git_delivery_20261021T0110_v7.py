from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,re,subprocess,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
B='results/formal_main_v2/preflight/heartbeat_20261021T0910';E='results/formal_main_v2/engineering/supervision_delivery_20261021T0110'
BASE='98817e8d996e8db750191cccb8b01a7ba81da169'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SSHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
OLD=B+'/git_required_files_v1.json';OLD_SHA='3cb1d212fec9f588b442b955d65d8a2d11228bb4d92cb3bfc747527c7600e919'
TRACE='results/formal_main_v2/control_transport/git_delivery_v6_20261021T0110.jsonl'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def rd(n):return json.loads((R/n).read_bytes())
def save(n,v):
 p=R/n;assert not p.exists(),n;p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write((json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
def cp(src,dst):
 p=R/src;q=R/dst;assert not q.exists() and p.resolve()==p and q.resolve()==q and not any(x.is_symlink() for x in [p,*p.parents,q,*q.parents]);q.parent.mkdir(parents=True,exist_ok=True);q.open('xb').write(p.read_bytes())
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--audit-manifest',required=True);ap.add_argument('--audit-sha256',required=True);a=ap.parse_args()
assert a.audit_manifest=='.local/delivery_duplicate_independent_20261021T0110/delivery_manifest.json' and h(R/a.audit_manifest)==a.audit_sha256
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','gitresume_ctl')
guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','gitresume_guard')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASE
 assert h(R/'.git/index')=='c3c21b95e148b8e7b94381a5518fda2a9845d8451a13f80c864c9c61e2361e3c'
 assert h(R/'results/experiment_supervisor/state.json')=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 assert h(R/B/'final_summary.json')=='6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2'
 assert h(R/OLD)==OLD_SHA and git('show',':'+OLD).stdout==(R/OLD).read_bytes()
 value=rd(OLD);assert value['schema']=='cti_nonweight_archive_stage_v1' and value['kind']=='required_files' and len(value['files'])==633
 rows={};duplicates=[]
 for row in value['files']:
  n=row['path'];assert set(row)=={'path','sha256','bytes'} and ref(n)==row and git('show',':'+n).stdout==(R/n).read_bytes()
  if n in rows:assert rows[n]==row;duplicates.append(row)
  else:rows[n]=row
 assert len(rows)==632 and len({n.casefold() for n in rows})==632
 assert duplicates==[ref(B+'/git_ignored_allowlist_v1.json')]
 staged=set(git('diff','--cached','--name-only','-z').stdout.decode().strip('\0').split('\0'))
 expected=set()
 for n in rows:
  prior=git('show',BASE+':'+n,check=False)
  if prior.returncode or prior.stdout!=(R/n).read_bytes():expected.add(n)
 assert staged==expected|{OLD} and len(staged)==629
 assert h(R/TRACE)=='99e0f2781411a71a7e3e674a8978df42792c121f27251efe967daf503790f8f3'
 events=[json.loads(x) for x in (R/TRACE).read_bytes().splitlines()];assert events[0]['event']=='control_start' and events[-1]['event']=='control_end'
 final_audit=E+'/Delivery_independent/actual_review_v2.json'
 assert h(R/final_audit)=='69434136678f7ce1549de4e5b10c37d5272276263ab75e9ba06effb3debe7d8a'
 manifest=rd(a.audit_manifest);members=manifest['files'];assert isinstance(members,list) and 1<=len(members)<=8
 parent=Path(a.audit_manifest).parent;dest=E+'/Delivery_duplicate_independent'
 added=[OLD,TRACE]
 report=None
 for row in members:
  assert set(row)>={'path','sha256','bytes'}
  n=row['path'];assert Path(n).name==n and Path(n).suffix in {'.py','.json','.md'} and row['bytes']<10*(1<<20)
  src=(parent/n).as_posix();assert ref(src)==dict(path=src,sha256=row['sha256'],bytes=row['bytes'])
  if n=='independent_review.json':report=rd(src)
  dst=dest+'/'+n;guard.lexical(dst);cp(src,dst);added.append(dst)
 assert report is not None and report['status']=='passed_bounded_duplicate_list_correction'
 assert report['entrypoint_sha256']==h(Path(__file__)) and report['original_required_sha256']==OLD_SHA
 mtarget=dest+'/delivery_manifest_original.json';cp(a.audit_manifest,mtarget);added.append(mtarget)
 selfpath=Path(__file__).relative_to(R).as_posix();target=B+'/root_operations/'+Path(__file__).name;cp(selfpath,target);added.append(target)
 recovery=B+'/git_duplicate_list_correction.json'
 save(recovery,dict(status='exact_duplicate_metadata_row_removed_no_file_omitted',original_required=ref(OLD),duplicate_rows=duplicates,unique_paths_preserved=632,windows_case_aliases=0,staged_paths_before=629,original_failure_trace=ref(TRACE),independent_review=ref(dest+'/independent_review.json'),entrypoint=ref(target),scientific_state_unchanged=True,source173_guard_unchanged=True,new_GPU_submissions=0))
 added.append(recovery)
 required=B+'/git_required_files_v2.json';newrows={**rows,**{n:ref(n) for n in added}}
 save(required,{'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':[newrows[n] for n in sorted(newrows)]})
 for n in added+[required]:guard.lexical(n);git('add','--',n);assert git('show',':'+n).stdout==(R/n).read_bytes()
 raw=[x['path'] for x in rd(SNAP)['files']];assert len(raw)==9
 checked=guard.check(R,SNAP,SSHA,raw,required);assert checked['status']=='verified_index_archive_delivery' and checked['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard_v1.json',checked)
 diag=git('diff','--cached','--check',check=False);assert not diag.stderr;exceptions=[]
 allowed={E+'/Goal_full200_dispatch/README.md',E+'/Goal_full200_dispatch_v2/README.md'}
 if diag.returncode:
  for line in diag.stdout.decode().splitlines():
   if not re.match(r'^.*?:[0-9]+: ',line):continue
   match=re.fullmatch(r'(.*?):[0-9]+: trailing whitespace\.',line);assert match and match.group(1) in allowed,line;exceptions.append(match.group(1))
  assert set(exceptions)==allowed
 exceptions=sorted(set(exceptions))
 save(B+'/git_whitespace_diagnostic_v1.json',dict(returncode=diag.returncode,stdout=diag.stdout.decode(),exact_archived_source_whitespace_preserved=exceptions))
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 summary=rd(B+'/final_summary.json')
 save(B+'/git_delivery_v1.json',dict(schema='formal_main_v2',status='exact_index_and173_frozen_verified',baseline=BASE,source_frozen_files=173,root_complete=72,compatible_development_trials=7000,new_development_accepted=588,new_GPU_jobs=summary['new_GPU_jobs'],accepted_fixed_observations=90,independent_delivery_audit=ref(final_audit),final_sealed=True,weights_added=False,all_project_writes_server_only=True,prospective_Goal_raw_runtime_scope_deferred_to_exact_terminal_archive='results/formal_main_v2/raw_runtime/goal_full200_20261021T0110/attempt01',original_pre_guard_required_list_preserved=ref(OLD),duplicate_list_correction=ref(recovery),operational_snapshot_mapping=ref(B+'/operational_snapshot_filename_mapping.json'),index_guard=ref(B+'/git_index_guard_v1.json'),summary=ref(B+'/final_summary.json'),required_files=ref(required),utc=datetime.now(timezone.utc).isoformat()))
 for name in ['git_index_guard_v1.json','git_whitespace_diagnostic_v1.json','git_delivery_v1.json']:
  git('add','--',B+'/'+name);assert git('show',':'+B+'/'+name).stdout==(R/B/name).read_bytes()
 assert h(R/'results/experiment_supervisor/state.json')=='bd3df44300cf38e719a3387dc2de1ed8ffdf268e7a4fb792160c17c48b9632aa'
 assert h(R/B/'final_summary.json')=='6b7da6a87eada2d6c63ec0b0c357156953edd5132c7407d809755556719388a2'
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines())
 result=git('commit','-m','Accept Spatial588 and dispatch exact Object correction with audited Goal gates')
 head=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_20261021T0110.json',dict(commit=head,baseline=BASE,files=count,root_complete=72,index_guard='passed',final_sealed=True))
 print(json.dumps(dict(status='committed_not_yet_pushed',commit=head,files=count,summary=result.stdout.decode().splitlines()[:2])))
