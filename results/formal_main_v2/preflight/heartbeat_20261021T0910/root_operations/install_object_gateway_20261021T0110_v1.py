from pathlib import Path
import argparse,hashlib,importlib.util,json,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA");S=P/"snapshots/formal_main_v2_run_564be0995e"
B="results/formal_main_v2/preflight/heartbeat_20261021T0910";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0110"
PKG=E+"/Object_single_error_gateway";MAP=PKG+"/publication_map.json"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(n):return json.loads((R/n).read_bytes())
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
def save(n,v):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("x") as f:json.dump(v,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
def safe(p):assert p.resolve()==p and not any(x.is_symlink() for x in (p,*p.parents))
ap=argparse.ArgumentParser();ap.add_argument("--independent-review",required=True);ap.add_argument("--independent-review-sha256",required=True);ap.add_argument("--expected-state-sha256",required=True);a=ap.parse_args()
assert a.independent_review.startswith(E+"/Downstream_runtime_independent/") and ".." not in Path(a.independent_review).parts
assert h(R/a.independent_review)==a.independent_review_sha256
review=rd(a.independent_review)
assert h(R/MAP)=="6d0299502b095d4ea6b7d08e0ce16b9ff502e7352b1186b4d877b4b2f5724bf5"
mp=rd(MAP);files={x["destination"]:x["sha256"] for x in mp["files"]};assert len(files)==3
assert review["kind"]=="Object_single_error_gateway_independent_review" and review["status"]=="passed" and review["review_scope"]=="source_and_CPU_only" and review["GPU_execution_authorized"] is False and review["blockers"]==[] and review["gateway_files"]==files
pub=rd("results/formal_main_v2/engineering/supervision_delivery_20261020T2358/Object_single_error_production/publication_map.json");ten={x["destination"]:x["sha256"] for x in pub["files"]};assert len(ten)==10 and review["production_sources"]==ten
ip="results/formal_main_v2/source/formal_main_v2_run_564be0995e.json";assert h(R/ip)=="5baef5e7adc942b9d9c58eb7afe3faf69417f4d7939791997876652238a12926";inv=rd(ip);assert len(inv["files"])==173
cp=R/"scripts/ops/formal_autonomous_training_v1/controller.py";assert h(cp)=="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363";sp=importlib.util.spec_from_file_location("objgwinstall0910",cp);c=importlib.util.module_from_spec(sp);sys.modules[sp.name]=c;sp.loader.exec_module(c)
with c.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 state=R/"results/experiment_supervisor/state.json";before=h(state);assert before==a.expected_state_sha256
 for rel,want in inv["files"].items():
  for base in [R,S,R/"snapshots/formal_main_v2_run_564be0995e"]:assert h(base/rel)==want
 for rel,want in ten.items():assert h(R/rel)==h(P/rel)==want
 rows=[]
 for row in mp["files"]:
  rel=row["destination"];src=R/PKG/Path(row["source"]).name;safe(src);assert h(src)==row["sha256"] and src.stat().st_size==row["bytes"]
  assert row["roots"]==[str(R),str(P)] and rel.startswith("scripts/ops/formal_object_single_error_gateway_v1/")
  for root in [R,P]:safe(root/rel);assert not (root/rel).exists()
  rows.append(row)
 for row in rows:
  data=(R/PKG/Path(row["source"]).name).read_bytes()
  for root in [R,P]:
   dst=root/row["destination"];dst.parent.mkdir(parents=True,exist_ok=True);dst.open("xb").write(data);assert h(dst)==row["sha256"]
 assert h(state)==before
 save(B+"/Object_gateway_publication.json",dict(status="exact_independent_CPU_reviewed_gateway_sources_installed",source_manifest=ref(PKG+"/delivery_manifest_original.json"),map=ref(MAP),independent_review=ref(a.independent_review),files=rows,old10_unchanged=True,frozen173_unchanged=True,state_unchanged=True,actual_P_verify_passed=False,new_GPU_jobs=[],new_trials=0))
 print(json.dumps(dict(receipt=ref(B+"/Object_gateway_publication.json"),state_sha256=before)))
