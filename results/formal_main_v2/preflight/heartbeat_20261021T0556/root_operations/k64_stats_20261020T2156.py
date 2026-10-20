from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,time
import numpy as np
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
B=R/"results/formal_main_v2/preflight/heartbeat_20261021T0556"
ST="cf54288d932880c061936f89f94dd3fb9b71c99382226d5276bb694fe6c2f33a"
SEEDS=[17,23,41]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
refs=[]
def rd(rel,pin=None):
 p=R/rel;digest=h(p)
 if pin is not None:assert digest==pin,rel
 refs.append(dict(path=rel,sha256=digest))
 return json.loads(p.read_bytes())
def save(name,v):
 p=B/name
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
 return dict(path=p.relative_to(R).as_posix(),sha256=h(p))
s=rd("results/experiment_supervisor/state.json",ST);f=s["formal_main_progress"]
reg=rd("configs/experiments/formal_main_v2.json","a3f35d8e96d701c1a9ebadc2ad02259372cf6c91da6c9cb8d57c231892cf6ff9")
assert reg["statistics"]["bootstrap_repeats"]==10000 and reg["statistics"]["bootstrap_seed"]==20261016 and reg["statistics"]["seed_sd_ddof"]==1
suite_out={}
for suite in ["libero_spatial","libero_object"]:
 panel=rd("configs/manifests/formal_main_v2/"+suite+"/initial_states/development.json")
 assert panel["suite"]==suite and panel["split"]=="development"
 states=sorted(panel["states"],key=lambda x:(x["task_id"],x["source_state_index"],x["trial_id"]))
 assert len(states)==100 and len({x["trial_id"] for x in states})==100 and all(sum(x["task_id"]==t for x in states)==10 for t in range(10))
 data={};byseed={};allocations=[]
 for seed in SEEDS:
  methods=[f"A64_seed{seed}",f"B64_seed{seed}"]
  jobs=[j for j in s["registered_jobs"] if j.get("suite")==suite and j.get("mode")=="development" and j.get("method_ids")==methods and j["job_id"] in f["new_action_development_verified_by_job"]]
  assert len(jobs)==1
  j=jobs[0];e=f["new_action_development_verified_by_job"][j["job_id"]];rr=e["root_review"];root=rd(rr["path"],rr["sha256"]);q=root["reconstructed_summary"]
  assert root["status"]=="passed" and root["scientific_complete"] and root["completed_trials"]==200 and root["execution_version"]=="formal-downstream-action-v1" and not root["final_state_values_read"] and not root["final_release"]
  ir=e["independent_review"];ind=rd(ir["path"],ir["sha256"]);assert ind["status"]=="passed"
  rawrel=str(Path(j["run_root"]).relative_to("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")/"trials.jsonl")
  raw=R/rawrel;assert h(raw)==q["trials_jsonl_sha256"]
  refs.append(dict(path=rawrel,sha256=h(raw)))
  results=[json.loads(line) for line in raw.read_bytes().splitlines() if line]
  outcomes=[z for z in results if z.get("event")=="result"]
  assert len(outcomes)==200 and all(z["status"]=="completed" and type(z["success"]) is bool for z in outcomes)
  actual={(z["state_trial_id"],z["method"]):z["success"] for z in outcomes}
  assert len(actual)==200
  pairs=q["paired_AB"][f"k64_seed{seed}"]["results"]
  assert len(pairs)==100 and {z["state_trial_id"] for z in pairs}=={z["trial_id"] for z in states}
  for z in pairs:
   for m,arm in zip(methods,["A","B"]):
    assert actual[z["state_trial_id"],m]==z[arm+"_success"]
    data[z["state_trial_id"],m]=int(z[arm+"_success"])
  byseed[str(seed)]={"job_id":j["job_id"],"root_review":rr,"independent_review":ir}
  assert j["status"]=="COMPLETED" and j["exit_code"]=="0:0" and j["gpus"]==1
  allocations.append({"job_id":j["job_id"],"GPU_seconds":j["elapsed_seconds"]})
 methods=[f"{arm}64_seed{seed}" for seed in SEEDS for arm in ["A","B"]]
 v=np.array([[data[x["trial_id"],m] for m in methods] for x in states],dtype=np.int64).reshape(10,10,6)
 rng=np.random.default_rng(20261016);counts=np.zeros((10000,6),dtype=np.int64);dh=hashlib.sha256()
 for task in range(10):
  idx=rng.integers(0,10,size=(10000,10));dh.update(idx.astype("<i8").tobytes(order="C"));counts+=v[task][idx].sum(axis=1)
 draw=counts/100.;A=v[:,:,[0,2,4]].mean(axis=(0,1));BB=v[:,:,[1,3,5]].mean(axis=(0,1))
 diffdraw=(counts[:,[1,3,5]].sum(axis=1)-counts[:,[0,2,4]].sum(axis=1))/300.
 for i,seed in enumerate(SEEDS):
  a=v[:,:,2*i];b=v[:,:,2*i+1];byseed[str(seed)].update(A_successes=int(a.sum()),B_successes=int(b.sum()),A_rate=float(a.mean()),B_rate=float(b.mean()),B_minus_A=float((b-a).mean()),A_only=int(((a==1)&(b==0)).sum()),B_only=int(((a==0)&(b==1)).sum()),per_task_A_successes=a.sum(axis=1).tolist(),per_task_B_successes=b.sum(axis=1).tolist(),per_task_B_minus_A=(b-a).mean(axis=1).tolist())
 matrix=save(suite+"_k64_paired_states.json",{"method_order":methods,"states":[{"state_trial_id":x["trial_id"],"task_id":x["task_id"],"source_state_index":x["source_state_index"],"success_vector":[data[x["trial_id"],m] for m in methods]} for x in states],"unique_state_clusters":100})
 draws=save(suite+"_k64_bootstrap_draws.json",{"method_order":methods,"bootstrap_seed":20261016,"repeats":10000,"draw_indices_little_endian_int64_sha256":dh.hexdigest(),"success_count_draws":counts.tolist()})
 suite_out[suite]={"per_seed":byseed,"mean_A":float(A.mean()),"mean_B":float(BB.mean()),"mean_B_minus_A":float((BB-A).mean()),"seed_sd_ddof1_A":float(A.std(ddof=1)),"seed_sd_ddof1_B":float(BB.std(ddof=1)),"seed_sd_ddof1_B_minus_A":float((BB-A).std(ddof=1)),"CI95_B_minus_A":np.quantile(diffdraw,[.025,.975],method="linear").tolist(),"paired_states":matrix,"bootstrap_draws":draws,"unique_state_clusters":100,"trials":600,"allocations":allocations,"allocation_GPU_seconds":sum(x["GPU_seconds"] for x in allocations)}
assert h(R/"results/experiment_supervisor/state.json")==ST
for rr in refs:assert h(R/rr["path"])==rr["sha256"]
v={"schema":"formal_main_v2","status":"computed_pending_independent_statistics_review","kind":"complete_Spatial_Object64_three_seed_development_statistics","utc":datetime.now(timezone.utc).isoformat(),"source":{"path":str(Path(__file__).relative_to(R)),"sha256":h(Path(__file__))},"suite_results":suite_out,"seed_order":SEEDS,"task_stratified_bootstrap_repeats":10000,"bootstrap_seed":20261016,"same_initial_state_carries_all_three_seeds":True,"development_only":True,"new_trials":0,"new_GPU_seconds":0,"historical_costs_not_added_again":True,"final_release":False,"final_state_values_read":False,"O2A_executed":False,"no_equivalence_claim":True,"input_refs":refs}
out=save("Spatial_Object64_three_seed_development_statistics.json",v)
print(json.dumps({"statistics":out,"suites":{k:{n:z[n] for n in ["mean_A","mean_B","mean_B_minus_A","CI95_B_minus_A"]} for k,z in suite_out.items()}}))
