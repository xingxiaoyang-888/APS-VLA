from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,importlib.util,sys,fcntl
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B=R/"results/formal_main_v2/preflight/heartbeat_20261021T0556"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def mod(rel,pin,name):
 p=R/rel;assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=mod("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","root2156c")
g=mod("scripts/ops/formal_action_deployment_posttraining_k64s23_v1/gateway.py","873d0145f8d3ed51e916f39e1e36cb0251d10777a6f98429621f526d37a2c7bb","root2156g")
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 sp=R/"results/experiment_supervisor/state.json";before=h(sp);s=json.loads(sp.read_bytes());a=s["autonomous_training_v1"];f=s["formal_main_progress"]
 assert before=="cf54288d932880c061936f89f94dd3fb9b71c99382226d5276bb694fe6c2f33a"
 snap=c.Slurm().observe(s["registered_jobs"]);cap=c.capacity(s["registered_jobs"],snap,a["controller_job_id"])
 for j in s["registered_jobs"]:g.check_observed_identity(j,snap["rows"][j["job_id"]],snap["queue"].get(j["job_id"]),c.TERMINAL)
 assert not cap["unknown"] and not cap["findings"] and not cap["occupied"]
 ctl=snap["rows"]["3034538"];assert ctl["status"]=="COMPLETED" and ctl["exit_code"]=="0:0" and ctl["gpus"]==0
 assert s["pending_submission"] is None and a["root_submission_hold"] is None and a["reserved_GPU_slots"]==0 and not a["occupied_job_ids"]
 w=R/"results/formal_main_v2/autonomous_training/run_v1";owner=json.loads((w/"owner.json").read_bytes())
 assert owner["owner_id"]==a["owner_id"] and owner["coordinator_job_id"]=="3034538"
 with (w/"controller.lease.lock").open("rb") as z:fcntl.flock(z.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(z.fileno(),fcntl.LOCK_UN)
 formal=[j for j in s["registered_jobs"] if j.get("experiment")=="formal_main_v2"];sec=sum(snap["rows"][j["job_id"]]["elapsed_seconds"]*snap["rows"][j["job_id"]]["gpus"] for j in formal)
 assert len(formal)==269 and sec==1984462
 assert f["root_and_independent_completed_arms"]==72 and f["completed_final_trials"]==0 and not f["test_opened"] and not f["global_release_created"]
 old=s["last_root_supervision_snapshot"];assert h(R/old["path"])==old["sha256"]
 v=dict(schema="formal_main_v2",status="unchanged_terminal_training_and_development_gates",utc=datetime.now(timezone.utc).isoformat(),state_sha256=before,observation=snap,capacity=cap,controller_terminal=ctl,controller_lease_released=True,pending_submission=None,root_hold=None,registered_formal_jobs=len(formal),GPU_seconds=sec,GPU_hours=sec/3600,source173_unchanged=True,training_arms=72,accepted_development_trials=6400,final_sealed=True,prior_root_snapshot=old,state_written=False,new_GPU_jobs=0)
 B.mkdir(parents=True,exist_ok=True)
 with (B/"initial_observation.json").open("x") as z:json.dump(v,z,sort_keys=True,indent=2);z.write("\n")
 assert h(sp)==before
 print(json.dumps({k:v[k] for k in ["status","utc","GPU_hours","training_arms","accepted_development_trials","controller_lease_released","new_GPU_jobs","state_written"]}))
