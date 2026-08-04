mod enums;
mod error;
mod source;

use pyo3::prelude::*;
use std::io::Write;

use enums::{Compression, Version};
use error::{RepakError, to_pyerr};
use source::Source;

type FileWriter = std::io::BufWriter<std::fs::File>;

fn parse_key(value: &Bound<'_, PyAny>) -> PyResult<aes::Aes256> {
    use aes::cipher::KeyInit;
    use base64::Engine as _;

    let invalid = || RepakError::new_err("expected a 256 bit AES key as bytes, hex or base64");

    if let Ok(bytes) = value.cast::<pyo3::types::PyBytes>() {
        return aes::Aes256::new_from_slice(bytes.as_bytes()).map_err(|_| invalid());
    }

    let text: String = value.extract()?;
    let from_slice = |bytes: Vec<u8>| aes::Aes256::new_from_slice(&bytes).ok();
    hex::decode(text.strip_prefix("0x").unwrap_or(&text))
        .ok()
        .and_then(from_slice)
        .or_else(|| {
            base64::engine::general_purpose::STANDARD_NO_PAD
                .decode(text.trim_end_matches('='))
                .ok()
                .and_then(from_slice)
        })
        .ok_or_else(invalid)
}

fn open_source(value: &Bound<'_, PyAny>) -> PyResult<Source> {
    if let Ok(bytes) = value.cast::<pyo3::types::PyBytes>() {
        return Ok(Source::Memory(std::io::Cursor::new(
            bytes.as_bytes().to_vec(),
        )));
    }

    let path: std::path::PathBuf = value.extract()?;

    Ok(Source::File(std::io::BufReader::new(std::fs::File::open(
        path,
    )?)))
}

/// Configure encryption and compression, then open a pak reader or writer.
#[pyclass(module = "repak", skip_from_py_object)]
#[derive(Clone, Default)]
pub struct PakBuilder {
    key: Option<aes::Aes256>,
    compression: Vec<repak::Compression>,
}

impl PakBuilder {
    fn build(&self) -> repak::PakBuilder {
        let mut builder = repak::PakBuilder::new();

        if let Some(key) = &self.key {
            builder = builder.key(key.clone());
        }

        if !self.compression.is_empty() {
            builder = builder.compression(self.compression.iter().copied());
        }

        builder
    }
}

#[pymethods]
impl PakBuilder {
    #[new]
    fn new() -> Self {
        Self::default()
    }

    /// Return a builder using the given 256 bit AES key.
    fn key(&self, key: &Bound<'_, PyAny>) -> PyResult<Self> {
        Ok(Self {
            key: Some(parse_key(key)?),
            compression: self.compression.clone(),
        })
    }

    /// Return a builder allowed to use the given compression algorithms when writing.
    fn compression(&self, py: Python<'_>, compression: Vec<Compression>) -> PyResult<Self> {
        let compression: Vec<repak::Compression> =
            compression.into_iter().map(Into::into).collect();

        if compression.contains(&repak::Compression::Oodle) {
            py.detach(|| oodle_loader::oodle().map_err(error::oodle_to_pyerr))?;
        }

        Ok(Self {
            key: self.key.clone(),
            compression,
        })
    }

    /// Open a pak from a path or bytes, detecting its version.
    fn reader(&self, py: Python<'_>, source: &Bound<'_, PyAny>) -> PyResult<PakReader> {
        let mut source = open_source(source)?;
        let builder = self.build();
        let pak = py.detach(|| builder.reader(&mut source).map_err(to_pyerr))?;
        Ok(PakReader::new(pak, source))
    }

    /// Open a pak from a path or bytes using an explicit version.
    fn reader_with_version(
        &self,
        py: Python<'_>,
        source: &Bound<'_, PyAny>,
        version: Version,
    ) -> PyResult<PakReader> {
        let mut source = open_source(source)?;
        let builder = self.build();

        let pak = py.detach(|| {
            builder
                .reader_with_version(&mut source, version.into())
                .map_err(to_pyerr)
        })?;

        Ok(PakReader::new(pak, source))
    }

    /// Create a pak writer at the given path, truncating any existing file.
    #[pyo3(signature = (path, *, version = None, mount_point = "../../../".to_owned(), path_hash_seed = None))]
    fn writer(
        &self,
        path: std::path::PathBuf,
        version: Option<Version>,
        mount_point: String,
        path_hash_seed: Option<u64>,
    ) -> PyResult<PakWriter> {
        let file = std::fs::File::create(path)?;
        let version = version.unwrap_or_else(Version::latest).into();

        Ok(PakWriter::new(self.build().writer(
            std::io::BufWriter::new(file),
            version,
            mount_point,
            path_hash_seed,
        )))
    }
}

struct ReaderState {
    pak: repak::PakReader,
    source: Source,
}

