# repak

Python bindings for [repak](https://github.com/trumank/repak), a Rust library for reading and writing Unreal Engine `.pak` files.

## Installation

```sh
# Using pip
pip install repak

# Using uv
uv add repak

# Using poetry
poetry add repak
```

Prebuilt wheels are published for Linux, macOS and Windows. A single abi3 wheel per platform covers CPython 3.10 and newer, including 3.14. No Rust toolchain is required.

## Reading

```python
import repak

with repak.PakBuilder().reader("game.pak") as pak:
    print(pak.version, pak.mount_point)

    for path in pak:
        print(path)

    data = pak.get("Content/Asset.uasset")
    pak.read_file("Content/Asset.uasset", "Asset.uasset")
    pak.unpack("out")
```

`PakReader` supports `len()`, `in` and iteration over entry paths. A pak may also be read from memory by passing `bytes` instead of a path.

## Writing

```python
import repak

builder = repak.PakBuilder().compression([repak.Compression.ZLIB])

with builder.writer("mod.pak") as pak:
    pak.write_file("Content/Asset.uasset", data)
```

The index is written when the `with` block exits. Without a context manager, call `write_index()` yourself. Entries are only compressed if the builder was given a compression algorithm.

To append to an existing pak, turn a reader into a writer:

```python
import repak

reader = repak.PakBuilder().reader("mod.pak")
with reader.into_writer("mod.pak") as pak:
    pak.write_file("Content/Extra.uasset", data)
```

## Encryption

```python
import repak

pak = repak.PakBuilder().key("0x0123456789abcdef...").reader("game.pak")
```

The key is a 256 bit AES key given as `bytes`, a hex string with an optional `0x` prefix, or base64.

## Oodle

Oodle works out of the box:

```python
import repak

builder = repak.PakBuilder().compression([repak.Compression.OODLE])
```

The Oodle library is proprietary and cannot be shipped inside the wheel, so **repak downloads it on first use**, the first time an Oodle pak is read or written.

To avoid the download, or when the install directory is not writable, point `REPAK_OODLE_PATH` at a copy you already have. That also lets you substitute a different Oodle version:

```sh
export REPAK_OODLE_PATH=/opt/oodle/liboo2corelinux64.so.9
```

`repak.oodle_library_path()` returns the path in use. If the library cannot be fetched or loaded, Oodle operations raise `repak.OodleError`.

## Errors

All failures raise `repak.RepakError` or one of its subclasses: `MissingEntryError`, `VersionError`, `EncryptionError` and `CompressionError`. Filesystem failures raise the usual `OSError`.

## Versioning

The package version tracks the version of the upstream `repak` crate it wraps. Fixes to the bindings alone are released as post releases, for example `0.2.3.post1`.

Upstream resolves the Oodle library relative to the running executable, which inside a Python extension is the interpreter and is often not writable. `vendor/oodle_loader` replaces that crate through a cargo `[patch]` entry so the path is resolvable, without forking repak itself.

## Development

The preferred dev environment requires Python 3.14 and Rust nightly toolchain, pinned in `rust-toolchain.toml`.

```sh
uv sync
uv run pytest
uv run ruff check
uv run ruff format
uv run pyright
cargo clippy --all-targets
cargo fmt
```

`uv sync` compiles the extension module. Use `uv run maturin develop --uv` to rebuild it after changing Rust code.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
