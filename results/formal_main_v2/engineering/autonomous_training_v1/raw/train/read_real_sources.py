"""Read actual immutable identities only; does not admit/submit any pair."""
import hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("readiness_execution",HERE/"execution.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
R=m.CONTROL_ROOT
e=m.Evidence(R)
inherited_path="results/formal_main_v2/preflight/autonomous_execution_v1/inherited_training_GPU_evidence_root.json"
inherited_sha="39689af6ed5d8c4e5bf62e84b35c9da40893975c2d917e3a7eba9789a71354b1"
inherited=e.read(inherited_path,inherited_sha)
assert inherited["status"]=="passed_identity_recheck_no_new_GPU_test"
assert inherited["source173_unchanged_R_S"] is True and inherited["completed_arms"]==28
gates=[]
for suite in ("libero_10","libero_spatial","libero_object","libero_goal"):
    path=f"results/formal_main_v2/{suite}/acceptance/root_review.json"
    gates.append(e.read(path))
jobs=[g["job_at_review"] for g in gates]
summary=[]
for g in gates:
    suite=g["suite"]
    _,pair,_,inventory=m.context(e,suite+"_k128_seed17")
    checked=m._gate(e,pair,jobs,dict(mode="resume"))
    assert checked==g
    assert inherited["suites"][suite]["acceptance"]==dict(path=f"results/formal_main_v2/{suite}/acceptance/root_review.json",sha256=e.watch(f"results/formal_main_v2/{suite}/acceptance/root_review.json"))
    for field in ("runtime_compatibility","component_compatibility"):
        if field in checked:
            for rel,expected in checked[field]["files"].items():
                assert m.sha(Path(m.P)/rel)==expected
    summary.append(dict(suite=suite,job_id=g["job_id"],counts=g["reviewed_counts"],
                        metadata="runtime_compatibility" in g,component="component_compatibility" in g))
for rel,expected in inventory["files"].items():
    assert m.sha(Path(m.SOURCE)/rel)==expected
for name in ("execution.py","test_execution.py","read_real_sources.py"):
    e.watch(str((HERE/name).relative_to(R)))
e.unchanged()
result=dict(schema=m.SCHEMA,kind="autonomous_training_candidate_source_readiness",status="passed_read_only_identity_check",
    source173_R_S_exact=True,suites=summary,inherited_GPU_evidence=dict(path=inherited_path,sha256=inherited_sha),
    completed_arms_reused=inherited["completed_arms"],new_GPU_seconds=0,models_loaded=False,weights_read=False,
    actual_training_admitted=False,state_read_or_written=False,scientific_reviewer_replaced=False,
    read_evidence_sha256=e.hashes)
with (HERE/"real_source_readiness.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
print(json.dumps(dict(status=result["status"],refs=len(e.hashes),suites=summary)))
