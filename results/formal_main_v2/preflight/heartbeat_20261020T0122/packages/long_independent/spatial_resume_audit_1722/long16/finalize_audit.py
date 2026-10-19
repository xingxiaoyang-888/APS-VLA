"""Finalize a bounded science-plan audit; no planner rerun or production mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,xml.etree.ElementTree as ET
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B=R/".local/spatial_resume_audit_1722/long16"
A=R/".local/long_development_1722"
e={}
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(8<<20),b""):h.update(b)
 return h.hexdigest()
def track(path,expected=None):
 p=Path(path);p=R/p if not p.is_absolute() else p
 assert p.resolve()==p and (R in p.parents or P in p.parents)
 assert p.suffix.lower() not in (".pt",".pth",".bin",".safetensors",".ckpt")
 h=digest(p)
 if expected is not None:assert h==expected,(str(p),h,expected)
 key=p.relative_to(R).as_posix() if R in p.parents else str(p)
 assert key not in e or e[key]==h
 e[key]=h
 return p
def read(path,expected=None):return json.loads(track(path,expected).read_bytes())
def descriptor(path):
 p=track(path);return dict(path=p.relative_to(R).as_posix(),sha256=e[p.relative_to(R).as_posix()],bytes=p.stat().st_size)
def write(name,v):
 p=B/name
 with p.open("x",encoding="utf-8",newline="\n") as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
 return dict(path=p.relative_to(R).as_posix(),sha256=digest(p),bytes=p.stat().st_size)
raw=read(B/"science_reconstruction.json","18486173c6b89021c2591b35e62d0ce9bd15eaa43dcc0e11f70e587a9912857d")
for key,h in raw["read_evidence_sha256"].items():track(key,h)
assert raw["passed_checks"]==18 and all(x["status"]=="passed" for x in raw["checks"])
run=read(B/"science_a1.execution.json")
assert run["returncode"]==0
track(B/"science_a1.log",run["log_sha256"])
track(B/"audit_science_v2.py",run["entrypoint_sha256"])
track(B/"audit_science.py","296fb98310f40ad183a314349393faa9c5642520dee343a09087385a585ddb6e")
track(__file__)
track("results/formal_main_v2/control_transport/long16_independent_1722_a1.jsonl")
author=read(A/"candidate_review.json","79204acb7c06ff63d5471b9b1d395bb09c11ba3920923f5527a63cba3da59d0e")
track(A/"README.md","805e11e646042c3781698b64b8c6d6af2ecb71844c47ed5e90cbc2504887a16f")
archive=read(A/"final_delivery_files.json","8801e3fe823d90354287d3b9e7731e9853d1f9a3a82c768656effdeefda94cdc")
for row in archive["files"]:
 p=track(row["path"],row["sha256"]);assert p.stat().st_size==row["bytes"]
xml=ET.parse(track(A/"tests_a1.xml")).getroot()
suites=[xml] if xml.tag=="testsuite" else list(xml.iter("testsuite"))
author_counts={k:sum(int(n.attrib.get(k,0)) for n in suites) for k in ("tests","failures","errors","skipped")}
assert author_counts==dict(tests=31,failures=0,errors=0,skipped=0)
old=read("results/formal_main_v2/downstream_reviews/3019954.json","cde7e784bced622a6a30169af1f3c34ece8b710da8a6d65ab804454457c5d9ba")
assert old["completed_trials"]==old["expected_trials"]==600 and old["cost"]["all_attempt_gpu_seconds"]==10531
assert sum(x["gpus"]*x["elapsed_seconds"] for x in old["cost"]["allocations"])==10531
old_refs={}
for name in ("trials.jsonl","closed_loop_report.json"):
 rel=str(Path(old["run_root"]).relative_to(P)/name)
 expect=old["files"].get(rel)
 if expect is None:expect=old["evidence_sha256"].get(rel)
 assert isinstance(expect,str) and len(expect)==64,("old raw SHA missing",rel)
 track(rel,expect);track(P/rel,expect);old_refs[rel]=expect
projection=read(A/"runtime_science_input_projection.json","0b50a5b152f83a0488c17cc19e3d13c9674949e4939700df1b8cc11a1e40f62e")
expected={}
plans=[]
for row in raw["plans"]:
 p=read(row["scientific_plan"]["path"],row["scientific_plan"]["sha256"]);plans.append(p)
 for name,h in p["invocation"]["watched_files"].items():
  assert name not in expected or expected[name]==h;expected[name]=h
 for rel,h in p["publish_files"].items():
  name=str(P/rel);assert name not in expected or expected[name]==h;expected[name]=h
actual={x["server_path"]:x["sha256"] for x in projection["files"]}
assert len(actual)==len(projection["files"])==222 and actual==expected
for row in projection["files"]:
 p=track(row["local_path"],row["sha256"]);assert p.stat().st_size==row["bytes"]
assert projection["history_evidence_is_not_automatically_runtime_required"] is True
assert projection["checkpoint_data_included"] is False and projection["new_action_runtime_readiness_included"] is False
snapshot=read(raw["state_snapshot"]["path"],raw["state_snapshot"]["sha256"])
assert len(snapshot["registered_jobs"])==259 and snapshot.get("pending_submission") is None
missing=[x for x in raw["P_runtime_watches"] if x["status"]=="pending_root_publication"]
assert len(missing)==16
for x in missing:assert not Path(x["path"]).exists()
result=dict(schema="formal_main_v2",kind="Long16_fresh_development_plan_independent_CPU_review",
 status="passed_independent_scientific_plan_review",production_status="HOLD_PRODUCTION",
 review_role="independent",reviewed_utc=datetime.now(timezone.utc).isoformat(),
 author_review=descriptor(A/"candidate_review.json"),author_archive=descriptor(A/"final_delivery_files.json"),
 manifest_index=descriptor(A/"manifest_index.json"),plan_index=descriptor(A/"plan_index.json"),
 independently_reconstructed_plans=raw["plans"],source_files={k:v for k,v in e.items() if k in [
 ".local/long_development_1722/prepare.py","scripts/formal_execution_manifests.py","scripts/ops/formal_downstream_supervisor.py",
 "scripts/ops/formal_action_deployment_v1/contract.py","scripts/ops/formal_action_deployment_v1/runtime_scope.py"]},
 independent_execution=descriptor(B/"science_a1.execution.json"),independent_reconstruction=descriptor(B/"science_reconstruction.json"),
 independent_checks=18,independent_checks_passed=18,independent_seconds=raw["elapsed_seconds"],
 author_tests_parsed_not_rerun=author_counts,author_tests_do_not_count_as_independent_tests=True,
 fixture_boundary="8 positive original plans used real full registry, canonical R manifests and actual source/science validators. Only the 5 duplicate/overlap/pending/final negatives used in-memory mutations; no patched planner, fake sources, GPU or environment.",
 full_registry_count=259,registry_filtered=False,state_snapshot=raw["state_snapshot"],
 observed_state_before_sha256=raw["state_raw_sha256_at_start"],observed_state_after_sha256=raw["state_raw_sha256_at_end"],
 state_written=False,production_source_changed=False,source_R_and_S_173_exact=True,
 development=dict(suite="libero_10",method_ids=sorted(raw["checkpoint_identity_sources"]),selector_instances=16,
  shards=8,trials_per_shard=200,planned_trials=1600,unique_initial_states_per_method=100,
  common_panel={"path":"configs/manifests/formal_main_v2/libero_10/initial_states/development.json","sha256":e["configs/manifests/formal_main_v2/libero_10/initial_states/development.json"]},
  same_original_method_IDs=True,new_generation_or_registry_alias=False,environment=dict(max_steps=520,action_chunk=8,wait_steps=10,environment_seed=0,runtime_seed=17)),
 selected_checkpoint_identity=raw["checkpoint_identity_sources"],
 selected_checkpoint_bytes_independently_read=False,
 selected_checkpoint_bytes_evidence=descriptor("results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json"),
 old_Long_six=dict(completed_trials=600,all_allocation_GPU_seconds=10531,allocation_ids=old["raw_invocation_job_ids"],
  root_review=descriptor("results/formal_main_v2/downstream_reviews/3019954.json"),raw_R_and_P_SHA=old_refs,
  semantics_not_relabelled=True,new_action_identity_status="HOLD_SEPARATE_REGISTRATION_REQUIRED"),
 original_runtime_projection={"ref":descriptor(A/"runtime_science_input_projection.json"),"files":222,"derived_from":"exact union of unchanged original watched_files and publish_files"},
 missing_P_runtime_inputs=missing,new_action_runtime_contract_checked=raw["new_runtime_contract"],
 blockers_for_current_scientific_plan=[],
 required_before_any_submission=[
 "Create and independently review one exact new-action effective plan/contract per shard; do not execute these original v1 scientific plans as new action identity.",
 "Root must issue exact development-only runtime readiness and prepared invocation, with real canonical root/independent references; none is generated or approved by this audit.",
 "Publish full P runtime closure, including the 8 absent pair configs and 8 canonical manifests listed here, then verify unmodified wrapper against actual P.",
 "Refresh full live registry, checkpoint identities, shared lock/CAS, exact authorization, reservation ownership, all-mode capacity<=8 and durable pending; this snapshot is not a future submission admission."
 ],
 no_claims=["No new trials/GPU execution or success-rate/latency claim.","No guarantee 200 trials finish in4h; failures and full actual costs must remain.",
  "No O2A/freeze/final release or completion of all22 new-action methods.","No readiness, root authorization, reservation, state mutation, P publication or Slurm query/submission."],
 preparation_notes=["Initial audit_science.py was never executed; before execution its source_index lookup was corrected to the actual source_state_index field in separately saved audit_science_v2.py.",
  "The independent execution passed on its first actual run; the author's earlier transport-path rejection and unrun test draft are retained in its immutable archive.",
  "A tool-side JavaScript btoa ReferenceError happened before any remote write/execution; no scientific/test outcome resulted."],
 read_evidence_sha256=dict(sorted(e.items())))
print(json.dumps({"independent_review":write("independent_review.json",result),"read_evidence_count":len(e)},ensure_ascii=False))
