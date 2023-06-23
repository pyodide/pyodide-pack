import os
from pathlib import Path


def _get_stdlib_module_paths() -> list[Path]:
    """Return a list of paths to the standard library modules.

    This is mainly used for testing purposes.
    """
    base_dir = Path(os.__file__).parent
    res = []
    for path in base_dir.glob("**/*.py"):
        if "test" in str(path):
            # There are test files in the standard library, skip them
            continue
        if path.parts[-4:-1] == ("lib2to3", "tests", "data"):
            # There are files in this folder with either Python2 or bad encoding, skip them
            continue
        res.append(path)
    return res
