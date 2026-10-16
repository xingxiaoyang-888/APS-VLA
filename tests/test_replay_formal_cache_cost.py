"""Synthetic evidence only; no tensors, network, simulator or GPU imports."""
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cache_replay_under_test", ROOT / "scripts/replay_formal_cache_cost.py")
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def ref(root, name, value, *, lines=False):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(x) + "\n" for x in value) if lines else json.dumps(value)
    path.write_text(text, encoding="utf-8")
    return dict(path=name, sha256=r.digest(path))


def key(ns, logical):
    return hashlib.sha256((ns + ":" + logical).encode()).hexdigest()


def sizes(ns, names, amount=10, black=5):
    return [dict(namespace=ns, logical_key="window:" + n, key=key(ns, "window:" + n), bytes=amount) for n in names] + [
        dict(namespace=ns, logical_key="shared:black-image", key=key(ns, "shared:black-image"), bytes=black)]


def matrix():
    return dict(schema=r.SCHEMA, suite_order=list(r.SUITES), budgets=[256, 128, 64], seeds=[17, 23, 41],
        arms=["A", "B"], training_arms=72,
        suites={s: dict(windows=f"manifests/{s}/windows.json", protocol=f"manifests/{s}/protocol.json",
            model_revision="revision-" + s, model_manifest_sha256="a" * 64) for s in r.SUITES},
        pairs=[dict(suite=s, visual_tokens=b, seed=n, path=f"configs/{s}_k{b}_s{n}.json", sha256="f" * 64,
            run_root_server=f"/project/results/formal_main_v2/{s}/k{b}/seed{n}")
            for s in r.SUITES for b in (256, 128, 64) for n in (17, 23, 41)])


def cache_rows(ns="a" * 64, logical="window:x", *, job="100", publish=True, arm="A", phase="training", update=1):
    context = dict(job_id=job, cache_identity_sha256=ns, arm=arm, phase=phase, update=update)
    identity = dict(logical_key=logical, key=key(ns, logical))
    if not publish:
        return [dict(event="cache_hit", seconds=.03, time_unix_ns=1, **context, **identity)]
    if logical == "shared:black-image":
        generation = [dict(event="shared_black_generate_start"), dict(event="shared_black_generate_end", seconds=.1, vision_forwards=1)]
    else:
        generation = [dict(event="feature_generate_start", window_id=logical[7:], split="train"),
            dict(event="feature_generate_end", window_id=logical[7:], seconds=.1, teacher_forwards=1,
                vision_forwards=2, future_target_detached=True, window_alignment_validated=True)]
    rows = [dict(event="cache_miss", **identity), *generation,
            dict(event="cache_publish", seconds=.2, bytes=10, sha256="b" * 64, **identity)]
    return [dict(**x, **context, time_unix_ns=i + 1) for i, x in enumerate(rows)]


def parse(tmp_path, rows):
    f = ref(tmp_path, "cache.jsonl", rows, lines=True)
    return r.parse_cache(r.Evidence(tmp_path), f, job="100", namespace="a" * 64, windows={"x": {}},
                         hardware={"identity_sha256": "h" * 64, "gpu_class": "l40"})


@pytest.mark.parametrize("name", ["../outside.json", "sealed/data.json", "checkpoints/receipt.json",
    "weights/fake.json", "initial_states/dev.json", "test/values.json", "a/panel.json", "a/value.pt", "C:/absolute.json"])
def test_reject_sensitive_path_before_open(tmp_path, name):
    with pytest.raises(ValueError):
        r.Evidence(tmp_path).path(dict(path=name, sha256="0" * 64))


@pytest.mark.parametrize("option", ["--registration", "--evidence"])
@pytest.mark.parametrize("name", ["../outside.json", "sealed/data.json", "checkpoints/receipt.json",
    "weights/fake.json", "initial_states/dev.json", "test/values.json", "tests/values.json",
    "a/panel.json", "a/PaNeL.JsOn", "a/init_states_test.json", "a/INIT_STATES_TEST.JSON",
    "a/value.pt", "a/value.txt", "test/../allowed.json"])
