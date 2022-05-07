# pyodide-pack

[![GHA CI](https://github.com/rth/pyodide-pack/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rth/pyodide-pack/actions/workflows/main.yml)

Python package bundler for the web

THIS IS STILL WIP AND NOT READY FOR USE

Pyodide-pack detects used modules in a Python application running in the web with Pyodide, and creates a minimal bundle with them. This allows to significantly reduce the download size of Python applications, provided that the code to execute is known in advance.

## Install

Pyodide-pack requires Python 3.10+ as well as NodeJS,

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
   (TODO: *this should be automated*)

3. Create the package bundle,

   ```bash
   python pyodide_pack/cli.py examples/scikit-learn/app.py  --include-paths='*lapack*so'
   ```

   which would produce the following output

   ```
   Running pyodide-pack on examples/scikit-learn/app.py

   Note: unless otherwise specified all sizes are given for gzip compressed files to take into account CDN compression.

   Loaded requirements from: examples/scikit-learn/requirements.txt
   Running the input code in Node.js to detect used modules..

   [...]

   Done input code execution in 26.3 s

   Detected 13 dependencies with a total size of 27.59 MB  (uncompressed: 99.53 MB)

   In total 634 files and 113 shared libraries were accessed.
                                     Packing..
   ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ No ┃ Package                        ┃ All files ┃    Size (MB) ┃ Reduction ┃
   ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
   │  1 │ distutils.tar                  │   101 → 3 │  0.26 → 0.00 │    98.2 % │
   │  2 │ CLAPACK-3.2.1.zip              │     2 → 1 │  1.27 → 1.27 │     0.0 % │
   │  3 │ python_dateutil-2.8.2-py2.py3… │    25 → 0 │  0.24 → 0.00 │   100.0 % │
   │  4 │ six-1.16.0-py2.py3-none-any.w… │     6 → 0 │  0.01 → 0.00 │   100.0 % │
   │  5 │ pytz-2022.1-py2.py3-none-any.… │   612 → 0 │  0.43 → 0.00 │   100.0 % │
   │  6 │ setuptools-62.0.0-py3-none-an… │   213 → 0 │  0.76 → 0.00 │   100.0 % │
   │  7 │ pyparsing-3.0.7-py3-none-any.… │    17 → 0 │  0.10 → 0.00 │   100.0 % │
   │  8 │ joblib-1.1.0-py2.py3-none-any… │   62 → 23 │  0.18 → 0.09 │    50.3 % │
   │  9 │ threadpoolctl-3.1.0-py3-none-… │     5 → 1 │  0.01 → 0.01 │    30.7 % │
   │ 10 │ numpy-1.22.3-cp310-cp310-emsc… │ 418 → 101 │  3.63 → 2.92 │    19.6 % │
   │ 11 │ pandas-1.4.2-cp310-cp310-emsc… │   469 → 0 │  5.11 → 0.00 │   100.0 % │
   │ 12 │ scikit_learn-1.0.2-cp310-cp31… │ 357 → 103 │  4.12 → 1.34 │    67.4 % │
   │ 13 │ scipy-1.8.0-cp310-cp310-emscr… │ 669 → 396 │ 11.47 → 7.45 │    35.0 % │
   └────┴────────────────────────────────┴───────────┴──────────────┴───────────┘
   Wrote pyodide-package-bundle.zip with 13.28 MB (51.9% reduction)

   Running the input code in Node.js to validate bundle..

   warning: no blob constructor, cannot create blobs with mimetypes
   warning: no BlobBuilder
   Python initialization complete

   Done input code execution in 21.8 s

   Bundle generation successful.
   ```
4. Load your Python web application with,
   ```js
   let pyodide = await loadPyodide({fullStdLib: false});

   await pyodide.runPythonAsync(`
     from pathlib import Path
     from pyodide.http import pyfetch
     import os
     response = await pyfetch("<your-server>/pyodide-package-bundle.zip")
     await response.unpack_archive(extract_dir='/')
     so_paths = Path('/bundle-so-list.txt').read_text().splitlines()
   `)

   for (const path of pyodide.globals.get('so_paths')) {
     await pyodide._module.API.tests.loadDynlib(path, true);
   }
   ```
   (TODO: *ship the list of .so files to pre-load in the zip and add a Pyodide utils
    function to make this easier*)

## Implementation

This bundler runs your applications in a Node.js and intercepts,
 - `FS.open` calls in read mode, which includes accessed files in the Emscripten's MEMFS file system opened from Python, C or Javascript.
 - calls to load a dynamic library

Package wheels are then repacked into a single bundle with the accessed files and dynamic libraries.

## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
