from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyodide-bundler")
except PackageNotFoundError:
    pass
