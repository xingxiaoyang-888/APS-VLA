"""Read-only real scientific/raw/metadata verification. Never invokes Gateway.run."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,time
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/cuda_continuous_admission_independent_1111"
C=R/".local/cuda_continuous_admission_1111"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
pins={"gateway.py":"a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792","admission.py":"65a6a6c22710ba74f43c86589b7acdac7bd3c1b10fd86028d339eb98e3f71dcb"}
for name,h in pins.items():assert sha(C/name)==h
spec=importlib.util.spec_from_file_location("independent_real_admission_gateway",C/"gateway.py")
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g);a=g.a
before={rel:sha(R/rel) for rel in ["scripts/ops/formal_autonomous_training_v1/"+n+".py" for n in ("controller","backend","worker","execution")]}
context={"kind":"private_readonly_planning_context_not_root_authorization","status":"not_authorized","gateway_files":g.source_files(),"submission_authorized":False}
ctx=D/"planning_context_only_not_authorization.json"
with ctx.open("xb") as f:f.write(a.canonical(context))
ref={"path":ctx.relative_to(R).as_posix(),"sha256":sha(ctx)}
state=json.loads((R/a.STATE).read_bytes());rows=a.history(state)
reviewer=a.load(R/a.OLD_REVIEWER,a.REVIEWER_SHA,"independent_pinned_original_startup_reviewer")
science=a.Science(R,reviewer=reviewer)
t=time.monotonic();plan=science.prepare(state,context,ref);raw_seconds=time.monotonic()-t
t=time.monotonic();native=a.NativeIO().preflight(plan);native_seconds=time.monotonic()-t
old=plan["prior_invocation"];new=plan["invocation"];projection=json.loads(json.dumps(new))
projection.pop("continuous_admission");projection["registered_utc"]=old["registered_utc"];projection["segment_end"]=500
for flag in ("--stop-after-updates","--max-wall-seconds"):projection["argv"][projection["argv"].index(flag)+1]=old["argv"][old["argv"].index(flag)+1]
assert projection==old
assert plan["root_review"]["completed_by_arm"]=={"A":500,"B":500}
assert native["server_resume_checks"]==plan["server_resume_checks"]
assert sum(j["elapsed_seconds"]*j["gpus"] for j in rows)==6596
science.e.unchanged()
assert before=={rel:sha(R/rel) for rel in before}
for name,h in pins.items():assert sha(C/name)==h
out={"schema":"formal_main_v2","kind":"independent_real_readonly_continuation_science_reconstruction","status":"passed_real_raw_and_input_SHA_only","reviewed_utc":datetime.now(timezone.utc).isoformat(),"authorization_validated":False,"submission_authorized":False,"candidate_gateway_run_called":False,"Slurm_queries_or_submission":False,"production_state_written":False,"weights_deserialized":False,"raw_rebuild_seconds":raw_seconds,"native_input_hash_seconds":native_seconds,"prior_jobs":rows,"historical_GPU_seconds":6596,"current_completed":{"A":500,"B":500},"next_sample_cursor":{"A":4000,"B":4000},"future_requested_target_only":5000,"scientific_projection_exactly_preserved":True,"server_input_verification":native,"root_review":a.ROOT_REVIEW,"independent_recovery_review":a.INDEPENDENT,"read_evidence_sha256":dict(science.e.hashes),"protected_source_sha256":before,"candidate_source_sha256":pins,"context_ref":ref,"limitations":["Read-only candidate scientific preparation is not the typed root authorization gate.","Server input/resume files were hashed; no optimizer/RNG/tensors loaded. Frozen training core validates them at actual resume.","No new GPU execution, Slurm query, global capacity proof or submission occurred. Existing Spatial reservation is not consumed."]}
out["read_evidence_sha256"].update({p.relative_to(R).as_posix():sha(p) for p in [Path(__file__),ctx,C/"gateway.py",C/"admission.py"]})
with (D/"actual_readonly.json").open("xb") as f:f.write(a.canonical(out))
print(json.dumps({"status":out["status"],"read_refs":len(out["read_evidence_sha256"]),"server_inputs":len(native["server_files"]),"resume_arms":[x["arm"] for x in native["server_resume_checks"]],"historical_GPU_seconds":6596,"sha256":sha(D/"actual_readonly.json"),"raw_seconds":raw_seconds,"native_seconds":native_seconds}))
