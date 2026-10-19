"""Narrow CPU checks. Actual source/data planner integration is the eight-plan phase."""
import copy, importlib.util, json, sys
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("long1722_prepare_test",HERE/"prepare.py")
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)

@pytest.fixture(scope="module")
def data():
    index=json.loads((HERE/"plan_index.json").read_bytes())
    state=json.loads((HERE/"state_snapshot_for_plans.json").read_bytes())
    p=a.load(a.PLANNER,a.PLANNER_SHA);m=a.load(a.BUILDER,a.BUILDER_SHA)
    return index,state,p,m

def test_exact_partition(data):
    index,state,p,m=data
    ids=json.loads((HERE/"all22_identity_coverage.json").read_bytes())["manifest"]["methods"]
    assert len(a.validate_shards(index["plans"],[r["identity"]["method_id"] for r in ids]))==16
    assert len(state["registered_jobs"])==index["full_registry_rows"]
    assert index["submission_authorized"] is False and index["final_release"] is False
    assert index["old600_GPU_seconds"]==10531

@pytest.mark.parametrize("mutation",["duplicate","old6","missing","wrong_pair","wrong_trials"])
def test_bad_shard_partition_rejected(data,mutation):
    index,_,_,_=data
    shards=copy.deepcopy(index["plans"])
    allids=[r["identity"]["method_id"] for r in json.loads((HERE/"all22_identity_coverage.json").read_bytes())["manifest"]["methods"]]
    if mutation=="duplicate": shards[1]=copy.deepcopy(shards[0])
    elif mutation=="old6": shards[0]["method_ids"]=["A128_seed17","B128_seed17"]
    elif mutation=="missing": shards.pop()
    elif mutation=="wrong_pair": shards[0]["method_ids"].reverse()
    else: shards[0]["expected_trials"]=201
    with pytest.raises(ValueError): a.validate_shards(shards,allids)

@pytest.mark.parametrize("field,value",[
    ("resume",True),("prior_job_ids",["3022743"]),("prior_allocation_cost",[{"job_id":"3022743"}]),
    ("prior_review","results/foreign.json"),("repair_record","results/repair.json"),
    ("stop_after",12),("stage","final"),("suite","libero_spatial")])
def test_nonfresh_science_rejected(data,field,value):
    index,_,_,_=data;row=index["plans"][0]
    plan=json.loads((a.R/row["scientific_plan"]["path"]).read_bytes())
    plan["invocation"][field]=value
    with pytest.raises(ValueError): a.validate_fresh_plan(plan,row)

@pytest.mark.parametrize("idx",range(8))
def test_original_prior_contract_with_full_registry(data,idx):
    index,state,p,m=data;row=index["plans"][idx];before=p.signature(state)
    args=a.plan_args(row["canonical_path"])
    v=dict(evidence=m.Evidence(a.R),suite="libero_10",methods=row["method_ids"])
    key,output,prior,review=p.prior_contract(args,state,v,a.R)
    assert prior==[] and review is None and key==row["stage_key"]
    assert str(p.P/output)==row["run_root"] and p.signature(state)==before

@pytest.mark.parametrize("status",["RUNNING","SUBMITTED","PENDING","UNKNOWN","COMPLETING","FAILED"])
def test_original_prior_rejects_new_overlap_without_filtering(data,status):
    index,state,p,m=data;row=index["plans"][0]
    full=copy.deepcopy(state)
    full["registered_jobs"].append(dict(experiment="formal_main_v2",job_id="999999999",
        suite="libero_10",mode="development",stage_key=row["stage_key"],method_ids=row["method_ids"],
        status=status,exit_code="1:0" if status=="FAILED" else None,elapsed_seconds=2,gpus=1,
        source_sha256=p.FROZEN_SHA256,adapter_sha256=p.ADAPTER_SHA256,
        run_root=row["run_root"],submitted_utc="2099-01-01T00:00:00+00:00"))
    args=a.plan_args(row["canonical_path"])
    v=dict(evidence=m.Evidence(a.R),suite="libero_10",methods=row["method_ids"])
    with pytest.raises(ValueError): p.prior_contract(args,full,v,a.R)

def test_old_six_still_overlap_and_are_not_relabelled(data):
    _,state,p,m=data
    args=a.plan_args("results/formal_main_v2/execution/libero_10_development_first_pair_v1.json")
    v=dict(evidence=m.Evidence(a.R),suite="libero_10",methods=list(a.OLD6))
    with pytest.raises(ValueError): p.prior_contract(args,state,v,a.R)

def test_duplicate_formal_registry_rejected(data):
    index,state,p,m=data
    full=copy.deepcopy(state);full["registered_jobs"].append(copy.deepcopy(next(j for j in full["registered_jobs"] if j.get("experiment")=="formal_main_v2")))
    with pytest.raises(ValueError): p.formal_jobs(full)

def test_no_scientific_or_runtime_source_changes():
    a.guard_protected()
