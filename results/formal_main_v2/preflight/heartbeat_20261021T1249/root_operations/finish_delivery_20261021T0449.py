from pathlib import Path,PurePosixPath
from datetime import datetime,timezone
import argparse,hashlib,importlib.util,json,os,subprocess,sys
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo");B="results/formal_main_v2/preflight/heartbeat_20261021T1249";E="results/formal_main_v2/engineering/supervision_delivery_20261021T0449"
BASE="0b46f1169042e407c128e226b8cc7eabb468e873";STATE="results/experiment_supervisor/state.json";ST="0621504d45ef43e44f6d46c01d0a8c4d0c9acdfdd29d05df9101d75979fc5d6e";SUM="281cb598d6dda4b50420be5439256607fdb5e9c70bf59a8dafba1e68b7546391"
INDEX="7b84527592221abab8dffc3096a623432c8d92560c89f57dc04cc5b13046f6a6";REQ="daf0c53e281d7f637b2a20ba53dc7182d400242b1b5978b006b3aee3a2d01e19"
SNAP="results/formal_main_v2/nonweight_archives/v1/snapshots/last_training_20261020T1644.json";SSHA="1ec87a42055015a0d0ea5e059d913d3d1de0d7be0870b023a81f7ee774976509"
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(n):return dict(path=n,sha256=h(R/n),bytes=(R/n).stat().st_size)
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
 v=rd(src+"/delivery_manifest.json",pin);seen=set();added=[];mapping=[]
 for row in v["files"]:
  n=row["path"];n=n[len(src)+1:] if n.startswith(src+"/") else n
  p=PurePosixPath(n);assert not p.is_absolute() and ".." not in p.parts and n not in seen;seen.add(n)
  assert ref(src+"/"+n)==dict(path=src+"/"+n,sha256=row["sha256"],bytes=row["bytes"])
  out=dst+"/"+n;guard.lexical(out)
  assert row["bytes"]<100*(1<<20) and not out.endswith(".tar.gz") and "/raw_runtime/" not in out and "/observer/blobs/" not in out
  mapping.append(dict(source=src+"/"+n,**cp(src+"/"+n,out)));added.append(out)
 out=dst+"/delivery_manifest_original.json";cp(src+"/delivery_manifest.json",out);added.append(out)
 out=dst+"/root_publication_mapping.json";save(out,dict(source_manifest=ref(src+"/delivery_manifest.json"),files=mapping));added.append(out);return added
ap=argparse.ArgumentParser();ap.add_argument("--delivery-manifest-sha256",required=True);ap.add_argument("--delivery-report-name",required=True);ap.add_argument("--delivery-report-sha256",required=True);ap.add_argument("--stage-manifest-sha256",required=True);ap.add_argument("--stage-report-sha256",required=True);a=ap.parse_args()
assert os.environ.get("CTI_SERVER_CONTROL_ROOT")==str(R)
assert a.delivery_report_name.endswith(".json") and "/" not in a.delivery_report_name
dp=".local/goal_remaining5_Delivery_independent_20261021T0449";gp=".local/git_final_precheck_20261021T0449"
dr=rd(dp+"/"+a.delivery_report_name,a.delivery_report_sha256);gr=rd(gp+"/independent_stage_precheck.json",a.stage_report_sha256)
for report in [dr,gr]:
 assert str(report["status"]).startswith("passed") and report.get("blockers")==[]
 assert INDEX in json.dumps(report) and ST in json.dumps(report) and SUM in json.dumps(report)
