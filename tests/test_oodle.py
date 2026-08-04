import pathlib

import pytest

import repak

PAYLOAD = bytes(range(256)) * 512


def test_library_path_is_platform_specific() -> None:
    assert repak.oodle_library_path().name.startswith(("liboo2core", "oo2core_"))


def test_library_path_sits_next_to_the_extension_module() -> None:
    assert repak.oodle_library_path().parent == pathlib.Path(repak.__file__).parent


def test_env_var_overrides_the_path(
    monkeypatch: "pytest.MonkeyPatch", tmp_path: "pathlib.Path"
) -> None:
    override = tmp_path / "custom-oodle.so"
    monkeypatch.setenv("REPAK_OODLE_PATH", str(override))
    assert repak.oodle_library_path() == override


def test_oodle_error_is_a_repak_error() -> None:
    assert issubclass(repak.OodleError, repak.RepakError)


def test_requesting_oodle_installs_the_library() -> None:
    repak.PakBuilder().compression([repak.Compression.OODLE])
    assert repak.oodle_library_path().is_file()


def test_oodle_round_trip(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "oodle.pak"
    builder = repak.PakBuilder().compression([repak.Compression.OODLE])
    with builder.writer(path) as writer:
        writer.write_file("Content/Big.uasset", PAYLOAD)

    with repak.PakBuilder().reader(path) as reader:
        assert reader.used_compression() == [repak.Compression.OODLE]
        assert reader.get("Content/Big.uasset") == PAYLOAD


def test_oodle_pak_is_smaller_than_its_input(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "compressed.pak"
    builder = repak.PakBuilder().compression([repak.Compression.OODLE])
    with builder.writer(path) as writer:
        writer.write_file("Content/Big.uasset", PAYLOAD)

    assert path.stat().st_size < len(PAYLOAD)