def test_cli_rejects_forbidden_before_stat_or_digest(tmp_path, monkeypatch, capsys, option, name):
    allowed_registration = tmp_path / "registration.json"
    checked, hashed = [], []
    def is_file(path):
        assert path == allowed_registration, "forbidden input reached is_file"
        checked.append(path)
        return True
    def digest(path):
        assert path in (allowed_registration, Path(r.__file__)), "forbidden input reached digest"
        hashed.append(path)
        return "f" * 64
    monkeypatch.setattr(Path, "is_file", is_file)
    monkeypatch.setattr(r, "digest", digest)
    monkeypatch.setattr(r.sys, "argv", ["cache-replay", "--project-root", str(tmp_path),
        "--registration", "registration.json", option, name])
    assert r.main() == 2
    assert json.loads(capsys.readouterr().out)["status"] == "rejected_evidence"
    assert checked == ([allowed_registration] if option == "--evidence" else [])
    assert hashed == ([allowed_registration, Path(r.__file__)] if option == "--evidence" else [Path(r.__file__)])


def test_top_level_reference_allows_project_metadata_and_missing_file(tmp_path):
    expected = ref(tmp_path, "input.json", {"x": 1})
    assert r.top_level_reference(tmp_path, Path("input.json")) == expected
    assert r.top_level_reference(tmp_path, tmp_path / "input.json") == expected
    assert r.top_level_reference(tmp_path, Path("missing.json")) == dict(path="missing.json", sha256="0" * 64)


