import json
from pathlib import Path
from typing import Any

from pyodide_lock import PyodideLockSpec

from pyodide_pack.archive import ArchiveFile
from pyodide_pack.dynamic_lib import DynamicLib


def _load_results_json(path) -> dict[str, Any]:
    """Load the results.json with runtime execution information."""
    with open(path) as fh:
        db = json.load(fh)

    db["opened_file_names"] = list(
        {path for path in db["opened_file_names"] if "__pycache__" not in path}
    )
    db["dynamic_libs_map"] = {
        path: DynamicLib(path, load_order=idx)
        for idx, path in enumerate(db["find_object_calls"])
        if path.endswith(".so")
    }
    return db


def _get_packages_from_lockfile(
    pyodide_lock: PyodideLockSpec, loaded_packages: dict[str, str], package_dir: Path
) -> dict[str, ArchiveFile]:
    """Get the dictionary of packages from a lockfile wrapped into ArchiveFile objects."""
    packages: dict[str, ArchiveFile] = {}
    for key, val in loaded_packages.items():
        if val == "default channel":
            file_name = pyodide_lock.packages[key].file_name
        else:
            # Otherwise loaded from custom URL
            # TODO: this branch needs testing
            file_name = val

        packages[file_name] = ArchiveFile(package_dir / file_name, name=key)
    return packages
