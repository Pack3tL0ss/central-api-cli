from typer.testing import CliRunner

from centralcli.cli import app

from . import test_data, update_log

runner = CliRunner()


def test_assign_label():
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "assign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            "-Y"
        ]
    )
    if result.exit_code != 0:
        update_log(result.stdout)
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout
