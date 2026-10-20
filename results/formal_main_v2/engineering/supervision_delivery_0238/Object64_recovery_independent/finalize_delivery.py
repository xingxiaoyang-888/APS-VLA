from pathlib import Path
import json,hashlib,tarfile
from datetime import datetime,timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/object64_recovery_independent_0238'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def ref(p):
 return {'path':p.relative_to(R).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def put(name,obj):
 p=D/name
 data=(json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
 with p.open('xb') as f:f.write(data)
 return ref(p)
reviewp=D/'independent_review.json'
assert sha(reviewp)=='25c78029fa2b5456ea07cf596e518356f96f5acba252b6fe4ef6bc1a5e7b97b0'
j=json.loads(reviewp.read_bytes()); refs=j['read_evidence_sha256']
assert j['status']=='passed_original_target_recovery_only' and j['historical_failure_preserved'] is True
assert j['cost']['all_pair_allocated_GPU_seconds']==5210
am=R/'results/formal_main_v2/engineering/cuda_startup_evidence_1808/archive_manifest.json'
assert sha(am)=='fc0910d97775c96d5d2fccbbba21b1efed873756dd83e818bb5c9b59f0d29060'
archive_manifest=json.loads(am.read_bytes())
ap=R/archive_manifest['archive']
assert sha(ap)==archive_manifest['sha256']=='c4e8b1227fc06633d0277bbe30e3b001d7c41682075989d2336ff5ab4de4b143'
canonical={};aliases=[];tarwanted={}
def add(p):
 r=ref(p); old=canonical.setdefault(r['path'],r); assert old==r
for rel,h in sorted(refs.items()):
 p=R/rel
 assert p.is_file() and sha(p)==h,rel
 if rel.startswith(D.relative_to(R).as_posix()+'/'):continue
 if not rel.startswith('.local/'):
  add(p);continue
 if rel.startswith('.local/cuda_recovery_autonomous_1940/'):
  dest=R/'results/formal_main_v2/engineering/cuda_recovery_autonomous_1940'/Path(rel).name
 elif '/inputs/' in rel and not rel.split('/inputs/',1)[1].startswith('.local/'):
  dest=R/rel.split('/inputs/',1)[1]
 else:dest=None
 if dest is not None and dest.is_file() and sha(dest)==h:
  assert dest.stat().st_size==p.stat().st_size
  add(dest);aliases.append({'original_path':rel,'sha256':h,'bytes':p.stat().st_size,'restoration':'copy_exact_existing_canonical_bytes_to_original_relative_path','canonical':ref(dest)})
 else:
  item=archive_manifest['files'].get(rel)
  assert item and item['sha256']==h and item['bytes']==p.stat().st_size,rel
  tarwanted[rel]=item
with tarfile.open(ap,'r:gz') as tf:
 names={}
 for m in tf.getmembers():
  if m.name in tarwanted:
   assert m.name not in names and m.isfile() and not m.issym() and not m.islnk(),m.name
   names[m.name]=m
 assert set(names)==set(tarwanted)
 for rel,item in sorted(tarwanted.items()):
  m=names[rel];h=hashlib.sha256();n=0
  f=tf.extractfile(m);assert f is not None
  with f:
   for b in iter(lambda:f.read(1048576),b''):n+=len(b);h.update(b)
  assert n==m.size==item['bytes'] and h.hexdigest()==item['sha256'],rel
  aliases.append({'original_path':rel,'sha256':item['sha256'],'bytes':n,
                  'restoration':'exact_tar_member_to_original_relative_path_without_content_change',
                  'archive':ref(ap),'archive_manifest':ref(am),'member':rel})
add(am);add(ap)
extra=[
 'results/formal_main_v2/engineering/terminal_delivery_0943/independent/audit_3039258_v2.py',
 'results/formal_main_v2/preflight/heartbeat_20261020T1038/3044017_root_terminal.json',
 'scripts/ops/server_control_transport_v1/run_server_control.py',
 'scripts/ops/server_control_transport_v1/bundle_manifest.json',
 'results/formal_main_v2/control_transport/object64_recovery_independent_0238_a1.jsonl']
for rel in extra:
 p=R/rel
 if rel.endswith('bundle_manifest.json') and not p.is_file():
  raise AssertionError('Expected pinned transport manifest path missing; inspect exact CLI before packaging')
 add(p)
assert len(aliases)==213,(len(aliases),len(tarwanted))
er=put('existing_evidence_refs.json',{
 'schema':'formal_main_v2','kind':'independent_recovery_existing_evidence_closure','job_id':3044017,
 'review':ref(reviewp),'all_original_R_read_refs_rehashed':True,'original_R_read_ref_count':len(refs),
 'original_read_evidence_sha256':refs,'existing_canonical_files':list(sorted(canonical.values(),key=lambda x:x['path'])),
 'exact_historical_path_restorations':sorted(aliases,key=lambda x:x['original_path']),
 'server_read_evidence_sha256':j['server_read_evidence_sha256'],
 'server_ref_count':len(j['server_read_evidence_sha256']),
 'no_archive_members_extracted':True,'private_dependency_copies_created':False,
 'historical_receipts_rewritten':False,'checkpoint_or_weight_bytes_in_delivery':False,
 'scope':'Historical paths remain unchanged in the signed raw review. Canonical exact-byte sources and seven validated tar members reconstruct those paths; original raw data and server-only model/checkpoint bytes are not recopied.'})
readme='''Object64 seed23 / 3044017 independent original-target recovery audit

Status: passed_original_target_recovery_only.
The failed 3028468 allocation remains FAILED with 69 GPU seconds. The successful
3044017 allocation contributes 5141 GPU seconds; total 5210. Both arms reached
500 updates from a fresh initialized run, each with 4000 actual uses / 4000 unique
windows / cursor 4000. resumed_from_existing_checkpoint is false: the old CUDA
startup failure produced no checkpoint or arm initialization.

The checker independently rebuilt full fixed 40000 sample order, same A/B
initialization, update and microbatch records, original 5000-step schedule,
validation at 0 and 500 over all 204 windows, task-equal teacher metrics,
hard64 (32 tokens per view), candidate selection, commit and cache journals,
all 25 pull files, source173 in R/S, Object-only metadata compatibility and its
own GPU acceptance provenance. Actual server hashes cover both resume files,
four partial candidates, and official Object150000 components. No checkpoint
tensor was deserialized; the optimizer/RNG payload itself was not loaded.

This is not completion of the 5000-step pair, not a new training or GPU test,
and not authorization for continuous5000, a new submission, or final evaluation.
The original next ordinary boundary is 1000. A separately audited root admission
may authorize a different execution target without changing these historical facts.

execution_a1.json contains the exact pinned server transport invocation.
The checker completed once with exit0 in about9.2 seconds. preparation_a1_failure
preserves the earlier generator insertion-needle assertion, before any checker
execution; prepare_a2.py changed only that generator's exact whitespace match.
No shared state/Git/production files or scientific source were modified.

existing_evidence_refs.json is the complete read closure. Historical private paths
are mapped to already-existing exact canonical bytes or validated members in the
existing CUDA failure archive; none are silently rewritten in the original review.
The server model/checkpoint hashes are references only. delivery_files.json lists
all new private files and itself is delivered separately by its external SHA.
'''
with (D/'README.txt').open('xb') as f:f.write(readme.encode())
verification={'schema':'formal_main_v2','kind':'independent_audit_delivery_verification','utc':datetime.now(timezone.utc).isoformat(),
 'review':ref(reviewp),'closure':er,'read_ref_count':len(refs),'server_hash_ref_count':len(j['server_read_evidence_sha256']),
 'canonical_dependency_count':len(canonical),'historical_alias_count':len(aliases),
 'validated_tar_member_count':len(tarwanted),'original_review_unchanged':True,
 'all_current_R_raw_read_refs_match_review':True,'GPU_jobs_submitted':0,'production_state_or_Git_writes':False,
 'limitations':['Server checkpoint/model bytes were streamed only for SHA; no tensor load.',
 'Passed scope is original500 target recovery only.','No fresh Slurm query or model execution performed for this audit.']}
put('packaging_verification.json',verification)
files=[ref(p) for p in sorted(D.iterdir()) if p.is_file() and p.name!='delivery_files.json']
assert not [p for p in D.iterdir() if not p.is_file()]
manifest={'schema':'formal_main_v2','kind':'independent_original_target_recovery_delivery','job_id':3044017,
 'status':'complete','review':ref(reviewp),'existing_evidence_refs':er,
 'include_manifest_itself':True,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'files':files,
 'no_canonical_large_files_copied':True,'no_private_fixture_dependencies_missing':True,
 'scope':'Only own server audit source, preserved generator failure, raw execution logs, review and exact-byte restoration map. No state/Git/Slurm or scientific source change.'}
mr=put('delivery_files.json',manifest)
print(json.dumps({'review':ref(reviewp),'delivery':mr,'closure':er,'new_files_excluding_manifest':len(files),'new_bytes_excluding_manifest':manifest['total_bytes'],'canonical_dependencies':len(canonical),'historical_aliases':len(aliases),'tar_members':len(tarwanted)},ensure_ascii=False))
