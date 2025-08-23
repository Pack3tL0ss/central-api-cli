import asyncio

import pytest
from typer.testing import CliRunner

from centralcli import cache
from centralcli.cache import api
from centralcli.cli import app
from centralcli.exceptions import MissingRequiredArgumentException

from . import capture_logs, config, test_data

runner = CliRunner()


@pytest.fixture(scope="function")
def ensure_cache_test_ap():
    if config.dev.mock_tests:
        devices = [
            {
                "id": "e3e8cc40-5545-55f3-abcb-6551acf5bdcc",
                "serial": test_data["test_add_do_del_ap"]["serial"],
                "mac": test_data["test_add_do_del_ap"]["mac"],
                "type": "ap",
                "model": "IAP-205-US",
                "sku": "JL185A",
                "services": "foundation-ap",
                "subscription_key": "ADURDXCTOYTUXKJE",
                "subscription_expires": 1788715367,
                "assigned": True,
                "archived": False
            }
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.inventory_by_serial]
        if missing:
            assert asyncio.run(cache.update_inv_db(data=devices))
    yield


@pytest.fixture(scope="function")
def ensure_cache_test_ap_devdb():
    if config.dev.mock_tests:
        devices = [
            {
                "name": "cencli-test-ap",
                "status": "Down",
                "type": "ap",
                "model": "205",
                "ip": "10.0.31.99",
                "mac": test_data["test_add_do_del_ap"]["mac"],
                "serial": test_data["test_add_do_del_ap"]["serial"],
                "group": "cencli_test_group3",
                "site": "cencli_test_site1",
                "version": "10.7.2.0_92876",
                "swack_id": test_data["test_add_do_del_ap"]["serial"],
                "switch_role": None
            }
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.devices_by_serial]
        if missing:
            assert asyncio.run(cache.update_dev_db(data=devices))
    yield


@pytest.fixture(scope="function")
def ensure_cache_site1():
    if config.dev.mock_tests:
        batch_del_sites = [
            {"address":"123 test ave","city":"Nashville","country":"United States","latitude":"36.1626638","longitude":"-86.7816016","site_id":1109,"site_name":"cencli_test_site1","state":"Tennessee","zipcode":""},
        ]
        missing = [site["site_name"] for site in batch_del_sites if site["site_name"] not in cache.sites_by_name]
        if missing:
            assert asyncio.run(cache.update_site_db(data=batch_del_sites))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group3():
    if config.dev.mock_tests:
        groups = [
            {
                "name": "cencli_test_group3",
                "allowed_types": ["ap"],
                "gw_role": "branch",
                "aos10": False,
                "microbranch": False,
                "wlan_tg": True,
                "wired_tg": False,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": None
            }
        ]
        missing = [group["name"] for group in groups if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=groups))
    yield


def test_archive(ensure_cache_test_ap):
    result = runner.invoke(app, ["archive", test_data["test_add_do_del_ap"]["mac"], "-y"])
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_unarchive(ensure_cache_test_ap):
    result = runner.invoke(app, ["unarchive", test_data["test_add_do_del_ap"]["serial"]])
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_move_pre_provision(ensure_cache_group3, ensure_cache_test_ap):
    result = runner.invoke(app, ["move", test_data["test_add_do_del_ap"]["serial"], "group", "cencli_test_group3", "-y"])
    assert result.exit_code == 0
    assert "201" in result.stdout


def test_remove_test_ap_from_site(ensure_cache_test_ap, ensure_cache_test_ap_devdb, ensure_cache_site1):
    result = runner.invoke(app, ["remove", test_data["test_add_do_del_ap"]["serial"], "site", "cencli_test_group3", "-y"])
    assert result.exit_code == 0
    assert "201" in result.stdout


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
    result = runner.invoke(app, ["kick",  "all", test_data["ap"]["serial"], "--ssid", test_data["kick_ssid"], "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all_missing_argument():
    try:
        api.session.request(api.device_management.kick_users, test_data["ap"]["serial"])
    except MissingRequiredArgumentException:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_kick_all_missing_argument should have raised a MissingRequiredArgumentException but did not")


def test_save():
    result = runner.invoke(app, ["save",  test_data["switch"]["serial"]])
    capture_logs(result, "test_reboot_save")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_sync_gw():
    result = runner.invoke(app, ["sync",  test_data["gateway"]["name"]])
    capture_logs(result, "test_reboot_save")
    assert result.exit_code == 0
    assert "200" in result.stdout


if config.dev.mock_tests:
    def test_reboot_swarm():
        result = runner.invoke(app, ["reboot",  test_data["aos8_ap"]["name"], "-sy"])
        capture_logs(result, "test_reboot_swarm")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_enable_auto_sub():
        result = runner.invoke(app, ["enable",  "auto-sub", "advanced-ap", "-y"])
        capture_logs(result, "test_enable_auto_sub")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_disable_auto_sub():
        result = runner.invoke(app, ["disable",  "auto-sub", "advanced-ap", "-y"])
        capture_logs(result, "test_disable_auto_sub")
        assert result.exit_code == 0
        assert "200" in result.stdout