def test_sha_and_changed_input_rejected(tmp_path):
    f = ref(tmp_path, "data.json", {"x": 1}); reader = r.Evidence(tmp_path)
    assert reader.read(f) == {"x": 1}
    (tmp_path / f["path"]).write_text('{"x":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        reader.unchanged()
    with pytest.raises(ValueError, match="SHA"):
        r.Evidence(tmp_path).read(f)


def test_missing_reference_pending(tmp_path):
    with pytest.raises(r.Pending):
        r.Evidence(tmp_path).read(None)


def test_jsonl_tail_never_salvaged(tmp_path):
    p = tmp_path / "journal.jsonl"; p.write_bytes(b'{"a":1}\n{"b":2}')
    reader = r.Evidence(tmp_path); rows = reader.lines(dict(path=p.name, sha256=r.digest(p)))
    assert len(rows) == 1 and reader.tails[0]["line"] == 2
    p.write_bytes(b'{"a":1}\n{broken}\n')
    with pytest.raises(ValueError, match="non-tail"):
        r.Evidence(tmp_path).lines(dict(path=p.name, sha256=r.digest(p)))


def test_no_ram_touch_to_disk_and_segment_reset():
    ns = "a" * 64
    # a is a RAM hit before c. Its disk position must remain older than b;
    # v then evicts a, making the next process's first a a miss.
    result = r.replay_counts(["a", "b", "a", "c", "a", "x", "x", "x"], ["v"], ns,
        sizes(ns, ["a", "b", "c", "x", "v"]), capacity=35, segment=4, batch=1)
    assert result["counts"] == dict(black_publish=1, window_requests=11, window_publish=7,
                                   ram_hits=3, evictions=4, black_hit=1, window_hit=1)
    assert result["peak_disk_bytes"] == 35
    assert all(op["key"] != key(ns, "shared:black-image") or op["operation"] in ("cache_hit", "cache_publish") for op in result["operations"])


def test_5000_contract_ten_black_accesses_and_eleven_validations():
    ns = "a" * 64; order = ["a", "b", "c", "d"] * 10000; validation = ["v", "w"]
    result = r.replay_counts(order, validation, ns, sizes(ns, set(order + validation)))
    assert result["counts"]["window_requests"] == 40000 + 11 * 2
    assert result["counts"]["black_publish"] == 1 and result["counts"]["black_hit"] == 9
    assert result["counts"].get("evictions", 0) == 0


def test_independent_arms_do_not_share_disk_or_black():
    ns = "a" * 64; data = sizes(ns, ["x", "v"])
    a = r.replay_counts(["x"] * 8, ["v"], ns, data, segment=8, batch=1)
    b = r.replay_counts(["x"] * 8, ["v"], ns, data, segment=8, batch=1)
    assert a == b and a["counts"]["black_publish"] == 1


@pytest.mark.parametrize("mutate", ["missing", "conflict"])
def test_no_size_proxies_or_conflict_resolution(mutate):
    ns = "a" * 64; data = sizes(ns, ["x", "v"])
    if mutate == "missing":
        data.pop(0)
    else:
        data.append({**data[0], "bytes": 11})
    result = r.replay_counts(["x"] * 8, ["v"], ns, data, segment=8, batch=1)
    assert result["status"] == "unknown_sizes" and result["counts"] is None
    assert result["missing_sizes"] if mutate == "missing" else result["conflicting_sizes"]


def test_foreign_namespace_sizes_cannot_fill_missing_key():
    result = r.replay_counts(["x"] * 8, ["v"], "a" * 64, sizes("b" * 64, ["x", "v"]), segment=8, batch=1)
    assert len(result["missing_sizes"]) == 3


def test_pinned_black_is_capacity_not_free():
    with pytest.raises(ValueError, match="pinned"):
        r.replay_counts(["x"] * 8, ["v"], "a" * 64, sizes("a" * 64, ["x", "v"], amount=10, black=9), capacity=18, segment=8, batch=1)


def test_cache_publication_requires_real_complete_generation(tmp_path):
    result = parse(tmp_path, cache_rows())
    assert result["requests"][("A", "training", 1)] == ["x"]
    assert result["observations"][0]["seconds"] == .2  # .1 nested generation is not added.
    assert result["observations"][0]["source"]["line"] == 4
    assert result["sizes"][0]["bytes"] == 10


@pytest.mark.parametrize("mutation", ["wrong_key", "wrong_namespace", "no_generation_end", "wrong_producer", "negative_time", "duplicate_miss"])
def test_cache_corruption_rejected(tmp_path, mutation):
    rows = cache_rows()
    if mutation == "wrong_key": rows[0]["key"] = "c" * 64
    elif mutation == "wrong_namespace": rows[0]["cache_identity_sha256"] = "c" * 64
    elif mutation == "no_generation_end": rows.pop(2)
    elif mutation == "wrong_producer": rows[2]["vision_forwards"] = 1
    elif mutation == "negative_time": rows[-1]["seconds"] = -1
    else: rows.insert(1, rows[0].copy())
    with pytest.raises(ValueError): parse(tmp_path, rows)


def test_miss_is_not_invented_publication_or_size(tmp_path):
    result = parse(tmp_path, cache_rows()[:-1])
    assert result["sizes"] == [] and result["observations"] == []
    assert result["unknown"][0]["kind"] == "ambiguous_unlogged_commit_or_incomplete_generation"


def test_hit_without_publication_cannot_supply_size(tmp_path):
    result = parse(tmp_path, cache_rows(publish=False))
    assert result["sizes"] == [] and len(result["observations"]) == 1


def test_all_spikes_preserved_and_no_other_key_or_hardware_proxy():
    replay = dict(status="exact_under_registered_no_failure_schedule", operations=[dict(key="k", operation="cache_hit", count=3)])
    obs = [dict(namespace="n", key="k", operation="cache_hit", hardware={"identity_sha256": "h"},
                seconds=t, source=dict(sha256="a" * 64, line=i+1)) for i, t in enumerate([.1, .2, 9.82])]
    value = r.calibrate(replay, "n", obs, "h")
    assert value["complete_seconds"]["mean"] == pytest.approx(10.12)
    assert value["calibration"][0]["maximum"] == 9.82 and len(value["calibration"][0]["sources"]) == 3
    for target_ns, target_hw in (("wrong", "h"), ("n", "different"), ("n", None)):
        missing = r.calibrate(replay, target_ns, obs, target_hw)
        assert missing["complete_seconds"] is None and missing["covered_operations"] == 0


def test_unknown_operation_does_not_turn_into_zero():
    replay = dict(status="exact_under_registered_no_failure_schedule", operations=[dict(key="k", operation="cache_publish", count=1)])
    obs = [dict(namespace="n", key="k", operation="cache_hit", hardware={"identity_sha256": "h"}, seconds=.1, source={})]
    value = r.calibrate(replay, "n", obs, "h")
    assert value["complete_seconds"] is None and value["covered_operation_seconds"] is None


def test_partial_calibration_is_not_complete_total():
    replay = dict(status="exact_under_registered_no_failure_schedule", operations=[
        dict(key="k", operation="cache_hit", count=2), dict(key="q", operation="cache_hit", count=2)])
    obs = [dict(namespace="n", key="k", operation="cache_hit", hardware={"identity_sha256": "h"}, seconds=.1, source={})]
    value = r.calibrate(replay, "n", obs, "h")
    assert value["complete_seconds"] is None and value["operation_coverage"] == .5
    assert value["covered_operation_seconds"]["mean"] == pytest.approx(.2)


def test_job_hardware_never_inherits_another_jobs_runtime(tmp_path):
    bill = dict(allocation="cpu=7,gres/gpu:l40=1,gres/gpu=1,mem=64G,node=1", gpus=1, node="gpu4025")
    value = r.job_hardware(r.Evidence(tmp_path), {}, {"job_id": "100"}, bill, None)
    assert value["gpu_class"] == "l40" and value["node"] == "gpu4025"
    assert value["identity_sha256"] is None and "torch_version" in value["missing"]


def test_actual_bill_unique_and_separate(tmp_path):
    jobs = [dict(job_id="100", experiment=r.SCHEMA, mode="train", suite="libero_10", run_root="/root", source_sha256="a", invocation_sha256="b")]
    state = ref(tmp_path, "supervision.json", {"registered_jobs": jobs})
    bill = ref(tmp_path, "accounting.json", {"jobs": [dict(**jobs[0], status="FAILED", elapsed_seconds=19, gpus=1)]})
    _, _, total = r.read_accounting(r.Evidence(tmp_path), dict(supervisor_state=state, accounting=bill), matrix())
    assert total["gpu_seconds"] == total["failed_gpu_seconds"] == 19
    payload = json.loads((tmp_path / bill["path"]).read_text()); payload["jobs"] *= 2
    bill = ref(tmp_path, "accounting.json", payload)
    with pytest.raises(ValueError, match="duplicate"):
        r.read_accounting(r.Evidence(tmp_path), dict(supervisor_state=state, accounting=bill), matrix())


def test_missing_final_evidence_never_completes(tmp_path):
    registration = ref(tmp_path, "registration.json", matrix())
    result = r.analyze(r.Evidence(tmp_path), registration, None)
    assert result["status"] == "pending_evidence" and not result["arms"]
    assert result["missing"] and result["actual_allocation"] is None


@pytest.mark.parametrize("field,value", [("budgets", [128]), ("training_arms", 2), ("seeds", [17])])
def test_no_pilot_or_matrix_shortcuts(field, value):
    reg = matrix(); reg[field] = value
    with pytest.raises(ValueError): r.check_registration(reg)


@pytest.fixture
def arm_evidence(tmp_path):
    reg = matrix(); suite = "libero_10"; pair = next(p for p in reg["pairs"] if (p["suite"], p["visual_tokens"], p["seed"]) == (suite,128,17))
    train, val = ["t" + str(i) for i in range(20)], ["v" + str(i) for i in range(10)]
    rows = {wid: dict(window_id=wid, split=split, task_id=i % 10, episode_id=split+str(i))
        for split, values in (("train",train),("validation",val)) for i,wid in enumerate(values)}
    wm = dict(train=train, validation=val, rows=rows, windows_sha256="1"*64, protocol_sha256="2"*64)
    config = dict(schema=r.SCHEMA, suite=suite, seed=17, tokens_per_camera=64, model_revision=reg["suites"][suite]["model_revision"],
        training=dict(updates=5000,effective_batch=8),selection=dict(updates=list(range(0,5001,500))))
    pair["sha256"] = ref(tmp_path,pair["path"],config)["sha256"]
    sources = {"src/cti_vla/training/formal_records.py":"3"*64}
    cache_identity = dict(suite=suite, model_revision=config["model_revision"],asset_manifest_sha256="a"*64,
        window_manifest_sha256=wm["windows_sha256"],data_protocol_sha256=wm["protocol_sha256"],
        dataset_statistics_sha256="4"*64,producer_source_files=sources)
    identity = dict(pair_config_sha256=r.signature(config),training_config_sha256=r.signature({**config,"arm":"A"}),
        window_manifest_sha256=wm["windows_sha256"],data_protocol_sha256=wm["protocol_sha256"],
        training_source_files=sources,cache_identity=cache_identity,frozen_model_sha256="5"*64,f01_report_sha256="6"*64)
    order = r.sample_order(train,17)
    report = dict(schema=r.SCHEMA,arm="A",identity=identity,status="checkpointed",training_updates_completed=0,
        next_sample_cursor=0,committed_samples=0,train_pool_windows=len(train),vla_parameters_unchanged=True,
        frozen_model_sha256="5"*64,sample_order_sha256=r.signature(order),initial_scorer_sha256="7"*64,evaluations=[{"update":0}],
        attempted_forward_backward_samples_completed=0,job_ids=["100"])
    ordering = dict(version=r.ORDER_VERSION,seed=17,samples=order,order_sha256=r.signature(order),
        train_pool_sha256=r.signature(train),train_pool_size=len(train),initial_scorer_sha256="7"*64)
    item=dict(suite=suite,visual_tokens=128,seed=17,arm="A",report=ref(tmp_path,"training/A/progress_report.json",report),
        training_order=ref(tmp_path,"training/A/training_order.json",ordering))
    arm=r.check_arm(r.Evidence(tmp_path),item,pair,wm,reg,{})
    job=dict(job_id="100",mode="train",suite=suite,run_root=pair["run_root_server"]+"/training")
    return dict(root=tmp_path,reg=reg,pair=pair,wm=wm,item=item,arm=arm,job=job,report=report)


def test_partial_arm_stays_incomplete(arm_evidence):
    assert arm_evidence["arm"]["complete"] is False


@pytest.mark.parametrize("mutation", ["namespace","order","cursor","data"])
def test_arm_identity_mismatch_rejected(arm_evidence,mutation):
    f=arm_evidence; report=deepcopy(f["report"])
    if mutation=="namespace":report["identity"]["cache_identity"]["producer_source_files"]={"wrong":"3"*64}
    elif mutation=="order":report["sample_order_sha256"]="8"*64
    elif mutation=="cursor":report["next_sample_cursor"]=8
    else:report["identity"]["data_protocol_sha256"]="9"*64
    item={**f["item"],"report":ref(f["root"],"training/A/progress_report.json",report)}
    with pytest.raises(ValueError):r.check_arm(r.Evidence(f["root"]),item,f["pair"],f["wm"],f["reg"],{})


def test_actual_attempt_requests_and_failure_prefix(arm_evidence):
    f=arm_evidence;arm=f["arm"];order=arm["order"];aid="attempt1"
    base=dict(job_id="100",attempt_id=aid)
    payload=[dict(event="attempt_start",identity=arm["identity"],completed_update=0,next_sample_cursor=0),
        dict(event="update_start",update=1,window_ids=order[:8]),
        dict(event="sample_start",update=1,micro_batch_index=0,window_id=order[0]),
        dict(event="sample_end",update=1,micro_batch_index=0,window_id=order[0]),
        dict(event="attempt_end",status="failed",completed_update_in_memory=0,seconds=.4)]
    payload=[dict(**x,**base,attempt_elapsed_seconds=i*.1) for i,x in enumerate(payload)]
    journal=ref(f["root"],"attempt/cost_events.jsonl",payload,lines=True)
    value=r.parse_attempt(r.Evidence(f["root"]),journal,arm,{"100":f["job"]},{"100":{"status":"FAILED"}})
    assert value["sample_ends"]==1 and not value["completed_updates"] and value["failed_or_partial"]
    payload[2]["window_id"]="wrong";journal=ref(f["root"],"attempt/cost_events.jsonl",payload,lines=True)
    with pytest.raises(ValueError,match="microbatch"):
        r.parse_attempt(r.Evidence(f["root"]),journal,arm,{"100":f["job"]},{"100":{"status":"FAILED"}})


def test_same_size_republication_retains_all_timing_sources(tmp_path):
    first=cache_rows();second=cache_rows()
    for row in second:row["time_unix_ns"]+=4
    result=parse(tmp_path,first+second)
    assert len(result["observations"])==2 and [x["source"]["line"] for x in result["observations"]]==[4,8]
    assert len(result["sizes"])==2


def test_source_has_no_execution_backdoors():
    text=(ROOT/"scripts/replay_formal_cache_cost.py").read_text(encoding="utf-8")
    for forbidden in ("import torch", "import subprocess", "import requests", "torch.load(", "ssh ", "sbatch "):
        assert forbidden not in text


def test_shared_observation_index_preserves_spike_lines_without_arm_copies():
    idx=r.ObservationIndex()
    for n,t in enumerate([.1,.2,9.82],1):
        idx.add(dict(namespace="n",key="k",operation="cache_hit",seconds=t,job_id="100",
            hardware={"identity_sha256":"h"},source=dict(path="cache.jsonl",sha256="a"*64,line=n)))
    replay=dict(status="exact_under_registered_no_failure_schedule",operations=[dict(key="k",operation="cache_hit",count=3)])
    value=r.calibrate(replay,"n",idx,"h",compact=True)
    assert value["complete_seconds"]["mean"]==pytest.approx(10.12)
    assert "calibration" not in value and "unknown" not in value
    shared=idx.summary()
    assert shared["journals"][0]["completed_operation_lines"]==[1,2,3]
    assert shared["eligible_calibration"][0]["maximum"]==9.82


def test_complete_40000_writer_shaped_attempt(arm_evidence):
    """Real parser sees all40000 samples once; matrix test needn't repeat72x."""
    f=arm_evidence;arm=f["arm"];aid="full_attempt"
    p=f["root"]/"full_attempt/cost_events.jsonl";p.parent.mkdir()
    clock=0
    with p.open("w",encoding="utf-8") as handle:
        def event(name,**fields):
            nonlocal clock
            clock+=.01
            handle.write(json.dumps(dict(event=name,job_id="100",attempt_id=aid,attempt_elapsed_seconds=clock,**fields))+"\n")
        event("attempt_start",identity=arm["identity"],completed_update=0,next_sample_cursor=0)
        for update in range(5001):
            if update:
                ids=arm["order"][(update-1)*8:update*8]
                event("update_start",update=update,window_ids=ids)
                for micro,wid in enumerate(ids):
                    event("sample_start",update=update,micro_batch_index=micro,window_id=wid)
                    event("sample_end",update=update,micro_batch_index=micro,window_id=wid)
                event("update_end",update=update,seconds=.17,forward_backward_samples=8)
            if update%500==0:
                event("validation_start",update=update,windows=10)
                event("validation_end",update=update,seconds=.01,window_forwards=10)
        event("attempt_end",status="completed",completed_update=5000,seconds=clock)
    value=r.parse_attempt(r.Evidence(f["root"]),dict(path=p.relative_to(f["root"]).as_posix(),sha256=r.digest(p)),
        arm,{"100":f["job"]},{"100":{"status":"COMPLETED"}})
    assert value["sample_ends"]==40000 and value["completed_updates"]==set(range(1,5001))
    assert len(value["groups"])==5011


def build_matrix_evidence(root):
    """All real top-level writer fields/links, with bounded journal prototypes.

    Full journal parsing is independently tested above. The matrix integration
    below substitutes only those two expansion layers, not identity validation,
    pull/review bindings, receipt checks, accounting, replay or completion gates.
    """
    reg=matrix();suites={};identities={};training=[];jobs=[];cache_jobs=[];inventory={};proto={}
    for suite in r.SUITES:
        train=[suite+":t"+str(i) for i in range(10)];val=[suite+":v"+str(i) for i in range(10)]
        rows=[dict(window_id=w,split=split,task_id=i,episode_id=split+str(i))
            for split,values in (("train",train),("validation",val)) for i,w in enumerate(values)]
        suites[suite]=dict(windows=ref(root,reg["suites"][suite]["windows"],dict(suite=suite,version="formal-main-v2-full-pool-h8",
            horizon=8,test_pixels_opened=False,train_window_ids=train,validation_window_ids=val,windows=rows)),
            protocol=ref(root,reg["suites"][suite]["protocol"],{"suite":suite}))
        proto[suite]=(train,val)
    for pi,pair in enumerate(reg["pairs"]):
        suite=pair["suite"];seed=pair["seed"];budget=pair["visual_tokens"];job=str(1000+pi);train,val=proto[suite]
        config=dict(schema=r.SCHEMA,suite=suite,seed=seed,tokens_per_camera=budget//2,model_revision=reg["suites"][suite]["model_revision"],
            training=dict(updates=5000,effective_batch=8),selection=dict(updates=list(range(0,5001,500)),metric="task_macro_hard_validation_teacher_l1"))
        pair["sha256"]=ref(root,pair["path"],config)["sha256"]
        sources={"src/cti_vla/training/formal_records.py":"3"*64}
        ci=dict(suite=suite,model_revision=config["model_revision"],asset_manifest_sha256="a"*64,
            window_manifest_sha256=suites[suite]["windows"]["sha256"],data_protocol_sha256=suites[suite]["protocol"]["sha256"],
            producer_source_files=sources,dataset_statistics_sha256="4"*64)
        ns=r.signature({"cache_version":r.CACHE_VERSION,**ci});order=r.sample_order(train,seed)
        directory=f"results/formal_main_v2/{suite}/k{budget}/seed{seed}/training"
        j=dict(job_id=job,experiment=r.SCHEMA,mode="train",suite=suite,stage_key="stage"+job,run_root=pair["run_root_server"]+"/training",
            source_sha256="5"*64,invocation_sha256="6"*64,status="COMPLETED",gpus=1,elapsed_seconds=5000,
            exit_code="0:0",allocation="gres/gpu:l40=1,gres/gpu=1,cpu=7",node="gpu4025")
        jobs.append(j);file_refs=[];proto[job]={}
        for arm in ("A","B"):
            identity=dict(pair_config_sha256=r.signature(config),training_config_sha256=r.signature({**config,"arm":arm}),
                window_manifest_sha256=ci["window_manifest_sha256"],data_protocol_sha256=ci["data_protocol_sha256"],cache_identity=ci,
                training_source_files=sources,frozen_model_sha256="7"*64,f01_report_sha256="8"*64)
            evaluations=[dict(update=u,validation_metric=.5,artifact_sha256="9"*64,candidate_sha256="9"*64) for u in range(0,5001,500)]
            md=dict(arm=arm,suite=suite,seed=seed,visual_tokens=budget,training_complete=True,pair_id=r.signature(config),
                config_sha256=r.signature({**config,"arm":arm}),window_manifest_sha256=ci["window_manifest_sha256"],
                data_protocol_sha256=ci["data_protocol_sha256"],selection_protocol_sha256=r.signature(config["selection"]),
                frozen_model_sha256="7"*64,training_source_files=sources,model_revision=config["model_revision"],update=0,validation_metric=.5)
            receipt=dict(schema=r.SCHEMA,kind="deployment_receipt",metadata=md,metadata_sha256=r.signature(md),pair_config=config,
                training_config={**config,"arm":arm},planned_updates=5000,completed_updates=5000,training_complete=True,
                base_frozen=True,checkpoint_unchanged=True,evaluations=evaluations,checkpoint_sha256="b"*64,f01_report_sha256="8"*64)
            report=dict(schema=r.SCHEMA,arm=arm,status="completed",identity=identity,training_updates_completed=5000,
                next_sample_cursor=40000,committed_samples=40000,train_pool_windows=10,vla_parameters_unchanged=True,
                frozen_model_sha256="7"*64,initial_scorer_sha256="c"*64,sample_order_sha256=r.signature(order),
                evaluations=evaluations,best_checkpoint_sha256="b"*64,job_ids=[job],attempted_forward_backward_samples_completed=40000)
            ordering=dict(version=r.ORDER_VERSION,seed=seed,samples=order,order_sha256=r.signature(order),
                train_pool_sha256=r.signature(train),train_pool_size=10,initial_scorer_sha256="c"*64)
            start=dict(event="attempt_start",job_id=job,attempt_id=job+arm,identity=identity,
                completed_update=0,next_sample_cursor=0,attempt_elapsed_seconds=0)
            cr=ref(root,directory+f"/{arm}/attempts/{job+arm}/cost_events.jsonl",[start],lines=True)
            item=dict(suite=suite,visual_tokens=budget,seed=seed,arm=arm,report=ref(root,directory+f"/{arm}/training_report.json",report),
                receipt=ref(root,directory+f"/{arm}/deployment_receipt.json",receipt),
                training_order=ref(root,directory+f"/{arm}/training_order.json",ordering),cost_events=[cr])
            training.append(item);file_refs += [item[k] for k in ("report","receipt","training_order")]+[cr]
            proto[job][arm]=(order,val)
        cache=[];stamp=0
        for logical in ["shared:black-image"]+["window:"+x for x in train+val]:
            rows=cache_rows(ns,logical,job=job)
            for row in rows:row["time_unix_ns"]+=stamp
            stamp+=len(rows);cache+=rows
        cf=ref(root,directory+f"/cache_events/{job}_uuid.jsonl",cache,lines=True);file_refs.append(cf)
        jf=ref(root,f"results/formal_main_v2/job_receipts/{job}.json",dict(schema=r.SCHEMA,job_id=job,stage="train",stage_key=j["stage_key"],
            source_sha256=j["source_sha256"],invocation_sha256=j["invocation_sha256"],wall_seconds=4999,exit_code=0));file_refs.append(jf)
        fields=("status","exit_code","elapsed_seconds","allocation","node")
        pull=dict(schema=r.SCHEMA,kind="nonweight_pull",status="verified_nonweight_snapshot",final_evidence=True,
            weights_copied=False,sealed_initial_states_copied=False,scientific_completion_inferred=False,missing=[],
            selected_jobs=[dict(**j,include_run_root=True,active_overlapping_job_ids=[])],
            accounting_before={"jobs":{job:{k:j[k] for k in fields}}},accounting_after={"jobs":{job:{k:j[k] for k in fields}}},files=[])
        for f in file_refs:
            marker=f["path"].split("/training/",1)[-1]
            pull["files"].append(dict(relative=f["path"],sha256=f["sha256"],bytes=(root/f["path"]).stat().st_size,
                job_ids=[job],action="downloaded_verified",path=j["run_root"]+"/"+marker))
            inventory[f["path"]]=f["sha256"]
        pf=ref(root,f"results/formal_main_v2/pulls/{job}/receipt.json",pull)
        # Like the historical acceptance writer, direct cache SHA is absent;
        # the review->pull->file chain must suffice.
        review=dict(schema=r.SCHEMA,kind="root_segment_review",job_id=job,status="passed",source_sha256=j["source_sha256"],
            invocation_sha256=j["invocation_sha256"],sealed_states_opened=False,weights_copied=False,
            evidence_sha256={pf["path"]:pf["sha256"],jf["path"]:jf["sha256"]})
        rf=ref(root,directory+f"/segment_reviews/{job}.json",review)
        cache_jobs.append(dict(job_id=job,namespace_sha256=ns,cache_events=[cf],job_receipt=jf,root_review=rf,verified_pull=pf))
        inventory[pf["path"]]=pf["sha256"];inventory[rf["path"]]=rf["sha256"]
    registration=ref(root,"registration.json",reg)
    state=ref(root,"supervision.json",{"registered_jobs":jobs});bills=ref(root,"accounting.json",{"jobs":jobs})
    for f in [state,bills]+[f for s in suites.values() for f in s.values()]:inventory[f["path"]]=f["sha256"]
    close=ref(root,"final_cost_inventory.json",dict(schema=r.SCHEMA,kind="final_cost_inventory",issued_by="root",complete=True,
        registration_sha256=r.signature(reg),job_ids=[j["job_id"] for j in jobs],cache_job_ids=[j["job_id"] for j in jobs],evidence_sha256=inventory))
    evidence=dict(schema=r.SCHEMA,kind="cache_replay_evidence",registration_sha256=r.signature(reg),supervisor_state=state,
        accounting=bills,root_cost_inventory=close,suites=suites,training=training,cache_jobs=cache_jobs)
    return registration,ref(root,"evidence.json",evidence),proto


def test_full72_entrypoint_layered_contract(tmp_path,monkeypatch):
    registration,evidence,proto=build_matrix_evidence(tmp_path)
    actual_cache_parser=r.parse_cache
    def expanded_attempt(reader,reference,arm,registered,bills):
        # This expansion only saves redundant72x40000 fixture serialization.
        first=reader.lines(reference)[0][0];job=first["job_id"]
        assert first["identity"]==arm["identity"]
        groups={("validation",u):dict(expected=arm["windows"]["validation"],sample_starts=0,sample_ends=0,complete=True)
            for u in range(0,5001,500)}
        groups[("training",5000)]=dict(expected=arm["order"][-8:],sample_starts=8,sample_ends=8,complete=True)
        return dict(job=job,aid=first["attempt_id"],groups=groups,completed_updates=set(range(1,5001)),sample_ends=40000,
            failed_or_partial=False,ref=reference)
    def expanded_cache(reader,reference,**kwargs):
        result=actual_cache_parser(reader,reference,**kwargs);requests={}
        for arm,(order,val) in proto[kwargs["job"]].items():
            for u in range(0,5001,500):requests[(arm,"validation",u)]=val
            requests[(arm,"training",5000)]=order[-8:]
        result["requests"]=requests
        return result
    monkeypatch.setattr(r,"parse_attempt",expanded_attempt);monkeypatch.setattr(r,"parse_cache",expanded_cache)
    result=r.analyze(r.Evidence(tmp_path),registration,evidence)
    assert result["status"]=="completed_estimate_with_limitations" and len(result["arms"])==72
    assert result["actual_allocation"]["gpu_seconds"]==36*5000
    assert all(x["replay"]["counts"]["window_requests"]==40110 for x in result["arms"])
    assert all(x["timing"]["complete_seconds"] is None for x in result["arms"])
    assert all("operations" not in x["replay"] and "calibration" not in x["timing"] for x in result["arms"])
    assert result["observation_index"]["observations"]==36*21
    assert len(json.dumps(result))<750_000
    # Even a root-closed accounting list cannot turn a71-instance matrix into72.
    value=json.loads((tmp_path/evidence["path"]).read_text());value["training"].pop()
    # Omitting its cost source is detected through the pull before completion.
    f=ref(tmp_path,"incomplete_evidence.json",value)
    result=r.analyze(r.Evidence(tmp_path),registration,f)
    assert result["status"]=="pending_evidence" and result["missing"]
