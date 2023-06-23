# pyodide-pack

[![PyPI Latest Release](https://img.shields.io/pypi/v/pyodide-pack.svg)](https://pypi.org/project/pyodide-pack/)
[![GHA CI](https://github.com/rth/pyodide-pack/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rth/pyodide-pack/actions/workflows/main.yml)
[![codecov](https://codecov.io/github/pyodide/pyodide-pack/branch/main/graph/badge.svg?token=2BBYXLX6AE)](https://codecov.io/github/pyodide/pyodide-pack)

Python package bundler and minifier for the web

Pyodide-pack aims to reduce the size and load time of Python applications running in the browser using different strategies:
 - Minification of the source code via AST rewrite
 - Transformation of the source code into a different format such as Python bytecode (.pyc files)
 - Dead code elimination, by removing unused Python modules (detected at runtime)

Each of these approaches have different tradeoffs, and can be used separately or in combination.

## Install

Pyodide-pack requires Python 3.10+ and can be installed via pip:

```
pip install pyodide-pack
```

(optionally) For elimation of unused modules via runtime detection, run NodeJS  needs to be installed,
as well,

```bash
npm install pyodide@0.20.1-alpha.2
# A hack due to the npm package having issues
wget https://cdn.jsdelivr.net/pyodide/v0.20.0/full/packages.json -O node_modules/pyodide/packages.json
```

## Usage

For Python wheel minification via AST rewrites, run,
```
pyodide minify <path_to_wheel>.whl
```


See the documentation at [pyodide-pack.pyodide.org](https://pyodide-pack.pyodide.org).


## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
