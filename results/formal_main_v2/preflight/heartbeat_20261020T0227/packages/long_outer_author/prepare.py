"""Exact Long16 action envelopes from pinned pure planners; CPU preparation only."""
from __future__ import annotations
import argparse, copy, hashlib, importlib.util, json, sys, traceback
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
S=P/"snapshots/formal_main_v2_run_564be0995e"
HERE=R/".local/long_action_outer_1827"
DEST="results/formal_main_v2/execution/long_remaining16_action_v1_1827"
OLD=".local/long_development_1722"
PREF="scripts/ops/formal_action_deployment_v1/"
PAIR_ORDER=((128,23),(128,41),(256,17),(256,23),(256,41),(64,17),(64,23),(64,41))
PINS={
 OLD+"/prepare.py":"3231fcc6be4c48da80e0a75580ddc05bd4b6197e6423b536f28be6b044b23e18",
 OLD+"/plan_index.json":"e27f3c8973e778bd98b31327cbfe9b02c91faee4ad73af14e8c6cb8aa0132890",
 OLD+"/candidate_review.json":"79204acb7c06ff63d5471b9b1d395bb09c11ba3920923f5527a63cba3da59d0e",
 ".local/spatial_resume_audit_1722/long16/independent_review.json":"37b8009c1291980b1524e84f26c31ca901309dd30a2346ee6ed0af1c32cd77f8",
 "results/formal_main_v2/preflight/heartbeat_20261020T0122/Long_selected_identity_root_check.json":"e3b08dff62a583e910aecd04179841017e10f1216f6a19f431036fe056ff5757",
 PREF+"contract.py":"efe07d29bf572e48bce3a97b25794984c9093f5525941bbb1cc8ab1587d67f19",
 PREF+"wrapper.py":"d00a3a7c749f0ee2a83d9b0cdd0ee9560bf2cea4b0de8dc02c568b2ca0947f33",
 PREF+"entry.py":"2cdb69923146cbffcaaec555b970d03efbce0c9b9f74e3b743a2ce67a21aae19",
 PREF+"runtime_scope.py":"6bc93fffd71981182e36857a33e7c255ce88d8f2cdab930f2779d92776b7ee53",
 PREF+"gateway.py":"8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a",
 PREF+"reviewer.py":"9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd",
 PREF+"consumer.py":"16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034",
 "scripts/server/run_formal_downstream.py":"f47a2606f6de8733eef35c3a3ba6e4a39cc920ed126a3cb60a139600bd457e24",
}
sys.path[:0]=[str(R/"src"),str(R/"scripts")]
READS={}

def require(ok,message):
    if not ok: raise ValueError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(8<<20),b""): h.update(b)
    return h.hexdigest()

