from typer.testing import CliRunner

from centralcli.cli import app

from . import update_log

runner = CliRunner()


def test_del_label():
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label1",
        "-Y"
        ])
    if result.exit_code != 0:
        update_log(result.stdout)
    assert result.exit_code == 0
    assert "200" in result.stdout
