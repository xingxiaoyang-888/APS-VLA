from pathlib import Path
import hashlib,json,sys
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/object_single_error_candidate_20261020T2253'
sys.path.insert(0,str(D))
import fixed as F
def put(name,value):
 raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
 with (D/name).open('xb') as f:f.write(raw)
def ref(p):return dict(path=p.relative_to(R).as_posix(),bytes=p.stat().st_size,sha256=F.sha(p.read_bytes()))
tests=json.loads((D/'cpu_tests.json').read_text())
assert tests['status']=='passed_CPU_candidate_only' and tests['positive_checks']==24 and tests['negative_checks']==74
entries=[]
for name in ['fixed.py','iterator.py','gate.py','terminal.py','scope.json']:
 p=D/name;target=F.BASE+'/'+name
 assert F.sha(p.read_bytes())==tests['source_map'][target]
 entries.append(dict(source=p.relative_to(R).as_posix(),target_R=str(R/target),target_P=str(F.P/target),bytes=p.stat().st_size,sha256=F.sha(p.read_bytes()),actual_installed=False))
put('publication_map.json',dict(schema='formal_main_v2',kind='Object_single_error_CPU_candidate_publication_map',
 status='HOLD_not_installed',current_runtime_core_only=entries,core_closure_sha256=tests['bundle_sha256'],
 unimplemented_required_production_paths=[F.BASE+'/'+n for n in ['wrapper.py','entry.py','gateway.py','reviewer.py','consumer.py']],
 exact_future_plan_directory=F.EX,exact_future_output=str(F.P/F.OUT),
 production_receipt_paths=[F.EX+'/'+n+'.json' for n in ['root_legacy_adoption','root_repair','independent_runtime_review','runtime_readiness','root_submission_review']],
 actual_599_independent_archive=ref(R/F.PROOF_ARCHIVE),root_599_adoption_performed=False,
 complete_production_source_closure_frozen=False,actual_P_verified=False,submit_authorized=False))
put('readonly_reproduction_receipt.json',dict(schema='formal_main_v2',kind='Object_single_error_readonly_CPU_reproduction',
 status='passed',verification_entry=ref(D/'verify_saved.py'),tests=ref(D/'cpu_tests.json'),positive=24,negative=74,
 synthetic_only=True,new_scientific_trials=0,new_GPU_seconds=0,actual_P_verified=False,production_admitted=False))
journal_names=['object_single_error_bootstrap_20261020T2253.jsonl','object_single_error_CPU_20261020T2253_a1.jsonl','object_single_error_CPU_20261020T2253_verify.jsonl']
for name in journal_names:
 src=R/'results/formal_main_v2/control_transport'/name;raw=src.read_bytes()
 rows=[json.loads(x) for x in raw.splitlines()]
 assert rows[-1].get('returncode',rows[-1].get('exit_code',0))==0
 with (D/('transport_'+name)).open('xb') as f:f.write(raw)
allfiles=sorted(p for p in D.iterdir() if p.is_file())
assert not any(p.suffix in ['.bin','.pt','.npz','.safetensors'] for p in allfiles)
assert all(p.stat().st_size<100_000_000 for p in allfiles)
manifest=dict(schema='formal_main_v2',kind='Object_single_error_CPU_candidate_delivery',root=D.relative_to(R).as_posix(),
 status='HOLD_CPU_candidate_requires_independent_audit_and_production_chain',
 file_count=len(allfiles),total_bytes=sum(p.stat().st_size for p in allfiles),files=[ref(p) for p in allfiles],
 source_core_sha256=tests['bundle_sha256'],new_scientific_trials=0,new_GPU_seconds=0,Slurm_submissions=0,
 actual_P_verified=False,production_admitted=False,original599_independent_modified=False,
 original600_raw_sha256=F.PINS[F.RUN+'/trials.jsonl'],original6713_GPU_seconds_preserved=True,final_sealed=True,
 independent_review_not_yet_run=True,production_write_performed=False,
 packaging_transport_journal='results/formal_main_v2/control_transport/object_single_error_package_20261020T2253.jsonl')
put('delivery_manifest.json',manifest)
print(json.dumps(dict(manifest=ref(D/'delivery_manifest.json'),file_count=len(allfiles),total_bytes=manifest['total_bytes'],
 status=manifest['status']),ensure_ascii=False))
