from typer.testing import CliRunner

from centralcli import config
from centralcli.cli import app

from . import capture_logs, test_data

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
    capture_logs(result, "test_assign_label")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout


def test_assign_subscription():
    result = runner.invoke(
        app,
        [
            "assign",
            "subscription",
            "advanced-ap",
            test_data["ap"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_assign_subscription", expect_failure=False if not config.is_old_cfg else True)
    assert result.exit_code == 0 if not config.is_old_cfg else 1
    assert "202" in result.stdout if not config.is_old_cfg else "required"
