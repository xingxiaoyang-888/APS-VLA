"""Formal CLI wiring and guards; model execution is covered separately."""
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
import torch

from test_future_auxiliary import example, cpu_threads
from cti_vla.training import formal_future, formal_records, formal_resume_acceptance
from cti_vla.data import formal_windows
from cti_vla.evaluation import formal_acceptance, formal_runtime, checkpoint_manifest, future_input_acceptance
from cti_vla.models import openvla_oft_loader, openvla_oft_policy
from cti_vla_baselines import acl_matched


def runner_module():
    path = Path(__file__).resolve().parents[1] / "scripts/run_formal_future.py"
    spec = importlib.util.spec_from_file_location("formal_runner_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class Verified:
    digest: str = "synthetic"


def test_cli_uses_project_protocol_roots_and5000_plan_for500_segment(example, tmp_path, monkeypatch):
    runner = runner_module()
    root = Path(__file__).resolve().parents[1]
    config_path = root / "configs/experiments/formal_main_v2/libero_10_k128_seed17.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    args = runner.parser().parse_args([part for key, value in {
        "config": config_path, "protocol": tmp_path / "protocol.json", "windows": tmp_path / "windows.json",
        "checkpoint": tmp_path / "base", "asset-manifest": tmp_path / "base_manifest.json",
        "data-directory": tmp_path / "data", "cache-directory": tmp_path / "hf",
        "feature-cache": tmp_path / "features", "training-checkpoints": tmp_path / "weights",
        "output": tmp_path / "results", "input-acceptance-report": tmp_path / "f00.json",
        "acceptance-report": tmp_path / "f01.json", "stop-after-updates": 500,
        "max-wall-seconds": 300.,
    }.items() for part in ("--" + key, str(value))])
    for path in (args.input_acceptance_report, args.acceptance_report):
        path.write_text(json.dumps({"frozen_model_sha256": "b" * 64}))
    (args.acceptance_report.parent / "resume_acceptance.json").write_text("{}")
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="posix", environ={"SLURM_JOB_ID": "cpu-test"}))
    monkeypatch.setattr(runner, "_within", lambda path, _: Path(path))
    observed = {}
    def load_protocol(path, project_root):
        observed["protocol_project_root"] = project_root
        return SimpleNamespace(payload={"suite": "libero_10", "dataset_asset": "configs/assets/data.json",
            "inherited_protocol": {"path": "configs/manifests/parent.json"}})
    monkeypatch.setattr(formal_windows, "load_formal_protocol", load_protocol)
    monkeypatch.setattr(formal_windows, "load_formal_windows", lambda *a: {"suite": "libero_10"})
    monkeypatch.setattr(checkpoint_manifest, "load_checkpoint_manifest", lambda _: SimpleNamespace(revision=config["model_revision"]))
    monkeypatch.setattr(checkpoint_manifest, "verify_checkpoint_directory", lambda *a: Verified())
    monkeypatch.setattr(formal_future, "formal_source_hashes", lambda _: {"synthetic.py": "a" * 64})
    monkeypatch.setattr(formal_future, "file_sha256", lambda _: "a" * 64)
    monkeypatch.setattr(formal_future, "parameter_fingerprint", lambda _: "b" * 64)
    monkeypatch.setattr(formal_acceptance, "select_formal_acceptance_windows", lambda *a: [{"window_id": "fixed"}])
    def gate_f00(*args, **kwargs):
        observed["f00"] = kwargs
    def gate_f01(*args, **kwargs):
        observed["f01"] = kwargs
    monkeypatch.setattr(formal_acceptance, "require_formal_input_acceptance", gate_f00)
    monkeypatch.setattr(formal_acceptance, "require_formal_acceptance", gate_f01)
    monkeypatch.setattr(future_input_acceptance, "verify_input_acceptance_journal", lambda *a: observed.update(input_journal=True))
    monkeypatch.setattr(formal_acceptance, "verify_formal_operator_journal", lambda *a: observed.update(operator_journal=True))
    monkeypatch.setattr(formal_resume_acceptance, "require_formal_resume_acceptance", lambda *a, **kw: observed.update(f03=True))
    monkeypatch.setattr(formal_resume_acceptance, "verify_resume_journal", lambda *a: observed.update(f03_journal=True))
    components = SimpleNamespace(vla=example.vla, action_head=example.teacher.action_head,
                                  proprio_projector=example.teacher.proprio_projector)
    components.vla.projector = example.student.visual_projector
    monkeypatch.setattr(openvla_oft_loader, "load_openvla_oft_components", lambda *a, **kw: components)
    monkeypatch.setattr(openvla_oft_policy, "OpenVLAOFTTokenPolicy", lambda *a, **kw: example.teacher)
    monkeypatch.setattr(acl_matched, "FrozenDifferentiableOFTPolicy", lambda *a, **kw: example.student)
    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(AutoProcessor=SimpleNamespace(from_pretrained=lambda *a, **kw: object())))
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    def provider(**kwargs):
        observed["provider"] = kwargs
        return object()
    monkeypatch.setattr(formal_records, "FormalRecordProvider", provider)
    calls = []
    def train(**kwargs):
        calls.append(kwargs)
        assert observed["f00"] and observed["f01"]
        assert observed["input_journal"] and observed["operator_journal"]
        assert observed["f03"] and observed["f03_journal"]
        assert kwargs["spec"].updates == 5000 and kwargs["spec"].alpha(500) > .1
        assert kwargs["stop_after_updates"] == 500 and 0 < kwargs["max_wall_seconds"] <= 300
        return {"status": "checkpointed", "training_updates_completed": 500}
    monkeypatch.setattr(formal_future, "train_formal_arm", train)
    result = runner.run(args)
    assert observed["protocol_project_root"] == Path("/ssdfs/datahome/u15016/XXY_CVPR/CTI-VLA")
    assert observed["protocol_project_root"] != runner.ROOT
    assert [row["arm"] for row in calls] == ["A", "B"]
    assert observed["provider"]["max_cache_bytes"] == 128 * 1024**3
    assert observed["provider"]["ram_records"] == 2
    assert "seed" not in observed["provider"]["cache_identity"]
    assert "tokens_per_camera" not in observed["provider"]["cache_identity"]
    assert result["status"] == "checkpointed" and result["pair_complete"] is False
    assert (args.output / "training_progress.json").is_file()
    assert not (args.output / "training_summary.json").exists()


def test_runner_local_execution_guard(tmp_path):
    runner = runner_module()
    if runner.os.name != "nt":
        pytest.skip("Windows-specific local safeguard")
    with pytest.raises(RuntimeError, match="server Slurm"):
        runner.run(SimpleNamespace())


def test_runner_containment_guard(tmp_path):
    runner = runner_module()
    with pytest.raises(ValueError, match="strictly below"):
        runner._within(tmp_path, tmp_path)
    with pytest.raises(ValueError, match="strictly below"):
        runner._within(tmp_path.parent / "outside", tmp_path)
    assert runner._within(tmp_path / "inside", tmp_path) == (tmp_path / "inside").resolve()
