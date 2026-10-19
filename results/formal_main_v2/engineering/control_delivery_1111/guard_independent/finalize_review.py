"""Write bounded independent CPU audit receipts; never changes production."""
from pathlib import Path
import hashlib,json,datetime,xml.etree.ElementTree as ET
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
C=R/".local/action_mixed_prefix_guard_1111"
D=R/".local/action_mixed_prefix_independent_1111"
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_new(name,value):
    p=D/name
    with p.open("xb") as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
    return {"path":p.relative_to(R).as_posix(),"sha256":digest(p),"bytes":p.stat().st_size}
pins={
"reviewer.py":"843f0336fd4161eb23d512b34935c7fca7d75032aceefe86084a16a7939a642c",
"consumer.py":"b3f754557646c8e5fa6172fd8a1bcded7e246bbfb4c490502bdc1e3f73e21b31",
"test_guard.py":"d3e3f49ded661cb236caead9d7b0a0fd4dc940cef5853405c3be19332dcc8990",
"candidate_review.json":"a3232e8db5162725ed24cbb15de770f789b58769ac06a30e382933bfe81ceb8f",
"archive_closure.json":"76635436c51bcce97bca1e3339644b5e1b1bc2a470370a3fa7fec904ceb35dc3"}
for n,h in pins.items():assert digest(C/n)==h,n
before=json.loads((D/"inputs_before.json").read_bytes())
after={n:digest(n) for n in before["read_evidence_sha256"]}
assert after==before["read_evidence_sha256"]
after_ref=write_new("inputs_after.json",{
"schema":"formal_main_v2","kind":"independent_protected_input_snapshot",
"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"all_before_refs_unchanged":True,"frozen_files_per_root":173,"approved_runtime_files":7,
"read_evidence_sha256":after})
extra={
".local/action_downstream_consumers_0809/reviewer.py":"scripts/ops/formal_action_deployment_v1/reviewer.py",
".local/action_downstream_consumers_0809/consumer.py":"scripts/ops/formal_action_deployment_v1/consumer.py",
".local/action_deployment_runtime_0809/runtime.py":"scripts/ops/formal_action_deployment_v1/runtime_scope.py"}
equivalent={}
for p,q in extra.items():
    a,b=digest(R/p),digest(R/q);assert a==b,(p,q)
    equivalent[p]={"sha256":a,"same_bytes_as":q}
    after[str(R/p)]=a;after[str(R/q)]=b
upstream={
"scripts/review_formal_downstream.py":"753edb55ce21fd43f85499e136a7e52093ecf9feaeafadf0f01cece8fa267202",
"scripts/ops/formal_downstream_supervisor.py":"f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571",
"scripts/formal_execution_manifests.py":"614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89",
"scripts/analyze_formal.py":"7f9573877f8a3662bd06dae9362823fd478283ed14cc86a6c3763f6fb4f682f1",
"scripts/ops/formal_asset_downstream_review.py":"6d9af87498c76cc71459d5441e66eff2a2bde9aa063479519a4d628f44a7d699",
"scripts/ops/formal_evaluation_adapter.py":"b54dc0d87cbc10c639b0cf59475011f7a68809999862c14ebf02393e96764acd",
"scripts/server/run_formal_downstream.py":"f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24"}
for n,h in upstream.items():assert digest(R/n)==h,n;after[str(R/n)]=h
dep_ref=write_new("fixture_source_identity.json",{
"schema":"formal_main_v2","kind":"CPU_fixture_dependency_identity","private_fixture_implementation_same_bytes":equivalent,
"exact_upstream_pins_rechecked":upstream,
"claim":"Only candidate scope and raw scientific/parser serialization are exercised. This is not a real runtime readiness or GPU proof."})
root=ET.parse(D/"pytest_a1.xml").getroot()
suites=[root] if root.tag=="testsuite" else list(root.iter("testsuite"))
counts={k:sum(int(s.get(k,0)) for s in suites) for k in ["tests","failures","errors","skipped"]}
assert counts==dict(tests=13,failures=0,errors=0,skipped=0),counts
command=json.loads((D/"pytest_a1_command.json").read_bytes())
assert command["returncode"]==0 and command["test_sha256"]==digest(D/"test_independent.py")
author=json.loads((C/"candidate_review.json").read_bytes())
assert author["CPU_tests"]["tests"]==23 and author["CPU_tests"]["failures"]==0
evidence=dict(after)
for n in ["test_independent.py","finalize_review.py","pytest_a1.xml","pytest_a1.log","pytest_a1_command.json","inputs_before.json","inputs_after.json","fixture_source_identity.json"]:
    evidence[str(D/n)]=digest(D/n)
