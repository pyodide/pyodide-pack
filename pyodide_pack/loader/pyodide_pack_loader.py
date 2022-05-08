from pathlib import Path


async def load_dynamic_libs():
    """Load dynamic libraries in the pyodide-pack bundle"""
    from pyodide_js import _module

    for paths in Path("/bundle-so-list.txt").read_text().splitlines():
        path, is_shared = paths.split(",")
        await _module.API.tests.loadDynlib(path, bool(is_shared))
