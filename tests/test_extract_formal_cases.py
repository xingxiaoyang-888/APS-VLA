"""CPU synthetic final cases. No actual trial, weights, sealed values or network.

The integration fixture reuses the real release, E04, adapter and root review
writers/validators. Its upstream GPU/source gates are explicitly substituted by
the existing synthetic72-selector fixture; the production173 hashes stay intact.
"""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import test_review_formal_downstream as upstream
from cti_vla.evaluation import formal_trials as trials
from cti_vla.evaluation.libero_runtime import TrialLedger, run_episode

ROOT = Path(__file__).resolve().parents[1]
tool = upstream.upstream.module("scripts/extract_formal_cases.py")


@pytest.fixture(scope="module", autouse=True)
def protected_sources():
    scheduler = upstream.upstream.module("scripts/ops/formal_downstream_supervisor.py")
    inventory = json.loads((ROOT / scheduler.SOURCE_INVENTORY).read_text())
    names = list(inventory["files"]) + [n for n in tool.SOURCES if n not in inventory["files"]]
    before = {n: tool.digest(ROOT / n) for n in names}
    assert all(before[n] == sha for n, sha in inventory["files"].items())
    yield
    assert before == {n: tool.digest(ROOT / n) for n in names}


def state(index, task=0):
    return dict(trial_id=f"state-{task}-{index}", task_id=task, task_name=f"task_{task}", source_state_index=index,
        initial_state_sha256="1" * 64)


def pair_rows(states, results, budget=64, seed=17):
    return {s["trial_id"] + f":{arm}{budget}_seed{seed}": dict(trial_id=s["trial_id"] + f":{arm}{budget}_seed{seed}",
        success=success, status="completed" if success else "policy_error")
        for s, (a, b) in zip(states, results) for arm, success in (("A", a), ("B", b))}


def row(*, sha="1" * 64, offset=0, control_step=0, value=0.):
    kept = list(range(offset, offset + 32)) + list(range(256 + offset, 288 + offset))
    return dict(chunks=[dict(control_step=control_step, observation_sha256=sha,
        metadata=dict(retained_indices=kept), normalized_actions=[[value] * 7 for _ in range(8)])])


def test_numeric_first_selection_has_all_four_slots_and_missing():
    states = [state(10), state(2), state(5), state(1, task=1)]
    outcomes = pair_rows(states, [(False, True), (False, True), (True, False), (False, False)])
    selected = tool.select_pair(states, outcomes, suite="libero_10", budget=64, seed=17)
    assert [r["category"] for r in selected] == list(tool.CATEGORIES)
    assert selected[0]["selection"]["state"]["source_state_index"] == 2
    assert selected[0]["candidate_count"] == 2
    assert selected[2]["selection"]["state"]["task_id"] == 1
    assert selected[3]["status"] == "missing" and selected[3]["selection"] is None


def test_incomplete_pair_pending_not_missing_category():
    states = [state(2)]
    outcomes = pair_rows(states, [(True, False)])
    outcomes.pop(next(iter(outcomes)))
    with pytest.raises(tool.PendingEvidence, match="Incomplete A/B"):
        tool.select_pair(states, outcomes, suite="libero_10", budget=64, seed=17)


@pytest.mark.parametrize("a,b,expected", [(False, True, "B_only_success"), (True, False, "A_only_success"),
    (False, False, "both_failure"), (True, True, "both_success")])
def test_four_terminal_categories(a, b, expected):
    assert tool.category(a, b) == expected


def test_first_shared_observation_only_and_correct_camera_sets_action_label():
    a, b = row(), row(offset=16, value=.25)
    result = tool.compare_first(a, b, 64)
    assert result["status"] == "available"
    assert result["intersection_over_budget"] == .5 and result["jaccard"] == pytest.approx(1 / 3)
    assert result["cameras"][1]["common"] == list(range(16, 32))
    assert result["action_difference"]["value"] == .25
    assert result["teacher_or_demo_action_error"] is None
    assert "not teacher/demo error" in result["action_difference"]["interpretation"]


