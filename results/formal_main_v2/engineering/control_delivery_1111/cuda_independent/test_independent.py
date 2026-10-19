"""Independent CPU tests: no Slurm/network or production writes."""
import copy,hashlib,importlib.util,json
from pathlib import Path
import pytest

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
C=R/".local/cuda_continuous_admission_1111"
PINS={"admission.py":"65a6a6c22710ba74f43c86589b7acdac7bd3c1b10fd86028d339eb98e3f71dcb","gateway.py":"a0f81f18ccdb6f9b0cd5f5f3f871b3f6ab451809a1c6386e347ea3602abd9792","test_continuation.py":"408e154a2a7558d8d14cd631408e438c5514e1e0b5f0c9c9ff1077793f62dc55","real_prepare_a1.json":"80db41eed2cba90f5067fe81faa79a0c640c56e26d88f2227e6759e6a5f76b4b"}
for n,h in PINS.items():assert hashlib.sha256((C/n).read_bytes()).hexdigest()==h
spec=importlib.util.spec_from_file_location("independent_candidate_fixture",C/"test_continuation.py")
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
g,a,c,d=f.g,f.a,f.c,f.d
box=f.box
io_case=f.io_case
typed_fixture=f.typed_fixture

class NoBackend:
 def inspect_and_prepare(self,*args,**kwargs):raise AssertionError("unresolved pending reached backend")
 def verify_evidence(self,*args,**kwargs):raise AssertionError("unresolved pending reached cached evidence")

@pytest.mark.parametrize("fault",["timeout","checkpoint","final_CAS"])
def test_actual_candidate_pending_held_by_actual_controller(box,monkeypatch,fault):
 if fault=="checkpoint":box.io.fault="checkpoint"
 elif fault=="timeout":box.slurm.fault="timeout"
 else:
  original=box.gate.cas;count=[0]
  def cas(value):
   count[0]+=1
   if count[0]==3:raise OSError("independent final CAS injection")
   return original(value)
  monkeypatch.setattr(box.gate,"cas",cas)
 with pytest.raises((TimeoutError,ValueError,OSError)):box.gate.run(submit=True)
 before=box.read();pending=copy.deepcopy(before["pending_submission"]);control=copy.deepcopy(before["autonomous_training_v1"])
 assert pending is not None
 calls=len(box.slurm.calls)
 pairs=[{"suite":su,"visual_tokens":bu,"seed":se,"sha256":"d"*64} for su in ("libero_10","libero_spatial","libero_object","libero_goal") for bu in (256,128,64) for se in (17,23,41)]
 ctl=c.Controller(box.root,box.root/"independent_controller",pairs,NoBackend(),box.slurm,a.ACTIVATION["sha256"],"3034538")
 ctl._lease=True;got=ctl.tick();after=box.read()
 assert got["status"]=="unresolved_submission" and after["pending_submission"]==pending
 assert len(box.slurm.calls)==calls
 for key in ("blocked_pairs","reserved_GPU_slots","reservation_root_record"):
  assert after["autonomous_training_v1"][key]==control[key]
 for oldjob,newjob in zip(before["registered_jobs"][:2],after["registered_jobs"][:2]):
  for key in ("job_id","status","exit_code","elapsed_seconds","gpus","invocation","invocation_sha256","source_sha256"):
   assert newjob[key]==oldjob[key]

def test_missing_recheck_cannot_reach_sbatch(box,monkeypatch):
 monkeypatch.delattr(type(box.io),"recheck")
 with pytest.raises(AttributeError):box.gate.run(submit=True)
 assert box.read()["pending_submission"]["status"]=="prepared_before_invocation_publication"
 assert not box.slurm.calls
 assert (box.root/a.INVREL).is_file()

def test_second_observation_loses_only_free_slot(box,monkeypatch):
 state=box.read()
 extra={"job_id":"9900","name":"cti-engineering","gpus":1,"status":"PENDING","exit_code":"0:0","experiment":"formal_main_v2","mode":"engineering"}
 state["registered_jobs"].append(extra);box.write(state)
 original=box.slurm.observe;calls=[0]
 def observe(jobs):
  calls[0]+=1;s=original(jobs)
  if calls[0]==1:
   s["rows"]["9900"]["status"]="COMPLETED";s["queue"].pop("9900",None)
  return s
 monkeypatch.setattr(box.slurm,"observe",observe)
 with pytest.raises(ValueError,match="unreserved GPU capacity"):box.gate.run(submit=True)
 assert calls==[2] and not box.slurm.calls and box.read()["pending_submission"] is None
 assert not box.gate.audit.exists()

