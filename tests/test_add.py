import asyncio

import pytest
from typer.testing import CliRunner

from centralcli import cache, config
from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


@pytest.fixture(scope="function")
def ensure_cache_group1():
    if config.dev.mock_tests:
        batch_del_group1 = [
            {
                "name": "cencli_test_group1",
                "allowed_types": ["ap", "gw", "cx", "sw"],
                "gw_role": "branch",
                "aos10": False,
                "microbranch": False,
                "wlan_tg": False,
                "wired_tg": False,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": None
            }
        ]
        missing = [group["name"] for group in batch_del_group1 if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=batch_del_group1))
    yield


def test_add_group1():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group1", "-Y"])
    capture_logs(result, "test_add_group1")
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group2_wired_tg():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group2", "--sw", "--wired-tg", "-Y"])
    assert any(
        [
            result.exit_code == 0 and "Created" in result.stdout,
            result.exit_code == 1 and "already exists" in result.stdout
        ]
    )


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


def test_add_site_by_address():
    result = runner.invoke(app, ["-d", "add", "site",  "cencli_test_site3", "123 Main St.", "Gallatin", "TN", "37066", "US", "-Y"])
    capture_logs(result, "test_add_site_by_address")
    assert True in [
        result.exit_code == 0 and "37066" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_site_by_geo():
    result = runner.invoke(app, ["-d", "add", "site",  "cencli_test_site4", "--lat", "36.378545", "--lon", "-86.360740", "-Y"])
    assert True in [
        result.exit_code == 0 and "36.37" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_label():
    result = runner.invoke(app, ["-d", "add", "label",  "cencli_test_label1", "-Y"])
    assert True in [
        result.exit_code == 0 and "test_label" in result.stdout,
        result.exit_code == 1 and "already exist" in result.stdout
    ]


def test_add_label_multi():
    result = runner.invoke(app, ["-d", "add", "label",  "cencli_test_label2", "cencli_test_label3", "-Y"])
    assert True in [
        result.exit_code == 0 and "test_label" in result.stdout,
        result.exit_code == 1 and "already exist" in result.stdout
    ]


def test_add_guest():
    result = runner.invoke(app, ["-d", "add", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--email", test_data["portal"]["guest"]["email"], "--company", "central-api-cli test company", "--yes"])
    assert True in [
        result.exit_code == 0 and "200" in result.stdout,
    ]
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout


def test_add_device():
    result = runner.invoke(app, ["-d", "add", "device",  "serial", "CN63HH906Z", "mac", "F0:5C:19:CE:7A:86", "group", "atm-local", "-s", "foundation-ap", "--yes"])
    assert True in [
        result.exit_code == 0 and "200" in result.stdout,
    ]
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout


def test_add_wlan(ensure_cache_group1):
    result = runner.invoke(app, ["-d", "add", "wlan",  "cencli_test_group1", "delme", "vlan", "110", "psk", "C3ncliR0cks!", "--hidden", "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout
