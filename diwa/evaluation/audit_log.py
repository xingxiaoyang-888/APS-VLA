"""Atomic, schema-checked records for mandatory pre-expansion audits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Mapping

from diwa.evaluation.gates import check_expansion_gates


@dataclass(frozen=True)
class AuditRecord:
    run_id: str
    config_signature: str
    policy_signature: str
    data_signature: str
    environment: Mapping[str, str]
    metrics: Mapping[str, float]
    created_at_utc: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("run_id", "config_signature", "policy_signature", "data_signature"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty")
        if self.schema_version != 1:
            raise ValueError("unsupported audit schema version")
        try:
            datetime.fromisoformat(self.created_at_utc.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("created_at_utc must be ISO-8601") from error
        if not self.environment or any(
            not isinstance(key, str)
            or not isinstance(value, str)
            or not key.strip()
            or not value.strip()
            for key, value in self.environment.items()
        ):
            raise ValueError("environment entries must be non-empty strings")
        check_expansion_gates(dict(self.metrics))

    @classmethod
    def create(
        cls,
        *,
        run_id: str,
        config_signature: str,
        policy_signature: str,
        data_signature: str,
        environment: Mapping[str, str],
        metrics: Mapping[str, float],
    ) -> "AuditRecord":
        return cls(
            run_id=run_id,
            config_signature=config_signature,
            policy_signature=policy_signature,
            data_signature=data_signature,
            environment=dict(environment),
            metrics=dict(metrics),
            created_at_utc=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "config_signature": self.config_signature,
            "policy_signature": self.policy_signature,
            "data_signature": self.data_signature,
            "environment": dict(self.environment),
            "metrics": dict(self.metrics),
            "created_at_utc": self.created_at_utc,
            "schema_version": self.schema_version,
        }


def save_audit_record(path: str | Path, record: AuditRecord) -> Path:
    output = Path(path)
    if output.suffix != ".json":
        raise ValueError("audit record path must end in .json")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")
    if temporary.exists():
        raise FileExistsError("stale audit temporary file exists")
    try:
        temporary.write_text(json.dumps(record.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output


__all__ = ["AuditRecord", "save_audit_record"]
