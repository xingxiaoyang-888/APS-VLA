"""Run exact commit with-body only in isolated server fixtures; never real main."""
from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import ast,copy,fcntl,hashlib,importlib.util,json,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/spatial_pending_reconciliation_independent_1518"
PIN="7a978396858622e0ad1aa2fa54699db499cf563a5d7327a3d4bfe6d977729490"
SOURCE=R/".local/reconcile_commit_1518.py"
raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==PIN
tree=ast.parse(raw);body=[n for n in tree.body if isinstance(n,ast.With)]
assert len(body)==1
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {"submit","prepare"} for n in ast.walk(body[0]))
program=compile(ast.Module(body=body,type_ignores=[]),str(SOURCE),"exec",dont_inherit=True)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
refs={".local/reconcile_commit_1518.py":PIN}
def read(rel,pin=None):
 p=R/rel;b=p.read_bytes();hh=hashlib.sha256(b).hexdigest();refs[rel]=hh
 if pin:assert hh==pin
 return json.loads(b)
def load(rel,pin,name):
 p=R/rel;assert h(p)==pin;refs[rel]=pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
c=load("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","commit_ind_c")
g=load("scripts/ops/formal_action_deployment_v1/gateway.py","8f247fc1e2b8c8ed2fded79286390dd548392c74d28105df332beb3b8d13173a","commit_ind_g")
probe=read("results/formal_main_v2/preflight/heartbeat_20261019T2318/Spatial_pending_probe_v2.json","888c31564d5cb2b4eab5e306c7f2e375b2d56832994dde63f5dbaa26707390f1")
state=read("results/experiment_supervisor/state.json");state_ref=refs.pop("results/experiment_supervisor/state.json")
ref=state["pending_submission"]["authorization"]
auth,e,plan,scientific,prepared=g.validate_authorization(R,ref)
refs.update(e.hashes);e.unchanged()
prepared_raw=(R/auth["prepared_invocation"]["path"]).read_bytes()
assert hashlib.sha256(prepared_raw).hexdigest()==state["pending_submission"]["invocation_sha256"]
BASE=state["pending_submission"]["audit_relative"]
ack_raw=(R/BASE/"sbatch_result.json").read_bytes();failed_raw=(R/BASE/"failed_transaction.json").read_bytes()
refs[BASE+"/sbatch_result.json"]=hashlib.sha256(ack_raw).hexdigest()
refs[BASE+"/failed_transaction.json"]=hashlib.sha256(failed_raw).hexdigest()
owner=read("results/formal_main_v2/autonomous_training/run_v1/owner.json")
results=[]
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes) else json.dumps(b).encode())
for case in ["success","wrong_token","changed_invocation_raw_bytes","missing_accounting","CAS_failure","unheld_lease"]:
 root=D/"isolated_commit_a1"/case/"R";remote=D/"isolated_commit_a1"/case/"P";root.mkdir(parents=True,exist_ok=False);remote.mkdir()
 initial=copy.deepcopy(state)
 if case=="wrong_token":initial["pending_submission"]["request_token"]="wrong"
 path=root/"results/experiment_supervisor/state.json";save(path,initial)
 lock=path.parent/".writer.lock";lock.touch(exist_ok=False)
 inv=initial["pending_submission"]["invocation"]
 for p in [root/inv,remote/inv,root/auth["prepared_invocation"]["path"]]:save(p,prepared_raw)
 if case=="changed_invocation_raw_bytes":save(remote/inv,json.loads(prepared_raw))
 save(root/BASE/"sbatch_result.json",ack_raw);save(root/BASE/"failed_transaction.json",failed_raw)
 lease=root/"results/formal_main_v2/autonomous_training/run_v1/controller.lease.lock";save(lease,b"")
 own=copy.deepcopy(owner);own["lock"]=str(lease);save(root/"results/formal_main_v2/autonomous_training/run_v1/owner.json",own)
 out=root/"results/formal_main_v2/preflight/heartbeat_20261019T2318";out.mkdir(parents=True)
 counter={"observe":0,"queries":[],"CAS":0,"state_commits":0}
 def query(argv,**kwargs):
  assert argv[0] in {"sacct","squeue","scontrol"},argv
  counter["queries"].append(argv)
  if argv[0]=="scontrol":return SimpleNamespace(returncode=0,stdout=probe["scontrol_corroboration"]["stdout"],stderr="")
  rawq=probe["observation"]["raw_sacct" if argv[0]=="sacct" else "raw_squeue"]
  if case=="missing_accounting" and argv[0]=="sacct":rawq="".join(x+"\n" for x in rawq.splitlines() if not x.startswith("3042529|"))
  return SimpleNamespace(returncode=0,stdout=rawq,stderr="")
 def slurm(**kwargs):
  counter["observe"]+=1
  return c.Slurm(runner=query,**kwargs)
 def atomic(p,v,expected_sha=None):
  counter["CAS"]+=1
  assert p==path and expected_sha==h(path)
  if case=="CAS_failure":raise ValueError("synthetic CAS refusal after durable receipt")
  c.atomic_json(p,v,expected_sha);counter["state_commits"]+=1
 proxyc=SimpleNamespace(**c.__dict__);proxyc.Slurm=slurm;proxyc.atomic_json=atomic
 proxyg=SimpleNamespace(**g.__dict__)
 ev=SimpleNamespace(hashes=e.hashes.copy(),unchanged=lambda:None)
 proxyg.validate_authorization=lambda rt,rr:(auth,ev,plan,scientific,prepared)
 oldbytes=path.read_bytes();f=lease.open("rb")
 if case!="unheld_lease":fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 outcome=None
 try:
  exec(program,dict(R=root,P=remote,B="results/formal_main_v2/preflight/heartbeat_20261019T2318",c=proxyc,g=proxyg,
    h=h,Path=Path,datetime=datetime,timezone=timezone,hashlib=hashlib,json=json,copy=copy,fcntl=fcntl,print=lambda *args:None))
  outcome="completed"
 except (ValueError,AssertionError) as ex:outcome=type(ex).__name__+":"+str(ex)
 finally:f.close()
 after=json.loads(path.read_bytes())
 if case=="success":
  assert outcome=="completed" and counter["state_commits"]==1
  assert after["registered_jobs"][:-1]==initial["registered_jobs"]
  j=after["registered_jobs"][-1]
  assert j["job_id"]=="3042529" and (j["status"],j["exit_code"],j["elapsed_seconds"],j["gpus"])==("FAILED","1:0",2,1)
  assert after["pending_submission"] is None and after["autonomous_training_v1"]["reserved_GPU_slots"]==0
  a=copy.deepcopy(initial["autonomous_training_v1"]);b=copy.deepcopy(after["autonomous_training_v1"])
  for k in ["reserved_GPU_slots","downstream_reservations_consumed"]:a.pop(k,None);b.pop(k,None)
  assert a==b
  receipt=json.loads((out/"Spatial_pending_reconciliation.json").read_bytes())
  assert receipt["job_GPU_seconds"]==2 and receipt["submissions"]==0 and receipt["scientific_stage_complete"] is False
 elif case=="CAS_failure":
  assert "synthetic CAS refusal" in outcome and path.read_bytes()==oldbytes and after["pending_submission"]==initial["pending_submission"]
  assert (out/"Spatial_pending_reconciliation.json").exists() and (root/"results/formal_main_v2/submissions/3042529.json").exists()
  assert not (out/"Spatial_pending_reconciliation_commit.json").exists()
 else:
  assert outcome!="completed" and path.read_bytes()==oldbytes and counter["state_commits"]==0
  assert not (out/"Spatial_pending_reconciliation.json").exists()
  if case in {"wrong_token","changed_invocation_raw_bytes","unheld_lease"}:assert counter["observe"]==0
  if case=="missing_accounting":assert "post-submit accounting incomplete" in outcome
 results.append({"case":case,"passed":True,"candidate_outcome":outcome,"scheduler":counter})
