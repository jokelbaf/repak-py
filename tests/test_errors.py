import base64
import pathlib

import pytest

import repak


def test_error_hierarchy() -> None:
    for error in (
        repak.MissingEntryError,
        repak.VersionError,
        repak.EncryptionError,
        repak.CompressionError,
    ):
        assert issubclass(error, repak.RepakError)
    assert issubclass(repak.RepakError, Exception)


def test_missing_entry(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader, pytest.raises(repak.MissingEntryError):
        reader.get("Absent.txt")


def test_garbage_input_raises_version_error(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "garbage.pak"
    path.write_bytes(b"not a pak file at all" * 16)
    with pytest.raises(repak.VersionError):
        repak.PakBuilder().reader(path)


def test_missing_file_raises_oserror(tmp_path: "pathlib.Path") -> None:
    with pytest.raises(FileNotFoundError):
        repak.PakBuilder().reader(tmp_path / "does-not-exist.pak")


@pytest.mark.parametrize(
    "key",
    [
        bytes(range(32)),
        "00" * 32,
        "0x" + "00" * 32,
        base64.b64encode(bytes(32)).decode(),
    ],
)
def test_accepted_key_formats(key: "str | bytes") -> None:
    assert isinstance(repak.PakBuilder().key(key), repak.PakBuilder)


@pytest.mark.parametrize("key", ["", "zz", "00" * 16, bytes(16)])
def test_rejected_key_formats(key: "str | bytes") -> None:
    with pytest.raises(repak.RepakError):
        repak.PakBuilder().key(key)


def test_key_must_be_str_or_bytes() -> None:
    with pytest.raises(TypeError):
        repak.PakBuilder().key(1234)  # pyright: ignore[reportArgumentType]
