from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/collect_terminal_20261020T1949/development_gateway'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['k64s23_gateway_root_drafts_static_20261020T1949_v2.jsonl','k64s23_gateway_root_drafts_static_20261020T1949_v3.jsonl']:
 src=R/'results/formal_main_v2/control_transport'/name;dst=D/'transport'/name
 with dst.open('xb') as f:f.write(src.read_bytes())
refs={
 'gateway':{'path':str((D/'revision01/gateway.py').relative_to(R)),'sha256':'873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb'},
 'root_signer_draft':{'path':str((D/'root_sign_readiness_v1.py').relative_to(R)),'sha256':'773bc105bd77ddab8a9927e981f87c2050ff1baecb34cfdb4009916099e81338'},
 'root_dispatch_draft':{'path':str((D/'root_dispatch_v1.py').relative_to(R)),'sha256':'750a8178ef670d7a45ffc9797a05f6fb492ff0d123f9fbb0f095211b4a5af041'},
 'CPU_report':{'path':str((D/'CPU_attempt01/CPU_report.json').relative_to(R)),'sha256':'7d257e61b0f4643af1a6f12884c0650e80862c7f3f8ade7f51af63da2a4921bd'},
 'root_canonical_publication':{'path':'results/formal_main_v2/preflight/heartbeat_20261021T0349/k64_gateway_source_publication.json','sha256':'f89ca24e826f7a21ab4d5bb7e50cd6617fbefcb3ecb6d98cc344ee212408fa12'},
 'independent_gateway_CPU':{'path':'.local/k64_seed23_bridges_independent_20261020T1949/control_runtime_attempt01/independent_gateway_CPU_review.json','sha256':'45a86335a1c3224c47e76e162e90958f2437fd0152fe8ee1edbf710bfb10284a'}
}
for ref in refs.values():assert h(R/ref['path'])==ref['sha256']
assert not any(p.is_symlink() for p in D.rglob('*'))
files=[dict(source=p.relative_to(R).as_posix(),path=p.relative_to(D).as_posix(),sha256=h(p),bytes=p.stat().st_size) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json']
assert all(x['bytes']<100*1024**2 for x in files)
value={'schema':'formal_main_v2','kind':'bounded_k64s23_development_gateway_author_complete_delivery','created_utc':datetime.now(timezone.utc).isoformat(),'root':D.relative_to(R).as_posix(),'files':files,'file_count':len(files),'total_bytes':sum(x['bytes'] for x in files),'key_refs':refs,'source_closed_no_further_writes':True,'candidate_root_helpers_executed_by_author':False,'new_GPU_submissions':0,'scientific_trials_added':0,'actual_per_pair_P_readiness_pending_root':True,'all_failures_retained':True,'frozen_173_unchanged':True,'existing_collect_author_delivery_unchanged':{'path':'.local/collect_terminal_20261020T1949/collect_delivery_manifest.json','sha256':'897889f47bc402209b73bda69b09401f4174210cf8dedeb0ec929ae16df8e91a'},'seal_transport':'results/formal_main_v2/control_transport/k64s23_gateway_author_seal_20261020T1949_v1.jsonl','seal_transport_note':'Transport records this manifest writer itself and remains in canonical audit log; excluded from self-referential manifest bytes. Root post-readiness/submission receipts belong outside this sealed author directory.'}
assert h(R/value['existing_collect_author_delivery_unchanged']['path'])==value['existing_collect_author_delivery_unchanged']['sha256']
p=D/'delivery_manifest.json'
with p.open('x') as f:json.dump(value,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
print(json.dumps({'manifest':str(p.relative_to(R)),'sha256':h(p),'files':len(files),'bytes':value['total_bytes'],'closed':True}))
