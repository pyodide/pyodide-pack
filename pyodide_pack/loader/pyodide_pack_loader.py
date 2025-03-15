from pathlib import Path


async def setup():
    """Load dynamic libraries in the pyodide-pack bundle"""
    try:
        from pyodide_js import _module

        # We need to handle duplicate shared libraries carefully. Many packages
        # that depend on static/shared libraries like h5py and netcdf4 may include
        # them (such as libhdf5_hl.so); loading them more than once, especially one
        # by one instead of their dependent order may cause errors.

        loaded_libs = set()
        so_list_path = Path("/bundle-so-list.txt")
        if not so_list_path.exists():
            print(f"Warning: {so_list_path} not found")
            return

        for line in so_list_path.read_text().splitlines():
            try:
                path, is_shared = line.split(",")

                if path in loaded_libs:
                    continue

                lib_basename = Path(path).name
                if any(lib_basename == Path(loaded).name for loaded in loaded_libs):
                    continue

                await _module.API.loadDynlib(path, bool(is_shared))
                loaded_libs.add(path)
            except Exception as e:
                print(f"Warning: Failed to load {path}: {str(e)}")
    except Exception as e:
        print(f"Error in setup: {str(e)}")
