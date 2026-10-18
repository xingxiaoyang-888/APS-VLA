"""Read-only independent reconstruction; writes only own verification.json."""
from pathlib import Path
import hashlib,json,importlib.util,xml.etree.ElementTree as ET
R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
A=R/".local/action_v3_autonomous_dispatch_audit_1808"
D=R/".local/action_v3_autonomous_dispatch_1808"
E={}
def key(p):return p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p)
def read(p,want=None):
 p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 assert want is None or h==want,(str(p),h,want)
 k=key(p);assert k not in E or E[k]==h
 E[k]=h;return b
def obj(p,want=None):return json.loads(read(p,want))
def ref(r):b=read(R/r["path"],r["sha256"]);assert len(b)==r["bytes"];return b
before=obj(A/"inputs_before.json")
for path,want in before["protected_sha256"].items():read(Path(path),want)
author=obj(D/"candidate_review.json","940f1d4358910f5169a100e317be83e1a68e16cd32372167be3e77481a7dbf73")
assert author["status"]=="passed_author_CPU_candidate_pending_independent_root_and_GPU"
for row in author["all_candidate_nonfixture_files"].values():ref(row)
for rel,want in author["dependencies_sha256"].items():read(R/rel,want)
assert author["candidate_files"]["entry.py"]["sha256"]=="1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788"
assert author["candidate_files"]["facade.py"]["sha256"]=="5bee1357c507df49627b9f38e358c7d48c91b8e1e598cb8ffa8aae641724985a"
# Prove final runtime change from the preserved earlier version is only missing-lock precondition plus binding.
old=read(D/"facade_before_missing_lock_guard.py.txt").decode()
new=read(D/"facade.py").decode()
extra="        require((self.state_path.parent/'.writer.lock').is_file(),'shared writer lock missing; check-only never creates it')\n"
assert new==old.replace("        with self.c.exclusive_lock(self.state_path.parent/'.writer.lock'):\n",extra+"        with self.c.exclusive_lock(self.state_path.parent/'.writer.lock'):\n")
old=read(D/"entry_before_missing_lock_guard.py.txt").decode()
assert read(D/"entry.py").decode()==old.replace("b63de6b928f549b03a09380f205c1d301c57608a377d96d6fb4b92c672ad3caf","5bee1357c507df49627b9f38e358c7d48c91b8e1e598cb8ffa8aae641724985a")
nr=obj(R/"configs/experiments/formal_main_v2_node_exclusion_action_gpu_v3.json")
for rel,want in nr["failure_evidence_sha256"].items():read(R/rel,want)
cp=R/"scripts/ops/formal_autonomous_training_v1/controller.py"
cb=read(cp,"acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363")
sp=importlib.util.spec_from_file_location("_independent_parse_controller",cp)
c=importlib.util.module_from_spec(sp);exec(compile(cb,str(cp),"exec"),c.__dict__)
report=obj(D/"read_only_preflight_v2_stdout.json")
execution=obj(D/"read_only_preflight_v2_execution.json")
assert execution["returncode"]==0 and execution["default_mode_tested"] and execution["Slurm_submissions"]==0
assert execution["argv"][-1]==author["candidate_files"]["entry.py"]["sha256"]
assert report["status"]=="passed_read_only_contract_and_live_capacity"
o=report["observation"];jobs=o["registered_jobs"];ids=[str(j["job_id"]) for j in jobs]
assert len(ids)==245 and len(set(ids))==245 and ids==o["queried_job_ids"]
raw=o["snapshot"]
rows=c.parse_sacct(raw["raw_sacct"],set(ids))
assert rows==raw["rows"] and set(rows)==set(ids)
queue={}
for line in raw["raw_squeue"].splitlines():
 if line.strip():
  cs=line.split("|");assert len(cs)==3 and cs[0] in ids and cs[0] not in queue
  queue[cs[0]]={"status":c.state_name(cs[1]),"comment":cs[2]}
assert queue==raw["queue"]
caps=c.capacity(jobs,{"rows":rows,"queue":queue},"3034538")
assert caps==o["capacity"] and not caps["unknown"] and not caps["findings"]
assert len(caps["occupied"])==7 and set(caps["occupied"])==set(report["active_GPU_job_ids"])
cpu=[str(j["job_id"]) for j in jobs if j.get("gpus")==0 and rows[str(j["job_id"])]["gpus"]==0]
assert cpu==o["confirmed_CPU_zero_job_ids"] and "3034538" in cpu
assert rows["3034538"]["status"]=="RUNNING" and "3034538" not in caps["occupied"]
assert report["available"] and report["remote_existing_count"]+report["remote_missing_count"]==307
assert report["full_original_contract_verified"] and report["frozen_R_and_S_files"]==173
assert report["all_eight_v3_sources_unchanged"] and not report["legacy_refresh_called"]
assert not report["state_changed"] and not report["submitted"] and not report["GPU_submitted"]
def xml_counts(p):
 v=ET.fromstring(read(p));s=v if v.tag=="testsuite" else v.find("testsuite")
 return {k:int(s.attrib[k]) for k in ("tests","failures","errors","skipped")},float(s.attrib["time"])
authors,at=xml_counts(D/"pytest_a2.xml");assert authors=={"tests":34,"failures":0,"errors":0,"skipped":0}
tests,tt=xml_counts(A/"pytest_a2.xml");assert tests=={"tests":19,"failures":0,"errors":0,"skipped":0}
oldtests,ot=xml_counts(A/"pytest_a1.xml");assert oldtests=={"tests":17,"failures":1,"errors":0,"skipped":0}
for name in ["test_independent.py","test_independent.a1.py.txt","test_independent.a1_to_a2.diff","pytest_a1.log","pytest_a2.log","execution_a1.json","execution_a2.json","verify_evidence.py"]:read(A/name)
assert obj(A/"execution_a2.json")["returncode"]==0
# Check directive boundaries directly in the unchanged actual wrapper.
wrapper=read(R/"results/formal_main_v2/engineering/formal_main_v2_action_execution_compat_gpu_v3/source/probe.slurm").decode()
for token in ["--gres=gpu:l40:1","--time=01:00:00","--no-requeue"]:assert token in wrapper
after={path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in before["protected_sha256"]}
assert after==before["protected_sha256"]
out={"status":"passed_independent_CPU_checks_and_retained_live_observation_reconstruction","protected_files":len(after),"protected_173_each_R_S":True,
 "author_tests_verified_not_rerun":authors,"independent_final_tests":tests,"independent_seconds":tt,
 "historical_independent_failure":{"counts":oldtests,"cause":"test expected duplicate-stage rejection but consumed-reservation gate correctly rejected earlier; original code/XML/log retained"},
 "reconstructed_read_only":{"registered_jobs":len(ids),"active_GPU_jobs":caps["occupied"],"confirmed_CPU0_job_ids":cpu,"unknown":[],"findings":[],"submissions":0,"capacity_timestamp_is_not_future_reservation_authority":True},
 "unchanged_original_v3_wrapper_boundaries":{"gpus":1,"wall_seconds":3600,"no_requeue":True,"cells":16},
 "production_state_read_by_independent":False,"production_state_writes":0,"Slurm_submissions":0,"GPU_runs":0,"sealed_state_reads":0,
 "read_evidence_sha256":dict(sorted(E.items()))}
with (A/"verification.json").open("xb") as f:f.write((json.dumps(out,indent=2,ensure_ascii=False)+"\n").encode())
print(json.dumps({k:v for k,v in out.items() if k!="read_evidence_sha256"},ensure_ascii=False))