@pytest.mark.parametrize("change,reason", [
    (lambda a: a.update(chunks=[]), "A_first_chunk_missing_or_invalid"),
    (lambda a: a["chunks"][0].update(control_step=8), "A_first_chunk_not_control_step_zero"),
    (lambda a: a["chunks"][0].update(observation_sha256="wrong"), "A_first_observation_hash_invalid"),
    (lambda a: a["chunks"][0]["metadata"].update(retained_indices=[0] * 64), "A_first_token_set_invalid"),
    (lambda a: a["chunks"][0].update(observation_sha256="2" * 64), "first_observation_hash_mismatch"),
])
def test_unavailable_diagnostic_does_not_search_a_later_matching_chunk(change, reason):
    a, b = row(), row()
    change(a)
    # A later shared observation is not an excuse to replace the first input.
    if a["chunks"]:
        a["chunks"].append(row(control_step=8)["chunks"][0])
    b["chunks"].append(row(control_step=8)["chunks"][0])
    result = tool.compare_first(a, b, 64)
    assert result["status"] == "unavailable" and result["reason"] == reason
    assert "cameras" not in result


def test_original_first_case_not_replaced_by_an_available_later_case():
    states = [state(10), state(2)]
    outcomes = pair_rows(states, [(True, True), (True, True)])
    selected = tool.select_pair(states, outcomes, suite="libero_10", budget=64, seed=17)[3]
    comparison = tool.compare_first(dict(chunks=[]), row(), 64)
    assert selected["selection"]["state"]["source_state_index"] == 2
    assert selected["candidate_count"] == 2 and comparison["status"] == "unavailable"


def test_grid_has512_indexed_cells_and_synthetic_watermark():
    case = dict(case_id="synthetic_test", token_comparison=tool.compare_first(row(), row(offset=16), 64))
    value = tool.svg(case, synthetic=True)
    assert tool.SYNTHETIC in value and value.count("data-patch=") == 512
    assert 'data-camera="0" data-patch="16" data-selection="common" x="16" y="82"' in value
    assert 'data-camera="1" data-patch="0" data-selection="A_only" x="352" y="66"' in value
    assert "<image" not in value


def test_no_lf_tail_never_repaired(tmp_path):
    path = tmp_path / "trials.jsonl"
    raw = b'{"event":"invocation"}'
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="tail"):
        list(tool.locate_lines(path))
    assert path.read_bytes() == raw


def test_line_trace_is_exact_original_bytes(tmp_path):
    path = tmp_path / "trials.jsonl"
    raw = b'{"event": "start"}\n' + b'{"event":"result"}\n'
    path.write_bytes(raw)
    pairs = list(tool.locate_lines(path))
    assert pairs[1][1] == dict(line=2, byte_offset=19, bytes=19, line_sha256=tool.hashlib.sha256(raw[19:]).hexdigest())


@pytest.mark.parametrize("relative", ["sealed_final.json", "x/sealed_final_renamed.json", "weights/config.json",
    "checkpoints/receipt.json", "downstream/final/panel.json", "a/../b.json"])
def test_forbidden_paths_rejected_before_read(tmp_path, relative):
    with pytest.raises(ValueError):
        tool.checked_path(tmp_path, relative)


def test_unreleased_pending_does_not_follow_final_references_or_publish(tmp_path, monkeypatch):
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(dict(schema=tool.SCHEMA, kind="formal_fixed_case_inputs", synthetic=True,
        final_reviews={"libero_10": {"path": "sealed_final.json", "sha256": "1" * 64}})))
    original = Path.open
    def guard(path, *args, **kwargs):
        assert "sealed" not in path.name
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guard)
    result = tool.extract(path, tmp_path / "synthetic-pending", project=tmp_path, synthetic=True)
    assert result["status"] == "pending" and not result["cases_written"]
    assert not (tmp_path / "synthetic-pending").exists()


