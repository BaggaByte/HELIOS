"""
Hashing helpers for evidence integrity and malware triage.

`helios/core/evidence/manager.py` already had its own local `calculate_hash`
for the evidence chain — this module is the shared, general-purpose version
used by malware analysis, deduplication (e.g. "have we seen this JS bundle
before?"), and anywhere else a file's identity needs to be checked without
duplicating hashing logic per module.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, Union

_CHUNK_SIZE = 1024 * 1024  # 1 MiB — keeps memory flat for large binaries/PCAPs

SUPPORTED_ALGOS = ("md5", "sha1", "sha256", "sha512")


def hash_bytes(data: bytes, algo: str = "sha256") -> str:
    """Return the hex digest of `data` using `algo`."""
    if algo not in SUPPORTED_ALGOS:
        raise ValueError(f"Unsupported hash algorithm: {algo!r}")
    h = hashlib.new(algo)
    h.update(data)
    return h.hexdigest()


def hash_file(path: Union[str, Path], algo: str = "sha256") -> str:
    """Stream-hash a file on disk without loading it fully into memory."""
    if algo not in SUPPORTED_ALGOS:
        raise ValueError(f"Unsupported hash algorithm: {algo!r}")
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_all(data: bytes) -> Dict[str, str]:
    """
    Compute md5 + sha1 + sha256 + sha512 of `data` in a single pass.
    Convenient for malware triage / evidence records that store every
    common digest for a submitted artifact.
    """
    hashers = {algo: hashlib.new(algo) for algo in SUPPORTED_ALGOS}
    for h in hashers.values():
        h.update(data)
    return {algo: h.hexdigest() for algo, h in hashers.items()}


def hash_file_all(path: Union[str, Path]) -> Dict[str, str]:
    """Stream-hash a file on disk, computing all supported algorithms at once."""
    hashers = {algo: hashlib.new(algo) for algo in SUPPORTED_ALGOS}
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(_CHUNK_SIZE), b""):
            for h in hashers.values():
                h.update(chunk)
    return {algo: h.hexdigest() for algo, h in hashers.items()}
