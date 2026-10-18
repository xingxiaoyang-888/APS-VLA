"""Synthetic scheduler tests. No model, GPU, network or production-state access."""
import copy,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import controller as c
D=Path(__file__).resolve().parent
PAIRS=[dict(suite=s,visual_tokens=k,seed=seed,sha256="a"*64,run_root_server=str(c.P/f"results/formal_main_v2/{s}/k{k}/seed{seed}")) for s,k,seed in sorted(c.PAIR_KEYS)]
def job(i,p=None,status="RUNNING",gpus=1,mode="train"):
    p=p or PAIRS[i%36]
    return dict(job_id=str(100+i),experiment=c.ROUND,mode=mode,suite=p["suite"],visual_tokens=p["visual_tokens"],training_seed=p["seed"],status=status,gpus=gpus,stage_key=f"{p['suite']}_train_k{p['visual_tokens']}_seed{p['seed']}",segment_end=500,exit_code="0:0" if status!="FAILED" else "1:0",submitted_utc=f"2026-10-19T00:00:{i%60:02d}+00:00")
def observed(j,status=None):
    return dict(job_id=j["job_id"],status=status or j["status"],gpus=j["gpus"],exit_code=j["exit_code"],elapsed_seconds=17,allocation="gres/gpu="+str(j["gpus"]),node="synthetic",scheduler_name="cti-formal",scheduler_comment="")
def snap(jobs):return dict(rows={j["job_id"]:observed(j) for j in jobs},queue={},raw_sacct="synthetic",raw_squeue="")
def plan(p,history):
    key=c.pair_key(p);inv=f"results/formal_main_v2/invocations/{key}_auto1.json"
    wrapper=(c.S/"scripts/server/formal_main.slurm" if p["suite"] in ("libero_10","libero_spatial") else c.P/("scripts/server/formal_goal_asset_main.slurm" if p["suite"]=="libero_goal" else "scripts/server/formal_asset_main.slurm"))
    return dict(pair_key=key,source_root=str(c.S),source_sha256=c.SOURCE_SHA,config_sha256=p["sha256"],target_updates=5000,soft_wall_seconds=169200,wall_time="48:00:00",gpus=1,resume=bool(history),run_root=p["run_root_server"]+"/training",wrapper=str(wrapper),invocation=inv,invocation_sha256="b"*64,exports=dict(SOURCE_ROOT=str(c.S),INVOCATION=str(c.P/inv)),scientific_verification=dict(status="passed_full_verification"),evidence_refs=[dict(path="synthetic.json",sha256="c"*64)],job_record={},autonomous_execution={"synthetic":True},stage_key=f"{p['suite']}_train_k{p['visual_tokens']}_seed{p['seed']}")
class Backend:
    def __init__(self,ready=None):
        self.ready=ready or c.pair_key(PAIRS[0]);self.calls=[];self.checks=[];self.complete=False;self.bad=False;self.allcomplete=False
    def inspect_and_prepare(self,p,h,state):
        self.calls.append(c.pair_key(p))
        if self.allcomplete or (self.complete and c.pair_key(p)==self.ready):
            return dict(decision="complete",completed_by_arm=dict(A=5000,B=5000),validation_updates=list(range(0,5001,500)),selected_checkpoints_verified=not self.bad,evidence_refs=[dict(path="synthetic.json",sha256="c"*64)])
        if c.pair_key(p)!=self.ready:return dict(decision="blocked",reason="unselected synthetic fixture")
        return dict(decision="ready",completed_by_arm=dict(A=500 if h else 0,B=500 if h else 0),evidence_refs=[dict(path="synthetic.json",sha256="c"*64)],plan=plan(p,h))
    def verify_evidence(self,refs):
        self.checks.append(refs)
        if self.bad and not self.complete:raise ValueError("synthetic SHA mismatch")
    def verify_prepared_plan(self,p):pass
