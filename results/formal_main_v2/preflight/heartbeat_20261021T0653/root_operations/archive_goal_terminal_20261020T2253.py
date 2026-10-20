from pathlib import Path
import hashlib,json,fcntl,tarfile,gzip,io,os
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');P=Path('/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA')
B='results/formal_main_v2/preflight/heartbeat_20261021T0653';BASE='results/formal_main_v2/engineering/goal_paired_input_gate_20261020T2156';Q=P/BASE/'attempt01'
def sha(b):return hashlib.sha256(b).hexdigest()
def checked(p,h):
 assert p.is_file() and not p.is_symlink()
 b=p.read_bytes();assert sha(b)==h,(str(p),h);return b
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:
  with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def emit(p,d):put(p,(json.dumps(d,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
rv=json.loads(checked(R/B/'Goal_terminal_root_review.json','612766294af9462d0c21edbdcb177433a0cd1f2897b1d613ab9eb674f43bbb19'))
assert rv['status']=='root_engineering_terminal_verified_pending_independent'
with (R/'results/experiment_supervisor/.writer.lock').open('a+b') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 before=(R/'results/experiment_supervisor/state.json').read_bytes();assert sha(before)=='63c74e7e591283409a792a7597fdb9bf99d1936ff1311e123bd687a83237a51f'
 metadata=[]
 for x in rv['metadata_allowlist']:
  source=Path(x['source']);assert source.is_relative_to(P)
  rel=x['relative'];assert not Path(rel).is_absolute() and '..' not in Path(rel).parts
  data=checked(source,x['sha256']);assert len(data)==x['bytes'];dest=R/BASE/rel;put(dest,data)
  metadata.append({**x,'destination':dest.relative_to(R).as_posix()})
 allrefs=rv['blob_allowlist'];assert len(allrefs)==10741 and sum(x['bytes'] for x in allrefs)==474068525
 groups=[];group=[];size=0
 for x in allrefs:
  if group and size+x['bytes']>32*1024*1024:groups.append(group);group=[];size=0
  group.append(x);size+=x['bytes']
 if group:groups.append(group)
 parts=[]
 for idx,members in enumerate(groups,1):
  rel=f'{BASE}/attempt01/observer/blob_archives/part-{idx:03d}.tar.gz';dest=R/rel;assert not dest.exists()
  dest.parent.mkdir(parents=True,exist_ok=True)
  with dest.open('xb') as raw:
   with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0,compresslevel=6) as z:
    with tarfile.open(fileobj=z,mode='w',format=tarfile.PAX_FORMAT) as t:
     for x in members:
      assert x['path'].startswith('blobs/') and '..' not in Path(x['path']).parts
      data=checked(Q/'observer'/x['path'],x['sha256']);assert len(data)==x['bytes']
      info=tarfile.TarInfo(x['path']);info.size=len(data);info.mode=0o600;info.mtime=0;t.addfile(info,io.BytesIO(data))
   raw.flush();os.fsync(raw.fileno())
  with tarfile.open(dest,'r:gz') as t:
   got=t.getmembers();assert [x.name for x in got]==[x['path'] for x in members]
   for m,x in zip(got,members):assert m.isfile() and m.size==x['bytes'] and sha(t.extractfile(m).read())==x['sha256']
  parts.append({'path':rel,'sha256':sha(dest.read_bytes()),'compressed_bytes':dest.stat().st_size,'uncompressed_member_bytes':sum(x['bytes'] for x in members),'members':members})
 out={'schema':'formal_main_v2','kind':'exact_development_engineering_blob_archive','status':'all_members_verified','job_id':'3054127','root_raw_review':{'path':B+'/Goal_terminal_root_review.json','sha256':'612766294af9462d0c21edbdcb177433a0cd1f2897b1d613ab9eb674f43bbb19'},'metadata':metadata,'parts':parts,'blob_count':len(allrefs),'blob_bytes':sum(x['bytes'] for x in allrefs),'compressed_bytes':sum(x['compressed_bytes'] for x in parts),'weights_or_sealed_values':False,'new_scientific_trials':0,'old200_adopted':False,'new_Goal_science_HOLD':True,'final_release':False}
 emit(R/BASE/'attempt01/observer/blob_archive_manifest.json',out)
 assert (R/'results/experiment_supervisor/state.json').read_bytes()==before
 print(json.dumps({'manifest':BASE+'/attempt01/observer/blob_archive_manifest.json','sha256':sha((R/BASE/'attempt01/observer/blob_archive_manifest.json').read_bytes()),'parts':len(parts),'blobs':out['blob_count'],'compressed_bytes':out['compressed_bytes']}))
