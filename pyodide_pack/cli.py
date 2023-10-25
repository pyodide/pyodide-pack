import json
import shutil
import sys
import zipfile
from pathlib import Path
from time import perf_counter

import typer
from pydantic import parse_obj_as
from pyodide_lock import PyodideLockSpec
from rich.console import Console
from rich.live import Live
from rich.table import Table

from pyodide_pack._utils import (
    _get_packages_from_lockfile,
    spawn_web_server,
)
from pyodide_pack.archive import ArchiveFile
from pyodide_pack.config import PackConfig, _find_pyproject_toml, _get_config_section
from pyodide_pack.runners.node import NodeRunner
from pyodide_pack.runtime_detection import PackageBundler, RuntimeResults

ROOT_DIR = Path(__file__).parents[1]


def main(
    example_path: Path,
    verbose: bool = typer.Option(
        False, "-v", help="Increase verbosity (currently ignored)"
    ),
    config_path: Path = typer.Option(
        None,
        "--config",
        help="Path to the pyproject.toml with the tool.pyodide_pack section",
    ),
    include_paths: str = typer.Option(
        None,
        "--include",
        help='One or multiple glob patterns separated by "," of extra files to include',
    ),
    write_debug_map: bool = typer.Option(
        False,
        help="Write a debug map (to './debug-map.json') with all"
        "the detected imports for the generated bundle",
    ),
):  # type: ignore
    """Create a minimal bundle for a Pyodide application with the required dependencies

    Experimental: this is based on runtime dependency analysis and may not work for all
    applications.
    """
    console = Console()
    console.print(
        f"Running [bold]pyodide pack[/bold] on [bold]{example_path}[/bold] in Node.js"
    )

    if config_path is not None:
        if not config_path.exists():
            console.print(f"config {config_path} does not exist")
            sys.exit(1)
        config_data = _get_config_section(config_path)
        if config_data is None:
            console.print(
                f"could not find the [tool.pyodide_pack] section in " f"{config_path}"
            )
            sys.exit(1)
        config = parse_obj_as(PackConfig, config_data)
    else:
        config_path = _find_pyproject_toml(example_path.parent)
        if config_path is None:
            console.print(
                "Could not find pyproject.toml, falling back to "
                "defaults modified by CLI arguments"
            )
            config = PackConfig()
        else:
            config_data = _get_config_section(config_path)
            if config_data is None:
                console.print(
                    "Could not find [tool.pyodide_pack] section in"
                    f"{config_path}, falling back to "
                    "defaults modified by CLI arguments"
                )
                config = PackConfig()
            else:
                config = parse_obj_as(PackConfig, config_data)
                console.print(f"Loaded config from {config_path}")
    if include_paths is not None:
        config.include_paths = include_paths.split(",")

    console.print(
        "\n[bold]Note:[/bold] unless otherwise specified all sizes are given "
        "for gzip compressed files to be representative of CDN compression.\n"
    )
    code = example_path.read_text()

    js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "discovery.js"
    js_template_kwargs = dict(
        code=code, packages=config.requires, output_path="results.json"
    )
    with NodeRunner(js_template_path, ROOT_DIR, **js_template_kwargs) as runner:
        t0 = perf_counter()
        runner.run()
        console.print(
            f"\nDone input code execution in [bold]{perf_counter() - t0:.1f} s[/bold]\n"
        )

        db = RuntimeResults.from_json(runner.tmp_path / "results.json")

    if write_debug_map:
        db.to_json(Path("./debug-map.json"))

    package_dir = ROOT_DIR / "node_modules" / "pyodide"

    if "pyodide_lock" in db:
        pyodide_lock = PyodideLockSpec(**json.loads(db["pyodide_lock"]))
    else:
        pyodide_lock = PyodideLockSpec.from_json(package_dir / "pyodide-lock.json")

    packages = _get_packages_from_lockfile(
        pyodide_lock, db["loaded_packages"], package_dir
    )

    stdlib_archive = ArchiveFile(package_dir / "python_stdlib.zip", name="stdlib")
    stdlib_stripped_path = Path("python_stdlib_stripped.zip")

    packages_size = sum(el.total_size(compressed=False) for el in packages.values())
    packages_size_gzip = sum(el.total_size(compressed=True) for el in packages.values())
    console.print(
        f"Detected [bold]{len(packages)}[/bold] dependencies with a "
        f"total size of {packages_size_gzip/1e6:.2f} MB  "
        f"(uncompressed: {packages_size/1e6:.2f} MB)"
    )
    total_initial_size = packages_size_gzip + stdlib_archive.total_size(compressed=True)
    console.print(
        f"Total initial size (stdlib + dependencies): {total_initial_size/1e6:.2f} MB"
    )
    console.print("\n")

    out_bundle_path = Path("./pyodide-package-bundle.zip")

    table = Table(title="Packing..")
    table.add_column("No", justify="right")
    table.add_column("Package", max_width=30)
    table.add_column("All files", justify="right")
    table.add_column(".so libs", justify="right")
    table.add_column("Size (MB)", justify="right")
    table.add_column("Reduction", justify="right")

    dynamic_libs = []
    with Live(table) as live:
        with zipfile.ZipFile(
            stdlib_stripped_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as fh_out:
            imported_paths = db.get_imported_paths(strip_prefix=db.stdlib_prefix)
            in_file_names = sorted(stdlib_archive.namelist())
            bundler = PackageBundler(db, config=config)
            for in_file_name in in_file_names:
                if in_file_name not in imported_paths:
                    continue
                in_stream = stdlib_archive.read(in_file_name)
                if in_stream is None:
                    continue
                out_stream = bundler.process_content(in_file_name, in_stream)
                if out_stream is None:
                    continue
                # File paths starting with / fails to get correctly extracted
                # in extract_archive in Pyodide
                with fh_out.open(in_file_name.lstrip("/"), "w") as fh:
                    fh.write(out_stream)
        stdlib_archive_stripped = ArchiveFile(stdlib_stripped_path, name="stdlib")

        msg_0 = "0"
        msg_1 = "stdlib"
        msg_2 = f"{len(stdlib_archive.namelist())} [red]→[/red] {len(stdlib_archive_stripped.namelist())}"
        msg_3 = ""
        msg_4 = (
            f"{stdlib_archive.total_size(compressed=True) / 1e6:.2f} [red]→[/red] "
            f"{stdlib_archive_stripped.total_size(compressed=True)/1e6:.2f}"
        )
        msg_5 = f"{100*(1 - stdlib_archive_stripped.total_size(compressed=True) / stdlib_archive.total_size(compressed=True)):.1f} %"
        table.add_row(msg_0, msg_1, msg_2, msg_3, msg_4, msg_5)
        live.refresh()
        with zipfile.ZipFile(
            out_bundle_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as fh_out:
            for idx, ar in enumerate(sorted(packages.values(), key=lambda x: x.name)):
                # Sort keys for reproducibility
                in_file_names = sorted(ar.namelist())

                bundler = PackageBundler(db, config=config)
                for in_file_name in in_file_names:
                    out_file_name = bundler.process_path(in_file_name)
                    if out_file_name is None:
                        continue
                    in_stream = ar.read(in_file_name)
                    if in_stream is None:
                        continue
                    out_stream = bundler.process_content(in_file_name, in_stream)
                    if out_stream is None:
                        continue
                    # File paths starting with / fails to get correctly extracted
                    # in extract_archive in Pyodide
                    with fh_out.open(out_file_name.lstrip("/"), "w") as fh:
                        fh.write(out_stream)

                dynamic_libs.extend(bundler.dynamic_libs)

                stats = bundler.stats

                msg_0 = f"{idx+1}"
                msg_1 = ar.file_path.name
                msg_2 = f"{len(in_file_names)} [red]→[/red] {stats['fh_out']}"
                msg_3 = f"{stats['so_in']} [red]→[/red] {stats['so_out']}"
                msg_4 = f"{ar.total_size(compressed=True) / 1e6:.2f} [red]→[/red] {stats['size_gzip_out']/1e6:.2f}"
                msg_5 = f"{100*(1 - stats['size_gzip_out'] / ar.total_size(compressed=True)):.1f} %"
                table.add_row(msg_0, msg_1, msg_2, msg_3, msg_4, msg_5)
                live.refresh()

            # Write the list of .so libraries to pre-load
            with fh_out.open("bundle-so-list.txt", "w") as fh:
                for so in sorted(dynamic_libs):
                    fh.write(f"{so.path},{so.shared}\n".encode())
            with fh_out.open("home/pyodide/pyodide_pack_loader.py", "w") as fh:
                loader_path = (
                    Path(__file__).parent / "loader" / "pyodide_pack_loader.py"
                )
                fh.write(loader_path.read_text().encode("utf-8"))

    out_bundle_size = out_bundle_path.stat().st_size
    if packages_size_gzip:
        console.print(
            f"Wrote {out_bundle_path} with {out_bundle_size/ 1e6:.2f} MB "
            f"({100*(1 - out_bundle_size/packages_size_gzip):.1f}% reduction) \n"
        )

    # We start a webserver so that the bundle can be loaded via fetch
    with spawn_web_server(dist_dir=".") as (_, port, server_logs):
        js_template_path = ROOT_DIR / "pyodide_pack" / "js" / "validate.js"
        js_template_kwargs = dict(code=code, output_path="results.json", port=port)
        with NodeRunner(js_template_path, ROOT_DIR, **js_template_kwargs) as runner:
            shutil.copy(
                stdlib_stripped_path, runner.tmp_path / stdlib_stripped_path.name
            )
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

    total_final_size = (
        stdlib_archive_stripped.total_size(compressed=True) + out_bundle_size
    )

    console.print(
        f"\nTotal output size (stdlib + packages): "
        f"{total_final_size/1e6:.2f} MB "
        f"({100*(1 - total_final_size/total_initial_size):.1f}% reduction)"
    )

    console.print("\nBundle validation successful.")


if "sphinx" in sys.modules and __name__ != "__main__":
    app = typer.Typer()
    app.command()(main)
    typer_click_object = typer.main.get_command(app)


if __name__ == "__main__":
    typer.run(main)
