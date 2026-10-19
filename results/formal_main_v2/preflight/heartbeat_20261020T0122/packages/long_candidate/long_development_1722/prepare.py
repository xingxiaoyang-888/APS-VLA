"""Prepare real Long manifests with the unchanged source/science builder; never submit."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, sys, time, traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
HERE=R/".local/long_development_1722"
DEST="results/formal_main_v2/execution/long_remaining16_action_v1_1722"
INVENTORY="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
INVENTORY_SHA="5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926"
ROOT_CHECK="results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json"
ROOT_CHECK_SHA="e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757"
BUILDER="scripts/formal_execution_manifests.py"
BUILDER_SHA="614a5e71e0802ca42e3358c32dce2f025e55191324c26eb571929444b4595c89"
PLANNER="scripts/ops/formal_downstream_supervisor.py"
PLANNER_SHA="f24acea144fb53e8e72981d86f901af03769131d5e2534648eaee6277d88f571"
PAIRS=((128,23),(128,41),(256,17),(256,23),(256,41),(64,17),(64,23),(64,41))
OLD6=("dense","uniform256","uniform128","uniform64","A128_seed17","B128_seed17")
STATE="results/experiment_supervisor/state.json"
sys.path[:0]=[str(R/"src"),str(R/"scripts")]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def encoded(v):
    return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()

def write(name, value):
    p=HERE/name
    if HERE not in p.resolve().parents: raise ValueError("private output only")
    p.parent.mkdir(parents=True,exist_ok=True)
    b=value if isinstance(value,bytes) else encoded(value)
    with p.open("xb") as f: f.write(b)
    return {"path":p.relative_to(R).as_posix(),"sha256":hashlib.sha256(b).hexdigest(),"bytes":len(b)}

def load(rel,expected):
    p=R/rel
    if sha(p)!=expected: raise ValueError("source pin: "+rel)
    spec=importlib.util.spec_from_file_location("long1722_"+p.stem,p)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m

def guard_protected():
    if sha(R/INVENTORY)!=INVENTORY_SHA: raise ValueError("inventory pin")
    inv=json.loads((R/INVENTORY).read_bytes())
    if len(inv["files"])!=173: raise ValueError("173 sources")
    for rel,expected in inv["files"].items():
        if sha(R/rel)!=expected: raise ValueError("frozen source changed: "+rel)
    for rel,expected in [(BUILDER,BUILDER_SHA),(PLANNER,PLANNER_SHA),(ROOT_CHECK,ROOT_CHECK_SHA)]:
        if sha(R/rel)!=expected: raise ValueError("fixed dependency changed: "+rel)
    return {**inv["files"],BUILDER:BUILDER_SHA,PLANNER:PLANNER_SHA,INVENTORY:INVENTORY_SHA,ROOT_CHECK:ROOT_CHECK_SHA}

def validate_shards(shards,all_ids):
    flat=[mid for s in shards for mid in s["method_ids"]]
    want={f"{a}{k}_seed{s}" for k,s in PAIRS for a in ("A","B")}
    if len(shards)!=8 or len(flat)!=16 or set(flat)!=want or len(set(flat))!=16:
        raise ValueError("exact eight unique A/B pairs required")
    if set(flat)&set(OLD6) or set(all_ids)!=set(flat)|set(OLD6) or len(all_ids)!=22:
        raise ValueError("original22 identities/old6 partition")
    for (k,s),row in zip(PAIRS,shards):
        if row["method_ids"]!=[f"A{k}_seed{s}",f"B{k}_seed{s}"] or row["expected_trials"]!=200:
            raise ValueError("pair order/size")
    return flat

def manifests():
    protected=guard_protected();m=load(BUILDER,BUILDER_SHA);e=m.Evidence(R)
    registration=m.registration_contract(e,m.REGISTRATION);sources=m.source_contract(e,INVENTORY)
    from cti_vla.evaluation.formal_trials import expected_method_ids
    from cti_vla.data.formal_initial_states import load_formal_development_panel
    panel_rel=registration["suites"]["libero_10"]["initial_states_root"]+"/development.json"
    panel=load_formal_development_panel(e.path(panel_rel));panel_sha=e.watch(panel_rel)
    if panel["suite"]!="libero_10" or len(panel["states"])!=100: raise ValueError("fixed100 dev panel")
    rows=m.suite_rows(e,registration,"libero_10",sources,expected_method_ids())
    byid={r["identity"]["method_id"]:r for r in rows}
    root=e.read(ROOT_CHECK)
    if e.watch(ROOT_CHECK)!=ROOT_CHECK_SHA or root["submission_authorized"] is not False:
        raise ValueError("root identity proof pin/scope")
    selected={}
    for mid,row in byid.items():
        if row["identity"]["method"] not in ("A","B"): continue
        proof=root["all18_selected"][mid]
        receipt=e.read(row["receipt"])
        for typ in ("root_review","independent_review"):
            ref=proof[typ]
            if e.watch(ref["path"])!=ref["sha256"]: raise ValueError("root/independent pin")
            audited=e.read(ref["path"])
            if not str(audited.get("status","")).startswith("passed"): raise ValueError("incomplete original review")
        if (row["checkpoint"]!=proof["checkpoint_path"] or row["identity"]["checkpoint_sha256"]!=proof["checkpoint_sha256"]
                or receipt["metadata"]["update"]!=proof["selected_update"] or proof["checkpoint_reselected"] is not False):
            raise ValueError("selected identity drift")
        selected[mid]=proof
    all_manifest=m.make_execution(registration,"libero_10",rows)
    all_manifest.update(development_panel=panel_rel,development_panel_sha256=panel_sha)
    coverage=write("all22_identity_coverage.json",dict(schema="formal_main_v2",kind="identity_coverage_only_not_execution_authorization",
        manifest=all_manifest,current_fresh_method_ids=root["fresh_target_method_ids"],old_six=list(OLD6),
        old_six_new_action_identity_status="HOLD_SEPARATE_REGISTRATION_REQUIRED",
        original600_GPU_seconds=10531,original600_records_retained=True,all18_selected=selected,
        submission_authorized=False,final_release=False,test_opened=False))
    shards=[]
    for k,s in PAIRS:
        ids=[f"A{k}_seed{s}",f"B{k}_seed{s}"]
        value=m.make_execution(registration,"libero_10",[byid[mid] for mid in ids])
        value.update(development_panel=panel_rel,development_panel_sha256=panel_sha)
        if value["environment"]!={"action_chunk":8,"environment_seed":0,"runtime_seed":17,"wait_steps":10,"max_steps":520}:
            raise ValueError("Long environment changed")
        name=f"libero_10_k{k}_seed{s}_development.json"
        ref=write("manifests/"+name,value)
        shards.append(dict(visual_tokens=k,seed=s,method_ids=ids,expected_trials=200,
            unique_development_initial_states=100,candidate=ref,canonical_path=DEST+"/"+name))
    validate_shards(shards,list(byid))
    e.unchanged()
    if protected!=guard_protected(): raise ValueError("protected inputs changed")
    ev=write("manifest_evidence.json",dict(schema="formal_main_v2",kind="long16_manifest_reconstruction_evidence",
        builder={"path":BUILDER,"sha256":BUILDER_SHA},source_provenance=e.source_provenance["libero_10"],
        read_evidence_sha256=e.files,checkpoint_bytes_read=False,test_opened=False,protected_files=protected))
    out=write("manifest_index.json",dict(schema="formal_main_v2",kind="candidate_development_manifest_publication_request",
        status="prepared_only_not_authorized",shards=shards,coverage=coverage,evidence=ev,expected_total_trials=1600,
        unique_initial_states=100,publication_by_root_required=True,source_173_unchanged=True,
        runtime_outer_plan_pending=True,submission_authorized=False))
    return out

def plan_args(manifest):
    return SimpleNamespace(stage="development",execution_manifest=manifest,source_inventory=INVENTORY,
        freeze_directory=None,profile_panel=None,prior_review=None,collection_review=None,repair_record=None,
        output_relative=None,resume=False,stop_after=None)

def validate_fresh_plan(plan,shard):
    inv=plan["invocation"]
    if (inv["method_ids"]!=shard["method_ids"] or inv["prior_job_ids"] or inv["prior_allocation_cost"]
            or inv["prior_review"] is not None or inv["repair_record"] is not None or inv["resume"]
            or inv["stop_after"] is not None or inv["stage"]!="development" or inv["suite"]!="libero_10"
            or plan["output_must_exist"] or "--resume" in inv["argv"]
            or any("sealed" in a or "final_registry" in a for a in inv["argv"])):
        raise ValueError("fresh plan is not exact development pair")
    if plan["resources"]["time"]!="04:00:00" or plan["resources"]["gres"]!="gpu:l40:1":
        raise ValueError("resource contract changed")
    return inv

def plans():
    protected=guard_protected();m=load(BUILDER,BUILDER_SHA);p=load(PLANNER,PLANNER_SHA)
    idx=json.loads((HERE/"manifest_index.json").read_bytes())
    from cti_vla.evaluation.formal_trials import expected_method_ids
    validate_shards(idx["shards"],expected_method_ids())
    state_bytes=(R/STATE).read_bytes();state=json.loads(state_bytes)
    state_ref=write("state_snapshot_for_plans.json",state_bytes)
    full_registry_sig=p.signature(state["registered_jobs"])
    if state.get("pending_submission") is not None: raise ValueError("pending state blocks pure planner")
    output=[];all_reads={};closure=[]
    for shard in idx["shards"]:
        canonical=R/shard["canonical_path"]
        if not canonical.is_file() or sha(canonical)!=shard["candidate"]["sha256"]:
            raise ValueError("root must first publish exact canonical manifest: "+str(canonical))
        args=plan_args(shard["canonical_path"])
        plan=p.plan(args,state,project=R,helper=m)
        inv=validate_fresh_plan(plan,shard)
        if p.signature(state["registered_jobs"])!=full_registry_sig:
            raise ValueError("planner mutated/filtered full registry")
        if (P/plan["output_relative"]).exists(): raise ValueError("server output already exists")
        if (P/plan["invocation_relative"]).exists(): raise ValueError("server invocation already exists")
        name=f"k{shard['visual_tokens']}_seed{shard['seed']}"
        ref=write("plans/"+name+"/scientific_plan.json",plan)
        args_ref=write("plans/"+name+"/plan_arguments.json",vars(args))
        output.append(dict(**shard,scientific_plan=ref,plan_arguments=args_ref,plan_sha256=plan["plan_sha256"],
            stage_key=inv["stage_key"],run_root=inv["run_root"],invocation_relative=plan["invocation_relative"]))
        for rel,h in inv["root_evidence_sha256"].items():
            if rel in all_reads and all_reads[rel]!=h: raise ValueError("cross-plan evidence drift")
            all_reads[rel]=h
        print(json.dumps({"pair":name,"status":"original_pure_plan_passed","trials":200,"plan_sha256":plan["plan_sha256"]}),flush=True)
    e=m.Evidence(R)
    for rel,h in all_reads.items():
        if e.watch(rel)!=h: raise ValueError("plan dependency drift: "+rel)
        closure.append(dict(local_path=rel,server_path=str(P/rel),sha256=h,bytes=e.path(rel).stat().st_size,
            role="root_science_evidence",publication_required=not(P/rel).is_file() or sha(P/rel)!=h))
    # The source snapshot mapping is identity-preserving, never a generic alias.
    inventory=json.loads((R/INVENTORY).read_bytes())
    for rel,h in inventory["files"].items():
        server=Path(inventory["source_root_server"])/rel
        if not server.is_file() or sha(server)!=h: raise ValueError("server frozen source changed")
        closure.append(dict(local_path=rel,server_path=str(server),sha256=h,bytes=(R/rel).stat().st_size,
            role="frozen_scientific_source",publication_required=False))
    if protected!=guard_protected(): raise ValueError("protected source changed")
    dependency_ref=write("science_dependency_closure.json",dict(scope="science_only_outer_runtime_pending",
        files=closure,weights_included=False,final_values_included=False))
    evidence_ref=write("plan_read_evidence.json",dict(read_evidence_sha256=all_reads,
        state_snapshot=state_ref,full_registry_rows=len(state["registered_jobs"]),
        full_registry_canonical_sha256=full_registry_sig,state_modified=False,registry_filtered=False,
        actual_original_planner={"path":PLANNER,"sha256":PLANNER_SHA},protected_files=protected))
    result=write("plan_index.json",dict(schema="formal_main_v2",kind="long16_original_scientific_plan_candidates",
        status="eight_original_pure_plans_passed_runtime_outer_pending",plans=output,
        read_evidence=evidence_ref,dependency_closure=dependency_ref,full_registry_rows=len(state["registered_jobs"]),
        expected_total_trials=1600,common_unique_development_initial_states=100,old600_GPU_seconds=10531,
        old600_records_retained=True,old_six_new_execution_status="HOLD_SEPARATE_REGISTRATION_REQUIRED",
        scientific_results_created=False,submission_authorized=False,final_release=False,
        required_before_submission=["root/independent plan review","new action runtime effective plans and readiness",
            "complete canonical R-to-P publication and unmodified wrapper verification",
            "new exact authorization, capacity/reservation and pending transaction checks"]))
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument("phase",choices=["manifests","plans"]);a=ap.parse_args()
    start=time.monotonic()
    try:
        out=manifests() if a.phase=="manifests" else plans()
        print(json.dumps({"status":"passed_candidate_preparation_only","output":out,"seconds":time.monotonic()-start}))
    except BaseException:
        traceback.print_exc();raise
if __name__=="__main__": main()
