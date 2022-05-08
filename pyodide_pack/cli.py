import fnmatch
import gzip
import json
import os
import sys
import zipfile
from pathlib import Path
from time import perf_counter

import typer
from rich.console import Console
from rich.live import Live
from rich.table import Table

from pyodide_pack._utils import match_suffix
from pyodide_pack.archive import ArchiveFile
from pyodide_pack.dynamic_lib import DynamicLib
from pyodide_pack.runners.node import NodeRunner

app = typer.Typer()

ROOT_DIR = Path(__file__).parents[1]


@app.command()
def bundle(
    example_path: Path,
    requirement_path: Path = typer.Option(
        None, "-r", help="Path to the requirements.txt file"
    ),
    verbose: bool = typer.Option(False, "-v", help="Increase verbosity"),
    include_paths: str = typer.Option(
        None,
        help='One or multiple glob patterns separated by "," of extra files to include',
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
    requirements = requirement_path.read_text().splitlines()
    console.print(f"Loaded requirements from: {requirement_path}")
    code = example_path.read_text()

    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "discovery.js"
    js_template_kwargs = dict(
        code=code, packages=requirements, output_path="results.json"
    )
    with NodeRunner(js_template_path, ROOT_DIR, **js_template_kwargs) as runner:

        console.print("Running the input code in Node.js to detect used modules..\n")
        t0 = perf_counter()
        runner.run()
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]\n"
        )

        with open(runner.tmp_path / "results.json") as fh:
            db = json.load(fh)

        db["opened_file_names"] = list(
            {path for path in db["opened_file_names"] if "__pycache__" not in path}
        )
        db["dynamic_libs_map"] = {
            path: DynamicLib(path, load_order=idx)
            for idx, path in enumerate(db["find_object_calls"])
            if path.endswith(".so")
        }

    package_dir = ROOT_DIR / "node_modules" / "pyodide"
    with open(package_dir / "packages.json") as fh:
        packages_json = json.load(fh)

    packages: dict[str, ArchiveFile] = {}
    for key, val in db["loaded_packages"].items():
        if val == "default channel":
            file_name = packages_json["packages"][key]["file_name"]
        else:
            # Otherwise loaded from custom URL
            # TODO: this branch needs testing
            file_name = val

        packages[file_name] = ArchiveFile(package_dir / file_name, name=key)

    packages_size = sum(el.total_size(compressed=False) for el in packages.values())
    packages_size_gzip = sum(el.total_size(compressed=True) for el in packages.values())
    console.print(
        f"Detected [bold]{len(packages)}[/bold] dependencies with a "
        f"total size of {packages_size_gzip/1e6:.2f} MB  "
        f"(uncompressed: {packages_size/1e6:.2f} MB)"
    )
    console.print(
        f"In total {len(db['opened_file_names'])} files and {len(db['find_object_calls'])} "
        "shared libraries were accessed.\n"
    )

    out_bundle_path = Path("./pyodide-package-bundle.zip")

    table = Table(title="Packing..")
    table.add_column("No", justify="right")
    table.add_column("Package", max_width=30)
    table.add_column("All files", justify="right")
    if verbose:
        table.add_column(".py", justify="right")
        table.add_column(".so", justify="right")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Reduction", justify="right")

    dynamic_libs = []
    with zipfile.ZipFile(
        out_bundle_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as fh_out, Live(table) as live:

        for idx, ar in enumerate(sorted(packages.values(), key=lambda x: x.name)):
            # Sort keys for reproducibility
            in_file_names = sorted(ar.namelist())

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
                if out_file_name := match_suffix(db["opened_file_names"], in_file_name):
                    stats["py_out"] += 1
                elif out_file_name := match_suffix(
                    list(db["dynamic_libs_map"].keys()), in_file_name
                ):
                    stats["so_out"] += 1
                    # Get the dynamic library path while preserving order
                    # also determine if it's a shared library or not from
                    # the given package
                    dll = db["dynamic_libs_map"][out_file_name]
                    dll.shared = packages_json["packages"][ar.name].get(
                        "sharedlibrary", False
                    )
                    dynamic_libs.append(dll)

                if (
                    out_file_name is None
                    and include_paths is not None
                    and any(
                        fnmatch.fnmatch(in_file_name, pattern)
                        for pattern in include_paths.split(",")
                    )
                ):
                    # TODO: this is hack and should be done better
                    out_file_name = os.path.join(
                        "/lib/python3.10/site-utils", in_file_name
                    )
                    match Path(in_file_name).suffix:
                        case ".py":
                            stats["py_out"] += 1
                        case ".so":
                            stats["so_out"] += 1
                            # Manually included dynamic libraries are going to be loaded first
                            dll = DynamicLib(out_file_name, load_order=-1000)
                            dll.shared = packages_json["packages"][ar.name].get(
                                "sharedlibrary", False
                            )
                            dynamic_libs.append(dll)

                if out_file_name is not None:
                    stats["fh_out"] += 1
                    stream = ar.read(in_file_name)
                    if stream is not None:
                        stats["size_out"] += len(stream)
                        stats["size_gzip_out"] += len(gzip.compress(stream))
                        # File paths starting with / fails to get correctly extracted
                        # in extract_archive in Pyodide
                        with fh_out.open(out_file_name.lstrip("/"), "w") as fh:
                            fh.write(stream)

            msg_0 = f"{idx+1}"
            msg_1 = ar.file_path.name
            msg_2 = f"{len(in_file_names)} [red]→[/red] {stats['fh_out']}"
            msg_3 = f"{stats['py_in']} [red]→[/red] {stats['py_out']}"
            msg_4 = f"{stats['so_in']} [red]→[/red] {stats['so_out']}"
            msg_5 = f"{ar.total_size(compressed=True) / 1e6:.2f} [red]→[/red] {stats['size_gzip_out']/1e6:.2f}"
            msg_6 = f"{100*(1 - stats['size_gzip_out'] / ar.total_size(compressed=True)):.1f} %"
            if verbose:
                table.add_row(msg_0, msg_1, msg_2, msg_3, msg_4, msg_5, msg_6)
            else:
                table.add_row(msg_0, msg_1, msg_2, msg_5, msg_6)
            live.refresh()

        # Write the list of .so libraries to pre-load
        with fh_out.open("bundle-so-list.txt", "w") as fh:
            for so in sorted(dynamic_libs):
                fh.write(f"{so.path},{so.shared}\n".encode())

    out_bundle_size = out_bundle_path.stat().st_size
    console.print(
        f"Wrote {out_bundle_path} with {out_bundle_size/ 1e6:.2f} MB "
        f"({100*(1 - out_bundle_size/packages_size_gzip):.1f}% reduction) \n"
    )

    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "validate.js"
    js_template_kwargs = dict(code=code, output_path="results.json")
    with NodeRunner(js_template_path, ROOT_DIR, **js_template_kwargs) as runner:
        console.print("Running the input code in Node.js to validate bundle..\n")
        t0 = perf_counter()
        runner.run()
        with open(runner.tmp_path / "results.json") as fh:
            benchmarks = json.load(fh)

    table = Table(title="Validating and benchmarking the output bundle..")
    table.add_column("Step", justify="left")
    table.add_column("Load time (s)", justify="right")
    table.add_column("Fraction of load time", justify="right")
    total_run_time = sum(benchmarks.values())
    for key, val in benchmarks.items():
        table.add_row(key, f"{val/1e9:.2f}", f"{100*val/total_run_time:.1f} %")
    table.add_row(
        "[bold]TOTAL[/bold]",
        f"[bold]{total_run_time/1e9:.2f}[/bold]",
        "[bold]100 %[/bold]",
    )
    console.print(table)

    console.print("\nBundle validation successful.")


if __name__ == "__main__":
    app()
