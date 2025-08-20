from typer.testing import CliRunner

from centralcli import log
from centralcli.cache import api
from centralcli.cli import app
from centralcli.exceptions import MissingRequiredArgumentException

from . import test_data

runner = CliRunner()


def test_blink_switch_on_timed():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "on", "1"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch_on():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "on"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch_off():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "off"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_wrong_dev_type():
    result = runner.invoke(
        app,
        [
            "blink",
            test_data["gateway"]["mac"],
            "on"
        ]
    )
    log.info("ABOVE ERRORS related to device identifier matching but wrong type are from test run, and can be ignored")
    assert result.exit_code == 1
    assert "Unable to gather" in result.stdout
    assert "excluded" in result.stdout


def test_bounce_interface():
    result = runner.invoke(app, ["bounce",  "interface", test_data["switch"]["name"].lower(), test_data["switch"]["test_ports"][0], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_bounce_poe_multiport():
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(), ",".join(test_data["switch"]["test_ports"]), "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


# This group remains as it is deleted in cleanup of test_update
def test_clone_group():
    result = runner.invoke(app, ["-d", "clone", "group", test_data["gateway"]["group"], test_data["clone"]["to_group"], "-Y"])
    assert result.exit_code == 0  # TODO check this we are not returning a 1 exit_code on resp.ok = False?
    assert "201" in result.stdout or "400" in result.stdout
    assert "Created" in result.stdout or "already exists" in result.stdout


def test_kick_client():
    result = runner.invoke(app, ["kick",  "client", test_data["client"]["wireless"]["name"][0:-2], "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all():
    result = runner.invoke(app, ["kick",  "all", test_data["ap"]["serial"], "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all_by_ssid():
    result = runner.invoke(app, ["kick",  "all", test_data["ap"]["serial"], test_data["kick_ssid"], "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all_missing_argument():
    try:
        api.session.request(api.device_management.kick_users, test_data["ap"]["serial"])
    except MissingRequiredArgumentException:
        ...  # Test Passes
    else:
        raise AssertionError("test_kick_all_missing_argument should have raised a MissingRequiredArgumentException but did not")
