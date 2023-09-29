
async function main() {
  const { loadPyodide } = require("pyodide");
  let fs = await import("fs");

  let pyodide = await loadPyodide()
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

  // Monkeypatching findObject calls used in dlopen
  let loadDynlibCalls = [];
  const loadDynlib_orig = pyodide._api.loadDynlib;
  pyodide._api.loadDynlib = function(path, global) {
	console.error("loadDynlib", path, global);
	loadDynlibCalls.push({"path": path, "global": global});
	return loadDynlib_orig(path, dontResolveLastLink);
  }

  try {
  	await pyodide.loadPackage({{packages}});
  } catch (e) {
	console.log("Failed to load packages with loadPackage, re-trying with micropip.");
	await pyodide.loadPackage("micropip");
	let micropip = pyodide.pyimport("micropip");
	await micropip.install({{packages}});
  }

  await pyodide.runPythonAsync(`
{{ code }}
`);
  // Run code used in the loader
  await pyodide.runPythonAsync(`
import pyodide.http
`);
  // Look for loaded modules. That's the only way to access imported stdlib from the zipfile.
  let sysModules = pyodide.runPython(
	"import sys; {name: getattr(mod, '__file__', None) for name, mod in sys.modules.items()}"
  ).toJs({dict_converter : Object.fromEntries});

  // writing the list of accessed files to disk
  var obj = {
	opened_file_names: file_list,
	loaded_packages: pyodide.loadedPackages,
	load_dyn_lib_calls: loadDynlibCalls,
	sys_modules: sysModules,
	LDSO_loaded_libs_by_handle: pyodide._module.LDSO['loadedLibsByHandle'],
  };
  if ("micropip" in pyodide.loadedPackages) {
    obj.pyodide_lock = pyodide.pyimport("micropip").freeze();
  }
  // For some reason there is a double / in the path
  obj.stdlib_prefix = pyodide.pyimport('sysconfig').get_path('stdlib').replace('//', '/');
  let jsonString = JSON.stringify(obj);
  let file = fs.createWriteStream("{{ output_path }}");
  file.write(jsonString);
  file.end();
}
main();
