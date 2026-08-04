use pyo3::prelude::*;

pyo3::create_exception!(repak, RepakError, pyo3::exceptions::PyException);
pyo3::create_exception!(repak, MissingEntryError, RepakError);
pyo3::create_exception!(repak, VersionError, RepakError);
pyo3::create_exception!(repak, EncryptionError, RepakError);
pyo3::create_exception!(repak, CompressionError, RepakError);
pyo3::create_exception!(repak, OodleError, RepakError);

pub fn to_pyerr(err: repak::Error) -> PyErr {
    let message = err.to_string();
    match err {
        repak::Error::Io(err) => err.into(),
        repak::Error::MissingEntry(_) => MissingEntryError::new_err(message),
        repak::Error::Aes | repak::Error::Encryption | repak::Error::Encrypted => {
            EncryptionError::new_err(message)
        }
        repak::Error::OodleFailed(err) => oodle_to_pyerr(err),
        repak::Error::Oodle => OodleError::new_err(message),
        repak::Error::Compression | repak::Error::DecompressionFailed(_) => {
            CompressionError::new_err(message)
        }
        repak::Error::Magic(_)
        | repak::Error::Version { .. }
        | repak::Error::UnsupportedOrEncrypted(_) => VersionError::new_err(message),
        _ => RepakError::new_err(message),
    }
}

pub fn oodle_to_pyerr(err: oodle_loader::Error) -> PyErr {
    match err {
        oodle_loader::Error::Io(err) => err.into(),
        _ => OodleError::new_err(err.to_string()),
    }
}

pub fn register(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("RepakError", module.py().get_type::<RepakError>())?;
    module.add(
        "MissingEntryError",
        module.py().get_type::<MissingEntryError>(),
    )?;
    module.add("VersionError", module.py().get_type::<VersionError>())?;
    module.add("EncryptionError", module.py().get_type::<EncryptionError>())?;
    module.add(
        "CompressionError",
        module.py().get_type::<CompressionError>(),
    )?;
    module.add("OodleError", module.py().get_type::<OodleError>())?;
    Ok(())
}
