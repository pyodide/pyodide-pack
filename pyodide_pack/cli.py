from pathlib import Path
import tempfile
from time import perf_counter

import typer
import jinja2
from rich.console import Console
from subprocess import call

app = typer.Typer()


@app.command()
def bundle(example_path: Path, requirement_path: Path = typer.Option(..., '-r')):
    console = Console()
    console.print(f'Running pyodide-bundle on {example_path}')
    js_template_path = Path(__file__).parent / 'js' / 'main.js'
    requirements = requirement_path.read_text().splitlines()
    code = example_path.read_text()

    with tempfile.TemporaryDirectory() as tmp_dir_str:


        tmp_dir = Path(tmp_dir_str)
        js_template = jinja2.Template(js_template_path.read_text())
        fs_output_path = tmp_dir / 'fs_logs.txt'
        js_body = js_template.render(code=code, packages=requirements, output_path=fs_output_path)
        (tmp_dir / 'main.js').write_text(js_body)
        (tmp_dir / 'node_modules').symlink_to(Path(__file__).parents[1] / 'node_modules', target_is_directory=True)
        console.print('Running the input code in Node.js\n')
        t0 = perf_counter()
        call(['node', str(tmp_dir / 'main.js')])
        console.print(f'\nDone input code execution in {perf_counter() - t0:.1f} s\n')





if __name__ == "__main__":
    app()
