from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


def test_assign_label(ensure_cache_label1):
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "assign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            test_data["switch"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_assign_label")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout

