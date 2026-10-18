"""Assemble this audit only; never modifies an input or production state."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,xml.etree.ElementTree as ET
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo')
D=R/'.local/cuda_recovery_autonomous_audit_1940';C=R/'.local/cuda_recovery_autonomous_1940'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def dump_new(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,sort_keys=True);f.write('\n')
protected=read(D/'inputs_before.json')['protected_sha256'];after={}
for path,pin in protected.items():
    value=sha(Path(path));assert value==pin,path;after[path]=value
dump_new(D/'protected_after.json',dict(status='all_362_protected_files_unchanged',files=after))
old=read(D/'retained_failures_verification.json')
actual=read(D/'current_server_read_only.json')
assert old['failed_GPU_seconds']==226
assert actual['state_before_sha256']==actual['state_after_sha256']
assert len(actual['three_failures'])==3
for jid,target,updates,cursor,cost in [('3028460',500,0,0,84),('3028468',500,0,0,69),('3028522',1500,1000,8000,73)]:
    row=actual['three_failures'][jid]
    assert row['allowed_original_target']==target and row['retained_failed_GPU_seconds']==cost
    assert row['completed_by_arm']=={'A':updates,'B':updates}
    assert row['next_sample_cursor']=={'A':cursor,'B':cursor}
    assert not row['preflight']['model_loaded'] and not row['preflight']['final_states_opened']
pins={'gateway.py':'c97b66100a0a21a722b17e32129b7a220fac7b2b2cb8b9cc9678b88f605476c3','evidence.py':'96e5e0a653c2ed884f09f7c3bf1ce19f0664c1665921a183bc351a97f5ff9d87','test_gateway.py':'afff8a86e9e335d2a53aa3cceabea5c1f6eeffc838bd97aed506fcd1e856a2be'}
for name,pin in pins.items():assert sha(C/name)==pin,name
command=read(D/'pytest_a1_command.json');execution=read(D/'pytest_a1_execution.json')
assert execution['returncode']==0 and execution['source_before']==pins and execution['source_after']==pins
assert execution['test_sha256']==sha(D/'test_independent_gateway.py')==sha(D/'test_independent_gateway_a1.py.txt')
def junit(p,expected):
    suites=list(ET.parse(p).getroot().iter('testsuite'))
    totals={k:sum(int(x.get(k,'0')) for x in suites) for k in ['tests','failures','errors','skipped']}
    assert totals==dict(tests=expected,failures=0,errors=0,skipped=0),totals
    return dict(**totals,seconds=sum(float(x.get('time','0')) for x in suites))
tests=junit(D/'pytest_a1.xml',20);author=junit(C/'pytest_a3.xml',46)
evidence={}
def watch(p,expected=None):
    p=Path(p);value=sha(p)
    if expected:assert value==expected,str(p)
    key=p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p)
    if key in evidence:assert evidence[key]==value,key
    evidence[key]=value
for path,pin in protected.items():watch(Path(path),pin)
for rel,pin in old['read_evidence_sha256'].items():watch(Path(rel) if Path(rel).is_absolute() else R/rel,pin)
for rel,pin in actual['read_evidence_sha256'].items():watch(R/rel,pin)
for case in actual['three_failures'].values():
    for path,row in case['preflight']['server_files'].items():watch(Path(path),row['sha256'])
    for path,row in case['preflight']['control_metadata'].items():watch(Path(path),row['sha256'])
candidate_files=['gateway.py','evidence.py','test_gateway.py','pytest_a3.xml','pytest_a3.log','pytest_a3_command.json',
    'R_only_metadata_fix.json','evidence_before_path_guard.py.txt','README.md']
for n in candidate_files:watch(C/n)
for p in (C/'before_R_only_metadata_fix').iterdir():
    if p.is_file():watch(p)
own_files=['inputs_before.json','verify_existing_proofs.py','retained_failures_verification.json','retained_failures_verification.log','retained_failures_execution.json',
    'spatial_control_only_evidence_finding_a1.json','test_independent_gateway.py','test_independent_gateway_a1.py.txt','pytest_a1_command.json',
    'pytest_a1.xml','pytest_a1.log','pytest_a1_execution.json','verify_server_read_only.py','current_server_read_only.json','current_server_read_only.log',
    'current_server_execution.json','protected_after.json','assemble_review.py']
for n in own_files:watch(D/n)
checkpoint_metadata=actual['three_failures']['3028522']['preflight']['server_resume_checks']
receipt=dict(schema='formal_main_v2',kind='cuda_startup_server_recovery_gateway_independent_CPU_review',
    version='cuda-recovery-autonomous-independent-1940-v1',status='passed_CPU_review',
    reviewed_utc=datetime.now(timezone.utc).isoformat(),
    files={(C/n).relative_to(R).as_posix():pins[n] for n in ['gateway.py','evidence.py']},
    candidate_test_sha256=pins['test_gateway.py'],
    conclusion='No unresolved CPU gateway blocker. Exactly one separately root-authorized recovery may use each retained failed attempt at its original target only; this review is not retry authorization.',
    independent_tests=dict(**tests,command=command['command'],cwd=command['cwd'],execution_wall_seconds=execution['wall_seconds'],
      fixture_boundaries='Actual Gateway transaction, pinned controller Slurm parser/capacity/CAS/locks, typed authorization validator and NativeIO checks. Transactions use isolated state, synthetic scheduler/ACK/publication and upstream Science; official tensor/model/environment/GPU execution is not run. Real original failure reconstruction and current server filesystem/registry observations are separate below.'),
    author_evidence=dict(**author,role='Inspected existing final author a3 results, not rerun or relabeled independent.',
       command_ref=(C/'pytest_a3_command.json').relative_to(R).as_posix()),
    retained_failed_cases={jid:{k:v for k,v in row.items() if k!='preflight'} for jid,row in actual['three_failures'].items()},
    retained_failed_GPU_seconds_total=226,new_GPU_seconds=0,
    current_server_read_only=dict(reference=(D/'current_server_read_only.json').relative_to(R).as_posix(),sha256=sha(D/'current_server_read_only.json'),
      registered_jobs=len(actual['registered_jobs_snapshot']),capacity=actual['capacity_observation'],
      production_state_unchanged_under_shared_writer_lock=True,Object_both_checkpoint_roots_absent=True,
      Spatial_resume_metadata=checkpoint_metadata,model_loaded=False,checkpoint_tensors_deserialized=False),
    review_findings_resolved=[
      dict(issue='Sealed/state values reachable through lexical path before IO',resolution='Any sealed path part and state stems outside Python source now reject before filesystem IO; old source is retained.'),
      dict(issue='Spatial previous root review was incorrectly required as P runtime output',resolution='Only canonical previous_boundary_review exact path/SHA/bytes is rehashed in R and excluded from P inventory; no directory-wide exemption. Actual runtime raw bytes/current resumes now pass.')],
    controls_verified=['all registered IDs including CPU and historical G0 queried','CPU0 exemption requires registry plus current allocation proof; UNKNOWN blocks',
      'fresh second capacity query and active pair gate','original target 500/500/1500 with --resume and 12600 soft wall',
      'typed root authorization plus exact-source independent review and dedicated CUDA reservation required',
      'shared preexisting writer lock and CAS; durable pending precedes R/P invocation publication',
      'strict full ACK and duplicate old ID rejection; uncertain outcome retains pending and does not resend',
      'known job ID persisted before receipt/final-state failure; opaque controller and full historical registry preserved',
      'all FAILED evidence and 226 GPU seconds preserved; blocked pairs are not cleared',
      'fixed original wrapper SHA; --exclude=gpu4020/--no-requeue/04:00:00; no new scientific runtime'],
    required_root_steps_before_any_actual_submit=['publish new typed single-recovery authorization bound to these two exact source bytes and this independent review',
      'reserve one explicitly CUDA-owned GPU slot without consuming another engineering reservation',
      'repeat same-lock all-registry accounting, current original-output inventory, Object root-absence or Spatial actual double-resume SHA checks',
      'submit only the exact original target once through reviewed gateway; keep pending on any uncertainty',
      'review actual recovery artifacts afterward; any later unblock/admission to continuous5000 needs a separate root decision and verified evidence'],
    limits=dict(CPU_review_is_retry_authorization=False,current_GPU_slots_occupied=len(actual['capacity_observation']['occupied']),
      current_submit_allowed=False,reason='All eight GPU slots were occupied at the read-only observation, and no new root CUDA authorization/reservation is asserted.',
      observed_node_hardware_cause_proven=False,final_release_authorized=False,continuous5000_admission_authorized=False,
      Slurm_submissions=0,production_state_writes=0,Git_writes=0,local_Windows_project_writes=0,
      protected_R_and_S_frozen_source_files=346,total_protected_files=362),
    evidence_sha256=evidence,read_evidence_sha256=evidence)
dump_new(D/'independent_review.json',receipt)
print(json.dumps({'path':str(D/'independent_review.json'),'sha256':sha(D/'independent_review.json'),'refs':len(evidence),'status':receipt['status'],'tests':tests,'files':receipt['files']},indent=2))
