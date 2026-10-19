from pathlib import Path
import ast, hashlib, importlib.util, json, difflib
from datetime import datetime, timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/cuda_recovery_independent_0943"
read={}
def watch(p):
    p=Path(p)
    if not p.is_absolute(): p=R/p
    raw=p.read_bytes(); rel=p.relative_to(R).as_posix()
    h=hashlib.sha256(raw).hexdigest()
    if rel in read: assert read[rel]==h
    read[rel]=h
    return raw
def load(p): return json.loads(watch(p))
source=".local/cuda_terminal_review_0943/review_formal_segment_startup.py"
assert hashlib.sha256(watch(source)).hexdigest()=="ee0efc4b762e879e91e5e184fbc33dc236741cf71d51a6f5b4711710812f47b4"
old=".local/cuda_startup_recovery_0840/review_formal_segment_startup.py"
assert hashlib.sha256(watch(old)).hexdigest()=="a06069b9139d24e9ac35944559fa0918afce62a4c58d57adee63ace2c3776f4a"
before=".local/cuda_terminal_review_0943/before_schema_fix.py"
watch(before)
for rel in [".local/cuda_terminal_review_0943/startup_failure_evidence.py",
            ".local/cuda_startup_recovery_0840/startup_failure_evidence.py",
            "scripts/review_formal_acceptance.py"]:
    watch(rel)
spec=importlib.util.spec_from_file_location("audited_ownership",R/source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
e=m.Evidence(R)
local_rel=".local/cuda_terminal_review_0943/actual_local_review.json"
actual=e.read(local_rel)
assert e.watch(local_rel)=="9d8c57dd948172d1a51afb5dee674e4bc06122246c41e78072936f5d97965801"
pull="results/formal_main_v2/pulls/20261019T095542Z_e5d54e39d3ae/receipt.json"
assert e.watch(pull)=="8cf02df4314a103db61824fbf64a238994a1572757bc443682ab6d5d319be0e8"
jobs={str(x["job_id"]):x for x in actual["registered_pair_jobs_at_review"]}
ownership=m.require_pulled_startup_ownership(e,pull,jobs["3039258"],list(actual["files"]),jobs,actual["startup_failure_history"])
assert ownership==actual["startup_pull_ownership"] and len(ownership)==3
e.unchanged()
for rel,h in e.hashes.items():
    assert hashlib.sha256(watch(rel)).hexdigest()==h
inventory=load("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json")
assert len(inventory["files"])==173
for rel,h in inventory["files"].items():
    assert hashlib.sha256(watch(rel)).hexdigest()==h
proof_files=["test_startup_pull_partition.py","partition_tests.xml","partition_tests.log","partition_test_run.json",
             "test_startup_pull_partition_v2.py","partition_tests_v2.xml","partition_tests_v2.log","partition_test_run_v2.json"]
for name in proof_files: watch(D/name)
run1=load(D/"partition_test_run.json");run2=load(D/"partition_test_run_v2.json")
assert run1["exit_code"]==1 and run2["exit_code"]==0
watch(__file__)
result=dict(schema="formal_main_v2",kind="startup_pull_ownership_independent_CPU_review",
    status="passed_CPU_review",reviewed_utc=datetime.now(timezone.utc).isoformat(),
    candidate=dict(path=source,sha256=read[source]),
    original=dict(path=old,sha256=read[old]),
    exact_diff_scope=["One exact three-file per failed-job ownership partition",
                     "Current and shared run-root files still use original require_pulled",
                     "Explicit startup_pull_ownership field retained and immutable-existing-review compared"],
    findings_resolved=[dict(issue="Initial proposed selected-job invocation_sha256 check required a field absent from the real pull writer",
             resolution="Current patch binds actual old invocation SHA through full registered job plus original canonical verifier; selected/registered projections stay unmodified")],
    actual_read_only=dict(pull=pull,ownership=ownership,canonical_failure_reconstructed=True,
         actual_invocation_sha_bound=True,old_status="FAILED",old_exit_code="1:0",old_gpu_seconds=84,
         current_status="COMPLETED",current_exit_code="0:0",current_gpu_seconds=6512,
         total_pair_allocated_gpu_seconds=6596,current_and_history_inventory_unchanged=True),
    tests=dict(final_passed=33,final_failed=0,final_junit_seconds=2.56,
        initial_passed=32,initial_failed=1,initial_failure_scope="Synthetic fixture list rebinding retained the original closure; only fixture corrected",
        original_require_pulled_executed=True,
        synthetic_canonical_oracle_only=True,
        real_case_original_canonical_verifier_executed=True,
        commands=[run1["command"],run2["command"]]),
    frozen_source_files_checked=173,
    limitations=["This review accepts only the narrow CPU evidence-consumer correction.",
                 "It does not sign the actual terminal training recovery; that awaits root server-resume review and independent raw recomputation.",
                 "No new GPU execution, submission, production state change, tensor loading or final-state access.",
                 "No automatic 5000 admission, failed-record deletion or original target change."],
    read_evidence_sha256=dict(sorted(read.items())))
for rel,h in read.items(): assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,rel
out=D/"ownership_patch_independent_review.json"
with out.open("x") as f:json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
print(json.dumps(dict(path=str(out),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),evidence_files=len(read),status=result["status"])))
