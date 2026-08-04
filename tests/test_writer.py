import pathlib

import pytest

import repak


def test_write_index_explicitly(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "explicit.pak"
    writer = repak.PakBuilder().writer(path)
    writer.write_file("Readme.txt", b"hello")
    assert writer.closed is False
    writer.write_index()
    assert writer.closed is True

    with repak.PakBuilder().reader(path) as reader:
        assert reader.get("Readme.txt") == b"hello"


def test_context_manager_writes_index(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "managed.pak"
    with repak.PakBuilder().writer(path) as writer:
        writer.write_file("Readme.txt", b"hello")
    assert writer.closed is True

    with repak.PakBuilder().reader(path) as reader:
        assert reader.files() == ["Readme.txt"]


def test_exception_leaves_index_unwritten(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "aborted.pak"
    with pytest.raises(RuntimeError, match="boom"), repak.PakBuilder().writer(path) as writer:  # noqa: PT012
        writer.write_file("Readme.txt", b"hello")
        raise RuntimeError("boom")

    assert writer.closed is True
    with pytest.raises(repak.RepakError):
        repak.PakBuilder().reader(path)


def test_writing_after_close_raises(tmp_path: "pathlib.Path") -> None:
    writer = repak.PakBuilder().writer(tmp_path / "closed.pak")
    writer.write_index()
    with pytest.raises(repak.RepakError, match="closed"):
        writer.write_file("Readme.txt", b"hello")


def test_no_compression_without_builder_opt_in(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "plain.pak"
    with repak.PakBuilder().writer(path) as writer:
        writer.write_file("Readme.txt", b"hello " * 128)

    with repak.PakBuilder().reader(path) as reader:
        assert reader.used_compression() == []
        assert reader.get("Readme.txt") == b"hello " * 128


def test_compress_false_skips_compression(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "uncompressed.pak"
    builder = repak.PakBuilder().compression([repak.Compression.ZLIB])
    with builder.writer(path) as writer:
        writer.write_file("Readme.txt", b"hello " * 128, compress=False)

    with repak.PakBuilder().reader(path) as reader:
        assert reader.used_compression() == []
        assert reader.get("Readme.txt") == b"hello " * 128


def test_custom_mount_point(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "mounted.pak"
    with repak.PakBuilder().writer(path, mount_point="../../") as writer:
        writer.write_file("Readme.txt", b"hello")

    with repak.PakBuilder().reader(path) as reader:
        assert reader.mount_point == "../../"


def test_path_hash_seed_round_trips(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "seeded.pak"
    with repak.PakBuilder().writer(path, path_hash_seed=1234) as writer:
        writer.write_file("Readme.txt", b"hello")

    with repak.PakBuilder().reader(path) as reader:
        assert reader.path_hash_seed == 1234


def test_into_writer_appends(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "appended.pak"
    with repak.PakBuilder().writer(path) as writer:
        writer.write_file("First.txt", b"first")

    reader = repak.PakBuilder().reader(path)
    with reader.into_writer(path) as writer:
        writer.write_file("Second.txt", b"second")
    assert reader.closed is True

    with repak.PakBuilder().reader(path) as reopened:
        assert sorted(reopened.files()) == ["First.txt", "Second.txt"]
        assert reopened.get("First.txt") == b"first"
        assert reopened.get("Second.txt") == b"second"


def test_writer_accepts_str_path(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "stringly.pak"
    with repak.PakBuilder().writer(str(path)) as writer:
        writer.write_file("Readme.txt", b"hello")
    assert path.exists()


def test_empty_pak(tmp_path: "pathlib.Path") -> None:
    path = tmp_path / "empty.pak"
    with repak.PakBuilder().writer(path):
        pass

    with repak.PakBuilder().reader(path) as reader:
        assert reader.files() == []
        assert len(reader) == 0
