"""CPU-only ancestry gates.

Actual v1 raw writer/reviewer supplies the positive report shape. Training, GPU
runtime and readiness are explicit inherited fixture stand-ins. Synthetic chain
and freeze metadata test consumers only: never production receipts or GPU proof.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

R = Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
HERE = Path(__file__).parent
NEW = "scripts/ops/formal_action_consumption_guard_v1/"
sys.path[:0] = [str(R / "src"), str(R / "tests")]

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

ORIGINAL_TEST = load(R / ".local/action_downstream_consumers_0809/test_consumers.py", "prefix_original_fixture")
BASE = load(R / "scripts/ops/formal_action_deployment_v1/reviewer.py", "prefix_original_raw")
ORIGINAL = load(R / "scripts/ops/formal_action_deployment_v1/consumer.py", "prefix_original_consumer")

def save(root, name, value):
    path = root / name; path.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    path.write_bytes(raw)
    return {"path": name, "sha256": hashlib.sha256(raw).hexdigest()}

def install(root):
    for name in ("reviewer.py", "consumer.py"):
        save(root, NEW + name, (HERE / name).read_bytes())
    for name in BASE.PINNED:
        save(root, name, (R / name).read_bytes())
    for name in (BASE.REVIEWER, BASE.CONSUMER):
        save(root, name, (R / name).read_bytes())
    tag = hashlib.sha256(str(root).encode()).hexdigest()[:12]
    return (load(root / (NEW + "reviewer.py"), "prefix_guard_" + tag),
            load(root / (NEW + "consumer.py"), "prefix_consumer_" + tag))

@pytest.fixture(scope="module")
def actual_v1(tmp_path_factory):
    root = tmp_path_factory.mktemp("actual_v1_writer")
    monkeypatch = pytest.MonkeyPatch()
    original_save = ORIGINAL_TEST.save
    def construct_contract(project, name, value):
        # The old fixture omitted this envelope field because it stubs envelope
        # admission. Supply the actual registered field BEFORE writer/review;
        # do not manufacture a successful reviewer output after the fact.
        if name == "results/formal_main_v2/preflight/new-contract.json":
            value["version"] = BASE.VERSION
        return original_save(project, name, value)
    monkeypatch.setattr(ORIGINAL_TEST, "save", construct_contract)
    ng, nc, p, a, invref, contractref, parentpath, writer = ORIGINAL_TEST.layered_writer_fixture(root, monkeypatch)
    pullref = {"path": a.pull_relative, "sha256": ng.digest(root / a.pull_relative)}
    report = ng.review(root, job=a.job, invocation_ref=invref, pull_ref=pullref,
        registered_jobs=p.state["registered_jobs"], expected_contract_ref=contractref)
    reference = save(root, a.review_relative, report)
    rebuilt = nc.review_downstream_output(ng.Evidence(root), reference,
        expected_stage="development", suite="libero_10", require_complete=False)
    assert report["kind"] == "root_downstream_review" and report["scientific_complete"] is False
    assert rebuilt["files"] == report["files"] and rebuilt["cost"] == report["cost"]
    yield SimpleNamespace(root=root, ng=ng, nc=nc, report=report, rebuilt=rebuilt, reference=reference,
        invocation=deepcopy(a.inv), contract=json.loads((root / contractref["path"]).read_bytes()))
    monkeypatch.undo()


def chain(root, template, *, depth=1, suite="libero_10", legacy_leaf=False, output=None, provenance=None):
    """Explicit synthetic metadata chains shaped from actual v1 review output."""
    output = output or "results/formal_main_v2/" + suite + "/development/synthetic"
    remote = str(BASE.P / output); stage = suite + "_development_synthetic"
    manifest = "a" * 64
    contract_template = deepcopy(template.contract)
    contract_template["runtime_contract"]["suite"] = suite
    semantics = BASE.semantic_identity(contract_template)
    prior_ref = prior = None
    files = {output + "/" + name: hashlib.sha256((name + suite).encode()).hexdigest()
        for name in ("trials.jsonl", "closed_loop_report.json", "config.json", "panel.json")}
    for n in range(depth):
        contract = deepcopy(contract_template); contract["transition"] = None
        inv = deepcopy(template.invocation)
        inv.update(schema="formal_main_v2", kind="formal_downstream_invocation", version=BASE.VERSION,
            stage="development", suite=suite, run_root=remote, stage_key=stage,
            execution_manifest_sha256=manifest, resume=bool(n), prior_review=None,
            prior_job_ids=[], root_evidence_sha256={})
        historical = None
        if n:
            transition = dict(schema="formal_main_v2",kind="formal_action_runtime_transition",status="root_reviewed",
                from_version=prior.get("execution_version", "formal-downstream-root-v1"), to_version=BASE.VERSION,
                run_root=remote,stage_key=stage,execution_manifest_sha256=manifest,
                terminal_trials_repeated=False,prior_outcomes_replaced=False,new_trial_ids_only=True,
                prior_review=prior_ref["path"],prior_job_ids=[str(n-1)],files=files)
            independent = dict(kind="formal_action_runtime_transition_review",status="passed",review_role="independent",
                stage_key=stage, files=files, prior_review=prior_ref["path"],
                from_version=transition["from_version"],to_version=BASE.VERSION)
            transition["independent_review"] = save(root, f"results/formal_main_v2/preflight/{suite}_{n}_ind.json", independent)
            tref = save(root, f"results/formal_main_v2/preflight/{suite}_{n}_transition.json", transition)
            contract["transition"] = tref
            inv.update(prior_review=prior_ref["path"], prior_job_ids=[str(n-1)],
                root_evidence_sha256={prior_ref["path"]: prior_ref["sha256"]})
            historical = dict(reference=tref,from_version=transition["from_version"],preserved_prefix_bytes=10,
                preserved_prefix_sha256=files[output + "/trials.jsonl"],historical_terminal_outcomes_replaced=False)
        cref = save(root, f"results/formal_main_v2/preflight/{suite}_{n}_contract.json", contract)
        inv["action_execution_contract"] = cref
        iref = save(root, f"results/formal_main_v2/invocations/{suite}_{n}.json", inv)
        report = deepcopy(template.report)
        report.update(schema="formal_main_v2",kind="root_downstream_review",status="passed",reviewed_by="root",
            stage="development",suite=suite,run_root=remote,stage_key=stage,execution_manifest_sha256=manifest,
            invocation=iref["path"], invocation_sha256=iref["sha256"],invocation_ref=iref,
            action_execution_contract=cref,action_semantics_sha256=semantics,historical_transition=historical,
            execution_version=BASE.VERSION,files=files,scientific_complete=True)
        if provenance is not None: report["source_provenance"] = deepcopy(provenance)
        else: report["source_provenance"]["suite"] = suite
        if n == 0 and legacy_leaf: report.pop("execution_version")
        prior_ref = save(root, f"results/formal_main_v2/downstream_reviews/{suite}_{n}.json", report)
        prior = report
    return prior_ref, report


def scoped(root, monkeypatch, reports):
    guard, consumer = install(root)
    calls = []
    def reconstruction(ev, reference, **kwargs):
        # Explicit upstream reconstruction stand-in for metadata-only fault tests.
        calls.append((reference["path"], deepcopy(kwargs)))
        value = reports[reference["path"]]
        if kwargs.get("require_complete", True) and value.get("scientific_complete") is not True:
            raise ValueError("Synthetic incomplete root")
        return deepcopy(value)
    upstream = SimpleNamespace(review_downstream_output=reconstruction,
        require_matching_o2a=ORIGINAL.require_matching_o2a)
    monkeypatch.setattr(guard, "upstreams", lambda ev: (BASE, upstream))
    monkeypatch.setattr(consumer, "_guard", lambda ev: guard)
    return guard, consumer, calls


def test_positive_original_v1_raw_report_and_partial_completion(actual_v1, monkeypatch):
    v = actual_v1; guard, consumer = install(v.root)
    monkeypatch.setattr(guard,"upstreams",lambda ev:(v.ng,v.nc))
    monkeypatch.setattr(consumer,"_guard",lambda ev:guard)
    ev=v.ng.Evidence(v.root)
    _,_,consume,proofs=guard.guarded_consumer(ev)
    report=consume(ev,v.reference,expected_stage="development",suite="libero_10",require_complete=False)
    assert report == v.rebuilt or {k:x for k,x in report.items() if k!='reviewed_utc'} == {k:x for k,x in v.rebuilt.items() if k!='reviewed_utc'}
    assert len(proofs)==1 and len(proofs[0]["chain"])==1
    assert proofs[0]["legacy_prefix_equivalence_inferred"] is False
    # Actual incomplete raw result remains ineligible, despite current semantics.
    with pytest.raises(ValueError):
        consumer.require_matching_o2a(v.ng.Evidence(v.root),[v.reference],{}, {},suite="libero_10")

@pytest.mark.parametrize("depth",[1,2,3])
def test_current_only_metadata_ancestry(tmp_path,actual_v1,depth):
    guard,_=install(tmp_path); ref,report=chain(tmp_path,actual_v1,depth=depth)
    result=guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")
    assert len(result["chain"])==depth and result["exception_receipts_supported"] is False

@pytest.mark.parametrize("depth",[1,2,3])
def test_old_leaf_rejected_through_complete_chain(tmp_path,actual_v1,depth):
    guard,_=install(tmp_path); ref,report=chain(tmp_path,actual_v1,depth=depth,legacy_leaf=True)
    with pytest.raises(ValueError,match="Unresolved legacy"):
        guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")

@pytest.mark.parametrize("mutation",["unknown_version","missing_marker","semantics","completion","equivalence","resolution","invocation_sha","contract_sha"])
def test_tampered_top_receipts_rejected(tmp_path,actual_v1,mutation):
    guard,_=install(tmp_path);ref,report=chain(tmp_path,actual_v1,depth=2)
    if mutation=="unknown_version":report["execution_version"]="unknown-newer-version"
    elif mutation=="missing_marker":report.pop("historical_transition")
    elif mutation=="semantics":report["action_semantics_sha256"]="b"*64
    elif mutation=="completion":report.pop("scientific_complete")
    elif mutation=="equivalence":report["historical_equivalence"]={"path":"unregistered.json","sha256":"1"*64}
    elif mutation=="resolution":report["separate_treatment_resolution"]=True
    elif mutation=="invocation_sha":report["invocation_ref"]["sha256"]="c"*64
    else:report["action_execution_contract"]["sha256"]="d"*64
    ref=save(tmp_path,ref["path"],report)
    with pytest.raises(ValueError):guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")

@pytest.mark.parametrize("mutation",["from_version","prefix_sha","prefix_bytes","replacement"])
def test_historical_summary_cannot_hide_or_replace_prefix(tmp_path,actual_v1,mutation):
    guard,_=install(tmp_path);ref,report=chain(tmp_path,actual_v1,depth=2)
    h=report["historical_transition"]
    if mutation=="from_version":h["from_version"]="formal-downstream-root-v1"
    elif mutation=="prefix_sha":h["preserved_prefix_sha256"]="d"*64
    elif mutation=="prefix_bytes":h["preserved_prefix_bytes"]=0
    else:h["historical_terminal_outcomes_replaced"]=True
    ref=save(tmp_path,ref["path"],report)
    with pytest.raises(ValueError):guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")


def test_actual_original_o2a_gate_with_guard_and_negative_order(tmp_path,actual_v1,monkeypatch):
    ref,report=chain(tmp_path,actual_v1,depth=2)
    full={**deepcopy(report),"stage":"full","observations":30,"methods":22,"attempted_policy_forwards":14300}
    comp={**full,"stage":"components"}
    fr=save(tmp_path,"results/formal_main_v2/downstream_reviews/full.json",full)
    cr=save(tmp_path,"results/formal_main_v2/downstream_reviews/components.json",comp)
    reports={ref["path"]:report,fr["path"]:full,cr["path"]:comp}
    guard,consumer,calls=scoped(tmp_path,monkeypatch,reports)
    original_code=ORIGINAL.require_matching_o2a.__code__
    result=consumer.require_matching_o2a(BASE.Evidence(tmp_path),[ref],fr,cr,suite="libero_10")
    assert result["original_verification"]["kind"]=="formal_action_O2A_identity_verification"
    assert len(result["development_ancestry"][0]["chain"])==2 and result["final_release"] is False
    assert ORIGINAL.require_matching_o2a.__code__ is original_code
    comp["attempted_policy_forwards"]=1
    with pytest.raises(ValueError):consumer.require_matching_o2a(BASE.Evidence(tmp_path),[ref],fr,cr,suite="libero_10")
    calls.clear(); ref,report=chain(tmp_path,actual_v1,depth=3,legacy_leaf=True)
    reports[ref["path"]]=report
    with pytest.raises(ValueError,match="Unresolved legacy"):
        consumer.require_matching_o2a(BASE.Evidence(tmp_path),[ref],fr,cr,suite="libero_10")
    assert [k for k,_ in calls]==[ref["path"]]


def test_byte_identical_candidate_relocation_and_upstream_pin(tmp_path):
    guard,consumer=install(tmp_path);ev=BASE.Evidence(tmp_path)
    loaded=consumer._guard(ev);base,original=loaded.upstreams(ev)
    assert base.VERSION==BASE.VERSION and original.require_matching_o2a.__code__.co_code==ORIGINAL.require_matching_o2a.__code__.co_code
    ev.unchanged()
    p=tmp_path/BASE.CONSUMER;p.write_bytes(p.read_bytes()+b"\n# unexpected drift\n")
    with pytest.raises(ValueError,match="Pinned upstream"):
        loaded.upstreams(BASE.Evidence(tmp_path))
    p=tmp_path/(NEW+"reviewer.py");p.write_bytes(p.read_bytes()+b"\n# guard drift\n")
    with pytest.raises(ValueError,match="Exact independent ancestry"):
        consumer._guard(BASE.Evidence(tmp_path))


def test_real_original_global_release_metadata_compatibility(tmp_path,actual_v1,monkeypatch):
    import test_formal_execution_manifests as ft
    t=ft.load_tool();p=ft.project.__wrapped__(tmp_path,monkeypatch,t)
    index=ft.write_development_runs(p)
    reports={}
    # Original complete 88-identity fixture builds/re-audits real freeze formats.
    # Its 72 checkpoint/GPU identities are declared synthetic and never opened.
    for suite,refs in index["root_reviews"].items():
        old=json.loads((tmp_path/refs[0]["path"]).read_bytes())
        reference,report=chain(tmp_path,actual_v1,suite=suite,output=index["suites"][suite][0],provenance=old["source_provenance"])
        report.update(synthetic_operational_gate_stub=True,completed_trials=2200,cost=old["cost"],job_id=old["job_id"])
        reference=save(tmp_path,reference["path"],report)
        index["root_reviews"][suite]=[reference];reports[reference["path"]]=report
    ft.save(t,tmp_path/"development_index.json",index)
    # Read guard sources before the freeze; modifying evidence afterwards is forbidden.
    guard,consumer,calls=scoped(tmp_path,monkeypatch,reports)
    matrix=t.build_global(t.Evidence(tmp_path),p.registration,p.sources,"development_index.json","freeze",checkpoint_inventory="checkpoint_inventory.json")
    assert len(matrix["instances"])==88 and isinstance(matrix["suites"],dict)
    # base.load loads the exact pinned real helper. release_global itself is NOT
    # patched: all 88 identities, raw completion, root refs and hashes are checked.
    ev=BASE.Evidence(tmp_path)
    result=consumer.audit_freeze(ev,"freeze",p.registration)
    assert result["original_verification"]["status"]=="verified_not_released"
    assert len(result["development_ancestry"])==4 and result["final_release"] is False
    assert not (tmp_path/"freeze/root_release.json").exists()
    assert not (tmp_path/"freeze/final_execution").exists()
    # 88-instance evidence still rejects mutation; the ancestry layer does not
    # bypass the original helper even when every development report is current.
    raw=tmp_path/"freeze/execution_rows.json"
    raw.write_bytes(raw.read_bytes()+b" ")
    with pytest.raises(ValueError,match="Global freeze input/output bytes changed"):
        consumer.audit_freeze(BASE.Evidence(tmp_path),"freeze",p.registration)


def test_legacy_freeze_is_rejected_before_global_helper(tmp_path,actual_v1,monkeypatch):
    reports={};refs={}
    for suite in sorted(BASE.SUITES if hasattr(BASE,"SUITES") else {"libero_spatial","libero_object","libero_goal","libero_10"}):
        ref,report=chain(tmp_path,actual_v1,suite=suite,depth=2,legacy_leaf=True)
        reports[ref["path"]]=report;refs[suite]=ref
        save(tmp_path,"freeze/development_root_reviews/"+suite+".json",{"reviews":[{"reference":ref}]})
    save(tmp_path,"freeze/global_freeze.json",{"suites":{s:{} for s in refs}})
    guard,consumer,calls=scoped(tmp_path,monkeypatch,reports)
    real_load=BASE.load
    def reject_helper(ev,path,checksum=None):
        if path==BASE.OLD_HELPER:raise AssertionError("Must reject legacy before global helper")
        return real_load(ev,path,checksum)
    monkeypatch.setattr(BASE,"load",reject_helper)
    with pytest.raises(ValueError,match="Unresolved legacy"):
        consumer.audit_freeze(BASE.Evidence(tmp_path),"freeze",{})
    assert len(calls)==1 and not (tmp_path/"freeze/root_release.json").exists()
