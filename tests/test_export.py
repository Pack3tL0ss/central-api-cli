from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


def test_export_redsky_bssids():
    result = runner.invoke(app, ["export", "redsky-bssids", "--pnc", "-y"])
    capture_logs(result, "test_export_redsky_bssids")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_export_redsky_bssids_no_mask():
    result = runner.invoke(app, ["export", "redsky-bssids", "--no-mask", "-y"])
    capture_logs(result, "test_export_redsky_bssids_no_mask")
    assert result.exit_code == 0
    assert "BSSID" in result.stdout


def test_export_redsky_bssids_yaml():
    result = runner.invoke(app, ["export", "redsky-bssids", "--yaml", "-y"])
    capture_logs(result, "test_export_redsky_bssids_yaml")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_export_redsky_bssids_too_many_filters():
    result = runner.invoke(app, ["export", "redsky-bssids", "--site", test_data["ap"]["site"], "--group", test_data["ap"]["group"]])
    capture_logs(result, "test_export_redsky_bssids_too_many_filters", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout

def test_export_configs():
    result = runner.invoke(app, ["export", "configs", "-y"])
    capture_logs(result, "test_export_configs")
    assert result.exit_code == 0
    assert "Done" in result.stdout

def test_export_configs_group_only():
    result = runner.invoke(app, ["export", "configs", "-G", "-R", "--show", "--yes"])  # -R invalid w/ -G will display warning
    capture_logs(result, "test_export_configs_group_only")
    assert result.exit_code == 0
    assert "ignoring" in result.stdout
    assert "Done" in result.stdout