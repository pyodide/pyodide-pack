let { loadPyodide } = require("hoodmane-pyodide");
let fs = require("fs");

async function main() {
  let pyodide = await loadPyodide();
  let file_list = [];
  const open_orig = pyodide._module.FS.open;
  pyodide._module.FS.open = function (path, flags, mode, fd_start, fd_end) {
    // readonly flag is even https://github.com/emscripten-core/emscripten/blob/e8f25f84933a7973ad1a4e32084a8bf169d67d35/tests/fs/test_trackingdelegate.c#L18
    console.log("-" + path + " mode=" + mode + " flags=" + (flags % 2));
    // only keep files in read mode
    if (flags % 2 == 0) {
      file_list.push(path);
    }
    return open_orig(path, flags, mode, fd_start, fd_end);
  };
  await pyodide.loadPackage("numpy");
  await pyodide.runPythonAsync("import numpy as np");

  // writing the list of accessed files to disk
  let file = fs.createWriteStream("opened_fd.csv");
  // file.on('error', function(err) { /* error handling */ });
  file_list.forEach((v) => file.write(v + "\n"));
  file.end();
}
main();