def test_missing_release_rejected_before_any_final_metadata(tmp_path, monkeypatch):
    helper = upstream.upstream.module("scripts/formal_execution_manifests.py")
    evidence = helper.Evidence(tmp_path)
    with pytest.raises(tool.PendingEvidence):
        tool.read_ref(evidence, None, "root_release")
    source = tmp_path / "source.json"
    source.write_text("{}\n")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        tool.read_ref(evidence, dict(path="source.json", sha256="0" * 64), "tamper")
    with pytest.raises(ValueError, match="project-relative"):
        tool.read_ref(evidence, dict(path=str(source), sha256=tool.digest(source)), "absolute-reference")


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    """Complete compact metadata corpus, mostly zero-control policy errors.

    There are still exactly35200 cells; no lowered production cardinality gate.
    Only the already-tested GPU acceptance/source constructor is substituted.
    """
    with pytest.MonkeyPatch.context() as patch:
        p = upstream.project.__wrapped__(tmp_path_factory.mktemp("synthetic_case_corpus"), patch)
        p.args.freeze_directory = upstream.upstream.freeze_project(p)
        p.args.stage = "final"
        p.args.stop_after = None
        artifacts = {}
        for suite_index, suite in enumerate(tool.SUITES):
            p.args.execution_manifest = p.args.freeze_directory + "/final_execution/" + suite + ".json"
            p.args.output_relative = None
            a = upstream.begin(p, job_id=str(700 + suite_index))
            signature = p.scheduler.signature(a.config)
            events = [dict(event="invocation", slurm_job_id=a.job["job_id"], run_signature=signature)]
            ordered = sorted(a.panel["states"], key=lambda s: (s["task_id"], s["source_state_index"]))
            special = {s["trial_id"]: i for i, s in enumerate(ordered[:4])}
            for initial in a.panel["states"]:
                for method in a.manifest["methods"]:
                    identity = method["identity"]
                    base = trials._identity(a.panel, initial, identity["method_id"])
                    events.append({**base, "event": "start", "run_signature": signature})
                    pos = special.get(initial["trial_id"], -1)
                    win = identity["visual_tokens"] == 128 and identity.get("training_seed") == 17 and (
                        (pos == 1 and identity["method"] == "B") or (pos == 2 and identity["method"] == "A")
                        or (pos == 3 and identity["method"] in ("A", "B")))
                    result = dict(status="policy_error", success=False, termination="policy_error", control_steps=0,
                        wait_steps=10, policy_calls=1, chunks=[], executed_actions=[], wall_seconds=.001)
                    if win:
                        result = run_episode(upstream.timing.FakeEnv(1), upstream.policy(identity), "synthetic", [0.],
                            max_steps=upstream.fp.FORMAL_SUITES[suite]["max_steps"])
                    events.append({**base, **result, "event": "result", "attempt_wall_seconds": .001,
                        "run_signature": signature})
            ledger_path = p.root / a.output / "trials.jsonl"
            ledger_path.write_bytes(b"".join((json.dumps(r, allow_nan=False) + "\n").encode() for r in events))
            ledger = TrialLedger(ledger_path, run_signature=signature)
            provenance = {**a.config, "run_signature": signature, "checkpoint": a.base,
                "runtime": {**a.config["runtime"], "slurm_job_id": a.job["job_id"]}}
            a.summary = trials.summarize_formal_trials(a.panel, a.inv["method_ids"], ledger,
                provenance=provenance, checkpoint_unchanged=True)
            p.save(a.output + "/closed_loop_report.json", a.summary)
            upstream.emit_adapter(p, a)
            upstream.pull(p, a)
            review = upstream.review(p, a)
            assert review["scientific_complete"] and review["completed_trials"] == 8800
            p.save(a.review_relative, review)
            artifacts[suite] = a
        state_path = ".local/synthetic_supervisor_snapshot.json"
        p.save(state_path, p.state)
        def ref(relative):
            return dict(path=relative, sha256=tool.digest(p.root / relative))
        spec = dict(schema=tool.SCHEMA, kind="formal_fixed_case_inputs", synthetic=True,
            registration=ref(p.scheduler.REGISTRATION), source_inventory=ref(p.scheduler.SOURCE_INVENTORY),
            supervisor_state=ref(state_path), global_freeze=ref(p.args.freeze_directory + "/global_freeze.json"),
            root_release=ref(p.args.freeze_directory + "/root_release.json"),
            final_reviews={s: ref(a.review_relative) for s, a in artifacts.items()})
        p.save("case_inputs.json", spec)
        yield SimpleNamespace(project=p, artifacts=artifacts, spec=spec, ref=ref)


def injected(corpus, monkeypatch):
    p = corpus.project
    original = tool.load
    dependencies = {"scripts/formal_execution_manifests.py": p.helper,
        "scripts/ops/formal_downstream_supervisor.py": p.scheduler, "scripts/review_formal_downstream.py": upstream.tool}
    monkeypatch.setattr(tool, "load", lambda name: dependencies[name] if name in dependencies else original(name))
    original_open = Path.open
    def guard(path, *args, **kwargs):
        assert "sealed" not in path.name.lower()
        assert path.suffix.lower() not in (".pt", ".pth", ".bin", ".safetensors")
        assert not (path.name == "panel.json" and "final" in path.parts)
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guard)
    return p


