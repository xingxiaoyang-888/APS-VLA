from pathlib import Path
import hashlib, json, importlib.util, sys, subprocess, time
from datetime import datetime, timezone
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/Spatial64seed23_terminal_1032'
t0=time.perf_counter();c0=time.process_time()
PULL='results/formal_main_v2/pulls/20261020T113838Z_c5823055f27a/receipt.json'
PULL_SHA='a39164a76e708535cdf6cb02cd549e6c83c65ebfe76e7392012a64fa00ca9b01'
SNAP='results/formal_main_v2/nonweight_archives/v1/snapshots/Spatial64seed23_20261020_1032.json'
SNAP_SHA='46d99a0368858d1301310a890380873331a65f3f21ac4011605b00b41c06d9c4'
INPUTS='results/formal_main_v2/preflight/heartbeat_20261020T1832/Spatial3044479_archive_inputs.json'
INPUTS_SHA='2c7031f0ada3649873a56207395a834895b2976d6323b156693f497525ff13a2'
REVIEW_SHA='cc04fd98fd39a2159ca32775167f262efcdd528ad3bb4945c4998d025fe7f554'
CODEC='scripts/ops/nonweight_archive.py'
CODEC_SHA='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
def ref(p):
 p=Path(p);h=hashlib.sha256();n=0
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b);n+=len(b)
 return dict(path=p.relative_to(R).as_posix(),bytes=n,sha256=h.hexdigest())
def read(rel,sha):
 p=R/rel; rr=ref(p);assert rr['sha256']==sha,(rel,rr)
 return json.loads(p.read_text()),rr
pull,pullref=read(PULL,PULL_SHA);inputs,inputref=read(INPUTS,INPUTS_SHA)
review,reviewref=read('.local/Spatial64seed23_terminal_1032/independent_review.json',REVIEW_SHA)
assert review['status']=='passed_complete_training_only' and review['archive_reconstruction'] is None
assert ref(R/CODEC)['sha256']==CODEC_SHA
spec=importlib.util.spec_from_file_location('exact_nonweight_codec_spatial3044479',R/CODEC)
codec=importlib.util.module_from_spec(spec);sys.modules[spec.name]=codec;spec.loader.exec_module(codec)
v,evidence,objects,chunks=codec.verified_plan(R,SNAP,SNAP_SHA)
assert inputs['snapshot']==ref(R/SNAP) and inputs['pull']==pullref
rawrefs=[{k:x[k] for k in ('path','bytes','sha256')} for x in v['files']]
assert sorted(rawrefs,key=lambda x:x['path'])==sorted(inputs['raw'],key=lambda x:x['path'])
assert len(rawrefs)==3 and sum(x['bytes'] for x in rawrefs)==156929174
assert pull['requested_job_ids']==['3024716','3025205','3028522','3043399','3044479']
assert len(pull['files'])==65 and pull['status']=='verified_nonweight_snapshot'
assert not pull['weights_copied'] and not pull['sealed_initial_states_copied']
pullrefs={x['relative']:dict(path=x['relative'],bytes=x['bytes'],sha256=x['sha256']) for x in pull['files']}
assert len(pullrefs)==65
class CompareSink:
 def __init__(self,f):self.f=f;self.h=hashlib.sha256();self.n=0
 def write(self,b):
  assert self.f.read(len(b))==b,'decoded block differs from retained raw original'
  self.h.update(b);self.n+=len(b)
  return len(b)
new=[]
for row in v['files']:
 rr={k:row[k] for k in ('path','bytes','sha256')}
 assert pullrefs[row['path']]==rr and ref(R/row['path'])==rr
 with (R/row['path']).open('rb') as f:
  sink=CompareSink(f)
  obj=codec.verify_object(R,row['manifest'],row['sha256'],row['bytes'],sink=sink)
  assert f.read(1)==b'' and sink.n==row['bytes'] and sink.h.hexdigest()==row['sha256']
 with (R/row['path']).open('rb') as f:first=json.loads(f.readline())
 assert str(first['job_id'])=='3044479'
 new.append(dict(**rr,manifest=row['manifest'],chunks=len(obj['chunks']),first_event=first['event'],job_id='3044479',decoded_stream_matches_original_byte_for_byte=True))
