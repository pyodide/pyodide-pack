# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
import sys
from importlib import metadata as importlib_metadata
from pathlib import Path

# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "pyodide-pack"
copyright = "2023, Pyodide maintainers"
author = "Pyodide maintainers"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
    "sphinx_autodoc_typehints",
]
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.10", None),
    "pyodide": ("https://pyodide.org/en/stable/", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
sys.path.append(Path(__file__).parent.parent.as_posix())

html_theme = "sphinx_book_theme"
html_logo = "_static/img/pyodide-logo.png"
html_static_path = ["_static"]
try:
    release = importlib_metadata.version("pyodide-pack")
except importlib_metadata.PackageNotFoundError:
    print("Could not find package version, please install micropip to build docs")
    release = "0.0.0"
