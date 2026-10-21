from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");B="results/formal_main_v2/preflight/heartbeat_20261021T0910"
SOURCE=".local/object_single_error_gateway_20261021T0110/live_inputs_v2_before_terminal_confirmation.json"
PIN="5c0d8fabdcd9b62abac85230b4858934481fed193652c0c6993d5a4ccd313aa6"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
p=R/"scripts/ops/formal_autonomous_training_v1/controller.py";assert h(p)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
spec=importlib.util.spec_from_file_location("savedterminal0910",p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 state=R/"results/experiment_supervisor/state.json";before=h(state);s=json.loads(state.read_bytes())
 assert h(R/SOURCE)==PIN;j=json.loads((R/SOURCE).read_bytes());assert j["state_sha256"]==before
 assert j["state_for_projection"]=={k:s[k] for k in j["state_for_projection"]}
 v=j["result"];o=v["observation"];ids=[str(x["job_id"]) for x in s["registered_jobs"]]
 assert len(ids)==len(set(ids))==301 and c.parse_sacct(o["raw_sacct"],set(ids))==o["rows"] and set(o["rows"])==set(ids)
 assert all(x["status"] in c.TERMINAL for x in o["rows"].values()) and o["queue"]=={} and o["raw_squeue"]==""
 for q in o["queries"]:
  assert q["returncode"]==0 and q["argv"][0]=="sacct" and q["stdout"]==o["raw_sacct"]
 caps=c.capacity(s["registered_jobs"],o,"3034538");assert not caps["unknown"] and not caps["findings"] and caps["occupied"]==[]
 target=o["rows"]["3054201"];assert (target["status"],target["exit_code"],target["elapsed_seconds"],target["gpus"])==("COMPLETED","0:0",6635,1)
 cost=sum(o["rows"][str(x["job_id"])]["gpus"]*o["rows"][str(x["job_id"])]["elapsed_seconds"] for x in s["registered_jobs"] if x.get("experiment")=="formal_main_v2")
 assert cost==1991937 and v["lease"]["lease_available_measured"] is True
 cp=R/B/"Object_preflight_original_observation.json";cp.open("xb").write((R/SOURCE).read_bytes());assert h(cp)==PIN
 out=dict(schema="formal_main_v2",kind="root_saved_preflight_observation_projection",utc=v["utc"],state_sha256=before,observation=o,capacity=caps,allocated_GPU_seconds=cost,allocated_GPU_hours=cost/3600,controller_lease_released=True,lease=v["lease"],source_gateway_original_observation=dict(path=str(cp.relative_to(R)),sha256=PIN),new_Slurm_queries=0,new_GPU_jobs=[],projection_reparsed_by_original_pinned_controller=True,all_formal_allocations_terminal=True)
 save(B+"/terminal_observation_from_Object_preflight.json",out);assert h(state)==before
 print(json.dumps(dict(path=B+"/terminal_observation_from_Object_preflight.json",sha256=h(R/B/"terminal_observation_from_Object_preflight.json"),cost=cost)))
