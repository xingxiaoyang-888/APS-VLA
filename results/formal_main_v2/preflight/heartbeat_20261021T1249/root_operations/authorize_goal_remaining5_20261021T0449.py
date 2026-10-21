from pathlib import Path,PurePosixPath
import argparse,json,hashlib,fcntl,os,sys,importlib.util,datetime
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B="results/formal_main_v2/preflight/heartbeat_20261021T1249";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
PROD="scripts/ops/formal_goal_remaining5_gate_v1";BASE="scripts/ops/formal_goal_remaining5_dispatch_v1"
M="200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f";GS="45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b";SS="f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b"
ST="d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba"
D=".local/goal_remaining5_independent_20261021T0449/runtime_source_CPU";DEST=E+"/Goal_runtime_independent"
def sha(b):return hashlib.sha256(b).hexdigest()
def h(p):return sha(p.read_bytes())
def read(p,pin=None):
 b=p.read_bytes()
 if pin:assert sha(b)==pin,str(p)
 return json.loads(b)
def ref(rel):p=R/rel;return {"path":rel,"sha256":h(p),"bytes":p.stat().st_size}
def put(p,b):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents])
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def encoded(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode()
def save(p,x):put(p,encoded(x))
def module(p,pin,name):
 assert h(p)==pin
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
ap=argparse.ArgumentParser();ap.add_argument("--independent-manifest-sha256",required=True);ap.add_argument("--independent-report-sha256",required=True);a=ap.parse_args()
assert os.environ.get("CTI_SERVER_CONTROL_ROOT")==str(R)
mp=read(R/PROD/"package_manifest.json",M);g=module(R/BASE/"gateway.py",GS,"goal_r5_root_auth_gateway");e=module(P/PROD/"entry.py",mp["files"][PROD+"/entry.py"],"goal_r5_root_auth_entry")
report=read(R/D/"independent_review.json",a.independent_report_sha256)
assert str(report["status"]).startswith("passed") and report["blockers"]==[] and report["package_manifest_sha256"]==M and report["package_files"]==mp["files"] and report.get("reviewed_by") not in (None,"root")
manifest_b=(R/D/"delivery_manifest.json").read_bytes();assert sha(manifest_b)==a.independent_manifest_sha256
manifest=json.loads(manifest_b);rows=[];seen=set()
for rr in manifest["files"]:
 n=rr["path"];n=n[len(D)+1:] if n.startswith(D+"/") else n
 pp=PurePosixPath(n);assert not pp.is_absolute() and ".." not in pp.parts and n not in seen;seen.add(n)
 src=R/D/n;b=src.read_bytes();assert not src.is_symlink() and len(b)==rr["bytes"] and sha(b)==rr["sha256"] and len(b)<100*(1<<20)
 rows.append((n,b,rr))
assert not (R/DEST).exists()
capture_index=read(R/B/"Goal_remaining5_actual_P_index.json")
captures={read(R/x["path"],x["sha256"])["pair_key"]:x for x in capture_index["captures"]}
plan_index=read(R/B/"Goal_remaining5_prepared_invocations.json","45a1fe173f83597a8181f5129a5354bbdf0f49143743eac96de2dff8a418e578")
payloads=[]
for key in mp["pair_keys"]:
 ctx=e.context(key);d=g.make_dispatcher(key,SS);x=ctx.X
 indfile=key+"_independent_readiness.json";assert indfile in seen
 ind=read(R/D/indfile);e.check_review(ctx,ind,"independent",M,ctx.config_sha)
 assert ind.get("pair_key",key)==key
 current=read(R/captures[key]["path"],captures[key]["sha256"])
 assert current["returncode"]==0 and current["runtime_files"]==mp["files"]
 inv=json.loads(current["stdout"])["original_invocation"];assert inv["path"]==str(ctx.ORIGINAL) and h(ctx.ORIGINAL)==inv["sha256"]
 root={"schema":"formal_main_v2","kind":"goal_remaining5_single_attempt_CPU_readiness","status":"passed","reviewed_by":"root","version":e.VERSION,"pair_key":key,"package_manifest_sha256":M,"config_sha256":ctx.config_sha,"original_chain_preserved":True,"observer_gaps_fixed":True,"paired_input_gate_CPU_passed":True,"pre_policy_pair_equality_gate":True,"all_query_input_integrity_gate":True,"original_policy_error_retained_then_halt":True,"full200_bound_tests_passed":True,"original_typed_raw_consumer_ready":True,"two_root_storage_contract_verified":True,"real_GPU_acceptance":False,"scientific_release":False,"actual_P_metadata_source_capacity_verified":True,"evidence":[ref(E+"/Goal_runtime_author/author_readiness.json"),{"path":DEST+"/independent_review.json","sha256":a.independent_report_sha256,"bytes":(R/D/"independent_review.json").stat().st_size},captures[key],ref(x+"/plan_root_review.json"),ref(x+"/plan_independent_review.json")],"scope_note":"Root source/CPU/readiness integration plus actual P metadata/source/identity/capacity process. No GPU or scientific terminal result claimed."}
 e.check_review(ctx,root,"root",M,ctx.config_sha)
 rb=encoded(root);ib=(R/D/indfile).read_bytes()
 auth={"schema":"formal_main_v2","kind":"root_goal_remaining5_single_attempt_authorization","version":e.VERSION,"status":"approved","reviewed_by":"root","stage_key":ctx.stage_key,"pair_key":key,"config_sha256":ctx.config_sha,"package_manifest_sha256":M,"entrypoint_sha256":mp["files"][PROD+"/entry.py"],"maximum_gpu_jobs":1,"maximum_attempts":1,"maximum_wall_seconds":7200,"counts_against_8_GPU_slots":True,"automatic_retry":False,"scientific_release":False,"original_goal200_HOLD":True,"new_Goal_science_HOLD":True,"maximum_trials":200,"maximum_total_control_steps":60000,"maximum_total_policy_queries":7600,"policy_watchdog_seconds":60.0,"raw_observation_root":str(ctx.RAW),"root_storage_decision":ctx.storage_decision,"root_fixed_design":{"path":ctx.root_decision["path"],"sha256":ctx.root_decision["sha256"]},"resources":e.RESOURCES,"dispatch_record_path":str(ctx.DISPATCH),"reservation_path":str(ctx.RESERVATION),"root_review":{"path":str(ctx.BASE/"root_readiness.json"),"sha256":sha(rb)},"independent_review":{"path":str(ctx.BASE/"independent_readiness.json"),"sha256":sha(ib)},"original_invocation":inv}
 e.validate_authorization(ctx,auth,ctx.config_sha,M,mp["files"][PROD+"/entry.py"])
 ab=encoded(auth)
 admission={**d.admission_fixed(),"prepared_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"dispatch_files":d.source_map(),"runtime_files":mp["files"],"authorization":{"path":d.authorization,"sha256":sha(ab),"bytes":len(ab)},"runtime_independent_review":{"path":DEST+"/independent_review.json","sha256":a.independent_report_sha256,"bytes":(R/D/"independent_review.json").stat().st_size},"dispatch_independent_review":ref(E+"/Goal_gateway_independent/independent_review.json"),"actual_P_verification":captures[key]}
 for n,b in [("root_readiness.json",rb),("independent_readiness.json",ib),("root_authorization.json",ab),("dispatch_admission.json",encoded(admission))]:payloads.append((x+"/"+n,b))
with (R/"results/experiment_supervisor/.writer.lock").open("a") as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert h(R/"results/experiment_supervisor/state.json")==ST
 s=read(R/"results/experiment_supervisor/state.json");assert s["pending_submission"] is None and s["autonomous_training_v1"]["reserved_GPU_slots"]==0
 for key in mp["pair_keys"]:
  c=e.context(key);assert not c.OUTPUT.exists() and not c.RAW.exists()
 for rel,b in payloads:
  for r in [R,P]:assert not (r/rel).exists(),rel
 for n,b,rr in rows:put(R/DEST/n,b)
 put(R/DEST/"delivery_manifest_original.json",manifest_b)
 save(R/DEST/"root_publication_mapping.json",{"source_root":D,"manifest_sha256":a.independent_manifest_sha256,"files":[{"source":D+"/"+n,"path":DEST+"/"+n,"sha256":sha(b),"bytes":len(b)} for n,b,rr in rows]})
 for rel,b in payloads:
  for r in [R,P]:put(r/rel,b)
 save(R/B/"Goal_remaining5_root_authorization_publication.json",{"schema":"formal_main_v2","kind":"root_exact_five_once_authorization_publication","status":"five_exact_once_authorizations_published_not_submitted","state_sha256_unchanged":ST,"package_manifest_sha256":M,"independent_runtime_report":ref(DEST+"/independent_review.json"),"files":[{"path":n,"sha256":sha(b),"bytes":len(b),"R_P_same":True} for n,b in payloads],"new_GPU_submissions":0,"global_release":False,"final_sealed":True})
dry=R/E/"Goal_native_admission";dry.mkdir(parents=True,exist_ok=False)
results=[]
for key in mp["pair_keys"]:
 d=g.make_dispatcher(key,SS);pin=h(R/("results/formal_main_v2/execution/goal_remaining5_v1/"+key+"/dispatch_admission.json"))
 bundle=d.admission(pin);out=d.Transaction(d.Native(bundle),bundle).run(submit=False)
 assert out["status"]=="read_only_ready_not_submitted" and out["state_sha256"]==ST
 p=dry/(key+".json");save(p,out);results.append(ref(str(p.relative_to(R))))
 print("native admission ready",key,flush=True)
save(R/B/"Goal_remaining5_native_admission_index.json",{"schema":"formal_main_v2","status":"all_five_native_admissions_passed_without_submission","results":results,"state_sha256_unchanged":ST,"new_GPU_submissions":0})
print(json.dumps({"status":"five_authorized_once_and_native_read_only_ready","captures":results}))
