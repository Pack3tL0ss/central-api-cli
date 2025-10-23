import pytest
from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


@pytest.mark.parametrize(
    "args",
    [
        ("--pnc", "-M", "6"),
        ("--no-mask",),
        ("--yaml",)
    ]
)
def test_export_redsky_bssids(args: tuple[str]):
    result = runner.invoke(app, ["export", "redsky-bssids", *args, "-y"])
    capture_logs(result, "test_export_redsky_bssids")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_export_redsky_bssids_too_many_filters():
    result = runner.invoke(app, ["export", "redsky-bssids", "--site", test_data["ap"]["site"], "--group", test_data["ap"]["group"]])
    capture_logs(result, "test_export_redsky_bssids_too_many_filters", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout


@pytest.mark.parametrize(
    "args,expect",
    [
        ([], None),
        (["-G", "-R", "--show"], "ignoring"), # -R invalid w/ -G will display warning
        (["--switch"], None),
        (["--match", test_data["ap"]["group"][0:-2]], None),
        (["--ap", "--env"], None),
    ]
)
def test_export_configs(args: list[str], expect: str | None):
    result = runner.invoke(app, ["export", "configs", *args, "-Y"])
    capture_logs(result, "test_export_configs")
    assert result.exit_code <= 1
    if expect:
        assert expect in result.stdout
    assert "Done" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ("--match", "XXYYNO_MATCH_ZZ"),
        ("--match", "VPNC", "--gw", "-G"),
    ]
)
def test_export_configs_fail(args: list[str]):
    result = runner.invoke(app, ["export", "configs", *args, "-Y"])
    capture_logs(result, "test_export_configs_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout
