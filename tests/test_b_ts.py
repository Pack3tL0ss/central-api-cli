from typer.testing import CliRunner

from centralcli.cli import app  # type: ignore # NoQA

from . import test_data

runner = CliRunner()


# show testing relies on a troubleshooting session having occured for the test switch "show ts results..."
def test_ts_ping():
    result = runner.invoke(app, ["ts", "ping", test_data["switch"]["name"], test_data["gateway"]["ip"]])
    assert result.exit_code == 0
    assert "packets" in result.stdout


def test_ts_clients():
    result = runner.invoke(app, ["ts", "clients", test_data["ap"]["name"]])
    assert result.exit_code == 0
    assert "API" in result.stdout