findings=[
"Current root must be rebuilt by the original consumer before ancestry inspection; SHA-bound ancestors are immutable metadata, not re-read from appended mutable old output.",
"Every ancestor is required to use the exact current execution version, same run/stage/manifest, source/runtime semantic identity and explicit historical marker.",
"Transitive old->new->new lineage is rejected before full/components consumption and before release_global; no equivalence exception is inferred or supported.",
"The original O2A function code and original release_global(release=False) gate remain preserved; publication alone does not activate this guard.",
"Partial current-runtime raw results remain incomplete; cache keys include the complete argument set and cached evidence is rehashed before reuse."]
receipt={
"schema":"formal_main_v2","kind":"formal_action_mixed_prefix_guard_independent_CPU_review",
"version":"mixed-prefix-independent-1111-v1","status":"passed_CPU_review","review_role":"independent",
"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
"files":{"scripts/ops/formal_action_consumption_guard_v1/reviewer.py":pins["reviewer.py"],
"scripts/ops/formal_action_consumption_guard_v1/consumer.py":pins["consumer.py"]},
"physical_candidate_files":{str(C/n):pins[n] for n in ["reviewer.py","consumer.py"]},
"author_review":{"path":(C/"candidate_review.json").relative_to(R).as_posix(),"sha256":pins["candidate_review.json"]},
"author_tests":{"count":23,"independently_rerun":False,"original_global_release_88_identity_fixture":"author evidence only; original helper used release=False"},
"independent_tests":{**counts,"pytest_reported_seconds":19.37,"junit_seconds":sum(float(s.get("time",0)) for s in suites),"command":command,
"coverage":["real legacy inner writer and original raw-science reconstruction shape under declared fixture stand-ins",
"deep legacy ancestor blocks O2A before any full/components read",
"rehashed ancestor root/marker/semantics/hidden-history corruption",
"independent transition prefix mismatch after coherent reference rebinding",
"runtime source pin mismatch despite internally rehashed semantic signature",
"cache cannot promote partial completion or hide later raw byte drift",
"byte-identical relocation and pinned guard/upstream source rejection",
"legacy ancestry rejects before any global release helper"],
"standins":["author setup only is reused; independent assertions and faults are in this audit source",
"metadata-only ancestry tests stub upstream raw reconstruction explicitly",
"the one real-format writer/reviewer fixture uses synthetic training/checkpoint/readiness admission and synthetic outer runtime journal; GPU/environment/runtime restore verification is a stand-in",
"no author or independent synthetic receipt is treated as real development, O2A, checkpoint or release evidence"]},
"source_checks":{"pre_and_post_refs":len(before["read_evidence_sha256"]),"all_unchanged":True,
"frozen_R_files":173,"frozen_S_files":173,"approved_runtime_R_files":7,
"private_fixture_sources_same_as_canonical":equivalent},
"findings":findings,"blockers":[],
"authorization_limits":{"byte_identical_relocation_only":True,"production_activation":False,"production_chain_complete":False,
"actual_new_development_results_audited":0,"actual_O2A_join_verified":False,"GPU_execution":False,
"equivalence_inferred":False,"final_release":False,"Slurm_submitted":False,"production_state_written":False,
"production_source_written":False,"Git_written":False,"P_written":False,"sealed_values_read":False,"weights_read":False},
"remaining":["Root may only integrate these exact bytes under a separate explicit invocation contract.",
"All complete real development/full/components evidence and original scientific gates remain required.",
"Mixed legacy prefixes continue to block later O2A/global freeze; a future equivalence protocol would require separate registration and independent review."],
"read_evidence_sha256":dict(sorted(evidence.items()))}
ref=write_new("independent_review.json",receipt)
names=["test_independent.py","finalize_review.py","pytest_a1.xml","pytest_a1.log","pytest_a1_command.json","inputs_before.json","inputs_after.json","fixture_source_identity.json","independent_review.json"]
files={n:{"sha256":digest(D/n),"bytes":(D/n).stat().st_size} for n in names}
archive=write_new("archive_closure.json",{"schema":"formal_main_v2","kind":"independent_audit_archive_closure",
"relative_root":D.relative_to(R).as_posix(),"files":files,"total_bytes":sum(x["bytes"] for x in files.values()),
"excluded":["pytest_a1_tmp/** and tmp/** are regenerable synthetic fixtures and are not immutable audit inputs"],
"upstream_author_closure":{"path":(C/"archive_closure.json").relative_to(R).as_posix(),"sha256":pins["archive_closure.json"]},
"extra_fixture_sources_referenced":equivalent})
print(json.dumps({"review":ref,"archive":archive,"evidence_count":len(evidence),"protected_refs":len(before["read_evidence_sha256"]),"tests":counts,"archive_total_bytes":sum(x["bytes"] for x in files.values())}))
