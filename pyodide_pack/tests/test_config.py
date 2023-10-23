from pyodide_pack.config import _find_pyproject_toml, _get_config_section

def test_find_pyproject_toml(tmp_path):
    """Test that we can find the pyproject.toml in any of the parent dirs"""
    assert _find_pyproject_toml(tmp_path) is None
    assert _find_pyproject_toml(tmp_path / "non_existing_path.txt") is None
    assert _find_pyproject_toml(tmp_path / "pyproject.toml") is None
    input_path = tmp_path / "pyproject.toml"
    input_path.write_text('')
    assert _find_pyproject_toml(input_path) == input_path
    assert _find_pyproject_toml(tmp_path) == input_path
    (nested_dir := tmp_path / "a" / "b" / "c").mkdir(parents=True)
    assert _find_pyproject_toml(nested_dir) == input_path
    (input_path2 := nested_dir / 'pyproject.toml').write_text('')
    assert _find_pyproject_toml(nested_dir) == input_path2
    

def test_get_config_section(tmp_path):
    import tomli_w

    config_path = tmp_path / 'pyproject.toml'
    config_path.write_text("")
    assert _get_config_section(config_path) is None
    config_path.write_text(tomli_w.dumps({"tools": {}})) is None
    config_path.write_text(tomli_w.dumps({"tools": {"pyodide_pack": ""}})) is None
    config_path.write_text(tomli_w.dumps({"tools": {"pyodide_pack": {}}})) == {}
    config_path.write_text(tomli_w.dumps({"tools": {"pyodide_pack": {"a": 1}}})) == {"a": 1}

    
