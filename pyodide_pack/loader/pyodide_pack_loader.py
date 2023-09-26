from pathlib import Path


async def setup():
    """Load dynamic libraries in the pyodide-pack bundle"""
    from pyodide_js import _module

    for paths in Path("/bundle-so-list.txt").read_text().splitlines():
        path, is_shared = paths.split(",")
        await _module._api.loadDynlib(path, bool(is_shared))
