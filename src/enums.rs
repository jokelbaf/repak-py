use pyo3::prelude::*;

#[pyclass(eq, eq_int, hash, frozen, module = "repak", from_py_object)]
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub enum Version {
    V0,
    V1,
    V2,
    V3,
    V4,
    V5,
    V6,
    V7,
    V8A,
    V8B,
    V9,
    V10,
    V11,
}

#[pymethods]
impl Version {
    /// Return the newest pak version supported by repak.
    #[staticmethod]
    pub fn latest() -> Self {
        repak::Version::iter()
            .next()
            .expect("repak exposes at least one version")
            .into()
    }
}

impl From<repak::Version> for Version {
    fn from(value: repak::Version) -> Self {
        match value {
            repak::Version::V0 => Self::V0,
            repak::Version::V1 => Self::V1,
            repak::Version::V2 => Self::V2,
            repak::Version::V3 => Self::V3,
            repak::Version::V4 => Self::V4,
            repak::Version::V5 => Self::V5,
            repak::Version::V6 => Self::V6,
            repak::Version::V7 => Self::V7,
            repak::Version::V8A => Self::V8A,
            repak::Version::V8B => Self::V8B,
            repak::Version::V9 => Self::V9,
            repak::Version::V10 => Self::V10,
            repak::Version::V11 => Self::V11,
        }
    }
}

impl From<Version> for repak::Version {
    fn from(value: Version) -> Self {
        match value {
            Version::V0 => Self::V0,
            Version::V1 => Self::V1,
            Version::V2 => Self::V2,
            Version::V3 => Self::V3,
            Version::V4 => Self::V4,
            Version::V5 => Self::V5,
            Version::V6 => Self::V6,
            Version::V7 => Self::V7,
            Version::V8A => Self::V8A,
            Version::V8B => Self::V8B,
            Version::V9 => Self::V9,
            Version::V10 => Self::V10,
            Version::V11 => Self::V11,
        }
    }
}

#[pyclass(eq, eq_int, hash, frozen, module = "repak", from_py_object)]
#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
#[allow(clippy::upper_case_acronyms)]
pub enum Compression {
    ZLIB,
    GZIP,
    OODLE,
    ZSTD,
    LZ4,
}

impl From<repak::Compression> for Compression {
    fn from(value: repak::Compression) -> Self {
        match value {
            repak::Compression::Zlib => Self::ZLIB,
            repak::Compression::Gzip => Self::GZIP,
            repak::Compression::Oodle => Self::OODLE,
            repak::Compression::Zstd => Self::ZSTD,
            repak::Compression::LZ4 => Self::LZ4,
        }
    }
}

impl From<Compression> for repak::Compression {
    fn from(value: Compression) -> Self {
        match value {
            Compression::ZLIB => Self::Zlib,
            Compression::GZIP => Self::Gzip,
            Compression::OODLE => Self::Oodle,
            Compression::ZSTD => Self::Zstd,
            Compression::LZ4 => Self::LZ4,
        }
    }
}
