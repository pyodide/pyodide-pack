import ast
import fnmatch
import shutil
import sys
import zipfile
from pathlib import Path
from time import perf_counter

import typer

from pyodide_pack.config import PyPackConfig

STRIP_DOCSTRING_EXCLUDES: list[str] = []
STRIP_DOCSTRING_MODULE_EXCLUDES: list[str] = [
    "numpy/*"  # known issue for v1.25 to double check for v1.26
]


class _StripDocstringsTransformer(ast.NodeTransformer):
    """Strip docstring in an AST tree.

    AST parsing also strips comments.
    """

    def visit_FunctionDef(self, node):
        """Remove the docstring from the function definition"""
        if ast.get_docstring(node, clean=False) is not None:
            del node.body[0]
            if not len(node.body):
                # Nothing left in the body, add a pass statement
                node.body.append(ast.Pass())

        # Continue processing the function's body
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


def _path_matches_patterns(path: str, patterns: list[str]) -> bool:
    """Check if a path matches any of the patterns."""
    for pattern in patterns:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def _strip_module_docstring(tree: ast.Module) -> ast.Module:
    """Remove docstring from module.

    If the first statement is an expression with a string value, remove it.
    """
    if (
        tree.body
        and isinstance(expr := tree.body[0], ast.Expr)
        and isinstance(expr.value, ast.Str | ast.Constant)
        and isinstance(expr.value.value, str)
    ):
        tree.body.pop(0)
    return tree


def _rewrite_py_code(
    code: str,
    file_name: str,
    py_config: PyPackConfig,
) -> str:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    try:
        if py_config.strip_docstrings and not _path_matches_patterns(
            file_name, STRIP_DOCSTRING_EXCLUDES
        ):
            tree = _strip_module_docstring(tree)
        if py_config.strip_module_docstrings and not _path_matches_patterns(
            file_name, STRIP_DOCSTRING_MODULE_EXCLUDES
        ):
            tree = _StripDocstringsTransformer().visit(tree)
        uncommented_code = ast.unparse(tree)
    except RecursionError:
        # Some files (e.g. modules in sympy) produce a recursion error when running
        # the node transformer on them
        print(f"Skipping AST rewrite for {file_name} due to RecursionError")
        uncommented_code = code

    return uncommented_code


def main(
    input_dir: Path = typer.Argument(..., help="Path to the folder to compress"),
    strip_docstrings: bool = typer.Option(False, help="Strip docstrings"),
    strip_module_docstrings: bool = typer.Option(
        False, help="Strip module lebel docstrings"
    ),
    # py_compile: bool = typer.Option(False, help="py-compile files")
) -> None:
    """Minify a folder of Python files.

    Note: this API will change before the next release
    """
    output_dirname = input_dir.name + "_stripped"
    py_config = PyPackConfig(
        strip_docstrings=strip_docstrings,
        strip_module_docstrings=strip_module_docstrings,
        py_compile=False,
    )
    if py_config.strip_docstrings:
        output_dirname += "_no_docstrings"
    output_dir = input_dir.parent / output_dirname
    shutil.rmtree(output_dir, ignore_errors=True)
    shutil.copytree(input_dir, output_dir)
    t0 = perf_counter()
    n_processed = 0
    for file in output_dir.glob("**/*.py"):
        if not file.is_file():
            continue

        try:
            code = file.read_text()
        except UnicodeDecodeError:
            continue
        uncommented_code = _rewrite_py_code(
            code, file_name=str(file), py_config=py_config
        )

        if uncommented_code is None:
            continue

        file.write_text(uncommented_code)
        n_processed += 1

    typer.echo(f"Processed {n_processed} files in {perf_counter() - t0:.2f} seconds")

    zip_path = output_dir.parent / (output_dir.name + ".zip")
    with zipfile.ZipFile(zip_path, "w", compression=0) as fh:
        for file in output_dir.glob("**/*"):
            if not file.is_file():
                continue
            fh.write(file, file.relative_to(output_dir))
    typer.echo(f"Created zip file at {zip_path}")


if "sphinx" in sys.modules and __name__ != "__main__":
    app = typer.Typer()
    app.command()(main)
    typer_click_object = typer.main.get_command(app)
