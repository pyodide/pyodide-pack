import subprocess
import tempfile
from pathlib import Path

import jinja2


class NodeRunner:
    def __init__(self, path: Path, node_root: Path, **kwargs):
        """Setup a Node.js runner

        This also copies a Jinja2 template of a Javascript file and renders it
        with the provided kwargs

        Parameters
        ----------
        path
           template path
        kwargs
           kwargs used to render the template with Jinja2
        """
        template = jinja2.Template(path.read_text())
        self.template_name = path.name
        self._tmp_path = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp_path.name)
        js_body = template.render(**kwargs)
        (self.tmp_path / self.template_name).write_text(js_body)
        (self.tmp_path / "node_modules").symlink_to(
            node_root / "node_modules", target_is_directory=True
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._tmp_path.cleanup()

    def run(self):
        subprocess.run(
            ["node", str(self.tmp_path / self.template_name)],
            check=True,
            cwd=str(self.tmp_path),
        )