assert h(SOURCE)==PIN
refs[str(Path(__file__).relative_to(R))]=h(Path(__file__))
res={"schema":"formal_main_v2","kind":"exact_pending_commit_isolated_CPU_review","status":"passed_CPU_checks",
"source":{"path":SOURCE.relative_to(R).as_posix(),"sha256":PIN},"tests":results,"mutations_to_real_state":False,
"real_Slurm_calls":0,"mutating_candidate_main_executed":False,"exact_AST_with_body_executed":True,
"standins":["server-only temporary R/P and copy of current registered-state snapshot","typed authorization reader returns real already validated metadata without copying its closure","fake Slurm runner replays root-captured exact 258-row snapshot and scontrol raw text","temporary actual flock lease, not production controller lease","synthetic CAS refusal case and Evidence unchanged no-op inside isolated body; original authorization/Evidence validation ran separately on read-only R"],
"real_metadata_validation_refs":refs,"mutable_input_state_sha256":state_ref,
"limitation":"CPU review of this exact one-job bookkeeping reconciliation only; no new submission, actual production commit or scientific result approval."}
out=D/"commit_CPU_checks.json"
with out.open("x") as f:json.dump(res,f,sort_keys=True,indent=2);f.write("\n")
print(json.dumps({"passed":len(results),"sha256":h(out),"receipt":str(out),"candidate_sha256":PIN}))