ctl=module("scripts/ops/formal_autonomous_training_v1/controller.py","acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363","finish0449ctl")
guard=module("scripts/ops/check_nonweight_archive_stage.py","ebe5d25ff5850fe37e73cec551332ccd2b446aa3c4bbb0e38b6b83ce7a6775f6","finish0449guard")
with ctl.exclusive_lock(R/"results/experiment_supervisor/.writer.lock"):
 assert git("rev-parse","HEAD").stdout.decode().strip()==BASE and h(R/".git/index")==INDEX
 assert h(R/STATE)==ST and h(R/B/"final_summary.json")==SUM
 old=B+"/git_required_files_v1.json";oldv=rd(old,REQ);rows={}
 for row in oldv["files"]:
  n=row["path"];assert n not in rows and ref(n)==row and git("show",":"+n).stdout==(R/n).read_bytes();rows[n]=row
 added=[old,B+"/git_index_guard_v1.json",B+"/git_whitespace_diagnostic_v1.json"]
 added+=package(dp,a.delivery_manifest_sha256,E+"/Delivery_independent")
 added+=package(gp,a.stage_manifest_sha256,E+"/Git_final_precheck")
 push=".local/push_delivery_20261021T0449.py";assert h(R/push)=="6c4c54551f36440e2525b48c3d77eb99b7331a1c8b8dfe036160099e9550ac32"
 for n in [str(Path(__file__).relative_to(R)),push]:
  out=B+"/root_operations/"+Path(n).name;cp(n,out);added.append(out)
 closed=[]
 for p in sorted((R/"results/formal_main_v2/control_transport").glob("*0449*.jsonl")):
  n=p.relative_to(R).as_posix()
  if n in rows:continue
  ev=[json.loads(l) for l in p.read_bytes().splitlines()];assert ev and ev[0]["event"]=="control_start"
  if ev[-1]["event"]!="control_end":
   assert p.name=="finish_delivery_20261021T0449.jsonl",p.name
   continue
  added.append(n);closed.append(ref(n))
 bindings=B+"/git_delivery_audit_bindings.json"
 save(bindings,dict(status="actual_integration_and_exact_index_audited",state=ref(STATE),summary=ref(B+"/final_summary.json"),delivery_audit=ref(E+"/Delivery_independent/"+a.delivery_report_name),Git_final_precheck=ref(E+"/Git_final_precheck/independent_stage_precheck.json"),inherited_runtime_audit=ref(E+"/Goal_runtime_independent/independent_review.json"),inherited_ACK_audit=ref(E+"/Goal_ACK_independent/independent_review.json"),new_scientific_acceptance=0,scientific_terminal_reviews_not_rerun=True,completed_control_traces=closed,normal_GPU_jobs_not_polled=True));added.append(bindings)
 for n in added:
  guard.lexical(n);assert (R/n).stat().st_size<100*(1<<20) and "/raw_runtime/" not in n and "/observer/blobs/" not in n and "/attempt01/" not in n
  assert n not in rows or rows[n]==ref(n);rows[n]=ref(n)
 required=B+"/git_required_files_v2.json";assert required not in rows
 assert len(rows)==len({n.casefold() for n in rows})
 save(required,dict(schema="cti_nonweight_archive_stage_v1",kind="required_files",files=[rows[n] for n in sorted(rows)]))
 for n in added+[required]:assert git("check-ignore","-q","--",n,check=False).returncode==1
 for i in range(0,len(added+[required]),100):git("add","--",*(added+[required])[i:i+100])
 raw=[r["path"] for r in rd(SNAP)["files"]];checked=guard.check(R,SNAP,SSHA,raw,required)
 assert checked["status"]=="verified_index_archive_delivery" and checked["frozen_files_verified_in_worktree_and_index"]==173
 gn=B+"/git_index_guard_v2.json";save(gn,checked);git("add","--",gn)
 git("diff","--cached","--check")
 delivery=B+"/git_delivery_v1.json";save(delivery,dict(status="exact_nonweight_delivery_verified_not_yet_pushed",utc=datetime.now(timezone.utc).isoformat(),baseline=BASE,root_complete_arms=72,accepted_complete_development_trials=7800,new_scientific_trials_accepted=0,unique_initial_states=400,new_GPU_jobs=["3057505","3057510","3057515","3057526","3057533"],saved_observation_GPU_seconds=1995402,cost_final=False,saved_running_GPUs=5,final_sealed=True,exact_CPU_archives=19,source_frozen_files=173,required_files=ref(required),index_guard=ref(gn),independent_delivery=ref(E+"/Delivery_independent/"+a.delivery_report_name),raw_payloads_and_weights_added=False,all_project_writes_server_only=True));git("add","--",delivery)
 assert h(R/STATE)==ST and h(R/B/"final_summary.json")==SUM
 expected=set()
 for n in set(rows)|{required,gn,delivery}:
  prior=git("show",BASE+":"+n,check=False)
  if prior.returncode or prior.stdout!=(R/n).read_bytes():expected.add(n)
 staged=set(git("diff","--cached","--name-only","-z").stdout.decode().strip("\0").split("\0"))
 assert expected==staged,(sorted(expected-staged),sorted(staged-expected))
 for n in sorted(staged):assert git("show",":"+n).stdout==(R/n).read_bytes(),n
 result=git("commit","-m","Dispatch five audited Goal development pairs once and preserve source and ACK evidence")
 head=git("rev-parse","HEAD").stdout.decode().strip()
 save(".local/git_commit_20261021T0449.json",dict(status="committed_not_yet_pushed",commit=head,baseline=BASE,files=len(staged),state_sha256=ST,summary_sha256=SUM,accepted_development=7800,new_acceptance=0,final_sealed=True))
 print(json.dumps(dict(status="committed_not_yet_pushed",commit=head,files=len(staged),summary=result.stdout.decode().splitlines()[:2])))
