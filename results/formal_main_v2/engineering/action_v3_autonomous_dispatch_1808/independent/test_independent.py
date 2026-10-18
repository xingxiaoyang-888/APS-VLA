"""Independent CPU checks; synthetic scheduler/publication/ack only.
The old execute_submit, real node adapter, real Facade, real Slurm parser,
shared writer lock and CAS are exercised unchanged. No production state I/O.
"""
import copy, importlib.util, json, hashlib
from pathlib import Path
import pytest

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
D=R/".local/action_v3_autonomous_dispatch_1808"
PINS={
 "facade.py":"5bee1357c507df49627b9f38e358c7d48c91b8e1e598cb8ffa8aae641724985a",
 "entry.py":"1cb2e30fbde96376183f77b5fb863e823500e2601f2157af00f93ff5ee703788",
 "test_dispatch.py":"c2c8d064958dc0e1e2fb80e3ff1c485358e80c6d4be31bf9a38de007bf54e7d3",
}
for name,want in PINS.items():
 assert hashlib.sha256((D/name).read_bytes()).hexdigest()==want
spec=importlib.util.spec_from_file_location("_independent_author_fixture",D/"test_dispatch.py")
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

@pytest.fixture
def box(tmp_path,monkeypatch):
 return a.box.__wrapped__(tmp_path,monkeypatch)

def state(box):return a.ctl.read_json(box.sp)
def refuse_without_publication(box):
 before=box.sp.read_bytes()
 with pytest.raises((ValueError,RuntimeError,OSError)):box.run()
 assert box.sp.read_bytes()==before and not box.commands
 assert not (box.root/a.orig.c.INVOCATION).exists()
 assert not list((box.root/"results/formal_main_v2/submissions").glob("*.json"))

def training(state,jid,seed):
 row=next(j for j in state["registered_jobs"] if j["job_id"]==jid)
 row.update(mode="train",suite="libero_10",visual_tokens=128,training_seed=seed)

def test_actual_transaction_preserves_all_fields_and_old_refresh_never_runs(box,monkeypatch):
 original=a.fmod.load;called=[]
 def loaded(path,*args,**kwargs):
  mod=original(path,*args,**kwargs)
  if Path(path).name=="formal_supervisor.py":
   def forbidden(*_a,**_k):
    called.append("legacy");raise AssertionError("legacy refresh executed")
   mod.refresh=forbidden
  return mod
 monkeypatch.setattr(a.fmod,"load",loaded)
 box.amend(lambda s:training(s,"201",17))
 # Preserve arbitrary opaque controller metadata and historical failed records.
 box.amend(lambda s:s["autonomous_training_v1"].update(
  blocked_pairs={"failed_pair":{"history_sha256":"e"*64,"must_stay":"yes"}},
  verified_pairs={"keep":{"completed_by_arm":{"A":5000,"B":735}}},
  opaque_future_controller_field={"must_not_replace":[1,2,3]}))
 before=copy.deepcopy(state(box))
 out=box.run();after=state(box)
 assert out["submitted"] is True and called==[]
 assert after["registered_jobs"][:-1]==before["registered_jobs"]
 expected=copy.deepcopy(before["autonomous_training_v1"])
 expected["reserved_GPU_slots"]=0
 expected["reservation_consumed_by_job"]=after["autonomous_training_v1"]["reservation_consumed_by_job"]
 assert after["autonomous_training_v1"]==expected
 assert after["current_round_cost"]["registered_jobs"]==sum(j["experiment"]=="formal_main_v2" for j in after["registered_jobs"])
 assert after["current_round_cost"]["allocated_gpu_seconds"]==12345
 assert len(box.commands)==1 and "--exclude=gpu4020" in box.commands[0][-1]
 assert a.fmod.COORDINATOR not in json.loads((box.root/a.orig.c.INVOCATION).read_bytes())["active_request_job_ids_before"]
 assert len(box.fac.observation["capacity"]["occupied"])==7
 asked=box.seen[0][box.seen[0].index("-j")+1].split(",")
 assert asked==[j["job_id"] for j in before["registered_jobs"]]
 assert a.fmod.COORDINATOR in asked and "100" in asked and "102" in asked
 assert after["pending_submission"] is None
 assert box.fac.phase=="committed"

def test_eight_mixed_GPU_modes_and_confirmed_CPU_do_not_submit(box):
 box.amend(lambda s:training(s,"201",17))
 for jid,mode in [("202","development"),("203","profiling"),("204","engineering")]:
  box.amend(lambda s,jid=jid,mode=mode:next(j for j in s["registered_jobs"] if j["job_id"]==jid).update(mode=mode))
 extra=dict(job_id="208",experiment="formal_main_v2",mode="final",stage_key="extra_final",status="PENDING",gpus=1)
 box.amend(lambda s:s["registered_jobs"].append(extra))
 box.rows["208"]=["208","PENDING","0:0","0","cpu=0","None","cti",""]
 box.queued["208"]=["PENDING",""]
 before=box.sp.read_bytes();out=box.run()
 assert not out["submitted"] and len(out["active_request_job_ids"])==8
 assert box.sp.read_bytes()==before and not box.commands
 assert not (box.root/a.orig.c.INVOCATION).exists()

