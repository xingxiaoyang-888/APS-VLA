"""Seal independent seven-pair audit evidence; writes only its own new summary."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
A=R/".local/completed_pairs_independent_0547"
keys=["libero_spatial_k256_seed17","libero_spatial_k256_seed23","libero_spatial_k256_seed41","libero_spatial_k64_seed17","libero_spatial_k64_seed41","libero_object_k128_seed23","libero_object_k256_seed17"]
root_reported_boundaries=[2000,1500,1000,2000,1000,1000,1000]
evidence={};pairs=[]
def sha(p):
 d=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4*1024*1024),b""):d.update(b)
 return d.hexdigest()
def bind(p,expected=None):
 p=Path(p);h=sha(p)
 if expected is not None and h!=expected:raise ValueError("changed evidence "+str(p))
 if str(p) in evidence and evidence[str(p)]!=h:raise ValueError("conflicting evidence")
 evidence[str(p)]=h;return h
for key,old in zip(keys,root_reported_boundaries):
 p=A/(key+"_independent.json");h=bind(p);x=json.loads(p.read_bytes())
 assert x["status"]=="passed" and x["completed_by_arm"]=={"A":5000,"B":5000} and x["allowed_next_training_update"] is None
 for q,v in x["read_evidence_sha256"].items():bind(q,v)
 pairs.append({"pair_key":key,"receipt":{"path":str(p.relative_to(R)),"sha256":h},"completed_by_arm":x["completed_by_arm"],"allowed_next_training_update":None,"job_ids":x["job_ids"],"all_history_allocated_GPU_seconds":x["allocated_GPU_seconds"],"best_updates":{a:x["arms"][a]["best_update"] for a in ("A","B")},"best_sha256":{a:x["arms"][a]["best_checkpoint_sha256"] for a in ("A","B")},"validation_windows_per_node":x["validation_windows_per_node"],"evidence_refs":len(x["read_evidence_sha256"]),"root_reported_pre_audit_common_boundary":old,"conditional_increment_after_root_acceptance":2*(5000-old)})
files=["requested_pairs_snapshot.json","requested_pairs_snapshot_v2.json","audit_completed_attempt01.py.txt","audit_completed.py","audit_completed_object.py","attempt01_correction.json","attempt03_correction.json","attempt03_correction.diff","finalize_review.py"]
for attempt in (1,2,3,4):
 files.extend([f"attempt{attempt:02d}.stdout.log",f"attempt{attempt:02d}.stderr.log",f"attempt{attempt:02d}.execution.json"])
for name in files:bind(A/name)
result={"schema":"formal_main_v2","kind":"independent_completed_pairs_evidence_audit","status":"passed_independent_evidence_review","reviewed_utc":datetime.now(timezone.utc).isoformat(),"pairs":pairs,"pairs_checked":7,"arms_checked":14,"updates_in_reviewed_final_artifacts":70000,"all_history_allocated_GPU_seconds":sum(x["all_history_allocated_GPU_seconds"] for x in pairs),"accounting_note":"All-history cost is retained, not a new incremental cost charge. Boundaries below are supplied by root for deduplicated integration; this audit does not write or certify current supervisor counters.","integration":{"root_reported_previous_total":170000,"conditional_increment_after_root_acceptance":sum(x["conditional_increment_after_root_acceptance"] for x in pairs),"conditional_total_after_root_acceptance":170000+sum(x["conditional_increment_after_root_acceptance"] for x in pairs),"state_modified":False},"checked":["Bound machine completion to immutable original request and replayed original raw reviewer exactly; current global state not used for replay.","Independently regenerated all 40000 seeded samples per arm; checked exact update/microbatch sequence, actual set coverage, task/phase usage, full attempt and 50-step commit chain with no replay.","Independently recomputed 11 complete task-macro hard-validation metrics and earliest selected update; matched A/B initialization and initial hard behavior.","Recomputed original 5000-step annealing and fixed A/B logged losses; verified hard token masks per view, frozen VLA identity, source/config/data and Object loader history.","Freshly streamed SHA256 of both final best.pt and resume.pt per arm; exact server paths and stable stat checked, no tensor deserialization/copy.","Retained all historical terminal Slurm allocations; no new GPU run or Slurm call."],"audit_helper_failures_retained":[{"attempt":"01","cause":"Private helper sample digest used noncompact JSON; all sample values already matched. Corrected serializer to frozen compact encoding; raw records unchanged."},{"attempt":"03","cause":"Private helper expected only one pull reference; Object legitimately also binds acceptance pull. New Object helper chooses exactly current job/run_root terminal pull and retains all historical references. Spatial helper and completed receipts untouched."}],"limits":["Optimizer/RNG tensor contents were not independently deserialized. Assurance is exact frozen core/F03, chronological journal/cursor/commit identity and actual final resume SHA.","Teacher/demo error means are recomputed from logged per-window errors, not new inference.","Evidence audit establishes training integrity only; no new closed-loop efficacy, latency, final/test release or GPU execution claim."],"new_GPU_seconds":0,"Slurm_calls":0,"production_state_modified":False,"Git_modified":False,"sealed_values_read":False,"read_evidence_sha256":dict(sorted(evidence.items()))}
p=A/"independent_review.json"
with p.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write("\n")
print(json.dumps({"path":str(p),"sha256":sha(p),"refs":len(evidence),"pairs":7,"cost":result["all_history_allocated_GPU_seconds"],"conditional_increment":result["integration"]["conditional_increment_after_root_acceptance"]}))
