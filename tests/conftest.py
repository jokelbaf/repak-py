"""Shared fixtures for the repak test suite."""

import pathlib

import pytest

import repak

ENTRIES: "dict[str, bytes]" = {
    "Content/Asset.uasset": b"asset payload " * 64,
    "Content/Nested/Data.bin": bytes(range(256)),
    "Readme.txt": b"hello",
}


@pytest.fixture
def entries() -> "dict[str, bytes]":
    """Return the entries written into the sample pak."""
    return dict(ENTRIES)


@pytest.fixture
def sample_pak(tmp_path: "pathlib.Path", entries: "dict[str, bytes]") -> "pathlib.Path":
    """Return the path of a zlib compressed pak holding the sample entries."""
    path = tmp_path / "sample.pak"
    builder = repak.PakBuilder().compression([repak.Compression.ZLIB])
    with builder.writer(path) as writer:
        for name, data in entries.items():
            writer.write_file(name, data)
    return path
