from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


# show testing relies on a troubleshooting session having occured for the test switch "show ts results..."
def test_ts_inventory():
    result = runner.invoke(app, ["ts", "inventory", test_data["gateway"]["serial"]])
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_ts_ping():
    result = runner.invoke(app, ["ts", "ping", test_data["switch"]["name"], test_data["gateway"]["ip"]])
    capture_logs(result, "test_ts_ping")
    assert result.exit_code == 0
    assert "packets" in result.stdout


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
