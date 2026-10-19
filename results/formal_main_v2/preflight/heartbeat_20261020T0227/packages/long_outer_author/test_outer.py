"""Bounded CPU negative checks; never construct readiness or submit jobs."""
import copy, importlib.util, json, sys
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("outer1827_author",HERE/"prepare.py")
prep=importlib.util.module_from_spec(spec);sys.modules[spec.name]=prep;spec.loader.exec_module(prep)

@pytest.fixture(scope="module")
def box():
    old,c,runtime=prep.modules()
    index=json.loads((HERE/"outer_index.json").read_bytes())
    rows=[]
    for item in index["shards"]:
        d=HERE/"shards"/item["pair"]
        rows.append((item,json.loads((d/"scientific_plan.json").read_bytes()),
                     json.loads((d/"execution_contract.json").read_bytes()),
                     json.loads((d/"effective_plan.json").read_bytes())))
    return old,c,runtime,index,rows

def check(c,row,science=None,contract=None,effective=None):
    meta,original,body,plan=row
    return c.validate_effective(original if science is None else science,
        plan if effective is None else effective,scientific_plan_ref=meta["scientific_plan"],
        execution_contract_ref=meta["action_execution_contract"],execution_contract=body if contract is None else contract)

def test_exact_scope_and_cost(box):
    old,c,runtime,index,rows=box
    assert len(rows)==8
    assert len(set(index["methods"]))==16
    assert not set(index["methods"]) & set(old.OLD6)
    assert index["expected_total_trials"]==1600
    assert index["historical_Long_GPU_seconds"]==10531
    assert index["history_reused_as_new_results"] is False
    assert index["submission_authorized"] is False
    assert index["registry_unfiltered"] is True
    snap=json.loads((prep.R/index["state_observation"]["path"]).read_bytes())
    assert len(snap["registered_jobs"])==index["registry_count"]
    assert set(index["methods"])=={f"{arm}{k}_seed{s}" for k,s in prep.PAIR_ORDER for arm in ("A","B")}

@pytest.mark.parametrize("n",range(8))
def test_exact_pure_outer_reconstruction(box,n):
    old,c,runtime,index,rows=box
    meta,science,contract,effective=rows[n]
    assert check(c,rows[n]) is True
    assert c.effective_plan(science,scientific_plan_ref=meta["scientific_plan"],
        execution_contract_ref=meta["action_execution_contract"],execution_contract=contract)==effective
    assert science["invocation"]["argv"]==effective["invocation"]["argv"]
    assert science["invocation"]["source_provenance"]==effective["invocation"]["source_provenance"]
    assert science["invocation"]["method_ids"]==meta["method_ids"]
    assert effective["resources"]==science["resources"]
    assert "runtime_readiness" not in effective["invocation"]
    assert "registered_utc" not in effective["invocation"]

@pytest.mark.parametrize("field,value",[
    ("method_ids",["A128_seed17","B128_seed17"]),
    ("resume",True),("prior_job_ids",["3016981"]),
    ("stop_after",12),("source_sha256","0"*64),
    ("source_provenance",{}),("stage","final")])
def test_reject_changed_science_even_resigned(box,field,value):
    old,c,runtime,index,rows=box;plan=copy.deepcopy(rows[0][3])
    plan["invocation"][field]=value
    plan["plan_sha256"]=c.signature({k:v for k,v in plan.items() if k!="plan_sha256"})
    with pytest.raises(ValueError):check(c,rows[0],effective=plan)

@pytest.mark.parametrize("field,value",[("status","passed"),("final_evaluation_enabled",True),
    ("scientific_settings_changed",True),("transition",{"path":"results/fake.json","sha256":"0"*64})])
def test_contract_cannot_self_authorize_or_transition(box,field,value):
    old,c,runtime,index,rows=box;body=copy.deepcopy(rows[0][2]);body[field]=value
    with pytest.raises(ValueError):check(c,rows[0],contract=body)

@pytest.mark.parametrize("mutation",["drop_watch","extra_watch","drop_support","drop_publish","argv","resource","extra_field","old_version"])
def test_reject_hidden_outer_drift(box,mutation):
    old,c,runtime,index,rows=box;plan=copy.deepcopy(rows[0][3]);inv=plan["invocation"]
    if mutation=="drop_watch":inv["watched_files"].pop(next(iter(inv["watched_files"])))
    elif mutation=="extra_watch":inv["watched_files"][str(prep.P/"results/fake.json")]="0"*64
    elif mutation=="drop_support":inv["support_files"].pop(next(iter(inv["support_files"])))
    elif mutation=="drop_publish":plan["publish_files"].pop(next(iter(plan["publish_files"])))
    elif mutation=="argv":inv["argv"].append("--resume")
    elif mutation=="resource":plan["resources"]["time"]="48:00:00"
    elif mutation=="extra_field":inv["root_approved"]=True
    elif mutation=="old_version":inv["version"]="formal-downstream-root-v1"
    plan["plan_sha256"]=c.signature({k:v for k,v in plan.items() if k!="plan_sha256"})
    with pytest.raises(ValueError):check(c,rows[0],effective=plan)

@pytest.mark.parametrize("key,value",[
    ("action_values","clip"),("expected_base_loads",2),("first_minimal_install",False),
    ("final_allowed",True),("no_timed_policy_instrumentation",False),
    ("timing_validator","skip_shape_finite")])
def test_runtime_semantics_not_just_outer_shape(box,key,value):
    old,c,runtime,index,rows=box;scope=copy.deepcopy(rows[0][2]["runtime_contract"])
    scope["policy"][key]=value
    with pytest.raises(ValueError):
        runtime.validate_contract(scope,project_root=prep.R,source_root=prep.S)

@pytest.mark.parametrize("path",[
    "../escape.json","/tmp/foreign.json","results/weights/best.pt",
    "results/checkpoints/best.json","results/sealed/panel.json",
    "configs/manifests/formal_main_v2/libero_10/initial_states/test.json"])
def test_path_guard_rejects_before_read(box,path):
    old,c,runtime,index,rows=box
    with pytest.raises(ValueError):c.read_ref(prep.P,dict(path=path,sha256="0"*64))

def test_current_wrapper_requires_real_readiness(box):
    old,c,runtime,index,rows=box
    parent=prep.load(prep.PREF+"wrapper.py",prep.PINS[prep.PREF+"wrapper.py"])
    with pytest.raises(ValueError,match="Exact path/SHA reference required"):
        parent.verify(rows[0][3]["invocation"],project=prep.P)

def test_protected_publication_map_exact(box):
    old,c,runtime,index,rows=box
    mapping=json.loads((HERE/"publication_map.json").read_bytes())
    assert len(mapping["files"])==24
    for entry in mapping["files"]:
        assert entry["canonical_path"].startswith(prep.DEST+"/")
        assert prep.sha(prep.R/entry["candidate"]["path"])==entry["sha256"]
        assert entry["bytes"]==(prep.R/entry["candidate"]["path"]).stat().st_size
    assert mapping["publication_authorized_by_this_file"] is False