/// Read entries out of an opened pak file.
#[pyclass(module = "repak", skip_from_py_object)]
pub struct PakReader {
    state: std::sync::Mutex<Option<ReaderState>>,
}

impl PakReader {
    fn new(pak: repak::PakReader, source: Source) -> Self {
        Self {
            state: std::sync::Mutex::new(Some(ReaderState { pak, source })),
        }
    }

    fn with_state<T>(&self, f: impl FnOnce(&mut ReaderState) -> PyResult<T>) -> PyResult<T> {
        let mut guard = self.state.lock().unwrap_or_else(|err| err.into_inner());
        match guard.as_mut() {
            Some(state) => f(state),
            None => Err(RepakError::new_err("pak reader is closed")),
        }
    }
}

#[pymethods]
impl PakReader {
    /// Return the pak file format version.
    #[getter]
    fn version(&self) -> PyResult<Version> {
        self.with_state(|state| Ok(state.pak.version().into()))
    }

    /// Return the mount point all entry paths are relative to.
    #[getter]
    fn mount_point(&self) -> PyResult<String> {
        self.with_state(|state| Ok(state.pak.mount_point().to_owned()))
    }

    /// Return whether the pak index is encrypted.
    #[getter]
    fn encrypted_index(&self) -> PyResult<bool> {
        self.with_state(|state| Ok(state.pak.encrypted_index()))
    }

    /// Return the encryption key GUID, or None if the pak has none.
    #[getter]
    fn encryption_guid(&self) -> PyResult<Option<u128>> {
        self.with_state(|state| Ok(state.pak.encryption_guid()))
    }

    /// Return the seed used by the path hash index, or None if the pak has none.
    #[getter]
    fn path_hash_seed(&self) -> PyResult<Option<u64>> {
        self.with_state(|state| Ok(state.pak.path_hash_seed()))
    }

    /// Return whether the underlying file has been closed.
    #[getter]
    fn closed(&self) -> bool {
        self.state
            .lock()
            .unwrap_or_else(|err| err.into_inner())
            .is_none()
    }

    /// Return the paths of every entry in the pak.
    fn files(&self) -> PyResult<Vec<String>> {
        self.with_state(|state| Ok(state.pak.files()))
    }

    /// Return the compression algorithms actually used by entries in the pak.
    fn used_compression(&self) -> PyResult<Vec<Compression>> {
        self.with_state(|state| {
            Ok(state
                .pak
                .used_compression()
                .into_iter()
                .map(Into::into)
                .collect())
        })
    }

    /// Read a single entry and return its contents.
    fn get<'py>(
        &self,
        py: Python<'py>,
        path: String,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let data = py.detach(|| {
            self.with_state(|state| state.pak.get(&path, &mut state.source).map_err(to_pyerr))
        })?;
        Ok(pyo3::types::PyBytes::new(py, &data))
    }

    /// Read a single entry and write its contents to dest.
    fn read_file(&self, py: Python<'_>, path: String, dest: std::path::PathBuf) -> PyResult<()> {
        py.detach(|| {
            let mut writer = std::io::BufWriter::new(std::fs::File::create(dest)?);
            self.with_state(|state| {
                state
                    .pak
                    .read_file(&path, &mut state.source, &mut writer)
                    .map_err(to_pyerr)
            })?;
            writer.flush()?;
            Ok(())
        })
    }

    /// Extract every entry into directory, recreating the pak's directory structure.
    fn unpack(&self, py: Python<'_>, directory: std::path::PathBuf) -> PyResult<()> {
        py.detach(|| {
            self.with_state(|state| {
                for path in state.pak.files() {
                    let relative = std::path::Path::new(&path);
                    let contained = relative
                        .components()
                        .all(|part| matches!(part, std::path::Component::Normal(_)));

                    if !contained {
                        return Err(RepakError::new_err(format!(
                            "entry \"{path}\" would be written outside of the output directory"
                        )));
                    }

                    let dest = directory.join(relative);
                    if let Some(parent) = dest.parent() {
                        std::fs::create_dir_all(parent)?;
                    }

                    let mut writer = std::io::BufWriter::new(std::fs::File::create(dest)?);
                    
                    state
                        .pak
                        .read_file(&path, &mut state.source, &mut writer)
                        .map_err(to_pyerr)?;

                    writer.flush()?;
                }
                Ok(())
            })
        })
    }

    /// Reopen the pak at path for writing, positioned to append new entries.
    #[allow(clippy::wrong_self_convention)]
    fn into_writer(&self, path: std::path::PathBuf) -> PyResult<PakWriter> {
        let state = self
            .state
            .lock()
            .unwrap_or_else(|err| err.into_inner())
            .take()
            .ok_or_else(|| RepakError::new_err("pak reader is closed"))?;

        let file = std::fs::OpenOptions::new()
            .read(true)
            .write(true)
            .open(path)?;

        let writer = state
            .pak
            .into_pakwriter(std::io::BufWriter::new(file))
            .map_err(to_pyerr)?;

        Ok(PakWriter::new(writer))
    }

    /// Close the underlying file.
    fn close(&self) {
        *self.state.lock().unwrap_or_else(|err| err.into_inner()) = None;
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    #[pyo3(signature = (*_args))]
    fn __exit__(&self, _args: &Bound<'_, pyo3::types::PyTuple>) -> bool {
        self.close();
        false
    }

    fn __len__(&self) -> PyResult<usize> {
        self.with_state(|state| Ok(state.pak.files().len()))
    }

    fn __contains__(&self, path: String) -> PyResult<bool> {
        self.with_state(|state| Ok(state.pak.files().contains(&path)))
    }

    fn __iter__<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, pyo3::types::PyIterator>> {
        let files = self.files()?;
        pyo3::types::PyList::new(py, files)?.into_any().try_iter()
    }

    fn __repr__(&self) -> String {
        match self.with_state(|state| Ok((state.pak.version(), state.pak.files().len()))) {
            Ok((version, files)) => format!("<PakReader version={version} files={files}>"),
            Err(_) => "<PakReader closed>".to_owned(),
        }
    }
}

