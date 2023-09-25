# Module removal by runtime detection

1. Create file with the code of your Python application running in the web. As example we will take,
   `examples/pandas/app.py`

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
   pyodide pack examples/pandas/app.py
   ```
   which would produce the following output

   ```
   Running pyodide-pack on examples/pandas/app.py

   Note: unless otherwise specified all sizes are given for gzip compressed files to
   be representative of CDN compression.

   Loaded requirements from: examples/pandas/requirements.txt
   Running the input code in Node.js to detect used modules..

   [...]
   Done input code execution in 3.8 s

   Using stdlib (547 files) with a total size of 2.25 MB.
   Detected 5 dependencies with a total size of 8.92 MB  (uncompressed: 35.46 MB)
   In total 487 files and 0 dynamic libraries were accessed.
   Total initial size (stdlib + dependencies): 11.17 MB


                                          Packing..
   ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
   ┃ No ┃ Package                        ┃ All files ┃ .so libs ┃   Size (MB) ┃ Reduction ┃
   ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
   │  0 │ stdlib                         │ 547 → 151 │          │ 2.25 → 0.75 │    66.7 % │
   │  1 │ numpy-1.25.2-cp311-cp311-emsc… │ 430 → 111 │   19 → 0 │ 3.06 → 2.36 │    23.0 % │
   │  2 │ pandas-1.5.3-cp311-cp311-emsc… │ 462 → 292 │   42 → 0 │ 5.17 → 4.64 │    10.3 % │
   │  3 │ python_dateutil-2.8.2-py2.py3… │   25 → 15 │    0 → 0 │ 0.24 → 0.22 │     9.4 % │
   │  4 │ pytz-2023.3-py2.py3-none-any.… │   614 → 5 │    0 → 0 │ 0.43 → 0.02 │    96.1 % │
   │  5 │ six-1.16.0-py2.py3-none-any.w… │     6 → 1 │    0 → 0 │ 0.01 → 0.01 │    18.5 % │
   └────┴────────────────────────────────┴───────────┴──────────┴─────────────┴───────────┘
   Wrote pyodide-package-bundle.zip with 7.37 MB (17.4% reduction)

   Spawning webserver at http://127.0.0.1:52009 (see logs in /tmp/tmpx0ktv9fw/http-server.log)
   Running the input code in Node.js to validate bundle..

           Validating and benchmarking the output bundle..
   ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
   ┃ Step                 ┃ Load time (s) ┃ Fraction of load time ┃
   ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
   │ loadPyodide          │          1.34 │                36.1 % │
   │ fetch_unpack_archive │          0.27 │                 7.4 % │
   │ load_dynamic_libs    │          0.00 │                 0.1 % │
   │ import_run_app       │          2.10 │                56.5 % │
   │ TOTAL                │          3.72 │                 100 % │
   └──────────────────────┴───────────────┴───────────────────────┘

   Total output size (stdlib + packages): 8.12 MB (27.3% reduction)

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
