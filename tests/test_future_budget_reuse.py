"""Synthetic CPU provenance tests; never generate a real-model engineering gate."""
from copy import deepcopy
import hashlib
import json

import pytest

from cti_vla.data.identity import file_sha256
from cti_vla.evaluation import future_budget_reuse as reuse
from cti_vla.evaluation.teacher_diagnostics import json_signature
from test_future_seed_reuse import bundle, put


@pytest.fixture
def budget_bundle(bundle):
    b = bundle
    # Rebuild synthetic original source/evidence coherently; its fixed functions
    # model unchanged input/cache dependencies, not real accepted semantics.
    old_root = b.paths["runner"].parents[1]
    target_source = "\n".join(f"def {name}():\n    return 'same'\n" for name in reuse.TARGET_NODES)
    for root in (old_root, b.source):
        (root / "src/cti_vla/training/future_auxiliary.py").write_text(target_source, encoding="utf-8")
    original = reuse.source_hashes(old_root)
    parent = reuse.read(b.paths["config"])
    parent["tokens_per_camera"] = 64
    put(b.paths["config"], parent)
    b.config = {**parent, "seed": 23, "run_id": "g1_future_long_k64_seed23_v1", "tokens_per_camera": 32}
    target = put(b.source / "configs/experiments/g1_future_long_k64_seed23_v1.json", b.config)
    reference = {**b.config, "seed": 17, "run_id": "g1_future_long_k64_seed17_v1"}
    anchor = put(b.source / "configs/experiments/g1_future_long_k64_seed17_v1.json", reference)
    f00 = reuse.read(b.paths["input_acceptance"])
    f00.update(source_files=original, config_sha256=json_signature(parent))
    put(b.paths["input_acceptance"], f00)
    inventory = reuse.read(b.paths["source_inventory"])
    inventory["files"].update(original)
    inventory["files"]["configs/experiments/g1_future_long_v1.json"] = file_sha256(b.paths["config"])
    inventory["source_sha256"] = hashlib.sha256(json.dumps(inventory["files"], sort_keys=True).encode()).hexdigest()
    put(b.paths["source_inventory"], inventory)
    for row in b.index:
        row["identity"]["config_sha256"] = file_sha256(b.paths["config"])
        row["identity"]["producer"]["source_files"] = original
    put(b.paths["cache_index"], b.index)
    keep = set(reuse.PARENT_LOGICAL_PATHS) | {"runner", "asset_manifest"}
    b.paths = {k: v for k, v in b.paths.items() if k in keep}
    experiment = put(b.source / reuse.REGISTRATION, {
        "new_configs": {"17": {"path": anchor.relative_to(b.source).as_posix(), "sha256": file_sha256(anchor)},
                        "23": {"path": target.relative_to(b.source).as_posix(), "sha256": file_sha256(target)}},
        "frozen_evidence_sha256": {v: file_sha256(b.paths[k]) for k, v in reuse.PARENT_LOGICAL_PATHS.items()},
    })
    b.reg = {"schema": reuse.SCHEMA, "allowed_config_changes": ["seed", "run_id", "tokens_per_camera"],
        "target_seed": 23, "target_run_id": b.config["run_id"], "target_config_identity_sha256": json_signature(b.config),
        "target_source_files": reuse.source_hashes(b.source), "experiment_registration_sha256": file_sha256(experiment),
        "parent_files": {k: {"path": p.relative_to(b.root).as_posix(), "sha256": file_sha256(p)} for k, p in b.paths.items()}}
    put(b.path, b.reg)
    return b


def load(b):
    return reuse.load_long_budget_reuse(b.path, config=b.config, project_root=b.root, source_root=b.source)


def test_64_reuses_only_original_inputs_and150_cache_not128_F01(budget_bundle):
    contract = load(budget_bundle)
    assert len(contract.cache_index) == 150
    assert contract.receipt["inherited_old128_F01"] is False
    assert contract.receipt["new_GPU_calls"] == 0
    assert "new64_F01_required" in contract.receipt["status"]
    assert not hasattr(contract, "parent_pair_id")


