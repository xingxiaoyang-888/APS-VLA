"""CPU Long registration/deployment contracts; no simulator or model claims."""
from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
from types import SimpleNamespace

import pytest

from cti_vla.data import long_initial_states as states
from cti_vla.data.experiment_protocol import INITIAL_STATE_SEED
from cti_vla.data.identity import canonical_mapping_signature, file_sha256
from cti_vla.evaluation import future_trials as trials, libero_runtime
from test_future_runtime import good_policy, panel as spatial_panel
from test_selector_runtime import Env, env_observation

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "configs/manifests/long_initial_states_v1"
PANEL = DIRECTORY / "development_panel_30.json"


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


evaluation = module("long_eval_tests", "scripts/eval_future_selector_libero.py")
analysis = module("long_analysis_tests", "scripts/analyze_g1_future.py")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_fixed_official_registration_and_reproducible_split(tmp_path):
    # Numeric inventories may inspect sealed initial-state bytes, never rollouts.
    report = states.build_long_initial_states(ROOT / "external/LIBERO", ROOT / "external/openvla-oft", tmp_path)
    assert report["development_count"] == 30 and report["sealed_final_count"] == 120
    assert report["cross_split_content_hash_intersection"] == 0
    assert file_sha256(tmp_path / PANEL.name) == states.LONG_PANEL_SHA256
    registration = read(tmp_path / "development_tasks.json")
    assert [r["task_id"] for r in registration["tasks"]] == [0, 3, 5]
    assert tuple(r["task_name"] for r in registration["tasks"]) == states.LONG_TASK_NAMES
    assert registration["horizon"]["max_steps"] == 520
    assert registration["horizon"]["source_line"] == 67
    dev, final = [read(tmp_path / f"init_states_{split}.json") for split in ("development", "test")]
    for payload in (dev, final):
        states.validate_long_initial_state_manifest(payload)
    for task, name in zip(states.LONG_TASK_IDS, states.LONG_TASK_NAMES):
        indices = list(range(50))
        seed = canonical_mapping_signature({"seed": INITIAL_STATE_SEED, "task": name}, namespace="cti-vla:init-state-split:v1")
        random.Random(seed).shuffle(indices)
        assert [r["source_state_index"] for r in dev["states"] if r["task_id"] == task] == sorted(indices[:10])
        assert [r["source_state_index"] for r in final["states"] if r["task_id"] == task] == sorted(indices[10:])


def test_wrong_source_revision_refused_before_state_inventory(monkeypatch, tmp_path):
    monkeypatch.setattr(states, "LIBERO_REVISION", "0" * 40)
    monkeypatch.setattr(states, "load_official_states", lambda _: pytest.fail("state bytes must remain unopened"))
    with pytest.raises(ValueError, match="fixed official source"):
        states.build_long_initial_states(ROOT / "external/LIBERO", ROOT / "external/openvla-oft", tmp_path)


def test_deployment_opens_only_pinned_dev_panel(monkeypatch):
    original = Path.read_text
    def guarded(path, *args, **kwargs):
        assert "test" not in path.name
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", guarded)
    panel = states.load_long_development_panel(PANEL)
    assert Counter(r["task_id"] for r in panel["states"]) == {0: 10, 3: 10, 5: 10}
    with pytest.raises(ValueError, match="sealed final"):
        states.load_long_development_panel(DIRECTORY / "init_states_test.json")


@pytest.mark.parametrize("change", ["state", "suite", "horizon", "methods", "test"])
def test_resigned_panel_cannot_change_registered_protocol(change):
    panel = states.load_long_development_panel(PANEL)
    if change == "state":
        panel["states"][0]["initial_state"][0] += .01
    elif change == "suite":
        panel["suite"] = "libero_spatial"
    elif change == "horizon":
        panel["max_steps"] = 700
    elif change == "methods":
        panel["methods"].append("uniform128")
    else:
        panel["split"] = "test"
    panel["panel_signature"] = states._signature({k: v for k, v in panel.items() if k != "panel_signature"})
    with pytest.raises(ValueError, match="frozen preregistration"):
        states.validate_long_development_panel(panel)


class NeverDone(Env):
    def step(self, action):
        self.steps += 1
        return env_observation(), 0, False, {}


@pytest.mark.parametrize("long,horizon,calls", [(True, 520, 65), (False, 220, 28)])
def test_exact_official_horizon_with_chunk8_and_separate_wait(tmp_path, long, horizon, calls):
    panel = states.load_long_development_panel(PANEL) if long else spatial_panel()
    policies = {m: good_policy for m in ("dense", "future_A", "future_B")}
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="unit-test")
    trials.evaluate_future_trials(panel, policies, ledger, lambda _: (NeverDone(), "fixed"), reseed=lambda: None, stop_after=1)
    row = next(iter(ledger.completed().values()))
    assert row["control_steps"] == horizon and row["wait_steps"] == 10
    assert row["policy_calls"] == calls and row["termination"] == "task_horizon"
    assert not row["success"]


@pytest.mark.parametrize("methods", [("future_A", "future_B"), ("dense", "uniform128", "future_A", "future_B")])
def test_long_cannot_omit_dense_or_add_uniform(tmp_path, methods):
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="unit-test")
    with pytest.raises(ValueError, match="exactly dense/A/B"):
        trials.evaluate_future_trials(states.load_long_development_panel(PANEL), dict.fromkeys(methods, good_policy), ledger,
            lambda _: pytest.fail("reject before simulator"), reseed=lambda: None)


