from pyodide_pack.testing import _get_stdlib_module_paths


def test_get_stdlib_module_paths():
    paths = _get_stdlib_module_paths()
    assert len(paths) > 2500
    assert all(p.suffix == ".py" for p in paths)
