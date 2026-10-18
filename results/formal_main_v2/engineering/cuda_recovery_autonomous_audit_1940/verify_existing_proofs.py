"""Rebuild only retained immutable startup failures, not an authorization."""
from pathlib import Path
import importlib.util,json,hashlib
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
A=R/".local/cuda_recovery_autonomous_audit_1940"
E={}
def read(p,want=None):
 p=Path(p);raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
 assert want is None or digest==want
 E[p.relative_to(R).as_posix()]=digest;return raw
g=R/".local/cuda_startup_recovery_0840/recover_startup_failure.py"
data=read(g,"a9440b5d6bc15a61901f1284267ef36850450a1a59e69c1ff672bc66dcdd7cc3")
read(g.with_name("startup_failure_evidence.py"),"c07c5b686d103aaabfe8a7280c62ff2a8b61fcb3ab5d07ff7592011fabbfa480")
sp=importlib.util.spec_from_file_location("_independent_startup_gateway",g);m=importlib.util.module_from_spec(sp)
exec(compile(data,str(g),"exec"),m.__dict__)
readiness=json.loads(read(R/".local/cuda_recovery_server_heartbeat_1808/readiness_review.json","39649e8d87fd4ea44029a4ebf4f333403b1007f3d1ed94290744b8a39e908798"))
publication=json.loads(read(R/"results/formal_main_v2/preflight/heartbeat_20261019T0208/cuda_failure_canonical_publication_root.json","65382bd0fbc599224129f8bcfea6a526f962aed9b1383b799aa0e4d785dac64b"))
assert publication["retry_authorized"] is False and publication["blocked_pairs_cleared"] is False
checks=[]
for case in readiness["cases"]:
 jid=case["job_id"];job=next(j for j in case["registered_pair_jobs_at_observation"] if j["job_id"]==jid)
 ev=m.Evidence(R);facts=m.failure.require_saved(ev,job=job)
 for rel,want in ev.hashes.items():read(R/rel,want)
 canonical=next(p for p in publication["proofs"] if p["job_id"]==jid)
 assert ev.hashes[canonical["path"]]==canonical["sha256"]
 assert facts["ordinary_segment_completed"] is False and facts["failed_status"]=="FAILED" and facts["failed_exit_code"]=="1:0"
 assert facts["current_allocation_new_updates"]==facts["current_allocation_arm_initializations"]==0
 expected={"3028460":(500,0,84),"3028468":(500,0,69),"3028522":(1500,1000,73)}[jid]
 assert facts["requested_segment_end"]==expected[0] and set(facts["completed_by_arm"].values())=={expected[1]} and facts["failed_allocation_gpu_seconds"]==expected[2]
 assert facts["next_sample_cursor"]==dict(A=expected[1]*8,B=expected[1]*8)
 assert facts["allowed_next_segment_end"]==expected[0] and facts["explicit_resume_required"] is True
 assert facts["node_hardware_failure_proven"] is False and facts["final_states_opened"] is False
 checks.append({"job_id":jid,"original_target":expected[0],"completed_by_arm":facts["completed_by_arm"],"cursor":facts["next_sample_cursor"],
  "failed_GPU_seconds":expected[2],"pair_GPU_seconds_before_retry":facts["pair_allocated_gpu_seconds"],
  "failed_status_preserved":True,"canonical_SHA":canonical["sha256"],"bound_archived_files":len(facts["evidence_bundle"]),
  "historical_resume_identity":facts["server_resume_checks"],"fresh_checkpoint_hash_in_this_check":False})
assert sum(x["failed_GPU_seconds"] for x in checks)==226
read(Path(__file__))
out={"status":"verified_three_immutable_failed_startups_not_retry_authorized","cases":checks,"failed_GPU_seconds":226,
 "current_checkpoint_recheck":"pending new gateway fresh same-lock check; this command does not inspect checkpoints",
 "original_reconstruction_used":True,"production_state_read":False,"production_state_written":False,"Slurm_queries_or_submissions":0,"GPU_runs":0,"read_evidence_sha256":E}
with (A/"retained_failures_verification.json").open("xb") as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+"\n").encode())
print(json.dumps({k:v for k,v in out.items() if k!="read_evidence_sha256"},ensure_ascii=False))
