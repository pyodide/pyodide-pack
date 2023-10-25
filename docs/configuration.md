(config)=
# Configuration

`pyodide pack` can be configured via a `pyproject.toml` file in the root of your project, or in a any of the parent directories.

Below is an example of configuration with default values. In most cases, the defaults should be fine, and you can only include fields you want to change.


```toml
[tool.pyodide_pack]
requires = []
include_paths =  []

[tool.pyodide_pack.py]
strip_module_docstrings = false
strip_docstrings = false
py_compile = false

[tool.pyodide_pack.so]
drop_unused_so = true
```


## Configuration options

### `requires`

List of dependencies to load. This list is passed to micropip, so it can be any valid micropip specifier.

### `include_paths`

List of paths to include in the bundle. This is useful for including files that were otherwise excluded by `pyodide pack`

### `py.strip_module_docstrings`

Whether to strip module docstrings. Default: `false`

### `py.strip_docstrings`

Whether to strip docstrings. Default: `false`

### `py.py_compile`

Whether to compile python files. Default: `false`

### `so.drop_unused_so`

Whether to drop unused `.so` files. Default: `true`
