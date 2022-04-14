# pyodide-pack

[![PyPi version](https://img.shields.io/pypi/v/pyodide-pack.svg)](https://pypi.org/project/pyodide-pack)

[![GH Actions](https://github.com/rth/pyodide-pack/workflows/main/badge.svg)](https://github.com/rth/pyodide-pack/actions?query=branch%3Amain+)

Python packages bundler for the web

Pyodide-pack evaluates at runtime Python modules accessed in a given application running in Pyodide/Node.js, then creates a bundle with only the required Python modules. This allows to significantly reduce the download size of Python applications, provided that the code to execute is known in advance.

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

   X, y = load_iris(return_X_y=True)
   estimator = Ridge()
   estimator.fit(X, y)
   ```
   This application can run with Pyodide, and will need to download around 21MB of packages for numpy, scipy, scikit-learn and joblib.

2. Create the package bundle,
   ```bash
   pyodide-bundle app.py
   ```   
   which would produce the following output
   ```


## Implementation

This bundler relies on intercepting `FS.open` calls in read mode, which includes files in the Emscripten's MEMFS opened both from Python and Javascript. Package wheels are then repacked into a single bundle with the accessed files.


## License

Pyodide-pack uses the [Mozilla Public License Version 2.0](https://choosealicense.com/licenses/mpl-2.0/).