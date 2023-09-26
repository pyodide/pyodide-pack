var buff;


async function main() {
  let { loadPyodide } = require("pyodide");
  let fs = await import("fs");
  let fetch = await import("node-fetch");
  let bench = new Object();

  let t0 = process.hrtime.bigint();
  let pyodide = await loadPyodide({fullStdLib: false, stdLibURL: "http://127.0.0.1:{{ port }}/python_stdlib_stripped.zip"});
  bench.loadPyodide = Number(process.hrtime.bigint() - t0);


  globalThis.fetch = fetch.default;

  t0 = process.hrtime.bigint();
  await pyodide.runPythonAsync(`
    from pyodide.http import pyfetch

    response = await pyfetch("http://127.0.0.1:{{ port }}/pyodide-package-bundle.zip")
    await response.unpack_archive(extract_dir='/')
  `);
  bench.fetch_unpack_archive = Number(process.hrtime.bigint() - t0);
  await pyodide.runPythonAsync(`
    from pathlib import Path

    assert Path('/home/pyodide/pyodide_pack_loader.py').exists()
  `)

  t0 = process.hrtime.bigint();

  let pp_loader = pyodide.pyimport('pyodide_pack_loader');
  await pp_loader.setup()

  bench.load_dynamic_libs = Number(process.hrtime.bigint() - t0);

  t0 = process.hrtime.bigint();

  await pyodide.runPythonAsync(`
{{ code }}
`);
  bench.import_run_app = Number(process.hrtime.bigint() - t0);

  let jsonString = JSON.stringify(bench);
  let file = fs.createWriteStream("{{ output_path }}");
  file.write(jsonString);
  file.end();

}
main();
