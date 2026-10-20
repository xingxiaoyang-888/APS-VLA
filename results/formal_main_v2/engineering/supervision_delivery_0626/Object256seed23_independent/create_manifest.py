from pathlib import Path
import hashlib,json
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/independent_object3042627_0626"
report=json.loads((D/"independent_review.json").read_bytes())
assert report["status"]=="passed_complete_training_only" and report["job_id"]=="3042627"
rows=[]
for p in sorted(D.rglob("*")):
 if p.is_file():
  assert p.resolve()==p and not p.is_symlink() and p.suffix not in {".pt",".bin",".safetensors",".pyc"}
  assert p.name!="manifest.json"
  b=p.read_bytes();rows.append({"path":p.relative_to(R).as_posix(),"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest()})
out={"schema":"formal_main_v2","kind":"independent_audit_delivery_manifest","job_id":"3042627","private_root":D.relative_to(R).as_posix(),"files":rows,"state_Git_or_Slurm_mutated":False,"tensor_deserialization":False}
p=D/"manifest.json"
with p.open("x") as f:json.dump(out,f,sort_keys=True,indent=2);f.write("\n")
print(json.dumps({"path":p.relative_to(R).as_posix(),"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"files":rows},sort_keys=True))
