from pathlib import Path
import hashlib,importlib.util,json,sys
from collections import defaultdict
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
B="results/formal_main_v2/preflight/heartbeat_20261021T0910"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
p=R/"scripts/ops/formal_autonomous_training_v1/controller.py"
assert h(p)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
spec=importlib.util.spec_from_file_location("cost0910ctl",p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 state=R/"results/experiment_supervisor/state.json";before=h(state)
 assert before=="40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a"
 on=B+"/live_observation.json";assert h(R/on)=="f47122d65727005fa744658cdad8ce0490ef22da58337d6817425476f005fcf8"
 obs=rd(on);s=rd("results/experiment_supervisor/state.json");rows=[];groups={};seen=set()
 for j in s["registered_jobs"]:
  if j.get("experiment")!="formal_main_v2":continue
  jid=str(j["job_id"]);assert jid not in seen;seen.add(jid);o=obs["observation"]["rows"][jid]
  sec=o["gpus"]*o["elapsed_seconds"];assert sec>=0
  row=dict(job_id=jid,registry_mode=j["mode"],registry_name=j.get("name",j.get("job_name")),status=o["status"],exit_code=o["exit_code"],allocated_gpus=o["gpus"],elapsed_seconds=o["elapsed_seconds"],GPU_seconds=sec)
  rows.append(row);g=groups.setdefault(j["mode"],dict(allocations=0,GPU_seconds=0,nonterminal=[]));g["allocations"]+=1;g["GPU_seconds"]+=sec
  if o["status"] in ["RUNNING","PENDING","CONFIGURING","COMPLETING"]:g["nonterminal"].append(jid)
 assert len(rows)==271 and sum(x["GPU_seconds"] for x in rows)==1991640
 assert groups["train"]["GPU_seconds"]==1887677 and groups["train"]["nonterminal"]==[]
 out=dict(schema="formal_main_v2",kind="registered_allocation_cost_projection",status="timestamped_lower_bound",observed_utc=obs["utc"],source_state_sha256=before,live_observation=dict(path=on,sha256=h(R/on)),unique_allocations=len(rows),GPU_seconds=sum(x["GPU_seconds"] for x in rows),GPU_hours=sum(x["GPU_seconds"] for x in rows)/3600,registry_mode_groups=groups,allocations=rows,all_allocations_including_failures_and_engineering=True,no_addition_of_previous_snapshot_totals=True,all_registry_modes_literal_not_reclassified=True,final_cost=False,new_Slurm_queries=0,new_GPU_jobs=[])
 save(B+"/allocation_cost_projection.json",out);assert h(state)==before
 print(json.dumps(dict(path=B+"/allocation_cost_projection.json",sha256=h(R/B/"allocation_cost_projection.json"),GPU_seconds=out["GPU_seconds"],groups=groups)))
