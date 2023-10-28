# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

 - Add configuration for `pyodide pack` loaded from the `[tool.pyodide_pack]` section of a
   `pyproject.toml` files
   [#35](https://github.com/pyodide/pyodide-pack/pull/35)


 - Add `pyidide minify` command to minify the Python packages with AST rewrites by,
   removing comments and docstrings
   [#23](https://github.com/pyodide/pyodide-pack/pull/23)

 - Add support for stdlib bundling in `pyodide pack`
   [#27](https://github.com/pyodide/pyodide-pack/pull/27)

 - Add support for packages installed via micropip in `pyodide pack`
   [#31](https://github.com/pyodide/pyodide-pack/pull/31)

## Fixed

 - Fix a syntax error when stripping docstrings from a function with an empty body
   [#35](https://github.com/pyodide/pyodide-pack/pull/35)


### Changed

 - Added support for Pyodide 0.24.0. This is now the minimal supported version of Pyodide.
   [#26](https://github.com/pyodide/pyodide-pack/pull/26)

## Fixed

 - Fix a syntax error when stripping docstrings from a function with an empty body
   [#35](https://github.com/pyodide/pyodide-pack/pull/35)


## [0.2.0] - 2022-09-04

### Changed

 - the CLI API was changed to `pyodide pack`

## [0.1.0] - 2022-09-02

Initial release
