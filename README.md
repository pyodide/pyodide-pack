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
   `examples/example1/app.py`
   
   **app.py**
   ```py
   import pandas as pd

   pd.DataFrame([10])
   ```
   This application can run with Pyodide, and will need to download around 21MB of packages, including numpy, scipy, scikit-learn and joblib, in addition to ~7.5MB for CPython with stdlib. 

2. Create the package bundle,
   ```bash
   python pyodide_pack/cli.py examples/example1/app.py  -r examples/example1/requirements.txt
   ```   
   which would produce the following output
   ```
   Running pyodide-pack on examples/example1/app.py
   Running the input code in Node.js to detect used modules..
   
   warning: no blob constructor, cannot create blobs with mimetypes
   warning: no BlobBuilder
   Loading distutils
   Loaded distutils
   Python initialization complete
   distutils already loaded from default channel
   Loading pandas, numpy, python-dateutil, six, pytz, setuptools, pyparsing
   Loaded six, python-dateutil, pyparsing, pytz, setuptools, numpy, pandas
   
   Done input code execution in 18.3 s
   
   In total 425 file paths were opened.
   Detected 7 dependencies with a total size of 10.56 MB
   
   Packing:
    - [1/7] six-1.16.0-py2.py3-none-any.whl (0.01 MB):  6 → 1 (83.3 % compression)
    - [2/7] pyparsing-3.0.7-py3-none-any.whl (0.10 MB):  17 → 0 (100.0 % compression)
    - [3/7] python_dateutil-2.8.2-py2.py3-none-any.whl (0.25 MB):  25 → 15 (40.0 % compression)
    - [4/7] setuptools-62.0.0-py3-none-any.whl (0.79 MB):  213 → 0 (100.0 % compression)
    - [5/7] pytz-2022.1-py2.py3-none-any.whl (0.50 MB):  612 → 5 (99.2 % compression)
    - [6/7] pandas-1.4.2-cp310-cp310-emscripten_wasm32.whl (5.21 MB):  469 → 284 (39.4 % compression)
    - [7/7] numpy-1.22.3-cp310-cp310-emscripten_wasm32.whl (3.70 MB):  418 → 100 (76.1 % compression)
   Wrote pyodide-package-bundle.zip with 7.82 MB (25.9% compression) 
   
   Running the input code in Node.js to validate bundle..
   Done input code execution in 15.4 s
   ```
   

## Implementation

This bundler relies on intercepting `FS.open` calls in read mode, which includes files in the Emscripten's MEMFS opened both from Python and Javascript. Package wheels are then repacked into a single bundle with the accessed files.


## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
