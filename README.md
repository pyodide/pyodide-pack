# pyodide-pack

[![PyPi version](https://img.shields.io/pypi/v/pyodide-pack.svg)](https://pypi.org/project/pyodide-pack)
[![GHA CI](https://github.com/rth/pyodide-pack/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rth/pyodide-pack/actions/workflows/main.yml)

Python package bundler for the web

THIS IS STILL WIP AND NOT READY FOR USE

Pyodide-pack detects used modules in a Python application running in the web with Pyodide, and creates a minimal bundle with them. This allows to significantly reduce the download size of Python applications, provided that the code to execute is known in advance.

## Install

Pyodide-pack requires Python 3.9+ as well as NodeJS,

```bash
pip install pyodide-pack
npm install pyodide@0.20.1-alpha.2
# A hack due to the npm package having issues
wget https://cdn.jsdelivr.net/pyodide/v0.20.0/full/packages.json -O node_modules/pyodide/packages.json
```

## Quickstart

1. Create file with the code of your Python application running in the web. As example we will take,
   `examples/pandas-ex/app.py`

   **app.py**

   ```py
   import pandas as pd

   pd.DataFrame([10])
   ```

   This application can run with Pyodide, and will need to download around X MB of packages, including numpy, pandas in addition to ~7.5MB for CPython with stdlib.

2. Start an HTTP server in the current folder;
   ```
   python -m http.server
   ```
   (TODO: this should be automated)

3. Create the package bundle,

   ```bash
   python pyodide_pack/cli.py examples/pandas-ex/app.py
   ```

   which would produce the following output

   ```
   Running pyodide-pack on examples/pandas-ex/app.py

   Note: unless otherwise specified all sizes are given for gzip compressed files to take into account CDN compression.

   Running the input code in Node.js to detect used modules..

   ...

   Done input code execution in 11.2 s

   Detected 8 dependencies with a total size of 10.54 MB  (uncompressed: 40.99 MB)
   In total 425 files and 54 shared libraries were accessed.

   Packing:
    - [1/8] distutils.tar: 101 → 0 files, 0.26 → 0.00 MB (100.0 % reduction)
    - [2/8] python_dateutil-2.8.2-py2.py3-none-any.whl: 25 → 15 files, 0.24 → 0.22 MB (9.4 % reduction)
    - [3/8] six-1.16.0-py2.py3-none-any.whl: 6 → 1 files, 0.01 → 0.01 MB (18.5 % reduction)
    - [4/8] pyparsing-3.0.7-py3-none-any.whl: 17 → 0 files, 0.10 → 0.00 MB (100.0 % reduction)
    - [5/8] pytz-2022.1-py2.py3-none-any.whl: 612 → 5 files, 0.43 → 0.02 MB (96.1 % reduction)
    - [6/8] setuptools-62.0.0-py3-none-any.whl: 213 → 0 files, 0.76 → 0.00 MB (100.0 % reduction)
    - [7/8] numpy-1.22.3-cp310-cp310-emscripten_wasm32.whl: 418 → 94 files, 3.63 → 2.49 MB (31.4 % reduction)
    - [8/8] pandas-1.4.2-cp310-cp310-emscripten_wasm32.whl: 469 → 283 files, 5.11 → 4.50 MB (12.0 % reduction)
   Wrote pyodide-package-bundle.zip with 7.35 MB (30.2% compression)

   Running the input code in Node.js to validate bundle..
   Done input code execution in ?? s
   ```
4. Load your Python web application with,
   ```
   let pyodide = await loadPyodide({fullStdLib: false});

   await pyodide.runPythonAsync(`
     from pyodide.http import pyfetch
     import os
     response = await pyfetch("<your-server>/pyodide-package-bundle.zip")
     await response.unpack_archive(extract_dir='/')
   `)

   for (const path of {{ so_files }}) {
     pyodide._module.API.tests.loadDynlib(path, true);
   }
   ```
   (TODO: ship the list of .so files to pre-load in the zip and add a Pyodide utils
    function to make this easier)

## Implementation

This bundler runs your applications in a Node.js and intercepts,
 - `FS.open` calls in read mode, which includes accessed files in the Emscripten's MEMFS file system opened from Python, C or Javascript.
 - calls to load a dynamic library

Package wheels are then repacked into a single bundle with the accessed files and dynamic libraries.

## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
