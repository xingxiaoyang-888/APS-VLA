from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import hashlib,json,zipfile,tarfile,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
V=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/venv/lib/python3.11/site-packages')
B=R/'results/formal_main_v2/preflight/heartbeat_20261020T1832'
cutoff=datetime(2026,10,17,tzinfo=timezone.utc).timestamp()
def h(p):
 m=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*(1<<20)),b''):m.update(b)
 return m.hexdigest()
def hb(b):return hashlib.sha256(b).hexdigest()
def stamp(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def exact(p,expected,kind):
 assert p.is_file() and not p.is_symlink() and p.resolve()==p
 before=p.stat();a=h(p);after=p.stat()
 assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),p
 assert a==expected,p
 return dict(path=str(p),sha256=a,bytes=after.st_size,mtime_ns=after.st_mtime_ns,ctime_ns=after.st_ctime_ns,mtime_utc=stamp(after.st_mtime),ctime_utc=stamp(after.st_ctime),
  inode=after.st_ino,device=after.st_dev,regular_no_symlink=True,current_bytes_equal_distribution=True,ctime_before_old_six_jobs=after.st_ctime<cutoff,kind=kind)
rows=[];packages=[];start=time.monotonic();cpu=time.process_time()
transfer=R/'configs/assets/libero_wheels_transfer.json';assert h(transfer)=='bfd7901791c5858e405188cfc1e917fdd3db73a277a2468dd94b8d620ec0cb23'
pins=json.loads(transfer.read_bytes())['files']
for package in ['robosuite','mujoco']:
 item=next(x for x in pins if x['path'].startswith(package+'-') and x['path'].endswith('.whl'))
 wheel=P/'external/wheels-libero'/item['path'];assert h(wheel)==item['sha256'] and wheel.stat().st_size==item['size']
 with zipfile.ZipFile(wheel) as z:
  names=[n for n in z.namelist() if n.startswith(package+'/') and not n.endswith('/')]
  assert names and all('..' not in PurePosixPath(n).parts for n in names)
  for name in names:rows.append(exact(V/name,hb(z.read(name)),package+'_wheel_member'))
 actual={p.relative_to(V).as_posix() for p in (V/package).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 extras=sorted(actual-set(names))
 packages.append(dict(package=package,wheel_path=str(wheel),wheel_sha256=item['sha256'],compared_files=len(names),extras_not_in_wheel=extras))
 assert not extras,(package,extras)
 assert not (V/package/'macros_private.py').exists()
archive=P/'external/libero-8f1084e.tar';assert h(archive)=='e0a261753ce056649da67f4c71938391a8d7c55a3eae53e4c17a5d79649da55c'
with tarfile.open(archive) as t:
 suffix='libero/libero/envs/env_wrapper.py'
 anchor=[m for m in t.getmembers() if m.isfile() and m.name.endswith(suffix)];assert len(anchor)==1
 prefix=anchor[0].name[:-len(suffix)]
 members=[m for m in t.getmembers() if m.isfile() and m.name.startswith(prefix+'libero/libero/') and PurePosixPath(m.name).suffix in {'.py','.json','.xml','.bddl'}]
 for member in members:
  rel=PurePosixPath(member.name).relative_to(prefix or '.')
  assert '..' not in rel.parts and not rel.is_absolute() and 'init_files' not in rel.parts
  with t.extractfile(member) as f:data=f.read()
  rows.append(exact(P/'external/LIBERO'/str(rel),hb(data),'LIBERO_source_config_task_asset'))
late=[v for v in rows if not v['ctime_before_old_six_jobs']]
result=dict(schema='formal_main_v2',kind='root_historical_runtime_source_inode_chain',utc=datetime.now(timezone.utc).isoformat(),
 status='source_chain_supports_no_intervening_file_rewrite' if not late else 'identity_chain_requires_review',cutoff_utc=stamp(cutoff),
 old_jobs=['3016981','3017161','3017959','3018505','3019176','3019954'],packages=packages,
 LIBERO_source_config_task_asset_files=len(members),files=rows,late_ctime_files=late,
 assumptions=['Ordinary Linux inode ctime semantics; no assumption of privileged metadata forgery.',
 'Interpret together with old per-job import paths, exact frozen factory and registered config; metadata alone is not historical controller-instance capture.'],
 no_historical_instance_capture_claim=True,no_new_RNG_dump_requirement=True,final_initial_state_values_read=False,
 hash_only_LIBERO_archive=True,only_extract_code_config_XML_BDDL=True,package_files_not_copied_or_modified=True,
 no_environment_constructed=True,no_GPU_calls=True,no_state_or_registry_mutation=True,
 CPU_wall_seconds=time.monotonic()-start,CPU_process_seconds=time.process_time()-cpu)
out=B/'root_runtime_inode_evidence.json'
with out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(dict(status=result['status'],files=len(rows),packages=packages,LIBERO_files=len(members),late_files=len(late),receipt=str(out.relative_to(R)),sha256=h(out),CPU_wall_seconds=result['CPU_wall_seconds'])),flush=True)
