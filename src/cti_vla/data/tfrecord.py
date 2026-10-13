"""Dependency-free TFRecord framing verifier.

This intentionally does not decode TensorFlow Example/SequenceExample payloads.
It verifies the storage envelope before an optional TensorFlow/TFDS environment
is introduced, keeping data preflight lightweight and bounded.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import struct
from typing import Iterator

_CRC32C_POLY = 0x82F63B78
_MASK_DELTA = 0xA282EAD8
_TABLE = []
for _index in range(256):
    _value = _index
    for _ in range(8):
        _value = (_value >> 1) ^ (_CRC32C_POLY if _value & 1 else 0)
    _TABLE.append(_value & 0xFFFFFFFF)


@dataclass(frozen=True)
class TFRecordSummary:
    path: str
    records: int
    payload_bytes: int
    file_bytes: int
    sha256: str


def _crc32c(data: bytes, crc: int = 0) -> int:
    value = crc ^ 0xFFFFFFFF
    for byte in data:
        value = _TABLE[(value ^ byte) & 0xFF] ^ (value >> 8)
    return (value ^ 0xFFFFFFFF) & 0xFFFFFFFF


def _masked_crc32c(data: bytes) -> int:
    crc = _crc32c(data)
    return (((crc >> 15) | ((crc << 17) & 0xFFFFFFFF)) + _MASK_DELTA) & 0xFFFFFFFF


def _read_exact(handle, size: int) -> bytes:
    value = handle.read(size)
    if len(value) != size:
        raise ValueError(f"truncated TFRecord: expected {size} bytes, got {len(value)}")
    return value


def _records(path: str | Path, max_record_bytes: int, digest=None) -> Iterator[tuple[int, bytes]]:
    input_path = Path(path)
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    if not isinstance(max_record_bytes, int) or isinstance(max_record_bytes, bool) or max_record_bytes <= 0:
        raise ValueError("max_record_bytes must be a positive integer")
    records = 0
    with input_path.open("rb") as handle:
        while True:
            header = handle.read(12)
            if not header:
                break
            if len(header) != 12:
                raise ValueError("truncated TFRecord length header")
            if digest is not None:
                digest.update(header)
            length_bytes = header[:8]
            length_crc = struct.unpack("<I", header[8:])[0]
            if _masked_crc32c(length_bytes) != length_crc:
                raise ValueError(f"invalid TFRecord length CRC at record {records}")
            (length,) = struct.unpack("<Q", length_bytes)
            if length > max_record_bytes:
                raise ValueError(f"TFRecord payload exceeds safety limit: {length}>{max_record_bytes}")
            payload = _read_exact(handle, length)
            trailer = _read_exact(handle, 4)
            if digest is not None:
                digest.update(payload)
                digest.update(trailer)
            payload_crc = struct.unpack("<I", trailer)[0]
            if _masked_crc32c(payload) != payload_crc:
                raise ValueError(f"invalid TFRecord payload CRC at record {records}")
            yield records, payload
            records += 1
    if records <= 0:
        raise ValueError("TFRecord file contains no records")


def iter_tfrecord_records(path: str | Path, *, max_record_bytes: int = 512 * 1024 * 1024) -> Iterator[tuple[int, bytes]]:
    """Yield (record_index, payload), checking CRC before yielding each record."""
    yield from _records(path, max_record_bytes)


def verify_tfrecord(path: str | Path, *, max_record_bytes: int = 512 * 1024 * 1024) -> TFRecordSummary:
    """Verify the entire shard and return SHA256 of its framing and payloads."""
    input_path = Path(path)
    digest = hashlib.sha256()
    records = payload_bytes = 0
    for _, payload in _records(input_path, max_record_bytes, digest):
        records += 1
        payload_bytes += len(payload)
    return TFRecordSummary(
        path=str(input_path.resolve()),
        records=records,
        payload_bytes=payload_bytes,
        file_bytes=input_path.stat().st_size,
        sha256=digest.hexdigest(),
    )


__all__ = ["TFRecordSummary", "iter_tfrecord_records", "verify_tfrecord"]
