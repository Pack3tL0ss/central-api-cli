import asyncio

import pytest
from typer.testing import CliRunner

from centralcli import cache, common, config
from centralcli.cli import app

from . import capture_logs
from ._test_data import test_data, test_device_file, test_group_file, test_site_file

runner = CliRunner()


@pytest.fixture(scope="function")
def ensure_cache_del_device():
    if config.dev.mock_tests:
        devices = [
            {
                "id": "e3e8cc40-5545-55f3-abcb-6551acf5bdcc",
                "serial": "CN63HH906Z",
                "mac": "F0:5C:19:CE:7A:86",
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
def ensure_cache_batch_del_devices():
    if config.dev.mock_tests:
        devices = common._get_import_file(test_device_file, import_type="devices")
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.inventory_by_serial]
        if missing:
            resp = common.batch_add_devices(data=devices, yes=True)
            assert any([r.ok for r in resp])
    yield


@pytest.fixture(scope="function")
def ensure_cache_batch_del_groups():
    if config.dev.mock_tests:
        groups = common._get_import_file(test_group_file, import_type="groups")
        missing = [group["name"] for group in groups if group["name"] not in cache.groups_by_name]
        if missing:
            resp = common.batch_add_groups(data=groups, yes=True)
            assert any([r.ok for r in resp])
    yield


@pytest.fixture(scope="function")
def ensure_cache_batch_del_sites():
    if config.dev.mock_tests:
        batch_del_sites = [
            {"address":"123 test ave","city":"Nashville","country":"United States","latitude":"36.1626638","longitude":"-86.7816016","site_id":1109,"site_name":"cencli_test_site1","state":"Tennessee","zipcode":""},
            {"address":"","city":"","country":"","latitude":"40.251300","longitude":"-86.592030","site_id":1110,"site_name":"cencli_test_site2","state":"","zipcode":""}
        ]
        missing = [site["site_name"] for site in batch_del_sites if site["site_name"] not in cache.sites_by_name]
        if missing:
            assert asyncio.run(cache.update_site_db(data=batch_del_sites))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_label():
    if config.dev.mock_tests:
        batch_del_labels = [{"id":1106,"name":"cencli_test_label1","devices":0}]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_label_multi():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id":1107,"name":"cencli_test_label2","devices":0},
            {"id":1108,"name":"cencli_test_label3","devices":0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_guest():
    if config.dev.mock_tests:
        batch_del_guests = [
            {
            "portal_id": "e5538808-0e05-4ecd-986f-4bdce8bf52a4",
            "name": "superlongemail@kabrew.com",
            "id": "7c9eb0df-b211-4225-94a6-437df0dfca59",
            "email": "superlongemail@kabrew.com",
            "phone": "+6155551212",
            "company": "central-api-cli test company",
            "enabled": True,
            "status": "Active",
            "created": 1755552751,
            "expires": 1755811951
            }
        ]
        missing = [guest["id"] for guest in batch_del_guests if guest["id"] not in cache.guests_by_id]
        if missing:
            assert asyncio.run(cache.update_guest_db(data=batch_del_guests))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_group():
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


@pytest.fixture(scope="function")
def ensure_cache_del_group_multi():
    if config.dev.mock_tests:
        del_groups_multi = [
            {
                "name": "cencli_test_group2",
                "allowed_types": ["sw"],
                "gw_role": "branch",
                "aos10": False,
                "microbranch": False,
                "wlan_tg": False,
                "wired_tg": True,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": None
            },
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
        missing = [group["name"] for group in del_groups_multi if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=del_groups_multi))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_site_by_address():
    if config.dev.mock_tests:
        del_sites = [
            {
                "id": 1104,
                "name": "cencli_test_site3",
                "address": "123 Main St.",
                "city": "Gallatin",
                "state": "Tennessee",
                "zip": "37066",
                "country": "United States",
                "lat": "36.3882547",
                "lon": "-86.4453126",
                "devices": 0,
            },
        ]
        missing = [site["id"] for site in del_sites if site["id"] not in cache.sites_by_id]
        if missing:
            assert asyncio.run(cache.update_site_db(data=del_sites))
    yield


@pytest.fixture(scope="function")
def ensure_cache_del_site4():
    if config.dev.mock_tests:
        del_sites = [
            {
                "id": 1105,
                "name": "cencli_test_site4",
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
                "country": "",
                "lat": "36.378545",
                "lon": "-86.360740",
                "devices": 0,
            }
        ]
        missing = [site["id"] for site in del_sites if site["id"] not in cache.sites_by_id]
        if missing:
            assert asyncio.run(cache.update_site_db(data=del_sites))
    yield



def test_del_wlan(ensure_cache_del_group):
    result = runner.invoke(app, ["-d", "delete", "wlan",  "cencli_test_group1",  "delme", "--yes"])
    capture_logs(result, "test_del_wlan")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_device(ensure_cache_del_device):
    result = runner.invoke(app, ["delete",  "device", "CN63HH906Z", "-Y"])
    capture_logs(result, "test_del_device")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_batch_del_devices(ensure_cache_batch_del_devices):
    result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_device_file)}', "-Y"])
    capture_logs(result, "test_batch_del_devices")
    assert result.exit_code == 0
    assert "subscriptions successfully removed" in result.stdout.lower()
    assert "200" in result.stdout


def test_batch_del_groups(ensure_cache_batch_del_groups):
    cache.responses.group = None  # Necessary as pytest treats all this as one session, so it thinks cache has been refreshed already
    result = runner.invoke(app, ["batch", "delete",  "groups", str(test_group_file), "-Y"])
    capture_logs(result, "test_batch_del_groups")
    assert result.exit_code == 0
    assert "success" in result.stdout.lower()
    assert result.stdout.lower().count("success") == len(test_data["batch"]["groups_by_name"])


def test_batch_del_sites(ensure_cache_batch_del_sites):
    result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file), "-Y"])
    capture_logs(result, "test_batch_del_sites")
    assert result.exit_code == 0
    assert "success" in result.stdout
    assert result.stdout.count("success") == len(test_data["batch"]["sites"])


def test_del_group(ensure_cache_del_group):
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group1",
        "-Y"
        ])
    capture_logs(result, "test_del_group")
    assert result.exit_code == 0
    assert "Success" in result.stdout


def test_del_group_multi(ensure_cache_del_group_multi):
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group3",
        "cencli_test_group4",
        "-Y"
        ])
    capture_logs(result, "test_del_group_multiple")
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert result.stdout.count("Success") == 2


def test_del_site_by_address(ensure_cache_del_site_by_address):
    result = runner.invoke(app, [
        "delete",
        "site",
        "123 Main St.",
        "-Y"
        ])
    capture_logs(result, "test_del_site_by_address")
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_del_site4(ensure_cache_del_site4):
    result = runner.invoke(app, [
        "delete",
        "site",
        "cencli_test_site4",
        "-Y"
        ])
    capture_logs(result, "test_del_site4")
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_del_label(ensure_cache_del_label):
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label1",
        "-Y"
        ])
    capture_logs(result, "test_del_label")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_label_multi(ensure_cache_del_label_multi):
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label2",
        "cencli_test_label3",
        "-Y"
        ])
    capture_logs(result, "test_del_label_multi")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_guest(ensure_cache_del_guest):
    result = runner.invoke(app, ["-d", "delete", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--yes"])
    capture_logs(result, "test_del_guest")
    assert result.exit_code == 0
    assert "200" in result.stdout
