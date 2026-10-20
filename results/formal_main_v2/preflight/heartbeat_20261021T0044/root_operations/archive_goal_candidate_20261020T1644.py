from pathlib import Path
import gzip,hashlib,importlib.util,io,json,sys,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');S=R/'.local/goal_prefix58_candidate_20261020T1644';B='results/formal_main_v2/preflight/heartbeat_20261021T0044';D='results/formal_main_v2/engineering/supervision_delivery_20261020T1644/Goal_prefix58_candidate'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,b):
 assert p.is_relative_to(R) and not any(z.is_symlink() for z in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b)
def enc(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+chr(10)).encode()
m=S/'delivery_manifest.json';assert h(m)=='9a2f425a7d6e715c6a108a400bd1a92fe713e2b368bdc3a2ab2e0e3a4da76595';data=json.loads(m.read_bytes());rows=data['files'];assert len(rows)==192
paths={}
for x in rows:
 p=S/x['path'];assert not Path(x['path']).is_absolute() and '..' not in Path(x['path']).parts and p.is_relative_to(S) and not any(z.is_symlink() for z in [p,*p.parents]);assert h(p)==x['sha256'] and p.stat().st_size==x['bytes'];paths[x['path']]=p
assert len(paths)==len(rows) and set(paths.values())|{m}=={p for p in S.rglob('*') if p.is_file()}
blobs={k:p for k,p in paths.items() if p.suffix=='.bin'};assert len(blobs)==138 and sum(p.stat().st_size for p in blobs.values())==3864
for n,p in blobs.items():assert n.startswith('cpu_') and '/blobs/' in n and p.stem==h(p) and p.stat().st_size<=36
handoff=json.loads((S/'handoff_summary.json').read_bytes());assert handoff['new_GPU_jobs']==0 and handoff['CPU_checks_passed']==handoff['CPU_checks_total']==212 and not handoff['real_GPU_runner_implemented'] and not handoff['independent_code_audit_completed']
cpath=R/'scripts/ops/formal_autonomous_training_v1/controller.py';assert h(cpath)=='acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363';sp=importlib.util.spec_from_file_location('GoalCandidateArchive1644',cpath);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/'results/experiment_supervisor/.writer.lock'):
 state=R/'results/experiment_supervisor/state.json';before=h(state);copies=[]
 for n,p in {**paths,'delivery_manifest.json':m}.items():
  if n in blobs:continue
  assert p.suffix in ('.py','.json','.jsonl','.md','.txt') and p.stat().st_size<100*(1<<20)
  dst=R/D/n;put(dst,p.read_bytes());copies.append(dict(source=ref(p),archive=ref(dst)))
 buf=io.BytesIO()
 with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0,filename='') as gz:
  with tarfile.open(fileobj=gz,mode='w') as tar:
   for n,p in sorted(blobs.items()):
    raw=p.read_bytes();t=tarfile.TarInfo(n);t.size=len(raw);t.mode=0o644;t.mtime=0;t.uid=t.gid=0;t.uname=t.gname='';tar.addfile(t,io.BytesIO(raw))
 target=R/D/'CPU_fixture_blobs.tar.gz';put(target,buf.getvalue());verified=[]
 with tarfile.open(target,'r:gz') as tar:
  members=tar.getmembers();assert {x.name for x in members}==set(blobs) and len(members)==len(blobs)
  for x in members:
   assert x.isfile() and x.name in blobs;raw=tar.extractfile(x).read();assert raw==blobs[x.name].read_bytes() and hashlib.sha256(raw).hexdigest()==h(blobs[x.name]);verified.append(dict(member=x.name,source=ref(blobs[x.name]),bytes=x.size))
 archive_index=dict(status='lossless_CPU_fixture_blobs_verified',archive=ref(target),members=verified,model_or_checkpoint_bytes=False,synthetic_CPU_fixture_only=True,restore='Extract CPU_fixture_blobs.tar.gz within this directory; exact member paths and SHA values are registered. No original input or source bytes changed.')
 put(R/D/'CPU_fixture_archive_index.json',enc(archive_index));assert h(state)==before
 out=R/B/'Goal_prefix58_candidate_delivery.json';put(out,enc(dict(schema='formal_main_v2',status='complete_CPU_candidate_archived_text_and_lossless_tiny_fixtures',source_manifest=ref(m),copies=copies,binary_archive=ref(target),binary_member_count=len(verified),binary_original_bytes=3864,all192_files_plus_manifest_preserved=True,CPU_checks=212,independent_code_audit=False,real_GPU_runner_implemented=False,new_GPU_jobs=0,new_trials=0,Goal_original200_HOLD=True,all_new_Goal_scientific_HOLD=True,state_unchanged=True)))
 print(json.dumps(dict(receipt=ref(out),text_files=len(copies),binary_members=len(verified),archive=ref(target),new_GPU=0)),flush=True)
