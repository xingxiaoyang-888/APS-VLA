"""Independent read-only reconstruction of eight real Long development science plans."""
from __future__ import annotations
import copy, hashlib, importlib.util, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
S=P/"snapshots/formal_main_v2_run_564be0995e"
OUT=R/".local/spatial_resume_audit_1722/long16"
AUTHOR=".local/long_development_1722"
INVENTORY="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
PANEL="configs/manifests/formal_main_v2/libero_10/initial_states/development.json"
PINS={
"SERVER_WORKSPACE.md":"fe43ae998a45bc749b3de1acbb8841d5b413962b59b05f62284e3f503a9baf62",
"docs/服务器工作区与GitHub同步.md":"a871dbefb420ac06ad4818fbf85116ae9db243839911afff999ebf9b49e83854",
INVENTORY:"5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926",
"scripts/formal_execution_manifests.py":"614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89",
"scripts/ops/formal_downstream_supervisor.py":"f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571",
"scripts/ops/formal_action_deployment_v1/contract.py":"efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19",
"scripts/ops/formal_action_deployment_v1/runtime_scope.py":"6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53",
AUTHOR+"/prepare.py":"3231fcc6be4c48da80e0a75580ddc05bd4b6197e6423b536f28be6b044b23e18",
AUTHOR+"/manifest_index.json":"03e2dcc45625f2b02ef5f4e99eede5b9e9c3971ef2267281c35b796b4ac4362b",
AUTHOR+"/plan_index.json":"e27f3c8973e778bd98b31327cbfe9b02c91faee4ad73af14e8c6cb8aa0132890",
"results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_manifest_publication.json":"a016d94f02f95c56aed8dcace698995770610e68041ec8f48eaa3d8ffbeb75c3",
"results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json":"e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757",
}
PAIRS=((128,23),(128,41),(256,17),(256,23),(256,41),(64,17),(64,23),(64,41))
OLD6={"dense","uniform256","uniform128","uniform64","A128_seed17","B128_seed17"}
EXPECTED={f"{a}{k}_seed{s}" for k,s in PAIRS for a in ("A","B")}
evidence={}
checks=[]
def require(v,msg):
    if not v:raise ValueError(msg)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""):h.update(b)
    return h.hexdigest()
def safe(p):
    p=Path(p).absolute()
    require(p==p.resolve() and (R in p.parents or P in p.parents),"non-direct/outside project path")
    require(p.suffix.lower() not in {".pt",".pth",".bin",".safetensors",".ckpt"},"weights forbidden")
    if p.suffix.lower() not in {".py",".pyc",".pyo"}:
        low=str(p).lower()
        require(not any("sealed" in x.lower() or x.lower()=="test" for x in p.parts),"sealed/test forbidden")
        if any(s in low for s in ("init_state","initial_state","final_state","test_state")):
            require(p in (R/PANEL,P/PANEL),"only fixed development state values permitted")
    return p
def watch(value,expected=None):
    p=safe(R/value if not Path(value).is_absolute() else value)
    h=sha(p)
    if expected is not None:require(h==expected,"SHA drift: "+str(p))
    key=str(p.relative_to(R)) if R in p.parents else str(p)
    require(key not in evidence or evidence[key]==h,"between-read drift: "+key)
    evidence[key]=h
    return p,h
def read(value,expected=None):
    p,h=watch(value,expected)
    return json.loads(p.read_bytes())
def ref(value):
    return read(value["path"],value["sha256"])
