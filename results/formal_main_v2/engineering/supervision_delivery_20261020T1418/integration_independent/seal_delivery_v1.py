from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,sys,time
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/integration_independent_20261020T1418';B='results/formal_main_v2/preflight/heartbeat_20261020T2218'
def guard(event,args):
 if event.startswith(('socket.','subprocess.')) or event in ['os.system','os.fork','os.posix_spawn']:raise PermissionError(event)
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(args[0]);mode=args[1];flags=args[2]
  if (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)):assert p.resolve().is_relative_to(D.resolve()),str(p)
sys.addaudithook(guard)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel,pin=None):
 p=R/rel
 if pin:assert sha(p)==pin,(rel,sha(p))
 return json.loads(p.read_bytes())
def ref(p):return dict(path=str(p.relative_to(R)),sha256=sha(p),bytes=p.stat().st_size)
def out(name,x):
 p=D/name;assert not p.exists();p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n');return ref(p)
reports={
 'submission_independent_review.json':'ea7336b1f5c449e42614a282a371355532796f6f82d7084ec92c81f3ea7402a5',
 'Goal_dense_statistics_independent_review.json':'751d744e09d3cd5c6afb2ff3e03bdc6ef369bb9c7e39ca1426eff681900d75bd',
 'preview_integration_independent_review.json':'c80ff2f5aa29054cfa07fdc6f6bd7a57fd6ce58091a0d252b9800d134f770fb6',
 'applied_integration_independent_review.json':'366107ca5d32669aadfaf346c3ff4d1b86c178811f246ff76b505a42eeb4b309'}
for name,pin in reports.items():assert sha(D/name)==pin
logs=[('independent_integration_20261020T1418_submissions_v1.jsonl',0),('independent_integration_20261020T1418_dense_statistics_v1.jsonl',0),('independent_integration_20261020T1418_preview_v1.jsonl',0),('independent_integration_20261020T1418_applied_v1.jsonl',1),('independent_integration_20261020T1418_applied_v2.jsonl',0),('heartbeat_20261020T1418_integration_apply.jsonl',0)]
closed=[];elapsed=0.0;(D/'closed_transport').mkdir(exist_ok=False)
for name,rc in logs:
 p=R/'results/formal_main_v2/control_transport'/name;b=p.read_bytes();rows=[json.loads(x) for x in b.splitlines() if x.strip()];assert rows[0]['event']=='control_start' and rows[-1]['event']=='control_end' and rows[-1]['returncode']==rc and rows[-1]['source173_and_entrypoint_unchanged']
 if name.startswith('heartbeat_'):
  assert sha(p)=='6adf0cc6cca99d474f3ed2e751afdf3411b569b44af48ea88bf5430fbffa5c76'
  assert rows[0]['entrypoint_sha256']=='b2c472fded9a1eed04ab769a97592b347e93b86d3c1a73c8ba28e96c3a807efd' and '--apply' in rows[0]['command']
 else:elapsed+=(rows[-1]['time_ns']-rows[0]['time_ns'])/1e9
 dest=D/'closed_transport'/name;dest.write_bytes(b);closed.append(dict(original=ref(p),copy=ref(dest),returncode=rc,kind='root_original_apply' if name.startswith('heartbeat_') else 'independent_audit'))
manifest=rd('.local/integration_candidate_20261020T1418/manifest.json','91e6680563d6d4a76bf24a4f9894503681532a77ef780c3bebf1afabcf377ada')
archive=rd(B+'/integration_candidate_delivery.json','f7defa4b2c76716b8693f5de0b45b73cc751d19a73c2ef3b2b594c5216891d87')
assert len(archive['copies'])==38 and manifest['file_count']==37 and not manifest['canonical_state_docs_Git_Slurm_mutations']
for pair in archive['copies']:
 a=pair['source'];b=pair['archive'];assert a['sha256']==b['sha256']==sha(R/a['path'])==sha(R/b['path'])
selftest=rd('.local/integration_candidate_20261020T1418/cpu_selfcheck_v3.json','628672d68c3d6d6f1e76ec684eb16701f1024e36f342ebcb93e5334fa950918a')
assert selftest['status']=='passed' and selftest['private_synthetic_test'] and selftest['count']==33 and not selftest['canonical_mutations']
for r in manifest['transport_logs']:
 rows=[json.loads(x) for x in (R/r['path']).read_bytes().splitlines() if x.strip()];assert sha(R/r['path'])==r['sha256'] and rows[-1]==r['last_event']
assert (D/'preview_transport_invocation_failure.json').is_file() and (D/'applied_integration_failure_v1.json').is_file()
receipt=out('delivery_receipt.json',dict(schema='formal_main_v2',kind='independent_delivery_and_root_apply_transport_seal',status='passed',utc=datetime.now(timezone.utc).isoformat(),reviewer='/root/devplans_audit_20261020_1418',reports=[ref(D/x) for x in reports],closed_transports=closed,root_original_apply_transport_verified=True,candidate38_archive_files_exact=True,candidate33_CPU_synthetic_checks_only=True,retained_audit_failures=['preview_transport_invocation_failure.json','applied_integration_failure_v1.json'],failure_scope='One invalid transport pin rejected before execution; one audit assumed indented state instead of controller compact canonical JSON. Corrected audit verifies both exact original encodings; production evidence unchanged.',new_GPU_jobs=0,new_GPU_seconds=0,independent_audit_commands_CPU_wall_seconds=elapsed,canonical_state_Git_Slurm_mutations=False))
files=[ref(p) for p in sorted(D.rglob('*')) if p.is_file()]
final=out('final_manifest.json',dict(schema='formal_main_v2',kind='independent_server_only_submission_statistics_integration_delivery',status='passed',reviewer='/root/devplans_audit_20261020_1418',source_directory=str(D.relative_to(R)),files=files,file_count=len(files),delivery_receipt=receipt,main_report=ref(D/'applied_integration_independent_review.json'),failure_records_preserved=True,own_seal_transport_not_self_referenced='results/formal_main_v2/control_transport/independent_integration_20261020T1418_seal_v1.jsonl',new_GPU_jobs=0,new_GPU_seconds=0,canonical_mutations=False))
print(json.dumps(dict(status='passed',manifest=final,delivery=receipt,file_count=len(files)),ensure_ascii=False))
