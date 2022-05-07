var buff;


async function main() {
  let pyodide_mod = await import("pyodide/pyodide.js");
  let fs = await import("fs");
  let fetch = await import("node-fetch");

  let pyodide = await pyodide_mod.loadPyodide({fullStdLib: false});
  globalThis.fetch = fetch.default;
  // pyodide.registerJsModule('fetch', fetch);
  // The following should work but currently it fails to use the right fetch in node.
  await pyodide.runPythonAsync(`
    from pyodide.http import pyfetch
    from pathlib import Path
    import os
    response = await pyfetch("http://0.0.0.0:8000/pyodide-package-bundle.zip")
    await response.unpack_archive(extract_dir='/')
    so_paths = Path('/bundle-so-list.txt').read_text().splitlines()
  `)

  for (const path of pyodide.globals.get('so_paths')) {
    await pyodide._module.API.tests.loadDynlib(path, true);
  }

  await pyodide.runPythonAsync(`
{{ code }}
`);
}
main();
