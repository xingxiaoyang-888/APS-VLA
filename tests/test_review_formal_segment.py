"""Synthetic full journals and actual data manifests; no GPU/checkpoint reads."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test_data_formal_windows import project as data_project, freeze
from cti_vla.data import formal_windows

REPO = Path(__file__).resolve().parents[1]


def tool():
    spec = importlib.util.spec_from_file_location("formal_segment_test", REPO / "scripts/review_formal_segment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def lines(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def remove_arm(c, arm):
    path = (c.base / arm).resolve()
    assert c.root.resolve() in path.parents and arm in ("A", "B")
    shutil.rmtree(path)


def close_envelope(c):
    m, root, base = c.m, c.root, c.base
    arm_reports = {}
    for arm in ("A", "B"):
        full, part = base / arm / "training_report.json", base / arm / "progress_report.json"
        arm_reports[arm] = read(full if full.exists() else part) if full.exists() or part.exists() else dict(status="not_started", planned_updates=5000)
    complete = all(r["status"] == "completed" for r in arm_reports.values())
    result_name = "training_summary.json" if complete else "training_progress.json"
    result = dict(schema=m.ROUND, status="completed" if complete else "checkpointed", planned_updates_per_arm=5000,
        job_id="202", requested_arms=["A", "B"], pair_complete=complete, test_opened=False, checkpoint_unchanged=True,
        source_files=c.sources, arms=arm_reports)
    save(base / result_name, result)
    save(base / "finalizations/202_final.json", dict(status="verified", kind="training" if complete else "engineering_segment",
        checkpoint_unchanged=True, job_id="202", result_status=result["status"], result_sha256=m.sha(base / result_name), source_files=c.sources))
    files = sorted(p for p in base.rglob("*") if p.is_file() and "segment_reviews" not in p.parts)
    pair_jobs=[j for j in read(root/m.STATE)["registered_jobs"] if j.get("stage_key")==c.job["stage_key"]]
    files += [root / "results/formal_main_v2/job_receipts/202.json", *[root / f"results/slurm/cti-formal_{j['job_id']}.{e}" for j in pair_jobs for e in ("out", "err")]]
    rows = [dict(relative=p.relative_to(root).as_posix(), path=str(m.P / p.relative_to(root).as_posix()),
        bytes=p.stat().st_size, sha256=m.sha(p), job_ids=[p.stem.split("_")[-1] if p.parent.name=="slurm" else "202"]) for p in files]
    before = save(c.pull.parent / "inventory_before.json", dict(files=rows))
    save(c.pull.parent / "inventory_after.json", dict(files=rows))
    accounting = dict(jobs={j["job_id"]:{k:j[k] for k in ("status","exit_code","elapsed_seconds","allocation")} for j in pair_jobs})
    save(c.pull, dict(schema=m.ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot", final_evidence=True,
        weights_copied=False, sealed_initial_states_copied=False, selected_jobs=[{**c.job, "include_run_root": True}],
        accounting_before=accounting, accounting_after=accounting, inventory_sha256=m.sha(before),
        files=[{**r, "action": "downloaded_verified"} for r in rows]))


def build_arm(c, arm, completed=500, *, job_id="202", attempt="20261016T010000_arm", start=0, resumed=False, fail_tail=False):
    m, manifest = c.m, c.manifest
    base, root = c.base / arm, c.root
    identity = {**c.identity, "training_config_sha256": m.signature({**c.config, "arm": arm})}
    order = m.order_for(manifest["train_window_ids"], c.config["seed"])
    initial = "a" * 64
    save(base / "training_order.json", dict(version=c.constants["FORMAL_ORDER_VERSION"], seed=c.config["seed"],
        train_pool_size=len(manifest["train_window_ids"]), train_pool_sha256=m.signature(manifest["train_window_ids"]),
        samples=order, order_sha256=m.signature(order), initial_scorer_sha256=initial))
    events, evaluations = [], []
    def emit(event, **fields):
        events.append(dict(event=event, job_id=job_id, attempt_id=attempt, **fields))
    def commit(update):
        emit("checkpoint_commit", completed_update=update, resume_sha256=("b" if arm == "A" else "c") * 64, seconds=.1)
    def validate(update):
        emit("validation_start", update=update, windows=len(manifest["validation_window_ids"]))
        ids = set(manifest["validation_window_ids"])
        rows = []
        for window in manifest["windows"]:
            if window["window_id"] in ids:
                rows.append({k: window[k] for k in ("window_id", "episode_id", "task_id")})
        k = c.config["tokens_per_camera"]
        for row in rows:
            row.update(teacher_l1=.2, demonstration_l1=.4, retained_indices=list(range(k)) + list(range(256, 256+k)),
                       normalized_actions=[[0.] * 7 for _ in range(8)])
        rows = sorted(rows, key=lambda r: manifest["validation_window_ids"].index(r["window_id"]))
        by_task = {}
        for row in rows:
            task = str(row["task_id"])
            by_task.setdefault(task, dict(windows=0, teacher_l1=.2, demonstration_l1=.4))["windows"] += 1
        path = base / "attempts" / attempt / f"validation_{update:05d}.json"
        val = dict(arm=arm, update=update, attempt_id=attempt, job_id=job_id, windows=len(rows),
            metric=c.constants["FORMAL_METRIC"], observations=rows, per_task=by_task, tasks=len(by_task),
            validation_metric=.2, demonstration_l1=.4, window_weighted_teacher_l1_diagnostic=.2)
        save(path, val)
        evaluations.append(dict(update=update, validation_metric=.2, artifact_path=str(m.P / path.relative_to(root).as_posix()),
            artifact_sha256=m.sha(path), candidate_path=str(m.PurePosixPath(c.pair["checkpoint_root_server"]) / arm / "candidates" /
                f"{attempt}_update{update:05d}.pt"), candidate_sha256="d" * 64))
        emit("validation_end", update=update, seconds=.5, window_forwards=len(rows), validation_metric=.2, artifact_sha256=m.sha(path))
    emit("attempt_start", identity=identity, completed_update=start, next_sample_cursor=start * 8, resumed=resumed)
    if start == 0 and not resumed:
        commit(0)
        validate(0)
        commit(0)
    for update in range(start + 1, completed + 1):
        emit("update_start", update=update, window_ids=order[(update-1)*8:update*8])
        for micro in range(8):
            for event in ("sample_start", "sample_end"):
                emit(event, update=update, micro_batch_index=micro, window_id=order[(update-1)*8+micro])
        emit("update_end", update=update, alpha=m.alpha(update), forward_backward_samples=8, grad_norm=.1,
            loss=.3 if arm == "A" else .31, action_loss=.3, teacher_l1=.2, demonstration_l1=.4,
            future_mse=.1 if arm == "B" else None, seconds=.1,
            peak_cuda_memory_allocated_bytes=1000,peak_cuda_memory_reserved_bytes=2000)
        if update % 500 == 0:
            validate(update)
        if update % 50 == 0:
            commit(update)
    if fail_tail:
        emit("update_start", update=completed + 1, window_ids=order[completed*8:(completed+1)*8])
        emit("sample_start", update=completed + 1, micro_batch_index=0, window_id=order[completed*8])
        emit("sample_end", update=completed + 1, micro_batch_index=0, window_id=order[completed*8])
        emit("attempt_end", status="failed", completed_update_in_memory=completed)
    else:
        if completed % 50:
            commit(completed)
        emit("attempt_end", status="completed" if completed == 5000 else "checkpointed", completed_update=completed)
    lines(base / "attempts" / attempt / "cost_events.jsonl", events)
    if fail_tail:
        return evaluations
    if resumed:
        old = read(base / "progress_report.json") if (base / "progress_report.json").exists() else None
        if old:
            evaluations = old["evaluations"] + evaluations
    lookup = {r["window_id"]: r for r in manifest["windows"]}
    by_task = {}
    for window in order[:completed*8]:
        by_task.setdefault(str(lookup[window]["task_id"]), []).append(window)
    sampling = {task: dict(samples=len(ids), unique_windows=len(set(ids)), unique_episodes=len({lookup[i]["episode_id"] for i in ids}),
        phase_sample_counts=dict(m.Counter(lookup[i]["phase"] for i in ids))) for task, ids in by_task.items()}
    history = [r for p in sorted((base / "attempts").glob("*/cost_events.jsonl")) for r in [json.loads(line) for line in p.read_text().splitlines()]]
    report = dict(schema=m.ROUND, status="checkpointed", arm=arm, planned_updates=5000, training_updates_completed=completed,
        next_sample_cursor=completed*8, committed_samples=completed*8, vla_parameters_unchanged=True,
        frozen_model_sha256=c.identity["frozen_model_sha256"], final_deployment_receipt_emitted=False, identity=identity,
        resume_checkpoint=str(m.PurePosixPath(c.pair["checkpoint_root_server"]) / arm / "resume.pt"),
        resume_sha256=("b" if arm == "A" else "c") * 64, initial_scorer_sha256=initial, sample_order_sha256=m.signature(order),
        unique_committed_windows=len(set(order[:completed*8])), train_pool_windows=len(manifest["train_window_ids"]),
        committed_sampling_by_task=sampling, effective_epochs=completed*8/len(manifest["train_window_ids"]),
        attempted_forward_backward_samples_completed=sum(r["event"] == "sample_end" for r in history),
        job_ids=sorted({r["job_id"] for r in history}), evaluations=evaluations,
        peak_cuda_memory_allocated_bytes=1000,peak_cuda_memory_reserved_bytes=2000)
    if completed == 5000:
        metadata = dict(schema=m.ROUND, suite=c.config["suite"], seed=c.config["seed"], arm=arm,
            visual_tokens=2*c.config["tokens_per_camera"], per_camera_budgets=[c.config["tokens_per_camera"]]*2,
            training_complete=True, base_frozen=True, checkpoint_unchanged=True, update=0, validation_metric=.2,
            pair_id=m.signature(c.config), config_sha256=identity["training_config_sha256"], training_source_files=c.sources,
            training_source_sha256=m.signature(c.sources), frozen_model_sha256=identity["frozen_model_sha256"],
            window_manifest_sha256=identity["window_manifest_sha256"], data_protocol_sha256=identity["data_protocol_sha256"],
            input_acceptance_sha256=identity["input_acceptance_sha256"], selection_protocol_sha256=identity["selection_protocol_sha256"],
            selection_metric=c.constants["FORMAL_METRIC"])
        receipt = dict(schema=m.ROUND, kind="deployment_receipt", pair_config=c.config, training_config={**c.config, "arm": arm},
            planned_updates=5000, completed_updates=5000, training_complete=True, base_frozen=True, checkpoint_unchanged=True,
            evaluations=evaluations, f01_report_sha256=identity["f01_report_sha256"], metadata=metadata,
            metadata_sha256=m.signature(metadata), checkpoint_sha256="e"*64)
        save(base / "deployment_receipt.json", receipt)
        for key in ("planned_updates", "final_deployment_receipt_emitted", "resume_checkpoint", "resume_sha256"):
            del report[key]
        report.update(status="completed", best_update=0, best_validation_metric=.2,
            best_checkpoint=str(m.PurePosixPath(c.pair["checkpoint_root_server"]) / arm / "best.pt"), best_checkpoint_sha256="e"*64)
    save(base / ("training_report.json" if completed == 5000 else "progress_report.json"), report)
    return report


@pytest.fixture
def setup(data_project, monkeypatch, request):
    from types import SimpleNamespace
    c = SimpleNamespace(m=tool(), root=data_project)
    m, root = c.m, c.root
    budget,seed=getattr(request,"param",(128,17))
    protocol, _, asset_path, _, _ = freeze(root)
    c.manifest = formal_windows.build_formal_windows(protocol)
    save(protocol.path.with_name("windows.json"), c.manifest)
    c.constants = m.literals(REPO / "src/cti_vla/training/formal_future.py")
    c.relative = f"results/formal_main_v2/libero_object/k{budget}/seed{seed}/training"
    c.base = root / c.relative
    real = read(REPO / m.REGISTRATION)
    suite = copy.deepcopy(real["suites"]["libero_object"])
    suite.update(data_manifest=asset_path.relative_to(root).as_posix(), data_manifest_sha256=m.sha(asset_path))
    save(root / suite["model_manifest"], read(REPO / suite["model_manifest"]))
    suite["model_manifest_sha256"] = m.sha(root / suite["model_manifest"])
    c.pair = copy.deepcopy(next(p for p in real["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == ("libero_object",budget,seed)))
    c.config = read(REPO / c.pair["path"])
    save(root / c.pair["path"], c.config)
    c.pair["sha256"] = m.sha(root / c.pair["path"])
    save(root / m.REGISTRATION, dict(schema=m.ROUND, suites={"libero_object": suite}, pairs=[c.pair]))
    for rel in ("src/cti_vla/training/formal_future.py", "src/cti_vla/training/formal_records.py"):
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, root / rel)
    for name in m.ENTRYPOINTS:
        path=root / "scripts" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# synthetic frozen entrypoint\n")
    c.sources={p.relative_to(root).as_posix():m.sha(p) for p in [*sorted((root/"src").rglob("*.py")), *[root/"scripts"/n for n in m.ENTRYPOINTS]]}
    frozen={**c.sources, **{r:m.sha(root/r) for r in (m.REGISTRATION,c.pair["path"],suite["model_manifest"])}}
    source=str(m.P/"snapshots/formal_main_v2_run_synthetic")
    c.source_sha=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
    c.inventory=save(root/"results/formal_main_v2/source/synthetic.json",dict(schema=m.ROUND,files=frozen,source_sha256=c.source_sha,source_root_server=source))
    gate_relative="results/formal_main_v2/libero_object/acceptance/attempt01"
    gates={"input_acceptance.json":dict(window_manifest_sha256=m.sha(protocol.path.with_name("windows.json")),data_protocol_sha256=m.sha(protocol.path),
        source_files=c.sources,frozen_model_sha256="f"*64),f"f01_k{budget}.json":{},"resume_acceptance.json":{},"f03_calls.jsonl":{},"acceptance_complete.json":{}}
    for name,value in gates.items():save(root/gate_relative/name,value)
    gate_files={name:m.sha(root/gate_relative/name) for name in gates}
    save(root/"results/formal_main_v2/libero_object/acceptance/root_review.json",dict(status="passed",suite="libero_object",job_id="101",source_files=c.sources,
        source_sha256=c.source_sha,output_relative=gate_relative,files=gate_files))
    c.job=dict(job_id="202",experiment=m.ROUND,mode="train",suite="libero_object",visual_tokens=budget,training_seed=seed,segment_end=500,
        status="COMPLETED",exit_code="0:0",stage_key=f"libero_object_train_k{budget}_seed{seed}",run_root=str(m.P/c.relative),source_root=source,
        source_sha256=c.source_sha,submitted_utc="2026-10-16T01:00:00+00:00",gpus=1,elapsed_seconds=1200,
        allocation="cpu=7,gres/gpu=1",
        invocation="results/formal_main_v2/invocations/pair.json")
    arguments={"--config":str(m.PurePosixPath(source)/c.pair["path"]),"--protocol":str(m.P/suite["protocol"]),"--windows":str(m.P/suite["windows"]),
        "--checkpoint":suite["model_root_server"],"--asset-manifest":str(m.PurePosixPath(source)/suite["model_manifest"]),"--data-directory":suite["data_root_server"],
        "--cache-directory":str(m.P/".local/formal-hf-libero_object"),"--feature-cache":suite["cache_root_server"],"--training-checkpoints":c.pair["checkpoint_root_server"],
        "--output":str(m.P/c.relative),"--arm":"both","--input-acceptance-report":str(m.P/gate_relative/"input_acceptance.json"),
        "--acceptance-report":str(m.P/gate_relative/f"f01_k{budget}.json"),"--stop-after-updates":"500","--max-wall-seconds":"12600"}
    watched={str(m.P/suite["protocol"]):m.sha(protocol.path),str(m.P/suite["windows"]):m.sha(protocol.path.with_name("windows.json")),
        str(m.PurePosixPath(source)/suite["model_manifest"]):suite["model_manifest_sha256"],str(m.PurePosixPath(source)/c.pair["path"]):c.pair["sha256"],
        **{str(m.P/gate_relative/name):digest for name,digest in gate_files.items()}}
    c.invocation=dict(schema=m.ROUND,stage="train",stage_key=c.job["stage_key"],suite="libero_object",source_root=source,source_sha256=c.source_sha,
        entrypoint="scripts/run_formal_future.py",registration_sha256=m.sha(root/m.REGISTRATION),segment_end=500,
        argv=[item for pair in arguments.items() for item in pair],watched_files=watched)
    save(root/c.job["invocation"],c.invocation)
    c.job["invocation_sha256"]=m.sha(root/c.job["invocation"])
    c.state=dict(registered_jobs=[dict(job_id="101",experiment=m.ROUND,mode="acceptance",status="COMPLETED",exit_code="0:0"),c.job])
    save(root/m.STATE,c.state)
    save(root/"results/formal_main_v2/job_receipts/202.json",dict(schema=m.ROUND,job_id="202",stage="train",stage_key=c.job["stage_key"],exit_code=0,
        invocation_sha256=c.job["invocation_sha256"],source_sha256=c.source_sha,wall_seconds=1190.))
    for ext in ("out","err"):
        p=root/f"results/slurm/cti-formal_202.{ext}";p.parent.mkdir(parents=True,exist_ok=True);p.write_text("synthetic retained log\n")
    cache=dict(suite="libero_object",model_revision=c.config["model_revision"],asset_manifest_sha256=suite["model_manifest_sha256"],
        data_protocol_sha256=m.sha(protocol.path),window_manifest_sha256=m.sha(protocol.path.with_name("windows.json")),dataset_statistics_sha256="0"*64,producer_source_files=c.sources)
    c.identity=dict(window_manifest_sha256=cache["window_manifest_sha256"],data_protocol_sha256=cache["data_protocol_sha256"],
        selection_protocol_sha256=m.signature(c.config["selection"]),input_acceptance_sha256=gate_files["input_acceptance.json"],f01_report_sha256=gate_files[f"f01_k{budget}.json"],
        resume_acceptance_sha256=gate_files["resume_acceptance.json"],resume_journal_sha256=gate_files["f03_calls.jsonl"],frozen_model_sha256="f"*64,
        asset_manifest_sha256=suite["model_manifest_sha256"],training_source_files=c.sources,cache_identity=cache,
        training_order_version=c.constants["FORMAL_ORDER_VERSION"],pair_config_sha256=m.signature(c.config),training_version=c.constants["FORMAL_TRAINING_VERSION"],
        training_numerics=c.constants["FORMAL_NUMERICS"],specification=dict(seed=seed,tokens_per_camera=budget//2,updates=5000,effective_batch=8,
            validation_every=500,checkpoint_every=50,learning_rate=.0001,weight_decay=.01,gradient_clip_norm=1.,alpha_start=2.,alpha_end=.1,future_weight=.1))
    save(c.base/"registered_config.json",c.config)
    for arm in ("A","B"):build_arm(c,arm)
    cache_version=m.literals(root/"src/cti_vla/training/formal_records.py")["FORMAL_CACHE_VERSION"]
    lines(c.base/"cache_events/202_cache.jsonl",[dict(event="cache_hit",job_id="202",cache_identity_sha256=m.signature({"cache_version":cache_version,**cache}),seconds=.1)])
    c.pull=root/"results/formal_main_v2/pulls/synthetic/receipt.json"
    close_envelope(c)
    monkeypatch.setattr(m,"probe_registered_resume",lambda specs:[dict(arm=s["arm"],path=s["path"],exists=s["must_exist"],bytes=100,sha256=s["sha256"]) for s in specs])
    c.review=lambda **kw:m.review("202",root=root,source_inventory=c.inventory,pull_receipt=c.pull,**kw)
    return c


def test_local_review_is_readonly_and_does_not_claim_server_sha(setup,monkeypatch):
    c=setup
    monkeypatch.setattr(c.m,"probe_registered_resume",lambda specs:pytest.fail("Default review must not use SSH"))
    result=c.review()
    assert result["status"]=="local_passed_remote_required"
    assert result["allowed_next_segment_end"]==1000 and result["completed_by_arm"]=={"A":500,"B":500}
    assert not (c.base/"segment_reviews").exists()


def test_explicit_root_sha_check_publishes_once(setup):
    c=setup
    result=c.review(verify_server_resume=True)
    assert result["status"]=="passed" and result["attempted_forward_backward_samples"]==8000
    assert c.review(verify_server_resume=True)==result


@pytest.mark.parametrize("bad",["missing","different_sha"])
def test_started_arm_cannot_silently_restart_if_resume_missing_or_changed(setup,monkeypatch,bad):
    c=setup
    def probe(specs):
        return [dict(arm=s["arm"],path=s["path"],exists=bad!="missing",bytes=100,sha256="0"*64) for s in specs]
    monkeypatch.setattr(c.m,"probe_registered_resume",probe)
    with pytest.raises(ValueError,match="existence|recovery file"):
        c.review(verify_server_resume=True)
    assert not (c.base/"segment_reviews").exists()


def test_incomplete_b_only_allows_original_500_boundary(setup):
    c=setup
    remove_arm(c,"B")
    build_arm(c,"B",247)
    close_envelope(c)
    result=c.review(verify_server_resume=True)
    assert result["completed_by_arm"]=={"A":500,"B":247}
    assert result["allowed_next_segment_end"]==500 and result["continuation"]=="complete_original_boundary_only"


def test_not_started_b_may_initialize_when_completing_original_boundary(setup):
    c=setup
    remove_arm(c,"B")
    close_envelope(c)
    result=c.review(verify_server_resume=True)
    assert result["allowed_next_segment_end"]==500
    assert result["server_resume_checklist"][1]["must_exist"] is False


@pytest.mark.parametrize("setup",[(64,23),(256,41)],indirect=True)
def test_registered_other_budgets_and_seeds_use_dynamic_validation_panel(setup):
    c=setup;result=c.review()
    assert result["visual_tokens"]==c.job["visual_tokens"] and result["seed"]==c.job["training_seed"]
    assert len(c.manifest["validation_window_ids"])!=165
    assert result["allowed_next_segment_end"]==1000


@pytest.mark.parametrize("field,value",[("next_sample_cursor",3999),("initial_scorer_sha256","9"*64),
    ("attempted_forward_backward_samples_completed",3999),("resume_sha256","9"*64)])
def test_progress_corruption_fails_even_after_rehashing_pull(setup,field,value):
    c=setup;p=c.base/"A/progress_report.json";r=read(p);r[field]=value;save(p,r);close_envelope(c)
    with pytest.raises(ValueError):c.review(verify_server_resume=True)
    assert not (c.base/"segment_reviews").exists()


@pytest.mark.parametrize("mutation",["alpha500","sample_order","missing_sample_end","missing_commit","fresh_restart"])
def test_actual_journal_mutations_fail_after_valid_pull_rehash(setup,mutation):
    c=setup;p=next((c.base/"A/attempts").glob("*/cost_events.jsonl"));rows=[json.loads(x) for x in p.read_text().splitlines()]
    if mutation=="alpha500":next(r for r in rows if r["event"]=="update_end" and r["update"]==500)["alpha"]=.1
    if mutation=="sample_order":next(r for r in rows if r["event"]=="update_start")["window_ids"][0]="unknown"
    if mutation=="missing_sample_end":rows.pop(next(i for i,r in enumerate(rows) if r["event"]=="sample_end"))
    if mutation=="missing_commit":rows=[r for r in rows if not(r["event"]=="checkpoint_commit" and r["completed_update"]==500)]
    if mutation=="fresh_restart":rows[0]["resumed"]=True
    lines(p,rows);close_envelope(c)
    with pytest.raises(ValueError):c.review()


@pytest.mark.parametrize("mutation",["macro","token_budget","missing_window","changed_initial_behavior"])
def test_hard_validation_checks_full_panel_packing_and_macro(setup,mutation):
    c=setup;p=next((c.base/"B/attempts").glob("*/validation_00000.json"));v=read(p)
    if mutation=="macro":v["validation_metric"]=.3
    if mutation=="token_budget":v["observations"][0]["retained_indices"].pop()
    if mutation=="missing_window":v["observations"].pop()
    if mutation=="changed_initial_behavior":v["observations"][0]["normalized_actions"][0][0]=.1
    save(p,v)
    lp=p.parent/"cost_events.jsonl";rows=[json.loads(x) for x in lp.read_text().splitlines()]
    for r in rows:
        if r["event"]=="validation_end" and r["update"]==0:r["artifact_sha256"]=c.m.sha(p);r["validation_metric"]=v["validation_metric"]
    lines(lp,rows)
    rp=c.base/"B/progress_report.json";r=read(rp);r["evaluations"][0].update(artifact_sha256=c.m.sha(p),validation_metric=v["validation_metric"]);save(rp,r)
    close_envelope(c)
    with pytest.raises(ValueError):c.review()


def test_stale_pull_or_nonterminal_registration_fails(setup):
    c=setup
    c.state["registered_jobs"][-1]["status"]="RUNNING";save(c.root/c.m.STATE,c.state)
    with pytest.raises(ValueError,match="Terminal"):c.review()
    c.state["registered_jobs"][-1]["status"]="COMPLETED";save(c.root/c.m.STATE,c.state)
    p=c.base/"registered_config.json";p.write_text(p.read_text()+"\n")
    with pytest.raises(ValueError,match="SHA-pulled"):c.review()


def test_import_and_local_audit_do_not_import_torch(setup):
    c=setup
    code="import importlib.util,sys; s=importlib.util.spec_from_file_location('segment',sys.argv[1]); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.review('202',root=sys.argv[2],source_inventory=sys.argv[3],pull_receipt=sys.argv[4]); assert 'torch' not in sys.modules"
    result=subprocess.run([sys.executable,"-c",code,str(REPO/"scripts/review_formal_segment.py"),str(c.root),str(c.inventory),str(c.pull)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_probe_rejects_nonpair_or_unregistered_paths_without_ssh():
    m=tool()
    with pytest.raises(ValueError):m.probe_registered_resume([dict(arm="A",path="/elsewhere/resume.pt")])
    with pytest.raises(ValueError):m.probe_registered_resume([dict(arm=a,path=f"/elsewhere/{a}/resume.pt") for a in ("A","B")])


def update_invocation_and_state(c, *, target=None, resumed=False):
    if target is not None:
        c.job["segment_end"]=target
        c.invocation["segment_end"]=target
        index=c.invocation["argv"].index("--stop-after-updates")+1
        c.invocation["argv"][index]=str(target)
    if resumed:c.invocation["argv"].append("--resume")
    save(c.root/c.job["invocation"],c.invocation)
    c.job["invocation_sha256"]=c.m.sha(c.root/c.job["invocation"])
    save(c.root/c.m.STATE,c.state)
    p=c.root/"results/formal_main_v2/job_receipts/202.json";r=read(p);r["invocation_sha256"]=c.job["invocation_sha256"];save(p,r)


def test_a_clean_500_then_b_failure_in_same_job_retains_replay_and_allocation_bill(setup):
    c=setup
    for arm in ("A","B"):remove_arm(c,arm)
    prior={**c.job,"job_id":"201","status":"FAILED","exit_code":"1:0","submitted_utc":"2026-10-16T00:00:00+00:00","elapsed_seconds":200}
    c.state["registered_jobs"].insert(-1,prior)
    for ext in ("out","err"):(c.root/f"results/slurm/cti-formal_201.{ext}").write_text("retained failure log\n")
    build_arm(c,"A",500,job_id="201",attempt="20261016T000000_first")
    old_eval=build_arm(c,"B",50,job_id="201",attempt="20261016T000000_first",fail_tail=True)
    build_arm(c,"A",500,start=500,resumed=True)
    build_arm(c,"B",500,start=50,resumed=True)
    p=c.base/"B/progress_report.json";r=read(p);r["evaluations"]=old_eval+r["evaluations"];save(p,r)
    save(c.base/"failures/201_retained.json",dict(status="failed",error="synthetic failed sample"))
    update_invocation_and_state(c,resumed=True)
    close_envelope(c)
    result=c.review(verify_server_resume=True)
    assert result["attempted_forward_backward_samples"]==8001
    assert result["replayed_or_uncommitted_samples"]==1
    assert result["pair_allocated_gpu_seconds"]==1400
    assert result["allowed_next_segment_end"]==1000


def test_missing_intermediate_commit_is_not_masked_by_final_commit(setup):
    c=setup;p=next((c.base/"A/attempts").glob("*/cost_events.jsonl"));rows=[json.loads(x) for x in p.read_text().splitlines()]
    lines(p,[r for r in rows if not(r["event"]=="checkpoint_commit" and r["completed_update"]==250)])
    close_envelope(c)
    with pytest.raises(ValueError,match="50-update commit"):c.review()


def test_true_5000_completion_points_to_receipts_and_never_5500(setup):
    c=setup
    for arm in ("A","B"):
        remove_arm(c,arm)
        build_arm(c,arm,5000)
    update_invocation_and_state(c,target=5000)
    close_envelope(c)
    result=c.review(verify_server_resume=True)
    assert result["allowed_next_segment_end"] is None and result["resume_required"] is False
    assert result["continuation"]=="formal_training_complete_no_extension"
    assert len(result["completed_training_receipts"])==2


def test_wrong_final_best_point_is_rejected_even_with_valid_receipt_hash(setup):
    c=setup
    for arm in ("A","B"):
        remove_arm(c,arm)
        build_arm(c,arm,5000)
    update_invocation_and_state(c,target=5000)
    path=c.base/"A/deployment_receipt.json";value=read(path);value["metadata"]["update"]=500
    value["metadata_sha256"]=c.m.signature(value["metadata"]);save(path,value)
    close_envelope(c)
    with pytest.raises(ValueError,match="Selected checkpoint metadata"):c.review()
