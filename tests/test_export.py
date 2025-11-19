from __future__ import annotations

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
    "_,args,expect",
    [
        [1, (), None],
        [2, ("-G", "-R", "--show"), "ignoring"], # -R invalid w/ -G will display warning
        [3, ("--switch",), None],
        [4, ("--switch", "-s"), None],
        [5, ("--gw", "-s", "--group", test_data["gateway"]["group"]), None],
        [6, ("--ap", "-s", "--group", test_data["ap"]["group"]), None],
        [7, ("--match", test_data["ap"]["group"][0:-2]), None],
        [8, ("--ap", "--env"), None],
        [9, ("--ap", "--env", "-s"), None],
        [10, ("--cx", "--group", test_data["template_switch"]["group"], "-V"), None],  # variables
        [11, ("--cx", "--group", test_data["template_switch"]["group"], "-V", "--show"), None],  # variables
    ]
)
def test_export_configs(_: int, args: tuple[str], expect: str | None):
    result = runner.invoke(app, ["export", "configs", *args, "-Y"])
    capture_logs(result, "test_export_configs")
    assert result.exit_code == 0
    if expect:
        assert expect in result.stdout
    assert "Done" in result.stdout


@pytest.mark.parametrize(
    "_,args",
    [
        [1, ("--match", "XXYYNO_MATCH_ZZ")],
        [2, ("--match", "VPNC", "--gw", "-G")],
        [3, ("--ap", "--groups-only")],
    ]
)
def test_export_configs_fail(_: int, args: tuple[str]):
    result = runner.invoke(app, ["export", "configs", *args, "-Y"])
    capture_logs(result, "test_export_configs_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout
