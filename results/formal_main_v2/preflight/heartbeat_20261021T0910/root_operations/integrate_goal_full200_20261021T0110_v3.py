from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os,subprocess,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA");PY=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python")
B="results/formal_main_v2/preflight/heartbeat_20261021T0910";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0110"
PROD="scripts/ops/formal_goal_full200_gate_v1";DISP="scripts/ops/formal_goal_full200_dispatch_v1";X="results/formal_main_v2/engineering/goal_full200_20261021T0110"
MSHA="2767f20cdd3b862138f590d65563e1bad844cfe14e6fe41aecf2854fc4f0baec";DSHA="8d3e282946c300f072a13c1b4a658f92b3e25cfb3130a0ad63ab186fe6386b3c"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents))
def immutable(p,b):
 safe(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b,str(p)
 else:p.open("xb").write(b)
def encoded(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False)+"\n").encode()
def save(n,v):immutable(R/n,encoded(v))
def module(p,pin,name):
 assert h(p)==pin
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument("--phase",choices=["install","verify","authorize","admission"],required=True);ap.add_argument("--runtime-review",required=True);ap.add_argument("--runtime-review-sha256",required=True);ap.add_argument("--dispatch-review",required=True);ap.add_argument("--dispatch-review-sha256",required=True);ap.add_argument("--independent-readiness",required=True);ap.add_argument("--independent-readiness-sha256",required=True);ap.add_argument("--expected-state-sha256",required=True);a=ap.parse_args()
for path,pin in [(a.runtime_review,a.runtime_review_sha256),(a.dispatch_review,a.dispatch_review_sha256),(a.independent_readiness,a.independent_readiness_sha256)]:
 assert path.startswith(E+"/Downstream_runtime_independent/") and ".." not in Path(path).parts and h(R/path)==pin
