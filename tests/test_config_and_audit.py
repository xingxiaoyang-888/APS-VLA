import json

import pytest

from diwa.config import load_stage_a_config, validate_stage_a_config
from diwa.evaluation.audit_log import AuditRecord, save_audit_record


def passing_metrics():
    return {
        "candidate_top1_coverage": 0.9,
        "candidate_oracle_regret": 0.01,
        "full_retention_max_abs_error": 0.001,
        "packed_speedup": 1.2,
        "content_permutation_mean_abs_change": 0.01,
    }


def test_primary_config_loads_with_stable_signature():
    config, signature = load_stage_a_config("configs/stage_a_libero_spatial.json")
    assert config["use_diffusion"] is False
    assert signature.startswith("sha256:")
    invalid = dict(config, use_diffusion=True)
    with pytest.raises(ValueError, match="architecture mismatch"):
        validate_stage_a_config(invalid)
    with pytest.raises(ValueError, match="must be integers"):
        validate_stage_a_config(dict(config, die_hidden_dim=256.0))


def test_audit_record_requires_passing_gates_and_saves_atomically(tmp_path):
    record = AuditRecord.create(
        run_id="pilot-0001",
        config_signature="sha256:config",
        policy_signature="sha256:policy",
        data_signature="sha256:data",
        environment={"cuda": "12.4", "torch": "2.x", "openvla_oft_commit": "abc123"},
        metrics=passing_metrics(),
    )
    path = save_audit_record(tmp_path / "pilot.json", record)
    assert json.loads(path.read_text(encoding="utf-8"))["run_id"] == "pilot-0001"
    with pytest.raises(RuntimeError, match="packed_speedup"):
        AuditRecord.create(
            run_id="bad",
            config_signature="c",
            policy_signature="p",
            data_signature="d",
            environment={"cuda": "12.4"},
            metrics=dict(passing_metrics(), packed_speedup=1.0),
        )
    with pytest.raises(ValueError, match="environment"):
        AuditRecord.create(
            run_id="bad-env",
            config_signature="c",
            policy_signature="p",
            data_signature="d",
            environment={"cuda": 12.4},
            metrics=passing_metrics(),
        )
