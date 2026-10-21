from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path('/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo');D=R/'.local/delivery_independent_20261021T0334'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,b):
 with (D/n).open('xb') as f:f.write(b)
r=D/'preintegration_review.json'
assert h(r)=='926ea3d1b8d2c171a218136dda989b00711c504fd2cda9af090c574d2b723cba'
v=json.loads(r.read_bytes());assert v['status']=='passed_bounded_preintegration' and v['blockers']==[] and v['check_count']==len(v['checks'])==351
for n,pin in [('.local/integrate_terminals_20261021T0334.py','f4e26c60c57a7494fc33d8f470387d3875e3c0a8f517653285c370957b036271'),('.local/integrate_terminals_20261021T0334_v2.py','83dad17ddc784b44c59f38b57faf694bda53af3d4d510055b537a3a0eef366c3'),('.local/integrate_terminals_20261021T0334_v3.py','e4f5de6cc298e5ea927d26b6f25281a089912f96baa4044c9a7ead3c7a8b7e48')]:
 p=R/n;assert h(p)==pin;save('reviewed_'+p.name,p.read_bytes())
p=R/'results/formal_main_v2/control_transport/preintegration_independent_20261021T0334.jsonl';save('preintegration_execution.jsonl',p.read_bytes())
save('README.md',('''# Terminal integration bounded pre-review

Status: passed_bounded_preintegration, 351 checks, no blockers within the stated source/design review scope. Exact source is root integrate_terminals_20261021T0334_v3.py, SHA e4f5de6cc298e5ea927d26b6f25281a089912f96baa4044c9a7ead3c7a8b7e48.

V1 kept a stale occupied job and active-cost wording; v2 corrected those but retained requested active job count 1. V3 changes only these three proven terminal projections: occupied3054717 to empty, requested1 to0 with actual allocated0, and terminal273/1994468-second scope. Historical failures, ready queue, completed legacy active_training, controller identity/lifecycle and all pending/reservation facts remain preserved.

The source keeps Goal independent original-consumer success as a mandatory pre-write gate. This review neither ran the integration nor admits the still separately reviewed Goal result. Root must supply actual final Goal report/manifest pins, then execute the exact source with the shared writer lock and both state CAS checks. Final state, summary, documents and Git allowlist require a subsequent actual review.

Count equations were checked: 6388+201=6589 current, Long600+Spatial12+Object599=1211 legacy, total7800 complete rows. Historical directory7600+201=7801 retains the original Object policy_error. Goal old200 and remaining1000 stay HOLD. No final evaluation or O2A release.

The remaining-five design manifest83b17715... has all11 exact members, preserves both prior failed design runs, fixes only Goal256 seeds23/41 and Goal64 seeds17/23/41, and proposes 200/60000/7600 and one attempt per pair. Its exact100 development-state order, small training/deployment references and earliest validation selection were crosschecked. Checkpoint bytes were deliberately not rehashed; only original receipt metadata/path/file-size identity was checked, and this scope is explicit. Missing P publications and absent per-pair plans, wrappers, sources, capacity and single-ACK admission keep production HOLD.

All 173 frozen R/S files match. This agent made no Slurm query, GPU submission, canonical/state/Git write, or final-value access. The frozen pre-review package will not be overwritten; any later actual delivery audit is separate.
''').encode())
files=[]
for p in sorted(D.iterdir()):
 if p.is_file():
  assert not p.is_symlink() and p.resolve()==p
  files.append(dict(path=p.name,sha256=h(p),bytes=p.stat().st_size))
m=dict(schema='formal_main_v2',kind='bounded_preintegration_independent_delivery',status='passed_bounded_preintegration',reviewed_by='independent',source_root=str(D),file_count=len(files),files=files,review=dict(path='preintegration_review.json',sha256=h(r),bytes=r.stat().st_size),entrypoint_sha256=v['entrypoint_sha256'],actual_final_state_review_pending=True,Git_review_pending=True,new_GPU_submissions=0,new_Slurm_queries=0,state_writes=False,Git_writes=False,utc=datetime.now(timezone.utc).isoformat())
save('delivery_manifest.json',(json.dumps(m,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
print(json.dumps(dict(status=m['status'],file_count=len(files),manifest_sha256=h(D/'delivery_manifest.json'),report_sha256=h(r))))
