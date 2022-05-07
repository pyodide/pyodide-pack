import fnmatch
import gzip
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path
from time import perf_counter

import jinja2
import typer
from rich.console import Console

from pyodide_pack._utils import match_suffix
from pyodide_pack.archive import ArchiveFile

app = typer.Typer()

ROOT_DIR = Path(__file__).parents[1]


@app.command()
def bundle(
    example_path: Path,
    requirement_path: Path = typer.Option(
        None, "-r", help="Path to the requirements.txt file"
    ),
    verbose: bool = typer.Option(False, "-v", help="Increase verbosity"),
    include_so: str = typer.Option(
        None,
        help='One or multiple glob patterns separated by "," of extra .so files to include',
    ),
):  # type: ignore
    console = Console()
    console.print(f"Running [bold]pyodide-pack[/bold] on [bold]{example_path}[/bold]")

    if requirement_path is None:
        requirement_path = example_path.parent / "requirements.txt"
        if not requirement_path.exists():
            console.print(
                f"Error: could not find requirements.txt in {example_path.parent}"
            )
            sys.exit(1)

    console.print(
        "\n[bold]Note:[/bold] unless otherwise specified all sizes are given "
        "for gzip compressed files to take into account CDN compression.\n"
    )
    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "discovery.js"
    requirements = requirement_path.read_text().splitlines()
    console.print(f"Loaded requirements from: {requirement_path}")
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
        subprocess.run(["node", str(tmp_dir / "discovery.js")], check=True)
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]\n"
        )

        with open(fs_output_path) as fh:
            db = json.load(fh)
        used_fs_paths = db["opened_file_names"]

        used_fs_paths = list(
            {path for path in used_fs_paths if "__pycache__" not in path}
        )

    package_dir = ROOT_DIR / "node_modules" / "pyodide"
    with open(package_dir / "packages.json") as fh:
        packages_db = json.load(fh)

    packages = {}
    for key, val in db["loaded_packages"].items():
        if val == "default channel":
            file_name = packages_db["packages"][key]["file_name"]
        else:
            # Otherwise loaded from custom URL
            file_name = val

        packages[file_name] = ArchiveFile(package_dir / file_name)

    packages_size = sum(el.total_size(compressed=False) for el in packages.values())
    packages_size_gzip = sum(el.total_size(compressed=True) for el in packages.values())
    console.print(
        f"Detected [bold]{len(packages)}[/bold] dependencies with a "
        f"total size of {packages_size_gzip/1e6:.2f} MB  "
        f"(uncompressed: {packages_size/1e6:.2f} MB)\n"
    )
    console.print(
        f"In total {len(used_fs_paths)} files and {len(db['find_object_calls'])} "
        "shared libraries were accessed."
    )

    console.print("[bold]Packing:[/bold]")
    out_bundle_path = Path("./pyodide-package-bundle.zip")
    out_so_libs = []
    with zipfile.ZipFile(
        out_bundle_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as fh_out:
        for idx, ar in enumerate(packages.values()):
            console.print(f" - [{idx+1}/{len(packages)}] {ar.name}: ", end="")
            if verbose:
                console.print("")
            in_file_names = list(set(ar.namelist()))

            stats = {
                "py_in": 0,
                "so_in": 0,
                "py_out": 0,
                "so_out": 0,
                "fh_out": 0,
                "size_out": 0,
                "size_gzip_out": 0,
            }
            for in_file_name in in_file_names:
                match Path(in_file_name).suffix:
                    case ".py":
                        stats["py_in"] += 1
                    case ".so":
                        stats["so_in"] += 1

                out_file_name = None
                if out_file_name := match_suffix(used_fs_paths, in_file_name):
                    stats["py_out"] += 1
                elif out_file_name := match_suffix(
                    db["find_object_calls"], in_file_name
                ):
                    stats["so_out"] += 1

                if (
                    out_file_name is None
                    and in_file_name.endswith(".so")
                    and include_so is not None
                    and any(
                        fnmatch.fnmatch(in_file_name, pattern)
                        for pattern in include_so.split(",")
                    )
                ):
                    # TODO: this is hack and should be done better
                    stats["so_out"] += 1
                    out_file_name = os.path.join(
                        "/lib/python3.10/site-utils", in_file_name
                    )

                if out_file_name is not None:
                    stats["fh_out"] += 1
                    stream = ar.read(in_file_name)
                    if stream is not None:
                        stats["size_out"] += len(stream)
                        stats["size_gzip_out"] += len(gzip.compress(stream))
                        if out_file_name.endswith(".so"):
                            out_so_libs.append(out_file_name)
                        with fh_out.open(out_file_name.lstrip("/"), "w") as fh:
                            fh.write(stream)

            msg = f"{len(in_file_names)} [red]→[/red] {stats['fh_out']} files"

            if verbose:
                msg += f" ({stats['py_in']} [red]→[/red] {stats['py_out']} .py, "
                msg += f"{stats['so_in']} [red]→[/red] {stats['so_out']} .so), "
            else:
                msg += ", "

            msg += (
                f"{ar.total_size(compressed=True) / 1e6:.2f} [red]→[/red] {stats['size_gzip_out']/1e6:.2f} MB "
                f"({100*(1 - stats['size_gzip_out'] / ar.total_size(compressed=True)):.1f} % reduction)"
            )
            if verbose:
                # Printing on the next line with indentation
                msg = textwrap.indent(msg, prefix=" " * 8)
            console.print(msg)
        # Write the list of .so libraries to pre-load
        with fh_out.open("bundle-so-list.txt", "w") as fh:
            fh.write("\n".join(out_so_libs).encode("utf-8"))

    out_bundle_size = out_bundle_path.stat().st_size
    console.print(
        f"Wrote {out_bundle_path} with {out_bundle_size/ 1e6:.2f} MB "
        f"({100*(1 - out_bundle_size/packages_size_gzip):.1f}% reduction) \n"
    )

    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "validate.js"

    with tempfile.TemporaryDirectory() as tmp_dir_str:

        tmp_dir = Path(tmp_dir_str)
        js_template = jinja2.Template(js_template_path.read_text())
        js_body = js_template.render(
            code=code,
            so_files=[str(el) for el in used_fs_paths if str(el).endswith(".so")],
        )
        (tmp_dir / "validate.js").write_text(js_body)
        (tmp_dir / "node_modules").symlink_to(
            ROOT_DIR / "node_modules", target_is_directory=True
        )
        console.print("Running the input code in Node.js to validate bundle..\n")
        t0 = perf_counter()
        subprocess.run(["node", str(tmp_dir / "validate.js")], check=True)
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]"
        )

    console.print("\nBundle generation successful.")


if __name__ == "__main__":
    app()
