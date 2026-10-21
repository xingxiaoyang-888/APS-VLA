from pathlib import Path
import hashlib,importlib.util,json,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
B="results/formal_main_v2/preflight/heartbeat_20261021T0910"
EXACT={
"results/formal_main_v2/execution/object_single_error_v1/root_legacy_adoption.json":"c431646cbac00f461177e95361fb8d31d66c78bcfbbfc2b5c766edb8eabd6d24",
"results/formal_main_v2/execution/object_single_error_v1/legacy599_adoption_rows.jsonl":"ac792e8d88f251f097f3f0e110e6c32aa45dbacd103404c0189b3bebf56ccb5e",
"results/formal_main_v2/engineering/supervision_delivery_20261020T2358/Object_single_error_independent/canonical599_adoption_addendum.json":"d9d6de64311c45639a40a028e75a2697ac5cb605b892e881c50e81ab4b4e5ecf",
"results/formal_main_v2/engineering/supervision_delivery_20261020T2253/Object599_independent/independent_review.json":"62c0a39784953b14f061ae7d161813f5e4bbfa5c8db39297e7047327b28463f7"}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents))
p=R/"scripts/ops/formal_autonomous_training_v1/controller.py";assert h(p)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
spec=importlib.util.spec_from_file_location("obproof0910ctl",p);c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 state=R/"results/experiment_supervisor/state.json";before=h(state);assert before=="40e7b58265a49ef61b8a02a793d3ce96c22bb84c93eae14a0b6bcf196ffd221a"
 rows=[]
 for rel,want in EXACT.items():
  src=R/rel;dst=P/rel;safe(src);safe(dst);assert h(src)==want
  if dst.exists():assert h(dst)==want
  rows.append(dict(path=rel,sha256=want,bytes=src.stat().st_size,already_present=dst.exists()))
 for row in rows:
  if not row["already_present"]:
   src=R/row["path"];dst=P/row["path"];dst.parent.mkdir(parents=True,exist_ok=True);dst.open("xb").write(src.read_bytes())
  assert h(P/row["path"])==row["sha256"]
 assert h(state)==before
 receipt=dict(status="four_exact_prior_evidence_files_mirrored_R_to_P",files=rows,state_unchanged=True,source_runtime_unchanged=True,actual_P_verify_passed=False,new_trials=0,new_GPU_jobs=[],not_runtime_admission=True)
 out=R/B/"Object_prior_evidence_publication.json"
 with out.open("x") as f:json.dump(receipt,f,sort_keys=True,ensure_ascii=False,indent=2);f.write("\n")
 print(json.dumps(dict(path=str(out.relative_to(R)),sha256=h(out),files=len(rows))))
