import pytest

from diwa.data.identity import canonical_mapping_signature, file_set_signature, stable_sample_id


def test_sample_id_is_stable_signed_int64_and_step_sensitive():
    first = stable_sample_id("libero_spatial", "episode-7", 12)
    assert first == stable_sample_id("libero_spatial", "episode-7", 12)
    assert first != stable_sample_id("libero_spatial", "episode-7", 13)
    assert 0 <= first < 2**63


def test_mapping_signature_is_key_order_independent():
    first = canonical_mapping_signature({"b": 2, "a": 1}, namespace="config")
    second = canonical_mapping_signature({"a": 1, "b": 2}, namespace="config")
    assert first == second
    assert first.startswith("sha256:")


def test_file_signature_changes_with_content(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("one", encoding="utf-8")
    first = file_set_signature([path], namespace="processor")
    path.write_text("two", encoding="utf-8")
    assert first != file_set_signature([path], namespace="processor")
    with pytest.raises(ValueError, match="at least one"):
        file_set_signature([], namespace="processor")
