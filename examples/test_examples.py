import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from pyodide_pack import cli


def gen_all_examples():
    for path in Path("examples").glob("*"):
        if path.is_dir() and (path / "requirements.txt").exists():
            yield path.resolve()


BASE_DIR = Path(__file__).parents[1]


@pytest.mark.parametrize("example_dir", gen_all_examples())
def test_all(example_dir, tmp_path):
    stdout = StringIO()
    os.chdir(tmp_path)
    # Assumes there is a node_modules in the current directory
    (tmp_path / "node_modules").symlink_to(
        BASE_DIR / "node_modules", target_is_directory=True
    )
    with redirect_stdout(stdout):
        cli.main(
            example_path=example_dir / "app.py",
            requirement_path=example_dir / "requirements.txt",
            verbose=False,
            include_paths=None,
            write_debug_map=True,
        )

    breakpoint()

    print(example_dir)
