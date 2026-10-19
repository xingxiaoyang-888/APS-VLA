import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

R=Path("/share/home/u15016/XXY_CVPR/CTI-VLA/control_repo")
SOURCE=R/"scripts/ops/formal_autonomous_training_v1/controller.py"
PIN="acf2f41826dbae34ece3ce73e56eb3b2779ff96d45b64cc7fdbd4d92da848363"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==PIN
spec=importlib.util.spec_from_file_location("independent_live_controller_pending",SOURCE)
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)

class NoBackend:
    def inspect_and_prepare(self,*args,**kwargs):
        raise AssertionError("pending must not reach backend")
    def verify_evidence(self,*args,**kwargs):
        raise AssertionError("pending must not review/dispatch another pair")

class Scheduler:
    def __init__(self,jobs): self.jobs=copy.deepcopy(jobs);self.calls=[]
    def observe(self,jobs):
        assert jobs==self.jobs
        self.calls.append("observe")
        rows={}
        for j in jobs:
            rows[j["job_id"]]={"job_id":j["job_id"],"status":j["status"],"exit_code":j["exit_code"],"elapsed_seconds":j["elapsed_seconds"],"gpus":j["gpus"],"allocation":"gres/gpu:l40=1" if j["gpus"] else "cpu=1","node":"synthetic","scheduler_name":"cti-formal","scheduler_comment":""}
        return {"rows":rows,"queue":{},"raw_sacct":"synthetic CPU stand-in; no scheduler called","raw_squeue":""}
    def submit(self,argv):
        raise AssertionError("pending must never submit")

@pytest.mark.parametrize("phase",["before_publication","submission_outcome_unknown","acknowledged_but_final_CAS_failed"])
def test_actual_controller_preserves_foreign_pending_and_reservation(tmp_path,phase):
    root=tmp_path/"project"; d=root/"results/experiment_supervisor";d.mkdir(parents=True)
    key="libero_object_k256_seed23"
    def job(jid,status,exitcode,seconds):
        return {"job_id":jid,"experiment":"formal_main_v2","mode":"train","suite":"libero_object","visual_tokens":256,"training_seed":23,"segment_end":500,"gpus":1,"status":status,"exit_code":exitcode,"elapsed_seconds":seconds}
    jobs=[job("3028460","FAILED","1:0",84),job("3039258","COMPLETED","0:0",6512)]
    pending={"kind":"cuda_continuous_single_attempt","version":"independent_pending_interoperation_fixture","state":phase,"pair_key":key,"request_token":"a"*64,"requested_gpus":1,"retry_permitted":False,"actual_sbatch_argv":["sbatch","--comment=not_executed"]}
    if phase.startswith("acknowledged"):pending["acknowledged_job_id"]="9999999"
    blocked={key:{"reason":"retained FAILED history","history_sha256":"b"*64}}
    reservation={"path":"results/formal_main_v2/execution/action_spatial_resume_0943/reservation_root_record.json","sha256":"c"*64}
    state={"registered_jobs":jobs,"pending_submission":pending,"autonomous_training_v1":{"blocked_pairs":blocked,"reserved_GPU_slots":1,"reservation_root_record":reservation},"formal_main_progress":{}}
    (d/"state.json").write_text(json.dumps(state))
    pairs=[{"suite":suite,"visual_tokens":budget,"seed":seed,"sha256":"d"*64} for suite in ("libero_10","libero_spatial","libero_object","libero_goal") for budget in (256,128,64) for seed in (17,23,41)]
    slurm=Scheduler(jobs)
    ctl=c.Controller(root,root/"audit_work",pairs,NoBackend(),slurm,"e"*64)
    ctl._lease=True
    result=ctl.tick()
    after=json.loads((d/"state.json").read_text())
    assert result["status"]=="unresolved_submission"
    assert after["pending_submission"]==pending
    assert after["autonomous_training_v1"]["blocked_pairs"]==blocked
    assert after["autonomous_training_v1"]["reserved_GPU_slots"]==1
    assert after["autonomous_training_v1"]["reservation_root_record"]==reservation
    assert [(j["job_id"],j["status"],j["exit_code"],j["elapsed_seconds"]) for j in after["registered_jobs"]]==[("3028460","FAILED","1:0",84),("3039258","COMPLETED","0:0",6512)]
    assert after["autonomous_training_v1"]["allocated_gpu_seconds_observed"]==6596
    assert slurm.calls==["observe"]