runtime=read(a.runtime_review);dispatch=read(a.dispatch_review);ind=read(a.independent_readiness)
pub=read(E+"/Goal_full200_v2/install_files.json");items=pub["files"];assert len(items)==11
package=read(E+"/Goal_full200_v2/package/package_manifest.json");assert h(R/E/"Goal_full200_v2/package/package_manifest.json")==MSHA and len(package["files"])==10
assert str(runtime["status"]).startswith("passed") and runtime["reviewed_by"] not in (None,"root") and runtime["blockers"]==[] and runtime["package_manifest_sha256"]==MSHA and runtime["package_files"]==package["files"]
dp=read(E+"/Goal_full200_dispatch_v2/publication_map.json");assert len(dp["install_files"])==2 and dp["files"][DISP+"/dispatch.py"]==DSHA
assert dispatch["kind"]=="Goal_full200_atomic_dispatch_independent_review" and dispatch["status"]=="passed" and dispatch["blockers"]==[] and dispatch["dispatch_files"]==dp["files"] and dispatch["runtime_files"]==package["files"] and dispatch["package_manifest_sha256"]==MSHA and dispatch["review_scope"]=="source_and_CPU_only" and dispatch["GPU_execution_authorized"] is False
assert ind["kind"]=="goal_full200_single_attempt_CPU_readiness" and ind["reviewed_by"]=="independent" and ind["status"]=="passed" and ind["package_manifest_sha256"]==MSHA and ind["real_GPU_acceptance"] is False
c=module(R/"scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","goal_root_install0910")
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 st=R/"results/experiment_supervisor/state.json";assert h(st)==a.expected_state_sha256
 state=read("results/experiment_supervisor/state.json");assert state.get("pending_submission") is None and state["autonomous_training_v1"].get("pending_submission") is None and state["autonomous_training_v1"]["reserved_GPU_slots"]==0
 inventory=read("results/formal_main_v2/source/formal_main_v2_run_564be0995e.json");assert len(inventory["files"])==173
 for n,w in inventory["files"].items():
  for root in [R,P/"snapshots/formal_main_v2_run_564be0995e",R/"snapshots/formal_main_v2_run_564be0995e"]:assert h(root/n)==w,n
 rows=[]
 for row in items:
  assert row["path"].startswith(PROD+"/");src=R/E/"Goal_full200_v2"/row["source"];assert h(src)==row["sha256"] and src.stat().st_size==row["bytes"]
  rows.append((src,row["path"],row["sha256"]))
 for row in dp["install_files"]:
  assert row["destination"].startswith(DISP+"/");src=R/E/"Goal_full200_dispatch_v2"/Path(row["source"]).name;assert h(src)==row["sha256"] and src.stat().st_size==row["bytes"]
  rows.append((src,row["destination"],row["sha256"]))
 if a.phase=="install":
  for src,n,pin in rows:
   for root in (R,P):safe(root/n);assert not (root/n).exists(),n
  for src,n,pin in rows:
   for root in (R,P):immutable(root/n,src.read_bytes());assert h(root/n)==pin
  result=dict(status="independently_reviewed_exact_sources_installed",runtime_review=ref(a.runtime_review),dispatch_review=ref(a.dispatch_review),installed_files={n:pin for src,n,pin in rows},source173_unchanged=True,new_GPU_jobs=[],state_unchanged=True,actual_P_verified=False)
  save(B+"/Goal_source_publication.json",result)
 else:
  for src,n,pin in rows:assert h(R/n)==h(P/n)==pin
  e=module(P/PROD/"entry.py",package["files"][PROD+"/entry.py"],"goal_published_root_verify0910")
  e.check_review(ind,"independent",MSHA,package["files"][PROD+"/config.json"])
  if a.phase=="verify":
   argv=[str(PY),"-B",str(P/PROD/"entry.py"),"--verify","--package-manifest-sha256",MSHA];q=subprocess.run(argv,capture_output=True,text=True,timeout=300)
   capture=dict(kind="Goal_full200_actual_P_verification_capture",argv=argv,returncode=q.returncode,stdout=q.stdout,stderr=q.stderr,runtime_files=package["files"],state_sha256=a.expected_state_sha256,new_GPU_jobs=[],scientific_trials=0)
   save(B+"/Goal_actual_P_capture.json",capture);assert q.returncode==0,q.stderr
   value=json.loads(q.stdout);assert value["status"]=="passed_metadata_source_capacity_only"
   result=dict(status="actual_P_metadata_source_capacity_verified",capture=ref(B+"/Goal_actual_P_capture.json"),new_GPU_jobs=[],GPU_execution_passed=False)
  elif a.phase=="authorize":
   capture=read(B+"/Goal_actual_P_capture.json");assert capture["returncode"]==0 and capture["runtime_files"]==package["files"]
   root=copy.deepcopy(ind);root["reviewed_by"]="root";root["root_adopted_independent_review"]=ref(a.runtime_review);root["actual_P_capture"]=ref(B+"/Goal_actual_P_capture.json");root["installed_source_receipt"]=ref(B+"/Goal_source_publication.json")
   e.check_review(root,"root",MSHA,package["files"][PROD+"/config.json"])
   payloads={X+"/root_readiness.json":encoded(root),X+"/independent_readiness.json":(R/a.independent_readiness).read_bytes()}
   def future(n):return dict(path=str(P/n),sha256=hashlib.sha256(payloads[n]).hexdigest())
   auth=dict(schema="formal_main_v2",kind="root_goal_full200_single_attempt_authorization",version=e.VERSION,status="approved",reviewed_by="root",stage_key=e.STAGE,config_sha256=package["files"][PROD+"/config.json"],package_manifest_sha256=MSHA,entrypoint_sha256=package["files"][PROD+"/entry.py"],maximum_gpu_jobs=1,maximum_attempts=1,maximum_wall_seconds=7200,counts_against_8_GPU_slots=True,automatic_retry=False,scientific_release=False,original_goal200_HOLD=True,new_Goal_science_HOLD=True,maximum_trials=200,maximum_total_control_steps=60000,maximum_total_policy_queries=7600,policy_watchdog_seconds=60.0,raw_observation_root=str(e.RAW),root_storage_decision=e.STORAGE_DECISION,root_fixed_design=dict(path=e.ROOT_DECISION_REL,sha256=e.ROOT_DECISION_SHA),resources=e.RESOURCES,dispatch_record_path=str(e.DISPATCH),reservation_path=str(e.RESERVATION),root_review=future(X+"/root_readiness.json"),independent_review=future(X+"/independent_readiness.json"))
   e.validate_authorization(auth,package["files"][PROD+"/config.json"],MSHA,package["files"][PROD+"/entry.py"])
   payloads[X+"/root_authorization.json"]=encoded(auth)
   for n,b in payloads.items():
    for base in (R,P):immutable(base/n,b)
   result=dict(status="root_authorized_one_fixed200_attempt_dispatch_gate_still_required",authorization=ref(X+"/root_authorization.json"),actual_P=ref(B+"/Goal_actual_P_capture.json"),independent_review=ref(a.runtime_review),independent_readiness=ref(a.independent_readiness),old200_HOLD=True,new_other1000_HOLD=True,scientific_trials=0,new_GPU_jobs=[])
   save(B+"/Goal_root_authorization_receipt.json",result)
  else:
   builder=E+"/Goal_full200_dispatch_v2/prepare_admission.py";assert h(R/builder)=="24e705da82cd1fc2507a16998bf88001027effa793e2a940b53f83fd760d6a64"
   argv=[str(PY),"-B",str(R/builder),"--dispatch-sha256",DSHA,"--runtime-review",a.runtime_review,"--dispatch-review",a.dispatch_review,"--actual-P-verification",B+"/Goal_actual_P_capture.json","--root-reviewed"]
   q=subprocess.run(argv,cwd=R,capture_output=True,timeout=300)
   save(B+"/Goal_admission_builder_capture.json",dict(argv=argv,returncode=q.returncode,stdout=q.stdout.decode(),stderr=q.stderr.decode()));assert q.returncode==0,q.stderr.decode()
   value=json.loads(q.stdout);g=module(R/DISP/"dispatch.py",DSHA,"goal_root_admission0910");g.check_admission_fields(value)
   for root in (R,P):immutable(root/X/"dispatch_admission.json",q.stdout)
   result=dict(status="exact_root_dispatch_admission_published",admission=ref(X+"/dispatch_admission.json"),authorization=ref(X+"/root_authorization.json"),new_GPU_jobs=[],scientific_trials=0)
   save(B+"/Goal_dispatch_admission_receipt.json",result)
 assert h(st)==a.expected_state_sha256
 print(json.dumps(result))
