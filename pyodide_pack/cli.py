from pathlib import Path
import tempfile
from time import perf_counter
import os
import contextlib
import zipfile
import tarfile

import typer
import jinja2
from rich.console import Console
from subprocess import call

app = typer.Typer()

ROOT_DIR = Path(__file__).parents[1]

class ArchiveFile:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        if file_path.suffix in ['.whl', '.zip']:
            self.opener = zipfile.ZipFile(file_path)
        elif file_path.suffix in ['.tar']:
            self.opener = tarfile.TarFile(file_path)
        else:
            raise NotImplementedError

    def namelist(self):
        if isinstance(self.opener, zipfile.ZipFile):
            return self.opener.namelist()
        else:
            raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.opener.close()

    def open(self, name, **kwargs):
        if isinstance(self.opener, zipfile.ZipFile):
            return self.opener.open(name, **kwargs)
        else:
            raise NotImplementedError





@app.command()
def bundle(example_path: Path, requirement_path: Path = typer.Option(..., "-r")):
    console = Console()
    console.print(f"Running [bold]pyodide-pack[/bold] on [bold]{example_path}[/bold]")
    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "discovery.js"
    requirements = requirement_path.read_text().splitlines()
    code = example_path.read_text()

    with tempfile.TemporaryDirectory() as tmp_dir_str:

        tmp_dir = Path(tmp_dir_str)
        js_template = jinja2.Template(js_template_path.read_text())
        fs_output_path = tmp_dir / "fs_logs.txt"
        js_body = js_template.render(
            code=code, packages=requirements, output_path=fs_output_path
        )
        (tmp_dir / "discovery.js").write_text(js_body)
        (tmp_dir / "node_modules").symlink_to(
            ROOT_DIR / "node_modules", target_is_directory=True
        )
        console.print("Running the input code in Node.js to detect used modules..\n")
        t0 = perf_counter()
        call(["node", str(tmp_dir / "discovery.js")])
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]"
        )

        used_fs_paths = fs_output_path.read_text().splitlines()
        used_fs_paths = list(
            set([path for path in used_fs_paths if "__pycache__" not in path])
        )
        console.print(
            f"\nIn total [bold]{len(used_fs_paths)}[/bold] file paths were opened."
        )

    package_dir = ROOT_DIR / "node_modules" / "pyodide"
    all_package_files = [
        path
        for path_str in os.listdir(package_dir)
        if (path := Path(path_str)).suffix in [".whl", ".tar", ".zip"]
    ]
    all_package_files = [
        el
        for el in all_package_files
        if str(el) not in ["distutils.tar", "pyodide_py.tar"]
    ]
    all_package_size = sum(
        (package_dir / el).stat().st_size for el in all_package_files
    )
    console.print(
        f"Detected [bold]{len(all_package_files)}[/bold] dependencies with a "
        f"total size of {all_package_size/1e6:.2f} MB\n"
    )

    console.print("[bold]Packing:[/bold]")
    out_bundle_path = Path('./pyodide-package-bundle.zip')
    with zipfile.ZipFile(out_bundle_path, 'w', compression=zipfile.ZIP_DEFLATED) as fh_out: 
        for idx, input_archive in enumerate(all_package_files):
            console.print(
                f" - [{idx+1}/{len(all_package_files)}] {input_archive} ({(package_dir / input_archive).stat().st_size / 1e6:.2f} MB): ",
                end="",
            )
            with ArchiveFile(package_dir / input_archive) as fh_in:
                in_file_names = list(set(fh_in.namelist()))
                console.print(
                    f" {len(in_file_names)} [red]→[/red] files",
                    end="",
                )

                n_included = 0
                for in_file_name in in_file_names:
                    out_file_names = [el for el in used_fs_paths if el.endswith(in_file_name)]
                    if len(out_file_names) or in_file_name.endswith('.so'):
                        n_included += 1
                        if len(out_file_names):
                            out_file_name = out_file_names[0]
                        else:
                            out_file_name = str(Path('/lib/python3.10/site-packages/') / in_file_name)
                        with fh_in.open(in_file_name) as fh:
                            stream = fh.read()
                        with fh_out.open(out_file_name.lstrip('/'), 'w') as fh:
                            fh.write(stream)
                console.print(
                        f" {n_included} ([bold]{100*(1 - n_included/len(in_file_names)):.1f}[/bold] % compression)",
                    end="",
                )


            console.print('')
    out_bundle_size = out_bundle_path.stat().st_size
    console.print(f"Wrote {out_bundle_path} with {out_bundle_size/ 1e6:.2f} MB "
                    f"({100*(1 - out_bundle_size/all_package_size):.1f}% compression) \n"
    )

    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "validate.js"

    with tempfile.TemporaryDirectory() as tmp_dir_str:

        tmp_dir = Path(tmp_dir_str)
        js_template = jinja2.Template(js_template_path.read_text())
        js_body = js_template.render(code=code, so_files=[str(el) for el in used_fs_paths if str(el).endswith('.so')])
        (tmp_dir / "validate.js").write_text(js_body)
        (tmp_dir / "node_modules").symlink_to(
            ROOT_DIR / "node_modules", target_is_directory=True
        )
        console.print("Running the input code in Node.js to validate bundle..\n")
        t0 = perf_counter()
        call(["node", str(tmp_dir / "validate.js")])
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]"
        )

    console.print(f"\nBundle generation successful.")


if __name__ == "__main__":
    app()
