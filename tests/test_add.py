# from pathlib import Path
from typer.testing import CliRunner

from centralcli.cli import app  # type: ignore # NoQA
from . import update_log, test_data
from centralcli import cache

update_log(f'{__file__.split("/")[-1]}: {id(cache)}')

runner = CliRunner()


def test_add_group1():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group1", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group2_wired_tg():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group2", "--sw", "--wired-tg", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group3_wlan_tg():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group3", "--ap", "--wlan-tg", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group4_aos10_gw_wlan():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group4", "--ap", "--gw", "--aos10", "--gw-role", "wlan", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]

def test_add_guest():
    result = runner.invoke(app, ["-d", "add", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--email", test_data["portal"]["guest"]["email"], "--company", "central-api-cli test company", "--yes"])
    assert True in [
        result.exit_code == 0 and "200" in result.stdout,
    ]
