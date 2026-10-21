from pathlib import Path
import hashlib,importlib.util,json,os,sys
from datetime import datetime,timezone
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B="results/formal_main_v2/preflight/heartbeat_20261021T0910";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0110"
STATE="results/experiment_supervisor/state.json";BEFORE="40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(rel,pin=None):
 p=R/rel
 if pin is not None:assert h(p)==pin,rel
 return json.loads(p.read_bytes())
def ref(rel):return dict(path=rel,sha256=h(R/rel),bytes=(R/rel).stat().st_size)
def new(rel,v):
 p=R/rel;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
rp="results/formal_main_v2/downstream_reviews/3054201.json";rr=rd(rp,"c4452ea92281151bf485f41777257392edf008e48f6268c78be9cfc17f115b92")
ip=E+"/Downstream_runtime_independent/Spatial_terminal/independent_review.json";ind=rd(ip,"6c3bb9e368d738d547017f4abfd4d3e2f504ab85c79b0ce9dc788ca8e4a13c34")
op=B+"/terminal_observation_from_Object_preflight.json";obs=rd(op,"89820eb12808cce09c4882c7ce17d189b44b8e01c460299663a32fd0c64e3c94")
cp=B+"/Spatial3054201_terminal_v2/completion.json";done=rd(cp,"d071b418ab0f188acabc2fbb5ce8ab0aae66e8c4ab0550e8f5a0c60a6404c3cb")
assert rr["status"]=="passed" and rr["scientific_complete"] and rr["completed_trials"]==600 and rr["bounded_development_admission"]
assert ind["status"]=="passed_real_raw_terminal_review" and ind["blockers"]==[] and ind["check_count"]==14793
assert ind["root_review"]["sha256"]==h(R/rp) and ind["root_completion_sha256"]==h(R/cp)
assert all(ind[k] for k in ["original_typed_consumer_rebuilt","actual_R_P_nonweight_hashes_verified","original_legacy_prefix_preserved","source173_verified"])
assert ind["current_wrapper_trials"]==588 and ind["legacy_compatible_trials"]==12 and ind["global_unique_development_initial_states_added"]==0
assert all(ind[k] is False for k in ["eligible_for_current_action_global_freeze","profiling_authorized","final_release"])
assert obs["state_sha256"]==BEFORE and obs["all_formal_allocations_terminal"] and not obs["capacity"]["occupied"]
for rel,want in rr["files"].items():assert h(R/rel)==want and h(P/rel)==want,rel
source=rd("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
assert len(source["files"])==173
for rel,want in source["files"].items():
 for base in (R,P/"snapshots/formal_main_v2_run_564be0995e",R/"snapshots/formal_main_v2_run_564be0995e"):assert h(base/rel)==want,rel
control=R/"scripts/ops/formal_autonomous_training_v1/controller.py";assert h(control)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
sp=importlib.util.spec_from_file_location("accept_spatial_0910",control);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 assert h(R/STATE)==BEFORE
 state=rd(STATE);f=state["formal_main_progress"];cur=f["new_action_development_verified_by_job"]
 assert "3054201" not in cur and sum(x["completed_trials"] for x in cur.values())==f["current_action_development_trial_count"]==5800
 assert f["completed_development_trials"]==7012 and f["historical_other_action_semantics_development_trials"]==1212 and f["current_action_development_unique_initial_states"]==400
 assert state.get("pending_submission") is None and state["autonomous_training_v1"].get("pending_submission") is None
 rows=obs["observation"]["rows"];ids=[str(j["job_id"]) for j in state["registered_jobs"] if j.get("experiment")=="formal_main_v2"]
 assert len(ids)==len(set(ids))==271
 sec=sum(rows[j]["elapsed_seconds"]*rows[j]["gpus"] for j in ids);assert sec==1991937
 origin=ind["origin_breakdown"];current=origin["3054201"];legacy=origin["3022743"]
 assert current["completed_trials"]==588 and current["unique_initial_states"]==98 and legacy["completed_trials"]==12
 acceptance=dict(schema="formal_main_v2",kind="root_Spatial588_bounded_development_acceptance",status="accepted_after_original_typed_consumer_and_independent_raw_review",reviewed_by="root",utc=datetime.now(timezone.utc).isoformat(),job_id="3054201",new_current_trials=588,retained_legacy_compatible_trials=12,complete_mixed_panel_trials=600,panel_unique_initial_states=100,global_unique_initial_states=400,global_unique_initial_states_added=0,origin_breakdown=origin,mixed_panel_methods=ind["methods"],root_review=ref(rp),independent_review=ref(ip),completion=ref(cp),pull=done["pull"],original_failures_retained=True,cost=ind["cost"],current_action_global_freeze_eligible=False,profiling_authorized=False,final_release=False,sealed_final_unread=True,new_GPU_submissions=0,state_before_sha256=BEFORE,complete_development_batch_trials_after=7000,current_action_trials_after=6388,historical_accepted_trials_after=7600,Object599_still_separate_legacy_adoption=True)
 ap=B+"/Spatial3054201_root_acceptance.json";new(ap,acceptance)
 cur["3054201"]=dict(job_id="3054201",suite="libero_spatial",seed=17,visual_tokens=128,completed_trials=588,unique_initial_states=98,successes={m:v["successes"] for m,v in current["methods"].items()},per_method_trials=98,root_review=ref(rp),independent_review=ref(ip),root_acceptance=ref(ap),raw_ledger=ref("results/formal_main_v2/libero_spatial/downstream/development/8c843c1d4ee8383c/attempt01/trials.jsonl"),mixed_panel_total_trials=600,retained_legacy_compatible_trials=12,mixed_panel_unique_initial_states=100,global_unique_initial_states_added=0,GPU_seconds=6635,all_linked_attempt_GPU_seconds=7030,GPU_cost_scope="Each allocation once;393 legacy+2 predispatch failure+6635 new, already included in global unique cost.",O2A_complete=False,scientific_final_release=False,eligible_for_current_action_global_freeze=False)
 f["current_action_development_trial_count"]=sum(x["completed_trials"] for x in cur.values());assert f["current_action_development_trial_count"]==6388
 f["completed_development_trials"]=f["current_action_development_trial_count"]+f["historical_other_action_semantics_development_trials"];assert f["completed_development_trials"]==7600
 f["complete_development_batches_accepted_trials"]=7000;f["complete_development_batches_compatible_legacy_trials"]=612
 f["Spatial588_root_terminal_acceptance_20261021T0110"]=ref(ap)
 f["latest_new_action_development_verified"]={"job_id":"3054201","root_acceptance":ref(ap),"new_current_trials":588,"full_mixed_panel":600,"legacy_retained":12}
 for j in state["registered_jobs"]:
  if str(j["job_id"])=="3054201":j.update(status="COMPLETED",raw_status="COMPLETED",exit_code="0:0",elapsed_seconds=6635,terminal_observation=ref(op),root_terminal_acceptance=ref(ap))
 state["current_round_cost"]=dict(allocated_gpu_hours=sec/3600,allocated_gpu_seconds=sec,final=True,historical_jobs_excluded=True,registered_jobs=271,scope="All271 unique formal allocations terminal at "+obs["utc"]+";retained setup/loading/cache/failure/engineering costs counted once;no future allocations included.",observation=ref(op))
 state["updated_utc"]=datetime.now(timezone.utc).isoformat()
 state["current_work"]="Training72 complete. Spatial588 raw terminal accepted:6388 current+612 compatible=7000/8800 complete batches;Object599 separate legacy;remaining Object/Goal gates;O2A/final closed."
 new(B+"/Spatial3054201_state_before.json",rd(STATE))
 payload=(json.dumps(state,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
 tmp=R/(STATE+".spatial0910.tmp");assert not tmp.exists()
 with tmp.open("xb") as out:out.write(payload);out.flush();os.fsync(out.fileno())
 assert h(R/STATE)==BEFORE;os.replace(tmp,R/STATE)
 receipt=dict(status="root_acceptance_and_state_CAS_complete",acceptance=ref(ap),before_sha256=BEFORE,after_sha256=h(R/STATE),new_current_trials=588,complete_batch_trials=7000,current_trials=6388,historical_accepted_trials=7600,unique_initial_states=400,GPU_seconds=sec,new_GPU_jobs=[])
 new(B+"/Spatial3054201_acceptance_transaction.json",receipt);print(json.dumps(receipt))
