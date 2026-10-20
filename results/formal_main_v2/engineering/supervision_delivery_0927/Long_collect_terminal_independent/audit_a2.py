from __future__ import annotations
from pathlib import Path
import sys, os, json, hashlib, importlib.util, traceback
from datetime import datetime, timezone
import numpy as np

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
S=P/"snapshots/formal_main_v2_run_564be0995e"
D=R/".local/Long_collect_terminal_independent_0927"
Orel="results/formal_main_v2/libero_10/downstream/collect/648ce4233e78353e/attempt01"
O=R/Orel
C="results/formal_main_v2/execution/long_collect_action_v1_0830/"
PULL="results/formal_main_v2/pulls/20261020T092912Z_f00b82b82873/receipt.json"
SNAP="results/formal_main_v2/preflight/heartbeat_20261020T1727/terminal_jobs_snapshot.json"
ROOT_REVIEW="results/formal_main_v2/downstream_reviews/3047982.json"
INV="results/formal_main_v2/invocations/libero_10_collect_648ce4233e78353e_attempt01.json"
INV_SRC="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json"
DEV="configs/manifests/formal_main_v2/libero_10/initial_states/development.json"
REG="configs/experiments/formal_main_v2.json"
REVIEWER="scripts/ops/formal_action_deployment_v1/reviewer.py"
CONSUMER="scripts/ops/formal_action_deployment_v1/consumer.py"
PINS={
PULL:"c97df5b4d1bf9b1793b4c62898eb255a832e5849244f4df0f21fa358087e9eb3",
SNAP:"30c4df52d1043dc1d6216ffcd55b394d0c3424865cb511ae585a7816b2358a9f",
ROOT_REVIEW:"45e76fbb32159d53dc7be7e5ca6b25d4d52815d44d0234063f30a69500567479",
INV:"4f12f98f6c7027961eb14d3de07fd27387e8f30dc4edab2490a7649b0b2109be",
INV_SRC:"5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926",
DEV:"46a06087483151e36198167e7d4e5313c50b63172e09128d65a3650112f0a268",
REG:"a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9",
REVIEWER:"9107560ef95eabf8e22a452d8dfb23ca552a85cfd3fc55f35cb38795475f65fd",
CONSUMER:"16c574cb2ab05f8493547e8174b685c78273d00577df4788f3d601b1e2d6d034",
C+"scientific_plan.json":"1c50e85dfea3042cb7cee74cf5482e2325e4036e0bc7a74187d0061983790ee0",
C+"effective_plan.json":"1ce34d9ecf18e36d2c0043e2fdfd42ca327344d286fb35704fdfe70e8b5ed8ac",
C+"execution_contract.json":"06ca8c538a323e14ad8197a80e9cc5c39d303976adbd8959630e535b11b1acc0",
C+"dense_development.json":"703980515d5b063c31276b0e610ffd6cdf68adae5e1f43cfb65ecd61d92923f1",
C+"runtime_readiness.json":"0430a393e1153ac9a0513d7ebf5e31b05f2401c3dff91035206f10d0e36bc1b1",
C+"independent_runtime_review.json":"e4f6635642d93585c4ba7c60a35af03e9ea4260405a0bdb732fe2eef5aabd242",
C+"submission_authorization.json":"e00503d5d79d397a8fc8016cb674c7d9f728c05e8229c3b3fe5e101f36e3f67b",
Orel+"/config.json":"d92b77bbf9ab1df249f77fc83b9e6eea38d15f3f659dbf4b4343e44726c517e9",
Orel+"/panel.json":"d06a6d7b1c90aed765b9121ec9909fbe14c4d491c0f9d7f9c321a156bfdb1b9c",
Orel+"/summary.json":"2c10c8d382d79bd70162cbb60c08744c35db3a6d66764f2a93d1e050952b6c7f"}
checks=[]
watched={}
def check(value,label):
    if not value: raise AssertionError(label)
    checks.append(label)
def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sig(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def read(p):
    p=Path(p); raw=p.read_bytes(); watched[str(p)]=hashlib.sha256(raw).hexdigest()
    def unique(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError("duplicate JSON key")
            out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x)))
