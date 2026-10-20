from pathlib import Path
import json,hashlib,subprocess,time
from collections import Counter
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/Spatial64seed23_terminal_1032'
t0=time.perf_counter(); c0=time.process_time()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def ref(p):return dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size)
def git(*args):return subprocess.run(['git','--no-optional-locks','-C',str(R),*args],capture_output=True,check=True).stdout
assert sha(D/'independent_review.json')=='cc04fd98fd39a2159ca32775167f262efcdd528ad3bb4945c4998d025fe7f554'
assert sha(D/'archive_delivery_independent.json')=='ec63f0943664bbccbed865d40d440b0c72da3c2e33cbfdd3d704c847193de082'
report=json.loads((D/'independent_review.json').read_text());archive=json.loads((D/'archive_delivery_independent.json').read_text())
assert report['status']=='passed_complete_training_only' and report['completed_by_arm']=={'A':5000,'B':5000} and report['new_reviewed_arm_updates']==7000 and report['final_release_authorized'] is False
assert archive['status']=='passed_archive_reconstruction_and_historical_raw_Git_identity'
pr=R/archive['pull']['path'];assert ref(pr)==archive['pull']
pull=json.loads(pr.read_text()); assert len(pull['files'])==65
head=git('rev-parse','HEAD').decode().strip()
names=[x['relative'] for x in pull['files']]
listing=git('ls-tree','-r','-z',head,'--',*names)
entries={b.split(b'\t',1)[1].decode():b.split(b'\t',1)[0].decode().split() for b in listing.split(b'\0') if b}
archived={x['path']:x for x in archive['new_archived_raw']}
oldraw={x['path'] for x in archive['historical_raw_Git_identity']}
rows=[]
for item in sorted(pull['files'],key=lambda x:x['relative']):
 p=item['relative'];rr=dict(path=p,bytes=item['bytes'],sha256=item['sha256']);assert ref(R/p)==rr
 entry=entries.get(p); previous=None
 if entry:
  mode,kind,oid=entry;assert kind=='blob' and mode=='100644'
  blob=git('cat-file','blob',oid)
  previous=dict(blob=oid,bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest())
  exact=previous['bytes']==rr['bytes'] and previous['sha256']==rr['sha256']
 else:exact=False
 if p in archived:category='new_lossless_archive_verified';method=dict(snapshot=archive['archive_snapshot'],manifest=archived[p]['manifest'])
 elif exact:category='existing_Git_blob_exact';method=dict(commit=head,blob=previous['blob'])
 elif previous:category='updated_nonweight_pending_root_Git';method=dict(prior_Git=previous)
 else:category='new_nonweight_pending_root_Git';method={}
 if p in oldraw:assert exact
 rows.append(dict(**rr,pull_kind=item['kind'],category=category,delivery=method))
assert len(rows)==65 and len({r['path'] for r in rows})==65
counts=dict(Counter(x['category'] for x in rows))
classification=dict(schema='formal_main_v2',kind='independent65_file_delivery_classification',status='passed_fixed_bytes_classified',pull=ref(pr),Git_commit=head,files=rows,counts=counts,archive_reconstruction=ref(D/'archive_delivery_independent.json'),pending_Git_is_not_claimed_delivered=True,CPU_wall_seconds=time.perf_counter()-t0,CPU_process_seconds=time.process_time()-c0,GPU_seconds=0,Git_writes=False,state_writes=False)
cp=D/'pull65_delivery_classification.json'
with cp.open('x') as f:json.dump(classification,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
notes=dict(kind='preexecution_inspection_note',scope='readonly Python source escaping inspection',outcome='A cautious replace/assert diagnostic exited before any write because original Python source escapes were already correct. No candidate/source/product changed. Archive verifier a1 subsequently ran through exact transport and passed.',experimental_failure=False,additional_GPU_seconds=0)
np=D/'preexecution_inspection_note.json'
with np.open('x') as f:json.dump(notes,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
logs=[]
for p in sorted((R/'results/formal_main_v2/control_transport').glob('Spatial64seed23_terminal_1032_a*.jsonl')):
 v=[json.loads(x) for x in p.read_text().splitlines()]
 assert v[-1]['event']=='control_end' and v[-1]['source173_and_entrypoint_unchanged'] is True and v[-1]['returncode']==0
 logs.append({**ref(p),'returncode':0,'wall_seconds':(v[-1]['time_ns']-v[0]['time_ns'])/1e9})
assert len(logs)==2
m=dict(schema='formal_main_v2',kind='Spatial64_seed23_independent_terminal_delivery',files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json'],independent_review=ref(D/'independent_review.json'),archive_review=ref(D/'archive_delivery_independent.json'),delivery_classification=ref(cp),transport_logs=logs,root_operations_candidates_author_executed=False,weights_copied_or_deserialized=False,final_release_authorized=False)
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(m,f,sort_keys=True,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(manifest=ref(p),report=m['independent_review'],archive_review=m['archive_review'],classification=m['delivery_classification'],counts=counts,transport=logs)))
