import pathlib

import pytest

import repak


def test_latest_is_a_known_version() -> None:
    assert repak.Version.latest() is repak.Version.V11


def test_versions_compare_by_identity() -> None:
    assert repak.Version.V11 == repak.Version.V11
    assert repak.Version.V11 != repak.Version.V10


def test_versions_are_hashable() -> None:
    assert {repak.Version.V10, repak.Version.V11, repak.Version.V10} == {
        repak.Version.V10,
        repak.Version.V11,
    }


def test_compression_members_are_distinct() -> None:
    members = {
        repak.Compression.ZLIB,
        repak.Compression.GZIP,
        repak.Compression.OODLE,
        repak.Compression.ZSTD,
        repak.Compression.LZ4,
    }
    assert len(members) == 5


def test_magic_is_exposed() -> None:
    assert repak.MAGIC == 0x5A6F12E1


@pytest.mark.parametrize(
    "version",
    [
        repak.Version.V0,
        repak.Version.V3,
        repak.Version.V5,
        repak.Version.V7,
        repak.Version.V8A,
        repak.Version.V8B,
        repak.Version.V9,
        repak.Version.V10,
        repak.Version.V11,
    ],
)
def test_every_version_round_trips(tmp_path: "pathlib.Path", version: "repak.Version") -> None:
    path = tmp_path / "versioned.pak"
    with repak.PakBuilder().writer(path, version=version) as writer:
        writer.write_file("Content/Asset.uasset", b"payload")

    with repak.PakBuilder().reader(path) as reader:
        assert reader.version == version
        assert reader.get("Content/Asset.uasset") == b"payload"
