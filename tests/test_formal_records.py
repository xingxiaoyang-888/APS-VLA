"""Shared-cache bounds, concurrency, corruption and crash recovery on CPU."""
import multiprocessing
from pathlib import Path
import sqlite3
import time

import pytest
import torch

from cti_vla.training.formal_records import BoundedRecordCache
from cti_vla.training.formal_future import atomic_torch_save


def cache(root, *, capacity=16000, identity=None, events=None):
    return BoundedRecordCache(root, identity=identity or {"producer": "one"}, max_bytes=capacity,
        event=lambda event, **fields: (events.append({"event": event, **fields}) if events is not None else None))


def test_cache_hit_hash_and_namespace(tmp_path):
    events, calls = [], []
    first = cache(tmp_path, events=events)
    def build():
        calls.append(1)
        return {"feature": torch.arange(20), "diagnostic": {"value": .25}}
    assert torch.equal(first.get_or_create("one", build)["feature"], torch.arange(20))
    assert first.get_or_create("one", build)["diagnostic"] == {"value": .25}
    assert len(calls) == 1 and any(e["event"] == "cache_hit" for e in events)
    second = cache(tmp_path, identity={"producer": "two"})
    assert first.key("one") != second.key("one")
    second.get_or_create("one", build)
    assert len(calls) == 2
    with pytest.raises(ValueError, match="capacity differs"):
        cache(tmp_path, capacity=17000)


def test_lru_capacity_and_shared_black_pinned(tmp_path):
    events = []
    store = cache(tmp_path, capacity=16000, events=events)
    store.get_or_create("black", lambda: {"black": torch.ones(5)}, pinned=True)
    for i in range(7):
        store.get_or_create(str(i), lambda i=i: {"feature": torch.full((1024,), float(i))})
    with sqlite3.connect(tmp_path / "index.sqlite3") as db:
        rows = list(db.execute("SELECT key,bytes FROM entries"))
    assert sum(row[1] for row in rows) <= 16000
    assert store.key("black") in {row[0] for row in rows}
    assert len(list((tmp_path / "records").glob("*.pt"))) == len(rows)
    assert any(e["event"] == "cache_eviction" for e in events)
    assert store.get_or_create("black", lambda: pytest.fail("pinned black unexpectedly rebuilt"))["black"].numel() == 5


def test_corrupt_file_never_silently_regenerated(tmp_path):
    store = cache(tmp_path)
    store.get_or_create("record", lambda: {"x": torch.ones(1)})
    path = tmp_path / "records" / (store.key("record") + ".pt")
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="corrupt"):
        store.get_or_create("record", lambda: pytest.fail("corruption masked by regeneration"))


def test_crash_after_eviction_index_commit_recovers_orphan(tmp_path, monkeypatch):
    events = []
    store = cache(tmp_path, capacity=8000, events=events)
    store.get_or_create("old", lambda: {"x": torch.ones(1024)})
    original = store._delete_evicted_files
    def crash(_):
        raise RuntimeError("injected crash after transaction commit")
    monkeypatch.setattr(store, "_delete_evicted_files", crash)
    with pytest.raises(RuntimeError, match="injected"):
        store.get_or_create("new", lambda: {"x": torch.full((1024,), 2.)})
    # Both files can remain after a killed process, but only the committed new
    # one is indexed. Recovery deletes the old orphan without touching new.
    restarted = cache(tmp_path, capacity=8000, events=events)
    value = restarted.get_or_create("new", lambda: pytest.fail("committed cache record lost"))
    assert torch.equal(value["x"], torch.full((1024,), 2.))
    assert len(list((tmp_path / "records").glob("*.pt"))) == 1
    assert any(row["event"] == "cache_orphan_cleanup" for row in events)
    assert all((tmp_path / "records" / (row[0] + ".pt")).exists()
        for row in sqlite3.connect(tmp_path / "index.sqlite3").execute("SELECT key FROM entries"))


def _concurrent_worker(root, ready, begin, result):
    try:
        store = cache(Path(root), capacity=16000)
        ready.put(1)
        begin.wait(20)
        def build():
            with (Path(root) / "generated.txt").open("a", encoding="utf-8") as handle:
                handle.write("one\n")
            time.sleep(.1)
            return {"value": torch.tensor([7.])}
        value = store.get_or_create("same-window", build)
        result.put(("ok", float(value["value"][0])))
    except BaseException as error:
        result.put(("error", repr(error)))


def test_two_processes_share_one_atomic_production(tmp_path):
    ctx = multiprocessing.get_context("spawn")
    ready, begin, result = ctx.Queue(), ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=_concurrent_worker, args=(str(tmp_path), ready, begin, result)) for _ in range(2)]
    try:
        for worker in workers:
            worker.start()
        assert ready.get(timeout=30) == ready.get(timeout=30) == 1
        begin.set()
        assert result.get(timeout=30) == result.get(timeout=30) == ("ok", 7.)
        for worker in workers:
            worker.join(30)
            assert worker.exitcode == 0
        assert (tmp_path / "generated.txt").read_text().splitlines() == ["one"]
    finally:
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
                worker.join()