def test_90_paired_trials_resume_and_no_cross_suite_identity(tmp_path):
    panel = states.load_long_development_panel(PANEL)
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature="unit-test")
    policies = dict.fromkeys(("dense", "future_A", "future_B"), good_policy)
    observed = []
    def environment(state):
        observed.append((state["trial_id"], state["initial_state_sha256"]))
        return Env(), "fixed"
    trials.evaluate_future_trials(panel, policies, ledger, environment, reseed=lambda: None, stop_after=3)
    assert len(set(observed)) == 1
    reloaded = libero_runtime.TrialLedger(ledger.path, run_signature="unit-test")
    assert trials.evaluate_future_trials(panel, policies, reloaded, environment, reseed=lambda: None) == 87
    result = trials.summarize_future_trials(panel, policies, reloaded, provenance={}, checkpoint_unchanged=True)
    assert result["stage"] == "G1-F_Long_development" and result["status"] == "completed"
    assert result["completed_trials"] == result["expected_trials"] == 90
    assert result["paired_AB"]["completed_pairs"] == 30
    assert all(v["trials"] == 10 for m in result["methods"].values() for v in m["per_task"].values())
    with pytest.raises(ValueError, match="identity"):
        trials.validate_future_trial_identities(spatial_panel(), policies, reloaded)


def long_args(tmp_path, **changes):
    config = tmp_path / "long_config.json"
    write(config, {"suite": "libero_10"})
    return SimpleNamespace(**({"suite": "libero_10", "config": config, "panel": PANEL,
        "prepare_only": True, "controls": None} | changes))


def test_long_prepare_is_only_90_dev_trials_without_loading_weights(tmp_path):
    args = long_args(tmp_path)
    result = evaluation.run(args)
    assert result["expected_trials"] == 90 and result["gpu_calls"] == 0
    assert result["methods"] == ("dense", "future_A", "future_B")
    assert args.stats_key == "libero_10_no_noops"
    assert not result["checkpoint_validated"] and not result["f01_accepted"]


@pytest.mark.parametrize("changes", [{"config": None}, {"panel": None}, {"controls": ["dense", "uniform128"]}])
def test_long_prepare_requires_explicit_own_protocol(tmp_path, changes):
    with pytest.raises(ValueError):
        evaluation.run(long_args(tmp_path, **changes))


def test_long_execution_routes_protocol_to_rlds_asset_not_model_asset(tmp_path, monkeypatch):
    from cti_vla.data import long_future_windows
    path = tmp_path / "evidence.json"
    write(path, {"suite": "libero_10"})
    args = SimpleNamespace(suite="libero_10", **dict.fromkeys(("config", "window_manifest", "f01_report",
        "receipt_a", "receipt_b", "checkpoint_a", "checkpoint_b", "asset_manifest", "protocol", "panel",
        "input_acceptance_report"), path))
    class ReachedCorrectLoader(Exception):
        pass
    def load(protocol, *positional, **keywords):
        assert protocol == args.protocol and not positional and not keywords
        raise ReachedCorrectLoader()
    monkeypatch.setattr(long_future_windows, "load_long_future_protocol", load)
    with pytest.raises(ReachedCorrectLoader):
        evaluation._execute(args, {}, ("dense", "future_A", "future_B"))


def test_long_analysis_rebuilds_90_trials_and_dense_paired_comparisons(tmp_path):
    panel = states.load_long_development_panel(PANEL)
    config = {"suite": "libero_10", "max_steps": 520, "panel_signature": panel["panel_signature"],
        "methods": ["dense", "future_A", "future_B"],
        "selectors": {arm: {"selector_checkpoint_sha256": arm} for arm in ("A", "B")}}
    ledger = libero_runtime.TrialLedger(tmp_path / "trials.jsonl", run_signature=analysis.signature(config))
    for state in panel["states"]:
        for method in config["methods"]:
            identity = trials._identity(panel, state, method)
            ledger.append({**identity, "event": "start"})
            ledger.append({**identity, "event": "result", "status": "completed", "success": method != "future_A"})
    summary = trials.summarize_future_trials(panel, config["methods"], ledger, provenance=config, checkpoint_unchanged=True)
    for name, value in (("panel.json", panel), ("config.json", config), ("closed_loop_report.json", summary)):
        write(tmp_path / name, value)
    result = analysis.analyze_closed_loop(tmp_path, {}, analysis.Evidence(), repeats=100, suite="libero_10", panel_path=PANEL)
    assert result["paired_counts"]["B_only"] == 30
    assert result["paired_B_minus_A"]["mean"] == 1
    assert result["paired_vs_dense"]["A"]["selector_minus_dense"]["mean"] == -1
    assert result["paired_vs_dense"]["B"]["selector_minus_dense"]["mean"] == 0
    with pytest.raises(ValueError, match="frozen development"):
        analysis.analyze_closed_loop(tmp_path, {}, analysis.Evidence(), repeats=100)
    # Changing a horizon, even alongside new config/event signatures, is refused.
    config["max_steps"] = 220
    summary["provenance"] = config
    write(tmp_path / "config.json", config)
    for event in ledger.events:
        event["run_signature"] = analysis.signature(config)
    ledger.path.write_text("".join(json.dumps(r) + "\n" for r in ledger.events), encoding="utf-8")
    summary["trials_jsonl_sha256"] = file_sha256(ledger.path)
    write(tmp_path / "closed_loop_report.json", summary)
    with pytest.raises(ValueError, match="horizon"):
        analysis.analyze_closed_loop(tmp_path, {}, analysis.Evidence(), repeats=100, suite="libero_10", panel_path=PANEL)
