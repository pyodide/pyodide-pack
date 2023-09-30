from __future__ import annotations

import json
from pathlib import Path

from pyodide_pack.dynamic_lib import DynamicLib


class RuntimeResults(dict):
    """Results from the execution of the runtime."""

    @property
    def stdlib_prefix(self):
        """Find the prefix for one of the stdlib modules loaded from the zip files

        Examples
        --------
        >>> db = RuntimeResults(sys_modules={"pathlib": "/lib/python311.zip/pathlib.py"})
        >>> db.stdlib_prefix
        '/lib/python311.zip'
        """
        return self["sys_modules"]["pathlib"].replace("/pathlib.py", "")

    def get_imported_paths(self, strip_prefix: str | None = None):
        """Get the paths of all imported modules.

        Optionally by stripping a prefix from the paths.

        Examples
        --------
        >>> db = RuntimeResults(sys_modules={
        ...         "pathlib": "/lib/python311.zip/pathlib.py",
        ...         "os": "/lib/python311.zip/os.py"},
        ...     opened_file_names=["/lib/python311.zip/pathlib.py"])
        >>> db.get_imported_paths()
        ['/lib/python311.zip/pathlib.py', '/lib/python311.zip/os.py']
        >>> db.get_imported_paths(strip_prefix="/lib/python311.zip")
        ['pathlib.py', 'os.py']
        """
        imported_paths = list(self["sys_modules"].values()) + self["opened_file_names"]
        if strip_prefix is not None:
            imported_paths = [
                path.replace(strip_prefix + "/", "")
                for path in imported_paths
                if path.startswith(strip_prefix)
            ]
        # Remove duplicates, relying on the fact that dict preserves insertion order
        imported_paths = list(dict.fromkeys(imported_paths))
        return imported_paths

    @classmethod
    def from_json(cls, path) -> RuntimeResults:
        """Load the results.json with runtime execution information."""
        with open(path) as fh:
            db = cls(json.load(fh))

        db["opened_file_names"] = [
            path for path in db["opened_file_names"] if "__pycache__" not in path
        ]
        # drop duplicates, while preserving order
        db["opened_file_names"] = list(dict.fromkeys(db["opened_file_names"]))

        db["dynamic_libs_map"] = {
            obj["path"]: DynamicLib(
                obj["path"], shared=obj.get("global", False), load_order=idx
            )
            for idx, obj in enumerate(db["load_dyn_lib_calls"])
            if obj["path"].endswith(".so") and obj["path"] in db["dl_accessed_symbols"]
        }
        return db

    def to_json(self, path: Path) -> None:
        """Save the results.json with runtime execution information."""
        with open(path, "w") as fh:
            json.dump(self, fh, indent=2, default=vars)