def test_safe_path_refuses_escape_and_other_local_files(tmp_path):
    store = cache(tmp_path)
    for value in ("../weights.pt", "records/other.pt", "other/" + "a" * 64 + ".pt"):
        with pytest.raises(ValueError):
            store._safe_path(value)


def test_real_registered_episode_index_and_generated_window_alignment(tmp_path, monkeypatch):
    """Real protobuf/split/window lookup with a synthetic frozen visual model."""
    import json
    import shutil
    from types import SimpleNamespace
    import numpy as np
    from test_data_formal_windows import freeze, ROOT
    from test_future_auxiliary import example as make_example
    from cti_vla.data import formal_windows, sequence_example
    from cti_vla.evaluation import libero_runtime
    from cti_vla.training.formal_records import FormalRecordProvider
    from cti_vla.training.future_auxiliary import frozen_future_target
    from cti_vla.training.formal_future import capture_rng, restore_rng
    benchmark = tmp_path / "external/LIBERO/libero/libero/benchmark"
    benchmark.mkdir(parents=True)
    for name in ("__init__.py", "libero_suite_task_map.py"):
        shutil.copyfile(ROOT / "external/LIBERO/libero/libero/benchmark" / name, benchmark / name)
    protocol, data, _, _, _ = freeze(tmp_path)
    manifest = formal_windows.build_formal_windows(protocol)
    toy = make_example.__wrapped__()
    toy.vla.projector = toy.student.visual_projector
    toy.vla.vision_backbone = torch.nn.Identity()
    toy.vla._process_vision_features = lambda pixels, *_: toy.vla.projector(toy.vla.vision_backbone(pixels))
    stats = {"q01": [-10000.] * 7, "q99": [10000.] * 7, "min": [-10000.] * 7,
             "max": [10000.] * 7, "mask": [True] * 6 + [False]}
    toy.vla.norm_stats = {"libero_object_no_noops": {"action": stats, "proprio": {}}}
    def prepare(episode, step, *args, **kwargs):
        return {"pixel_values": toy.batch.raw_tokens[:1] + step * .01,
                "input_ids": toy.batch.input_ids[:1], "attention_mask": toy.batch.attention_mask[:1],
                "normalized_proprio": torch.as_tensor(np.array(episode.proprio[step], copy=True))[None] * .001}
    monkeypatch.setattr(libero_runtime, "prepare_rlds_eval_inputs", prepare)
    monkeypatch.setattr(libero_runtime, "process_camera", lambda image, **kw: image)
    monkeypatch.setattr(libero_runtime, "_prepare_processed_inputs", lambda *a, **kw: {"pixel_values": torch.zeros_like(toy.batch.raw_tokens[:1])})
    decoded = []
    original_decode = sequence_example.decode_libero_example
    def decode(payload):
        result = original_decode(payload)
        assert result.episode_id not in protocol.manifests["test"].episode_ids
        decoded.append(result.episode_id)
        return result
    monkeypatch.setattr(sequence_example, "decode_libero_example", decode)
    kwargs = dict(protocol=protocol, manifest=manifest, data_directory=data,
        components=SimpleNamespace(vla=toy.vla), processor=object(), policy=toy.teacher,
        stats_key="libero_object_no_noops", cache_root=tmp_path / "cache", cache_identity={"fixture": True},
        events_path=tmp_path / "cache_events.jsonl", max_cache_bytes=1 << 20, ram_records=2, job_id="cpu")
    provider = FormalRecordProvider(**kwargs)
    provider.set_context(arm="A", phase="training", update=1)
    row = provider.rows[provider.train_window_ids[0]]
    rng = capture_rng()
    record = provider.get(row["window_id"])
    # Cache production must not perturb the optimizer RNG stream.
    actual = torch.rand(4)
    restore_rng(rng)
    assert torch.equal(actual, torch.rand(4))
    with torch.no_grad():
        expected = frozen_future_target(toy.vla.projector(toy.batch.raw_tokens[:1] + row["future_step"] * .01))
    assert torch.equal(record["future_target"], expected)
    episode = provider.get_episode(row)
    normalized = formal_windows.normalize_demo_actions(episode.actions[row["start_step"]:row["future_step"]], stats)
    assert np.array_equal(record["demonstration_actions"][0].numpy(), normalized)
    assert record["future_window_diagnostics"]["horizon_control_actions"] == 8
    assert record["future_window_diagnostics"]["raw_proprio_l2_change"] > 0
    calls = toy.vla.language_model.model.calls
    provider.get(row["window_id"])
    second = FormalRecordProvider(**kwargs)
    assert torch.equal(second.get(row["window_id"])["teacher_actions"], record["teacher_actions"])
    assert toy.vla.language_model.model.calls == calls
    events = [json.loads(line) for line in kwargs["events_path"].read_text().splitlines()]
    generated = [event for event in events if event["event"] == "feature_generate_end"]
    assert len(generated) == 1 and generated[0]["future_target_required_by_current_arm"] is False
    assert generated[0]["teacher_forwards"] == generated[0]["current_vision_forwards"] == generated[0]["future_vision_forwards"] == 1
    assert len(decoded) == 2  # one selected legal episode per process/provider
    with pytest.raises(ValueError, match="registered"):
        provider.get("unregistered-test-window")
