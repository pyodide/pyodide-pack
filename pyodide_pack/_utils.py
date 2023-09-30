import multiprocessing
import os
import shutil
import sys
import tempfile
import urllib.request
from contextlib import contextmanager
from pathlib import Path

from pyodide_lock import PyodideLockSpec

from pyodide_pack.archive import ArchiveFile


def match_suffix(file_paths: list[str], suffix: str) -> str | None:
    """Match suffix in a list of file paths.

    Return the most likely path or None of None matched

    Examples
    --------
    >>> match_suffix(['/usr/a.py', '/usr/b/d.py'], 'd.py')
    '/usr/b/d.py'
    >>> match_suffix(['/usr/a.py', '/usr/b/d.py'], 'c.py')
    >>> match_suffix(['/usr/a.py', '/usr/b/a.py'], 'a.py')
    '/usr/a.py'
    """
    results = [el for el in file_paths if el.endswith(suffix)]
    match results:
        case []:
            return None
        case [path]:
            return path
        case _:
            # If there are multiple matches, we return the shortest
            # one as less likely to be a vendored package.
            # for instance numpy/__init__.py will match both
            #  - /lib/.../numpy/__init__.py
            #  - /lib/.../pandas/compat/numpy/__init__.py
            # however only the first one is correct
            results = list(sorted(results, key=len))
            return results[0]


# Adapted from pyodide conftest.py


def run_web_server(q: multiprocessing.Queue, log_filepath, dist_dir):
    """Start the HTTP web server

    Parameters
    ----------
    q : Queue
      communication queue
    log_path : pathlib.Path
      path to the file where to store the logs
    """
    import http.server
    import socketserver

    os.chdir(dist_dir)

    log_fh = log_filepath.open("w", buffering=1)
    sys.stdout = log_fh
    sys.stderr = log_fh

    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format_, *args):
            print(
                "[{}] source: {}:{} - {}".format(
                    self.log_date_time_string(), *self.client_address, format_ % args
                )
            )

        def end_headers(self):
            # Enable Cross-Origin Resource Sharing (CORS)
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

    with socketserver.TCPServer(("", 0), Handler) as httpd:
        host, port = httpd.server_address
        print(f"Starting webserver at http://{host}:{port}")  # type: ignore[str-bytes-safe]
        httpd.server_name = "test-server"  # type: ignore[attr-defined]
        httpd.server_port = port  # type: ignore[attr-defined]
        q.put(port)

        httpd.serve_forever()


@contextmanager
def spawn_web_server(dist_dir: str):
    tmp_dir = tempfile.mkdtemp()
    log_path = Path(tmp_dir) / "http-server.log"
    q: multiprocessing.Queue[str] = multiprocessing.Queue()

    p = multiprocessing.Process(target=run_web_server, args=(q, log_path, dist_dir))

    try:
        p.start()
        port = q.get()
        hostname = "127.0.0.1"

        print(
            f"Spawning webserver at http://{hostname}:{port} "
            f"(see logs in {log_path})"
        )
        yield hostname, port, log_path
    finally:
        p.terminate()
        shutil.rmtree(tmp_dir)


def _get_packages_from_lockfile(
    pyodide_lock: PyodideLockSpec, loaded_packages: dict[str, str], package_dir: Path
) -> dict[str, ArchiveFile]:
    """Get the dictionary of packages from a lockfile wrapped into ArchiveFile objects."""
    packages: dict[str, ArchiveFile] = {}
    for key, val in loaded_packages.items():
        if val == "default channel":
            file_name = pyodide_lock.packages[key].file_name
        elif val == "pypi":
            url = pyodide_lock.packages[key].file_name
            file_name = os.path.basename(url)
            # Cache wheels in node_modules/pyodide
            # Will raise an exception if the URL is not valid
            with urllib.request.urlopen(url) as response:
                (package_dir / file_name).write_bytes(response.read())
        else:
            # Otherwise loaded from custom URL
            # TODO: this branch needs testing
            file_name = val

        packages[file_name] = ArchiveFile(package_dir / file_name, name=key)
    return packages
