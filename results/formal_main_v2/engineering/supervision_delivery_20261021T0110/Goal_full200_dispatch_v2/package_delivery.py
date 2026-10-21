from pathlib import Path
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/goal_full200_dispatch_20261021T0110_v2';OLD=R/'.local/goal_full200_dispatch_20261021T0110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
old=json.loads((OLD/'delivery_manifest.json').read_bytes())
assert sha(OLD/'delivery_manifest.json')=='d3d9cfca965d9af267c424431ecaa3a465bbf39366c5eac9d3c105c3fd6d0a80'
for r in old['files']:
 p=R/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
pins=json.loads((D/'final_pins.json').read_bytes());cpu=json.loads((D/'CPU_report.json').read_bytes())
assert sha(D/'dispatch.py')==pins['dispatch']==cpu['dispatch_sha256']
assert sha(D/'verify_cpu.py')==pins['verify_cpu']
assert cpu['positive_count']==94 and cpu['negative_count']==187
pub=json.loads((D/'publication_map.json').read_bytes());scope=json.loads((D/'scope.json').read_bytes())
assert sha(D/'scope.json')==pins['scope']
for path,pin in scope['runtime_files'].items():
 p=R/'.local/goal_full200_author_20261021T0110_v2/package'/Path(path).name
 assert sha(p)==pin
journal=D/'transport';journal.mkdir()
for p in sorted((R/'results/formal_main_v2/control_transport').glob('goal_full200_dispatch_20261021T0110_v2_*.jsonl')):
 with (journal/p.name).open('xb') as f:f.write(p.read_bytes())
assert len(list(journal.iterdir()))==3
report=json.loads((OLD/'author_report.json').read_bytes())
report.update(kind='Goal_full200_exact_atomic_dispatch_v2_author_delivery',status='passed_CPU_candidate_pending_independent_and_root',
 dispatch_files=pub['files'],CPU_positive=94,CPU_negative=187,read_only_replay_passed=True,
 CPU_report=dict(path=str((D/'CPU_report.json').relative_to(R)),sha256=sha(D/'CPU_report.json')),
 preparer=dict(path=str((D/'prepare_admission.py').relative_to(R)),sha256=sha(D/'prepare_admission.py'),behavior='prints reviewed admission JSON only; no writes/scheduler'),
 previous_package=dict(path=str((OLD/'delivery_manifest.json').relative_to(R)),sha256=sha(OLD/'delivery_manifest.json'),all38_original_members_rehashed=True),
 independent_v1_blocker=dict(path=str((D/'v1_terminal_contract_blocker.json').relative_to(R)),sha256=sha(D/'v1_terminal_contract_blocker.json')),
 source_changes=['Preserve original consumer development mode and original_run registration root.',
  'Keep exact typed goal_dispatch_mode; do not reject unrelated development rows as duplicates.'],
 real_original_consumer_validate_job_called=True,
 terminal_fixture_only=True,real_GPU_terminal_evidence_created=False,
 retained_failures=['Original d3d9 dispatcher/source/CPU/failures remain byte-identical and retained.',
  'Independent v1 registration mismatch reproduced and retained; no production job was submitted from v1.',
  'Only final v2 runtime2767f20c is allowed; v1 consumer gap remains historical.'])
write(D/'author_report.json',report)
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='delivery_manifest.json':
  assert not p.is_symlink()
  files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
write(D/'delivery_manifest.json',dict(schema='formal_main_v2',kind='Goal_full200_atomic_dispatch_v2_CPU_delivery_manifest',
 root=str(D.relative_to(R)),file_count=len(files),files=files,production_admitted=False,GPU_execution_authorized=False))
print(json.dumps(dict(manifest_sha256=sha(D/'delivery_manifest.json'),file_count=len(files),bytes=sum(x['bytes'] for x in files),
 author_report_sha256=sha(D/'author_report.json'),pins=pins,CPU_positive=94,CPU_negative=187),sort_keys=True))
