"""Python bindings for repak, a library for Unreal Engine .pak files."""

from repak import _repak

MAGIC: "int" = _repak.MAGIC

Compression = _repak.Compression
PakBuilder = _repak.PakBuilder
PakReader = _repak.PakReader
PakWriter = _repak.PakWriter
Version = _repak.Version

CompressionError = _repak.CompressionError
EncryptionError = _repak.EncryptionError
MissingEntryError = _repak.MissingEntryError
OodleError = _repak.OodleError
RepakError = _repak.RepakError
VersionError = _repak.VersionError

oodle_library_path = _repak.oodle_library_path

__all__ = (
    "MAGIC",
    "Compression",
    "CompressionError",
    "EncryptionError",
    "MissingEntryError",
    "OodleError",
    "PakBuilder",
    "PakReader",
    "PakWriter",
    "RepakError",
    "Version",
    "VersionError",
    "oodle_library_path",
)
