from pathlib import Path
import hashlib,json,shutil
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/goal_full200_dispatch_20261021T0110'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
 with p.open('x') as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2);f.write('\n')
pins=json.loads((D/'final_pins.json').read_bytes());cpu=json.loads((D/'CPU_report.json').read_bytes())
assert pins['dispatch']==sha(D/'dispatch.py')==cpu['dispatch_sha256']
assert pins['verify_cpu']==sha(D/'verify_cpu.py')
assert cpu['positive_count']==84 and cpu['negative_count']==177
assert cpu['runtime_package_manifest_sha256']==pins['runtime_package_manifest']=='2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec'
scope=json.loads((D/'scope.json').read_bytes());pub=json.loads((D/'publication_map.json').read_bytes())
assert sha(D/'scope.json')==pins['scope']
journal=D/'transport';journal.mkdir(exist_ok=True)
for p in sorted((R/'results/formal_main_v2/control_transport').glob('goal_full200_dispatch_20261021T0110_*.jsonl')):
 target=journal/p.name
 with target.open('xb') as f:f.write(p.read_bytes())
required=['construct','construct_tests','cpu_v4','cpu_v5','cpu_v6','freeze_v2','cpu_final_v2','replay_final']
for s in required:assert (journal/('goal_full200_dispatch_20261021T0110_'+s+'.jsonl')).is_file(),s
report=dict(schema='formal_main_v2',kind='Goal_full200_exact_atomic_dispatch_author_delivery',
 status='passed_CPU_candidate_pending_independent_and_root',review_scope='source_and_CPU_only',
 dispatch_files=pub['files'],runtime_package_manifest_sha256=pins['runtime_package_manifest'],runtime_files=scope['runtime_files'],
 CPU_report=dict(path=str((D/'CPU_report.json').relative_to(R)),sha256=sha(D/'CPU_report.json')),
 CPU_positive=84,CPU_negative=177,read_only_replay_passed=True,
 scope=dict(stage_key=scope['stage_key'],pair_id=scope['pair_id'],maximum_trials=200,unique_development_states=100,
  maximum_total_control_steps=60000,maximum_total_policy_queries=7600,maximum_attempts=1,maximum_GPU_jobs=1,
  all_modes_capacity=8,old200_HOLD=True,otherGoal1000_HOLD=True,final_allowed=False),
 submission_transactions='one held sbatch, durable original ACK, CAS registration, exact real-runtime metadata dispatch proof, one release',
 reconcile='existing original pending and ACK only; no new submit; possibly-issued release never repeated; source-only existing-job metadata does not claim fresh RAW',
 preparer=dict(path=str((D/'prepare_admission.py').relative_to(R)),sha256=pins['prepare_admission'],behavior='prints reviewed candidate admission JSON only; no writes or scheduler'),
 old_engineering_GPU_seconds=1643,new_Slurm_queries=0,new_Slurm_submissions=0,new_GPU_seconds=0,new_scientific_trials=0,
 canonical_files_written_by_author=False,P_files_written_by_author=False,state_written_by_author=False,Git_written_by_author=False,
 actual_P_verification_performed_by_author=False,GPU_execution_authorized=False,production_admitted=False,
 source173_not_modified_by_author=True,old_Object_package_not_modified_by_author=True,
 blockers=['Independent final v2 runtime source/CPU review and exact dispatcher source/CPU review remain required.',
  'Root canonical R/P publication, byte verification and actual P --verify capture are required.',
  'Real root/independent runtime readiness, exact root authorization and root dispatch admission must be formed from reviewed evidence.',
  'No Goal new200 GPU output or real terminal review exists; all raw scientific acceptance remains prospective.'],
 retained_failures=['Two early CPU fixture mismatches are preserved, not production failures.',
  'The transport SHA typo was rejected before executing the replay; original stderr and corrected replay are retained.',
  'Runtime v1 evidence remains historical; only final v2 package SHA is bound by final source.'])
dump(D/'author_report.json',report)
dump(D/'derivation_addendum.json',dict(schema='formal_main_v2',kind='Goal_exact_derivation_final_scope',
 original_construction=sha(D/'derivation.json'),final_dispatch_sha256=pins['dispatch'],
 copied_Object_gateway_is_not_called_or_authorized=True,
 post_construction_changes=['Final v2 runtime and exact scope literal pins.',
 'Root full200 admission field/time guard and JSON-only preparation helper.',
 'Goal-only naming, truthful root preparation timestamp and actual sbatch call timestamps.',
 'New held dispatch proof consumed by unchanged final runtime validate_dispatch.',
 'Existing-ACK metadata branch rebuilds original full scientific chain without fresh RAW claims, and is forbidden for new submissions.']))
files=[]
for p in sorted(D.rglob('*')):
 if p.is_file() and p.name!='delivery_manifest.json':
  assert not p.is_symlink()
  assert p.suffix in ('.py','.json','.jsonl','.md','.txt')
  files.append(dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)))
manifest=dict(schema='formal_main_v2',kind='Goal_full200_atomic_dispatch_CPU_delivery_manifest',
 root=str(D.relative_to(R)),file_count=len(files),files=files,production_admitted=False,GPU_execution_authorized=False)
dump(D/'delivery_manifest.json',manifest)
print(json.dumps(dict(manifest_sha256=sha(D/'delivery_manifest.json'),file_count=len(files),bytes=sum(x['bytes'] for x in files),
 author_report_sha256=sha(D/'author_report.json'),dispatch=pins['dispatch'],scope=pins['scope'],CPU_positive=84,CPU_negative=177),sort_keys=True))