/// Write entries into a pak file.
#[pyclass(module = "repak", skip_from_py_object)]
pub struct PakWriter {
    inner: std::sync::Mutex<Option<repak::PakWriter<FileWriter>>>,
}

impl PakWriter {
    fn new(writer: repak::PakWriter<FileWriter>) -> Self {
        Self {
            inner: std::sync::Mutex::new(Some(writer)),
        }
    }
}

#[pymethods]
impl PakWriter {
    /// Return whether the index has already been written.
    #[getter]
    fn closed(&self) -> bool {
        self.inner
            .lock()
            .unwrap_or_else(|err| err.into_inner())
            .is_none()
    }

    /// Write data into the pak at path, compressing it if the builder allows compression.
    #[pyo3(signature = (path, data, *, compress = true))]
    fn write_file(
        &self,
        py: Python<'_>,
        path: String,
        data: Vec<u8>,
        compress: bool,
    ) -> PyResult<()> {
        py.detach(|| {
            let mut guard = self.inner.lock().unwrap_or_else(|err| err.into_inner());
            let writer = guard
                .as_mut()
                .ok_or_else(|| RepakError::new_err("pak writer is closed"))?;
            writer.write_file(&path, compress, data).map_err(to_pyerr)
        })
    }

    /// Write the index and close the pak, after which no more entries can be added.
    fn write_index(&self, py: Python<'_>) -> PyResult<()> {
        py.detach(|| {
            let writer = self
                .inner
                .lock()
                .unwrap_or_else(|err| err.into_inner())
                .take()
                .ok_or_else(|| RepakError::new_err("pak writer is closed"))?;

            let mut file = writer.write_index().map_err(to_pyerr)?;
            file.flush()?;
            file.get_ref().sync_all()?;

            Ok(())
        })
    }

    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    #[pyo3(signature = (exc_type = None, exc_value = None, traceback = None))]
    fn __exit__(
        &self,
        py: Python<'_>,
        exc_type: Option<&Bound<'_, PyAny>>,
        exc_value: Option<&Bound<'_, PyAny>>,
        traceback: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<bool> {
        let (_, _) = (exc_value, traceback);

        if exc_type.is_some() {
            *self.inner.lock().unwrap_or_else(|err| err.into_inner()) = None;
        } else if !self.closed() {
            self.write_index(py)?;
        }

        Ok(false)
    }

    fn __repr__(&self) -> String {
        if self.closed() {
            "<PakWriter closed>".to_owned()
        } else {
            "<PakWriter open>".to_owned()
        }
    }
}

/// Return the path the Oodle library is loaded from or downloaded to.
#[pyfunction]
fn oodle_library_path() -> std::path::PathBuf {
    oodle_loader::library_path()
}

#[pymodule]
fn _repak(module: &Bound<'_, PyModule>) -> PyResult<()> {
    if let Ok(filename) = module.filename()
        && let Ok(filename) = filename.to_str()
        && let Some(parent) = std::path::Path::new(filename).parent()
    {
        oodle_loader::set_library_dir(parent.to_path_buf());
    }

    module.add_function(wrap_pyfunction!(oodle_library_path, module)?)?;
    module.add("MAGIC", repak::MAGIC)?;
    module.add_class::<Compression>()?;
    module.add_class::<PakBuilder>()?;
    module.add_class::<PakReader>()?;
    module.add_class::<PakWriter>()?;
    module.add_class::<Version>()?;
    error::register(module)?;
    Ok(())
}
