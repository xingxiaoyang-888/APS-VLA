from pathlib import Path
import hashlib,io,json,tarfile
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent
SELF_LOG='results/formal_main_v2/control_transport/goal_prefix58_independent_20261020T1825_package_final_v1.jsonl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(D).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,sort_keys=True,indent=2);f.write(chr(10))
assert sha(D/'CPU_delivery_manifest.json')=='a9482103a6b226588a86061680db0ce3b8f37bc285fbb2ef245371d425a175bc'
prior=json.loads((D/'CPU_delivery_manifest.json').read_bytes())
for x in prior['files']:p=D/x['path'];assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes']
fixtures=sorted(p for prefix in ['dispatch_v3_attempt01','dispatch_v3_attempt02'] for p in (D/prefix/'fixtures').rglob('*') if p.is_file());rows=[ref(p) for p in fixtures];archive=D/'synthetic_dispatch_fixtures_lossless.tar.gz'
with tarfile.open(archive,'x:gz') as t:
 for p,row in zip(fixtures,rows):
  b=p.read_bytes();info=tarfile.TarInfo(row['path']);info.size=len(b);info.mtime=0;info.uid=info.gid=0;info.mode=0o644;t.addfile(info,io.BytesIO(b))
expected={x['path']:x for x in rows};seen=set()
with tarfile.open(archive,'r:gz') as t:
 for member in t:
  assert member.isfile() and member.name in expected and member.name not in seen;seen.add(member.name);b=t.extractfile(member).read();r=expected[member.name];assert hashlib.sha256(b).hexdigest()==r['sha256'] and len(b)==r['bytes']
assert seen==set(expected)
put(D/'synthetic_dispatch_member_manifest.json',dict(kind='independent_synthetic_dispatch_lossless_archive',archive=ref(archive),members=rows,member_count=len(rows),restored_in_memory_all_sha256_verified=True,real_model_weights_or_checkpoints=False,synthetic_only=True))
logs=[]
for p in sorted((R/'results/formal_main_v2/control_transport').glob('goal_prefix58_independent_20261020T1825_*.jsonl')):
 if p.relative_to(R).as_posix()==SELF_LOG:continue
 lines=[json.loads(x) for x in p.read_text().splitlines() if x.strip()];assert lines[-1]['event']=='control_end' and lines[-1]['source173_and_entrypoint_unchanged'],str(p)
 q=D/'closed_transport'/p.name;q.parent.mkdir(exist_ok=True)
 if q.exists():assert q.read_bytes()==p.read_bytes()
 else:q.write_bytes(p.read_bytes())
 logs.append(dict(original=p.relative_to(R).as_posix(),copy=ref(q),returncode=lines[-1]['returncode']))
put(D/'handoff.json',dict(status='CPU_and_published_metadata_independently_passed_single_root_dispatch_only',repair_CPU=ref(D/'attempt02/independent_review.json'),outer_CPU=ref(D/'outer_attempt01/independent_review.json'),independent_readiness=ref(D/'outer_attempt01/independent_readiness.json'),blocked_dispatch_v1=ref(D/'dispatch_v1_blocked/independent_review.json'),dispatch_v3=ref(D/'dispatch_v3_attempt02/independent_review.json'),post_publication=ref(D/'post_publication/independent_review.json'),checks=dict(repair=494,repair_negative=77,outer=141,outer_negative=112,dispatch=190,dispatch_cases=34),all_failed_attempts_and_old_sources_retained=True,failed_mock_reason='First dispatcher fixture relocated ORIGINAL to a different path than the original configuration; exact original guard rejected before submit. Only private fixture path was corrected; full rerun passed.',archive=ref(archive),archive_members=ref(D/'synthetic_dispatch_member_manifest.json'),closed_transport=logs,maximum_GPU_jobs=1,maximum_wall_seconds=1800,real_Slurm_operations=0,real_GPU_acceptance=False,scientific_release=False,original200_and_new_Goal_science_HOLD=True,post_execution_audit_not_claimed=True,sealing_transport_external=SELF_LOG))
exclude={x['path'] for x in rows}
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.relative_to(D).as_posix() not in exclude and 'blobs' not in p.relative_to(D).parts and p.name!='delivery_manifest.json']
assert all(x['bytes']<100*1024*1024 for x in files)
put(D/'delivery_manifest.json',dict(status='sealed_complete_independent_CPU_and_publication_review',files=files,file_count=len(files),all_nonweight_bytes_preserved=True,synthetic_dispatch_archive=ref(archive),synthetic_dispatch_members=ref(D/'synthetic_dispatch_member_manifest.json'),synthetic_CPU_archive=ref(D/'synthetic_CPU_blobs_lossless.tar.gz'),synthetic_CPU_members=ref(D/'synthetic_CPU_blobs_member_manifest.json'),excluded_direct_synthetic_fixtures=len(rows),sealing_transport_external=SELF_LOG))
print(json.dumps(dict(manifest=ref(D/'delivery_manifest.json'),handoff=ref(D/'handoff.json'),files=len(files),synthetic_fixture_files=len(rows),archive_bytes=archive.stat().st_size)))
