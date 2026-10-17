"""Focused CPU pull checks for the frozen evaluator's excluded lock file.

The real pull verifier checks a tiny synthetic SHA inventory. No trial runner,
GPU, upstream science stand-in, actual final values, SSH or submission is used.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def module(relative):
    spec = importlib.util.spec_from_file_location("lock_test_" + Path(relative).stem, ROOT / relative)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


REVIEW = module("scripts/review_formal_downstream.py")
SCHEDULER = module("scripts/ops/formal_downstream_supervisor.py")
MANIFEST = module("scripts/formal_execution_manifests.py")


@pytest.fixture(scope="module", autouse=True)
def unchanged_protected_files():
    inventory = json.loads((ROOT / SCHEDULER.SOURCE_INVENTORY).read_bytes())
    expected = dict(inventory["files"])
    assert len(expected) == 173
    for relative in (
        "scripts/review_formal_downstream.py", "scripts/ops/formal_downstream_supervisor.py",
        "scripts/formal_execution_manifests.py", "scripts/analyze_formal.py",
        SCHEDULER.ADAPTER, SCHEDULER.WRAPPER, SCHEDULER.ASSET_REVIEW, SCHEDULER.ASSET_ADAPTER,
        "tests/test_review_formal_downstream.py", "tests/test_formal_asset_downstream_integration.py",
        "tests/test_formal_asset_consumers.py",
    ):
        expected[relative] = SCHEDULER.digest(ROOT / relative)
    assert all(SCHEDULER.digest(ROOT / path) == digest for path, digest in inventory["files"].items())
    yield
    assert all(SCHEDULER.digest(ROOT / path) == digest for path, digest in expected.items())


@pytest.fixture
def project(tmp_path):
    def make(stage="development"):
        output = f"results/formal_main_v2/libero_10/downstream/{stage}/synthetic/attempt01"
        pull_relative = "results/formal_main_v2/pulls/synthetic_lock/receipt.json"
        directory = str(PurePosixPath(pull_relative).parent)
        job = dict(job_id="900", name="cti-formal-downstream", mode=stage,
                   stage_key="synthetic_" + stage, run_root=str(SCHEDULER.P / output),
                   status="COMPLETED", exit_code="0:0", elapsed_seconds=437, gpus=1,
                   invocation="results/formal_main_v2/invocations/synthetic_lock.json",
                   execution_manifest_sha256="a" * 64)

        def save(relative, value):
            path = tmp_path / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((json.dumps(value, sort_keys=True) + "\n").encode())
            return path

        job["invocation_sha256"] = SCHEDULER.digest(save(job["invocation"], {"synthetic": True}))
        artifacts = []
        for extension in ("json", "jsonl"):
            filename = job["job_id"] + "_" + "b" * 32 + "." + extension
            relative = output + "/adapter_invocations/" + filename
            path = save(relative, {"synthetic": True})
            artifacts.append(dict(path=str(SCHEDULER.P / relative),
                                  source=str(SCHEDULER.P / "results/formal_main_v2/adapter_invocations" / filename),
                                  sha256=SCHEDULER.digest(path), bytes=path.stat().st_size))
        wrapper_relative = "results/formal_main_v2/job_receipts/900.json"
        wrapper = dict(schema=SCHEDULER.ROUND, kind="formal_downstream_job_receipt", job_id=job["job_id"],
                       stage=stage, stage_key=job["stage_key"], run_root=job["run_root"],
                       source_sha256=SCHEDULER.FROZEN_SHA256, adapter_sha256=SCHEDULER.ADAPTER_SHA256,
                       invocation_sha256=job["invocation_sha256"], adapter_artifacts=artifacts)
        save(wrapper_relative, wrapper)
        raw_names = [output + "/config.json", wrapper_relative]
        raw_names += [PurePosixPath(row["path"]).relative_to(SCHEDULER.P).as_posix() for row in artifacts]
        save(raw_names[0], {"synthetic": True})
        for extension in ("out", "err"):
            name = f"results/slurm/{job['name']}_{job['job_id']}.{extension}"
            save(name, {"synthetic": True})
            raw_names.append(name)

        def repull(excluded=(), missing=()):
            rows = [dict(relative=name, path=str(SCHEDULER.P / name),
                         bytes=(tmp_path / name).stat().st_size,
                         sha256=SCHEDULER.digest(tmp_path / name), job_ids=[job["job_id"]])
                    for name in sorted(raw_names)]
            inventory = dict(files=rows, excluded=deepcopy(list(excluded)), missing=deepcopy(list(missing)))
            for name in ("inventory_before.json", "inventory_after.json"):
                save(directory + "/" + name, inventory)
            pull = dict(schema=SCHEDULER.ROUND, kind="nonweight_pull", status="verified_nonweight_snapshot",
                        final_evidence=True, weights_copied=False, sealed_initial_states_copied=False,
                        selected_jobs=[dict(job_id=job["job_id"], include_run_root=True, run_root=job["run_root"],
                                            source_sha256=SCHEDULER.FROZEN_SHA256)],
                        accounting_before={"jobs": {job["job_id"]: deepcopy(job)}},
                        accounting_after={"jobs": {job["job_id"]: deepcopy(job)}},
                        files=[dict(row, action="downloaded_verified") for row in rows],
                        inventory_sha256=SCHEDULER.digest(tmp_path / directory / "inventory_before.json"))
            save(pull_relative, pull)
            return pull

        def check(evidence=None, jobs=None):
            return REVIEW.pulled_candidate(evidence or MANIFEST.Evidence(tmp_path), SCHEDULER, job,
                                           pull_relative, [job] if jobs is None else jobs)

        repull()
        return SimpleNamespace(root=tmp_path, job=job, output=output, pull_relative=pull_relative,
                               directory=directory, raw_names=raw_names, wrapper=wrapper,
                               wrapper_relative=wrapper_relative, save=save, repull=repull, check=check)
    return make


def lock_row(project, *, path=None, reason="unregistered_nonweight_extension"):
    return dict(job_id=project.job["job_id"], path=path or project.job["run_root"] + "/.evaluation.lock", reason=reason)


@pytest.mark.parametrize("stage", ["development", "final"])
def test_exact_evaluation_lock_is_accepted_without_opening_it(project, stage):
    p = project(stage)
    p.repull([lock_row(p)])
    assert not (p.root / p.output / ".evaluation.lock").exists()
    evidence = MANIFEST.Evidence(p.root)
    candidate = p.check(evidence)
    assert candidate["scientific_complete"] is False
    assert set(candidate["files"]) == set(p.raw_names)
    assert not any(name.endswith("/.evaluation.lock") for name in evidence.files)


@pytest.mark.parametrize("stage", SCHEDULER.STAGES)
def test_existing_empty_exclusion_modes_are_unchanged(project, stage):
    assert project(stage).check()["scientific_complete"] is False


@pytest.mark.parametrize("stage", ["collect", "full", "components", "train", "evaluate"])
def test_lock_exception_is_only_for_development_and_final(project, stage):
    p = project(stage)
    p.repull([lock_row(p)])
    with pytest.raises(ValueError, match="Unexpected excluded downstream evidence"):
        p.check()


@pytest.mark.parametrize("stage", ["development", "final"])
@pytest.mark.parametrize("suffix", [
    "/.evaluation.lock/", "/.evaluation.lock.bak", "/sub/.evaluation.lock", "/../.evaluation.lock",
    "/./.evaluation.lock", "//.evaluation.lock", "/.training.lock", "/panel.json",
])
def test_similar_or_noncanonical_paths_are_not_exempt(project, stage, suffix):
    p = project(stage)
    p.repull([lock_row(p, path=p.job["run_root"] + suffix)])
    with pytest.raises(ValueError, match="Unexpected excluded downstream evidence"):
        p.check()


@pytest.mark.parametrize("stage", ["development", "final"])
@pytest.mark.parametrize("reason", [None, "", "unregistered_nonweight_extension ", "final_rollout_panel_contains_initial_state_values"])
def test_lock_requires_exact_exclusion_reason(project, stage, reason):
    p = project(stage)
    p.repull([lock_row(p, reason=reason)])
    with pytest.raises(ValueError, match="Unexpected excluded downstream evidence"):
        p.check()


def test_another_output_lock_or_unknown_current_job_exclusion_still_fails(project):
    p = project()
    for extra in [lock_row(p, path=p.job["run_root"].replace("attempt01", "attempt02") + "/.evaluation.lock"),
                  dict(job_id=p.job["job_id"], path=p.job["run_root"] + "/unexpected.txt", reason="unregistered_nonweight_extension")]:
        p.repull([lock_row(p), extra])
        with pytest.raises(ValueError, match="Unexpected excluded downstream evidence"):
            p.check()


def test_original_final_panel_exception_and_other_job_scope_are_retained(project):
    p = project("final")
    p.repull([lock_row(p), dict(job_id=p.job["job_id"], path=p.job["run_root"] + "/panel.json",
                               reason="final_rollout_panel_contains_initial_state_values"),
              dict(job_id="901", path="unrelated", reason="unrelated")])
    evidence = MANIFEST.Evidence(p.root)
    assert p.check(evidence)["scientific_complete"] is False
    assert not any(name.endswith(("/panel.json", "/.evaluation.lock")) for name in evidence.files)


def test_development_panel_cannot_use_final_panel_exception(project):
    p = project()
    p.repull([dict(job_id=p.job["job_id"], path=p.job["run_root"] + "/panel.json",
                   reason="final_rollout_panel_contains_initial_state_values")])
    with pytest.raises(ValueError, match="Unexpected excluded downstream evidence"):
        p.check()


def test_copied_final_panel_is_rejected_before_any_hash_or_file_access(project, monkeypatch):
    p = project("final")
    pull = p.repull([lock_row(p)])
    pull["files"].append(dict(relative=p.output + "/panel.json", sha256="f" * 64))
    p.save(p.pull_relative, pull)
    evidence = MANIFEST.Evidence(p.root)
    original_read = evidence.read
    reads = []

    def read(name):
        reads.append(name)
        assert name == p.pull_relative, "Final panel guard must precede inventory/other reads"
        return original_read(name)

    monkeypatch.setattr(evidence, "read", read)
    monkeypatch.setattr(SCHEDULER, "verify_review_pull", lambda *a, **kw: pytest.fail("Final panel reached the hash verifier"))
    with pytest.raises(ValueError, match="Final value panel must not be read"):
        p.check(evidence)
    assert reads == [p.pull_relative]
    assert not (p.root / p.output / "panel.json").exists()


@pytest.mark.parametrize("mutation, message", [
    ("inventory_sha", "changed during transfer"), ("accounting", "terminal accounting"),
    ("selected_source", "terminal SHA-pulled"), ("duplicate", "Duplicate SHA-pull"),
    ("raw_sha", "SHA identity differs"), ("invocation", "invocation changed"),
    ("wrapper", "exact registered wrapper"), ("unregistered", "not registered"),
])
def test_lock_does_not_bypass_original_pull_and_identity_checks(project, mutation, message):
    p = project()
    pull = p.repull([lock_row(p)])
    jobs = None
    if mutation == "inventory_sha":
        pull["inventory_sha256"] = "0" * 64
    elif mutation == "accounting":
        pull["accounting_after"]["jobs"][p.job["job_id"]]["elapsed_seconds"] += 1
    elif mutation == "selected_source":
        pull["selected_jobs"][0]["source_sha256"] = "0" * 64
    elif mutation == "duplicate":
        pull["files"].append(deepcopy(pull["files"][0]))
    elif mutation == "raw_sha":
        p.save(p.output + "/config.json", {"changed": True})
    elif mutation == "invocation":
        p.save(p.job["invocation"], {"changed": True})
    elif mutation == "wrapper":
        p.save(p.wrapper_relative, {**p.wrapper, "adapter_sha256": "0" * 64})
        pull = p.repull([lock_row(p)])
    else:
        jobs = []
    p.save(p.pull_relative, pull)
    with pytest.raises(ValueError, match=message):
        p.check(jobs=jobs)


@pytest.mark.parametrize("stage", ["development", "final"])
def test_lock_does_not_bypass_missing_terminal_inventory(project, stage):
    p = project(stage)
    p.repull([lock_row(p)], [dict(job_id=p.job["job_id"], path=p.job["run_root"] + "/trials.jsonl")])
    with pytest.raises(ValueError, match="Incomplete terminal pull inventory"):
        p.check()
