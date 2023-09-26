import json

from pyodide_pack.dynamic_lib import DynamicLib
from pyodide_pack.runtime_detection import RuntimeResults


def test_runtime_results(tmp_path):
    input_data = {
        "opened_file_names": ["a.py", "b.py", "__pycache__/a.cpython-38.pyc"],
        "find_object_calls": ["c.so"],
    }

    with open(tmp_path / "results.json", "w") as fh:
        json.dump(input_data, fh)

    res = RuntimeResults.from_json(tmp_path / "results.json")
    assert list(res.keys()) == [
        "opened_file_names",
        "find_object_calls",
        "dynamic_libs_map",
    ]

    assert res["opened_file_names"] == ["a.py", "b.py"]
    assert res["dynamic_libs_map"] == {
        "c.so": DynamicLib(path="c.so", load_order=0, shared=False)
    }