def save(name,value):
    p=D/name
    with p.open("x",encoding="utf-8") as f:
        f.write(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n")
def ref(rel):return {"path":rel,"sha256":digest(R/rel)}
def load(name,rel):
    spec=importlib.util.spec_from_file_location(name,R/rel)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod
def guard(event,args):
    if event in ("subprocess.Popen","os.system","socket.connect","socket.bind"):
        raise RuntimeError("Independent CPU audit cannot spawn commands/network")
    if event=="open":
        p,mode,flags=args
        if isinstance(p,(str,bytes)):
            q=Path(os.fsdecode(p)).absolute()
            write=any(c in str(mode or "") for c in "wax+") or (isinstance(flags,int) and bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))
            if write and D not in q.parents:raise RuntimeError("Write outside private audit directory")
            if q.suffix.lower() in (".pt",".pth",".bin",".ckpt",".safetensors",".pkl",".pickle",".init",".pruned_init"):
                raise RuntimeError("Weight or sealed state payload forbidden")
            if q==R/"results/experiment_supervisor/state.json":raise RuntimeError("No mutable supervisor state reads")
sys.addaudithook(guard)

def main():
    for rel,h in PINS.items():check(digest(R/rel)==h,"pin:"+rel)
    inventory=read(R/INV_SRC)
    check(len(inventory["files"])==173,"173 frozen files")
    check(inventory["source_sha256"]=="dd3e5450e80b8e1f05a78acf6a05daf393f7362420fd8e87a8e6f5ec03feb61e","frozen aggregate identity")
    for rel,h in inventory["files"].items():
        check(digest(R/rel)==h,"frozen R:"+rel)
        check(digest(S/rel)==h,"frozen S:"+rel)
    invocation=read(R/INV); check(digest(P/INV)==PINS[INV],"actual P invocation exact bytes")
    science=read(R/(C+"scientific_plan.json")); effective=read(R/(C+"effective_plan.json"))
    for label,plan in [("science",science),("effective",effective)]:
        check(sig({k:v for k,v in plan.items() if k!="plan_sha256"})==plan["plan_sha256"],label+" canonical plan digest")
        check(plan["invocation_relative"]==INV and plan["output_relative"]==Orel,label+" invocation/output")
        check(plan["invocation"]["stage"]=="collect" and plan["invocation"]["method_ids"]==["dense"],label+" dense collect only")
    check(invocation["stage"]=="collect" and invocation["method_ids"]==["dense"] and invocation["prior_job_ids"]==[] and not invocation["resume"],"single collection invocation")
    check(invocation["scientific_settings_changed"] is False and invocation["final_values_read_locally"] is False,"no science change or final state read")
    pull=read(R/PULL)
    check(pull["status"]=="verified_nonweight_snapshot" and pull["weights_copied"] is False and pull["sealed_initial_states_copied"] is False,"original nonweight pull")
    check(pull["requested_job_ids"]==["3047982"] and not pull["missing"] and not pull["excluded"],"exact complete single-job pull")
    check(len(pull["files"])==53,"53 pulled nonweight files")
    for f in pull["files"]:
        rel=f["relative"]
        check(digest(R/rel)==f["sha256"] and (R/rel).stat().st_size==f["bytes"],"pull R:"+rel)
        check(digest(P/rel)==f["sha256"] and (P/rel).stat().st_size==f["bytes"],"pull P:"+rel)
    snapshot=read(R/SNAP);jobs=snapshot["registered_jobs"]
    matches=[j for j in jobs if str(j["job_id"])=="3047982"]
    check(len(matches)==1,"unique immutable terminal job")
    job=matches[0]
    check(job["status"]=="COMPLETED" and job["exit_code"]=="0:0" and job["elapsed_seconds"]==472,"real successful Slurm terminal 472s")
    check(job["mode"]=="collect" and job["suite"]=="libero_10" and job["run_root"]==str(P/Orel),"registered collection identity")
    check([str(j["job_id"]) for j in jobs if j.get("stage_key")==job["stage_key"]]==["3047982"],"no second registered collection allocation")
    reviewer=load("independent_long_collect_action_reviewer_0927",REVIEWER)
    rebuilt=reviewer.review(R,job=job,invocation_ref=ref(INV),pull_ref=ref(PULL),registered_jobs=jobs,expected_contract_ref=ref(C+"execution_contract.json"))
    check(rebuilt["scientific_complete"] is True and rebuilt["observations"]==30 and rebuilt["completed_collection_trajectories"]==10,"original reviewer complete raw collect")
    root=read(R/ROOT_REVIEW)
    clean=lambda x:{k:v for k,v in x.items() if k!="reviewed_utc"}
    check(clean(rebuilt)==clean(root),"independent original reviewer equals actual root receipt except review time")
    consumer=load("independent_long_collect_action_consumer_0927",CONSUMER)
    ev=reviewer.Evidence(R)
    consumed=consumer.review_downstream_output(ev,ref(ROOT_REVIEW),expected_stage="collect",suite="libero_10",run_root=job["run_root"])
    check(clean(consumed)==clean(rebuilt),"original exact-version consumer full reconstruction")
    for k in ["weights_read","final_state_values_read","final_release","old_report_or_invocation_fabricated"]:
        check(rebuilt[k] is False,"reviewer boundary:"+k)
    from cti_vla.evaluation import formal_profiling as fp
    from cti_vla.evaluation.profiling import RAW_KEYS, RawObservation, observation_signature
    from cti_vla.evaluation.libero_runtime import _observation_hash
    development=read(R/DEV);reg=read(R/REG);manifest=read(R/(C+"dense_development.json"))
    config=read(O/"config.json");panel=read(O/"panel.json");summary=read(O/"summary.json")
    check(config["command"]=="collect" and config["slurm_job_id"]=="3047982","actual collect command/job")
    check(config["future_head_deployed"] is False and config["test_opened"] is False,"no future head or test deployment")
    identity=manifest["methods"][0]["identity"]
    check(identity==config["dense_identity"] and identity["visual_tokens"]==512 and identity["model_revision"]=="95220f9a3421a7ff12d4218e73d09ade830fa9a3","official frozen Long Dense identity")
    states=[min([s for s in development["states"] if s["task_id"]==i],key=lambda s:s["source_state_index"]) for i in range(10)]
    check([s["source_state_index"] for s in states]==[0,4,7,3,6,2,3,6,8,2],"ten preregistered minimum development source indices")
    check(fp.fixed_profile_states(development)==states,"independent selection equals original function")
    check(panel["development_panel_sha256"]==sig(development),"canonical development signature distinct from raw SHA")
    check(panel["content_signature"]==sig({k:v for k,v in panel.items() if k!="content_signature"}),"panel signed content")
    samples,panelmeta=fp.load_profile_panel(O/"panel.json",development=development,registration=reg,dense_identity=identity)
    check(len(samples)==30 and panelmeta==summary["panel"],"original loader 30 immutable raw observations")
    events=[reviewer.json_bytes(s) for s in (O/"collection_trials.jsonl").read_bytes().splitlines()]
    check(len(events)==20 and [e["event"] for e in events]==["start","result"]*10,"exact ten unfiltered start/result pairs")
    expectedshapes={"agentview_image":("uint8",(256,256,3)),"robot0_eye_in_hand_image":("uint8",(256,256,3)),"robot0_eef_pos":("float64",(3,)),"robot0_eef_quat":("float64",(4,)),"robot0_gripper_qpos":("float64",(2,))}
    details=[];totalsteps=0;calls=0
    for task,state in enumerate(states):
        start,row=events[2*task:2*task+2]
        for e in (start,row):
            check(e["trial_id"]==state["trial_id"] and e["method"]=="dense" and e["run_signature"]==sig(config),f"raw trial fixed identity {task}")
        receipt=read(O/f"task{task:02d}/receipt.json");tr=receipt["trajectory"];n=tr["control_steps"];selected=[0,(n-1)//2,n-1]
        check(receipt["state"]=={k:state[k] for k in fp.STATE_FIELDS},f"full state metadata {task}")
        check(receipt["content_signature"]==sig({k:v for k,v in receipt.items() if k!="content_signature"}),f"receipt content {task}")
        check(tr=={k:v for k,v in row.items() if k not in ("event","method","trial_id","run_signature")},f"raw trial equals receipt {task}")
        check(tr["status"]=="completed" and tr["wait_steps"]==10 and 3<=n<=520,f"wait/horizon {task}")
        check(tr["success"] or (n==520 and tr["termination"]=="task_horizon"),f"unsuccessful trajectory not replaced {task}")
        check([o["control_step"] for o in receipt["observations"]]==selected and len(set(selected))==3,f"actual first/middle/last {task}")
        hashes=receipt["all_control_observation_sha256"]
        check(len(hashes)==n and all(len(h)==64 for h in hashes),f"all real control observation hashes {task}")
        check([c["control_step"] for c in tr["chunks"]]==list(range(0,n,8)),f"chunk8 cadence {task}")
        check(len(tr["executed_actions"])==n and tr["policy_calls"]==len(tr["chunks"])==(n+7)//8,f"actions and policy call count {task}")
        for c in tr["chunks"]:
            step=c["control_step"];meta=c["metadata"]
            check(c["observation_sha256"]==hashes[step],f"pre-action policy query {task}:{step}")
            check(np.array_equal(np.asarray(tr["executed_actions"][step:min(step+8,n)]),np.asarray(c["environment_actions"][:min(8,n-step)])),f"executed chunk actions {task}:{step}")
            check(meta["method"]=="dense" and meta["future_head_calls"]==0 and meta["visual_tokens"]==512 and meta["per_camera_budgets"]==[256,256] and meta["policy_calls"]==1 and meta["vision_calls"]==1 and meta["scorer_calls"]==0 and meta["packing_calls"]==1,f"actual Dense deployment counters {task}:{step}")
        for item,step,phase in zip(receipt["observations"],selected,("first","middle","last")):
            path=O/f"task{task:02d}"/item["arrays"]["path"]
            check(item["phase"]==phase and path.name==phase+".npz" and digest(path)==item["arrays"]["sha256"],f"NPZ identity {task}:{phase}")
            with np.load(path,allow_pickle=False) as archive:
                check(set(archive.files)==set(RAW_KEYS)==set(expectedshapes),f"only current raw inputs {task}:{phase}")
                arrays={k:archive[k].copy() for k in archive.files}
            check(all(not a.dtype.hasobject and np.isfinite(a).all() for a in arrays.values()),f"raw arrays numeric no pickle {task}:{phase}")
            check(all((str(arrays[k].dtype),arrays[k].shape)==expectedshapes[k] for k in arrays),f"unprocessed native arrays {task}:{phase}")
            hraw=hashlib.sha256();hroll=hashlib.sha256()
            for key in RAW_KEYS:
                a=np.ascontiguousarray(arrays[key])
                hraw.update(json.dumps([key,a.dtype.str,a.shape]).encode());hraw.update(a.tobytes())
                hroll.update(key.encode()+str(a.dtype).encode()+str(a.shape).encode()+a.tobytes())
            sample=RawObservation(item["observation_id"],state["trial_id"],state["task_name"],receipt["instruction"],phase,arrays)
            check(hraw.hexdigest()==item["raw_sha256"]==observation_signature(sample),f"independent raw observation hash {task}:{phase}")
            check(hroll.hexdigest()==item["rollout_observation_sha256"]==hashes[step]==_observation_hash(arrays),f"independent timeline hash {task}:{phase}")
        check(receipt["new_success_trials"] is False and receipt["test_opened"] is False and receipt["provenance"]==panel["provenance"],f"scope/provenance {task}")
        details.append({"task_id":task,"source_state_index":state["source_state_index"],"actual_control_steps":n,"selected_control_steps":selected,"policy_calls":tr["policy_calls"],"termination":tr["termination"],"collection_success_diagnostic_only":tr["success"]})
        totalsteps+=n;calls+=tr["policy_calls"]
    check(totalsteps==2917 and calls==369 and summary["policy_calls"]==calls,"all collection control steps and calls")
    check(details[-1]["collection_success_diagnostic_only"] is False and details[-1]["actual_control_steps"]==520,"failed task9 retained")
    check(summary["new_success_trials"] is False and summary["test_opened"] is False and panel["new_success_trials"] is False,"zero success denominator addition")
    check(rebuilt["cost"]["current_gpu_seconds"]==472 and rebuilt["cost"]["all_attempt_gpu_seconds"]==472 and len(rebuilt["cost"]["allocations"])==1,"all single-allocation GPU cost")
    wall=summary["execution_wall_seconds_including_model_loading"];loadsec=config["model_loading_seconds_excluded_from_calls"]
    check(0<loadsec<wall<472,"model load included in allocation and complete collection wall")
    for rel,h in inventory["files"].items():check(digest(R/rel)==h and digest(S/rel)==h,"frozen unchanged at exit:"+rel)
    ev.unchanged()
    for path,h in watched.items():check(digest(path)==h,"immutable input unchanged:"+path)
    proof={"original_reviewer_source":ref(REVIEWER),"original_consumer_source":ref(CONSUMER),"root_receipt":ref(ROOT_REVIEW),"reviewer_rebuilt_equal_except_reviewed_utc":True,"consumer_rebuilt_equal_except_reviewed_utc":True,"canonical_rebuilt_without_time_sha256":sig(clean(rebuilt)),"evidence_sha256":rebuilt["evidence_sha256"],"actual_runtime_review":rebuilt["actual_runtime_review"],"cost":rebuilt["cost"],"registered_job_snapshot":ref(SNAP),"pull_receipt":ref(PULL)}
    save("original_reconstruction_proof.json",proof)
    report={"schema":"formal_main_v2","kind":"independent_collect_terminal_review","status":"passed","reviewed_by":"independent_subagent","job_id":"3047982","suite":"libero_10","stage":"collect","scientific_complete":True,"scope":"Original collect only: fixed raw observation panel; no success-rate addition, no O2A or component timing result, no global release","root_review":ref(ROOT_REVIEW),"invocation":ref(INV),"action_execution_contract":ref(C+"execution_contract.json"),"pull_receipt":ref(PULL),"terminal_snapshot":ref(SNAP),"checks_passed":len(checks),"checks":checks,"audit_attempts":{"a1":"Independent script KeyError per_camera after original reviewer and consumer succeeded; no collection error","a2":"Use exact frozen metadata key per_camera_budgets; production code and evidence unchanged"},"source_frozen_files":173,"panel":ref(Orel+"/panel.json"),"observations":30,"collection_trajectories":10,"collection_control_steps":totalsteps,"collection_policy_calls":calls,"tasks":details,"cost":{"gpu_seconds":472,"gpu_hours":472/3600,"execution_wall_seconds_including_model_loading":wall,"model_loading_seconds_included_in_allocation":loadsec,"all_registered_allocations_counted":1},"constraints":{"all_fixed_task_and_state_identities_preserved":True,"failure_trajectory_not_filtered":True,"only_actual_pre_action_observations":True,"NPZ_allow_pickle":False,"future_head_deployed":False,"new_success_trials":0,"O2A_measurements_produced":False,"full_components_global_freeze_still_required":True,"final_release":False,"weights_read":False,"sealed_values_read":False,"models_loaded":False,"GPU_or_scheduler_queries":False,"state_registry_or_Git_writes":False},"original_reviewer_and_consumer_both_executed":True,"reconstruction_proof":{"path":str((D/"original_reconstruction_proof.json").relative_to(R)),"sha256":digest(D/"original_reconstruction_proof.json")},"reviewed_utc":datetime.now(timezone.utc).isoformat()}
    save("independent_review.json",report)
    files=[{"path":str(p.relative_to(R)),"sha256":digest(p),"bytes":p.stat().st_size} for p in sorted(D.iterdir()) if p.is_file() and p.name!="manifest.json"]
    save("manifest.json",{"kind":"independent_audit_manifest","files":files,"source_frozen_files":173})
    print(json.dumps({"status":"passed","checks":len(checks),"observations":30,"gpu_seconds":472,"report_sha256":digest(D/"independent_review.json"),"manifest_sha256":digest(D/"manifest.json")}))
if __name__=="__main__":
    try:main()
    except BaseException as exc:
        save("failure_a2.json",{"status":"failed","type":type(exc).__name__,"error":str(exc),"traceback":traceback.format_exc(),"checks_passed":len(checks)})
        raise
