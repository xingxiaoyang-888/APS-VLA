from pathlib import Path,PurePosixPath
import hashlib,json,fcntl,os,importlib.util,sys,datetime
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");B="results/formal_main_v2/preflight/heartbeat_20261021T1249";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
ST="58e4ff5cd74c07c667a942119d2ed2de80059efb294ad8f21d192cdbe14bdac7"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(rel):p=R/rel;return {"path":rel,"bytes":p.stat().st_size,"sha256":h(p)}
def rd(rel,pin=None):
 p=R/rel
 if pin:assert h(p)==pin
 return json.loads(p.read_bytes())
def put(p,b):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(rel,x):put(R/rel,(json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode())
def module(rel,pin,name):
 p=R/rel;assert h(p)==pin;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def package(src,pin,dst):
 m=rd(src+"/delivery_manifest.json",pin);seen=set();rows=[]
 for r in m["files"]:
  n=r["path"];n=n[len(src)+1:] if n.startswith(src+"/") else n
  assert not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts and n not in seen;seen.add(n)
  b=(R/src/n).read_bytes();assert len(b)==r["bytes"] and hashlib.sha256(b).hexdigest()==r["sha256"]
  rows.append((n,b))
 assert not (R/dst).exists()
 for n,b in rows:put(R/dst/n,b)
 put(R/dst/"delivery_manifest_original.json",(R/src/"delivery_manifest.json").read_bytes())
 save(dst+"/source_map.json",{"source_root":src,"manifest_sha256":pin,"files":[{"source":src+"/"+n,**ref(dst+"/"+n)} for n,b in rows],"new_scientific_results":0})
g=module("scripts/ops/formal_goal_remaining5_dispatch_v1/gateway.py","45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b","r5_final_observer")
c=g.controller()
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 assert h(R/"results/experiment_supervisor/state.json")==ST
 s=rd("results/experiment_supervisor/state.json");jobs=s["registered_jobs"]
 assert s["pending_submission"] is None and s["autonomous_training_v1"]["reserved_GPU_slots"]==0 and s["autonomous_training_v1"]["root_submission_hold"] is None
 obs=g.actual_observation(c,c.Slurm(timeout=30),jobs);cap=c.capacity(jobs,obs,"3034538");assert not cap["unknown"] and not cap["findings"]
 lease=g.probe_lease(s,obs["rows"]["3034538"])
 details={};queries=[]
 for jid in cap["occupied"]:
  a=c.Slurm(timeout=30).run(["scontrol","show","job","-o",jid]);assert a.returncode==0
  d=g.fields(a.stdout);j=next(j for j in jobs if str(j["job_id"])==jid);g.validate_live_identity(j,d,obs["queue"].get(jid));details[jid]=d
  queries.append({"argv":["scontrol","show","job","-o",jid],"returncode":a.returncode,"stdout":a.stdout,"stderr":a.stderr})
 formal=[j for j in jobs if j.get("experiment")=="formal_main_v2"];assert len(formal)==278
 cost=sum(obs["rows"][str(j["job_id"])]["elapsed_seconds"]*obs["rows"][str(j["job_id"])]["gpus"] for j in formal)
 new=[j for j in jobs if j.get("goal_dispatch_mode")=="goal_remaining5_prospective"];assert {j["job_id"] for j in new}=={"3057505","3057510","3057515","3057526","3057533"}
 result={"schema":"formal_main_v2","kind":"root_post_dispatch_registered_accounting_snapshot","utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"state_sha256":ST,"observation":obs,"capacity":cap,"active_details":details,"scontrol_queries":queries,"controller_lease":lease,"formal_unique_allocations":278,"formal_GPU_seconds":cost,"formal_GPU_hours":cost/3600,"new_jobs":[{"pair_key":j["pair_key"],"job_id":j["job_id"],"row":obs["rows"][j["job_id"]]} for j in new],"scientific_acceptance_inferred":False,"new_trials_accepted":0,"all_running_costs_are_lower_bounds":True}
 save(B+"/post_dispatch_observation.json",result)
 package(".local/goal_remaining5_published_integration_20261021T0449","d05b2fd96eec3e5e3f8db9e20835c32b6e360a45e8879097ee2a181489421050",E+"/Goal_published_interface_independent")
 package(".local/goal_remaining5_authorization_helper_review_20261021T0449","2206fddb7bfdd1f06b1648cc7f8366a2b457f63f511363651eea06d3e36c7779",E+"/Goal_authorization_helper_independent")
 package(".local/goal30_fixed_observation_design_20261021T0449","7100bf88f63840006fb726b9447cdc7414e5500d96f365904a57c270c5c4ebc9",E+"/Goal_fixed30_design")
 assert h(R/"results/experiment_supervisor/state.json")==ST
print(json.dumps({"receipt":ref(B+"/post_dispatch_observation.json"),"GPU_seconds":cost,"GPU_hours":cost/3600,"capacity":cap,"new_jobs":result["new_jobs"]}))
