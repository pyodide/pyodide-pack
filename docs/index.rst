.. pyodide-pack documentation master file, created by
   sphinx-quickstart on Thu Jun 22 21:54:44 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyodide-pack
============

Python package bundler and minifier for the web

Pyodide-pack aims to reduce the size and load time of Python applications running in the browser using different strategies:

- Minification of the source code via AST rewrite
- Transformation of the source code into a different format such as Python bytecode (.pyc files)
- Dead code elimination, by removing unused Python modules (detected at runtime)

Each of these approaches have different tradeoffs, and can be used separately or in combination.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   ast-rewrite.md
   module-elimination-at-runtime.md
   cli.md
   configuration.md
