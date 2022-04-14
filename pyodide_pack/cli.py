from pathlib import Path

import typer

app = typer.Typer()


@app.command()
def bundle(example_path: Path):
    code = example_path.read_text()


if __name__ == "__main__":
    app()
