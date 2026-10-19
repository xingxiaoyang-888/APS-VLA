from pathlib import Path
import hashlib,importlib.util,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');B='results/formal_main_v2/preflight/heartbeat_20261019T1743'
p=R/'scripts/ops/nonweight_archive.py';assert hashlib.sha256(p.read_bytes()).hexdigest()=='f81284b3c56fbfd1cce339c4ea98b20943c8cd0866b4e8b94c38ac3cdbd1e3c2'
sp=importlib.util.spec_from_file_location('archive_corrected_request',p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
old='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0547_union17_v2.json'
prev=json.loads((R/old).read_text());bad='results/formal_main_v2/nonweight_archives/v1/requests/completed_training_20261019_0943_union23.json';request=json.loads((R/bad).read_text())
assert len(request['files'])==23
request['provenance']=[prev['request']]+[x for x in request['provenance'] if x['path']!=old]
rel=B+'/nonweight_archive_request_v2.json';snapshot='results/formal_main_v2/nonweight_archives/v1/snapshots/completed_training_20261019_0943_union23.json'
m.lexical(rel,'metadata');m.lexical(snapshot,'snapshot');m.request_value(request)
for row in request['provenance']:m.lexical(row['path'],'metadata')
with (R/rel).open('x') as f:json.dump(request,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
result=m.pack(R,rel,snapshot)
with (R/(B+'/nonweight_archive_pack.json')).open('x') as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
print(json.dumps({'status':result['status'],'snapshot':snapshot,'sha256':hashlib.sha256((R/snapshot).read_bytes()).hexdigest(),'files':23,'raw_bytes':sum(x['bytes'] for x in request['files']),'originals_retained':True}),flush=True)