def emit(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
    with p.open("xb") as f:f.write(raw)
    return {"path":str(p.relative_to(R)),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
def load(rel):
    p,_=watch(rel,PINS[rel])
    spec=importlib.util.spec_from_file_location("ind1722_"+p.stem,p)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module
def passed(name):checks.append({"name":name,"status":"passed"});print("PASS "+name,flush=True)
def rejects(name,fn):
    try:fn()
    except (ValueError,AssertionError) as e:checks.append({"name":name,"status":"passed","rejection":str(e)});print("PASS "+name,flush=True)
    else:raise AssertionError("expected rejection: "+name)
def main():
    started=time.monotonic()
    for p,h in PINS.items():watch(p,h)
    watch(__file__)
    inventory=read(INVENTORY);require(len(inventory["files"])==173,"source count")
    for rel,h in inventory["files"].items():watch(rel,h);watch(S/rel,h)
    passed("173_science_sources_exact_in_R_and_frozen_S")
    sys.path[:0]=[str(R/"src"),str(R/"scripts")]
    planner=load("scripts/ops/formal_downstream_supervisor.py")
    builder=load("scripts/formal_execution_manifests.py")
    runtime=load("scripts/ops/formal_action_deployment_v1/runtime_scope.py")
    contract=load("scripts/ops/formal_action_deployment_v1/contract.py")
    state_path=R/"results/experiment_supervisor/state.json"
    state_raw=state_path.read_bytes();state=json.loads(state_raw);before=copy.deepcopy(state)
    state_ref=emit("state_snapshot_at_independent_reconstruction.json",state)
    require(state.get("pending_submission") is None,"actual unresolved pending")
    ids=[j["job_id"] for j in state["registered_jobs"]]
    require(len(ids)==len(set(ids)),"duplicate registry identity")
    jobs=state["registered_jobs"]
    old=[j for j in jobs if j.get("experiment")=="formal_main_v2" and j.get("suite")=="libero_10" and j.get("mode")=="development"]
    require(len(old)==6 and {j["job_id"] for j in old}=={"3016981","3017161","3017959","3018505","3019176","3019954"},"old history differs")
    require(all(set(j["method_ids"])==OLD6 for j in old),"old six IDs drift")
    require(sum(j["elapsed_seconds"]*j["gpus"] for j in old)==10531,"old allocation cost missing")
    require(not any(set(j.get("method_ids",[]))&EXPECTED for j in old),"new target already evaluated")
    for job in old:watch(job["invocation"],job["invocation_sha256"])
    passed("full_registry_old_six_allocations_10531_GPU_seconds_retained")
    idx=read(AUTHOR+"/manifest_index.json")
    author_plans=read(AUTHOR+"/plan_index.json")["plans"]
    require(len(author_plans)==8,"author plan count")
    root=read("results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json")
    panel=read(PANEL)
    from cti_vla.data.formal_initial_states import load_formal_development_panel
    real_panel=load_formal_development_panel(R/PANEL)
    require(real_panel==panel and len(panel["states"])==100 and panel["suite"]=="libero_10","fixed panel invalid")
    panelsha=watch(PANEL)[1]
    initial_ids=[(x["task_id"],x["source_index"]) for x in panel["states"]]
    require(len(set(initial_ids))==100,"duplicate initial state")
    selected={};plans=[];seen=[];allwatches={};rootreads={}
    for (budget,seed),shard in zip(PAIRS,idx["shards"]):
        mids=[f"A{budget}_seed{seed}",f"B{budget}_seed{seed}"]
        require(shard["method_ids"]==mids and shard["expected_trials"]==200,"shard identity changed")
        manifest=ref(shard["candidate"]);canonical=read(shard["canonical_path"],shard["candidate"]["sha256"])
        require(manifest==canonical,"publication changed manifest")
        require(canonical["development_panel"]==PANEL and canonical["development_panel_sha256"]==panelsha,"panel drift")
        require(canonical["environment"]==dict(action_chunk=8,environment_seed=0,runtime_seed=17,wait_steps=10,max_steps=520),"environment changed")
        require([m["identity"]["method_id"] for m in canonical["methods"]]==mids,"method ordering")
        for row in canonical["methods"]:
            mid=row["identity"]["method_id"];r=root["all18_selected"][mid];receipt=read(row["receipt"])
            require(row["checkpoint"]==r["checkpoint_path"] and row["identity"]["checkpoint_sha256"]==r["checkpoint_sha256"],"selected checkpoint identity differs")
            require(receipt["checkpoint_sha256"]==r["checkpoint_sha256"] and receipt["metadata"]["update"]==r["selected_update"],"receipt selection drift")
            require(row["identity"]["deployment_receipt_sha256"]==planner.signature(receipt),"semantic receipt SHA differs")
            require(row["identity"]["visual_tokens"]==budget and row["identity"]["training_seed"]==seed,"wrong pair")
            for key in ("root_review","independent_review"):ref(r[key])
            selected[mid]=r
        args=SimpleNamespace(stage="development",execution_manifest=shard["canonical_path"],source_inventory=INVENTORY,
            freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,
            output_relative=None,resume=False,stop_after=None)
        result=planner.plan(args,state,project=R)
        inv=result["invocation"]
        original_author=next(x for x in author_plans if x["visual_tokens"]==budget and x["seed"]==seed)
        require(ref(original_author["scientific_plan"])==result,"independent original planner differs from author plan")
        require(state==before,"original planner changed/filtered full registry")
        require(inv["method_ids"]==mids and inv["resume"] is False and inv["prior_job_ids"]==[] and inv["prior_allocation_cost"]==[],"not fresh disjoint plan")
        require(inv["prior_review"] is None and inv["repair_record"] is None and inv["stop_after"] is None,"unexpected repair/prior/stop")
        require(inv["stage"]=="development" and inv["suite"]=="libero_10" and not result["output_must_exist"],"stage/output mismatch")
        require(result["resources"]["time"]=="04:00:00" and result["resources"]["gres"]=="gpu:l40:1","resource drift")
        require(not (P/result["output_relative"]).exists() and not (P/result["invocation_relative"]).exists(),"server output/invocation exists")
        require(not any("sealed" in v or "final_registry" in v for v in inv["argv"]) and "--resume" not in inv["argv"],"forbidden final/resume")
        for rel,h in inv["root_evidence_sha256"].items():watch(rel,h);rootreads[rel]=h
        for path,h in inv["watched_files"].items():
            require(path not in allwatches or allwatches[path]==h,"cross-plan watch conflict");allwatches[path]=h
        out=emit(f"rebuilt/k{budget}_seed{seed}_scientific_plan.json",result)
        plans.append({"budget":budget,"seed":seed,"method_ids":mids,"scientific_plan":out,"plan_sha256":result["plan_sha256"],"stage_key":inv["stage_key"],"output":inv["run_root"]})
        seen+=mids
        passed(f"real_original_planner_full_registry_k{budget}_seed{seed}")
    require(len(plans)==8 and len(seen)==len(set(seen))==16 and set(seen)==EXPECTED and not set(seen)&OLD6,"partition incomplete")
    require(len({p["stage_key"] for p in plans})==8 and len({p["output"] for p in plans})==8,"stage/output collision")
    passed("eight_pair_partition_exact_sixteen_1600_trials_no_old_six_overlap")
    closure=[]
    for name,h in sorted(allwatches.items()):
        p=safe(name)
        if p.exists():watch(p,h);status="already_present_exact"
        else:status="pending_root_publication"
        closure.append(dict(path=name,sha256=h,status=status))
    passed("all_existing_P_watches_exact_missing_dependencies_explicit")
    runtime_contract=runtime.make_contract(project_root=R,source_root=S,suite="libero_10",stage="development")
    watched=runtime.validate_contract(runtime_contract,project_root=R,source_root=S)
    for name,h in watched.items():watch(name,h)
    require(runtime_contract["policy"]["action_values"]=="unchanged" and runtime_contract["policy"]["scientific_settings_changed"] is False and runtime_contract["policy"]["final_allowed"] is False,"runtime scope drift")
    passed("actual_new_action_runtime_contract_and_original_16_cell_GPU_acceptance_bound")
    # Pure original admission negatives reuse actual immutable source context; no scientific function is patched.
    first=plans[0];saved=read(first["scientific_plan"]["path"],first["scientific_plan"]["sha256"])
    args=SimpleNamespace(stage="development",execution_manifest=idx["shards"][0]["canonical_path"],source_inventory=INVENTORY,
        freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,
        output_relative=None,resume=False,stop_after=None)
    validated=dict(evidence=builder.Evidence(R),suite="libero_10",methods=first["method_ids"])
    added=copy.deepcopy(state)
    added["registered_jobs"].append(dict(experiment="formal_main_v2",job_id="999999991",mode="development",suite="libero_10",
        method_ids=first["method_ids"],stage_key=first["stage_key"],status="RUNNING",run_root=first["output"]))
    rejects("original_prior_gate_rejects_duplicate_pair_active",lambda:planner.prior_contract(args,added,validated,R))
    overlap=copy.deepcopy(state);overlap["registered_jobs"].append(dict(experiment="formal_main_v2",job_id="999999992",mode="development",suite="libero_10",
        method_ids=[first["method_ids"][0]],stage_key="different_group",status="COMPLETED",run_root="/invalid"))
    rejects("original_prior_gate_rejects_partial_method_overlap",lambda:planner.prior_contract(args,overlap,validated,R))
    pending=copy.deepcopy(state);pending["pending_submission"]={"status":"unknown"}
    rejects("original_planner_rejects_unresolved_pending",lambda:planner.plan(args,pending,project=R))
    wrong=copy.deepcopy(saved);wrong["invocation"]["argv"]+=["--sealed-final","not_opened"]
    wrong["plan_sha256"]=planner.signature({k:v for k,v in wrong.items() if k!="plan_sha256"})
    rejects("new_contract_rejects_final_flags_before_any_file_read",lambda:contract.validate_inner(wrong))
    rejects("runtime_contract_rejects_final_stage",lambda:runtime.make_contract(project_root=R,source_root=S,suite="libero_10",stage="final"))
    require(state==before,"test altered production state object")
    for key,h in list(evidence.items()):watch(key,h)
    state_after=hashlib.sha256(state_path.read_bytes()).hexdigest()
    result=dict(schema="formal_main_v2",kind="Long16_fresh_development_independent_science_reconstruction",
        status="passed_science_plan_reconstruction_pending_outer_and_root_authorization",
        reviewed_utc=datetime.now(timezone.utc).isoformat(),checks=checks,passed_checks=len(checks),
        elapsed_seconds=time.monotonic()-started,state_snapshot=state_ref,
        state_raw_sha256_at_start=hashlib.sha256(state_raw).hexdigest(),state_raw_sha256_at_end=state_after,
        state_writes=0,full_registry_rows=len(jobs),registry_filtered=False,production_mutation=False,
        expected_trials=1600,trials_per_pair=200,common_development_initial_states=100,plans=plans,
        checkpoint_identity_sources=selected,checkpoint_bytes_read_by_this_audit=False,
        root_checkpoint_bytes_proof=PINS["results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json"],
        new_runtime_contract=runtime_contract,P_runtime_watches=closure,original_Long600_GPU_seconds=10531,
        original_Long600_records_untouched=True,old_six_new_action_identity="HOLD_SEPARATE_REGISTRATION",
        GPU_execution=False,Slurm_query=False,submission_authorized=False,root_readiness_created=False,
        synthetic_scope="only in-memory duplicate/pending/final-negative inputs; positive plans use actual full registry and original validators",
        read_evidence_sha256=evidence)
    out=emit("science_reconstruction.json",result)
    print(json.dumps({"result":out,"checks":len(checks),"seconds":result["elapsed_seconds"]}),flush=True)
if __name__=="__main__":main()
