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
   `examples/scikit-learn/app.py`

   **app.py**

   ```py
   from sklearn.linear_model import Ridge

   est = Ridge()
   ```

   This application can run with Pyodide, and will need to download around 27
   MB of packages, including numpy, scipy and scikit-learn in addition to
   ~7.5MB for CPython with stdlib.

2. Start an HTTP server in the current folder;
   ```
   python -m http.server
   ```
   (TODO: *this should be automated*)

3. Create the package bundle,

   ```bash
   python pyodide_pack/cli.py examples/scikit-learn/app.py  --include-paths='*lapack*so' -v
   ```
   (*For now CLAPACK needs to be manually included*)

   which would produce the following output

   ```
   Running pyodide-pack on examples/scikit-learn/app.py

   Note: unless otherwise specified all sizes are given for gzip compressed files to take into account CDN compression.

   Loaded requirements from: examples/scikit-learn/requirements.txt
   Running the input code in Node.js to detect used modules..

   [...]

   Done input code execution in 19.6 s

   Detected 7 dependencies with a total size of 20.94 MB  (uncompressed: 73.86 MB)
   In total 628 files and 113 shared libraries were accessed.

                                                 Packing..
   ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ No ┃ Package                        ┃ All files ┃       .py ┃      .so ┃    Size (MB) ┃ Reduction ┃
   ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
   │  1 │ CLAPACK-3.2.1.zip              │     2 → 1 │     0 → 0 │    1 → 1 │  1.27 → 1.27 │     0.0 % │
   │  2 │ distutils.tar                  │   101 → 3 │    93 → 3 │    0 → 0 │  0.26 → 0.00 │    98.2 % │
   │  3 │ joblib-1.1.0-py2.py3-none-any… │   62 → 23 │   57 → 23 │    0 → 0 │  0.18 → 0.09 │    50.3 % │
   │  4 │ numpy-1.22.3-cp310-cp310-emsc… │ 418 → 101 │  233 → 87 │  19 → 14 │  3.63 → 2.92 │    19.6 % │
   │  5 │ scikit_learn-1.0.2-cp310-cp31… │ 357 → 103 │  253 → 81 │  55 → 22 │  4.12 → 1.34 │    67.4 % │
   │  6 │ scipy-1.8.0-cp310-cp310-emscr… │ 669 → 396 │ 503 → 319 │ 107 → 77 │ 11.47 → 7.45 │    35.0 % │
   │  7 │ threadpoolctl-3.1.0-py3-none-… │     5 → 1 │     1 → 1 │    0 → 0 │  0.01 → 0.01 │    30.7 % │
   └────┴────────────────────────────────┴───────────┴───────────┴──────────┴──────────────┴───────────┘
   Wrote pyodide-package-bundle.zip with 13.28 MB (36.6% reduction)

   Running the input code in Node.js to validate bundle..

   warning: no blob constructor, cannot create blobs with mimetypes
   warning: no BlobBuilder
   Python initialization complete
           Validating and benchmarking the output bundle..
   ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃ Step                 ┃ Load time (s) ┃ Fraction of load time ┃
   ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
   │ loadPyodide          │          3.54 │                16.1 % │
   │ fetch_unpack_archive │          0.55 │                 2.5 % │
   │ load_dynamic_libs    │         15.04 │                68.4 % │
   │ import_run_app       │          2.87 │                13.0 % │
   │ TOTAL                │         22.00 │                 100 % │
   └──────────────────────┴───────────────┴───────────────────────┘

   Bundle validation successful.
   ```
4. Load your Python web application with,
   ```js
   let pyodide = await loadPyodide({fullStdLib: false});

   await pyodide.runPythonAsync(`
     from pathlib import Path
     from pyodide.http import pyfetch
     from pyodide_js import _module

     response = await pyfetch("<your-server>/pyodide-package-bundle.zip")
     await response.unpack_archive(extract_dir='/')

     for paths in Path('/bundle-so-list.txt').read_text().splitlines():
        path, is_shared = paths.split(',')
        await _module.API.tests.loadDynlib(path, bool(is_shared))
   `)
   ```

## Implementation

This bundler runs your applications in a Node.js and intercepts,
 - `FS.open` calls in read mode, which includes accessed files in the Emscripten's MEMFS file system opened from Python, C or Javascript.
 - calls to load a dynamic library

Package wheels are then repacked into a single bundle with the accessed files and dynamic libraries.

## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
