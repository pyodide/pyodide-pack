from subprocess import check_output


def test_cli_help():
    output = check_output(["pyodide", "pack", "--help"]).decode("utf-8")
    assert "Create a minimal bundle" in output
