import sys
import zipfile
from io import BytesIO

import pytest

from pyodide_pack.testing import _get_stdlib_module_paths


@pytest.fixture(scope="session")
def example_zipfile_xml() -> bytes:
    """Example zip file (as bytes) containing the xml related modules."""
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as zf:
        for path in _get_stdlib_module_paths():
            if "xml" not in str(path):
                continue
            zf.write(path, path.relative_to(sys.prefix))

    stream.seek(0)

    return stream.read()