@pytest.mark.parametrize("change", ["budget", "seed", "lambda", "source", "cache_repin", "cache_producer",
                                   "target_definition", "cache_function"])
def test_new_budget_contract_rejects_wrong_scope_or_forged_reuse(budget_bundle, change):
    b = budget_bundle
    if change == "budget":
        b.config["tokens_per_camera"] = 64
    elif change == "seed":
        b.config["seed"] = 7
    elif change == "lambda":
        b.config["future"]["weight_B"] = .2
    elif change in ("cache_repin", "cache_producer"):
        index = deepcopy(b.index)
        if change == "cache_repin":
            index[0]["cache_sha256"] = "c" * 64
        else:
            index[0]["identity"]["producer"]["source_files"] = b.reg["target_source_files"]
        put(b.paths["cache_index"], index)
        b.reg["parent_files"]["cache_index"]["sha256"] = file_sha256(b.paths["cache_index"])
        put(b.path, b.reg)
    else:
        relative = "src/cti_vla/training/future_auxiliary.py" if change in ("source", "target_definition") else reuse.RUNNER
        path = b.source / relative
        path.write_text(path.read_text().replace("return 'same'", "return 'different'", 1)
                        if change != "cache_function" else path.read_text().replace("return 'unchanged'", "return 'different'"), encoding="utf-8")
        if change != "source":
            b.reg["target_source_files"] = reuse.source_hashes(b.source)
            put(b.path, b.reg)
    with pytest.raises(ValueError):
        load(b)


def new_f01(b):
    from test_future_long_contract import f01
    anchor = b.source / "configs/experiments/g1_future_long_k64_seed17_v1.json"
    report = f01()
    report.update(config_sha256=json_signature(reuse.read(anchor)), config_file_sha256=file_sha256(anchor),
        window_manifest_sha256=file_sha256(b.paths["windows"]), model_revision=b.config["model_revision"],
        input_acceptance_sha256=file_sha256(b.paths["input_acceptance"]), source_files=reuse.source_hashes(b.source),
        visual_tokens=64, per_camera_budgets=[32, 32], job_id="synthetic-new64-only")
    report["checks"].pop("hard128_packing")
    report["checks"]["hard64_packing"] = True
    path = put(b.root / "new64/f01_acceptance.json", report)
    put(path.parent / "acceptance_finalization.json", {
        "status": "verified", "checkpoint_unchanged": True, "result_status": "passed",
        "result_sha256": file_sha256(path), "job_id": report["job_id"],
    })
    return path, report


def gate(b, path):
    return reuse.require_budget_f01(path, config=b.config, source_root=b.source,
        window_manifest_sha256=file_sha256(b.paths["windows"]),
        input_acceptance_sha256=file_sha256(b.paths["input_acceptance"]))


def test_new64_F01_inherits_operator_for23_without_claiming_seed23_measurement(budget_bundle):
    b = budget_bundle
    path, report = new_f01(b)
    value = gate(b, path)
    assert value["accepted_pair_id"] == report["config_sha256"]
    assert value["receipt"]["measured_for_target_seed"] is False
    assert value["receipt"]["visual_tokens"] == 64


@pytest.mark.parametrize("change", ["old128", "missing_budget", "wrong_pair", "source", "unfinalized", "later_config"])
def test64_training_gate_cannot_use128_acceptance_or_changed_source(budget_bundle, change):
    b = budget_bundle
    path, report = new_f01(b)
    if change == "old128":
        report.update(visual_tokens=128, per_camera_budgets=[64, 64])
        report["checks"].pop("hard64_packing")
        report["checks"]["hard128_packing"] = True
    elif change == "missing_budget":
        report.pop("visual_tokens")
        report.pop("per_camera_budgets")
    elif change == "wrong_pair":
        report["config_sha256"] = json_signature(b.config)
    elif change == "source":
        report["source_files"] = {"forged.py": "a" * 64}
    elif change == "later_config":
        b.config["future"]["weight_B"] = .2
    else:
        (path.parent / "acceptance_finalization.json").unlink()
    put(path, report)
    with pytest.raises((ValueError, FileNotFoundError)):
        gate(b, path)
