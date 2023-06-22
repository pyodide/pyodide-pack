import ast
import shutil
import sys
import zipfile
from pathlib import Path
from time import perf_counter

import typer


class _StripDocstringsTransformer(ast.NodeTransformer):
    """Strip docstring in an AST tree.

    AST parsing also strips comments.
    """

    def visit_FunctionDef(self, node):
        """Remove the docstring from the function definition"""
        if ast.get_docstring(node, clean=False) is not None:
            del node.body[0]
        # Continue processing the function's body
        self.generic_visit(node)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef
    visit_ClassDef = visit_FunctionDef


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


def main(
    input_dir: Path = typer.Argument(..., help="Path to the folder to compress"),
    strip_docstrings: bool = typer.Option(False, help="Strip docstrings"),
) -> None:
    """Minify a folder of Python files."""
    output_dirname = input_dir.name + "_stripped"
    if strip_docstrings:
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

        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        if strip_docstrings:
            tree = _strip_module_docstring(tree)
            tree = _StripDocstringsTransformer().visit(tree)

        uncommented_code = ast.unparse(tree)
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
