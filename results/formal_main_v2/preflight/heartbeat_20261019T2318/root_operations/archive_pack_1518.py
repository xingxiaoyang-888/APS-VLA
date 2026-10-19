from pathlib import Path
import json,hashlib,importlib.util,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T2318'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
p=R/'scripts/ops/nonweight_archive.py';assert h(p)=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2';sp=importlib.util.spec_from_file_location('archive1518',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
old='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json';assert h(R/old)=='4af1f5375d8e79bf567aeb5e68e1b4ed28b52bce5dd77e6a65623e17be70abb2';snap=json.loads((R/old).read_text());reqref=snap['request'];assert h(R/reqref['path'])==reqref['sha256'];prev=json.loads((R/reqref['path']).read_text())
newnames=[
'results/formal_main_v2/libero_object/k128/seed41/training/A/attempts/20261019T023418_aa05f0ab4622/cost_events.jsonl',
'results/formal_main_v2/libero_object/k128/seed41/training/B/attempts/20261019T093146_826f174dbd4b/cost_events.jsonl',
'results/formal_main_v2/libero_object/k128/seed41/training/cache_events/3036313_78078dd1b2e7.jsonl']
files=prev['files']+[ref(n) for n in newnames];assert len(files)==len({v['path'] for v in files})==26
for row in files:assert ref(row['path'])==row
request=dict(schema='cti_nonweight_archive_v1',kind='archive_request',files=files,provenance=[reqref,ref(B+'/3036313_root_terminal.json'),ref('results/formal_main_v2/libero_object/k128/seed41/training/segment_reviews/3036313_independent.json')])
request_rel=B+'/nonweight_archive_request.json';snapshot='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_1518_union26.json'
m.lexical(request_rel,'metadata');m.lexical(snapshot,'snapshot');m.request_value(request)
for row in request['provenance']:m.lexical(row['path'],'metadata')
with (R/request_rel).open('x') as f:json.dump(request,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
result=m.pack(R,request_rel,snapshot)
with (R/B/'nonweight_archive_pack.json').open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(dict(status=result['status'],snapshot=snapshot,sha256=h(R/snapshot),files=26,raw_bytes=sum(x['bytes'] for x in files),originals_retained=True)))
