var buff;


async function main() {
  let pyodide_mod = await import("pyodide/pyodide.js");
  let fs = await import("fs");
  let fetch = await import("node-fetch");

  let pyodide = await pyodide_mod.loadPyodide();
  globalThis.fetch = fetch.default;
  // pyodide.registerJsModule('fetch', fetch);
  // The following should work but currently it fails to use the right fetch in node.
  await pyodide.runPythonAsync(`
    from pyodide.http import pyfetch
    import os
    response = await pyfetch("http://0.0.0.0:8000/pyodide-package-bundle.zip")
    await response.unpack_archive(extract_dir='/')
  `)
  
  for (const path of {{ so_files }}) {
    pyodide._module.API.tests.loadDynlib(path, true); 
  }

  await pyodide.runPythonAsync(`
{{ code }}
`);
}
main();
