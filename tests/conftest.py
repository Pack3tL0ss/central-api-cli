import asyncio
import shutil
from pathlib import Path

import pendulum
import pytest
from typer.testing import CliRunner

from centralcli import cache, common, config, log
from centralcli.cli import app

from . import test_data
from ._mock_request import test_responses
from ._test_data import test_device_file, test_group_file, test_site_file

runner = CliRunner()

cache_bak_file = config.cache_file.parent / f"{config.cache_file.name}.pytest.bak"


def stash_cache_file():  # pragma: no cover
    if config.cache_file.exists():
        log.info(f"Real Cache {config.cache_file}, backed up to {cache_bak_file} as mock test run is starting (which will add items that don't actually exist to the cache)")
        shutil.copy(config.cache_file, cache_bak_file)

    pytest_cache = config.cache_file.parent / f"{config.cache_file.name}.pytest"
    if pytest_cache.exists():
        log.info(f"Real cache replaced with existing pytest Cache {pytest_cache} to prepopulate items for mock run.")
        shutil.copy(pytest_cache, config.cache_file)



def restore_cache_file():  # pragma: no cover
    if cache_bak_file.exists():
        log.info(f"Stashing cache from mock test run for later use {cache_bak_file.name.removesuffix('.bak')}")
        config.cache_file.rename(cache_bak_file.parent / cache_bak_file.name.removesuffix('.bak'))  # we keep the pytest cache as running individual tests on subsequent runs would not work otherwise

        log.info(f"Restoring real cache from {cache_bak_file} after mock test run")
        cache_bak_file.rename(config.cache_file.parent / config.cache_file.name)


        return config.cache_file.exists()

def _cleanup_mock_cache():
    dbs = [cache.GroupDB, cache.SiteDB, cache.LabelDB, cache.CertDB]
    doc_ids = [[g.doc_id for g in db.all() if g["name"].startswith("cencli_test")] for db in dbs]
    assert [asyncio.run(cache.update_db(db, doc_ids=ids)) for db, ids in zip(dbs, doc_ids)]
    return


def _cleanup_test_groups():  # pragma: no cover
    del_groups = [g for g in cache.groups_by_name if g.startswith("cencli_test_")]
    if del_groups:
        result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


def _cleanup_test_sites():  # pragma: no cover
    del_sites = [s for s in cache.sites_by_name if s.startswith("cencli_test_")]
    if del_sites:
        result = runner.invoke(app, ["delete", "site", *del_sites, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


def _cleanup_test_labels():  # pragma: no cover
    del_labels = [label for label in cache.labels_by_name if label.startswith("cencli_test_")]
    if del_labels:
        result = runner.invoke(app, ["delete", "label", *del_labels, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session):
    if "--collect-only" not in session.config.invocation_params.args and config.dev.mock_tests and session.testscollected > 120:
        unused = "\n".join(test_responses.unused)
        unused_log_file = Path(config.log_dir / "pytest-unused-mocks.log")
        log.info(f"{len(test_responses.unused)} mock responses were unused.  See {unused_log_file} for details.")
        now = pendulum.now()
        ts = " ".join(now.to_day_datetime_string().split(", ")[1:])
        unused_log_file.write_text(
            f"The following {len(test_responses.unused)} mock responses were not used during this test run {ts}\n{unused}\n"
        )


def cleanup_test_items():  # pragma: no cover
    try:
        _cleanup_test_groups()
        _cleanup_test_labels()
        _cleanup_test_sites()
    except AssertionError as e:
        log.exception(f"An error ({repr(e)}) may have occured during test run cleanup.  You may need to verify test objects have been deleted from central.", exc_info=True)


def do_nothing():
    ...


def cleanup_import_files():
    test_files = [test_group_file, test_site_file, test_device_file]
    for file in test_files:
        if file.exists():
            file.unlink()


def setup():
    if config.dev.mock_tests:
        yield do_nothing()
        # yield stash_cache_file()
    else:  # pragma: no cover
        yield do_nothing()


def teardown():
    cleanup_import_files()
    if config.dev.mock_tests:
        return _cleanup_mock_cache()
        # return restore_cache_file()
    else:
        return cleanup_test_items()  # pragma: no cover

# -- FIXTURES --

@pytest.fixture(scope='session', autouse=True)
def session_setup_teardown():
    # Will be executed before the first test
    yield from setup()

    # executed after test is run
    teardown()


@pytest.fixture(scope='function', autouse=True)
def clear_lru_caches():
    cache.get_inv_identifier.cache_clear()
    cache.get_combined_inv_dev_identifier.cache_clear()
    cache.get_name_id_identifier.cache_clear()
    for db in cache._tables:
        db.clear_cache()
    cache.responses.clear()
    yield


@pytest.fixture(scope="function")
def ensure_cache_cert():
    if config.dev.mock_tests and "cencli-test" not in cache.certs_by_name:
        asyncio.run(cache.update_db(cache.CertDB, data={"name": "cencli-test", "type": "SERVER_CERT", "md5_checksum": "781b9320972dc571d9f3055c081e8a11", "expired": False, "expiration": 2071936577}, truncate=False))
    yield

    if config.dev.mock_tests and "cencli-test" in cache.certs_by_name:
        doc_id = cache.certs_by_name["cencli-test"].doc_id
        asyncio.run(cache.update_db(cache.CertDB, doc_ids=[doc_id]))


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


@pytest.fixture(scope="function")
def ensure_cache_group2():
    if config.dev.mock_tests:
        batch_del_group1 = [
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
            }
        ]
        missing = [group["name"] for group in batch_del_group1 if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=batch_del_group1))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group3():
    if config.dev.mock_tests:
        batch_del_group1 = [
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
        missing = [group["name"] for group in batch_del_group1 if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=batch_del_group1))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group4():
    if config.dev.mock_tests:
        batch_del_group1 = [
            {
                "name": "cencli_test_group4",
                "allowed_types": ["ap", "gw"],
                "gw_role": "wlan",
                "aos10": True,
                "microbranch": False,
                "wlan_tg": False,
                "wired_tg": False,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": False
            }
        ]
        missing = [group["name"] for group in batch_del_group1 if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=batch_del_group1))
    yield


