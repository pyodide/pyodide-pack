import functools
import gzip
import tarfile
import zipfile
from pathlib import Path


class ArchiveFile:
    """A wrapper to access .zip, .whl and .tar files with the same API

    We are only interested in reading archive files, not writing them.
    The archive is assumed to be immutable.
    """

    def __init__(self, file_path: Path, name: str | None):
        self.file_path = file_path
        if name is not None:
            self.name = name
        else:
            self.name = file_path.name
        if file_path.suffix in [".whl", ".zip"]:
            self.opener = zipfile.ZipFile(file_path)
        elif file_path.suffix in [".tar"]:
            self.opener = tarfile.TarFile(file_path)  # type: ignore
        else:
            raise NotImplementedError

    def namelist(self):
        if isinstance(self.opener, zipfile.ZipFile):
            return self.opener.namelist()
        else:
            return self.opener.getnames()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.opener.close()

    def read(self, name: str, **kwargs):
        if isinstance(self.opener, zipfile.ZipFile):
            with self.opener.open(name, **kwargs) as fh:
                return fh.read()
        else:
            fh = self.opener.extractfile(name, **kwargs)
            if fh is not None:
                return fh.read()
            else:
                return None

    @functools.cache
    def total_size(self, compressed: bool = False) -> int:
        """Get total size of files in the archive in bytes

        This ignores the archive metadata, so size might differ slightly from a
        .tar.gz file.

        Parameters
        ----------
        compressed
            if True total size if returned for gzip compressed files.
            Otherwise size is for uncompressed files.
        """
        size = 0
        for name in self.namelist():
            stream = self.read(name)
            if stream is None:
                continue
            if compressed:
                stream = gzip.compress(stream)
            size += len(stream)
        return size