# Git reference uses an immutable commit: no live HEAD-to-index assumptions.
def git(*args):
 return subprocess.run(['git','--no-optional-locks','-C',str(R),*args],capture_output=True,check=True).stdout
commit=git('rev-parse','HEAD').decode().strip()
streams={p:x for p,x in pullrefs.items() if Path(p).suffix in ('.jsonl','.out','.err')}
assert len(streams)==22
newpaths={r['path'] for r in new}
stdoutpaths={'results/slurm/cti-formal_3044479.out','results/slurm/cti-formal_3044479.err'}
historicalpaths=set(streams)-newpaths-stdoutpaths
assert len(historicalpaths)==17
assert sum(Path(p).suffix=='.jsonl' for p in historicalpaths)==9
assert sum(Path(p).suffix in ('.out','.err') for p in historicalpaths)==8
listing=git('ls-tree','-r','-z',commit,'--',*sorted(historicalpaths))
entries={b.split(b'\t',1)[1].decode():b.split(b'\t',1)[0].decode().split() for b in listing.split(b'\0') if b}
assert set(entries)==historicalpaths
old=[]
for path in sorted(historicalpaths):
 rr=streams[path];assert ref(R/path)==rr
 mode,kind,oid=entries[path];assert kind=='blob' and mode=='100644'
 b=git('cat-file','blob',oid)
 assert len(b)==rr['bytes'] and hashlib.sha256(b).hexdigest()==rr['sha256']
 old.append(dict(**rr,Git_commit=commit,Git_blob=oid,classification='historical_raw_Git_blob_exact'))
newstdout=[]
for path in sorted(stdoutpaths):
 rr=streams[path];assert ref(R/path)==rr
 newstdout.append(dict(**rr,classification='new_stdout_stderr_original_for_root_Git_delivery',Git_delivery_verified=False))
# Confirm all 65 pulled nonweight files have stayed fixed, including train/validation diagnostics.
for rr in pullrefs.values():assert ref(R/rr['path'])==rr
assert ref(D/'independent_review.json')['sha256']==REVIEW_SHA
assert ref(R/CODEC)['sha256']==CODEC_SHA
report=dict(schema='formal_main_v2',kind='independent_terminal_archive_delivery_review',status='passed_archive_reconstruction_and_historical_raw_Git_identity',job_id='3044479',reviewed_utc=datetime.now(timezone.utc).isoformat(),independent_training_review=reviewref,pull=pullref,root_archive_inputs=inputref,archive_snapshot=ref(R/SNAP),codec=ref(R/CODEC),archive_evidence=[x[0] for x in evidence.values()],new_archived_raw=new,new_archived_raw_bytes=156929174,historical_raw_Git_identity=old,historical_Git_jsonl_count=9,historical_Git_stdout_stderr_count=8,new_stdout_stderr_originals=newstdout,all65_pull_bytes_rechecked=True,all22_raw_streams_classified=True,archive_reconstruction_method='Pinned original codec verifies full object/chunk graph; independent sink compares every decoded byte with retained original and recomputes whole SHA256/length. No files restored.',GPU_seconds=0,CPU_wall_seconds=time.perf_counter()-t0,CPU_process_seconds=time.process_time()-c0,production_writes=False,Git_writes=False,checkpoint_read_or_deserialized=False,scientific_result_added=False,final_release_authorized=False,limitations=['Root still delivers two current stdout/stderr originals and new nonweight metadata through Git. This review does not assert the pending push has occurred.','Passed independent training review remains byte-identical; optimizer/RNG tensors were not independently deserialized.'])
p=D/'archive_delivery_independent.json'
with p.open('x') as f:json.dump(report,f,indent=2,sort_keys=True,ensure_ascii=False);f.write('\n')
print(json.dumps(dict(status=report['status'],report=ref(p),new_raw_bytes=156929174,historical_Git_raw_count=len(old),new_stdout_count=len(newstdout),CPU_wall_seconds=report['CPU_wall_seconds'])))
