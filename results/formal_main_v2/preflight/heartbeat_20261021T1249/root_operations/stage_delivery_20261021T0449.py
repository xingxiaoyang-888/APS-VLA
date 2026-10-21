from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");B="results/formal_main_v2/preflight/heartbeat_20261021T1249";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
BASE="0b46f1169042e407c128e226b8cc7eabb468e873";STATE="results/experiment_supervisor/state.json";ST="0621504d45ef43e44f6d46c01d0a8c4d0c9acdfdd29d05df9101d75979fc5d6e";SUM="281cb598d6dda4b50420be5439256607fdb5e9c70bf59a8dafba1e68b7546391"
SNAP="results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json";SSHA="1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):p=R/n;return dict(path=n,sha256=h(p),bytes=p.stat().st_size)
def rd(n,pin=None):
 if pin:assert h(R/n)==pin,n
 return json.loads((R/n).read_bytes())
def put(n,b):
 p=R/n;assert p.resolve()==p and not any(q.is_symlink() for q in [p,*p.parents]);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open("xb") as f:f.write(b);f.flush();os.fsync(f.fileno())
def save(n,v):put(n,(json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode());return ref(n)
def cp(src,dst):put(dst,(R/src).read_bytes());return ref(dst)
def module(n,pin,label):
 assert h(R/n)==pin
 sp=importlib.util.spec_from_file_location(label,R/n);m=importlib.util.module_from_spec(sp);sys.modules[label]=m;sp.loader.exec_module(m);return m
def git(*args,check=True):return subprocess.run(["git","-c","core.quotepath=false",*args],cwd=R,capture_output=True,check=check)
def package(src,pin,dst):
 mp=src+"/delivery_manifest.json";v=rd(mp,pin);seen=set();mapping=[]
 for row in v["files"]:
  n=row["path"];n=n[len(src)+1:] if n.startswith(src+"/") else n
  p=PurePosixPath(n);assert not p.is_absolute() and ".." not in p.parts and n not in seen;seen.add(n)
  assert ref(src+"/"+n)==dict(path=src+"/"+n,sha256=row["sha256"],bytes=row["bytes"])
  mapping.append(dict(source=src+"/"+n,**cp(src+"/"+n,dst+"/"+n)))
 cp(mp,dst+"/delivery_manifest_original.json");save(dst+"/root_publication_mapping.json",dict(source_manifest=ref(mp),files=mapping))
assert os.environ.get("CTI_SERVER_CONTROL_ROOT")==str(R)
ctl=module("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","stage0449ctl")
guard=module("scripts/ops/check_nonweight_archive_stage.py","ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6","stage0449guard")
with ctl.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 assert git("rev-parse","HEAD").stdout.decode().strip()==BASE and not git("diff","--cached","--name-only").stdout
 assert h(R/STATE)==ST
 s=rd(B+"/final_summary.json",SUM);assert s["compatible_development_trials"]==7800 and s["current_action_development_trials"]==6589 and s["final_sealed"] and len(s["new_GPU_jobs"])==5 and s["new_current_development_trials_accepted"]==0
 q=rd(B+"/root_integration_receipt.json");assert q["state_after"]==ref(STATE) and q["summary"]==ref(B+"/final_summary.json")
 pre=rd(".local/git_stage_precheck_20261021T0449/independent_precheck.json","10f50efa57479dedab60af4ae08937c40f42107e8eb53d3e9054658f5db52d5f")
 assert pre["status"]=="passed_current_archive_precheck_pending_final_required" and pre["blockers"]==[]
 package(".local/git_stage_precheck_20261021T0449","744e7a5426bb9d1b4fc29cecf1f01453d74346c865e5319ba71e4e7c9e66ca57",E+"/Git_static_precheck")
 helper_names=["archive_goal_plans_20261021T0449.py","archive_goal_runtime_20261021T0449.py","authorize_goal_remaining5_20261021T0449.py","build_goal_remaining5_dispatch_20261021T0449.py","complete_goal_method_metadata_20261021T0449.py","freeze_goal_remaining5_scope_20261021T0449.py","integrate_goal_remaining5_20261021T0449.py","observe_20261021T0449.py","observe_goal_dispatch_20261021T0449.py","prepare_goal_remaining5_20261021T0449.py","publish_goal_remaining5_design_20261021T0449.py","publish_goal_remaining5_plans_20261021T0449.py","publish_goal_remaining5_runtime_20261021T0449.py","publish_goal_remaining5_storage_20261021T0449.py",Path(__file__).name]
 for n in helper_names:cp(".local/"+n,B+"/root_operations/"+n)
 selected=set()
 for root in [B,E]:
  for p in (R/root).rglob("*"):
   if p.is_file():assert p.resolve()==p and not p.is_symlink();selected.add(p.relative_to(R).as_posix())
 manifest_name="scripts/ops/formal_goal_remaining5_gate_v1/package_manifest.json";manifest=rd(manifest_name,"200dcef220601fd26565bb48106856612853739f486f8374ef91a4967e60692f")
 assert len(manifest["files"])==20
 for n,pin in manifest["files"].items():assert h(R/n)==pin;selected.add(n)
 selected.update([manifest_name,"scripts/ops/formal_goal_remaining5_gate_v1/README.md","scripts/ops/formal_goal_remaining5_dispatch_v1/gateway.py","scripts/ops/formal_goal_remaining5_dispatch_v1/scope.json","scripts/ops/formal_goal_remaining5_dispatch_v1/README.md"])
 assert h(R/"scripts/ops/formal_goal_remaining5_dispatch_v1/gateway.py")=="45003c082efc508249e9ba41aac15639be7c4188d9517ee1717e71f563448f9b"
 assert h(R/"scripts/ops/formal_goal_remaining5_dispatch_v1/scope.json")=="f44e8cf97e0a9456782ea57ffeb4c4f39e47058b51c320b3947c73bd1a6cf27b"
 top={"dispatch_admission.json","effective_plan.json","execution_contract.json","execution_manifest.json","held_dispatch_record.json","independent_readiness.json","invocation_template.json","plan_independent_review.json","plan_root_review.json","reservation.json","root_authorization.json","root_readiness.json","runtime_readiness.json","scientific_plan.json","source_provenance.json","specification.json"}
 events={"committed.json","failed_transaction.json","held_capacity_before_registration.json","held_identity.json","pending.json","post_release_observation.json","preflight.json","registered_held.json","release_attempt.json","release_result.json","released_identity.json","sbatch_result.json"}
 assert len(top|events)==28
 execution_files=[]
 for key in manifest["pair_keys"]:
  x="results/formal_main_v2/execution/goal_remaining5_v1/"+key
  expected={x+"/"+n for n in top}|{x+"/dispatch_attempt01/"+n for n in events}
  for n in sorted(expected):assert (R/n).is_file();selected.add(n);execution_files.append(ref(n))
 prepared=rd(B+"/Goal_remaining5_prepared_invocations.json","45a1fe173f83597a8181f5129a5354bbdf0f49143743eac96de2dff8a418e578")
 assert len(prepared["original_invocations"])==5
 for row in prepared["original_invocations"]:assert h(R/row["path"])==row["sha256"];selected.add(row["path"])
 for n in [STATE,"docs/正式主实验规划.md","docs/完整实验计划.md","docs/实验进度.md","docs/正式主实验阶段结论.md","docs/正式下游阻塞登记_20261021T0449.md"]:selected.add(n)
 traces=[];deferred=[]
 for p in sorted((R/"results/formal_main_v2/control_transport").glob("*0449*.jsonl")):
  rows=[json.loads(l) for l in p.read_bytes().splitlines()];assert rows and rows[0]["event"]=="control_start"
  n=p.relative_to(R).as_posix()
  if rows[-1]["event"]!="control_end":deferred.append(n);continue
  selected.add(n);traces.append(ref(n))
 trace_meta=B+"/root_transport_manifest.json";save(trace_meta,dict(files=traces,in_progress_deferred=deferred,not_polled_or_interrupted=True));selected.add(trace_meta)
 tar_review=rd(E+"/Git_static_precheck/CPU_tar_member_review.json");assert tar_review["archive_count"]==19
 archives=[]
 for row in tar_review["archives"]:
  a=row["archive"];assert a==ref(a["path"]) and a["path"] in selected
  assert row["all_members_sha_bytes_verified"] and row["all_retained_private_members_equal"]
  m=row["member_manifest"];assert ref(m["path"])==m
  archives.append(a)
 allow=B+"/git_external_nonweight_allowlist_v1.json"
 save(allow,dict(kind="exact_development_control_and_CPU_evidence_only",CPU_archives=archives,CPU_member_count=tar_review["total_members"],closed_dispatch_metadata=execution_files,actual_scientific_results_added=0,explicit_exclusions=["entire results/formal_main_v2/raw_runtime","all observer/blobs including rng.json","all live Slurm and runtime logs","all attempt01 production raw output","all weights/checkpoints","all sealed final values"],first_accounting_delay_failures_preserved=5));selected.add(allow)
 assert len(selected)==len({n.casefold() for n in selected})
 for n in selected:
  guard.lexical(n);assert (R/n).stat().st_size<100*(1<<20)
  assert "/raw_runtime/" not in n and "/observer/blobs/" not in n and "/results/slurm/" not in n and "/attempt01/" not in n
  if n.endswith(".tar.gz"):assert n in {a["path"] for a in archives},n
 ignored=[]
 for n in sorted(selected):
  z=git("check-ignore","-q","--",n,check=False);assert z.returncode in [0,1]
  if z.returncode==0:ignored.append(ref(n))
 ign=B+"/git_ignored_allowlist_v1.json";save(ign,dict(kind="exact_nonweight_paths_only",files=ignored));selected.add(ign)
 required=B+"/git_required_files_v1.json";save(required,dict(schema="cti_nonweight_archive_stage_v1",kind="required_files",files=[ref(n) for n in sorted(selected)]))
 ignored_set={x["path"] for x in ignored}
 normal=sorted((selected|{required})-ignored_set);forced=sorted(ignored_set)
 for i in range(0,len(normal),100):git("add","--",*normal[i:i+100])
 for i in range(0,len(forced),100):git("add","-f","--",*forced[i:i+100])
 for n in sorted(selected|{required}):assert git("show",":"+n).stdout==(R/n).read_bytes(),n
 raw=[r["path"] for r in rd(SNAP)["files"]];checked=guard.check(R,SNAP,SSHA,raw,required)
 assert checked["status"]=="verified_index_archive_delivery" and checked["frozen_files_verified_in_worktree_and_index"]==173
 gn=B+"/git_index_guard_v1.json";save(gn,checked)
 diag=git("diff","--cached","--check",check=False);wn=B+"/git_whitespace_diagnostic_v1.json";save(wn,dict(returncode=diag.returncode,stdout=diag.stdout.decode(),stderr=diag.stderr.decode()))
 git("add","--",gn,wn)
 assert not diag.returncode,diag.stdout.decode()
 assert h(R/STATE)==ST and h(R/B/"final_summary.json")==SUM
 print(json.dumps(dict(status="staged_not_committed",required=ref(required),index_sha256=h(R/".git/index"),staged_count=len(git("diff","--cached","--name-only").stdout.decode().splitlines()),deferred_traces=deferred,state_sha256=ST,summary_sha256=SUM)))