class Scheduler:
    def __init__(self):
        self.calls=[];self.response=SimpleNamespace(returncode=0,stdout="999;cluster\n",stderr="")
        self.mutate=None;self.before_submit=None;self.error=None
    def observe(self,jobs):
        s=snap(jobs)
        if self.mutate:self.mutate(s)
        return s
    def submit(self,argv):
        self.calls.append(argv)
        if self.before_submit:self.before_submit(argv)
        if self.error:raise self.error
        return self.response
class ControllerTests(unittest.TestCase):
    def setUp(self):
        (D/"synthetic").mkdir(exist_ok=True)
        self.tmp=Path(tempfile.mkdtemp(prefix=self._testMethodName+"_",dir=D/"synthetic"))
        self.root=self.tmp/"project";self.work=self.tmp/"service"
        self.state=self.root/"results/experiment_supervisor/state.json"
        self.b=Backend();self.s=Scheduler();self.write([])
    def write(self,jobs,pending=None):
        c.atomic_json(self.state,dict(registered_jobs=jobs,pending_submission=pending))
    def make(self):return c.Controller(self.root,self.work,PAIRS,self.b,self.s,"d"*64,"8888")
    def tick(self):
        x=self.make()
        with x.leadership():return x.tick()
    def test_exact_eight_all_modes_stop(self):
        jobs=[job(i,mode=["train","engineering","development"][i%3]) for i in range(8)]
        self.write(jobs);self.assertEqual(self.tick()["status"],"capacity_full");self.assertFalse(self.s.calls)
    def test_unknown_occupies_and_blocks_even_below_eight(self):
        self.write([job(1,status="FUTURE_SLURM_STATE")]);r=self.tick()
        self.assertEqual(r["status"],"scheduler_uncertain");self.assertIn("101",r["occupied"]);self.assertFalse(self.s.calls)
    def test_missing_sacct_blocks(self):
        self.write([job(1)]);self.s.mutate=lambda s:s["rows"].clear()
        self.assertEqual(self.tick()["status"],"scheduler_uncertain");self.assertFalse(self.s.calls)
    def test_duplicate_pair_live_blocks(self):
        self.write([job(1,PAIRS[2]),job(2,PAIRS[2],status="SUBMITTED")])
        self.assertIn("duplicate_pair:"+c.pair_key(PAIRS[2]),self.tick()["findings"])
    def test_confirmed_zero_gpu_cpu_does_not_take_slot(self):
        jobs=[job(i,PAIRS[i+1]) for i in range(7)]+[job(50,gpus=0,mode="engineering")]
        self.write(jobs);self.assertEqual(self.tick()["status"],"submitted")
    def test_missing_zero_gpu_is_uncertain(self):
        j=job(50,gpus=0,mode="engineering");self.write([j]);self.s.mutate=lambda s:s["rows"].clear()
        self.assertEqual(self.tick()["status"],"scheduler_uncertain")
    def test_pending_is_fsynced_before_actual_call(self):
        def verify(argv):
            v=c.read_json(self.state);self.assertEqual(v["pending_submission"]["actual_sbatch_argv"],argv)
            self.assertEqual(v["registered_jobs"],[]);self.assertIs(v["pending_submission"]["retry_permitted"],False)
        self.s.before_submit=verify
        r=self.tick();self.assertEqual(r["status"],"submitted")
        v=c.read_json(self.state);self.assertIsNone(v["pending_submission"])
        self.assertEqual(v["registered_jobs"][0]["job_id"],"999")
        self.assertEqual(v["registered_jobs"][0]["name"],"cti-formal")
        self.assertEqual(v["formal_main_progress"]["parallel_execution"]["registered_requested_active_GPU_jobs"],1)
    def test_timeout_never_resubmits_after_process_restart(self):
        self.s.error=subprocess.TimeoutExpired(["sbatch"],60)
        self.assertEqual(self.tick()["status"],"unresolved_submission")
        self.s.error=None;self.assertEqual(self.tick()["status"],"unresolved_submission")
        self.assertEqual(len(self.s.calls),1);self.assertTrue(c.read_json(self.state)["pending_submission"])
    def test_nonzero_numeric_response_is_unresolved(self):
        self.s.response=SimpleNamespace(returncode=1,stdout="999\n",stderr="uncertain")
        self.assertEqual(self.tick()["status"],"unresolved_submission");self.tick();self.assertEqual(len(self.s.calls),1)
    def test_multiple_ack_lines_are_not_accepted(self):
        self.s.response=SimpleNamespace(returncode=0,stdout="999\n1000\n",stderr="")
        self.assertEqual(self.tick()["status"],"unresolved_submission");self.assertFalse(c.read_json(self.state)["registered_jobs"])
    def test_crash_after_ack_before_registry_keeps_pending(self):
        x=self.make();original=x._save
        def fail_ack(state,before):
            if state["registered_jobs"] and state["registered_jobs"][-1]["job_id"]=="999":raise OSError("injected disk full after sbatch")
            return original(state,before)
        x._save=fail_ack
        with x.leadership(),self.assertRaises(OSError):x.tick()
        self.assertTrue(c.read_json(self.state)["pending_submission"])
        self.assertEqual(self.tick()["status"],"unresolved_submission");self.assertEqual(len(self.s.calls),1)
    def test_crash_before_pending_no_submission(self):
        x=self.make();original=x._save
        def fail_pending(state,before):
            if state.get("pending_submission"):raise OSError("injected intent write failure")
            original(state,before)
        x._save=fail_pending
        with x.leadership(),self.assertRaises(OSError):x.tick()
        self.assertFalse(self.s.calls);self.assertIsNone(c.read_json(self.state)["pending_submission"])
    def test_journal_failure_after_durable_intent_preserves_hold(self):
        x=self.make();original=x.event
        def fail_event(kind,**data):
            if kind=="submission_intent_durable":raise OSError("injected journal full")
            original(kind,**data)
        x.event=fail_event
        with x.leadership(),self.assertRaises(OSError):x.tick()
        self.assertTrue(c.read_json(self.state)["pending_submission"]);self.assertFalse(self.s.calls)
    def test_existing_pending_never_calls_backend(self):
        self.write([],dict(invocation="prior",state="unknown"));self.tick()
        self.assertFalse(self.b.calls);self.assertFalse(self.s.calls)
    def test_sacct_queue_disagreement_no_free_slot(self):
        self.write([job(1,status="COMPLETED")]);self.s.mutate=lambda s:s["queue"].update({"101":dict(status="RUNNING",comment="")})
        self.assertEqual(self.tick()["status"],"scheduler_uncertain")
    def test_terminal_drift_is_not_written_over_old_terminal(self):
        self.write([job(1,status="COMPLETED")]);self.s.mutate=lambda s:s["rows"]["101"].update(status="FAILED",exit_code="1:0")
        self.assertEqual(self.tick()["status"],"scheduler_uncertain")
        self.assertEqual(c.read_json(self.state)["registered_jobs"][0]["status"],"COMPLETED")
        self.assertEqual(self.tick()["status"],"scheduler_uncertain")
    def test_failed_pair_without_exact_repair_cannot_submit(self):
        self.write([job(1,PAIRS[0],status="FAILED")]);self.assertEqual(self.tick()["status"],"waiting_or_blocked")
        self.assertFalse(self.s.calls)
    def test_scientific_sha_gate_precedes_intent(self):
        self.b.bad=True;self.tick();self.assertFalse(self.s.calls);self.assertIsNone(c.read_json(self.state)["pending_submission"])
    def test_complete_requires_selected_identity(self):
        self.b.complete=True;self.b.bad=True;self.tick()
        self.assertEqual(c.read_json(self.state)["formal_main_progress"]["trained_arms"],0)
    def test_full_matrix_ends_at72_no_extra_submission(self):
        self.b.allcomplete=True;self.assertEqual(self.tick()["status"],"training_matrix_complete")
        self.assertEqual(c.read_json(self.state)["formal_main_progress"]["trained_arms"],72);self.assertFalse(self.s.calls)
    def test_cached_complete_evidence_still_checked(self):
        self.b.allcomplete=True;self.tick();n=len(self.b.checks);self.tick()
        self.assertEqual(len(self.b.checks)-n,36)
    def test_active_pair_keeps_original_entrypoint(self):
        self.write([job(0)]);self.tick();self.assertNotIn(c.pair_key(PAIRS[0]),self.b.calls);self.assertFalse(self.s.calls)
    def test_explicit48h_exclusion_and_comment_only_token(self):
        self.tick();argv=self.s.calls[0]
        for v in ("--time=48:00:00","--no-requeue","--exclude=gpu4020","--gres=gpu:l40:1","--job-name=cti-formal"):self.assertIn(v,argv)
        self.assertEqual(sum(x.startswith("--comment=cti-auto-v1:") for x in argv),1)
        self.assertTrue(argv[-1].endswith("/scripts/server/formal_main.slurm"))
    def test_real_cross_process_lease_rejects_second_owner(self):
        x=self.make()
        code="import fcntl,sys; f=open(sys.argv[1],'a+b'); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)"
        with x.leadership():
            r=subprocess.run([sys.executable,"-B","-c",code,str(x.lease_path)],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0);self.assertIn("BlockingIOError",r.stderr)
        r=subprocess.run([sys.executable,"-B","-c",code,str(x.lease_path)],capture_output=True,text=True)
        self.assertEqual(r.returncode,0)
    def test_real_writer_contention_changes_no_state(self):
        x=self.make();before=c.file_sha(self.state)
        with x.leadership(),c.exclusive_lock(x.writer_path),self.assertRaises(BlockingIOError):x.tick()
        self.assertEqual(before,c.file_sha(self.state));self.assertFalse(self.s.calls)
    def test_CAS_rejects_unlocked_writer(self):
        before=c.file_sha(self.state);c.atomic_json(self.state,dict(registered_jobs=[],pending_submission="changed"))
        with self.assertRaisesRegex(ValueError,"outside writer"):c.atomic_json(self.state,{},before)
    def test_plan_identity_and_budget_reject(self):
        p=plan(PAIRS[0],[]);p["config_sha256"]="f"*64
        with self.assertRaises(ValueError):c.validate_plan(p,PAIRS[0],[])
        p=plan(PAIRS[0],[]);p["target_updates"]=5500
        with self.assertRaises(ValueError):c.validate_plan(p,PAIRS[0],[])
    def test_accounting_uses_unique_allocations_only(self):
        self.write([job(1,PAIRS[1],status="COMPLETED"),job(2,PAIRS[2],status="FAILED")])
        self.b.ready="none";self.tick()
        self.assertEqual(c.read_json(self.state)["current_round_cost"]["allocated_gpu_seconds"],34)
    def test_parser_rejects_duplicate_foreign_malformed_rows(self):
        good="10|RUNNING|0:0|7|gres/gpu=1|n|cti-formal|token|\n"
        self.assertEqual(c.parse_sacct(good,{"10"})["10"]["gpus"],1)
        for raw,ids in ((good+good,{"10"}),(good,{"11"}),("10|RUNNING|0:0|bad|x|n|j|c|\n",{"10"})):
            with self.subTest(raw=raw,ids=ids),self.assertRaises(ValueError):c.parse_sacct(raw,ids)
    def test_lexical_evidence_guard_precedes_open(self):
        with patch.object(c,"file_sha",side_effect=AssertionError("must not read")):
            for p in ("configs/manifests/x/initial_states/test.json","../state.json","weights/a.pt"):
                with self.subTest(p=p),self.assertRaises(ValueError):c.reference(self.root,dict(path=p,sha256="a"*64))
if __name__=="__main__":unittest.main()
