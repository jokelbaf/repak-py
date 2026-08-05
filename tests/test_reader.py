import pathlib

import pytest

import repak


def test_files_lists_every_entry(sample_pak: "pathlib.Path", entries: "dict[str, bytes]") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        assert sorted(reader.files()) == sorted(entries)


def test_get_returns_original_contents(
    sample_pak: "pathlib.Path", entries: "dict[str, bytes]"
) -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        for name, data in entries.items():
            assert reader.get(name) == data


def test_files_joins_the_mount_point(
    mounted_pak: "pathlib.Path", entries: "dict[str, bytes]"
) -> None:
    with repak.PakBuilder().reader(mounted_pak) as reader:
        assert sorted(reader.files()) == sorted(f"Game/Content/Sub/{name}" for name in entries)


def test_entries_keeps_the_stored_keys(
    mounted_pak: "pathlib.Path", entries: "dict[str, bytes]"
) -> None:
    with repak.PakBuilder().reader(mounted_pak) as reader:
        assert sorted(reader.entries()) == sorted(entries)


def test_get_accepts_either_form(mounted_pak: "pathlib.Path", entries: "dict[str, bytes]") -> None:
    with repak.PakBuilder().reader(mounted_pak) as reader:
        for name, data in entries.items():
            assert reader.get(f"Game/Content/Sub/{name}") == data
            assert reader.get(name) == data


def test_get_reports_a_missing_entry(mounted_pak: "pathlib.Path") -> None:
    with (
        repak.PakBuilder().reader(mounted_pak) as reader,
        pytest.raises(repak.MissingEntryError),
    ):
        reader.get("Game/Content/Sub/Absent.txt")


def test_read_file_accepts_either_form(
    mounted_pak: "pathlib.Path", entries: "dict[str, bytes]", tmp_path: "pathlib.Path"
) -> None:
    with repak.PakBuilder().reader(mounted_pak) as reader:
        reader.read_file("Game/Content/Sub/Readme.txt", tmp_path / "full.txt")
        reader.read_file("Readme.txt", tmp_path / "key.txt")

    assert (tmp_path / "full.txt").read_bytes() == entries["Readme.txt"]
    assert (tmp_path / "key.txt").read_bytes() == entries["Readme.txt"]


def test_mounted_container_protocol(
    mounted_pak: "pathlib.Path", entries: "dict[str, bytes]"
) -> None:
    with repak.PakBuilder().reader(mounted_pak) as reader:
        assert len(reader) == len(entries)
        assert "Game/Content/Sub/Readme.txt" in reader
        assert "Readme.txt" in reader
        assert "Game/Content/Sub/Absent.txt" not in reader
        assert sorted(reader) == sorted(f"Game/Content/Sub/{name}" for name in entries)


def test_unpack_recreates_the_mounted_layout(
    mounted_pak: "pathlib.Path", entries: "dict[str, bytes]", tmp_path: "pathlib.Path"
) -> None:
    out = tmp_path / "out"
    with repak.PakBuilder().reader(mounted_pak) as reader:
        reader.unpack(out)

    written = {
        path.relative_to(out).as_posix(): path.read_bytes()
        for path in out.rglob("*")
        if path.is_file()
    }
    assert written == {f"Game/Content/Sub/{name}": data for name, data in entries.items()}


def test_metadata(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        assert reader.version == repak.Version.latest()
        assert reader.mount_point == "../../../"
        assert reader.encrypted_index is False


def test_used_compression_reports_zlib(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        assert reader.used_compression() == [repak.Compression.ZLIB]


def test_container_protocol(sample_pak: "pathlib.Path", entries: "dict[str, bytes]") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        assert len(reader) == len(entries)
        assert "Readme.txt" in reader
        assert "Absent.txt" not in reader
        assert sorted(reader) == sorted(entries)


def test_reader_accepts_bytes(sample_pak: "pathlib.Path", entries: "dict[str, bytes]") -> None:
    with repak.PakBuilder().reader(sample_pak.read_bytes()) as reader:
        assert sorted(reader.files()) == sorted(entries)
        assert reader.get("Readme.txt") == entries["Readme.txt"]


def test_reader_accepts_str_path(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(str(sample_pak)) as reader:
        assert "Readme.txt" in reader


def test_reader_with_version(sample_pak: "pathlib.Path") -> None:
    builder = repak.PakBuilder()
    with builder.reader_with_version(sample_pak, repak.Version.latest()) as reader:
        assert "Readme.txt" in reader


def test_reader_accepts_pak_name(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(sample_pak.read_bytes(), pak_name="sample.pak") as reader:
        assert "Readme.txt" in reader


def test_reader_with_version_accepts_pak_name(sample_pak: "pathlib.Path") -> None:
    builder = repak.PakBuilder()
    version = repak.Version.latest()
    with builder.reader_with_version(sample_pak, version, pak_name="sample.pak") as reader:
        assert "Readme.txt" in reader


def test_read_file_writes_to_disk(
    sample_pak: "pathlib.Path", entries: "dict[str, bytes]", tmp_path: "pathlib.Path"
) -> None:
    dest = tmp_path / "extracted.uasset"
    with repak.PakBuilder().reader(sample_pak) as reader:
        reader.read_file("Content/Asset.uasset", dest)
    assert dest.read_bytes() == entries["Content/Asset.uasset"]


def test_unpack_recreates_directory_structure(
    sample_pak: "pathlib.Path", entries: "dict[str, bytes]", tmp_path: "pathlib.Path"
) -> None:
    out = tmp_path / "out"
    with repak.PakBuilder().reader(sample_pak) as reader:
        reader.unpack(out)

    written = {
        path.relative_to(out).as_posix(): path.read_bytes()
        for path in out.rglob("*")
        if path.is_file()
    }
    assert written == entries


def test_close_is_idempotent(sample_pak: "pathlib.Path") -> None:
    reader = repak.PakBuilder().reader(sample_pak)
    assert reader.closed is False
    reader.close()
    reader.close()
    assert reader.closed is True


def test_context_manager_closes(sample_pak: "pathlib.Path") -> None:
    with repak.PakBuilder().reader(sample_pak) as reader:
        assert reader.closed is False
    assert reader.closed is True


def test_closed_reader_raises(sample_pak: "pathlib.Path") -> None:
    reader = repak.PakBuilder().reader(sample_pak)
    reader.close()
    with pytest.raises(repak.RepakError, match="closed"):
        reader.get("Readme.txt")


def test_repr(sample_pak: "pathlib.Path") -> None:
    reader = repak.PakBuilder().reader(sample_pak)
    assert "PakReader" in repr(reader)
    reader.close()
    assert "closed" in repr(reader)
