from pathlib import Path
import json,hashlib,io,tarfile,datetime
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=Path(__file__).parent;C=R/'.local/goal_prefix58_repair_20261020T1825/revision01'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=p.relative_to(D).as_posix(),sha256=h(p),bytes=p.stat().st_size)
def put(p,o):
 assert not p.exists(),str(p)
 p.write_text(json.dumps(o,sort_keys=True,indent=2,ensure_ascii=False)+'\n')
for name,pin in [('ast_observer_v2.py','e88222ea96c290019b2ec838ff68fe25a9f94d115ae996d92735e18e4cf0800e'),('observer_v3.py','7a33c4ec531e0524a5e30b51e18205dc7d354868afa6190e3f39dcf14b283241'),('source_manifest.json','44b4aef4e80053f6b9567a2aca954853b116f30f4cf2c5c072a97d1b6dadb3aa')]:
 p=C/name;assert h(p)==pin;q=D/'reviewed_candidate'/name;q.parent.mkdir(exist_ok=True);assert not q.exists();q.write_bytes(p.read_bytes())
for name in ['ast_observer_v2.py.diff','observer_v3.py.diff']:
 q=D/'reviewed_candidate'/name;assert not q.exists();q.write_bytes((C/name).read_bytes())
blobs=sorted(p for p in D.rglob('*') if p.is_file() and 'blobs' in p.relative_to(D).parts)
assert blobs and all(p.suffix in ('.bin','.json') and p.relative_to(D).parts[0] in ('attempt01','attempt02') for p in blobs)
rows=[ref(p) for p in blobs];out=D/'synthetic_CPU_blobs_lossless.tar.gz';assert not out.exists()
with tarfile.open(out,'w:gz') as t:
 for p,r in zip(blobs,rows):
  b=p.read_bytes();i=tarfile.TarInfo(r['path']);i.size=len(b);i.mtime=0;i.uid=i.gid=0;i.mode=0o644;t.addfile(i,io.BytesIO(b))
expected={r['path']:r for r in rows};observed=[]
with tarfile.open(out,'r:gz') as t:
 for m in t:
  assert m.isfile() and m.name in expected;observed.append(m.name);b=t.extractfile(m).read();r=expected[m.name]
  assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
assert len(observed)==len(expected) and set(observed)==set(expected)
put(D/'synthetic_CPU_blobs_member_manifest.json',dict(schema='independent_synthetic_CPU_lossless_archive',archive=ref(out),members=rows,member_count=len(rows),restored_in_memory_all_sha256_verified=True,real_model_weights_or_checkpoints=False))
trans=[]
for suffix,rc in [('v1',1),('v2',0)]:
 name='goal_prefix58_independent_20261020T1825_cpu_'+suffix+'.jsonl';p=R/'results/formal_main_v2/control_transport'/name;rows2=[json.loads(x) for x in p.read_text().splitlines() if x.strip()];assert rows2[-1]['event']=='control_end' and rows2[-1]['returncode']==rc and rows2[-1]['source173_and_entrypoint_unchanged']
 q=D/'closed_transport'/name;q.parent.mkdir(exist_ok=True);assert not q.exists();q.write_bytes(p.read_bytes());trans.append(dict(original=p.relative_to(R).as_posix(),copy=ref(q),exit_code=rc))
put(D/'CPU_handoff.json',dict(status='independently_passed_three_bounded_repairs_CPU_only',review=ref(D/'attempt02/independent_review.json'),passed=494,negative_count=77,full58_original_trial_episode_CPU_trace_and_rng_equal=True,failed_harness=ref(D/'attempt01/failure.json'),failed_harness_reason='Private source recorder assumed every input was under R; accepted action adapter is at P. v2 records explicit R/P root and reruns all checks; candidate source never changed.',sources=[ref(p) for p in sorted((D/'reviewed_candidate').iterdir())],transport=trans,blob_archive=ref(out),blob_members=ref(D/'synthetic_CPU_blobs_member_manifest.json'),direct_blob_members_excluded_from_Git_delivery=True,outer_review_pending=True,actual_GPU_run=False,original200_and_new_Goal_science_HOLD=True,no_final_values_read=True))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and 'blobs' not in p.relative_to(D).parts and p.name not in ('CPU_delivery_manifest.json','delivery_manifest.json')]
put(D/'CPU_delivery_manifest.json',dict(status='sealed_CPU_component_only_outer_pending',files=files,file_count=len(files),blob_archive=ref(out),blob_member_manifest=ref(D/'synthetic_CPU_blobs_member_manifest.json'),all_synthetic_blob_bytes_preserved_losslessly=True,sealing_transport_external='results/formal_main_v2/control_transport/goal_prefix58_independent_20261020T1825_package_CPU_v1.jsonl'))
print(json.dumps(dict(manifest=ref(D/'CPU_delivery_manifest.json'),handoff=ref(D/'CPU_handoff.json'),files=len(files),blobs=len(blobs),archive_bytes=out.stat().st_size)))
