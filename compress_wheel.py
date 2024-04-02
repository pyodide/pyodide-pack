import zipfile
from pathlib import Path


def main():
    WHEELS_DIR = Path("./node_modules/hoodmane-pyodide/")
    fd_to_keep = Path("opened_fd.csv").read_text().splitlines()

    site_packages_prefix = "/lib/python3.10/site-packages/"

    fd_to_keep = [el for el in fd_to_keep if el.startswith(site_packages_prefix)]
    fd_to_keep = [el.replace(site_packages_prefix, "") for el in fd_to_keep]

    with (
        zipfile.ZipFile(
            WHEELS_DIR / "numpy-1.22.3-cp310-cp310-emscripten_wasm32.whl", "r"
        ) as zin,
        zipfile.ZipFile("/tmp/out.whl", "w") as zout,
    ):
        for item in zin.infolist():
            buff = zin.read(item.filename)
            keep = False
            if ".dist-info" in item.filename:
                keep = True
            elif item.filename in fd_to_keep:
                keep = True
            if not keep:
                continue
            print(item.filename)
            zout.writestr(item, buff)


if __name__ == "__main__":
    main()
