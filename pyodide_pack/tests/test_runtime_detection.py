import json

from pyodide_pack.config import PackConfig
from pyodide_pack.dynamic_lib import DynamicLib
from pyodide_pack.runtime_detection import PackageBundler, RuntimeResults


def test_runtime_results(tmp_path):
    input_data = {
        "opened_file_names": ["a.py", "b.py", "__pycache__/a.cpython-38.pyc"],
        "load_dyn_lib_calls": [
            {"path": "c.so", "global": False},
            {"path": "d.so", "global": False},
            {"path": "g.so", "global": True},
        ],
        "dl_accessed_symbols": {"c.so": None},
    }

    with open(tmp_path / "results.json", "w") as fh:
        json.dump(input_data, fh)

    res = RuntimeResults.from_json(tmp_path / "results.json")
    assert list(res.keys()) == [
        "opened_file_names",
        "load_dyn_lib_calls",
        "dl_accessed_symbols",
        "dynamic_libs_map",
    ]

    assert res["opened_file_names"] == ["a.py", "b.py"]
    # d.so not included as it's not in accessed LDSO symbols
    # g.so is include as it's globally loaded
    assert res["dynamic_libs_map"] == {
        "c.so": DynamicLib(path="c.so", load_order=0, shared=False),
        "g.so": DynamicLib(path="g.so", load_order=2, shared=True),
    }


def test_bundler_process_path(tmp_path):
    db = RuntimeResults(
        opened_file_names=["a.py", "d/b.py", "d/f.so", "c.so"],
        dynamic_libs_map={
            "d/f.so": DynamicLib(path="d/f.so", load_order=0, shared=False)
        },
    )
    bundler = PackageBundler(db, config=PackConfig())

    assert bundler.process_path("k.py") is None
    assert bundler.process_path("a.py") == "a.py"
    assert bundler.process_path("b.py") == "d/b.py"
    assert bundler.process_path("f.so") == "d/f.so"
