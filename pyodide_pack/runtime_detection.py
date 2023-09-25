from __future__ import annotations

import json

from pyodide_pack.dynamic_lib import DynamicLib


class RuntimeResults(dict):
    """Results from the execution of the runtime."""

    @property
    def stdlib_prefix(self):
        """Find the prefix for one of the stdlib modules loaded from the zip files

        Examples
        --------
        >>> db = RuntimeResults(

        """
        return self["init_sys_modules"]["pathlib"].replace("/pathlib.py", "")

    def get_imported_paths(self, strip_prefix: str | None = None):
        """Get the paths of all imported modules.

        Optionally by stripping a prefix from the paths.
        """
        imported_paths = (
            list(self["init_sys_modules"].values()) + self["opened_file_names"]
        )
        if strip_prefix is not None:
            imported_paths = [
                path.replace(strip_prefix + "/", "")
                for path in imported_paths
                if path.startswith(strip_prefix)
            ]
        return imported_paths

    @classmethod
    def from_json(cls, path) -> RuntimeResults:
        """Load the results.json with runtime execution information."""
        with open(path) as fh:
            db = cls(json.load(fh))

        db["opened_file_names"] = list(
            {path for path in db["opened_file_names"] if "__pycache__" not in path}
        )
        db["dynamic_libs_map"] = {
            path: DynamicLib(path, load_order=idx)
            for idx, path in enumerate(db["find_object_calls"])
            if path.endswith(".so")
        }
        return db
