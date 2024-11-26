from typer.testing import CliRunner
from centralcli.cli import app
from . import test_data

runner = CliRunner()


# Groups are created in test_add
def test_del_group():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group1",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout


def test_del_group_multiple():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group3",
        "cencli_test_group4",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert result.stdout.count("Success") == 2

def test_del_guest():
    result = runner.invoke(app, ["-d", "delete", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--yes"])
    assert True in [
        result.exit_code == 0 and "200" in result.stdout,
        result.exit_code != 0 and "Unable to gather" in result.stdout
    ]
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout
