
async function main() {
  let pyodide_mod = await import("pyodide/pyodide.js");
  let fs = await import("fs");

  let pyodide = await pyodide_mod.loadPyodide()
  let file_list = [];
  const open_orig = pyodide._module.FS.open;
  // Monkeypatch FS.open
  // Note: we can't use FS.trackingDelegate since we want this to work without
  // -sFS_DEBUG
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

  // Monkeypatching findObject calls used in dlopen
  let findObjectCalls = [];
  const findObject_orig = pyodide._module.FS.findObject;
  pyodide._module.FS.findObject = function(path, dontResolveLastLink) {
	findObjectCalls.push(path);
	return findObject_orig(path, dontResolveLastLink);
  }
  await pyodide.runPythonAsync(`
{{ code }}
`);

  // writing the list of accessed files to disk
  var obj = new Object();
  obj.opened_file_names = file_list;
  obj.loaded_packages = pyodide.loadedPackages;
  obj.find_object_calls = findObjectCalls;

  let jsonString = JSON.stringify(obj);
  let file = fs.createWriteStream("{{ output_path }}");
  file.write(jsonString);
  file.end();
}
main();