def test_ack_wrong_comment_remains_known_pending(box,monkeypatch):
 original=box.slurm.observe
 def observe(jobs):
  s=original(jobs)
  if "777777" in s["rows"]:
   s["queue"]["777777"]["comment"]="cti-cuda-continuous-v1:WRONG"
  return s
 monkeypatch.setattr(box.slurm,"observe",observe)
 with pytest.raises(ValueError):box.gate.run(submit=True)
 state=box.read()
 assert state["pending_submission"]["known_job_id"]=="777777"
 assert "777777" not in [j["job_id"] for j in state["registered_jobs"]]
 assert len(box.slurm.calls)==1
 with pytest.raises(ValueError):box.gate.run(submit=True)
 assert len(box.slurm.calls)==1

def test_new_metadata_never_claims_old_recovery_authorization(box):
 old=copy.deepcopy(box.read())
 job=box.gate.run(submit=True)["job"]
 md=job["startup_recovery"]
 assert md["kind"]=="cuda_recovered_continuation_scheduler_metadata"
 assert md["version"]==a.VERSION and md["phase"]=="continuous_after_original_target_recovery"
 assert md["authorization"]==box.ref
 assert job["continuous_admission"]["target_updates_per_arm"]==5000
 assert job["continuous_admission"]["prior_job_ids"]==["3028460","3039258"]
 assert "autonomous_execution" not in job
 assert box.read()["registered_jobs"][:2]==old["registered_jobs"][:2]
 assert d.registered_comment(job)==job["continuous_admission"]["request_token"]
 argv=job["continuous_admission"]["actual_sbatch_argv"]
 assert "--chdir="+str(a.P) in argv
 assert "--output="+str(a.P/"results/slurm/%x_%j.out") in argv
 assert "--error="+str(a.P/"results/slurm/%x_%j.err") in argv
 assert "--time=48:00:00" in argv and "--no-requeue" in argv and "--exclude=gpu4020" in argv

@pytest.mark.parametrize("case",["duplicate_A","missing_B"])
def test_native_exact_two_different_arms(io_case,case):
 io,plan=io_case
 if case=="duplicate_A":plan["server_resume_checks"]=[plan["server_resume_checks"][0],copy.deepcopy(plan["server_resume_checks"][0])]
 else:plan["server_resume_checks"]=plan["server_resume_checks"][:1]
 with pytest.raises(ValueError,match="two resume"):io.preflight(plan)

def test_native_symlink_resume_rejected_before_file_hash(io_case):
 io,plan=io_case;row=plan["server_resume_checks"][0];path=Path(row["path"])
 backup=path.with_name("synthetic_original_bytes");path.rename(backup);path.symlink_to(backup)
 with pytest.raises(ValueError,match="symlink"):io.preflight(plan)

@pytest.mark.parametrize("field,value",[
 ("kind","root_cuda_single_recovery_authorization"),
 ("status","draft_pending_root_review"),
 ("automatic_retry",True),
 ("controller_admission_changed",True),
 ("cursor_before",{"A":0,"B":0})])
def test_real_typed_validator_rejects_wrong_semantics(typed_fixture,field,value):
 root,auth,ref=typed_fixture;auth[field]=value
 with pytest.raises(ValueError,match="typed"):g.validate_authorization(root,ref("independent_bad",auth))

def test_real_typed_validator_validates_source_and_independent_binding(typed_fixture):
 root,auth,ref=typed_fixture
 indpath=root/auth["independent_review"]["path"];ind=json.loads(indpath.read_bytes())
 ind["files"][a.CANON+"admission.py"]="0"*64
 indpath.write_bytes(a.canonical(ind));auth["independent_review"]["sha256"]=a.digest(indpath.read_bytes())
 with pytest.raises(ValueError,match="independent"):g.validate_authorization(root,ref("independent_bad_identity",auth))

@pytest.mark.parametrize("path",[
 "configs/manifests/initial_states/sealed_final.json",
 "results/formal_main_v2/test/data.json",
 "results/formal_main_v2/checkpoints/metadata.json",
 "results/formal_main_v2/../elsewhere.json"])
def test_lexical_rejection_precedes_any_payload_io(tmp_path,monkeypatch,path):
 reads=[]
 def forbidden(*args,**kwargs):reads.append(args);raise AssertionError("forbidden path reached IO")
 monkeypatch.setattr(a,"stable",forbidden)
 with pytest.raises(ValueError):a.Evidence(tmp_path).read(path)
 assert reads==[]
