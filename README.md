# pyodide-pack

[![GHA CI](https://github.com/rth/pyodide-pack/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rth/pyodide-pack/actions/workflows/main.yml)

Python package bundler for the web

THIS PACKAGE IS STILL VERY EXPERIMENTAL

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
   `examples/scikit-learn/app.py`

   **app.py**

   ```py
   import pandas as pd  # noqa

   pd.DataFrame(range(10))
   ```

   This application can run with Pyodide, and will need to download around 10.5
   MB of packages, including numpy and pandas in addition to
   ~7MB for CPython with stdlib.

2. Create the package bundle,

   ```bash
   python pyodide_pack/cli.py examples/pandas/app.py
   ```
   which would produce the following output

   ```
   Running pyodide-pack on examples/pandas/app.py

   Note: unless otherwise specified all sizes are given for gzip compressed files to take into account CDN compression.

   Loaded requirements from: examples/pandas/requirements.txt
   Running the input code in Node.js to detect used modules..

   [..]

   Done input code execution in 11.1 s

   Detected 8 dependencies with a total size of 10.54 MB  (uncompressed: 40.99 MB)
   In total 425 files and 54 dynamic libraries were accessed.

                                          Packing..
   ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ No ┃ Package                        ┃ All files ┃ .so libs ┃   Size (MB) ┃ Reduction ┃
   ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
   │  1 │ distutils.tar                  │   101 → 0 │    0 → 0 │ 0.26 → 0.00 │   100.0 % │
   │  2 │ numpy-1.22.3-cp310-cp310-emsc… │  418 → 94 │  19 → 13 │ 3.63 → 2.49 │    31.4 % │
   │  3 │ pandas-1.4.2-cp310-cp310-emsc… │ 469 → 283 │  42 → 41 │ 5.11 → 4.50 │    12.0 % │
   │  4 │ pyparsing-3.0.7-py3-none-any.… │    17 → 0 │    0 → 0 │ 0.10 → 0.00 │   100.0 % │
   │  5 │ python_dateutil-2.8.2-py2.py3… │   25 → 15 │    0 → 0 │ 0.24 → 0.22 │     9.4 % │
   │  6 │ pytz-2022.1-py2.py3-none-any.… │   612 → 5 │    0 → 0 │ 0.43 → 0.02 │    96.1 % │
   │  7 │ setuptools-62.0.0-py3-none-an… │   213 → 0 │    0 → 0 │ 0.76 → 0.00 │   100.0 % │
   │  8 │ six-1.16.0-py2.py3-none-any.w… │     6 → 1 │    0 → 0 │ 0.01 → 0.01 │    18.5 % │
   └────┴────────────────────────────────┴───────────┴──────────┴─────────────┴───────────┘
   Wrote pyodide-package-bundle.zip with 7.36 MB (30.2% reduction)

   Running the input code in Node.js to validate bundle..

           Validating and benchmarking the output bundle..
   ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃ Step                 ┃ Load time (s) ┃ Fraction of load time ┃
   ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
   │ loadPyodide          │          2.59 │                24.4 % │
   │ fetch_unpack_archive │          0.27 │                 2.5 % │
   │ load_dynamic_libs    │          6.21 │                58.5 % │
   │ import_run_app       │          1.56 │                14.7 % │
   │ TOTAL                │         10.63 │                 100 % │
   └──────────────────────┴───────────────┴───────────────────────┘

   Bundle validation successful.
   ```
3. Load your Python web application with,
   ```js
   let pyodide = await loadPyodide({fullStdLib: false});

   await pyodide.runPythonAsync(`
     from pyodide.http import pyfetch

     response = await pyfetch("<your-server>/pyodide-package-bundle.zip")
     await response.unpack_archive(extract_dir='/')
   `)

   await pyodide.pyimport('pyodide_pack_loader').setup();
   ```

## Implementation

This bundler runs your applications in a Node.js and intercepts,
 - `FS.open` calls in read mode, which includes accessed files in the Emscripten's MEMFS file system opened from Python, C or Javascript.
 - calls to load a dynamic library

Package wheels are then repacked into a single bundle with the accessed files and dynamic libraries.

## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
