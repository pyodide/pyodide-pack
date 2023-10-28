from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Extra

try:
    import tomllib
except ImportError:
    # Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]


def _find_pyproject_toml(input_path: Path) -> Path | None:
    """Find a `pyproject.toml` in any of the parent dirs"""
    if not input_path.is_dir():
        input_path = input_path.parent

    if (pyproject_path := input_path / "pyproject.toml").exists():
        return pyproject_path

    if input_path == input_path.parent:
        # Reached root dir
        return None

    return _find_pyproject_toml(input_path.parent)


def _get_config_section(path: Path) -> dict[str, Any] | None:
    """Get the pyodide pack config section from a pyproject.toml"""
    config = tomllib.loads(path.read_text())
    tools_config = config.get("tool")
    if not isinstance(tools_config, dict):
        return None
    output = tools_config.get("pyodide_pack")
    if output and isinstance(output, dict):
        return output
    return None


class PyPackConfig(BaseModel, extra=Extra.forbid):  # type: ignore[call-arg]
    """Configuration for handling Python files"""

    strip_module_docstrings: bool = True
    strip_docstrings: bool = True
    py_compile: bool = False


class SoPackConfig(BaseModel, extra=Extra.forbid):  # type: ignore[call-arg]
    """Configuration for handling shared libraries"""

    drop_unused_so: bool = True


class PackConfig(BaseModel, extra=Extra.forbid):  # type: ignore[call-arg]
    """pyodide-pack configuration"""

    requires: list[str] = []
    include_paths: list[str] = []
    py: PyPackConfig = PyPackConfig()
    so: SoPackConfig = SoPackConfig()