def encode(v):
    return (json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n").encode()

def ref(path):
    p=Path(path);return dict(path=p.relative_to(R).as_posix(),sha256=sha(p),bytes=p.stat().st_size)

def read(rel,expected=None):
    p=R/rel
    require(p.resolve()==p and p.is_file(),"noncanonical input: "+rel)
    b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
    require(expected is None or expected==h,"input SHA: "+rel)
    require(rel not in READS or READS[rel]==h,"input drift: "+rel)
    READS[rel]=h
    return b

def write(name,value):
    p=HERE/name
    require(HERE in p.resolve().parents,"private output only")
    p.parent.mkdir(parents=True,exist_ok=True)
    b=value if isinstance(value,bytes) else encode(value)
    with p.open("xb") as f:f.write(b)
    return ref(p)

def load(rel,expected):
    read(rel,expected);p=R/rel
    spec=importlib.util.spec_from_file_location("outer1827_"+p.stem,p)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    return mod

def modules():
    for rel,h in PINS.items():read(rel,h)
    old=load(OLD+"/prepare.py",PINS[OLD+"/prepare.py"])
    return old,load(PREF+"contract.py",PINS[PREF+"contract.py"]),load(PREF+"runtime_scope.py",PINS[PREF+"runtime_scope.py"])

def protected(old):
    result=old.guard_protected()
    inv=json.loads(read(old.INVENTORY,old.INVENTORY_SHA))
    for rel,h in inv["files"].items():
        require(sha(S/rel)==h,"snapshot source changed: "+rel)
        READS[str(S/rel)]=h
    for rel,h in PINS.items():
        if rel.startswith(PREF):
            require(sha(P/rel)==h,"P runtime source changed: "+rel)
            READS[str(P/rel)]=h
    for rel,h in result.items():read(rel,h)
    return result

def validate_scope(plan,shard,old):
    inv=old.validate_fresh_plan(plan,shard)
    require(plan["resources"]=={
      "job_name":"cti-formal-downstream","account":"p_p15016","qos":"cpu-500_core-l40-8_card-a800-8_card",
      "partition":"L40","nodes":1,"ntasks":1,"cpus_per_task":7,"gres":"gpu:l40:1","mem":"64G","time":"04:00:00"},"original resource contract")
    require(not (R/plan["output_relative"]).exists() and not(P/plan["output_relative"]).exists(),"output already exists")
    require(not(R/plan["invocation_relative"]).exists() and not(P/plan["invocation_relative"]).exists(),"invocation already exists")
    return inv

def build():
    old,c,runtime=modules();before=protected(old)
    index=json.loads(read(OLD+"/plan_index.json",PINS[OLD+"/plan_index.json"]))
    require([(r["visual_tokens"],r["seed"]) for r in index["plans"]]==list(PAIR_ORDER),"eight shard identities")
    planner=old.load(old.PLANNER,old.PLANNER_SHA);helper=old.load(old.BUILDER,old.BUILDER_SHA)
    state_bytes=(R/old.STATE).read_bytes();state=json.loads(state_bytes)
    snapshot=write("state_snapshot_observed.json",state_bytes)
    registry_before=copy.deepcopy(state["registered_jobs"])
    require(state.get("pending_submission") is None,"pending blocks actual planner")
    scope=runtime.make_contract(project_root=R,source_root=S,suite="libero_10",stage="development")
    require(scope==runtime.make_contract(project_root=P,source_root=S,suite="libero_10",stage="development"),"R/P scope mismatch")
    runtime_watches={}
    for project in (R,P):
        for path,h in runtime.validate_contract(scope,project_root=project,source_root=S).items():
            require(path not in runtime_watches or runtime_watches[path]==h,"runtime watch conflict")
            runtime_watches[path]=h
    READS.update(runtime_watches)
    original_wrapper=load("scripts/server/run_formal_downstream.py",PINS["scripts/server/run_formal_downstream.py"])
    outer_wrapper=load(PREF+"wrapper.py",PINS[PREF+"wrapper.py"])
    files={name:PINS[name] for name in c.EXPECTED_NEW_FILES}
    files[c.ACTION_ADAPTER]=c.ACTION_SHA
    contract=dict(schema=c.SCHEMA,kind="formal_action_execution_contract",version=c.VERSION,
      status="candidate_pending_root_readiness",scientific_settings_changed=False,final_evaluation_enabled=False,
      files=files,runtime_contract=scope,GPU_acceptance=c.GPU_REFS,
      source_inventory=dict(path=c.INVENTORY,sha256=c.INVENTORY_SHA),transition=None)
    publication=[];rows=[];runtime_inputs={};root_science={}
    for shard in index["plans"]:
        name=f"k{shard['visual_tokens']}_seed{shard['seed']}"
        science_bytes=read(shard["scientific_plan"]["path"],shard["scientific_plan"]["sha256"])
        science=json.loads(science_bytes)
        manifest=shard["canonical_path"]
        read(manifest,shard["candidate"]["sha256"])
        rebuilt=planner.plan(old.plan_args(manifest),state,project=R,helper=helper)
        require(rebuilt==science,"current full-registry scientific plan differs: "+name)
        require(state["registered_jobs"]==registry_before,"full registry changed/filtered")
        inv=validate_scope(science,shard,old)
        args=original_wrapper.verify(inv)
        require(str(args.checkpoint)==scope["checkpoint"],"base checkpoint differs")
        sr=write("shards/"+name+"/scientific_plan.json",science_bytes)
        cr=write("shards/"+name+"/execution_contract.json",contract)
        science_ref=dict(path=DEST+"/"+name+"/scientific_plan.json",sha256=sr["sha256"])
        contract_ref=dict(path=DEST+"/"+name+"/execution_contract.json",sha256=cr["sha256"])
        effective=c.effective_plan(science,scientific_plan_ref=science_ref,execution_contract_ref=contract_ref,execution_contract=contract)
        er=write("shards/"+name+"/effective_plan.json",effective)
        c.validate_effective(science,effective,scientific_plan_ref=science_ref,execution_contract_ref=contract_ref,execution_contract=contract)
        try:
            outer_wrapper.verify(effective["invocation"],project=P)
        except ValueError as exc:
            require(str(exc)=="Exact path/SHA reference required","unexpected pre-readiness rejection")
            readiness_error=str(exc)
        else:raise ValueError("unsigned candidate unexpectedly accepted")
        for candidate,canonical,role in ((sr,science_ref["path"],"scientific_plan"),(cr,contract_ref["path"],"execution_contract"),(er,DEST+"/"+name+"/effective_plan.json","effective_plan")):
            publication.append(dict(candidate=candidate,canonical_path=canonical,sha256=candidate["sha256"],bytes=candidate["bytes"],role=role,pair=name))
        for rel,h in inv["root_evidence_sha256"].items():
            require(rel not in root_science or root_science[rel]==h,"science evidence conflict")
            root_science[rel]=h
        required=dict(effective["invocation"]["watched_files"])
        for rel,h in effective["publish_files"].items():
            path=str(P/c.relative(rel));require(path not in required or required[path]==h,"publish/watch conflict");required[path]=h
        for rel,h in effective["invocation"]["support_files"].items():
            path=str(P/c.relative(rel));require(path not in required or required[path]==h,"support/watch conflict");required[path]=h
        for path,h in required.items():
            require(path not in runtime_inputs or runtime_inputs[path]==h,"cross-shard runtime input conflict")
            runtime_inputs[path]=h
        projection=dict(schema="formal_main_v2",kind="candidate_action_runtime_input_projection",pair=name,
          execution_version=c.VERSION,scientific_plan=science_ref,action_execution_contract=contract_ref,
          effective_plan=dict(path=DEST+"/"+name+"/effective_plan.json",sha256=er["sha256"]),
          plan_sha256=effective["plan_sha256"],method_ids=inv["method_ids"],expected_trials=200,
          expected_development_initial_states=100,inputs=required,
          runtime_sources=files,prepared_invocation_created=False,runtime_readiness_created=False,
          submission_authorized=False,positive_full_wrapper_check_pending_genuine_readiness=True)
        pr=write("shards/"+name+"/runtime_projection.json",projection)
        rows.append(dict(pair=name,method_ids=inv["method_ids"],scientific_plan=science_ref,action_execution_contract=contract_ref,
          effective_plan=projection["effective_plan"],plan_sha256=effective["plan_sha256"],scientific_plan_sha256=science["plan_sha256"],
          runtime_projection=pr,stage_key=inv["stage_key"],run_root=inv["run_root"],invocation_relative=science["invocation_relative"],
          original_inner_P_verify=True,full_registry_original_plan_exact=True,unsigned_outer_rejected=readiness_error))
        print(json.dumps(dict(pair=name,status="pure_outer_and_real_P_science_passed_pending_root_readiness",plan_sha256=effective["plan_sha256"])),flush=True)
    require(len(rows)==8 and len({m for row in rows for m in row["method_ids"]})==16,"method duplication")
    roots=helper.Evidence(R)
    for rel,h in root_science.items():
        require(roots.watch(rel)==h,"science read evidence drift: "+rel)
        READS[rel]=h
    proposed={str(P/row["canonical_path"]):row for row in publication}
    inspections=[]
    for path,h in sorted(runtime_inputs.items()):
        p=Path(path)
        require(P in p.parents and p.resolve()==p,"noncanonical runtime input")
        c.relative(p.relative_to(P).as_posix())
        if path in proposed:
            require(proposed[path]["sha256"]==h,"candidate input conflict")
            status="present_exact" if p.is_file() and sha(p)==h else "missing_planned_candidate"
            require(not p.exists() or status=="present_exact","planned P destination contains different bytes")
        else:
            require(p.is_file() and sha(p)==h,"existing P runtime input missing or changed: "+path)
            READS[path]=h;status="present_exact"
        inspections.append(dict(path=path,sha256=h,status=status))
    for row in publication:
        for project in (R,P):
            p=project/row["canonical_path"]
            require(not p.exists() or (p.is_file() and sha(p)==row["sha256"]),"canonical publication conflict")
        row["R_present_exact"]=(R/row["canonical_path"]).is_file()
        row["P_present_exact"]=(P/row["canonical_path"]).is_file()
    require(protected(old)==before,"protected files changed")
    runtime.unchanged(runtime_watches)
    root_proof=json.loads(read(old.ROOT_CHECK,old.ROOT_CHECK_SHA))
    require(root_proof["original_development_GPU_seconds"]==10531 and root_proof["submission_authorized"] is False,"old cost proof")
    publication_ref=write("publication_map.json",dict(schema="formal_main_v2",kind="Long16_outer_candidate_publication",status="candidate_only",
      canonical_prefix=DEST,files=publication,publication_authorized_by_this_file=False,state_or_submission_changed=False))
    index_ref=write("outer_index.json",dict(schema="formal_main_v2",kind="Long16_eight_action_outer_candidates",status="candidate_pending_root_readiness",
      execution_version=c.VERSION,shards=rows,expected_total_trials=1600,methods=sorted(m for r in rows for m in r["method_ids"]),
      unique_development_initial_states_per_method=100,publication_map=publication_ref,
      state_observation=snapshot,registry_count=len(registry_before),registry_unfiltered=True,
      historical_Long_GPU_seconds=10531,historical_cost_reference=dict(path=old.ROOT_CHECK,sha256=old.ROOT_CHECK_SHA),
      history_reused_as_new_results=False,scientific_settings_changed=False,final_release=False,submission_authorized=False))
    write("P_runtime_inputs_observation.json",dict(schema="formal_main_v2",kind="actual_P_dependency_observation",inputs=inspections,
      missing_planned_candidates=[x for x in inspections if x["status"]!="present_exact"],
      positive_full_wrapper_pending=True))
    write("science_read_evidence.json",root_science)
    write("read_evidence_sha256.json",READS)
    write("build_result.json",dict(status="passed_CPU_outer_preparation_pending_root_and_independent_readiness",
      publication_map=publication_ref,outer_index=index_ref,eight_original_plans_exact=True,
      original_inner_P_checks=8,actual_runtime_R_P_checks=2,unsigned_outer_rejections=8,
      new_GPU_seconds=0,new_trials=0,protected_before_after_equal=True,root_or_independent_reviews_created=False))
    return index_ref

def verify_published():
    old,c,runtime=modules();before=protected(old)
    mapping=json.loads(read(HERE.relative_to(R).as_posix()+"/publication_map.json"))
    index=json.loads(read(HERE.relative_to(R).as_posix()+"/outer_index.json"))
    observed={}
    for row in mapping["files"]:
        for project in (R,P):
            p=project/row["canonical_path"];require(p.is_file() and sha(p)==row["sha256"],"publication absent/mismatch: "+str(p))
            observed[str(p)]=row["sha256"]
    original_wrapper=load("scripts/server/run_formal_downstream.py",PINS["scripts/server/run_formal_downstream.py"])
    for row in index["shards"]:
        science=c.read_ref(R,row["scientific_plan"]);contract=c.read_ref(R,row["action_execution_contract"]);effective=c.read_ref(R,row["effective_plan"])
        c.validate_effective(science,effective,scientific_plan_ref=row["scientific_plan"],execution_contract_ref=row["action_execution_contract"],execution_contract=contract)
        original_wrapper.verify(science["invocation"])
        observed.update(runtime.validate_contract(contract["runtime_contract"],project_root=P,source_root=S))
        for path,h in effective["invocation"]["watched_files"].items():
            require(sha(path)==h,"actual full outer dependency drift");observed[path]=h
    require(protected(old)==before,"protected drift")
    return dict(status="passed_actual_canonical_dependency_check_only_pending_readiness",shards=8,
      actual_R_P_files=observed,new_trials=0,new_GPU_seconds=0,root_readiness_created=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument("mode",choices=("build","verify-published"));args=parser.parse_args()
    if args.mode=="build":result=build()
    else:result=verify_published();write("published_check.json",result)
    print(json.dumps(dict(mode=args.mode,status="complete_CPU_only",result=result if args.mode=="build" else result["status"])),flush=True)

if __name__=="__main__":
    try:main()
    except Exception:
        traceback.print_exc();raise
