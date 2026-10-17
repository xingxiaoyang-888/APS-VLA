"""Synthetic provenance only; never a claim of GPU/scientific completion.

Source fixtures use actual immutable helper parsers and complete nonweight
receipt schemas. The original scientific gates remain the caller's separate
responsibility. Actual downstream writer integration is added below.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
from types import SimpleNamespace

import pytest

from cti_vla.evaluation import formal_runtime as runtime, formal_trials as trials
from cti_vla.evaluation.teacher_diagnostics import json_signature


ROOT=Path(__file__).resolve().parents[1]
HELPER="scripts/ops/formal_asset_downstream_review.py"


def load(relative,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True,indent=2)+"\n",encoding="utf-8",newline="\n")
    return path


def read(path):return json.loads(Path(path).read_text("utf-8"))


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    goal=load("tests/test_formal_goal_component_review.py","downstream_goal_source_fixture")
    generator=goal.project.__wrapped__(tmp_path_factory);base=next(generator)
    module=load(HELPER,"downstream_review_test")
    for name in (HELPER,module.SHARED):
        target=base.root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    before={n:sha(ROOT/n) for n in [*base.inventory["files"],module.METADATA_HELPER,module.COMPONENT_HELPER]}
    yield SimpleNamespace(**base.__dict__,goal=goal,d=module)
    assert before=={n:sha(ROOT/n) for n in before}
    with pytest.raises(StopIteration):next(generator)


def source_case(project,suite,stage):
    c=(project.goal.make_case(project,stage) if suite=="libero_goal" else project.old.make_case(project,suite,stage))
    c.job.update(gpus=1,elapsed_seconds=100,segment_end=None if stage=="acceptance" else 5000,
        training_seed=None if stage=="acceptance" else 17,visual_tokens=None if stage=="acceptance" else 128)
    return c


def pull_add(c,paths,jobs=None):
    pull=read(c.pull);jobs=jobs or [c.job]
    old={r["relative"]:{k:v for k,v in r.items() if k!="action"} for r in pull["files"]}
    for path in paths:
        path=Path(path);name=path.relative_to(c.root).as_posix()
        old[name]=dict(relative=name,path=str(c.m.P/name),sha256=sha(path),bytes=path.stat().st_size,
            job_ids=[j["job_id"] for j in jobs])
    entries=list(old.values())
    for name in ("inventory_before.json","inventory_after.json"):save(c.pull.parent/name,dict(files=entries))
    pull.update(inventory_sha256=sha(c.pull.parent/"inventory_before.json"),files=[dict(row,action="downloaded_verified") for row in entries],
        selected_jobs=[dict(j,include_run_root=True) for j in jobs],
        accounting_before=dict(jobs={j["job_id"]:{k:j[k] for k in ("status","exit_code","elapsed_seconds")} for j in jobs}),
        accounting_after=dict(jobs={j["job_id"]:{k:j[k] for k in ("status","exit_code","elapsed_seconds")} for j in jobs}))
    save(c.pull,pull)


def compatibility_review(c):
    e=c.shared.Evidence(c.root)
    meta=c.shared.review_runtime_compatibility(e,job=c.job,invocation=c.invocation,receipt=c.receipt,inventory=c.inventory,pull_receipt=c.pull)
    goal=c.shared.review_component_compatibility(e,job=c.job,invocation=c.invocation,receipt=c.receipt,inventory=c.inventory,
        metadata_review=meta,pull_receipt=c.pull)
    return meta,goal


def acceptance(project,suite):
    c=source_case(project,suite if suite in project.d.SUITES else "libero_object","acceptance");d=project.d
    if suite not in d.SUITES:
        c.relative=c.relative.replace("libero_object",suite)
        c.job.update(suite=suite,stage_key=suite+"_acceptance",run_root=str(d.P/c.relative))
        c.job.pop("runtime_compatibility")
        c.invocation.update(suite=suite,stage_key=c.job["stage_key"])
        c.invocation.pop("runtime_compatibility")
        save(c.root/c.job["invocation"],c.invocation);c.job["invocation_sha256"]=sha(c.root/c.job["invocation"])
    names=("input_acceptance.json","input_calls.jsonl","operator_calls.jsonl","resume_acceptance.json","f03_calls.jsonl",
        "acceptance_complete.json","f01_k128.json","f01_k256.json","f01_k64.json")
    sources={n:h for n,h in c.inventory["files"].items() if n.startswith("src/") and n.endswith(".py")}
    sources.update({"scripts/"+n:c.inventory["files"]["scripts/"+n] for n in
        ("run_formal_future.py","verify_formal_acceptance.py","eval_formal_selector_libero.py","verify_long_inputs.py")})
    paths=[]
    for name in names:
        p=c.root/c.relative/name
        save(p,dict(synthetic_provenance_only=True,status="passed",source_files=sources,frozen_model_sha256="b"*64))
        paths.append(p)
    pull_add(c,paths)
    meta,component=compatibility_review(c) if suite in d.SUITES else (None,None)
    files={p.relative_to(c.root/c.relative).as_posix():sha(p) for p in paths}
    for proof in (meta,component):
        if proof:
            for name in proof["required_pulled_files"]:
                files[Path(name).relative_to(c.relative).as_posix()]=sha(c.root/name)
    saved=dict(schema=d.SCHEMA,kind="root_acceptance_review",status="passed",suite=suite,job_id=c.job["job_id"],
        source_sha256=d.SOURCE_SHA256,source_files=sources,output_relative=c.relative,job_at_review=deepcopy(c.job),
        invocation_sha256=c.job["invocation_sha256"],files=files,
        evidence_sha256={c.pull.relative_to(c.root).as_posix():sha(c.pull)})
    if meta:saved.update(runtime_compatibility=c.runtime,runtime_compatibility_review=meta)
    if component:saved.update(component_compatibility=c.component,component_compatibility_review=component)
    rootreview=c.root/f"results/{d.SCHEMA}/{suite}/acceptance/root_review.json"
    save(rootreview,saved)
    registration=read(c.root/d.FORMAL_REGISTRATION)
    identity=trials.baseline_instance_identity(suite=suite,method="dense",visual_tokens=512,
        model_revision=registration["suites"][suite]["model_revision"],frozen_model_sha256="b"*64,source_files=sources,
        input_acceptance_sha256=sha(c.root/c.relative/"input_acceptance.json"))
    c.sources=sources;c.registration=registration;c.saved=saved;c.rootreview=rootreview;c.method_rows=[dict(identity=identity)]
    return c


def provenance(project,c,*,jobs=None,rows=None):
    return project.d.review_source_provenance(c.shared.Evidence(c.root),registration=c.registration,suite=c.job["suite"],
        inventory=c.inventory,method_rows=rows or c.method_rows,jobs=jobs or [c.job])


@pytest.mark.parametrize("suite",["libero_object","libero_goal"])
def test_accepted_baseline_provenance_rebuilds_both_original_helpers(project,suite):
    c=acceptance(project,suite)
    result=provenance(project,c)
    assert result["status"]=="verified" and set(result["method_bindings"])=={"dense"}
    assert ("component_implementation" in result)==(suite=="libero_goal")
    assert "results/experiment_supervisor/state.json" not in result["evidence_sha256"]
    assert all(sha(c.root/n)==h for n,h in result["evidence_sha256"].items())


@pytest.mark.parametrize("suite",["libero_10","libero_spatial"])
def test_legacy_source_is_audited_and_rejects_compatibility_fields(project,suite):
    c=acceptance(project,suite)
    result=provenance(project,c)
    assert result["status"]=="verified" and "metadata_implementation" not in result and "component_implementation" not in result
    c.job["runtime_compatibility"]={}
    c.saved["job_at_review"]=deepcopy(c.job);save(c.rootreview,c.saved)
    with pytest.raises(ValueError,match="legacy suite"):
        provenance(project,c)


@pytest.mark.parametrize("change",["missing_runtime","missing_goal","job_missing_goal","wrong_snapshot","missing_science_file","wrong_model","mutable_file","changed_helper"])
def test_source_provenance_fail_closed(project,change):
    c=acceptance(project,"libero_goal")
    original=None;target=None
    if change=="missing_runtime":c.saved.pop("runtime_compatibility_review")
    elif change=="missing_goal":c.saved.pop("component_compatibility_review")
    elif change=="job_missing_goal":c.job.pop("component_compatibility")
    elif change=="wrong_snapshot":c.saved["job_at_review"]["invocation_sha256"]="a"*64
    elif change=="missing_science_file":c.saved["files"].pop("resume_acceptance.json")
    elif change=="wrong_model":c.method_rows[0]["identity"]["model_revision"]="other"
    elif change=="mutable_file":
        with pytest.raises(ValueError,match="mutable supervisor"):
            project.d.immutable_file_map(c.shared.Evidence(c.root),{"results/experiment_supervisor/state.json":"a"*64})
        return
    elif change=="changed_helper":
        target=c.root/project.d.METADATA_HELPER;original=target.read_bytes();target.write_bytes(original+b"\n# changed\n")
    save(c.rootreview,c.saved)
    try:
        with pytest.raises(ValueError):provenance(project,c)
    finally:
        if target is not None:target.write_bytes(original)


def completed_pair(project,suite):
    accepted=acceptance(project,suite);d=project.d
    prior=source_case(project,suite,"train");last=source_case(project,suite,"train")
    prior.job["segment_end"]=2500
    base=last.relative
    pair=next(p for p in accepted.registration["pairs"] if (p["suite"],p["visual_tokens"],p["seed"])==(suite,128,17))
    config=read(accepted.root/pair["path"])
    files=[save(accepted.root/base/"registered_config.json",config)]
    arms={};rows=[]
    for arm in ("A","B"):
        metadata=runtime.make_formal_checkpoint_metadata(arm=arm,seed=17,scorer_dimensions=config["scorer_dimensions"],
            training_config={**config,"arm":arm},pair_config=config,window_manifest_sha256="e"*64,model_revision=config["model_revision"],
            stats_key=config["stats_key"],training_source_files=accepted.sources,update=500,validation_metric=.1,
            input_acceptance_sha256=accepted.method_rows[0]["identity"]["input_acceptance_sha256"],frozen_model_sha256="b"*64,
            data_protocol_sha256="f"*64,selection_protocol_sha256=json_signature(config["selection"]),training_complete=True)
        evaluations=[dict(update=u,validation_metric=.2 if u==0 else .1) for u in runtime.FORMAL_EVALUATION_UPDATES]
        receipt=dict(schema=d.SCHEMA,kind="deployment_receipt",metadata=metadata,metadata_sha256=json_signature(metadata),
            checkpoint_sha256=("a" if arm=="A" else "c")*64,training_config={**config,"arm":arm},pair_config=config,
            f01_report_sha256=sha(accepted.root/accepted.relative/"f01_k128.json"),planned_updates=5000,completed_updates=5000,
            evaluations=evaluations,training_complete=True,base_frozen=True,checkpoint_unchanged=True)
        runtime.validate_formal_receipt(receipt,metadata)
        identity=trials.selector_instance_identity({**metadata,"selector_checkpoint_sha256":receipt["checkpoint_sha256"],
            "deployment_receipt_sha256":json_signature(receipt),"f01_report_sha256":receipt["f01_report_sha256"]})
        checkpoint=str(PurePosixPath(pair["checkpoint_root_server"])/arm/"best.pt")
        report=dict(status="completed",training_updates_completed=5000,next_sample_cursor=40000,committed_samples=40000,
            best_checkpoint_sha256=identity["checkpoint_sha256"],evaluations=evaluations,vla_parameters_unchanged=True,best_checkpoint=checkpoint)
        arms[arm]=report
        receiptpath=base+"/"+arm+"/deployment_receipt.json"
        files.extend([save(accepted.root/receiptpath,receipt),save(accepted.root/base/arm/"training_report.json",report)])
        rows.append(dict(identity=identity,receipt=receiptpath,pair_config=pair["path"],checkpoint=checkpoint,
            f01_report=accepted.relative+"/f01_k128.json"))
    summary=dict(schema=d.SCHEMA,status="completed",pair_complete=True,planned_updates_per_arm=5000,checkpoint_unchanged=True,
        test_opened=False,job_id=last.job["job_id"],arms=arms)
    files.append(save(accepted.root/base/"training_summary.json",summary))
    for c in (prior,last):
        proofnames=[*c.m.ARTIFACT_NAMES]
        files.extend(c.copied/name for name in proofnames)
        files.append(c.root/f"results/{d.SCHEMA}/job_receipts/{c.job['job_id']}.json")
        if suite=="libero_goal":files.extend(c.component_dir/name for name in c.g.ARTIFACT_NAMES)
    pull_add(last,files,jobs=[prior.job,last.job])
    meta_history={};goal_history={}
    for c in (prior,last):
        c.pull=last.pull
        meta,goal=compatibility_review(c)
        meta_history[c.job["job_id"]]=meta
        if goal:goal_history[c.job["job_id"]]=goal
    saved=dict(schema=d.SCHEMA,kind="root_segment_review",status="passed",suite=suite,visual_tokens=128,seed=17,
        source_sha256=d.SOURCE_SHA256,output_relative=base,job_id=last.job["job_id"],requested_segment_end=5000,
        completed_by_arm={"A":5000,"B":5000},ab_same_registered_boundary=True,resume_required=False,
        continuation="formal_training_complete_no_extension",registered_pair_jobs_at_review=[deepcopy(prior.job),deepcopy(last.job)],
        runtime_compatibility=last.runtime,runtime_compatibility_history=meta_history,runtime_compatibility_review=meta_history[last.job["job_id"]],
        files={p.relative_to(last.root).as_posix():sha(p) for p in files},pair_allocated_gpu_seconds=200,
        evidence_sha256={last.pull.relative_to(last.root).as_posix():sha(last.pull)})
    if suite=="libero_goal":saved.update(component_compatibility=last.component,component_compatibility_history=goal_history,
        component_compatibility_review=goal_history[last.job["job_id"]])
    reviewpath=last.root/base/"segment_reviews"/(last.job["job_id"]+".json");save(reviewpath,saved)
    return SimpleNamespace(accepted=accepted,prior=prior,last=last,rows=rows,saved=saved,reviewpath=reviewpath,
        jobs=[accepted.job,prior.job,last.job],base=base)


@pytest.mark.parametrize("suite",["libero_object","libero_goal"])
def test_all5000_training_compatibility_history_and_selected_identity(project,suite):
    c=completed_pair(project,suite)
    result=provenance(project,c.accepted,jobs=c.jobs,rows=c.rows)
    assert set(result["method_bindings"])=={"A128_seed17","B128_seed17"}
    assert len(result["registered_source_jobs"])==3
    assert result["method_bindings"]["A128_seed17"]["registered_training_job_ids"]==[c.prior.job["job_id"],c.last.job["job_id"]]


@pytest.mark.parametrize("change",["missing_history","missing_goal_history","failed_prior","missing_registered_job","changed_old_raw","partial_training","missing_validation","checkpoint","omitted_cost"])
def test_complete_training_cannot_hide_history_or_partial_arms(project,change):
    c=completed_pair(project,"libero_goal")
    if change=="missing_history":c.saved["runtime_compatibility_history"].pop(c.prior.job["job_id"])
    elif change=="missing_goal_history":c.saved["component_compatibility_history"].pop(c.prior.job["job_id"])
    elif change=="failed_prior":
        c.jobs[1]["status"]="FAILED";c.saved["registered_pair_jobs_at_review"][0]["status"]="FAILED"
    elif change=="missing_registered_job":c.jobs.pop(1)
    elif change=="changed_old_raw":
        path=c.prior.copied/"compatibility_events.jsonl";path.write_bytes(path.read_bytes()+b"{}\n")
    elif change=="partial_training":c.saved["completed_by_arm"]["B"]=4500
    elif change=="missing_validation":
        p=c.last.root/c.rows[0]["receipt"];r=read(p);r["evaluations"].pop();save(p,r)
        c.saved["files"][c.rows[0]["receipt"]]=sha(p)
    elif change=="checkpoint":c.rows[0]["checkpoint"]+=".other"
    elif change=="omitted_cost":c.saved["pair_allocated_gpu_seconds"]=100
    save(c.reviewpath,c.saved)
    with pytest.raises(ValueError):provenance(project,c.accepted,jobs=c.jobs,rows=c.rows)


def test_path_guard_rejects_final_values_before_parent_io(project):
    class Parent:
        root=project.root
        def path(self,name):pytest.fail("final path reached parent I/O")
    evidence=project.d.ScopedEvidence(Parent())
    with pytest.raises(ValueError,match="sealed"):
        evidence.path("configs/manifests/formal_main_v2/libero_goal/initial_states/sealed_final.json")


@pytest.fixture(scope="module")
def actual_project(tmp_path_factory):
    writer=load("tests/test_formal_asset_evaluation_adapter.py","actual_downstream_writer_for_review")
    actual=writer.project.__wrapped__(tmp_path_factory)
    target=tmp_path_factory.mktemp("synthetic_downstream_review_transport")
    module=load(HELPER,"actual_downstream_review_parser")
    inventory=read(ROOT/module.SOURCE_INVENTORY)
    names={*inventory["files"],module.SOURCE_INVENTORY,HELPER,module.SHARED,module.METADATA_HELPER,module.COMPONENT_HELPER,
        *actual.adapter.contract_files("libero_goal")}
    for name in names:
        path=target/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,path)
    shared=load(module.SHARED,"actual_downstream_review_shared")
    reader=load("scripts/formal_execution_manifests.py","actual_downstream_review_evidence")
    before={name:sha(ROOT/name) for name in names}
    yield SimpleNamespace(writer=writer,actual=actual,root=target,d=module,inventory=inventory,shared=shared,reader=reader,cases={})
    assert before=={name:sha(ROOT/name) for name in before}


def transport_downstream(project,case):
    """Explicit path transport; original producer bytes are retained untouched.

    The producer runs its actual legacy adapter and scoped installers, replacing
    GPU eval/profile and official Goal tensor I/O only. This parser integration
    separately stubs scientific-source reconstruction and the caller's original
    scientific adapter audit; both are tested by their own source/core suites.
    The actual metadata/component identities, all raw events, all artifact SHA,
    parent archive, restoration, and transport parsers are exercised unchanged.
    """
    p,d=project.root,project.d;source_root=project.actual.project.as_posix()
    def translate(value):
        if isinstance(value,dict):return {translate(k):translate(v) for k,v in value.items()}
        if isinstance(value,list):return [translate(v) for v in value]
        if isinstance(value,str):
            normalized=value.replace("\\","/")
            if normalized==source_root or normalized.startswith(source_root+"/"):
                return str(d.P)+normalized[len(source_root):]
        return value
    invocation=translate(read(case.path));invrel=case.path.relative_to(project.actual.project).as_posix()
    # Copy only declared nonweight inputs. Final value paths are never in this map.
    for name,checksum in case.value["watched_files"].items():
        original=Path(name)
        if original==project.actual.project/d.SOURCE_INVENTORY:continue
        target=d._input_relative(translate(name))
        destination=p/target;destination.parent.mkdir(parents=True,exist_ok=True)
        require_safe=not any("sealed" in part.lower() for part in original.parts)
        assert require_safe
        shutil.copyfile(original,destination)
        assert sha(destination)==checksum
    invsha=sha(p/d.SOURCE_INVENTORY)
    invocation["source_inventory_sha256"]=invsha
    invocation["watched_files"][str(d.P/d.SOURCE_INVENTORY)]=invsha
    save(p/invrel,invocation);new_invsha=sha(p/invrel)
    relative=d.remote_relative(invocation["run_root"])
    rawdir=case.output/"asset_compatibility"/case.job
    original_files={str(rawdir/name):sha(rawdir/name) for name in ("identity.json","events.jsonl","completion.json")}
    identity=translate(read(rawdir/"identity.json"));complete=translate(read(rawdir/"completion.json"))
    events=translate([json.loads(line) for line in (rawdir/"events.jsonl").read_text("utf-8").splitlines()])
    oldproof=complete.get("legacy_adapter_proof")
    oldreceipt=oldevents=None
    if oldproof:
        rawold=case.output/"adapter_invocations"/(oldproof["attempt_id"]+".json")
        rawlog=rawold.with_suffix(".jsonl")
        original_files.update({str(rawold):sha(rawold),str(rawlog):sha(rawlog)})
        oldreceipt=translate(read(rawold));oldevents=translate([json.loads(line) for line in rawlog.read_text("utf-8").splitlines()])
        oldreceipt["source_inventory_sha256"]=invsha
        oldevents[0]["identity"]["source_inventory_sha256"]=invsha
    identity["invocation_sha256"]=complete["invocation_sha256"]=new_invsha
    identity["watched_files"]={str(d.P/invrel):new_invsha,**invocation["watched_files"]}
    for innername in ("metadata_identity","component_identity"):
        if innername in identity:
            inner=identity[innername];inner["source_inventory_sha256"]=invsha
            inner["watched_files"][str(d.P/d.SOURCE_INVENTORY)]=invsha
    for row in events:
        row["invocation_sha256"]=new_invsha
        if row["event"]=="asset_metadata_compat_enter":row["identity"]=deepcopy(identity["metadata_identity"])
        if row["event"]=="goal_component_compat_enter":row["identity"]=deepcopy(identity["component_identity"])
    job=dict(experiment=d.SCHEMA,job_id=case.job,suite=invocation["suite"],mode=invocation["stage"],stage_key=invocation["stage_key"],
        run_root=invocation["run_root"],source_root=str(d.SOURCE),source_sha256=d.SOURCE_SHA256,
        invocation=invrel,invocation_sha256=new_invsha,status="COMPLETED",exit_code="0:0",elapsed_seconds=600,gpus=1,
        downstream_asset_compatibility=invocation["downstream_asset_compatibility"],execution_manifest_sha256=invocation["execution_manifest_sha256"])
    base=p/relative/"asset_compatibility"/case.job
    source_proof=dict(schema=d.SCHEMA,kind="asset_downstream_source_provenance",status="verified",suite=job["suite"],
        metadata_implementation=invocation["downstream_asset_compatibility"]["metadata_implementation"],
        registered_source_jobs=[],shared_projection_sha256="a"*64,
        shared_projection=dict(input_acceptance_sha256=sha(p/d._input_relative(translate(str(case.args["input_acceptance"]))))),
        synthetic_scientific_source_standin=True)
    if job["suite"]=="libero_goal":source_proof["component_implementation"]=invocation["downstream_asset_compatibility"]["component_implementation"]
    c=SimpleNamespace(**project.__dict__,case=case,job=job,invocation=invocation,identity=identity,complete=complete,events=events,
        oldreceipt=oldreceipt,oldevents=oldevents,base=base,relative=relative,source_proof=source_proof,
        pull=p/f"results/{d.SCHEMA}/pulls/synthetic_downstream_{case.job}/receipt.json")
    seal_downstream(c)
    assert all(sha(Path(name))==checksum for name,checksum in original_files.items())
    save(base.parent/"synthetic_transport.json",dict(synthetic=True,original_files_sha256=original_files,
        path_mapping={source_root:str(d.P)},standins=["GPU eval/profile runner","official Goal target tensor I/O",
        "already separately tested scientific source reconstruction and original caller scientific adapter audit"],
        actual_parent_archive_exercised=True,actual_scientific_work_completed=False,
        resume_watch_scope="Planned immutable/mutable partition only; existing E04 plan producer integration is pending"))
    return c


def seal_downstream(c):
    d,p,job=c.d,c.root,c.job
    old_artifacts=[];old_receipts=[]
    if c.oldreceipt is not None:
        attempt=c.oldreceipt["attempt_id"]
        oldbase=p/c.relative/"adapter_invocations"
        oldbase.mkdir(parents=True,exist_ok=True)
        log=oldbase/(attempt+".jsonl")
        log.write_text("".join(json.dumps(row,sort_keys=True)+"\n" for row in c.oldevents),encoding="utf-8",newline="\n")
        c.oldreceipt["events_sha256"]=sha(log)
        save(oldbase/(attempt+".json"),c.oldreceipt)
        for suffix in (".json",".jsonl"):
            file=oldbase/(attempt+suffix)
            old_artifacts.append(dict(source=str(d.P/f"results/{d.SCHEMA}/adapter_invocations"/file.name),
                path=str(d.P/file.relative_to(p).as_posix()),sha256=sha(file),bytes=file.stat().st_size))
        proof=dict(attempt_id=attempt,status=c.oldreceipt["status"],runner_status=c.oldreceipt.get("runner_status"),
            receipt=old_artifacts[0],journal=old_artifacts[1],
            archive_owner="parent downstream wrapper; copies are verified by root after SHA pull")
        c.complete["legacy_adapter_proof"]=proof;c.complete["legacy_adapter_artifacts"]=old_artifacts
        for row in c.events:
            if row["event"]=="legacy_adapter_return":row["legacy_adapter_proof"]=deepcopy(proof)
        old_receipts=[dict(path=old_artifacts[0]["path"],status=c.oldreceipt["status"],runner_status=c.oldreceipt.get("runner_status"))]
    save(c.base/"identity.json",c.identity)
    for row in c.events:
        if "identity_sha256" in row:row["identity_sha256"]=sha(c.base/"identity.json")
    (c.base/"events.jsonl").write_text("".join(json.dumps(row,sort_keys=True)+"\n" for row in c.events),encoding="utf-8",newline="\n")
    globalbase=d.P/f"results/{d.SCHEMA}/downstream_asset_invocations"/job["job_id"]
    artifacts=[]
    for name in ("identity.json","events.jsonl"):
        file=c.base/name
        artifacts.append(dict(source=str(globalbase/name),path=str(d.P/file.relative_to(p).as_posix()),sha256=sha(file),bytes=file.stat().st_size))
    c.complete["compatibility_artifacts"]=deepcopy(artifacts)
    save(c.base/"completion.json",c.complete)
    file=c.base/"completion.json";artifacts.append(dict(source=str(globalbase/file.name),path=str(d.P/file.relative_to(p).as_posix()),sha256=sha(file),bytes=file.stat().st_size))
    receipt=dict(schema=d.SCHEMA,kind="formal_downstream_job_receipt",job_id=job["job_id"],stage=job["mode"],stage_key=job["stage_key"],
        run_root=job["run_root"],source_sha256=d.SOURCE_SHA256,adapter_sha256=d.OLD_ADAPTER_SHA256,invocation_sha256=job["invocation_sha256"],
        wrapper_sha256=c.invocation["wrapper_sha256"],stage_completed_claimed=False,
        downstream_asset_compatibility=c.invocation["downstream_asset_compatibility"],status="returned",exit_code=0,
        adapter_artifacts=old_artifacts,adapter_receipts=old_receipts,asset_compatibility_artifacts=artifacts)
    receiptfile=save(p/f"results/{d.SCHEMA}/job_receipts/{job['job_id']}.json",receipt)
    c.wrapper_receipt=receipt
    paths=[p/d.remote_relative(a["path"]) for a in artifacts+old_artifacts]+[receiptfile]
    entries=[dict(relative=x.relative_to(p).as_posix(),path=str(d.P/x.relative_to(p).as_posix()),
        sha256=sha(x),bytes=x.stat().st_size,job_ids=[job["job_id"]]) for x in paths]
    for name in ("inventory_before.json","inventory_after.json"):save(c.pull.parent/name,dict(files=entries))
    accounting=dict(jobs={job["job_id"]:{k:job[k] for k in ("status","exit_code","elapsed_seconds")}})
    save(c.pull,dict(schema=d.SCHEMA,kind="nonweight_pull",status="verified_nonweight_snapshot",final_evidence=True,weights_copied=False,
        sealed_initial_states_copied=False,selected_jobs=[dict(job,include_run_root=True)],accounting_before=accounting,accounting_after=accounting,
        inventory_sha256=sha(c.pull.parent/"inventory_before.json"),files=[dict(row,action="downloaded_verified") for row in entries]))


def review_actual(c,monkeypatch):
    monkeypatch.setattr(c.d,"review_source_provenance",lambda *a,**kw:deepcopy(c.source_proof))
    return c.d.review_invocation(c.reader.Evidence(c.root),job=c.job,invocation=c.invocation,wrapper_receipt=c.wrapper_receipt,
        inventory=c.inventory,pull_receipt=c.pull,source_provenance=c.source_proof,legacy_adapter_review=c.oldreceipt)


def actual_case(project,suite,stage="development"):
    key=(suite,stage)
    if key not in project.cases:
        case=project.writer.new_case(project.actual,suite=suite,stage=stage)
        project.writer.run_case(project.actual,case)
        project.cases[key]=case
    # Each parser mutation receives a fresh transport of retained original bytes.
    return transport_downstream(project,project.cases[key])


@pytest.mark.parametrize("suite",["libero_object","libero_goal"])
@pytest.mark.parametrize("stage",["development","final","collect","full","components"])
def test_actual_writer_context_parent_archive_pull_and_independent_review(actual_project,monkeypatch,suite,stage):
    c=actual_case(actual_project,suite,stage)
    result=review_actual(c,monkeypatch)
    assert result["status"]=="verified" and result["event_count"]==(14 if suite=="libero_goal" else 8)
    assert result["scientific_completion_not_inferred"] and result["metadata_loads"]==1
    assert result["component_loads"]==(2 if suite=="libero_goal" else 0)
    assert result["legacy_adapter_attempt_id"]==c.oldreceipt["attempt_id"]


@pytest.mark.parametrize("mutation",["missing_metadata_event","missing_component_event","wrong_component_mapping",
    "component_empty","component_not_restored","metadata_not_restored","outer_not_restored","different_inner_job",
    "unrestored_old_binding","old_code_mismatch","missing_old_proof","different_old_manifest","different_event_invocation",
    "different_event_stage","historical_contract","goal_missing_contract","parent_missing_contract","bytes_mismatch",
    "old_archive_missing","pull_missing_file","pull_changed_inventory","nonterminal_allocation","failed_outer"])
def test_actual_writer_proof_rejects_resealed_identity_and_lifecycle_mutations(actual_project,monkeypatch,mutation):
    c=actual_case(actual_project,"libero_goal")
    event=lambda name:next(row for row in c.events if row["event"]==name)
    if mutation=="missing_metadata_event":c.events.remove(event("asset_metadata_compat_load_complete"))
    elif mutation=="missing_component_event":c.events.remove(event("goal_component_load_complete"))
    elif mutation=="wrong_component_mapping":event("goal_component_load_start")["mapping"]["target_path"]+=".other"
    elif mutation=="component_empty":event("goal_component_load_complete")["state_tensor_count"]=0
    elif mutation=="component_not_restored":event("goal_component_compat_exit")["torch_load_unchanged"]=False
    elif mutation=="metadata_not_restored":event("asset_metadata_compat_exit")["original_loader_restored"]=False
    elif mutation=="outer_not_restored":c.complete["loader_bindings_restored"]=False
    elif mutation=="different_inner_job":c.oldreceipt["job_id"]="999999"
    elif mutation=="unrestored_old_binding":
        next(x for x in c.oldevents if x["event"]=="bindings_restored")["original_verify_code_sha256"]="f"*64
    elif mutation=="old_code_mismatch":c.oldreceipt["frozen_execute_code_sha256"]="f"*64
    elif mutation=="different_old_manifest":c.oldreceipt["execution_manifest_sha256"]="f"*64
    elif mutation=="different_event_invocation":event("goal_component_load_complete")["invocation_sha256"]="f"*64
    elif mutation=="different_event_stage":event("asset_metadata_compat_load_start")["stage"]="collect"
    elif mutation=="historical_contract":c.invocation["runtime_compatibility"]=c.source_proof["metadata_implementation"]
    elif mutation=="goal_missing_contract":c.invocation["downstream_asset_compatibility"].pop("component_implementation")
    elif mutation=="failed_outer":
        c.complete["status"]="failed";c.complete["exit_code"]=1;c.complete["errors"]=[dict(error="synthetic failure")]
    seal_downstream(c)
    # Post-seal failures intentionally target the independently bound raw map.
    if mutation=="missing_old_proof":
        value=read(c.base/"completion.json");value["legacy_adapter_proof"]=None;save(c.base/"completion.json",value)
    elif mutation=="parent_missing_contract":c.wrapper_receipt.pop("downstream_asset_compatibility")
    elif mutation=="bytes_mismatch":c.wrapper_receipt["asset_compatibility_artifacts"][0]["bytes"]+=1
    elif mutation=="old_archive_missing":c.wrapper_receipt["adapter_artifacts"].pop()
    elif mutation=="pull_missing_file":
        value=read(c.pull);value["files"].pop();save(c.pull,value)
    elif mutation=="pull_changed_inventory":
        path=c.pull.parent/"inventory_after.json";value=read(path);value["files"].pop();save(path,value)
    elif mutation=="nonterminal_allocation":
        c.job["status"]="RUNNING"
    if mutation in ("parent_missing_contract","bytes_mismatch","old_archive_missing"):
        save(c.root/f"results/{c.d.SCHEMA}/job_receipts/{c.job['job_id']}.json",c.wrapper_receipt)
    with pytest.raises(ValueError):review_actual(c,monkeypatch)


def test_object_rejects_goal_contract_even_null(actual_project,monkeypatch):
    c=actual_case(actual_project,"libero_object")
    c.invocation["downstream_asset_compatibility"]["component_implementation"]=None
    with pytest.raises(ValueError,match="exact downstream contract"):
        review_actual(c,monkeypatch)


@pytest.mark.parametrize("suite",["libero_object","libero_goal"])
def test_actual_resume_uses_new_job_attempt_and_preserves_original_bytes(actual_project,monkeypatch,suite):
    p=actual_project
    first=p.writer.new_case(p.actual,suite=suite);p.writer.run_case(p.actual,first)
    first_review=review_actual(transport_downstream(p,first),monkeypatch)
    ledger=first.output/"trials.jsonl";prefix=ledger.read_bytes()
    oldbytes={name:sha(first.output/"asset_compatibility"/first.job/name) for name in ("identity.json","events.jsonl","completion.json")}
    second=p.writer.new_case(p.actual,suite=suite,previous=first);p.writer.run_case(p.actual,second)
    c=transport_downstream(p,second);second_review=review_actual(c,monkeypatch)
    assert c.invocation["resume"] and second_review["job_id"]!=first_review["job_id"]
    assert second_review["legacy_adapter_attempt_id"]!=first_review["legacy_adapter_attempt_id"]
    assert ledger.read_bytes().startswith(prefix)
    resultrows=[json.loads(x) for x in ledger.read_text("utf-8").splitlines() if json.loads(x)["event"]=="result"]
    assert len(resultrows)==len({x["trial_id"] for x in resultrows})==2
    assert oldbytes=={name:sha(first.output/"asset_compatibility"/first.job/name) for name in oldbytes}
    first_identity=read(first.output/"asset_compatibility"/first.job/"identity.json")
    c.identity["job_id"]=first_identity["job_id"];seal_downstream(c)
    with pytest.raises(ValueError):review_actual(c,monkeypatch)


@pytest.mark.parametrize("behavior",["early","after_load"])
def test_actual_failed_writer_is_retained_and_never_verified(actual_project,monkeypatch,behavior):
    p=actual_project;case=p.writer.new_case(p.actual,suite="libero_goal")
    p.writer.run_case(p.actual,case,behavior=behavior,expected=1)
    c=transport_downstream(p,case)
    original={str(path):sha(path) for path in c.base.glob("*") if path.is_file()}
    with pytest.raises(ValueError):review_actual(c,monkeypatch)
    assert original=={name:sha(Path(name)) for name in original}


@pytest.mark.parametrize("mutation",["final_release","development_path","watched_final","final_output_panel"])
def test_final_values_never_read_by_local_runtime_reviewer(actual_project,monkeypatch,mutation):
    c=actual_case(actual_project,"libero_goal","final" if mutation in ("final_release","final_output_panel") else "development")
    spec=read(c.root/c.d.FORMAL_REGISTRATION)["suites"]["libero_goal"]
    forbidden=(c.root/c.relative/"panel.json" if mutation=="final_output_panel"
        else c.root/spec["initial_states_root"]/"sealed_final.json")
    touched=[]
    for method in ("open","stat","resolve"):
        original=getattr(Path,method)
        def guarded(path,*a,_original=original,**kw):
            if path==forbidden:
                touched.append(str(path));pytest.fail("local review touched final state values")
            return _original(path,*a,**kw)
        monkeypatch.setattr(Path,method,guarded)
    if mutation=="final_release":
        index=c.invocation["argv"].index("--release-sha256")+1;c.invocation["argv"][index]="f"*64
    elif mutation=="development_path":
        index=c.invocation["argv"].index("--development-panel")+1
        c.invocation["argv"][index]=str(c.d.P/spec["initial_states_root"]/"sealed_final.json")
    elif mutation=="final_output_panel":
        # Exercise the lexical guard itself, before the caller's path method.
        class Parent:
            root=c.root
            def path(self,name):pytest.fail("final value path reached parent I/O")
        guarded=c.d.ScopedEvidence(Parent(),forbidden_paths=[c.relative+"/panel.json"])
        with pytest.raises(ValueError,match="state-value panel"):
            guarded.path(forbidden)
        return
    else:c.invocation["watched_files"][str(c.d.P/spec["initial_states_root"]/"sealed_final.json")]="f"*64
    with pytest.raises(ValueError):review_actual(c,monkeypatch)
    assert not touched
