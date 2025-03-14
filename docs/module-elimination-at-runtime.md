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

    which would produce the following output:

    ```
    Running pyodide-pack on examples/pandas/app.py

    Note: unless otherwise specified all sizes are given for gzip compressed files to be representative of CDN compression.

    Loaded requirements from: examples/pandas/requirements.txt
    Running the input code in Node.js to detect used modules..

    [...]

    Done input code execution in 6.2 s

    Using stdlib (554 files) with a total size of 2.29 MB.
    Detected 5 dependencies with a total size of 9.34 MB  (uncompressed: 37.62 MB)
    In total 487 files and 0 dynamic libraries were accessed.
    Total initial size (stdlib + dependencies): 11.63 MB


                                            Packing..
    ┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━━━┓
    ┃ No ┃ Package                        ┃ All files ┃ .so libs ┃   Size (MB) ┃ Reduction ┃
    ┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━━━┩
    │  0 │ stdlib                         │ 554 → 168 │          │ 2.29 → 0.46 │    79.8 % │
    │  1 │ numpy-2.0.2-cp312-cp312-pyodi… │  338 → 96 │  19 → 12 │ 3.05 → 2.16 │    29.3 % │
    │  2 │ pandas-2.2.3-cp312-cp312-pyod… │ 396 → 295 │  44 → 42 │ 5.61 → 4.52 │    19.5 % │
    │  3 │ python_dateutil-2.9.0.post0-p… │   25 → 14 │    0 → 0 │ 0.23 → 0.18 │    21.6 % │
    │  4 │ pytz-2024.1-py2.py3-none-any.… │   615 → 5 │    0 → 0 │ 0.43 → 0.01 │    97.8 % │
    │  5 │ six-1.16.0-py2.py3-none-any.w… │     6 → 1 │    0 → 0 │ 0.01 → 0.01 │    41.8 % │
    └────┴────────────────────────────────┴───────────┴──────────┴─────────────┴───────────┘
    Wrote pyodide-package-bundle.zip with 6.99 MB (25.2% reduction)

    Spawning webserver at http://127.0.0.1:52009 (see logs in /tmp/tmpx0ktv9fw/http-server.log)
    Running the input code in Node.js to validate bundle..

            Validating and benchmarking the output bundle..
    ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Step                 ┃ Load time (s) ┃ Fraction of load time ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
    │ loadPyodide          │          0.82 │                34.6 % │
    │ fetch_unpack_archive │          0.14 │                 5.9 % │
    │ load_dynamic_libs    │          0.11 │                 4.6 % │
    │ import_run_app       │          1.30 │                54.9 % │
    │ TOTAL                │          2.36 │                 100 % │
    └──────────────────────┴───────────────┴───────────────────────┘

    Total output size (stdlib + packages): 7.45 MB (35.9% reduction)

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
