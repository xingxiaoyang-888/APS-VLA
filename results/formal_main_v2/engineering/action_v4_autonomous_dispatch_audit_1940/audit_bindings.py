"""Independent, read-only v4 dispatch bindings and mechanical derivation audit."""
import ast, hashlib, importlib.util, json, sys, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode=True
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
P=Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
S=P/"snapshots/formal_main_v2_run_564be0995e"
A=R/".local/action_v4_autonomous_dispatch_audit_1940"
C=R/".local/action_v4_autonomous_dispatch_1940"
O=R/".local/action_v3_autonomous_dispatch_1808"
evidence={}
PANELS={R/("configs/manifests/formal_main_v2/"+s+"/initial_states/development.json") for s in ("libero_10","libero_spatial","libero_object","libero_goal")}
def read(path, expected=None):
 p=Path(path)
 assert p.is_absolute() and (p.is_relative_to(R) or p.is_relative_to(S)),str(p)
 low=str(p).lower()
 assert not any("sealed" in x.lower() or x.lower()=="test" for x in p.parts),str(p)
 if p.suffix not in (".py",".pyc",".pyo"):
  assert not any(x in low for x in ("init_state","initial_state","final_state","test_state")) or p in PANELS,str(p)
 assert p.suffix.lower() not in (".pt",".pth",".safetensors",".ckpt",".bin"),str(p)
 assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if expected is not None:assert h==expected,(str(p),h,expected)
 assert str(p) not in evidence or evidence[str(p)]==h,str(p)
 evidence[str(p)]=h
 return b
def obj(p,h=None):return json.loads(read(p,h))
def load(p,name,h=None):
 b=read(p,h);spec=importlib.util.spec_from_file_location(name,p)
 m=importlib.util.module_from_spec(spec);sys.modules[name]=m
 exec(compile(b,str(p),"exec"),m.__dict__);return m
def assign_values(t):
 out={}
 for node in ast.parse(t).body:
  if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
   try:out[node.targets[0].id]=ast.literal_eval(node.value)
   except (ValueError,TypeError):pass
 return out
def replace_assign(t,name,value):
 nodes=[n for n in ast.parse(t).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id==name]
 assert len(nodes)==1,name
 n=nodes[0];lines=t.splitlines(True)
 return "".join(lines[:n.lineno-1])+name+"="+repr(value)+"\n"+"".join(lines[n.end_lineno:])
def exclusive(p,d):
 with p.open("x",encoding="utf-8",newline="\n") as f:
  json.dump(d,f,indent=2,ensure_ascii=False,allow_nan=False);f.write("\n")
