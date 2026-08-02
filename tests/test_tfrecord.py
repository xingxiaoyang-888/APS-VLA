import struct

import pytest

from diwa.data.tfrecord import _masked_crc32c, verify_tfrecord


def write_record(path, payload: bytes):
    length = struct.pack("<Q", len(payload))
    path.write_bytes(length + struct.pack("<I", _masked_crc32c(length)) + payload + struct.pack("<I", _masked_crc32c(payload)))


def test_tfrecord_framing_verifier_roundtrip(tmp_path):
    path = tmp_path / "sample.tfrecord"
    write_record(path, b"one")
    with path.open("ab") as handle:
        payload = b"two"
        length = struct.pack("<Q", len(payload))
        handle.write(length + struct.pack("<I", _masked_crc32c(length)) + payload + struct.pack("<I", _masked_crc32c(payload)))
    summary = verify_tfrecord(path)
    assert summary.records == 2
    assert summary.payload_bytes == 6


def test_tfrecord_framing_rejects_corruption_and_safety_limit(tmp_path):
    path = tmp_path / "sample.tfrecord"
    write_record(path, b"payload")
    raw = bytearray(path.read_bytes())
    raw[8] ^= 1
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="length CRC"):
        verify_tfrecord(path)
    write_record(path, b"payload")
    with pytest.raises(ValueError, match="safety limit"):
        verify_tfrecord(path, max_record_bytes=2)
