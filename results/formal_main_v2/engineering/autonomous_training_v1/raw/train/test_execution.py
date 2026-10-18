"""CPU execution-contract tests; raw scientific reviewer is an explicit upstream stand-in.

No model, actual checkpoint, sealed state, real registration or Slurm write.
The separate inherited-core tests execute the unchanged frozen training core.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("autonomous_train_tested", HERE / "execution.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(root, name, value):
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return p


def ref(root, name):
    return dict(path=name, sha256=m.sha(root / name))


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "synthetic_control"
    root.mkdir()
    monkeypatch.setattr(m, "CONTROL_ROOT", root)
    filemap = {}
    # The fixed count remains checked. These are synthetic bytes, not a fake
    # claim of a real GPU source snapshot.
    source_names = ["scripts/server/formal_main.slurm"] + [f"src/synthetic_{i:03d}.py" for i in range(172)]
    for name in source_names:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# synthetic frozen identity\n", encoding="utf-8")
        filemap[name] = m.sha(p)
    monkeypatch.setattr(m, "SOURCE_SHA", hashlib.sha256(json.dumps(filemap, sort_keys=True).encode()).hexdigest())
    write(root, m.INVENTORY, dict(files=filemap, source_root_server=m.SOURCE, source_sha256=m.SOURCE_SHA))
    monkeypatch.setattr(m, "INVENTORY_SHA", m.sha(root / m.INVENTORY))
    pins = {}
    for name in m.DEPENDENCY_PINS:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# synthetic upstream original reviewer stand-in\n", encoding="utf-8")
        pins[name] = m.sha(p)
    monkeypatch.setattr(m, "DEPENDENCY_PINS", pins)
    runtime_files = [
        "scripts/server/run_formal_asset_stage.py", "scripts/server/formal_asset_main.slurm",
        "scripts/ops/formal_asset_metadata_adapter.py", "configs/experiments/metadata_compat.json",
        "configs/assets/strict_object.json", "configs/assets/strict_goal.json"]
    component_files = [
        "scripts/server/run_formal_goal_asset_stage.py", "scripts/server/formal_goal_asset_main.slurm",
        "scripts/ops/formal_goal_component_adapter.py", "configs/experiments/component_compat.json"]
    for name in runtime_files + component_files:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{}\n" if p.suffix == ".json" else "# synthetic compatibility\n", encoding="utf-8")
    runtime = dict(schema=m.SCHEMA, files={n: m.sha(root/n) for n in runtime_files})
    component = dict(schema=m.SCHEMA, files={n: m.sha(root/n) for n in component_files})
    reg, jobs = dict(schema=m.SCHEMA, pairs=[], suites={}), []
    for i, suite in enumerate(("libero_10", "libero_spatial", "libero_object", "libero_goal")):
        protocol = f"configs/manifests/{m.SCHEMA}/{suite}/protocol.json"
        windows = f"configs/manifests/{m.SCHEMA}/{suite}/windows.json"
        asset = f"configs/assets/{suite}.json"
        for name in (protocol, windows, asset):
            write(root, name, dict(synthetic=True, suite=suite))
        reg["suites"][suite] = dict(protocol=protocol, windows=windows, model_manifest=asset,
            model_root_server=m.H+"/models/"+suite, data_root_server=m.H+"/data/"+suite,
            cache_root_server=m.H+"/data/formal_main_v2/"+suite)
        for budget in (256, 128, 64):
            for seed in (17, 23, 41):
                config = f"configs/experiments/{m.SCHEMA}/{suite}_k{budget}_seed{seed}.json"
                write(root, config, dict(schema=m.SCHEMA, synthetic=True, suite=suite, tokens_per_camera=budget//2,
                    seed=seed, updates=5000))
                reg["pairs"].append(dict(suite=suite, visual_tokens=budget, seed=seed, path=config,
                    sha256=m.sha(root/config), checkpoint_root_server=f"{m.H}/checkpoints/{m.SCHEMA}/{suite}/k{budget}/seed{seed}",
                    run_root_server=f"{m.P}/results/{m.SCHEMA}/{suite}/k{budget}/seed{seed}"))
        out = f"results/{m.SCHEMA}/{suite}/acceptance/attempt01"
        names = (*m.GATE_NAMES, "input_calls.jsonl", "operator_calls.jsonl", "f01_k64.json", "f01_k128.json", "f01_k256.json")
        for name in names:
            write(root, out+"/"+name, dict(synthetic=True, status="passed"))
        job = dict(job_id=str(100+i), experiment=m.SCHEMA, suite=suite, mode="acceptance", status="COMPLETED", exit_code="0:0")
        gate = dict(schema=m.SCHEMA, kind="root_acceptance_review", status="passed", suite=suite,
            source_sha256=m.SOURCE_SHA, job_id=job["job_id"], output_relative=out,
            files={n:m.sha(root/out/n) for n in names})
        if suite in ("libero_object", "libero_goal"):
            gate["runtime_compatibility"] = job["runtime_compatibility"] = copy.deepcopy(runtime)
            gate["runtime_compatibility_review"] = dict(status="verified", runtime_compatibility=runtime, evidence_sha256={})
        if suite == "libero_goal":
            gate["component_compatibility"] = job["component_compatibility"] = copy.deepcopy(component)
            gate["component_compatibility_review"] = dict(status="verified", component_compatibility=component, evidence_sha256={})
        write(root, f"results/{m.SCHEMA}/{suite}/acceptance/root_review.json", gate)
        jobs.append(job)
    write(root, m.REGISTRATION, reg)
    monkeypatch.setattr(m, "REGISTRATION_SHA", m.sha(root/m.REGISTRATION))
    write(root, m.AUTHORIZATION, dict(pair_target_updates_per_arm=5000, soft_wall_seconds=169200, allocation_time="48:00:00",
        final_release_unchanged=True, scientific_registration=ref(root,m.REGISTRATION), source_inventory=ref(root,m.INVENTORY)))
    monkeypatch.setattr(m, "AUTHORIZATION_SHA", m.sha(root/m.AUTHORIZATION))
    destination = root / ".local/adapter.py"
    destination.parent.mkdir()
    destination.write_bytes((HERE/"execution.py").read_bytes())
    return dict(root=root, reg=reg, jobs=jobs, adapter=ref(root,".local/adapter.py"))


def base(project, key="libero_10_k128_seed17", admission=None, jobs=None):
    root=project["root"]
    suite=m.PAIR_RE.fullmatch(key)[1]
    gate_path=f"results/{m.SCHEMA}/{suite}/acceptance/root_review.json"
    gate=json.loads((root/gate_path).read_bytes())
    admission=admission or dict(decision="ready", pair_key=key, mode="fresh",
        acceptance_review_ref=ref(root,gate_path), rebuilt_acceptance=copy.deepcopy(gate))
    return m.build_base_invocation(root, pair_key=key, source_inventory=ref(root,m.INVENTORY),
        jobs=project["jobs"] if jobs is None else jobs, admission=admission, registered_utc="2026-10-19T00:00:00Z")


@pytest.mark.parametrize("suite", ("libero_10","libero_spatial","libero_object","libero_goal"))
def test_fresh_targets5000_only_two_engineering_options_change(project,suite):
    key=suite+"_k128_seed17"
    original=base(project,key)
    result=m.build_execution(project["root"], original, adapter_ref=project["adapter"])
    a,b=original["invocation"],result["invocation"]
    changes=[i for i,(x,y) in enumerate(zip(a["argv"],b["argv"])) if x!=y]
    assert {a["argv"][i-1] for i in changes}=={"--stop-after-updates","--max-wall-seconds"}
    assert a["watched_files"]==b["watched_files"]
    assert result["sbatch_options"]==["--time=48:00:00"]
    assert b["segment_end"]==5000 and "--resume" not in b["argv"]
    assert b.get("runtime_compatibility")==a.get("runtime_compatibility")
    assert b.get("component_compatibility")==a.get("component_compatibility")
    assert not (project["root"]/result["invocation_relative"]).exists()
    assert m.verify_execution_contract(m.Evidence(project["root"]), b)==result["execution_contract"]


def terminal(project, *, completed=None, target=500, autonomous=False, previous=True, skip_a=False, skip_b=False):
    completed=completed or {"A":500,"B":500}
    root=project["root"]
    key="libero_10_k128_seed17"
    raw_base=base(project,key)
    if autonomous:
        raw_base["completed_before"]={"A":5000 if skip_a else 500,"B":500}
        auto=m.build_execution(root,raw_base,adapter_ref=project["adapter"])
        inv=auto["invocation"]
        inv["argv"].append("--resume")
        # Appending resume is part of the original base provenance.
        c=inv["autonomous_execution"]; origin=copy.deepcopy(inv);del origin["autonomous_execution"]
        for f in c["changed_options"]:
            origin["argv"][origin["argv"].index(f)+1]=c["changed_options"][f]["before"]
        origin["segment_end"]=int(c["changed_options"]["--stop-after-updates"]["before"])
        c["base_invocation_sha256"]=m.signature(origin)
        target=5000
    else:
        inv=raw_base["invocation"]
        inv["segment_end"]=target
        inv["argv"][inv["argv"].index("--stop-after-updates")+1]=str(target)
        if previous:inv["argv"].append("--resume")
    job=dict(job_id="201",experiment=m.SCHEMA,mode="train",suite="libero_10",stage_key="libero_10_train_k128_seed17",
        visual_tokens=128,training_seed=17,source_root=m.SOURCE,source_sha256=m.SOURCE_SHA,gpus=1,
        submitted_utc="2026-10-19T01:00:00Z",elapsed_seconds=100, status="COMPLETED",exit_code="0:0",
        segment_end=target,run_root=raw_base["output"],invocation=raw_base["invocation_relative"])
    if autonomous:
        job.update(autonomous_execution=copy.deepcopy(inv["autonomous_execution"]),allocation_time=m.ALLOCATION_TIME,soft_wall_seconds=m.SOFT_WALL)
    write(root,job["invocation"],inv)
    job["invocation_sha256"]=m.sha(root/job["invocation"])
    history=[]
    if previous:
        old=copy.deepcopy(job);old.update(job_id="200",submitted_utc="2026-10-19T00:00:00Z",elapsed_seconds=90,segment_end=500)
        history.append(old)
    history.append(job)
    out=job["run_root"][len(m.P)+1:]
    arms,checks,files={},[],{}
    for arm in ("A","B"):
        n=completed[arm]
        digest=hashlib.sha256(("resume"+arm+str(n)).encode()).hexdigest()
        check=dict(arm=arm,path=raw_base["pair"]["checkpoint_root_server"]+"/"+arm+"/resume.pt",exists=True,sha256=digest,bytes=77)
        checks.append(check)
        report=dict(status="completed" if n==5000 else "checkpointed",arm=arm,training_updates_completed=n,
            next_sample_cursor=n*8,vla_parameters_unchanged=True,evaluations=[dict(update=i) for i in range(0,n+1,500)],
            stop_reason="engineering_wall_limit_after_complete_update" if autonomous and n<5000 else "registered_engineering_segment_boundary")
        rp=out+"/"+arm+("/training_report.json" if n==5000 else "/progress_report.json")
        write(root,rp,report);files[rp]=m.sha(root/rp);arms[arm]=report
        if (arm=="A" and skip_a) or (arm=="B" and skip_b):
            continue
        ep=out+"/"+arm+"/attempts/current/cost_events.jsonl"
        start=5000 if skip_a and arm=="A" else 500 if previous else 0
        rows=[dict(event="attempt_start",job_id=job["job_id"],completed_update=start,next_sample_cursor=start*8,resumed=previous),
              dict(event="checkpoint_commit",job_id=job["job_id"],completed_update=n,resume_sha256=digest),
              dict(event="attempt_end",job_id=job["job_id"],status=report["status"],completed_update=n)]
        p=root/ep;p.parent.mkdir(parents=True)
        p.write_text("".join(json.dumps(r)+"\n" for r in rows),encoding="utf-8");files[ep]=m.sha(p)
    done=completed=={"A":5000,"B":5000}
    result=dict(job_id=job["job_id"],pair_complete=done,status="completed" if done else "checkpointed",arms=arms)
    result_path=out+("/training_summary.json" if done else "/training_progress.json")
    write(root,result_path,result);files[result_path]=m.sha(root/result_path)
    receipt_path=f"results/{m.SCHEMA}/job_receipts/{job['job_id']}.json"
    write(root,receipt_path,dict(wall_seconds=169201 if skip_b else 100));files[receipt_path]=m.sha(root/receipt_path)
    review=dict(schema=m.SCHEMA,kind="root_segment_review",status="passed",job_id=job["job_id"],suite="libero_10",
        visual_tokens=128,seed=17,source_sha256=m.SOURCE_SHA,output_relative=out,invocation_sha256=job["invocation_sha256"],
        reviewer_sha256=m.sha(root/m.REVIEWER),registered_pair_jobs_at_review=history,
        pair_allocated_gpu_seconds=sum(j["elapsed_seconds"] for j in history),files=files,
        server_resume_checks=checks,server_resume_checklist=[dict(arm=c["arm"],path=c["path"],must_exist=True,sha256=c["sha256"]) for c in checks],
        completed_by_arm=completed,requested_segment_end=target,allowed_next_segment_end=None if done else target if autonomous else target+500,
        completed_training_receipts=[out+"/A/deployment_receipt.json",out+"/B/deployment_receipt.json"] if done else [],
        evidence_sha256={})
    rpath=out+"/segment_reviews/201.json";write(root,rpath,review)
    return dict(pair_key=key,job=job,review_ref=ref(root,rpath),rebuilt_review=copy.deepcopy(review),actual_resume_checks=copy.deepcopy(checks))


def classify(project,args):
    return m.classify_terminal(project["root"],**args)


def rewrite_review(project,args,change):
    p=project["root"]/args["review_ref"]["path"]
    review=json.loads(p.read_bytes());change(review)
    write(project["root"],args["review_ref"]["path"],review)
    args["review_ref"]=ref(project["root"],args["review_ref"]["path"])
    args["rebuilt_review"]=copy.deepcopy(review)


def test_legacy500_automatically_admits_original5000(project):
    args=terminal(project)
    admission=classify(project,args)
    assert admission["decision"]=="ready" and admission["next_target"]==5000
    plan=base(project,admission=admission,jobs=project["jobs"]+args["rebuilt_review"]["registered_pair_jobs_at_review"])
    final=m.build_execution(project["root"],plan,adapter_ref=project["adapter"])
    assert final["invocation"]["argv"][-1]=="--resume"
    assert final["completed_before"]=={"A":500,"B":500}
    assert final["server_resume_checks"]==args["actual_resume_checks"]


def test_softwall_asymmetric_a_complete_b735(project):
    args=terminal(project,completed={"A":5000,"B":735},autonomous=True,skip_a=True)
    value=classify(project,args)
    assert value["decision"]=="ready" and value["completed_by_arm"]=={"A":5000,"B":735}
    assert value["next_target"]==5000


def test_softwall_before_b_keeps_existing_b_checkpoint(project):
    args=terminal(project,completed={"A":5000,"B":500},autonomous=True,skip_b=True)
    assert classify(project,args)["decision"]=="ready"


def test_softwall_after_complete_non50_step(project):
    args=terminal(project,completed={"A":735,"B":500},autonomous=True,skip_b=True)
    assert classify(project,args)["completed_by_arm"]=={"A":735,"B":500}


def test_both5000_complete_never5500(project):
    args=terminal(project,completed={"A":5000,"B":5000},target=5000)
    value=classify(project,args)
    assert value["decision"]=="complete" and value["next_target"] is None


@pytest.mark.parametrize("status",["FAILED","TIMEOUT","PREEMPTED","NODE_FAIL","OUT_OF_MEMORY","RUNNING","STAGE_OUT","","COMPLETED+"])
def test_non_success_never_reads_review_or_retries(project,status):
    job=dict(status=status,exit_code="1:0",job_id="202")
    value=m.classify_terminal(project["root"],pair_key="libero_10_k128_seed17",job=job,
        review_ref=None,rebuilt_review=None,actual_resume_checks=None)
    assert value["decision"]=="blocked" and value["automatic_retry"] is False


@pytest.mark.parametrize("mutation",["missing_resume","changed_resume","wrong_cursor","missing_validation","bad_tail","failed_attempt","missing_commit","wrong_stop","changed_root","unrebuilt","omitted_cost","failed_history"])
def test_evidence_failure_is_not_auto_recovery(project,mutation):
    args=terminal(project,completed={"A":5000,"B":735},autonomous=True,skip_a=True)
    root=project["root"];review=args["rebuilt_review"];out=review["output_relative"]
    if mutation=="missing_resume":args["actual_resume_checks"][1]["exists"]=False
    elif mutation=="changed_resume":args["actual_resume_checks"][1]["sha256"]="f"*64
    elif mutation=="changed_root":args["review_ref"]["sha256"]="f"*64
    elif mutation=="unrebuilt":args["rebuilt_review"]["completed_by_arm"]["B"]=734
    elif mutation in ("omitted_cost","failed_history"):
        def change(r):
            if mutation=="omitted_cost":r["pair_allocated_gpu_seconds"]-=1
            else:r["registered_pair_jobs_at_review"][0]["status"]="FAILED"
        rewrite_review(project,args,change)
    else:
        ep=out+"/B/attempts/current/cost_events.jsonl"
        rp=out+"/B/progress_report.json"
        result_path=out+"/training_progress.json"
        if mutation in ("wrong_cursor","missing_validation","wrong_stop"):
            r=json.loads((root/rp).read_bytes())
            if mutation=="wrong_cursor":r["next_sample_cursor"]-=1
            elif mutation=="missing_validation":r["evaluations"].pop()
            else:r["stop_reason"]="registered_engineering_segment_boundary"
            write(root,rp,r)
            result=json.loads((root/result_path).read_bytes());result["arms"]["B"]=r
            write(root,result_path,result)
            rewrite_review(project,args,lambda z:z["files"].update({rp:m.sha(root/rp),result_path:m.sha(root/result_path)}))
        else:
            p=root/ep;rows=[json.loads(x) for x in p.read_text().splitlines()]
            if mutation=="failed_attempt":rows[-1]["status"]="failed"
            if mutation=="missing_commit":rows.pop(1)
            text="".join(json.dumps(r)+"\n" for r in rows)
            if mutation=="bad_tail":text=text[:-1]
            p.write_text(text,encoding="utf-8")
            rewrite_review(project,args,lambda z:z["files"].update({ep:m.sha(p)}))
    with pytest.raises(ValueError):
        classify(project,args)


@pytest.mark.parametrize("mutation",["wrong_base","scientific_arg","contract","adapter","duplicate_invocation","failed_job","source"])
def test_plan_rejects_source_or_submission_drift(project,mutation):
    root=project["root"]
    plan=base(project)
    if mutation=="duplicate_invocation":
        write(root,plan["invocation_relative"],{})
        with pytest.raises(ValueError):base(project)
        return
    if mutation=="failed_job":
        job=dict(experiment=m.SCHEMA,job_id="9",stage_key="libero_10_train_k128_seed17",mode="train",suite="libero_10",
            visual_tokens=128,training_seed=17,source_root=m.SOURCE,source_sha256=m.SOURCE_SHA,gpus=1,status="FAILED",
            submitted_utc="2026-10-19T00:00:00Z",exit_code="1:0")
        with pytest.raises(ValueError):base(project,jobs=project["jobs"]+[job])
        return
    if mutation=="source":
        (root/"src/synthetic_000.py").write_text("changed")
        with pytest.raises(ValueError):m.build_execution(root,plan,adapter_ref=project["adapter"])
        return
    execution=m.build_execution(root,plan,adapter_ref=project["adapter"])
    inv=execution["invocation"]
    if mutation=="wrong_base":inv["autonomous_execution"]["base_invocation_sha256"]="e"*64
    elif mutation=="scientific_arg":inv["argv"][inv["argv"].index("--arm")+1]="A"
    elif mutation=="contract":inv["autonomous_execution"]["validation_updates"]=[0,5000]
    elif mutation=="adapter":inv["autonomous_execution"]["adapter"]["sha256"]="c"*64
    with pytest.raises(ValueError):m.verify_execution_contract(m.Evidence(root),inv)


@pytest.mark.parametrize("name",["../x.json","/x.json","results/sealed/value.json","results/weights/a.pt","results/test/init.json","results/init_states_test.json","results/final_states.json"])
def test_forbidden_paths_rejected_before_read(project,name,monkeypatch):
    def fail(*a,**k):raise AssertionError("filesystem read attempted")
    monkeypatch.setattr(Path,"resolve",fail)
    with pytest.raises(ValueError):m.Evidence.path(object.__new__(m.Evidence),name)


def test_machine_envelope_does_not_claim_root_or_independent(project):
    args=terminal(project,completed={"A":5000,"B":735},autonomous=True,skip_a=True)
    original=copy.deepcopy(args["rebuilt_review"])
    checks=original.pop("server_resume_checks")
    original.pop("reviewer_sha256");original["status"]="local_passed_remote_required"
    document=dict(schema=m.SCHEMA,kind="automatic_machine_training_review",version="autonomous-training-machine-review-v1",
        status="passed_machine_reconstruction",original_review=original,
        reviewer=dict(path=m.REVIEWER,sha256=m.sha(project["root"]/m.REVIEWER)),
        server_resume_checks=checks,root_signature_claimed=False,independent_review=False)
    path=args["review_ref"]["path"]
    write(project["root"],path,document)
    args.update(review_ref=ref(project["root"],path),rebuilt_review=original)
    value=classify(project,args)
    assert value["decision"]=="ready"
    assert value["verification_origin"]=="automatic_machine_reconstruction"
    assert value["independent_review"] is False and value["root_signature_claimed"] is False


def test_machine_envelope_cannot_mislabel_an_independent_review(project):
    args=terminal(project)
    document=dict(schema=m.SCHEMA,kind="automatic_machine_training_review",version="autonomous-training-machine-review-v1",
        status="passed_machine_reconstruction",original_review=args["rebuilt_review"],
        reviewer=dict(path=m.REVIEWER,sha256=m.sha(project["root"]/m.REVIEWER)),
        server_resume_checks=args["actual_resume_checks"],root_signature_claimed=False,independent_review=True)
    path=args["review_ref"]["path"];write(project["root"],path,document)
    args["review_ref"]=ref(project["root"],path)
    with pytest.raises(ValueError):classify(project,args)
