function patchFSopen(pyodide, fileList) {
  // Record FS.open
  // Note: we can't use FS.trackingDelegate since we want this to work without
  // -sFS_DEBUG
  const openOrig = pyodide._module.FS.open;
  pyodide._module.FS.open = function (path, flags, mode, fd_start, fd_end) {
    // Read-only flag is even
    // https://github.com/emscripten-core/emscripten/blob/e8f25f84933a7973ad1a4e32084a8bf169d67d35/tests/fs/test_trackingdelegate.c#L18
    // Here we only keep files in read mode.
    if (flags % 2 == 0) {
      fileList.push(path);
    }
    return openOrig(path, flags, mode, fd_start, fd_end);
  };
}


function pathchLoadDynLib(pyodide, loadDynlibCalls) {
  // Record loadDynlib calls
  const loadDynlibOrig = pyodide._module.loadDynamicLibrary;
  pyodide._module.loadDynamicLibrary = function(libName, flags, localScope, handle) {
	loadDynlibCalls.push({path: libName, global: flags.global});
	return loadDynlibOrig(libName, flags, localScope, handle)
  }
}


function patchSymbolAccess(pyodide, accessedSymbols) {
  // Record accessed symbols in pyodide._module.LDSO
  function wrapSym(symName, sym, libName) {
    if (!sym || typeof sym == "number") {
      return sym;
    }
    return new Proxy(sym, {
      get(sym, attr) {
        if (attr === "stub") {
          if (!(libName in accessedSymbols)) {
            accessedSymbols[libName] = new Set();
          }
          accessedSymbols[libName].add(symName);
        }
        return Reflect.get(sym, attr);
      },
    });
  }

  function wrapExports(exports, libName) {
    if (typeof exports !== "object") {
      return exports;
    }
    return new Proxy(exports, {
      get(exports, symName) {
        const sym = Reflect.get(exports, symName);
        if (libName in accessedSymbols &&  accessedSymbols[libName].has(symName)) {
          return sym;
        }
        return wrapSym(symName, sym, libName);
      },
    });
  }

  function wrapLib(lib, libName) {
    return new Proxy(lib, {
      get(lib, sym) {
        return wrapExports(Reflect.get(lib, sym), libName);
      },
    });
  }
  origLoadedlibs = pyodide._module.LDSO.loadedLibsByName;
  pyodide._module.LDSO.loadedLibsByName = new Proxy(origLoadedlibs, {
    set(libsByName, libName, lib) {
      return Reflect.set(libsByName, libName, wrapLib(lib, libName));
    },
  });
}


async function main() {
  const { loadPyodide } = require("pyodide");
  let fs = await import("fs");

  let pyodide = await loadPyodide()
  let fileList = [];
  patchFSopen(pyodide, fileList);

  let loadDynlibCalls = [];
  pathchLoadDynLib(pyodide, loadDynlibCalls);

  var accessedSymbols = new Object();
  patchSymbolAccess(pyodide, accessedSymbols);


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

  // Convert accessedSymbols to from Set to Array, so it can be serialized
  accessedSymbolsOut = new Object();
  for (const libName in accessedSymbols) {
     accessedSymbolsOut[libName] = Array.from(accessedSymbols[libName]);
  }

  // writing the list of accessed files to disk
  var obj = {
	opened_file_names: fileList,
	loaded_packages: pyodide.loadedPackages,
	load_dyn_lib_calls: loadDynlibCalls,
	sys_modules: sysModules,
	LDSO_loaded_libs_by_handle: pyodide._module.LDSO['loadedLibsByHandle'],
	dl_accessed_symbols: accessedSymbolsOut,
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
