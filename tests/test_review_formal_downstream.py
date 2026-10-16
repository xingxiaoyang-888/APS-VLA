"""CPU-only synthetic server evidence; no actual weights, SSH or final values.

Use the real trial, collection, profile and adapter binding writers. The upstream
GPU gate/source proof is substituted by the existing72-receipt fixture only.
"""
from contextlib import contextmanager, nullcontext
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import shutil
from types import SimpleNamespace

import numpy as np
import pytest

import test_formal_downstream_supervisor as upstream
import test_formal_profiling as timing
from cti_vla.evaluation import formal_profiling as fp, formal_trials as trials
from cti_vla.evaluation.libero_runtime import PolicyChunk, TrialLedger, run_episode, INPUTS_VERSION, ACTION_VERSION
from cti_vla.evaluation.formal_runtime import uniform_formal_indices
from cti_vla.evaluation.profiling import ProfileJournal, ProfileMethod, read_profile_cost
from cti_vla.models.abstraction.packing import PACKING_VERSION

ROOT = Path(__file__).resolve().parents[1]
tool = upstream.module("scripts/review_formal_downstream.py")


@pytest.fixture(scope="module", autouse=True)
def immutable_production_bytes():
    scheduler = upstream.module("scripts/ops/formal_downstream_supervisor.py")
    inventory = json.loads((ROOT / scheduler.SOURCE_INVENTORY).read_text(encoding="utf-8"))
    before = {name: scheduler.digest(ROOT / name) for name in inventory["files"]}
    support = {n: scheduler.digest(ROOT / n) for n in (scheduler.ADAPTER, scheduler.WRAPPER, "scripts/ops/formal_downstream_supervisor.py")}
    assert len(before) == 173 and before == inventory["files"]
    yield
    assert before == {n: scheduler.digest(ROOT / n) for n in before}
    assert support == {n: scheduler.digest(ROOT / n) for n in support}


@pytest.fixture
def project(tmp_path, monkeypatch):
    p = upstream.project.__wrapped__(tmp_path, monkeypatch)
    inventory, _ = p.scheduler.check_source(None, None, None)
    p.inventory = inventory
    for name in ("scripts/eval_formal_selector_libero.py", "scripts/eval_libero.py", "scripts/profile_formal.py",
                 "src/cti_vla/evaluation/formal_profiling.py", "src/cti_vla/evaluation/future_profiling.py"):
        dst = p.root / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, dst)
        inventory["files"][name] = p.scheduler.digest(dst)
    for suite, spec in p.registration["suites"].items():
        p.save(spec["model_manifest"], dict(schema_version=1, repository="synthetic/" + suite,
            revision=spec["model_revision"], total_bytes=1, files=[dict(path="not_present.safetensors", size=1, sha256="f"*64)]))
    shutil.copyfile(ROOT / "results/setup/runtime_sources.json", mkdir_parent(p.root / "results/setup/runtime_sources.json"))
    p.args.stop_after = 1
    return p


