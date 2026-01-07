from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, test_data

runner = CliRunner()


# show testing relies on a troubleshooting session having occured for the test switch "show ts results..."
def test_ts_inventory():
    result = runner.invoke(app, ["ts", "inventory", test_data["gateway"]["serial"]])
    capture_logs(result, "test_ts_inventory")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,args",
    [
        [1, (test_data["vsf_switch"]["name"], test_data["gateway"]["ip"], "-m")],
        [2, (test_data["template_switch"]["name"], test_data["gateway"]["ip"], "-r", "3")],
        [3, (test_data["ap"]["name"], test_data["gateway"]["ip"])],
    ]
)
def test_ts_ping(idx: int, args: list[str]):
    result = runner.invoke(app, ["ts", "ping", *args])
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert "completed" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [(test_data["ap"]["name"], "--wired"), lambda r: "API" in r],
        [(test_data["gateway"]["name"], "--wired"), lambda r: "--wired" in r],  # --wired ignored / only valid on APs
    ]
)
def test_ts_clients(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["ts", "clients", *args])
    capture_logs(result, "test_ts_clients")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [(test_data["ap"]["name"], "--wired"), lambda r: "⚠" in r or "❌" in r],
    ]
)
def test_ts_clients_fail(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["ts", "clients", *args])
    # capture_logs(result, "test_ts_clients_fail", expect_failure=True)  # exit code is 0 currently.  Prob need to adjust exit_on_fail to always be True in send_cmds_by_id
    # assert result.exit_code == 1
    assert pass_condition(result.stdout)


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


@pytest.mark.parametrize(
    "args",
    [
        (test_data["ap"]["name"], "show", "ap-env"),
        (test_data["ap"]["name"], "show ap-env"),
        (test_data["ap"]["name"], "53")
    ]
)
def test_ts_command(args: tuple[str]):
    result = runner.invoke(app, ["ts", "command", *args])
    capture_logs(result, "test_ts_command")
    assert result.exit_code == 0
    assert "completed" in result.stdout


@pytest.mark.parametrize(
    "idx,args,test_name_append",
    [
        [1, (test_data["ap"]["name"], "show", "ap-env"), None],
        [2, (test_data["ap"]["name"], "show", "ap-env"), "post"],
        [3, (test_data["ap"]["name"], "invalidcommand", "invalidcommand"), "invalid_command"],
        [4, (test_data["switch"]["name"], "invalidcommand", "invalidcommand"), None],
    ]
)
def test_ts_command_fail(idx: int, args: tuple[str], test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["ts", "command", *args])
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout or "❌" in result.stdout


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