@pytest.fixture(scope="function")
def ensure_inv_cache_test_ap():
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
def ensure_dev_cache_test_ap():
    if config.dev.mock_tests:
        test_ap = {
                "name": "cencli-test-ap",
                "status": "Down",
                "type": "ap",
                "model": "205",
                "ip": "10.0.31.99",
                "mac": test_data["test_add_do_del_ap"]["mac"],
                "serial": test_data["test_add_do_del_ap"]["serial"],
                "group": "cencli_test_group1",
                "site": "cencli_test_site1",
                "version": "10.7.2.0_92876",
                "swack_id": test_data["test_add_do_del_ap"]["serial"],
                "switch_role": None
        }
        if test_data["test_add_do_del_ap"]["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_ap, truncate=False))
    yield

    if test_data["test_add_do_del_ap"]["serial"] in cache.devices_by_serial:
        serial = test_data["test_add_do_del_ap"]["serial"]
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[serial].doc_id]))
    return


def _ensure_cache_site1():
    if config.dev.mock_tests:
        sites = [
            {
                "id": 1109,
                "name": "cencli_test_site1",
                "address": "123 test ave",
                "city": "Nashville",
                "state":  "Tennessee",
                "zip": "",
                "country": "United States",
                "lat": "36.1626638",
                "lon": "-86.7816016",
                "devices": 0,
            },
        ]
        missing = [site["name"] for site in sites if site["name"] not in cache.sites_by_name]
        if missing:
            assert asyncio.run(cache.update_site_db(data=sites))


@pytest.fixture(scope="function")
def ensure_cache_site1():
    _ensure_cache_site1()
    yield


def _ensure_cache_site2():
    if config.dev.mock_tests:
        sites = [
            {
                "id": 1110,
                "name": "cencli_test_site2",
                "address": "",
                "city": "",
                "state": "",
                "zip": "",
                "country": "",
                "lat": "40.251300",
                "lon": "-86.592030",
                "devices": 0
            }
        ]
        missing = [site["name"] for site in sites if site["name"] not in cache.sites_by_name]
        if missing:
            assert asyncio.run(cache.update_site_db(data=sites))



@pytest.fixture(scope="function")
def ensure_cache_site2():
    _ensure_cache_site2()
    yield

@pytest.fixture(scope="function")
def ensure_cache_site3():
    if config.dev.mock_tests:
        sites = [
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
        missing = [site["id"] for site in sites if site["id"] not in cache.sites_by_id]
        if missing:
            assert asyncio.run(cache.update_site_db(data=sites))
    yield


@pytest.fixture(scope="function")
def ensure_cache_site4():
    if config.dev.mock_tests:
        sites = [
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
        missing = [site["id"] for site in sites if site["id"] not in cache.sites_by_id]
        if missing:
            assert asyncio.run(cache.update_site_db(data=sites))
    yield


@pytest.fixture(scope="function")
def ensure_cache_label1():
    if config.dev.mock_tests and "cencli_test_label1" not in cache.labels_by_name:
        asyncio.run(cache.update_db(cache.LabelDB, data={"id": 1106, "name": "cencli_test_label1", "devices": 0}, truncate=False))
    yield

    if config.dev.mock_tests and "cencli_test_label1" in cache.labels_by_name:
        doc_id = cache.labels_by_name["cencli_test_label1"].doc_id
        asyncio.run(cache.update_db(cache.LabelDB, doc_ids=[doc_id]))


@pytest.fixture(scope="function")
def ensure_cache_label2():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id":1107,"name":"cencli_test_label2","devices":0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


@pytest.fixture(scope="function")
def ensure_cache_label3():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id":1108,"name":"cencli_test_label3","devices":0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group_cloned():
    if config.dev.mock_tests:
        groups = [
            {
                "name": "cencli_test_cloned",
                "allowed_types": ["ap"],
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
        missing = [group["name"] for group in groups if group["name"] not in cache.groups_by_name]
        if missing:
            assert asyncio.run(cache.update_group_db(data=groups))
    yield


@pytest.fixture(scope="function")
def ensure_inv_cache_add_do_del_ap():
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
def ensure_cache_batch_devices():
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
        _ensure_cache_site1()
        _ensure_cache_site2()
    yield


@pytest.fixture(scope="function")
def ensure_cache_guest1():
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
def ensure_cache_template():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli_test_template",
            "device_type": "sw",
            "group": "cencli_test_group2",
            "model": "ALL",
            "version": "ALL",
            "template_hash": "0976d6fef0f24e2d7cd38886f608757a"
        }
        if f'{cache_data["name"]}_{cache_data["group"]}' not in cache.templates_by_name_group:
            assert asyncio.run(cache.update_db(cache.TemplateDB, data=cache_data))
    yield


@pytest.fixture(scope="function")
def ensure_cache_template_by_name():
    if config.dev.mock_tests:
        cache_data = {
            "name": "2930F-8",
            "device_type": "sw",
            "group": "Branch1",
            "model": "JL258A",
            "version": "ALL",
            "template_hash": "0ba83fe0cc6e363891d80b8cba8223a8"
        }
        if f'{cache_data["name"]}_{cache_data["group"]}' not in cache.templates_by_name_group:
            assert asyncio.run(cache.update_db(cache.TemplateDB, data=cache_data))
    yield