def main():
 before=obj(A/"inputs_before.json","c663f03dd19b82a5044636736971ca513c619dcc6cdd05431cd65e11c94167b3")
 for p,h in before["files"].items():read(p,h)
 pins={"entry.py":"e259572effecf20f8769db47edfd1ac46799e8f50517fe3c98d6dfee919fef56","facade.py":"dd662101cf4e0546784d071925d86d1fd8d3b7a6dafc55fb6dbd74e58b55129e","test_dispatch.py":"38c61494d06ab2797a8473800b6e897b3f504439dcc7fbd2b0232f08c0796b46"}
 texts={n:read(C/n,h).decode() for n,h in pins.items()}
 ev=assign_values(texts["entry.py"]);fv=assign_values(texts["facade.py"])
 old_entry=read(O/"entry.py","1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788").decode()
 old_facade=read(O/"facade.py","5bee1357c507df49627b9f38e358c7d48c91b8e1e598cb8ffa8aae641724985a").decode()
 expected=old_entry.replace("v3","v4").replace("all_eight_v4_sources_unchanged","all_six_v4_sources_unchanged")
 for name in ("REL","FACADE_SHA","SOURCE","BINDINGS","REFS","NODE_REG"):expected=replace_assign(expected,name,ev[name])
 assert expected==texts["entry.py"],"entry non-mechanical change"
 expected=replace_assign(old_facade.replace("v3","v4"),"RESERVATION",fv["RESERVATION"])
 assert expected==texts["facade.py"],"facade non-mechanical change"
 binding=obj(R/"results/formal_main_v2/preflight/heartbeat_20261019T0340/action_v4_root_binding.json","b794d8bb982b49577a2139b5edbd924aedc605a46ae484bd819438b7fe8e42bd")
 for k in ("root_review","gpu_registration","node_registration","reservation","check","candidate_independent"):
  obj(R/binding[k]["path"],binding[k]["sha256"])
 assert ev["REFS"]["root_review"]==binding["root_review"]
 assert ev["REFS"]["gpu_registration"]==binding["gpu_registration"]
 assert ev["NODE_REG"]==binding["node_registration"] and fv["RESERVATION"]==binding["reservation"]
 assert ev["FACADE_SHA"]==pins["facade.py"] and ev["REL"]==".local/action_v4_autonomous_dispatch_1940/"
 assert ev["SOURCE"]=="results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4/source/"
 assert len(ev["BINDINGS"])==6
 for n,h in ev["BINDINGS"].items():read(R/(ev["SOURCE"]+n),h)
 entry=load(C/"entry.py","independent_v4_binding_entry",pins["entry.py"])
 facade=entry.load_facade()
 orig=facade.load(R/(ev["SOURCE"]+"submit.py"),"independent_v4_binding_submit",ev["BINDINGS"]["submit.py"])
 checked=orig.c.check_contract(R,root_ref=ev["REFS"]["root_review"],manifest_ref=ev["REFS"]["manifest"],registration_ref=ev["REFS"]["gpu_registration"])
 assert len(checked["deployment_files"])==290
 for row in checked["deployment_files"]:
  b=read(R/row["path"],row["sha256"]);assert len(b)==row["bytes"]
 for rel,h in checked["inventory"]["files"].items():read(R/rel,h);read(S/rel,h)
 assert len(checked["inventory"]["files"])==173
 reg=checked["registration"];manifest=checked["manifest"];root=checked["root_review"]
 prior=obj(R/"configs/experiments/formal_main_v2_action_execution_compat_gpu_v3.json")
 oldmanifest=obj(R/"results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/candidate_manifest.json")
 assert reg["version"]=="formal_main_v2_action_execution_compat_gpu_v4"
 assert reg["output_root"]==str(P/"results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v4")
 for k in ("limits","suite_order","method_order","gpus","attempt","automatic_retry"):assert reg[k]==prior[k],k
 assert manifest["suites"]==oldmanifest["suites"],"registered suite targets changed"
 assert reg["limits"]["cells"]==16 and reg["limits"]["max_vla_calls"]==16 and reg["limits"]["wall_seconds"]==3600
 assert reg["automatic_retry"] is False and reg["attempt"]==1
 assert manifest["action_adapter"]==oldmanifest["action_adapter"]
 assert root["gpu_registration_intent_sha256"]==orig.c.registration_intent(reg)
 cycle={ev["REFS"]["root_review"]["path"],ev["REFS"]["gpu_registration"]["path"],str((C/"entry.py").relative_to(R)),str((C/"facade.py").relative_to(R))}
 assert not cycle.intersection(root["evidence_sha256"])
 assert not cycle.intersection({x["path"] for x in root["deployment_files"]})
 assert root["scientific_release"] is False and root["scientific_trials"]==0
 assert root["engineering_cells"]==16 and root["final_states_opened"] is False
 constructor=reg["cpu_reviews"]["action_adapter_independent"]
 assert "formal_main_v2_action_execution_compat_gpu_v3/source/" in constructor["path"]
 node=obj(R/ev["NODE_REG"]["path"],ev["NODE_REG"]["sha256"])
 assert node["excluded_nodes"]==["gpu4020"] and node["automatic_retry"] is False
 reservation=obj(R/fv["RESERVATION"]["path"],fv["RESERVATION"]["sha256"])
 assert reservation["reserved_slots"]==1 and reservation["controller_job_id"]=="3034538"
 assert reservation["registration"]==binding["gpu_registration"]
 author=obj(C/"candidate_review.json","2a0d887587127347be0ff226cc46c057b0adb8bf12ec7eb4171753dfd6173c15")
 refs=obj(C/"references.json","25eb924c10b35dae82e4ad97bba656287ce3cef6ca53d836d52ad901e88dbada")
 assert len(refs["path_sha256"])==501
 for p,h in refs["path_sha256"].items():read(p,h)
 read(C/"final_binding.json","86509715c2a7875e5431df0b37e3276a5b8ce886b7467de44cb9f54993e3ee8a")
 xml=ET.fromstring(read(A/"pytest_a1.xml"));suites=list(xml) if xml.tag=="testsuites" else [xml]
 counts={k:sum(int(s.attrib.get(k,0)) for s in suites) for k in ("tests","failures","errors","skipped")}
 assert counts==dict(tests=21,failures=0,errors=0,skipped=0),counts
 for n in ("test_control_independent.py","pytest_a1.command.json","pytest_a1.execution.json","pytest_a1.log"):read(A/n)
 for p,h in before["files"].items():read(p,h)
 read(Path(__file__))
 result=dict(schema="formal_main_v2",kind="independent_v4_dispatch_static_closure_and_derivation",status="passed",
  created_utc=datetime.now(timezone.utc).isoformat(),source_pins=pins,
  exact_mechanical_entry_and_facade=True,root_bindings=binding,
  deployment_closure_count=len(checked["deployment_files"]),R_S_frozen_each=173,
  protected_files_unchanged=len(before["files"]),author_refs_rehashed=len(refs["path_sha256"]),
  independent_tests=counts,unchanged_registered_suite_targets=True,
  unchanged_selected_checkpoint_metadata=True,metadata_only_checkpoint_content_not_opened=True,
  unchanged_limits=reg["limits"],v3_adapter_constructor_reused=True,
  root_intent_self_reference_excluded=True,root_and_registration_absent_from_signed_deployment=True,
  final_control_entry_and_facade_not_in_upstream_signed_closure=True,
  prior_failed_v3_preserved_by_mechanical_and_CPU_test=True,
  actual_Slurm_queries=0,actual_Slurm_submissions=0,production_state_reads=0,production_state_writes=0,
  GPU_calls=0,sealed_state_reads=0,scientific_release=False,
  pending_requirement="Root must perform a fresh same-lock all-registry Slurm/capacity/reservation check before any one-shot submit.",
  read_evidence_sha256=evidence)
 exclusive(A/"static_binding_review.json",result)
 print(json.dumps({k:v for k,v in result.items() if k not in ("read_evidence_sha256","root_bindings","unchanged_limits")},indent=2))
 print("STATIC_SHA",hashlib.sha256((A/"static_binding_review.json").read_bytes()).hexdigest(),"REFS",len(evidence))
if __name__=="__main__":main()
