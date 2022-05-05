
async function main() {
  let pyodide_mod = await import("pyodide/pyodide.js");
  let fs = await import("fs");

  let pyodide = await pyodide_mod.loadPyodide()
  let file_list = [];
  const open_orig = pyodide._module.FS.open;
  pyodide._module.FS.open = function (path, flags, mode, fd_start, fd_end) {
    // Read-only flag is even
    // https://github.com/emscripten-core/emscripten/blob/e8f25f84933a7973ad1a4e32084a8bf169d67d35/tests/fs/test_trackingdelegate.c#L18
    // Here we only keep files in read mode.
    if (flags % 2 == 0) {
      file_list.push(path);
    }
    return open_orig(path, flags, mode, fd_start, fd_end);
  };
  await pyodide.loadPackage({{packages}});
  await pyodide.runPythonAsync(`
{{ code }}
`);

  // writing the list of accessed files to disk
  let file = fs.createWriteStream("{{ output_path }}");
  // file.on('error', function(err) { /* error handling */ });
  file_list.forEach((v) => file.write(v + "\n"));
  file.end();
}
main();
