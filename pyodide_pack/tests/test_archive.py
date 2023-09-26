import io
import tarfile
import zipfile

import pytest

from pyodide_pack.archive import ArchiveFile


@pytest.mark.parametrize("format_", ["tar", "zip"])
def test_archive(format_, tmp_path):
    file_path = tmp_path / ("test." + format_)
    if format_ == "tar":
        with tarfile.open(file_path, "w") as fh:
            buff = io.BytesIO(b"test")
            tarinfo = tarfile.TarInfo(name="a/b.py")
            tarinfo.size = 4
            fh.addfile(tarinfo, fileobj=buff)
    elif format_ in ["zip", "whl"]:
        with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as fh:
            with fh.open("a/b.py", "w") as fh_el:
                fh_el.write(b"test")
    assert file_path.exists()

    ar = ArchiveFile(file_path, name="test")
    assert ar.name == "test"
    assert ar.namelist() == ["a/b.py"]

    with ar as ar_context:
        assert ar_context is ar

    ar = ArchiveFile(file_path, name="test")
    assert ar.read("a/b.py") == b"test"

    assert ar.total_size(compressed=False) == 4
    # For this example the gzip compression has an overhead of 20 bytes
    assert ar.total_size(compressed=True) == 24


def test_archive_filter_to_zip(tmp_path):
    file_path = tmp_path / "test.zip"
    with zipfile.ZipFile(file_path, "w", compression=zipfile.ZIP_DEFLATED) as fh:
        for key in "abcd":
            with fh.open(f"{key}.py", "w") as fh_el:
                fh_el.write(b"test" + bytes(key, "utf-8"))
    assert file_path.exists()

    ar = ArchiveFile(file_path, name="test")
    assert ar.name == "test"
    assert ar.namelist() == ["a.py", "b.py", "c.py", "d.py"]

    ar_stripped = ar.filter_to_zip(
        tmp_path / "test_stripped.zip", lambda x: x != "b.py"
    )
    assert ar_stripped.namelist() == ["a.py", "c.py", "d.py"]
