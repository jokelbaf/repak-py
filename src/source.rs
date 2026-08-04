use std::fs;
use std::io;

pub enum Source {
    File(io::BufReader<fs::File>),
    Memory(io::Cursor<Vec<u8>>),
}

impl io::Read for Source {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        match self {
            Self::File(r) => r.read(buf),
            Self::Memory(r) => r.read(buf),
        }
    }
}

impl io::Seek for Source {
    fn seek(&mut self, pos: io::SeekFrom) -> io::Result<u64> {
        match self {
            Self::File(r) => r.seek(pos),
            Self::Memory(r) => r.seek(pos),
        }
    }
}
