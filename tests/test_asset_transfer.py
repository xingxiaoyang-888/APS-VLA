"""Protect immutable downloads against truncated or wrong HTTP responses."""
import hashlib
import importlib.util
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location("asset_downloader", Path(__file__).parents[1] / "scripts/server/download_assets.py")
assets = importlib.util.module_from_spec(spec)
spec.loader.exec_module(assets)


class Response:
    def __init__(self, payload, status=206, content_range="bytes 2-4/5"):
        import io
        self.body = io.BytesIO(payload)
        self.status = status
        self.headers = {"Content-Range": content_range}

    def read(self, count):
        return self.body.read(count)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_resume_verifies_content_before_promotion(tmp_path, monkeypatch):
    item = {"path": "test.bin", "size": 5, "sha256": hashlib.sha256(b"abcde").hexdigest()}
    partial = tmp_path / "test.bin.partial"
    partial.write_bytes(b"ab")
    monkeypatch.setattr(assets.urllib.request, "urlopen", lambda *a, **kw: Response(b"cde"))
    assets.download_file("https://example.invalid/test", tmp_path / "test.bin", item)
    assert (tmp_path / "test.bin").read_bytes() == b"abcde"
    assert not partial.exists()


def test_wrong_range_and_checksum_never_promote(tmp_path, monkeypatch):
    item = {"path": "test.bin", "size": 5, "sha256": hashlib.sha256(b"abcde").hexdigest()}
    partial = tmp_path / "test.bin.partial"
    partial.write_bytes(b"ab")
    monkeypatch.setattr(assets.urllib.request, "urlopen", lambda *a, **kw: Response(b"abcde", status=200))
    with pytest.raises(ValueError, match="honor resume"):
        assets.download_file("https://example.invalid/test", tmp_path / "test.bin", item)
    assert partial.read_bytes() == b"ab"
    monkeypatch.setattr(assets.urllib.request, "urlopen", lambda *a, **kw: Response(b"xyz"))
    with pytest.raises(ValueError, match="Hash mismatch"):
        assets.download_file("https://example.invalid/test", tmp_path / "test.bin", item)
    assert not (tmp_path / "test.bin").exists()


@pytest.mark.parametrize("name", ["../outside", "/outside", "C:/outside", "..\\outside"])
def test_manifest_cannot_escape_asset_root(tmp_path, name):
    with pytest.raises(ValueError):
        assets.safe_path(tmp_path, name)
