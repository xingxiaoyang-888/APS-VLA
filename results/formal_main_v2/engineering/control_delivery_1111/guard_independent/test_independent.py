"""Independent CPU review of the frozen mixed-prefix guard.
Reuses author setup only; current raw report is reconstructed by original writer
and reviewer. Metadata-only chain fault tests explicitly stub upstream raw
reconstruction. No actual GPU/O2A/release or production state is accessed.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import importlib.util
import json
import sys
import pytest

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
C=R/".local/action_mixed_prefix_guard_1111"
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m
    spec.loader.exec_module(m);return m
A=load(C/"test_guard.py","independent_guard_author_setup")
BASE=A.BASE

@pytest.fixture(scope="module")
def real_shape(tmp_path_factory):
    yield from A.actual_v1.__wrapped__(tmp_path_factory)

def read(root,path):
    return json.loads((root/path).read_bytes())

def change_oldest_and_rebind(root,depth,mutate):
    name="results/formal_main_v2/downstream_reviews/libero_10_0.json"
    v=read(root,name);mutate(v);ref=A.save(root,name,v)
    for n in range(1,depth):
        rn=f"results/formal_main_v2/downstream_reviews/libero_10_{n}.json"
        v=read(root,rn);inv=read(root,v["invocation_ref"]["path"])
        inv["root_evidence_sha256"][ref["path"]]=ref["sha256"]
        ir=A.save(root,v["invocation_ref"]["path"],inv)
        v.update(invocation_ref=ir,invocation_sha256=ir["sha256"])
        ref=A.save(root,rn,v)
    return ref,v

def replace_current_contract(root,ref,report,contract):
    cr=A.save(root,report["action_execution_contract"]["path"],contract)
    inv=read(root,report["invocation_ref"]["path"]);inv["action_execution_contract"]=cr
    ir=A.save(root,report["invocation_ref"]["path"],inv)
    report.update(action_execution_contract=cr,invocation_ref=ir,invocation_sha256=ir["sha256"])
    return A.save(root,ref["path"],report),report

def test_actual_raw_partial_schema_remains_partial(real_shape,monkeypatch):
    v=real_shape;guard,consumer=A.install(v.root)
    monkeypatch.setattr(guard,"upstreams",lambda ev:(v.ng,v.nc))
    monkeypatch.setattr(consumer,"_guard",lambda ev:guard)
    _,_,consume,proofs=guard.guarded_consumer(v.ng.Evidence(v.root))
    ev=v.ng.Evidence(v.root)
    _,_,consume,proofs=guard.guarded_consumer(ev)
    result=consume(ev,v.reference,expected_stage="development",suite="libero_10",require_complete=False)
    assert result["scientific_complete"] is False
    assert len(proofs)==1 and len(proofs[0]["chain"])==1
    assert result["files"]==v.rebuilt["files"] and result["cost"]==v.rebuilt["cost"]
    with pytest.raises(ValueError):
        consumer.require_matching_o2a(v.ng.Evidence(v.root),[v.reference],{},{},suite="libero_10")

@pytest.mark.parametrize("depth",[2,4])
def test_legacy_ancestor_blocks_before_any_profile_consumer(tmp_path,real_shape,monkeypatch,depth):
    ref,report=A.chain(tmp_path,real_shape,depth=depth,legacy_leaf=True)
    guard,consumer,calls=A.scoped(tmp_path,monkeypatch,{ref["path"]:report})
    with pytest.raises(ValueError,match="Unresolved legacy"):
        consumer.require_matching_o2a(BASE.Evidence(tmp_path),[ref],{}, {},suite="libero_10")
    assert calls==[(ref["path"],{"expected_stage":"development","suite":"libero_10"})]

@pytest.mark.parametrize("mutation,match",[
    ("root","Historical development identity"),("marker","marker is missing"),
    ("semantics","Historical action semantics"),("hidden","Fresh execution has hidden")])
def test_rebound_deep_ancestor_metadata_still_rejected(tmp_path,real_shape,mutation,match):
    guard,_=A.install(tmp_path);A.chain(tmp_path,real_shape,depth=3)
    def mutate(v):
        if mutation=="root":v["run_root"]+="_different"
        elif mutation=="marker":v.pop("historical_transition")
        elif mutation=="semantics":v["action_semantics_sha256"]="d"*64
        else:v["historical_transition"]={"from_version":"formal-downstream-root-v1"}
    ref,report=change_oldest_and_rebind(tmp_path,3,mutate)
    with pytest.raises(ValueError,match=match):
        guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")

def test_independent_prefix_reference_cannot_be_rebound_to_other_bytes(tmp_path,real_shape):
    guard,_=A.install(tmp_path);ref,report=A.chain(tmp_path,real_shape,depth=2)
    contract=read(tmp_path,report["action_execution_contract"]["path"])
    transition=read(tmp_path,contract["transition"]["path"])
    independent=read(tmp_path,transition["independent_review"]["path"])
    independent["files"][next(iter(independent["files"]))]="1"*64
    transition["independent_review"]=A.save(tmp_path,transition["independent_review"]["path"],independent)
    tr=A.save(tmp_path,contract["transition"]["path"],transition);contract["transition"]=tr
    report["historical_transition"]["reference"]=tr
    ref,report=replace_current_contract(tmp_path,ref,report,contract)
    with pytest.raises(ValueError,match="independent binding"):
        guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")

def test_runtime_source_pin_not_just_semantic_self_consistency(tmp_path,real_shape):
    guard,_=A.install(tmp_path);ref,report=A.chain(tmp_path,real_shape)
    contract=read(tmp_path,report["action_execution_contract"]["path"])
    contract["files"][guard.UPSTREAM_REVIEWER]="2"*64
    report["action_semantics_sha256"]=BASE.semantic_identity(contract)
    ref,report=replace_current_contract(tmp_path,ref,report,contract)
    with pytest.raises(ValueError,match="runtime source/semantic binding"):
        guard._require_current_ancestry(BASE.Evidence(tmp_path),BASE,ref,report,suite="libero_10")

def test_cache_does_not_promote_partial_result_to_complete(tmp_path,real_shape,monkeypatch):
    ref,report=A.chain(tmp_path,real_shape);report["scientific_complete"]=False
    ref=A.save(tmp_path,ref["path"],report)
    guard,_,calls=A.scoped(tmp_path,monkeypatch,{ref["path"]:report})
    ev=BASE.Evidence(tmp_path);_,_,consume,proofs=guard.guarded_consumer(ev)
    consume(ev,ref,expected_stage="development",suite="libero_10",require_complete=False)
    with pytest.raises(ValueError,match="incomplete"):
        consume(ev,ref,expected_stage="development",suite="libero_10",require_complete=True)
    assert len(calls)==2 and len(proofs)==1

def test_cached_same_ref_cannot_hide_byte_drift(tmp_path,real_shape,monkeypatch):
    ref,report=A.chain(tmp_path,real_shape)
    guard,_,calls=A.scoped(tmp_path,monkeypatch,{ref["path"]:report})
    ev=BASE.Evidence(tmp_path);_,_,consume,_=guard.guarded_consumer(ev)
    consume(ev,ref,expected_stage="development",suite="libero_10")
    p=tmp_path/ref["path"];p.write_bytes(p.read_bytes()+b" ")
    with pytest.raises(ValueError):
        consume(ev,ref,expected_stage="development",suite="libero_10")
    assert len(calls)==1

def test_exact_guard_and_upstream_code_relocation(tmp_path):
    guard,consumer=A.install(tmp_path)
    loaded=consumer._guard(BASE.Evidence(tmp_path));_,original=loaded.upstreams(BASE.Evidence(tmp_path))
    assert original.require_matching_o2a.__code__.co_code==A.ORIGINAL.require_matching_o2a.__code__.co_code
    p=tmp_path/guard.UPSTREAM_REVIEWER;p.write_bytes(p.read_bytes()+b"\n# drift\n")
    with pytest.raises(ValueError,match="Pinned upstream"):
        loaded.upstreams(BASE.Evidence(tmp_path))
    p=tmp_path/(A.NEW+"reviewer.py");p.write_bytes(p.read_bytes()+b"\n# drift\n")
    with pytest.raises(ValueError,match="Exact independent"):
        consumer._guard(BASE.Evidence(tmp_path))

def test_freeze_refuses_transitive_legacy_before_global_release(tmp_path,real_shape,monkeypatch):
    reports={}
    for suite in sorted({"libero_10","libero_goal","libero_object","libero_spatial"}):
        ref,report=A.chain(tmp_path,real_shape,suite=suite,depth=3,legacy_leaf=True)
        reports[ref["path"]]=report
        A.save(tmp_path,"freeze/development_root_reviews/"+suite+".json",{"reviews":[{"reference":ref}]})
    A.save(tmp_path,"freeze/global_freeze.json",{"suites":{s:{} for s in ["libero_10","libero_goal","libero_object","libero_spatial"]}})
    guard,consumer,calls=A.scoped(tmp_path,monkeypatch,reports)
    def forbidden(*args,**kwargs):raise AssertionError("Must not reach global release helper")
    monkeypatch.setattr(BASE,"load",forbidden)
    with pytest.raises(ValueError,match="Unresolved legacy"):
        consumer.audit_freeze(BASE.Evidence(tmp_path),"freeze",{})
    assert len(calls)==1 and not (tmp_path/"freeze/root_release.json").exists()
