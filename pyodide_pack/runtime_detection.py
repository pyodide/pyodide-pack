from __future__ import annotations

import fnmatch
import gzip
import json
import os
from pathlib import Path

from pyodide_pack._utils import (
    match_suffix,
)
from pyodide_pack.archive import ArchiveFile
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


class PackageBundler:
    """Only include necessary files for a given package."""

    def __init__(self, db: RuntimeResults, include_paths: str | None = None):
        self.db = db
        self.stats = {
            "py_in": 0,
            "so_in": 0,
            "py_out": 0,
            "so_out": 0,
            "fh_out": 0,
            "size_out": 0,
            "size_gzip_out": 0,
        }
        self.dynamic_libs: list[DynamicLib] = []
        self.include_paths = include_paths

    def process_path(self, in_file_name: str) -> str | None:
        """Process a path, returning the output path if it should be included."""
        db = self.db
        stats = self.stats
        match Path(in_file_name).suffix:
            case ".py":
                stats["py_in"] += 1
            case ".so":
                stats["so_in"] += 1

        out_file_name = None
        if out_file_name := match_suffix(
            list(db["dl_accessed_symbols"].keys()), in_file_name
        ):
            stats["so_out"] += 1
            # Get the dynamic library path while preserving order
            dll = db["dynamic_libs_map"][out_file_name]
            self.dynamic_libs.append(dll)
        elif out_file_name := match_suffix(db["opened_file_names"], in_file_name):
            stats["py_out"] += 1

        elif self.include_paths is not None and any(
            fnmatch.fnmatch(in_file_name, pattern)
            for pattern in self.include_paths.split(",")
        ):
            # TODO: this is hack and should be done better
            out_file_name = os.path.join("/lib/python3.11/site-utils", in_file_name)
            match Path(in_file_name).suffix:
                case ".py":
                    stats["py_out"] += 1
                case ".so":
                    stats["so_out"] += 1
                    # Manually included dynamic libraries are going to be loaded first
                    dll = DynamicLib(out_file_name, load_order=-1000)
                    self.dynamic_libs.append(dll)
        return out_file_name

    def copy_between_zip_files(
        self,
        in_file_name: str,
        out_file_name: str,
        archive: ArchiveFile,
        fh_out,
    ) -> None:
        """Copy a file between two archives."""
        stats = self.stats
        stats["fh_out"] += 1
        stream = archive.read(in_file_name)
        if stream is not None:
            stats["size_out"] += len(stream)
            stats["size_gzip_out"] += len(gzip.compress(stream))
            # File paths starting with / fails to get correctly extracted
            # in extract_archive in Pyodide
            with fh_out.open(out_file_name.lstrip("/"), "w") as fh:
                fh.write(stream)
