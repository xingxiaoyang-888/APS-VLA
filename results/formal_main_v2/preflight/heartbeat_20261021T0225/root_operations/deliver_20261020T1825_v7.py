from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,re,subprocess,sys,tarfile,io
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261021T0225';E='results/formal_main_v2/engineering/supervision_delivery_20261020T1825';BASELINE='ad2dea8105531fbd46b3013b234dc92806cdf213'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json';SNAP_SHA='1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509'
AUDIT='.local/git_metadata_audit_20261020T1825/audit.json'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def cp(src,dst):
 p=R/dst;p.parent.mkdir(parents=True,exist_ok=True);raw=(R/src).read_bytes()
 if p.exists():assert p.read_bytes()==raw
 else:p.open('xb').write(raw)
def git(*args,check=True):return subprocess.run(['git','-c','core.quotepath=false',*args],cwd=R,capture_output=True,check=check)
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument('--audit-sha256',required=True);args=ap.parse_args();assert re.fullmatch('[a-f0-9]{64}',args.audit_sha256)
c=module('scripts/ops/formal_autonomous_training_v1/controller.py','acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363','deliveryv4ctl')
guard=module('scripts/ops/check_nonweight_archive_stage.py','ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6','deliveryv4guard')
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 assert git('rev-parse','HEAD').stdout.decode().strip()==BASELINE
 s=rd('results/experiment_supervisor/state.json');f=s['formal_main_progress'];assert f['root_and_independent_completed_arms']==72 and f['root_and_independent_reviewed_arm_updates']==360000 and f['current_action_development_trial_count']==5400 and f['completed_development_trials']==6612 and f['completed_final_trials']==0 and f['test_opened'] is False and f['global_release_created'] is False
 assert s['pending_submission'] is None and s['autonomous_training_v1']['reserved_GPU_slots']==0 and s['autonomous_training_v1']['root_submission_hold'] is None
 last=s['last_root_supervision_snapshot'];assert last['path']==B+'/final_summary.json' and h(R/last['path'])==last['sha256'];summary=rd(last['path']);assert summary['compatible_development_trials']==6000
 previous=rd(B+'/git_required_files.json');selected={v['path'] for v in previous['files']}|{B+'/git_required_files.json'}
 for row in previous['files']:assert ref(row['path'])==row
 raw=git('diff','--cached','--name-status','-z').stdout.decode().split(chr(0));staged={raw[i+1]:raw[i] for i in range(0,len(raw)-1,2)};assert len(staged)==731 and set(staged)<=selected
 failures={}
 for n,status in staged.items():
  try:guard.lexical(n)
  except guard.StageError as ex:
   assert str(ex)=='Sealed/test directory forbidden' and status=='A' and 'sealed' in n
   assert git('cat-file','-e','HEAD:'+n,check=False).returncode!=0
   failures[n]=ref(n)
 assert len(failures)==13 and h(R/AUDIT)==args.audit_sha256
 audit=rd(AUDIT);assert audit['status']=='approved_bounded_lossless_metadata_archive'
 assert {v['path']:{k:v[k] for k in ['path','sha256','bytes']} for v in audit['files']}==failures
 assert hashlib.sha256(git('diff','--cached','--name-only','-z').stdout).hexdigest()==audit['staged_name_sha256']
 assert len(audit['staged_names'])==len(staged) and set(audit['staged_names'])==set(staged)
 for n in failures:assert git('show',':'+n).stdout==(R/n).read_bytes()
 archive=B+'/operational_audit_metadata_lossless.tar.gz';assert not (R/archive).exists()
 with tarfile.open(R/archive,'w:gz') as tf:
  for n in sorted(failures):
   raw=(R/n).read_bytes();item=tarfile.TarInfo(n);item.size=len(raw);item.mtime=0;item.mode=0o644;tf.addfile(item,io.BytesIO(raw))
 with tarfile.open(R/archive,'r:gz') as tf:
  members=tf.getmembers();assert len(members)==13 and {m.name for m in members}==set(failures) and all(m.isfile() for m in members)
  for m in members:
   raw=tf.extractfile(m).read();assert len(raw)==failures[m.name]['bytes'] and hashlib.sha256(raw).hexdigest()==failures[m.name]['sha256'] and raw==(R/m.name).read_bytes()
 audit_base='.local/git_metadata_audit_20261020T1825/';manifest_rel=audit_base+'delivery_manifest.json';assert h(R/manifest_rel)=='faac80350fcd97fb56df61f839ba18f8a087b274c4c2081e78c1f080993ca547'
 audit_manifest=rd(manifest_rel);assert audit_manifest['file_count']==8 and len(audit_manifest['files'])==8
 for row in audit_manifest['files']:
  assert row['source']==audit_base+row['path'] and '/' not in row['path'] and ref(row['source'])=={'path':row['source'],'sha256':row['sha256'],'bytes':row['bytes']}
  dst=E+'/Git_metadata_independent/'+row['path'];guard.lexical(dst);cp(row['source'],dst);selected.add(dst)
 manifest_dst=E+'/Git_metadata_independent/delivery_manifest_original.json';cp(manifest_rel,manifest_dst);selected.add(manifest_dst);audit_dst=E+'/Git_metadata_independent/audit.json'
 save(B+'/git_operational_metadata_archive.json',{'status':'independently_classified_operational_metadata_losslessly_archived','files':list(failures.values()),'archive':ref(archive),'independent_audit':ref(audit_dst),'original_paths_are_tar_member_names':True,'all_members_read_back_verified':13,'original_files_retained_on_server':True,'sealed_final_state_values_included':False,'pinned_index_guard_unchanged':True,'failed_attempt_retained':'results/formal_main_v2/control_transport/deliver_turn_20261020T1825_v3.jsonl'})
 # Only the thirteen audited, newly-added index entries are removed; no working-tree data is deleted.
 git('--literal-pathspecs','rm','--cached','--',*sorted(failures));selected-=set(failures);selected.update([archive,B+'/git_operational_metadata_archive.json'])
 closed=[];opened=[];root_sources=[]
 for raw in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if not raw:continue
  n=raw[3:]
  if not n.startswith('results/formal_main_v2/control_transport/') or n in failures:continue
  rows=[json.loads(x) for x in (R/n).read_bytes().splitlines()];assert rows[0]['event']=='control_start'
  if rows[-1]['event']!='control_end':opened.append(n);continue
  closed.append(n);selected.add(n);rel=rows[0].get('entrypoint','')
  if len(Path(rel).parts)==2 and Path(rel).parts[0]=='.local' and 'sealed' not in rel:
   assert h(R/rel)==rows[0]['entrypoint_sha256'];dst=B+'/root_operations/'+Path(rel).name;cp(rel,dst);root_sources.append({'source':rel,'archive':ref(dst)});selected.add(dst)
 for rel in ['.local/deliver_20261020T1825_v7.py','.local/github_push_20261020T1825.py']:
  dst=B+'/root_operations/'+Path(rel).name;cp(rel,dst);selected.add(dst);root_sources.append({'source':rel,'archive':ref(dst)})
 save(B+'/root_operation_sources_v7.json',{'status':'exact_sources_preserved','sources':root_sources,'closed_transports':[ref(n) for n in closed],'open_transports_excluded':opened,'operational_metadata_archive':ref(B+'/git_operational_metadata_archive.json')});selected.add(B+'/root_operation_sources_v7.json')
 for n in selected:
  guard.lexical(n);p=R/n;assert p.is_file() and p.resolve()==p and p.stat().st_size<100*(1<<20) and not any(x.is_symlink() for x in [p,*p.parents])
 fixture_names={x['path'] for x in rd(B+'/git_CPU_fixture_archive.json')['files']};assert len(fixture_names)==48
 unselected=[]
 for raw in git('status','--porcelain=v1','--untracked-files=all','-z').stdout.decode().split(chr(0)):
  if raw and raw[3:] not in selected:unselected.append(raw[3:])
 assert set(unselected)<=set(opened)|set(failures)|fixture_names,unselected
 selected=sorted(selected)
 for i in range(0,len(selected),60):git('add','-f','--',*selected[i:i+60])
 required=B+'/git_required_files_v7.json';save(required,{'schema':'cti_nonweight_archive_stage_v1','kind':'required_files','files':[ref(n) for n in selected]});git('add','--',required)
 RAW=[x['path'] for x in rd(SNAP)['files']];assert len(RAW)==9
 v=guard.check(R,SNAP,SNAP_SHA,RAW,required);assert v['status']=='verified_index_archive_delivery' and v['frozen_files_verified_in_worktree_and_index']==173
 save(B+'/git_index_guard.json',v)
 diag=git('diff','--cached','--check',check=False);assert not diag.stderr;exceptions=[]
 if diag.returncode:
  for line in diag.stdout.decode().splitlines():
   if not re.match(r'^.*?:[0-9]+: ',line):continue
   m=re.fullmatch(r'(.*?):[0-9]+: (trailing whitespace|new blank line at EOF)\.',line);assert m,line;n=m.group(1);assert n.startswith((E+'/',B+'/root_operations/')),n;exceptions.append(n)
  assert exceptions
 exceptions=sorted(set(exceptions));save(B+'/git_whitespace_diagnostic.json',{'returncode':diag.returncode,'stdout':diag.stdout.decode(),'exact_archived_source_whitespace_preserved':exceptions})
 git('diff','--cached','--check','--','.',*[':(exclude)'+n for n in exceptions])
 save(B+'/git_delivery.json',{'schema':'formal_main_v2','status':'exact_index_and173_frozen_verified','baseline':BASELINE,'source_frozen_files':173,'root_complete':72,'compatible_development_trials':6000,'new_development_accepted':200,'new_GPU_jobs':summary['new_GPU_jobs'],'final_sealed':True,'weights_added':False,'all_project_writes_server_only':True,'open_transports_excluded':opened,'index_guard':ref(B+'/git_index_guard.json'),'summary':last,'metadata_archive':ref(B+'/git_operational_metadata_archive.json'),'required_files':ref(required),'utc':datetime.now(timezone.utc).isoformat()})
 for n in ['git_index_guard.json','git_whitespace_diagnostic.json','git_delivery.json']:git('add','--',B+'/'+n);assert git('show',':'+B+'/'+n).stdout==(R/B/n).read_bytes()
 count=len(git('diff','--cached','--name-only').stdout.decode().splitlines());result=git('commit','-m','Record complete training, Object development, and bounded Goal and collection jobs');head=git('rev-parse','HEAD').stdout.decode().strip()
 save('.local/git_commit_20261020T1825.json',{'commit':head,'baseline':BASELINE,'files':count,'root_complete':72,'index_guard':'passed','final_sealed':True});print(json.dumps({'status':'committed_not_yet_pushed','commit':head,'files':count,'summary':result.stdout.decode().splitlines()[:2]}))