@pytest.mark.parametrize("change",["missing_historical","missing_CPU","CPU_unknown","CPU_queue_unknown","GPU_queue_unknown","CPU_actual_GPU"])
def test_all_registered_unknowns_fail_closed(box,change):
 if change=="missing_historical":box.rows.pop("100")
 elif change=="missing_CPU":box.rows.pop(a.fmod.COORDINATOR)
 elif change=="CPU_unknown":box.rows[a.fmod.COORDINATOR][1]="UNKNOWN"
 elif change=="CPU_queue_unknown":box.queued[a.fmod.COORDINATOR][0]="UNSUPPORTED"
 elif change=="GPU_queue_unknown":box.queued["201"][0]="UNSUPPORTED"
 elif change=="CPU_actual_GPU":box.rows[a.fmod.COORDINATOR][4]="cpu=1,gres/gpu=1"
 refuse_without_publication(box)

def test_same_pair_two_different_stage_keys_blocks(box):
 box.amend(lambda s:training(s,"201",17))
 box.amend(lambda s:training(s,"202",17))
 refuse_without_publication(box)
 assert any(x.startswith("duplicate_pair:") for x in box.fac.observation["capacity"]["findings"])

@pytest.mark.parametrize("fault",["ambiguous","bad_rc","sbatch_raise"])
def test_ack_failures_keep_exact_pending_and_prevent_second_submission(box,fault):
 box.fault=fault
 with pytest.raises((ValueError,OSError,RuntimeError)):box.run()
 after=state(box);pending=copy.deepcopy(after["pending_submission"])
 assert pending["status"]=="prepared_before_invocation_publication"
 assert after["registered_jobs"]==box.initial["registered_jobs"]
 assert after["autonomous_training_v1"]["reserved_GPU_slots"]==1
 assert len(box.commands)==1
 with pytest.raises(ValueError):box.run()
 assert len(box.commands)==1 and state(box)["pending_submission"]==pending

def test_known_ack_but_receipt_failure_preserves_identifier_and_reservation(box,monkeypatch):
 saved=a.fmod.exclusive_json
 def fail(path,value):
  if str(path).endswith("/submissions/900.json"):raise OSError("independent injected disk failure")
  return saved(path,value)
 monkeypatch.setattr(a.fmod,"exclusive_json",fail)
 with pytest.raises(OSError):box.run()
 after=state(box)
 assert after["pending_submission"]["known_job_id"]=="900"
 assert after["pending_submission"]["status"]=="submitted_identifier_observed"
 assert after["autonomous_training_v1"]["reserved_GPU_slots"]==1
 with pytest.raises(ValueError):box.run()
 assert len(box.commands)==1

def test_CAS_detects_foreign_state_and_never_overwrites(box):
 box.fault="cas"
 with pytest.raises(ValueError,match="state changed"):box.run()
 after=state(box)
 assert after["outside_writer"] is True
 assert after["pending_submission"]["status"]=="prepared_before_invocation_publication"
 assert after["registered_jobs"]==box.initial["registered_jobs"]

def test_shared_writer_conflict_blocks_before_scheduler_query(box):
 before=box.sp.read_bytes()
 with a.ctl.exclusive_lock(box.sp.parent/".writer.lock"):
  with pytest.raises(BlockingIOError):box.run()
 assert box.sp.read_bytes()==before and not box.commands and not box.seen

def test_state_whitelist_rejects_foreign_field_during_pending(box):
 fac,f=box.build();before=box.sp.read_bytes()
 with f.supervisor_lock():
  s=f.read(f.STATE);f.refresh(s)
  s["pending_submission"]=dict(stage_key=a.orig.c.STAGE,invocation=a.orig.c.INVOCATION,
   invocation_sha256="a"*64,status="prepared_before_invocation_publication",utc="synthetic-time")
  s["autonomous_training_v1"]["completed_pairs"]["forged_complete"]={"A":5000}
  with pytest.raises(ValueError,match="whitelist"):f.write(f.STATE,s)
 assert box.sp.read_bytes()==before and not box.commands

@pytest.mark.parametrize("restore_reservation",[False,True])
def test_success_reentry_is_not_a_second_attempt(box,restore_reservation):
 box.run()
 if restore_reservation:
  box.amend(lambda s:s["autonomous_training_v1"].update(reserved_GPU_slots=1))
 first=box.sp.read_bytes()
 # New audit directory, even with a synthetic restored reservation, cannot retry.
 fac,f=box.build()
 fac.audit=box.root/".local/second_independent_attempt"
 expected="already registered" if restore_reservation else "reservation missing"
 with pytest.raises(ValueError,match=expected):
  with a.node.exclude_future_sbatch(f,request={"kind":"action_execution_gpu_v3"},registration_ref=a.entry.NODE_REG,
   audit_relative=".local/second_independent_attempt/node.json"):
   a.orig.execute_submit(box.root,box.checked,a.entry.REFS,f)
 assert box.sp.read_bytes()==first and len(box.commands)==1


def test_missing_shared_lock_check_only_creates_nothing(box):
 lock=box.sp.parent/".writer.lock"
 lock.unlink()  # Only the independent synthetic fixture.
 fac,f=box.build(False)
 before={str(p.relative_to(box.root)):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in box.root.rglob("*") if p.is_file()}
 with pytest.raises(ValueError,match="writer lock"):
  with f.supervisor_lock():
   raise AssertionError("missing lock entered")
 after={str(p.relative_to(box.root)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in box.root.rglob("*") if p.is_file()}
 assert after==before and not lock.exists() and not fac.audit.exists()
