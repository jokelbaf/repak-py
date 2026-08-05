import os
import pathlib
import typing

MAGIC: int

_Path: typing.TypeAlias = str | os.PathLike[str]
_Source: typing.TypeAlias = str | os.PathLike[str] | bytes

def oodle_library_path() -> pathlib.Path:
    """Return the path the Oodle library is loaded from or downloaded to."""

@typing.final
class Version:
    """Pak file format version."""

    V0: typing.ClassVar[Version]
    V1: typing.ClassVar[Version]
    V2: typing.ClassVar[Version]
    V3: typing.ClassVar[Version]
    V4: typing.ClassVar[Version]
    V5: typing.ClassVar[Version]
    V6: typing.ClassVar[Version]
    V7: typing.ClassVar[Version]
    V8A: typing.ClassVar[Version]
    V8B: typing.ClassVar[Version]
    V9: typing.ClassVar[Version]
    V10: typing.ClassVar[Version]
    V11: typing.ClassVar[Version]

    @staticmethod
    def latest() -> Version:
        """Return the newest pak version supported by repak."""

@typing.final
class Compression:
    """Compression algorithm used by a pak entry."""

    ZLIB: typing.ClassVar[Compression]
    GZIP: typing.ClassVar[Compression]
    OODLE: typing.ClassVar[Compression]
    ZSTD: typing.ClassVar[Compression]
    LZ4: typing.ClassVar[Compression]

@typing.final
class PakBuilder:
    """Configure encryption and compression, then open a pak reader or writer."""

    def __new__(cls) -> PakBuilder: ...
    def key(self, key: str | bytes) -> PakBuilder:
        """Return a builder using the given 256 bit AES key."""

    def compression(self, compression: typing.Sequence[Compression]) -> PakBuilder:
        """Return a builder allowed to use the given compression algorithms when writing."""

    def reader(self, source: _Source, *, pak_name: str | None = None) -> PakReader:
        """Open a pak from a path or bytes, detecting its version.

        Silver Palace paks derive their index key from the pak's file name, which
        is taken from source when it is a path. Pass pak_name to override it, or
        to supply one when source is bytes.
        """

    def reader_with_version(
        self, source: _Source, version: Version, *, pak_name: str | None = None
    ) -> PakReader:
        """Open a pak from a path or bytes using an explicit version."""

    def writer(
        self,
        path: _Path,
        *,
        version: Version | None = None,
        mount_point: str = "../../../",
        path_hash_seed: int | None = None,
    ) -> PakWriter:
        """Create a pak writer at the given path, truncating any existing file."""

@typing.final
class PakReader:
    """Read entries out of an opened pak file."""

    @property
    def version(self) -> Version:
        """Pak file format version."""

    @property
    def mount_point(self) -> str:
        """Mount point entry keys are relative to."""

    @property
    def encrypted_index(self) -> bool:
        """Whether the pak index is encrypted."""

    @property
    def encryption_guid(self) -> int | None:
        """Encryption key GUID, or None if the pak has none."""

    @property
    def path_hash_seed(self) -> int | None:
        """Seed used by the path hash index, or None if the pak has none."""

    @property
    def closed(self) -> bool:
        """Whether the underlying file has been closed."""

    def files(self) -> list[str]:
        """Return the path every entry in the pak mounts at."""

    def entries(self) -> list[str]:
        """Return the keys every entry in the pak is stored under, relative to the mount point."""

    def used_compression(self) -> list[Compression]:
        """Return the compression algorithms actually used by entries in the pak."""

    def get(self, path: str) -> bytes:
        """Read a single entry and return its contents."""

    def read_file(self, path: str, dest: _Path) -> None:
        """Read a single entry and write its contents to dest."""

    def unpack(self, directory: _Path) -> None:
        """Extract every entry into directory, recreating the pak's directory structure."""

    def into_writer(self, path: _Path) -> PakWriter:
        """Reopen the pak at path for writing, positioned to append new entries."""

    def close(self) -> None:
        """Close the underlying file."""

    def __enter__(self) -> PakReader: ...
    def __exit__(self, *args: object) -> bool: ...
    def __len__(self) -> int: ...
    def __contains__(self, path: str) -> bool: ...
    def __iter__(self) -> typing.Iterator[str]: ...

@typing.final
class PakWriter:
    """Write entries into a pak file."""

    @property
    def closed(self) -> bool:
        """Whether the index has already been written."""

    def write_file(self, path: str, data: bytes, *, compress: bool = True) -> None:
        """Write data into the pak at path, compressing it if the builder allows compression."""

    def write_index(self) -> None:
        """Write the index and close the pak, after which no more entries can be added."""

    def __enter__(self) -> PakWriter: ...
    def __exit__(self, *args: object) -> bool: ...

class RepakError(Exception):
    """Base class for every error raised by repak."""

class MissingEntryError(RepakError):
    """Raised when a requested entry is not present in the pak."""

class VersionError(RepakError):
    """Raised when a pak's version cannot be determined or is unsupported."""

class EncryptionError(RepakError):
    """Raised when a pak is encrypted and no usable key was provided."""

class CompressionError(RepakError):
    """Raised when entry data cannot be compressed or decompressed."""

class OodleError(RepakError):
    """Raised when the Oodle library is missing or cannot be loaded."""
