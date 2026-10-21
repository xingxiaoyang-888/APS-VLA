from pathlib import Path
import json,hashlib,fcntl,os,subprocess,datetime
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA");S=P/"snapshots/formal_main_v2_run_564be0995e"
B=R/"results/formal_main_v2/preflight/heartbeat_20261021T1249";E=R/"results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
D=R/".local/goal_remaining5_runtime_20261021T0449/package";G=R/".local/goal_remaining5_dispatch_20261021T0449"
M="200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f";ST="d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba"
PROD="scripts/ops/formal_goal_remaining5_gate_v1";BASE="scripts/ops/formal_goal_remaining5_dispatch_v1"
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p,h=None):
 b=p.read_bytes()
 if h:assert sha(b)==h,str(p)
 return json.loads(b)
def put(p,b):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents])
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(p,x):put(p,(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode())
manifest=read(D/"package_manifest.json",M);assert len(manifest["files"])==20
items=[]
for rel,h in manifest["files"].items():
 assert rel.startswith(PROD+"/")
 src=D/rel[len(PROD)+1:];b=src.read_bytes();assert sha(b)==h
 items.append((rel,b,str(src.relative_to(R))))
items.append((PROD+"/package_manifest.json",(D/"package_manifest.json").read_bytes(),str((D/"package_manifest.json").relative_to(R))))
for name,src,h in [("gateway.py",G/"gateway_v3.py","45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b"),("scope.json",G/"scope.json","f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b")]:
 b=src.read_bytes();assert sha(b)==h;items.append((BASE+"/"+name,b,str(src.relative_to(R))))
inv=read(R/"results/formal_main_v2/source/formal_main_v2_run_564be0995e.json","5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926")
assert len(inv["files"])==173
for rel,h in inv["files"].items():
 if isinstance(h,dict):h=h["sha256"]
 for root in [R,S]:assert sha((root/rel).read_bytes())==h,rel
with (R/"results/experiment_supervisor/.writer.lock").open("a") as lk:
 fcntl.flock(lk,fcntl.LOCK_EX)
 assert sha((R/"results/experiment_supervisor/state.json").read_bytes())==ST
 for rel,b,src in items:
  for root in [R,P]:assert not (root/rel).exists(),str(root/rel)
 for rel,b,src in items:
  for root in [R,P]:put(root/rel,b)
 receipt={"schema":"formal_main_v2","kind":"root_exact_remaining5_source_publication","status":"published_source_only_GPU_HOLD","state_sha256_unchanged":ST,"package_manifest_sha256":M,"frozen_173_R_and_S_verified":True,"new_GPU_submissions":0,"source_rows":[{"path":r,"source":s,"bytes":len(b),"sha256":sha(b),"destinations":["R","P"]} for r,b,s in items]}
 save(B/"Goal_remaining5_runtime_publication.json",receipt)
assert sha((R/"results/experiment_supervisor/state.json").read_bytes())==ST
capture_dir=E/"Goal_actual_P"
capture_dir.mkdir(parents=True,exist_ok=False)
captures=[]
for key in manifest["pair_keys"]:
 argv=["/share/home/u15016/XXY_CVPR/CTI-VLA/venv/bin/python","-B",str(P/PROD/"entry.py"),"--pair-key",key,"--verify","--package-manifest-sha256",M]
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 c=subprocess.run(argv,cwd=str(R),capture_output=True,text=True,timeout=240,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
 cap={"schema":"formal_main_v2","kind":"Goal_remaining5_actual_P_verification_capture","pair_key":key,"started_utc":started,"completed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"argv":argv,"returncode":c.returncode,"stdout":c.stdout,"stderr":c.stderr,"runtime_files":manifest["files"],"new_GPU_submissions":0,"real_GPU_acceptance":False}
 out=capture_dir/(key+".json");save(out,cap)
 assert c.returncode==0,c.stderr[-4000:]
 v=json.loads(c.stdout);assert v["status"]=="passed_metadata_source_capacity_only" and v["pair_key"]==key and v["package_manifest_sha256"]==M and v["new_GPU_submissions"]==0
 captures.append({"path":str(out.relative_to(R)),"sha256":sha(out.read_bytes()),"bytes":out.stat().st_size})
 print("actual P verified",key,flush=True)
save(B/"Goal_remaining5_actual_P_index.json",{"schema":"formal_main_v2","status":"five_actual_P_verifications_passed_source_identity_capacity_only","captures":captures,"new_GPU_submissions":0,"state_unchanged":ST})
print(json.dumps({"status":"source_published_and_five_actual_P_verified","captures":captures}))
