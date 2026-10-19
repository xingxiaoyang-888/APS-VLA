"""Server-only read-only independent evidence aggregation; writes only own audit directory."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,xml.etree.ElementTree as ET
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
S=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA/snapshots/formal_main_v2_run_564be0995e")
D=R/".local/action_deployment_chain_independent_0809"
evidence={}
def record(path,expected=None):
    p=Path(path)
    if not p.is_absolute():p=R/p
    assert R in p.parents or S.parent.parent in p.parents,str(p)
    assert p.resolve()==p and p.is_file(),str(p)
    assert not any("sealed" in part.lower() for part in p.parts)
    assert p.suffix.lower() not in {".pt",".pth",".bin",".ckpt",".safetensors",".pkl",".pickle",".pruned_init",".init"}
    raw=p.read_bytes();got=hashlib.sha256(raw).hexdigest()
    if expected is not None:assert got==expected,(str(p),got,expected)
    evidence[str(p)]=got
    return raw
def get(path,expected=None):return json.loads(record(path,expected))
before=get(D/"source_before.json")
for rel,digest in before.items():record(rel,digest)
author=get(".local/action_deployment_runtime_0809/candidate_review.json",before[".local/action_deployment_runtime_0809/candidate_review.json"])
for path,digest in author["evidence_sha256"].items():record(path,digest)
inventory=get("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
assert len(inventory["files"])==173
for rel,digest in inventory["files"].items():
    record(R/rel,digest);record(S/rel,digest)
root_author=get(".local/action_downstream_integration_0809/candidate_review.json")
for rel,digest in root_author["source_files"].items():record(rel,digest)
for row in root_author["test_results"]:
    cmd=get(row["path"],row["sha256"])
    assert cmd.get("returncode")==0,cmd
    stem=Path(row["path"]).name.replace(".execution.json","")
    for suffix in ("stdout","stderr"):
        record(Path(row["path"]).with_name(stem+"."+suffix))
record("SERVER_WORKSPACE.md");record("docs/服务器工作区与GitHub同步.md")
record("scripts/server/run_formal_downstream.py","f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24")
record("scripts/ops/formal_evaluation_adapter.py","b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd")
record("results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/3039197/action_execution_identity.json")
for name in ("test_independent.py","pytest_a1.xml","pytest_a1.stdout","pytest_a1.stderr","pytest_a1.execution.json","audit.py",
    "audit_a1.py.txt","audit_a1.stdout","audit_a1.stderr","audit_a1.execution.json","audit_aggregation_fix.json"):
    record(D/name)
run=get(D/"pytest_a1.execution.json")
assert run["returncode"]==0 and run["source_sha256"]==before
assert run["test_sha256"]==evidence[str(D/"test_independent.py")]
tree=ET.fromstring(record(D/"pytest_a1.xml"))
suites=list(tree.iter("testsuite"));assert len(suites)==1
suite=suites[0].attrib
assert [int(suite[k]) for k in ("tests","failures","errors","skipped")]==[20,0,0,0],suite
source_after={rel:hashlib.sha256((R/rel).read_bytes()).hexdigest() for rel in before}
assert before==source_after
(D/"source_after.json").write_text(json.dumps(source_after,sort_keys=True,indent=2)+"\n")
record(D/"source_after.json")
# Verify author claimed full test result independently, without rerunning it.
tree2=ET.fromstring(record(author["tests"]["final_xml"]))
asuite=list(tree2.iter("testsuite"))[0].attrib
assert [int(asuite[k]) for k in ("tests","failures","errors","skipped")]==[90,0,0,0]
files={rel:before[rel] for rel in before if rel.endswith(("/runtime.py","/contract.py","/wrapper.py","/entry.py"))}
report=dict(schema="formal_main_v2",kind="formal_action_runtime_and_entry_independent_CPU_review",
    version="action-deployment-runtime-entry-independent-0809-v1",
    status="passed_CPU_independent_candidate_review",review_role="independent",reviewer="train64",
    reviewed_utc=datetime.now(timezone.utc).isoformat(),execution_version="formal-downstream-action-v1",
    files=files,production_chain_complete=False,scientific_settings_changed=False,final_evaluation_enabled=False,
    root_activation=False,Slurm_submissions=0,new_GPU_calls=0,production_state_writes=0,Git_operations=0,
    no_unresolved_CPU_blockers=True,
    tests=dict(independent_passed=20,failed=0,errors=0,skipped=0,pytest_seconds=float(suite["time"]),
        process_seconds=run["seconds"],command=run["command"],cwd=run["cwd"],
        test_source_sha256=run["test_sha256"],
        author_runtime_90_rehashed_not_rerun=True,root_author_contract19_wrapper9_rehashed_not_rerun=True),
    actual_production_code_exercised=[
        "Runtime.make_contract/validate_contract over real nonweight source and engineering acceptance refs; both R/S 173 exact bytes.",
        "Frozen timing endpoint plus scoped validator: amplitude clause removed only; shape/finite/deployed identity guards and action bytes unchanged.",
        "Derived one-base lifecycle from actual v4 plus actual frozen minimal-Prismatic installer; synthetic model loader, second-call/caught-failure poison and exact restoration.",
        "Actual root entry.main durable sequence/LF/fsync writer and unchanged old atomic publisher; same original-run call argument API and completion evidence.",
        "Actual runtime.verify_runtime_events on explicitly synthetic structural events within entry: incomplete runtime and corrupted restored status fail.",
        "Actual new parent verify rejects missing/incomplete/final-enabled readiness before loading scientific execution.",
        "Actual converter exact-two all-suite resume partition; config/panel remain post-run immutable and old inputs unmodified."],
    explicit_synthetic_boundaries=[
        "Entry tests relocate P into this audit's isolated directory and use synthetic Slurm ID; no production invocation or state exists.",
        "Entry tests replace upstream scientific wrapper.verify and GPU/environment legacy.run; use declared author synthetic event generator with actual accepted action identity only as CPU fixture material.",
        "The entry fixture retains actual durable writer, pure runtime structural validator, source-file checks and exact old publish implementation. It does not validate a real new scientific trial or timing result.",
        "Lifecycle test uses synthetic tensor/model load and real minimal installer; no checkpoint tensor or CUDA call.",
        "These independent checks plus source inspection do not alone issue typed runtime_readiness or assert whole new-version producer/reviewer/consumer production chain complete."],
    findings=[
        "No unresolved CPU blocker found in the four reviewed files at exact listed SHAs.",
        "Parent/entry bind actual new version; original v1 plan validation is a scientific-input check, not a forged old execution proof.",
        "Development resume pre-run checks exactly current trials.jsonl and closed_loop_report.json; prior root/pull evidence and other immutable files remain required.",
        "Action adapter and frozen model/policy/trial/timing algorithm sources remain exact originals; new scope does not clip/transform queued actions.",
        "Final stage is rejected before metadata/path reads by runtime and converter; no final values were read.",
        "Failures/duplicate attempts remain recorded/refused. Returned wrapper/runtime proof is not scientific completion or root activation."],
    source_before=before,source_after=source_after,source_173_R_and_S_match=True,
    evidence_sha256=dict(sorted(evidence.items())),read_evidence_sha256=dict(sorted(evidence.items())))
path=D/"independent_review.json"
assert not path.exists()
path.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),evidence_count=len(evidence),
    files=files,tests=report["tests"]),ensure_ascii=False))