def mkdir_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def policy(identity, *, selection=True, stage_context=lambda _: nullcontext()):
    def predict(obs, instruction):
        meta = dict(schema="formal_main_v2", suite=identity["suite"], method=identity["method"], visual_tokens=identity["visual_tokens"],
            per_camera_budgets=[identity["visual_tokens"]//2]*2, policy_calls=1, vision_calls=1, packing_calls=1,
            scorer_calls=int(identity["method"] in ("A", "B")), future_head_calls=0, language_cache="disabled",
            inputs_version=INPUTS_VERSION, action_version=ACTION_VERSION, packing_version=PACKING_VERSION,
            diagnostic_indices_recorded=selection)
        if identity["method"] in ("A", "B"):
            meta.update(selector_checkpoint_sha256=identity["checkpoint_sha256"], training_seed=identity["training_seed"], pair_id=identity["pair_id"])
        if selection:
            meta["retained_indices"] = (uniform_formal_indices(identity["visual_tokens"]).tolist() if identity["method"] == "uniform"
                else list(range(identity["visual_tokens"]//2)) + list(range(256,256+identity["visual_tokens"]//2)))
        for phase in fp.PHASES:
            with stage_context(phase):
                pass
        return PolicyChunk(np.zeros((8,7)), np.zeros((8,7)), meta)
    return predict


def official_sources(p):
    sources = json.loads((p.root / "results/setup/runtime_sources.json").read_text())
    return {"libero" if r["directory"].endswith("LIBERO") else "openvla_oft": dict(revision=r["revision"],
        verification="archive_all_files_sha256", archive_sha256=r["archive_sha256"], inventory_sha256="7"*64, file_count=101)
        for r in sources["sources"]}


def begin(p, *, job_id="500", status="COMPLETED"):
    plan = upstream.make_plan(p)
    inv = deepcopy(plan["invocation"])
    p.save(plan["invocation_relative"], inv)
    job = dict(job_id=job_id, name="cti-formal-downstream", experiment=p.scheduler.ROUND, mode=p.args.stage,
        suite=inv["suite"], method_ids=inv["method_ids"], stage_key=inv["stage_key"], source_sha256=inv["source_sha256"],
        adapter_sha256=inv["adapter_sha256"], status=status, exit_code="0:0" if status == "COMPLETED" else "1:0",
        elapsed_seconds=3600, gpus=1, run_root=inv["run_root"], invocation=plan["invocation_relative"],
        invocation_sha256=p.scheduler.digest(p.root / plan["invocation_relative"]), execution_manifest_sha256=inv["execution_manifest_sha256"], submitted_utc="2026-01-01")
    p.state["registered_jobs"].append(job)
    output = plan["output_relative"]
    manifest = json.loads((p.root / p.args.execution_manifest).read_text())
    opt = tool.options(inv)
    paths = [opt[k] for k in ("--execution-manifest", "--registration", "--asset-manifest", "--protocol", "--windows", "--input-acceptance")]
    gate = PurePosixPath(opt["--input-acceptance"]).parent
    paths += [str(gate/n) for n in ("input_calls.jsonl", "resume_acceptance.json", "f03_calls.jsonl")]
    primary = next(r for r in p.registration["pairs"] if r["suite"] == inv["suite"] and r["visual_tokens"] == 128 and r["seed"] == 17)
    paths.append(str(p.scheduler.P / primary["path"]))
    stage = p.args.stage
    paths += [opt[k] for k in (("--release", "--final-registry", "--sealed-final") if stage == "final" else ("--development-panel",))]
    if stage in ("collect", "full", "components"):
        paths += [str(PurePosixPath(inv["source_root"])/n) for n in ("scripts/profile_formal.py", "scripts/eval_libero.py", "src/cti_vla/evaluation/formal_profiling.py")]
    if stage in ("full", "components"):
        paths += [opt["--global-freeze"], opt["--panel"]]
    watched = {}
    source = PurePosixPath(inv["source_root"])
    for path in paths:
        if path == opt.get("--sealed-final"):
            watched[path] = "8"*64
        else:
            remote = PurePosixPath(path)
            rel = remote.relative_to(source if source in remote.parents else p.scheduler.P).as_posix()
            watched[path] = p.scheduler.digest(p.root / rel)
    for row in manifest["methods"]:
        if row["identity"]["method"] in ("A", "B"):
            watched[row["checkpoint"]] = row["identity"]["checkpoint_sha256"]
            for k in ("receipt", "pair_config", "f01_report"):
                watched[str(p.scheduler.P/row[k])] = p.scheduler.digest(p.root/row[k])
            path = str(PurePosixPath(row["f01_report"]).parent / "operator_calls.jsonl")
            watched[str(p.scheduler.P/path)] = p.scheduler.digest(p.root/path)
    state_root = p.registration["suites"][inv["suite"]]["initial_states_root"]
    panel = json.loads((p.root/state_root/ ("final_registry.json" if stage == "final" else "development.json")).read_text())
    if stage == "final":
        panel = {**panel, "release_file_sha256": opt["--release-sha256"]}
    spec = p.registration["suites"][inv["suite"]]
    asset = json.loads((p.root/spec["model_manifest"]).read_text())
    base = dict(repository=asset["repository"], revision=asset["revision"], file_count=1, total_bytes=1)
    common = dict(manifest=manifest, registration_sha256=p.scheduler.signature(p.registration), source_files=p.sources, watched_files=watched)
    if stage in ("development", "final"):
        config = dict(**common, schema="formal_main_v2", kind="evaluation_run", panel_signature=p.scheduler.signature(panel),
            source_verification=official_sources(p), runtime=dict(torch="synthetic", python="synthetic", cuda="synthetic", numpy="synthetic", gpu="NVIDIA L40"), policy_watchdog_seconds=60.)
        if stage != "final":
            p.save(output + "/panel.json", panel)
    else:
        attempt = dict(version=fp.PROFILE_VERSION, command=stage, suite=inv["suite"], registration_sha256=common["registration_sha256"],
            execution_manifest_sha256=inv["execution_manifest_sha256"], slurm_job_id=job_id, test_opened=False)
        p.save(output + "/attempt.json", attempt)
        config = dict(**common, **{k:v for k,v in attempt.items() if k != "registration_sha256"},
            runtime=dict(gpu="NVIDIA L40", python="synthetic", packages={}, dtype="bfloat16", attention="sdpa"),
            allocation=dict(gpu_uuid="synthetic-GPU", own_pid=123, other_compute_processes=0), model_loading_seconds_excluded_from_calls=.25,
            checkpoint=base, dense_identity=manifest["methods"][0]["identity"], all_instances_share_one_loaded_base=True,
            cache_scope="none", future_head_deployed=False, hardware={}, compile="disabled; native eager SDPA",
            profiling_registration=p.registration["profiling"], profiler_script_sha256=p.inventory["files"]["scripts/profile_formal.py"],
            profiler_module_sha256=p.inventory["files"]["src/cti_vla/evaluation/formal_profiling.py"])
        if stage == "collect":
            config["version"] = fp.PANEL_VERSION
        else:
            config["global_freeze_sha256"] = p.scheduler.digest(p.root/p.args.freeze_directory/"global_freeze.json")
    p.save(output + "/config.json", config)
    return SimpleNamespace(plan=plan,inv=inv,job=job,output=output,manifest=manifest,config=config,panel=panel,base=base,
        pull_relative=f"results/formal_main_v2/pulls/synthetic{job_id}/receipt.json", review_relative=f"results/formal_main_v2/downstream_reviews/{job_id}.json")


def emit_adapter(p, a, *, failed=False, before=None):
    """Actual recorded_bindings/append/publish functions; simulated server paths."""
    adapter = upstream.module(p.scheduler.ADAPTER)
    legacy = upstream.module("scripts/eval_libero.py")
    evaluate = upstream.module("scripts/eval_formal_selector_libero.py")
    profiler = upstream.module("scripts/profile_formal.py")
    from cti_vla.evaluation import future_profiling
    attempt = a.job["job_id"] + "_" + "a"*32
    archive = a.output + "/adapter_invocations/"
    event_path = p.root/archive/(attempt+".jsonl")
    context = dict(schema="formal_main_v2",kind="formal_evaluation_adapter",version=adapter.VERSION,attempt_id=attempt,
        job_id=a.job["job_id"],mode="evaluate" if p.args.stage in ("development","final") else p.args.stage,
        resume=a.inv["resume"],output=a.inv["run_root"],source_root=a.inv["source_root"],source_inventory=a.inv["source_inventory"],
        source_inventory_sha256=a.inv["source_inventory_sha256"],frozen_source_sha256=p.scheduler.FROZEN_SHA256,verified_frozen_file_count=173,
        adapter_path=str(p.scheduler.P/p.scheduler.ADAPTER),adapter_sha256=p.scheduler.ADAPTER_SHA256,
        execution_manifest_sha256=a.inv["execution_manifest_sha256"],registration_sha256=p.scheduler.signature(p.registration),
        eval_script_sha256=p.inventory["files"]["scripts/eval_formal_selector_libero.py"],legacy_validator_file_sha256=p.inventory["files"]["scripts/eval_libero.py"],
        frozen_execute_code_sha256=adapter.code_sha(evaluate.execute),frozen_trial_loop_code_sha256=adapter.code_sha(trials.evaluate_formal_trials))
    if context["mode"] != "evaluate":
        context.update(profiler_script_sha256=p.inventory["files"]["scripts/profile_formal.py"],
            frozen_profiler_run_code_sha256=adapter.code_sha(profiler.run),frozen_profiler_collect_code_sha256=adapter.code_sha(profiler.collect))
    def emit(event, **values):
        adapter.append(event_path, dict(event=event,attempt_id=attempt,job_id=a.job["job_id"],utc="synthetic-time",**values))
    emit("adapter_start",identity=deepcopy(context))
    with adapter.recorded_bindings(evaluate,legacy,future_profiling,PurePosixPath(a.inv["source_root"]),emit) as bindings:
        context["bindings"] = bindings
        if context["mode"] in ("evaluate","collect"):
            for key,row in official_sources(p).items():
                emit("official_source_verified",path=str(p.scheduler.P/("external/LIBERO" if key == "libero" else "external/openvla-oft")),
                    expected_revision=row["revision"],verification=row)
        if context["mode"] == "evaluate":
            before = before or dict(bytes=0,sha256=hashlib.sha256(b"").hexdigest(),terminal_trial_ids=[],invocation_job_ids=[],active_trial_ids=[],events=0)
            context.update(before_ledger_raw={k:before[k] for k in ("bytes","sha256")},before_ledger=before)
            emit("resume_preflight_passed",evidence=before,panel_signature=a.config["panel_signature"])
            if not failed:
                context["after_ledger"] = adapter.checked_ledger(p.root/a.output/"trials.jsonl",p.scheduler.signature(a.config),
                    panel=a.panel,identifiers=a.inv["method_ids"],validators=trials)
    context.update(status="failed" if failed else "returned",frozen_source_unchanged=True,old_ledger_prefix_unchanged=context["mode"]=="evaluate")
    if not failed:
        context["runner_status"] = a.summary["status"]
    emit("adapter_end",status=context["status"],runner_status=context.get("runner_status"))
    context.update(events_path=str(p.scheduler.P/"results/formal_main_v2/adapter_invocations"/(attempt+".jsonl")),
        events_sha256=p.scheduler.digest(event_path),finished_utc="synthetic-time")
    receipt_path=p.root/archive/(attempt+".json")
    adapter.publish(receipt_path,context)
    artifacts=[dict(source=str(p.scheduler.P/"results/formal_main_v2/adapter_invocations"/path.name),
        path=str(p.scheduler.P/archive/path.name),sha256=p.scheduler.digest(path),bytes=path.stat().st_size) for path in (receipt_path,event_path)]
    a.adapter=context
    wrapper=dict(schema="formal_main_v2",kind="formal_downstream_job_receipt",job_id=a.job["job_id"],stage=p.args.stage,
        stage_key=a.job["stage_key"],run_root=a.job["run_root"],invocation_sha256=a.job["invocation_sha256"],source_sha256=p.scheduler.FROZEN_SHA256,
        adapter_sha256=p.scheduler.ADAPTER_SHA256,wrapper_sha256=a.inv["wrapper_sha256"],stage_completed_claimed=False,wall_seconds=3000.,
        status=context["status"],exit_code=1 if failed else 0,adapter_artifacts=artifacts,
        adapter_receipts=[dict(path=str(p.scheduler.P/archive/receipt_path.name),status=context["status"],runner_status=context.get("runner_status"))])
    p.save(f"results/formal_main_v2/job_receipts/{a.job['job_id']}.json",wrapper)
    for ext in ("out","err"):
        p.save(f"results/slurm/{a.job['name']}_{a.job['job_id']}.{ext}",dict(synthetic=True))


def pull(p,a):
    names=[f.relative_to(p.root).as_posix() for f in (p.root/a.output).rglob("*") if f.is_file()]
    assert not (p.args.stage == "final" and a.output+"/panel.json" in names)
    names += [f"results/formal_main_v2/job_receipts/{a.job['job_id']}.json",*[f"results/slurm/{a.job['name']}_{a.job['job_id']}.{ext}" for ext in ("out","err")]]
    rows=[dict(relative=n,path=str(p.scheduler.P/n),bytes=(p.root/n).stat().st_size,sha256=p.scheduler.digest(p.root/n),job_ids=[a.job["job_id"]]) for n in sorted(names)]
    directory=str(PurePosixPath(a.pull_relative).parent)
    inventory=dict(files=rows,missing=[],excluded=[])
    for name in ("inventory_before.json","inventory_after.json"):
        p.save(directory+"/"+name,inventory)
    p.save(a.pull_relative,dict(schema="formal_main_v2",kind="nonweight_pull",status="verified_nonweight_snapshot",final_evidence=True,
        weights_copied=False,sealed_initial_states_copied=False,selected_jobs=[{**a.job,"include_run_root":True}],
        accounting_before={"jobs":{a.job["job_id"]:a.job}},accounting_after={"jobs":{a.job["job_id"]:a.job}},
        files=[{**r,"action":"downloaded_verified"} for r in rows],inventory_sha256=p.scheduler.digest(p.root/directory/"inventory_before.json")))


def rollout_fixture(p, *, complete=False, fail=False):
    a=begin(p,status="FAILED" if fail else "COMPLETED")
    sig=p.scheduler.signature(a.config)
    ledger=TrialLedger(p.root/a.output/"trials.jsonl",run_signature=sig)
    ledger.append(dict(event="invocation",slurm_job_id=a.job["job_id"]))
    policies={r["identity"]["method_id"]:policy(r["identity"]) for r in a.manifest["methods"]}
    if p.args.stage == "final":
        # Only synthetic identities are converted to a fake zero state in the
        # in-memory runner. No sealed file or real value is opened anywhere.
        runner_panel={**a.panel,"states":[{**s,"initial_state":[0.]} for s in a.panel["states"]]}
    else:
        runner_panel=a.panel
    trials.evaluate_formal_trials(runner_panel,policies,ledger,lambda _: (timing.FakeEnv(1),"synthetic instruction"),
        reseed=lambda:None,stop_after=None if complete else 1)
    if fail:
        ledger.append({**trials._identity(a.panel,a.panel["states"][0],a.inv["method_ids"][1]),"event":"start"})
    provenance={**a.config,"run_signature":sig,"checkpoint":a.base,"runtime":{**a.config["runtime"],"slurm_job_id":a.job["job_id"]}}
    a.summary=trials.summarize_formal_trials(a.panel,a.inv["method_ids"],ledger,provenance=provenance,checkpoint_unchanged=None if fail else True)
    p.save(a.output+"/closed_loop_report.json",a.summary)
    emit_adapter(p,a,failed=fail)
    pull(p,a)
    return a


def review(p,a):
    return tool.review(a.job["job_id"],a.pull_relative,project=p.root,state=p.state,scheduler=p.scheduler,helper=p.helper)


def make_dense_manifest(p):
    rows=p.helper.suite_rows(p.helper.Evidence(p.root),p.registration,"libero_10",p.sources,["dense"])
    p.args.stage="collect";p.args.stop_after=None
    p.args.execution_manifest="results/formal_main_v2/execution/collect.json"
    p.save(p.args.execution_manifest,p.helper.make_execution(p.registration,"libero_10",rows))


def collection_fixture(p, *, fail=False):
    make_dense_manifest(p)
    a=begin(p,status="FAILED" if fail else "COMPLETED")
    ledger=TrialLedger(p.root/a.output/"collection_trials.jsonl",run_signature=p.scheduler.signature(a.config))
    provenance={**a.config,"source_verification":official_sources(p),"checkpoint_unchanged":True}
    episodes=[]
    for state in fp.fixed_profile_states(a.panel):
        ledger.append(dict(event="start",trial_id=state["trial_id"],method="dense"))
        if fail and len(episodes)==2:
            break
        capture=fp.CaptureControlObservations(timing.FakeEnv())
        result=run_episode(capture,policy(a.manifest["methods"][0]["identity"],selection=False),"synthetic instruction",state["initial_state"],max_steps=520)
        ledger.append(dict(event="result",trial_id=state["trial_id"],method="dense",**result))
        episodes.append(fp.save_dense_collection(p.root/a.output/f"task{state['task_id']:02d}",state,"synthetic instruction",result,capture.captured,provenance=provenance))
    if fail:
        summary=dict(status="failed",command="collect",test_opened=False,cost=None,error="Synthetic interrupted environment",execution_wall_seconds_including_model_loading=5.)
    else:
        fp.write_profile_panel(p.root/a.output,a.panel,episodes,provenance=provenance,registration=p.registration)
        samples,panel=fp.load_profile_panel(p.root/a.output/"panel.json",development=a.panel,registration=p.registration,dense_identity=a.manifest["methods"][0]["identity"])
        summary=dict(status="completed_collection",observations=30,panel=panel,policy_calls=sum(r.get("policy_calls",0) for r in ledger.events if r["event"]=="result"),
            new_success_trials=False,test_opened=False,execution_wall_seconds_including_model_loading=5.,
            cost_scope="10 dense collection trajectories; all allocation time charged, excluded from success counts and latency samples")
    a.summary=summary;p.save(a.output+"/summary.json",summary)
    emit_adapter(p,a,failed=fail);pull(p,a)
    return a


def test_real_writers_partial_development_recompute_and_e04_consume(project):
    p=project;a=rollout_fixture(p)
    result=review(p,a)
    assert result["status"]=="passed" and result["scientific_complete"] is False and result["completed_trials"]==1
    assert result["cost"]["all_attempt_gpu_seconds"]==3600
    assert not (p.root/a.review_relative).exists()
    tool.publish_review(p.root/a.review_relative,result,root_review=True)
    consumed=p.scheduler.require_root_review(p.helper.Evidence(p.root),a.review_relative,p.scheduler.formal_jobs(p.state),expected_stage="development")
    assert consumed["completed_trials"]==1
    with pytest.raises(ValueError,match="new immutable"):
        tool.publish_review(p.root/a.review_relative,result,root_review=True)


def test_all_cells_complete_and_unknown_start_is_cost_only(project):
    a=rollout_fixture(project,complete=True)
    result=review(project,a)
    assert result["scientific_complete"] is True and result["completed_trials"]==400
    assert all(row["trials"]==100 for row in result["reconstructed_summary"]["methods"].values())


def test_failed_allocation_keeps_unknown_start_and_full_cost(project):
    a=rollout_fixture(project,fail=True)
    result=review(project,a)
    assert not result["scientific_complete"] and result["unfinished_attempts_unknown_cost"]==1
    assert result["reconstructed_summary"]["cost"]["policy_calls_total"] is None
    assert result["cost"]["all_attempt_gpu_seconds"]==3600


@pytest.mark.parametrize("mutation",["no_lf","bad_json","stale_report","action","token","checkpoint","missing_adapter","changed_pull","job_cost","missing_ledger","duplicate_start"])
def test_reject_corrupt_or_incomplete_raw_evidence_without_output(project,mutation):
    p=project;a=rollout_fixture(p)
    ledger=p.root/a.output/"trials.jsonl"
    if mutation=="no_lf": ledger.write_bytes(ledger.read_bytes().rstrip(b"\n"))
    elif mutation=="bad_json": ledger.write_bytes(ledger.read_bytes()+b'{broken\n')
    elif mutation=="stale_report":
        report=deepcopy(a.summary);report["completed_trials"]=0;p.save(a.output+"/closed_loop_report.json",report)
    elif mutation in ("action","token","checkpoint"):
        events=list(tool.lines(ledger));row=events[-1]
        if mutation=="action": row["executed_actions"][0][0]=.2
        elif mutation=="token": row["chunks"][0]["metadata"]["retained_indices"].pop()
        else:
            config=deepcopy(a.config);config["watched_files"][str(p.scheduler.P/p.scheduler.REGISTRATION)]="0"*64;p.save(a.output+"/config.json",config)
        ledger.write_bytes(b"".join((json.dumps(r)+"\n").encode() for r in events))
    elif mutation=="missing_adapter": (p.root/a.output/"adapter_invocations"/(a.adapter["attempt_id"]+".json")).unlink()
    elif mutation=="job_cost": a.job["elapsed_seconds"]=-1
    elif mutation=="missing_ledger": ledger.unlink()
    elif mutation=="duplicate_start":
        events=list(tool.lines(ledger));events.insert(2,deepcopy(events[1]))
        ledger.write_bytes(b"".join((json.dumps(r)+"\n").encode() for r in events))
    if mutation not in ("missing_adapter","changed_pull"):
        pull(p,a)
    else:
        (p.root/a.output/"config.json").write_bytes((p.root/a.output/"config.json").read_bytes()+b" ")
    with pytest.raises((ValueError,FileNotFoundError,KeyError,json.JSONDecodeError)):
        review(p,a)
    assert not (p.root/a.review_relative).exists()


def test_released_final_review_never_reads_sealed_or_output_state_values(project,monkeypatch):
    p=project;p.args.freeze_directory=upstream.freeze_project(p)
    p.args.stage="final";p.args.execution_manifest=p.args.freeze_directory+"/final_execution/libero_10.json"
    original=Path.open
    def guarded(path,*args,**kwargs):
        assert "sealed" not in path.name.lower()
        assert not (path.name=="panel.json" and "downstream" in path.parts and "final" in path.parts)
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,"open",guarded)
    a=rollout_fixture(p)
    result=review(p,a)
    assert result["stage"]=="final" and result["completed_trials"]==1 and result["expected_trials"]==8800
    assert result["final_state_values_read"] is False and result["weights_read"] is False


def test_fixed_collection_real_npz_trajectories_and_partial_failure(project):
    a=collection_fixture(project)
    result=review(project,a)
    assert result["scientific_complete"] and result["observations"]==30 and result["completed_collection_trajectories"]==10
    assert result["known_policy_calls"]==30


def test_partial_collection_retains_completed_and_unknown_attempts(project):
    a=collection_fixture(project,fail=True)
    result=review(project,a)
    assert not result["scientific_complete"] and result["completed_collection_trajectories"]==2
    assert result["unfinished_attempts_unknown_cost"]==1 and result["cost"]["all_attempt_gpu_seconds"]==3600


def test_collection_panel_cannot_replace_raw_trajectory(project):
    p=project;a=collection_fixture(p)
    path=p.root/a.output/"collection_trials.jsonl"
    events=list(tool.lines(path));events[1]["wall_seconds"]+=.1
    path.write_bytes(b"".join((json.dumps(r)+"\n").encode() for r in events));pull(p,a)
    with pytest.raises(ValueError,match="trajectory differs"):
        review(p,a)


def timing_fixture(p,stage,monkeypatch):
    collection=collection_fixture(p)
    receipt=review(p,collection);p.save(collection.review_relative,receipt)
    freeze=upstream.freeze_project(p)
    p.args.stage=stage;p.args.freeze_directory=freeze;p.args.profile_panel=collection.output+"/panel.json";p.args.collection_review=collection.review_relative
    p.args.execution_manifest="results/formal_main_v2/execution/profile.json"
    rows=p.helper.suite_rows(p.helper.Evidence(p.root),p.registration,"libero_10",p.sources,trials.expected_method_ids())
    p.save(p.args.execution_manifest,p.helper.make_execution(p.registration,"libero_10",rows))
    a=begin(p,job_id="501")
    samples,panel=fp.load_profile_panel(p.root/p.args.profile_panel,development=a.panel,registration=p.registration,dense_identity=rows[0]["identity"])
    a.config.update(panel=panel,panel_sha256=p.scheduler.digest(p.root/p.args.profile_panel))
    p.save(a.output+"/config.json",a.config)
    factories={}
    for row in rows:
        identity=row["identity"]
        @contextmanager
        def factory(identity=identity):
            context=[lambda _: nullcontext()]
            predictor=policy(identity,selection=False,stage_context=lambda name:context[0](name))
            yield ProfileMethod(predictor,dict(identity=identity,cache_scope="none",instruction_cache_enabled=False,future_head_deployed=False,
                precision="base_bfloat16_DIE_float32",attention="sdpa",batch_size=1),lambda value:context.__setitem__(0,value or (lambda _: nullcontext())))
        factories[identity["method_id"]]=factory
    clock=timing.Clock()
    telemetry=lambda:dict(uncontended_device=dict(gpu_uuid="synthetic-GPU",other_compute_processes=0))
    # CPU fixtures test the original serialization and analysis, not filesystem
    # fsync performance. ProfileJournal still serializes every original event;
    # a memory stream is flushed once to the fixture's project-local JSONL.
    import cti_vla.evaluation.profiling as journal_module
    class JournalBuffer(io.StringIO):
        def __exit__(self,*args):
            return False
        def fileno(self):
            return 1
    buffer=JournalBuffer();journal_path=p.root/a.output/"calls.jsonl";original_open=Path.open
    def memory_open(path,*args,**kwargs):
        if path==journal_path and args and args[0] in ("x","a"):
            return buffer
        return original_open(path,*args,**kwargs)
    with monkeypatch.context() as journal_patch:
        journal_patch.setattr(journal_module.os,"fsync",lambda _:None)
        journal_patch.setattr(Path,"open",memory_open)
        journal=ProfileJournal(journal_path,a.config)
        result=fp.profile_formal_methods(samples,factories,pass_name=stage,clock=clock,emit=journal,telemetry=telemetry,timer=clock.timer,synthetic=True)
    journal_path.write_bytes(buffer.getvalue().encode())
    # This is a deliberately constructed CPU server-evidence fixture, never a
    # real result. Production rejects synthetic=true; test that guard separately.
    result.update(synthetic=False,provenance=a.config,checkpoint_unchanged=True,cost=read_profile_cost(p.root/a.output/"calls.jsonl"),
        wall_seconds_including_measurement_overhead=1.,execution_wall_seconds_including_model_loading=2.,hardware_after=telemetry())
    p.save(a.output+"/measurements.json",result)
    summary=fp.summarize_formal_profile(result)
    summary.update(cost=result["cost"],checkpoint_unchanged=True,panel=panel,measurements_sha256=p.scheduler.digest(p.root/a.output/"measurements.json"),
        journal_sha256=p.scheduler.digest(p.root/a.output/"calls.jsonl"),config_sha256=p.scheduler.digest(p.root/a.output/"config.json"),execution_wall_seconds_including_model_loading=2.)
    a.summary=summary;p.save(a.output+"/summary.json",summary)
    emit_adapter(p,a);pull(p,a)
    return a


@pytest.mark.parametrize("stage",["full","components"])
def test_all14300_original_profile_calls_rebuild(stage,project,monkeypatch):
    p=project;a=timing_fixture(p,stage,monkeypatch)
    result=review(p,a)
    assert result["scientific_complete"] and result["attempted_policy_forwards"]==14300
    assert result["reconstructed_summary"]["cost"]["attempts_by_pass"]["warmup"]==1100
    # A SHA-consistent saved summary still cannot change the original raw call.
    journal=p.root/a.output/"calls.jsonl";events=list(tool.lines(journal))
    events[2]["task_name"]="another task"
    journal.write_bytes(b"".join((json.dumps(r)+"\n").encode() for r in events));pull(p,a)
    with pytest.raises(ValueError,match="input/phase"):
        review(p,a)


def test_valid_json_without_lf_is_rejected_and_bytes_preserved(tmp_path):
    path=tmp_path/"journal.jsonl";raw=b'{"event":"start"}';path.write_bytes(raw)
    with pytest.raises(ValueError,match="Incomplete"):
        list(tool.lines(path))
    assert path.read_bytes()==raw


def test_environment_failure_keeps_submitted_action_and_original_cost(project):
    p=project;a=begin(p,status="FAILED")
    ledger=TrialLedger(p.root/a.output/"trials.jsonl",run_signature=p.scheduler.signature(a.config))
    ledger.append(dict(event="invocation",slurm_job_id=a.job["job_id"]))
    class FailingEnv(timing.FakeEnv):
        def step(self,action):
            if self.steps == 10:
                raise RuntimeError("synthetic environment step failed")
            return super().step(action)
    policies={r["identity"]["method_id"]:policy(r["identity"]) for r in a.manifest["methods"]}
    with pytest.raises(RuntimeError,match="infrastructure attempt"):
        trials.evaluate_formal_trials(a.panel,policies,ledger,lambda _: (FailingEnv(),"instruction"),reseed=lambda:None,stop_after=1)
    row=ledger.events[-1]
    assert row["status"]=="infrastructure_error" and row["control_steps"]==0 and len(row["executed_actions"])==1
    provenance={**a.config,"run_signature":p.scheduler.signature(a.config),"checkpoint":a.base,"runtime":{**a.config["runtime"],"slurm_job_id":a.job["job_id"]}}
    a.summary=trials.summarize_formal_trials(a.panel,a.inv["method_ids"],ledger,provenance=provenance)
    p.save(a.output+"/closed_loop_report.json",a.summary);emit_adapter(p,a,failed=True);pull(p,a)
    result=review(p,a)
    assert not result["scientific_complete"] and result["completed_trials"]==0
    assert result["reconstructed_summary"]["cost"]["known_policy_calls"]==1 and result["cost"]["all_attempt_gpu_seconds"]==3600


@pytest.mark.parametrize("historical_mutation",[None,"adapter","job_receipt","slurm_log","pull_receipt"])
def test_explicit_resume_preserves_unknown_old_attempt_and_never_repeats_terminal(project,historical_mutation):
    p=project;old=rollout_fixture(p,fail=True)
    old.review=review(p,old);p.save(old.review_relative,old.review)
    p.args.prior_review=old.review_relative;p.args.resume=True
    upstream.repair_attempt(p,old)
    adapter=upstream.module(p.scheduler.ADAPTER)
    before=adapter.checked_ledger(p.root/old.output/"trials.jsonl",p.scheduler.signature(old.config),panel=old.panel,identifiers=old.inv["method_ids"],validators=trials)
    new=begin(p,job_id="501")
    assert new.output==old.output and new.config==old.config
    ledger=TrialLedger(p.root/new.output/"trials.jsonl",run_signature=p.scheduler.signature(new.config))
    ledger.append(dict(event="invocation",slurm_job_id="501"))
    policies={r["identity"]["method_id"]:policy(r["identity"]) for r in new.manifest["methods"]}
    trials.evaluate_formal_trials(new.panel,policies,ledger,lambda _: (timing.FakeEnv(1),"instruction"),reseed=lambda:None,stop_after=1)
    provenance={**new.config,"run_signature":p.scheduler.signature(new.config),"checkpoint":new.base,"runtime":{**new.config["runtime"],"slurm_job_id":"501"}}
    new.summary=trials.summarize_formal_trials(new.panel,new.inv["method_ids"],ledger,provenance=provenance,checkpoint_unchanged=True)
    p.save(new.output+"/closed_loop_report.json",new.summary);emit_adapter(p,new,before=before);pull(p,new)
    if historical_mutation:
        name={"adapter":old.output+"/adapter_invocations/"+old.adapter["attempt_id"]+".json",
            "job_receipt":"results/formal_main_v2/job_receipts/500.json",
            "slurm_log":"results/slurm/cti-formal-downstream_500.err","pull_receipt":old.pull_relative}[historical_mutation]
        path=p.root/name;path.write_bytes(path.read_bytes()+b" ")
        # The latest transfer is internally consistent; only the old immutable
        # audit chain can detect rewritten prior evidence.
        pull(p,new)
        with pytest.raises(ValueError,match="Historical immutable|historical terminal"):
            review(p,new)
        assert not (p.root/new.review_relative).exists()
        return
    result=review(p,new)
    assert result["completed_trials"]==2 and result["unfinished_attempts_unknown_cost"]==1
    assert result["cost"]["all_attempt_gpu_seconds"]==7200 and result["raw_invocation_job_ids"]==["500","501"]


def test_wrong_development_path_rejected_before_sealed_open(project,monkeypatch):
    p=project;a=rollout_fixture(p)
    index=a.inv["argv"].index("--development-panel")+1
    a.inv["argv"][index]=a.inv["argv"][index].replace("development.json","sealed_final.json")
    p.save(a.job["invocation"],a.inv);a.job["invocation_sha256"]=p.scheduler.digest(p.root/a.job["invocation"])
    receipt_path=f"results/formal_main_v2/job_receipts/{a.job['job_id']}.json"
    receipt=json.loads((p.root/receipt_path).read_text());receipt["invocation_sha256"]=a.job["invocation_sha256"];p.save(receipt_path,receipt)
    pull(p,a)
    original=Path.open
    def guarded(path,*args,**kwargs):
        assert "sealed" not in path.name.lower()
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,"open",guarded)
    with pytest.raises(ValueError,match="registered panel"):
        review(p,a)