def test_complete_released_root_review_chain_produces_all144_slots(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    output = p.root / "synthetic-cases-complete"
    result = tool.extract("case_inputs.json", output, project=p.root, synthetic=True)
    assert result["status"] == "complete" and result["slots"] == 144
    payload = json.loads((output / "cases.json").read_text(encoding="utf-8"))
    assert payload["final_trials"] == 35200 and payload["unique_initial_states"] == 1600
    assert payload["weights_read"] is payload["final_state_values_read"] is False
    assert payload["gpu_calls"] == 0 and payload["present"] == 48 and payload["missing"] == 96
    assert len(list((output / "grids").glob("*.svg"))) == 4
    assert tool.SYNTHETIC in (output / "cases.md").read_text(encoding="utf-8")
    for case in payload["cases"]:
        if case["status"] == "present":
            for arm in ("A", "B"):
                trace = case["selection"][arm]["trace"]
                raw = (p.root / trace["path"]).read_bytes()
                loc = trace["result"]
                line = raw[loc["byte_offset"]:loc["byte_offset"] + loc["bytes"]]
                assert tool.hashlib.sha256(line).hexdigest() == loc["line_sha256"]
                assert json.loads(line)["trial_id"] == case["selection"][arm]["trial_id"]
                assert case["selection"][arm]["identity"]["checkpoint_sha256"]
    receipt = json.loads((output / "case_receipt.json").read_text(encoding="utf-8"))
    assert all(tool.digest(output / name) == sha for name, sha in receipt["outputs_sha256"].items())
    with pytest.raises(ValueError, match="must be new"):
        tool.extract("case_inputs.json", output, project=p.root, synthetic=True)


def test_tampered_root_review_reference_rejected_before_output(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    spec = deepcopy(corpus.spec)
    spec["final_reviews"][tool.SUITES[0]]["sha256"] = "0" * 64
    p.save("tampered_case_inputs.json", spec)
    output = p.root / "synthetic-tamper"
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        tool.extract("tampered_case_inputs.json", output, project=p.root, synthetic=True)
    assert not output.exists()


def test_missing_suite_review_pending_no_partial_cases(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    spec = deepcopy(corpus.spec)
    del spec["final_reviews"][tool.SUITES[-1]]
    p.save("incomplete_case_inputs.json", spec)
    output = p.root / "synthetic-incomplete"
    result = tool.extract("incomplete_case_inputs.json", output, project=p.root, synthetic=True)
    assert result["status"] == "pending" and not output.exists()


def test_incomplete_scientific_review_pending_without_case_selection(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    spec = deepcopy(corpus.spec)
    original = p.root / spec["final_reviews"][tool.SUITES[0]]["path"]
    report = json.loads(original.read_text(encoding="utf-8"))
    report["scientific_complete"] = False
    p.save("results/formal_main_v2/downstream_reviews/synthetic_incomplete.json", report)
    spec["final_reviews"][tool.SUITES[0]] = corpus.ref("results/formal_main_v2/downstream_reviews/synthetic_incomplete.json")
    p.save("incomplete_scientific_inputs.json", spec)
    output = p.root / "synthetic-incomplete-scientific"
    result = tool.extract("incomplete_scientific_inputs.json", output, project=p.root, synthetic=True)
    assert result["status"] == "pending" and not output.exists()


def test_multi_run_input_explicitly_rejected_not_merged(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    spec = deepcopy(corpus.spec)
    spec["final_reviews"][tool.SUITES[0]] = [spec["final_reviews"][tool.SUITES[0]]]
    p.save("multi_run_inputs.json", spec)
    with pytest.raises(ValueError, match="Multiple final runs"):
        tool.extract("multi_run_inputs.json", p.root / "synthetic-multi-run", project=p.root, synthetic=True)
    assert not (p.root / "synthetic-multi-run").exists()


def test_raw_ledger_tamper_fails_the_original_pull_consumer(corpus, monkeypatch):
    p = injected(corpus, monkeypatch)
    a = corpus.artifacts[tool.SUITES[0]]
    path = p.root / a.output / "trials.jsonl"
    original = path.read_bytes()
    try:
        path.write_bytes(original + b'{}\n')
        with pytest.raises(ValueError, match="SHA identity differs"):
            tool.extract("case_inputs.json", p.root / "synthetic-ledger-tamper", project=p.root, synthetic=True)
    finally:
        path.write_bytes(original)
    assert not (p.root / "synthetic-ledger-tamper").exists()


def test_synthetic_opt_in_and_output_labels_mandatory(tmp_path):
    path = tmp_path / "inputs.json"
    path.write_text(json.dumps(dict(schema=tool.SCHEMA, kind="formal_fixed_case_inputs", synthetic=True)))
    with pytest.raises(ValueError, match="matching explicit"):
        tool.extract(path, tmp_path / "results/formal_main_v2/cases/test", project=tmp_path)
    with pytest.raises(ValueError, match="explicitly named synthetic"):
        tool.extract(path, tmp_path / "unmarked", project=tmp_path, synthetic=True)
