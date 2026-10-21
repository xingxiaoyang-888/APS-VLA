from pathlib import Path,PurePosixPath
import json,hashlib,fcntl,os
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
E=R/"results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,b):
 assert p.resolve()==p and not any(x.is_symlink() for x in [p,*p.parents])
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(p,x):put(p,(json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode())
def archive(src_rel,dst_name,pin):
 src=R/src_rel;mb=(src/"delivery_manifest.json").read_bytes();assert sha(mb)==pin
 manifest=json.loads(mb);target=E/dst_name;assert not target.exists()
 rows=[]
 for r in manifest["files"]:
  name=r["path"]
  if name.startswith(src_rel+"/"):name=name[len(src_rel)+1:]
  rel=PurePosixPath(name);assert not rel.is_absolute() and ".." not in rel.parts
  p=src/name;assert p.is_file() and not p.is_symlink()
  b=p.read_bytes();assert len(b)==r["bytes"] and sha(b)==r["sha256"],name
  rows.append((name,b,r))
 for name,b,r in rows:put(target/name,b)
 put(target/"delivery_manifest_original.json",mb)
 save(target/"source_map.json",{"kind":"exact_original_author_or_independent_package_copy","source_root":src_rel,"original_manifest_sha256":pin,"file_count":len(rows),"science_result_added":0,"files":[{"source":src_rel+"/"+name,"destination":str((target/name).relative_to(R)),"bytes":len(b),"sha256":sha(b)} for name,b,r in rows]})
 return {"path":str(target.relative_to(R)),"files":len(rows),"bytes":sum(len(x[1]) for x in rows),"original_manifest_sha256":pin}
with (R/"results/experiment_supervisor/.writer.lock").open("a") as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 assert sha((R/"results/experiment_supervisor/state.json").read_bytes())=="d795f666c630ba196f9eba8aae8d5cbed879e10fd596fc95d37c745f281948ba"
 a=archive(".local/goal_remaining5_runtime_20261021T0449","Goal_runtime_author","1db27d51a060e87966e56fe132f9ca9cd323204bddbfb4fa4c8a0791dafbd19f")
 b=archive(".local/goal_remaining5_gateway_independent_20261021T0449","Goal_gateway_independent","aca28a1d699cf1b7087bb997f9133177be55dc52b51465369a2c25f7fc8f127b")
 D=R/".local/goal_remaining5_dispatch_20261021T0449";out=E/"Goal_gateway_root_author";assert not out.exists()
 allowed={"gateway.py","source_provenance.json","verify_cpu_v2.py","CPU_report_v2.json","v3_correction.json","CPU_report_v3.json","scope.json","verify_cpu_v1.py","CPU_report_v1.json","gateway_v1.py","gateway_v3.py","verify_cpu_v3.py"}
 assert {str(p.relative_to(D)) for p in D.rglob("*") if p.is_file()}==allowed
 rows=[]
 for n in sorted(allowed):
  data=(D/n).read_bytes();put(out/n,data);rows.append({"path":n,"bytes":len(data),"sha256":sha(data)})
 save(out/"final_source_provenance.json",{"schema":"formal_main_v2","kind":"root_gateway_three_candidates_provenance","production_source":"gateway_v3.py","production_sha256":"45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b","scope_sha256":"f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b","v3_correction":"Two exact pair_key additions to held dispatch and reservation; v2 rejections retained; no scientific loop change.","runtime_package_sha256":"200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f","CPU":{"positive":302,"rejected":383},"new_GPU_submissions":0,"independent_review":{"path":str((E/"Goal_gateway_independent/independent_review.json").relative_to(R)),"sha256":"c6aecff90587beb0368b0c4d503ca3815da97b222e5f74ec46f3d4bed34043bc"}})
 save(out/"delivery_manifest.json",{"schema":"formal_main_v2","kind":"root_gateway_candidate_history","files":rows,"new_GPU_submissions":0,"private_source_root":str(D.relative_to(R))})
 c=R/".local/goal_remaining5_independent_20261021T0449/plan_check_count_clarification.json";cb=c.read_bytes();assert sha(cb)=="1a620caa6f7a7cfe9ead93e7b98436b3232728eceefb905eddeec2e49b19603a"
 put(E/"Goal_plan_count_clarification.json",cb)
print(json.dumps({"runtime":a,"gateway_independent":b,"root_gateway_files":len(rows)}))
