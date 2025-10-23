import pytest
from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


# show testing relies on a troubleshooting session having occured for the test switch "show ts results..."
def test_ts_inventory():
    result = runner.invoke(app, ["ts", "inventory", test_data["gateway"]["serial"]])
    capture_logs(result, "test_ts_inventory")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ([test_data["vsf_switch"]["name"], test_data["gateway"]["ip"], "-m"]),
        ([test_data["template_switch"]["name"], test_data["gateway"]["ip"]]),
    ]
)
def test_ts_ping(args: list[str]):
    result = runner.invoke(app, ["ts", "ping", *args])
    capture_logs(result, "test_ts_ping")
    assert result.exit_code == 0
    assert "completed" in result.stdout


def test_ts_clients():
    result = runner.invoke(app, ["ts", "clients", test_data["ap"]["name"]])
    capture_logs(result, "test_ts_clients")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_ts_images():
    result = runner.invoke(app, ["ts", "images", test_data["ap"]["name"]])
    capture_logs(result, "test_ts_images")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_ts_clear():
    result = runner.invoke(app, ["ts", "clear", test_data["switch"]["mac"]])
    capture_logs(result, "test_ts_clear")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_ts_command():
    result = runner.invoke(app, ["ts", "command", test_data["ap"]["name"], "show", "ap-env"])
    capture_logs(result, "test_ts_command")
    assert result.exit_code == 0
    assert "completed" in result.stdout


def test_ts_show_tech():
    result = runner.invoke(app, ["ts", "show-tech", test_data["switch"]["name"]])
    capture_logs(result, "test_ts_show_tech")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_ts_clients_wired():
    result = runner.invoke(app, ["ts", "clients", test_data["wired_clients_ap"]["name"]])
    capture_logs(result, "test_ts_clients_wired")
    assert result.exit_code == 0
    assert "completed" in result.stdout


def test_ts_dpi():
    result = runner.invoke(app, ["ts", "dpi", test_data["ap"]["name"]])
    capture_logs(result, "test_ts_dpi")
    assert result.exit_code == 0
    assert "completed" in result.stdout


def test_ts_ssid():
    result = runner.invoke(app, ["ts", "ssid", test_data["ap"]["name"]])
    capture_logs(result, "test_ts_ssid")
    assert result.exit_code == 0
    assert "completed" in result.stdout


def test_ts_overlay():
    result = runner.invoke(app, ["ts", "overlay", test_data["ap"]["name"]])
    capture_logs(result, "test_ts_overlay")
    assert result.exit_code == 0
    assert "completed" in result.stdout
