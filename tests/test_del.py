from typer.testing import CliRunner
from cli import app  # type: ignore # NoQA

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
