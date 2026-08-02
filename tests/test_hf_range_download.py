from pathlib import Path

import pytest

from scripts.download_hf_lfs_range import download


def test_download_rejects_overlong_partial_and_never_overwrites_output(tmp_path):
    output = tmp_path / "object.bin"
    output.write_bytes(b"verified")
    with pytest.raises(FileExistsError):
        download("https://invalid.example/object", output, 8, "0" * 64, 4)
    output.unlink()
    partial = Path(str(output) + ".partial")
    partial.write_bytes(b"too-long")
    with pytest.raises(ValueError, match="larger"):
        download("https://invalid.example/object", output, 4, "0" * 64, 4)
