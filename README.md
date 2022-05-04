# pyodide-pack

[![PyPi version](https://img.shields.io/pypi/v/pyodide-pack.svg)](https://pypi.org/project/pyodide-pack)
[![GHA CI](https://github.com/rth/pyodide-pack/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rth/pyodide-pack/actions/workflows/main.yml)

Python package bundler for the web

Pyodide-pack detects used modules in a Python application running in the web with Pyodide, and creates a minimal bundle with them.This allows to significantly reduce the download size of Python applications, provided that the code to execute is known in advance.

## Install

Pyodide-pack requires Python 3.9+ as well as NodeJS,
```
pip install pyodide-pack
npm install pyodide
```

## Quickstart

1. Create file with the code of your Python application running in the web. As example we will take,
   
   **app.py**
   ```py
   from sklearn.linear_model import Ridge
   from sklearn.datasets import load_iris

   def main():
       X, y = load_iris(return_X_y=True)
       estimator = Ridge()
       estimator.fit(X, y)
       return estimator
   ```
   This application can run with Pyodide, and will need to download around 21MB of packages, including numpy, scipy, scikit-learn and joblib, in addition to ~7.5MB for CPython with stdlib. 

2. Create the package bundle,
   ```bash
   pyodide-pack app.py
   ```   
   which would produce the following output
   ```
   Running pyodide-bundle on app.py
   Detected 4 Python dependencies, 
     - 3 Pyodide built wheels
     - 0 universal wheels from PyPi
   with a total of 29MB.

   Running application with Node.js..
   Detected 120 opened files while loading application.

   Repacking wheels:
     - numpy.whl
     - scipy.wl 
   Output written to pyodide-bundle-8ac519.zip (3MB).
   ```
   

## Implementation

This bundler relies on intercepting `FS.open` calls in read mode, which includes files in the Emscripten's MEMFS opened both from Python and Javascript. Package wheels are then repacked into a single bundle with the accessed files.


## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).
