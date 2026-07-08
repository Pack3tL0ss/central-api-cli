import asyncio
import shutil
from pathlib import Path

import pendulum
import psutil
import pytest
from rich.traceback import install
from typer.testing import CliRunner

from centralcli import cache, common, config, log
from centralcli.cli import app
from centralcli.client import Session
from centralcli.models.sql import MPSK, Client, Group, Portal, Site, Label, Cert, Subscription, FloorPlanAP
from centralcli.typedefs import PrimaryDeviceTypes
from centralcli.cache.sqlite import DBAction
from sqlalchemy import delete
from sqlalchemy.orm import Session as SQLSession

from . import mock_sleep, test_data
from ._mock_request import test_responses
from ._test_data import TEST_FILE_DIR, test_group_file

runner = CliRunner()

cache_bak_file = config.cache.file.parent / f"{config.cache.file.name}.pytest.bak"


BATCH_DEVICES = [
    {
        "id": "19478ff1-4168-5c61-895c-bc7c11aec0bd",
        "serial": "CNKDKSM0YH",
        "mac": "20:4C:03:BA:20:6C",
        "type": "ap",
        "model": "AP-505H-US",
        "sku": "R3V48A",
        "services": "advanced-ap",
        "subscription_key": "ENCYHFWQLJNQCWDU",
        "subscription_expires": 1788715367,
        "assigned": True,
        "archived": False
    },
    {
        "id": "6702ffe6-0770-518a-9e42-188d715a9c7b",
        "serial": "CNFHJ0TPF7",
        "mac": "38:17:c3:c6:e0:38",
        "type": "ap",
        "model": "315",
        "sku": "JW813A",
        "subscription": "advanced-ap",
        "subscription_key": "ENCYHFWQLJNQCWDU",
        "subscription_expires": 1924905600,
        "assigned": True,
        "archived": False
    },
    {
        "id": "f26c4528-4260-5e38-8167-2f4a08a214a4",
        "serial": "CNKJKV309D",
        "mac": "D0:D3:E0:CD:08:24",
        "type": "ap",
        "model": "AP-575-US",
        "sku": "R4H18A",
        "services": "advanced-ap",
        "subscription_key": "ENCYHFWQLJNQCWDU",
        "subscription_expires": 1788715367,
        "assigned": True,
        "archived": False
    },
    {
        "id": "347bd5b1-e53e-50e9-8fac-1e80bba794a1",
        "serial": "CNHPKLB01P",
        "mac": "20:4C:03:81:E7:B2",
        "type": "gw",
        "model": "9004-US",
        "sku": "R1B20A",
        "services": "advance-70xx",
        "subscription_key": "ARI76TMSFHXNJBJH",
        "subscription_expires": 1860052515,
        "assigned": True,
        "archived": False
    },
    {
        "id": "7750bcaa-aef8-11f0-986e-00155df42dd5",
        "serial": "CN29FP403H",
        "mac": "80:C1:6E:CD:32:40",
        "type": "sw",
        "model": "2530-12G",
        "sku": "J9773A",
        "services": "foundation-switch-6100",
        "subscription_key": "AZFG8CVMXQB23NNQ",
        "subscription_expires": 1924799400,
        "assigned": True,
        "archived": False
    },
    {
        "id": "6b538f45-f0bb-515d-87fc-0816495c0d44",
        "serial": "SG90KN00N5",
        "mac": "88:3a:30:9a:cc:40",
        "type": "cx",
        "model": "'6300'",
        "sku": "JL661A",
        "services": "advanced-switch-6300",
        "subscription_key": "E4F587FF6F6F848289",
        "subscription_expires": 1924799400,
        "assigned": True,
        "archived": False
    }
]


def pytest_configure(config):
    """
    Installs the rich traceback handler for all uncaught exceptions during pytest runs.
    """
    install(show_locals=True, suppress=[
        "pytester",  # Suppress internal pytest frames
        "pytest",   # Suppress pytest frames
        # Add other modules to suppress if needed, e.g., "my_library"
    ])


def stash_cache_file():  # pragma: no cover
    if config.cache.file.exists():
        log.info(f"Real Cache {config.cache.file}, backed up to {cache_bak_file} as mock test run is starting (which will add items that don't actually exist to the cache)")
        shutil.copy(config.cache.file, cache_bak_file)

    pytest_cache = config.cache.file.parent / f"{config.cache.file.name}.pytest"
    if pytest_cache.exists():
        log.info(f"Real cache replaced with existing pytest Cache {pytest_cache} to prepopulate items for mock run.")
        shutil.copy(pytest_cache, config.cache.file)


def restore_cache_file():  # pragma: no cover
    if cache_bak_file.exists():
        log.info(f"Stashing cache from mock test run for later use {cache_bak_file.name.removesuffix('.bak')}")
        config.cache.file.rename(cache_bak_file.parent / cache_bak_file.name.removesuffix('.bak'))  # we keep the pytest cache as running individual tests on subsequent runs would not work otherwise

        log.info(f"Restoring real cache from {cache_bak_file} after mock test run")
        cache_bak_file.rename(config.cache.file.parent / config.cache.file.name)

        return config.cache.file.exists()


def _cleanup_mock_cache():
    dbs = [Group, Site, Label, Cert]
    db_matches = [[db_model.to_dict() for db_model in cache._get_all(db) if db_model.name.startswith("cencli_test")] for db in dbs]
    if sum(map(len, db_matches)) > 0:  # pragma: no cover
        for db, data in zip(dbs, db_matches):
            asyncio.run(cache._update_db(db, data=data, action=DBAction.DELETE, column="name"))
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
    if "--collect-only" not in session.config.invocation_params.args and config.dev.mock_tests:  # pragma: no cover
        now = pendulum.now()
        ts = " ".join(now.to_day_datetime_string().split(", ")[1:])

        if test_responses.unused and session.testscollected > 900:
            # Log unused mocks.  This is currently disable (always returns empty list)
            unused = "\n".join(test_responses.unused)
            unused_log_file = Path(config.log_dir / "pytest-unused-mocks.log")
            log.info(f"{len(test_responses.unused)} mock responses were unused.  See {unused_log_file} for details.")
            unused_log_file.write_text(
                f"The following {len(test_responses.unused)} mock responses were not used during this test run {ts}\n{unused}\n"
            )

        if not test_responses.missing_mocks:
            return

        # Log missing mocks
        missing_mocks_log_file = Path(config.log_dir / "pytest-missing-mocks.log")
        missing = "\n".join(test_responses.missing_mocks)
        log.warning(f"{len(test_responses.missing_mocks)} mock responses were missing.  See {missing_mocks_log_file} for details.")
        missing_mocks_log_file.write_text(
            f"The following {len(test_responses.missing)} mock responses were not used during this test run {ts}\n{missing}\n"
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
    for file in TEST_FILE_DIR.iterdir():
        if file.exists():
            if file.is_dir():
                _ = [f.unlink() for f in file.iterdir()]
                file.rmdir()
            else:
                file.unlink()
        else:  # pragma: no cover
            ...

    try:
        TEST_FILE_DIR.rmdir()  # must be empty
    except OSError as e:  # pragma: no cover
        log.exception(f"{repr(e)} while attempting to remove test_file directory ({TEST_FILE_DIR}). (conftest.cleanup_import_files)", exc_info=True)


def setup():
    if config.dev.mock_tests:
        yield do_nothing()
    else:  # pragma: no cover
        yield do_nothing()


def teardown():
    cleanup_import_files()
    if config.dev.mock_tests:
        return _cleanup_mock_cache()
    else:
        return cleanup_test_items()  # pragma: no cover

# -- FIXTURES --


@pytest.fixture(scope='session', autouse=True)
def session_setup_teardown():
    # Will be executed before the first test
    yield from setup()

    # executed after test is run
    return teardown()


@pytest.fixture(scope='function', autouse=True)
def clear_lru_caches():
    cache.get_inv_identifier.cache_clear()
    cache.get_combined_inv_dev_identifier.cache_clear()
    cache.get_name_id_identifier.cache_clear()
    # for db in cache._tables:
    #     db.clear_cache()
    cache.responses.clear()
    Session.requests_clear()
    yield


@pytest.fixture(scope="function")
def ensure_cache_cert():
    cache_data = {"name": "cencli-test", "type": "SERVER_CERT", "md5_checksum": "781b9320972dc571d9f3055c081e8a11", "expired": False, "expiration": 2071936577}
    if config.dev.mock_tests and "cencli-test" not in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test" in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.DELETE, column="name"))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_cert_same_as_existing():
    cache_data = {"name": "cencli-test-existing-cert", "type": "SERVER_CERT", "md5_checksum": "43e0c762fc2bc47d8c6847a4b7b27af4", "expired": False, "expiration": 2071936577}
    if config.dev.mock_tests and "cencli-test-existing-cert" not in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test-existing-cert" in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.DELETE, column="name"))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_cert_expired():
    cache_data = {"name": "cencli-test-expired-cert", "type": "SERVER_CERT", "md5_checksum": "6bf2b4afbbe379f44589e4be994fa4c1", "expired": True, "expiration": 1736493627}
    if config.dev.mock_tests and "cencli-test-expired-cert" not in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test-expired-cert" in cache.certs_by_name:
        asyncio.run(cache._update_db(Cert, data=cache_data, action=DBAction.DELETE, column="name"))
    else:  # pragma: no cover
        ...


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
        cache_data = {
                "name": "cencli_test_group2",
                "allowed_types": ["sw", "ap"],
                "gw_role": "branch",
                "aos10": False,
                "microbranch": False,
                "wlan_tg": True,
                "wired_tg": True,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": None
        }
        if cache_data["name"] not in cache.groups_by_name:
            assert asyncio.run(cache.update_group_db(data=cache_data))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group3():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli_test_group3",
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
        if cache_data["name"] not in cache.groups_by_name:
            assert asyncio.run(cache.update_group_db(data=cache_data))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group4(request: pytest.FixtureRequest):
    gw_only = False if not hasattr(request, "param") else request.param
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli_test_group4",
            "allowed_types": ["ap", "gw"] if not gw_only else ["gw"],
            "gw_role": "wlan",
            "aos10": True,
            "microbranch": False,
            "wlan_tg": False,
            "wired_tg": False,
            "monitor_only_sw": False,
            "monitor_only_cx": False,
            "cnx": True
        }
        asyncio.run(cache.update_group_db(data=cache_data, action=DBAction.UPSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_group4_cx_only():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli_test_group4",
            "allowed_types": ["cx"],
            "gw_role": None,
            "aos10": None,
            "microbranch": None,
            "wlan_tg": False,
            "wired_tg": False,
            "monitor_only_sw": False,
            "monitor_only_cx": False,
            "cnx": False
        }
        asyncio.run(cache.update_group_db(data=cache_data, action=DBAction.UPSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_mpsk_network():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli-test-mpsknet",
            "id": "1ABCDE23FGH45I6K"
        }
        asyncio.run(cache.update_mpsk_net_db(data=cache_data, action=DBAction.UPSERT))
    yield

    if config.dev.mock_tests:
        asyncio.run(cache.update_mpsk_net_db(data=cache_data, action=DBAction.DELETE))


@pytest.fixture(scope="function")
def ensure_hook_proxy_started():  # pragma: no cover
    if config.dev.mock_tests and not [p.pid for p in psutil.process_iter(attrs=["name", "cmdline"]) if p.info["cmdline"] and True in ["webhooks" in x and "proxy" in x for x in p.info["cmdline"][1:]]]:
        with mock_sleep:
            result = runner.invoke(app, ["start", "hook-proxy", "-y"])
        assert result.exit_code == 0
        assert "Started" in result.stdout

    yield


@pytest.fixture(scope="function")
def ensure_no_cache():
    cache_file_bak = config.cache.file.parent / f"{config.cache.file.name}.bak"
    cache.engine.dispose()
    shutil.move(config.cache.file, cache_file_bak)
    config.cache.ok = False
    cache.create_engine()
    yield

    shutil.move(cache_file_bak, config.cache.file)
    return


@pytest.fixture(scope="function")
def ensure_inv_cache_batch_devices():
    if config.dev.mock_tests:
        devices = BATCH_DEVICES
        cache_devs = {dev["serial"]: cache.inventory_by_serial.get(dev["serial"], {}) for dev in devices}
        if not cache_devs == devices:
            assert asyncio.run(cache.update_inv_db(data=devices))
    yield


@pytest.fixture(scope="function")
def ensure_no_inv_dev_cache_batch_devices():
    if config.dev.mock_tests:
        devices = BATCH_DEVICES
        cache_inv_devs_by_serial = {
            dev["serial"]: cache.inventory_by_serial[dev["serial"]] for dev in devices if dev["serial"] in cache.inventory_by_serial
        }
        if cache_inv_devs_by_serial:  # pragma: no cover
            assert asyncio.run(cache.update_inv_db(data=[{"serial": s} for s in cache_inv_devs_by_serial], action=DBAction.DELETE))
        cache_mon_devs_by_serial = {
            dev["serial"]: cache.devices_by_serial[dev["serial"]] for dev in devices if dev["serial"] in cache.devices_by_serial
        }
        if cache_mon_devs_by_serial:  # pragma: no cover
            assert asyncio.run(cache.update_dev_db(data=[{"serial": s} for s in cache_mon_devs_by_serial], action=DBAction.DELETE))
    yield


@pytest.fixture(scope="function")
def ensure_inv_cache_batch_sub_devices():
    if config.dev.mock_tests:
        devices = [
            {
                "id": "7750bcaa-aef8-11f0-986e-00155df42dd5",
                "serial": "CN29FP403H",
                "mac": "80:C1:6E:CD:32:40",
                "type": "sw",
                "model": "2530-12G",
                "sku": "J9773A",
                "services": "foundation-switch-6100",
                "subscription_key": "AZFG8CVMXQB23NNQ",
                "subscription_expires": 1924799400,
                "assigned": True,
                "archived": False
            },
            {
                "id": "88e21965-d335-5d40-94de-29d76dbf42b9",
                "serial": "CN80FP53YW",
                "mac": "80:30:E0:60:D5:C0",
                "type": "sw",
                "model": "2530",
                "sku": "J9774A",
                "services": "foundation-switch-6100",
                "subscription_key": "AZFG8CVMXQB23NNQ",
                "subscription_expires": 1788715367,
                "assigned": True,
                "archived": False
            },
            {
                "id": "5a3c4c8a-5756-5302-a036-2f04180b0dcf",
                "serial": "CN36FP500Q",
                "mac": "80:C1:6E:CE:F2:00",
                "type": "sw",
                "model": "2530",
                "sku": "J9774A",
                "services": None,
                "subscription_key": None,
                "subscription_expires": None,
                "assigned": True,
                "archived": False
            },
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
            },
            {
                "id": "85c46b1b-695d-564b-92a8-a6d36dae4bc0",
                "serial": "CN71HKZ1CL",
                "mac": "F4:03:43:07:57:20",
                "type": "sw",
                "model": "2930F",
                "sku": "JL258A",
                "services": None,
                "subscription_key": None,
                "subscription_expires": None,
                "assigned": True,
                "archived": False
            },
            {
                "id": "6b538f45-f0bb-515d-87fc-0816495c0d44",
                "serial": "SG90KN00N5",
                "mac": "88:3a:30:9a:cc:40",
                "type": "cx",
                "model": "'6300'",
                "sku": "JL661A",
                "services": "advanced-switch-6300",
                "subscription_key": "E4F587FF6F6F848289",
                "subscription_expires": 1924799400,
                "assigned": True,
                "archived": False
            },
            {
                "id": "adf55d3d-6f97-5cf4-8990-3e72e3d2671a",
                "serial": "SG06KMY1S1",
                "mac": "64:E8:81:B8:0C:80",
                "type": "cx",
                "model": "6300",
                "sku": "JL659A",
                "services": "advanced-switch-6300",
                "subscription_key": "E4F587FF6F6F848289",
                "subscription_expires": 1924799400,
                "assigned": True,
                "archived": False
            },
        ]
        cache_devs = {dev["serial"]: cache.inventory_by_serial.get(dev["serial"], {}) for dev in devices}
        if not cache_devs == devices:
            assert asyncio.run(cache.update_inv_db(data=devices))
    yield


# @pytest.fixture(scope="function")
# def ensure_dev_cache_batch_sub_devies():  # sub test file by subscription with device name rather than serial
#     if config.dev.mock_tests:
#         test_switches = [
#             {
#                 "name": "core-6300",
#                 "status": "Up",
#                 "type": "cx",
#                 "model": "6300M 48SR5 CL6 PoE 4SFP56 Swch (JL659A)",
#                 "ip": "10.0.30.213",
#                 "serial": "SG06KMY1S1",
#                 "mac": "64:e8:81:b8:0c:80",
#                 "group": "WadeLab",
#                 "site": "WadeLab",
#                 "version": "10.17.0001",
#                 "swack_id": "b89e6557-392e-4089-87da-b59d151797ec",
#                 "switch_role": 2
#             },
#         ]
#         assert asyncio.run(cache.update_dev_db(data=test_switches))
#     yield

#     if config.dev.mock_tests:
#         asyncio.run(cache.update_dev_db(data=test_switches, action=DBAction.DELETE))


# we only want one of them to show as online
@pytest.fixture(scope="function")
def ensure_dev_cache_batch_devices():
    if config.dev.mock_tests:
        devices = [
            {
                "name": "ap.505h.206c",
                "status": "Up",
                "type": "ap",
                "model": "505H",
                "ip": "10.0.99.101",
                "mac": "20:4C:03:BA:20:6C",
                "serial": "CNKDKSM0YH",
                "group": "WadeLab",
                "site": "WadeLab",
                "version": "10.7.2.1_93286",
                "swack_id": "CNKDKSM0YH",
                "switch_role": None
            },
            {
                "name": "lower-patio.0824",
                "status": "Down",
                "type": "ap",
                "model": "575",
                "ip": "10.0.31.3",
                "serial": "CNKJKV309D",
                "mac": "D0:D3:E0:CD:08:24",
                "group": "WadeLab",
                "site": "WadeLab",
                "version": "10.7.2.1_93286",
                # "label": "cencli_test_label1",
            },  # previously commented out
            {
                "name": "mock-gw",
                "status": "Up",
                "type": "gw",
                "model": "9004-US",
                "ip": "10.99.0.101",
                "mac": "20:4C:03:81:E7:B2",
                "serial": "CNHPKLB01P",
                "group": "cencli_test_cloned",
                "site": "cencli_test_site1",
                "version": "10.7.2.1_93286",
                "swack_id": None,
                "switch_role": None
            },
            {
                "name": "cencli_test_ap2",
                "status": "Up",
                "type": "ap",
                "model": "315",
                "ip": "10.0.31.2",
                "mac": "38:17:c3:c6:e0:38",
                "serial": "CNFHJ0TPF7",
                "group": "Branch1",
                "site": "Antigua",
                "version": "10.7.2.1_93286",
            },  # above and below were not in the list prior
            {
                "name": "2530",
                "status": "Up",
                "type": "sw",
                "model": "2530-12G",
                "ip": "10.0.112.101",
                "mac": "80:C1:6E:CD:32:40",
                "serial": "CN29FP403H",
                "group": "Branch1",
                "site": "Antigua",
                "version": "16.11.0028",
            },
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.devices_by_serial]
        if missing:  # pragma: no cover
            assert asyncio.run(cache.update_dev_db(data=devices))
    yield

    if config.dev.mock_tests and missing:  # pragma: no cover
        asyncio.run(cache.update_dev_db(data=devices, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_inv_cache_test_ap():
    if config.dev.mock_tests:
        cache_data = {
                "id": "e3e8cc40-5545-55f3-abcb-6551acf5bdcc",
                "serial": test_data["test_devices"]["ap"]["serial"],
                "mac": test_data["test_devices"]["ap"]["mac"],
                "type": "ap",
                "model": "IAP-205-US",
                "sku": "JL185A",
                "services": "foundation-ap",
                "subscription_key": "ADURDXCTOYTUXKJE",
                "subscription_expires": 1788715367,
                "assigned": True,
                "archived": False
        }
        if not cache.inventory_by_serial.get(cache_data["serial"]) or not dict(cache.inventory_by_serial[cache_data["serial"]]) == cache_data:  # pragma: no cover
            assert asyncio.run(cache.update_inv_db(data=[cache_data]))
    yield


@pytest.fixture(scope="function")
def ensure_no_inv_cache_test_ap():
    if config.dev.mock_tests:
        cache_data = {
                "id": "e3e8cc40-5545-55f3-abcb-6551acf5bdcc",
                "serial": test_data["test_devices"]["ap"]["serial"],
                "mac": test_data["test_devices"]["ap"]["mac"],
                "type": "ap",
                "model": "IAP-205-US",
                "sku": "JL185A",
                "services": "foundation-ap",
                "subscription_key": "ADURDXCTOYTUXKJE",
                "subscription_expires": 1788715367,
                "assigned": True,
                "archived": False
        }
        cache_dev = cache.inventory_by_serial.get(cache_data["serial"])
        if cache_dev:
            asyncio.run(cache.update_inv_db(data=cache_data, action=DBAction.DELETE))
    yield


@pytest.fixture(scope="function")
def ensure_inv_cache_test_switch():
    if config.dev.mock_tests:
        test_switch = {
            "id": "5a3c4c8a-5756-5302-a036-2f04180b0dcf",
            "serial": test_data["test_devices"]["switch"]["serial"],
            "mac": test_data["test_devices"]["switch"]["mac"],
            "type": "sw",
            "model": "2530",
            "sku": "J9774A",
            "services": None,
            "subscription_key": None,
            "subscription_expires": None,
            "assigned": True,
            "archived": False
        }
        if test_switch["serial"] not in cache.inventory_by_serial:  # pragma: no cover
            asyncio.run(cache.update_inv_db(data=test_switch))
    yield


@pytest.fixture(scope="function")
def ensure_inv_cache_test_stack():
    if config.dev.mock_tests:
        uuids = ["3c4babfe-b69d-11f0-a17b-8b6a99632e62", "4e72b2e6-b69d-11f0-bb4f-1756d3cebf1a", "566f25d8-b69d-11f0-a91b-db8d0e83a247", "5d5c8f84-b69d-11f0-9788-ff9e03b0bd10"]
        now = pendulum.now()
        _exp = now + pendulum.duration(years=5)
        sub_exp = _exp.int_timestamp
        test_switches = [
            {
                "id": uuids[idx],
                "serial": sw["serial"],
                "mac": sw["mac"],
                "type": sw.get("type", "cx"),
                "model": f'{sw.get("model", "6300")}',
                "sku": sw.get("sku", "JL659A"),
                "services": "advanced-switch-6300",
                "subscription_key": "A5FMOCKE6E5MOCK289",
                "subscription_expires": sub_exp,
                "assigned": True,
                "archived": False
            } for idx, sw in enumerate(test_data["test_devices"]["stack"])
        ]
        assert asyncio.run(cache.update_inv_db(data=test_switches))
    yield

    if config.dev.mock_tests:
        asyncio.run(cache.update_inv_db(data=test_switches, action=DBAction.DELETE))


@pytest.fixture(scope="function")
def ensure_dev_cache_test_stack():
    if config.dev.mock_tests:
        switch_roles = [2, 3, 4, 4]
        test_switches = [
            {
                "name": f"cencli-test-stack-m{idx + 1}",
                "status": "Up",
                "type": sw.get("type", "cx"),
                "model": "6300M 48SR5 CL6 PoE 4SFP56 Swch (JL659A)",
                "ip": "10.99.99.99" if idx == 0 else None,
                "mac": sw["mac"],
                "serial": sw["serial"],
                "group": sw.get("group", "cencli_test_group1"),
                "site": sw.get("site", "cencli_test_site1"),
                "version": "10.16.1006",
                "swack_id": "53ef49a6-b6a1-11f0-ad91-6bef8bd7be86",
                "switch_role": switch_roles[idx]
            } for idx, sw in enumerate(test_data["test_devices"]["stack"])
        ]
        missing = [dev["serial"] for dev in test_switches if dev["serial"] not in cache.devices_by_serial]
        if missing:  # pragma: no cover
            assert asyncio.run(cache.update_dev_db(data=test_switches))
    yield

    remove_devs = [{"serial": ts["serial"]} for ts in test_switches]
    asyncio.run(cache.update_dev_db(data=remove_devs, action=DBAction.DELETE))


@pytest.fixture(scope="function")
def ensure_dev_cache_ap():
    if config.dev.mock_tests:
        cache_data = {
            "name": "ktcn.605h.5866",
            "status": "Up",
            "type": "ap",
            "model": "605H",
            "ip": "10.0.31.149",
            "mac": "f0:1a:a0:2a:58:66",
            "serial": "CNR4LHJ08G",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.7.2.1_93286",
            "swack_id": "CNR4LHJ08G",
            "switch_role": None
        }
        asyncio.run(cache.update_dev_db(data=cache_data, action=DBAction.UPSERT))  # pragma: no cover
        # clean_cache_data = list(cache.devices).copy()
    else:  # pragma: no cover
        ...
    yield

    # if config.dev.mock_tests and cache_data["name"] not in [ap.name for ap in cache.devices if ap.type == "ap"]:
    # else:  # pragma: no cover
    #     ...
    asyncio.run(cache.update_dev_db(data=cache_data, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_dev_cache_test_ap():
    if config.dev.mock_tests:
        test_ap = {
                "name": "cencli-test-ap",
                "status": "Down",
                "type": "ap",
                "model": "205",
                "ip": "10.0.31.99",
                "mac": test_data["test_devices"]["ap"]["mac"],
                "serial": test_data["test_devices"]["ap"]["serial"],
                "group": "cencli_test_group2",
                "site": "cencli_test_site1",
                "version": "10.7.2.0_92876",
                "swack_id": test_data["test_devices"]["ap"]["serial"],
                "switch_role": None
        }
        asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.UPSERT))
    else:  # pragma: no cover
        ...
    yield

    asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_dev_cache_no_last_rename_ap():
    if config.dev.mock_tests:
        if "CNP7KZ2422" in cache.devices_by_serial:
            asyncio.run(cache.update_dev_db(data=[{"serial": "CNP7KZ2422"}], action=DBAction.DELETE))
    else:  # pragma: no cover
        ...

    yield


@pytest.fixture(scope="function")
def ensure_dev_cache_test_flex_dual_ap():
    if config.dev.mock_tests:
        test_ap = {
            "name": "cencli-test-flex-dual-ap",
            "status": "Up",
            "type": "ap",
            "model": "605R",
            "ip": "10.0.31.103",
            "mac": "f0:1a:a0:aa:bb:cc",
            "serial": "USABC0D1EF",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.7.2.1_93286",
            "swack_id": "USABC0D1EF",
            "switch_role": None
        }
        asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.UPSERT))
    else:  # pragma: no cover
        ...

    yield

    asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_dev_cache_test_dyn_ant_ap():
    if config.dev.mock_tests:
        test_ap = {
            "name": "cencli-test-dyn-ant-ap",
            "status": "Up",
            "type": "ap",
            "model": "679",
            "ip": "10.0.31.105",
            "mac": "50:e4:e0:aa:bb:cc",
            "serial": "USABC0D1EG",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.7.2.1_93286",
            "swack_id": "USABC0D1EG",
            "switch_role": None
        }
        asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.UPSERT))
    else:  # pragma: no cover
        ...

    yield

    asyncio.run(cache.update_dev_db(data=test_ap, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_dev_cache_test_switch():
    if config.dev.mock_tests:
        test_sw = {
                "name": "cencli-test-sw",
                "status": "Down",
                "type": "sw",
                "model": "2530",
                "ip": "10.0.32.99",
                "mac": test_data["test_devices"]["switch"]["mac"],
                "serial": test_data["test_devices"]["switch"]["serial"],
                "group": "cencli_test_group2",
                "site": "cencli_test_site1",
                "version": "16.11.0026",
                "swack_id": None,
                "switch_role": None
        }
        asyncio.run(cache.update_dev_db(data=test_sw))
    yield

    asyncio.run(cache.update_dev_db(data=test_sw, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_cache_vsf_stack():
    cache_data = [
        {
            "name": "core-6300",
            "status": "Up",
            "type": "cx",
            "model": "6300M 48SR5 CL6 PoE 4SFP56 Swch (JL659A)",
            "ip": "10.0.30.213",
            "mac": "64:e8:81:b8:0c:80",
            "serial": "SG06KMY1S1",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.16.1006",
            "swack_id": "b89e6557-392e-4089-87da-b59d151797ec",
            "switch_role": 2
        },
        {
            "name": "core-6300",
            "status": "Up",
            "type": "cx",
            "model": "6300M 48SR5 CL6 PoE 4SFP56 Swch (JL659A)",
            "ip": None,
            "mac": "64:e8:81:aa:bb:cc",
            "serial": "SG0WADE1S2",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.16.1006",
            "swack_id": "b89e6557-392e-4089-87da-b59d151797ec",
            "switch_role": 3
        },
        {
            "name": "core-6300",
            "status": "Up",
            "type": "cx",
            "model": "6300M 48SR5 CL6 PoE 4SFP56 Swch (JL659A)",
            "ip": None,
            "mac": "64:e8:81:cc:bb:aa",
            "serial": "SG0WADE1S3",
            "group": "WadeLab",
            "site": "WadeLab",
            "version": "10.16.1006",
            "swack_id": "b89e6557-392e-4089-87da-b59d151797ec",
            "switch_role": 4
        }
    ]
    if config.dev.mock_tests:
        missing = [d for d in cache_data if d["serial"] not in cache.devices_by_serial]
        if missing:
            assert asyncio.run(cache.update_dev_db(missing))
    yield


@pytest.fixture(scope="function")
def ensure_dev_cache_test_vsx_switch():
    test_switch = {
        "name": "border1",
        "status": "Up",
        "type": "cx",
        "model": "8360-48XT4C switch (JL720A)",
        "ip": "10.0.30.142",
        "mac": "ec:02:73:bb:41:00",
        "serial": "SG18KRT025",
        "group": "ATM-LOCAL",
        "site": None,
        "version": "10.14.1020",
        "swack_id": None,
        "switch_role": 1
    }
    if config.dev.mock_tests:
        if test_switch["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_dev_db(data=test_switch))  # pragma: no cover
    yield

    if config.dev.mock_tests and test_switch["serial"] in cache.devices_by_serial:
        assert asyncio.run(cache.update_dev_db(data=test_switch, action=DBAction.DELETE))
    else:  # pragma: no cover
        ...

    return


# Ensures subscription has 0 available for certain tests
@pytest.fixture(scope="function")
def ensure_cache_subscription():
    if config.dev.mock_tests:
        test_sub = {
            "id": "7658e672-2af5-5646-aa37-406af19c6d41",
            "name": "advanced-ap",
            "type": "AP",
            "key": "ENCYHFWQLJNQCWDU",
            "qty": 1000,
            "available": 982,
            "is_eval": True,
            "sku": "Q9Y63-EVALS",
            "start_date": 1611532800,
            "end_date": 1924905600,
            "started": True,
            "expired": False,
            "valid": True
        }
        asyncio.run(cache._update_db(Subscription, data=test_sub, action=DBAction.UPSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_subscription_none_available():
    if config.dev.mock_tests:
        # available 982 below as we restore this after the test
        test_sub = {
            "id": "7658e672-2af5-5646-aa37-406af19c6d41",
            "name": "advanced-ap",
            "type": "AP",
            "key": "ENCYHFWQLJNQCWDU",
            "qty": 1000,
            "available": 982,
            "is_eval": True,
            "sku": "Q9Y63-EVALS",
            "start_date": 1611532800,
            "end_date": 1924905600,
            "started": True,
            "expired": False,
            "valid": True
        }
        asyncio.run(cache._update_db(Subscription, data={**test_sub, "available": 0}, action=DBAction.UPSERT))
    yield

    asyncio.run(cache._update_db(Subscription, data=test_sub, action=DBAction.UPSERT))
    return


@pytest.fixture(scope="function")
def ensure_cache_test_portal():
    if config.dev.mock_tests:
        test_portal = {
            "name": "cencli_test_portal",
            "id": "e2725c47-09e5-406a-b431-d503d02657ef",
            "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/cencli_test_portal/capture",
            "auth_type": "Anonymous",
            "is_aruba_cert": False,
            "is_default": False,
            "is_editable": True,
            "is_shared": True,
            "reg_by_email": False,
            "reg_by_phone": False
        }

        if test_portal["id"] not in cache.portals_by_id:
            assert asyncio.run(cache.update_portal_db(data=[test_portal]))
        else:  # pragma: no cover
            ...
    yield


@pytest.fixture(scope="function")
def ensure_cache_mpsk():
    if config.dev.mock_tests:
        cache_data = {
            "id": "4e650830-d4d6-4a19-b9af-e0f776c69d24",
            "name": "test@cencli.wtf",
            "role": "authenticated",
            "status": "enabled",
            "ssid": test_data["mpsk_ssid"]
        }

        if cache_data["id"] not in cache.mpsk_by_id:
            assert asyncio.run(cache._update_db(MPSK, data=cache_data, action=DBAction.INSERT))
    yield


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
            assert asyncio.run(cache.update_site_db(data=sites, action=DBAction.UPSERT))


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
            assert asyncio.run(cache.update_site_db(data=sites, action=DBAction.UPSERT))


@pytest.fixture(scope="function")
def ensure_cache_site2():  # pragma: no cover  Not used by itself currently, but keeping it for consistency so it's available
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
            assert asyncio.run(cache.update_site_db(data=sites, action=DBAction.UPSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_site4():
    if config.dev.mock_tests:
        cache_data = {
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
        if cache_data["name"] not in cache.sites_by_name:
            assert asyncio.run(cache.update_site_db(data=cache_data))
        else:  # pragma: no cover
            ...

    yield


@pytest.fixture(scope="function")
def ensure_cache_client_not_connected():
    if config.dev.mock_tests:
        cache_data = {
            "mac": "aa:bb:cc:dd:ee:ff",
            "name": "not-connected",
            "ip": "10.0.110.299",
            "type": "wireless",
            "network_port": "HPE_Aruba",
            "connected_serial": "CNR4LHJ08G",
            "connected_name": "ktcn.605h.5866",
            "site": "WadeLab",
            "group": "WadeLab",
            "last_connected": None
        }
        if cache_data["mac"] not in cache.clients_by_mac:
            assert asyncio.run(cache._update_db(Client, cache_data, action=DBAction.INSERT))
        else:  # pragma: no cover
            ...
    yield

    asyncio.run(cache._update_db(Client, data=cache_data, action=DBAction.DELETE, column="mac"))


@pytest.fixture(scope="function")
def ensure_cache_portal():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli-test",
            "id": "58039716-efb9-4397-9fe1-4b13e30df928",
            "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/delme/capture",
            "auth_type": "Anonymous",
            "is_aruba_cert": False,
            "is_default": False,
            "is_editable": True,
            "is_shared": True,
            "reg_by_email": False,
            "reg_by_phone": False
        }
        if cache_data["id"] not in cache.portals_by_id:
            asyncio.run(cache.update_portal_db(data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...

    yield

    asyncio.run(cache._update_db(Portal, data=cache_data, action=DBAction.DELETE, column="id"))


@pytest.fixture(scope="function")
def ensure_cache_no_defined_portals():
    if config.dev.mock_tests:
        defined = [p for p in cache.portals if p["name"] != "default"]
        portal_data = [{"id": p.id} for p in defined]
        if portal_data:
            assert asyncio.run(cache.update_portal_db(data=portal_data, action=DBAction.DELETE))
    else:  # pragma: no cover
        ...

    yield

    if config.dev.mock_tests:
        cache_data = [
            {
                "name": "BR1-Guest-Portal",
                "id": "c3919492-1927-4029-81d7-cab8dc5f18c4",
                "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/BR1-Guest-Portal/capture",
                "auth_type": "Anonymous",
                "is_aruba_cert": False,
                "is_default": False,
                "is_editable": True,
                "is_shared": True,
                "reg_by_email": False,
                "reg_by_phone": False
            },
            {
                "name": "delme",
                "id": "58039716-efb9-4397-9fe1-4b13e30df928",
                "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/delme/capture",
                "auth_type": "Anonymous",
                "is_aruba_cert": False,
                "is_default": False,
                "is_editable": True,
                "is_shared": True,
                "reg_by_email": False,
                "reg_by_phone": False
            },
            {
                "name": "gwu-guest",
                "id": "403c53ff-b414-4e77-9ad7-9be25236f429",
                "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/gwu-guest/capture",
                "auth_type": "Username/Password, Self-Registration",
                "is_aruba_cert": False,
                "is_default": False,
                "is_editable": True,
                "is_shared": True,
                "reg_by_email": False,
                "reg_by_phone": True
            },
            {
                "name": "Kabrew",
                "id": "e5538808-0e05-4ecd-986f-4bdce8bf52a4",
                "url": "https://naw1.cloudguest.central.arubanetworks.com/portal/scope.cust-5000692/Kabrew/capture",
                "auth_type": "Username/Password, Self-Registration",
                "is_aruba_cert": False,
                "is_default": False,
                "is_editable": True,
                "is_shared": True,
                "reg_by_email": True,
                "reg_by_phone": False
            }
        ]
        assert asyncio.run(cache.update_portal_db(cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_label1():
    cache_data = {"id": 1106, "name": "cencli_test_label1", "devices": 0}
    if config.dev.mock_tests and "cencli_test_label1" not in cache.labels_by_name:
        asyncio.run(cache.update_label_db(data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...
    yield

    asyncio.run(cache.update_label_db(data=cache_data, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_cache_label5():
    cache_data = {"id": 1110, "name": "cencli_test_label5", "devices": 0}
    if config.dev.mock_tests and "cencli_test_label5" not in cache.labels_by_name:  # pragma: no cover
        assert asyncio.run(cache.update_label_db(data=cache_data, action=DBAction.INSERT))
    else:  # pragma: no cover
        ...
    yield

    asyncio.run(cache.update_label_db(data=cache_data, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_cache_label2():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id": 1107, "name": "cencli_test_label2", "devices": 0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels, action=DBAction.UPSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_label3():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id": 1108, "name": "cencli_test_label3", "devices": 0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


@pytest.fixture(scope="function")
def ensure_cache_batch_labels():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id": 1109, "name": "cencli_test_label4", "devices": 0},
            {"id": 1110, "name": "cencli_test_label5", "devices": 0},
            {"id": 1111, "name": "cencli_test_label6", "devices": 0},
        ]
        missing = [label["name"] for label in batch_del_labels if label["name"] not in cache.labels_by_name]
        if missing:
            assert asyncio.run(cache.update_label_db(data=batch_del_labels))
    yield


# Need to add APs to FloorPlanAPDB
#   {
#     "id": "5000692__74:9E:75:C9:FF:16",
#     "name": "zrm.655.ff16",
#     "serial": "CNP7KZ2422",
#     "mac": "74:9E:75:C9:FF:16",
#     "floor_id": "5000692__3ca044b0-5bd3-40fe-ae40-f7cad0263575",
#     "building_id": "5000692__7",
#     "level": 2
#   }
@pytest.fixture(scope="function")
def ensure_cache_all_floor_plan():
    if config.dev.mock_tests:
        serials = ['CNC7J0T0GK', 'CNDDK2R9GJ', 'CNGQKGX0H3', 'CNKYKV1070', 'CNQVL8M0MH', 'PHS4LX101T', 'PHS4LX101V']
        cache_aps = {serial: cache.devices_by_serial[serial] for serial in serials}
        update_data = [
            {
                "id": f"5000692__{ap['mac']}",
                "name": ap['name'],
                "serial": ap['serial'],
                "mac": ap['mac'],
                "floor_id": "5000692__3ca044b0-5bd3-40fe-ae40-f7cad0263575",
                "building_id": "5000692__7",
                "level": 2
            }
            for ap in cache_aps.values()
        ]
        assert asyncio.run(cache._update_db(FloorPlanAP, data=update_data, action=DBAction.UPSERT))
    yield

    if config.dev.mock_tests:
        asyncio.run(cache._update_db(FloorPlanAP, data=update_data, action=DBAction.DELETE, column="id"))


def _ensure_cache_group_cloned(allowed_types: list[PrimaryDeviceTypes] = ["ap"],):
    allowed_types = sorted(allowed_types)
    if config.dev.mock_tests:
        cache_data = {
                "name": "cencli_test_cloned",
                "allowed_types": allowed_types,
                "gw_role": "branch",
                "aos10": False,
                "microbranch": False,
                "wlan_tg": False,
                "wired_tg": False,
                "monitor_only_sw": False,
                "monitor_only_cx": False,
                "cnx": None
        }
        asyncio.run(cache.update_group_db(data=cache_data, action=DBAction.UPSERT))

    yield


@pytest.fixture(scope="function")
def ensure_cache_group_cloned():
    yield from _ensure_cache_group_cloned()


@pytest.fixture(scope="function")
def ensure_cache_group_cloned_w_gw():
    yield from _ensure_cache_group_cloned(allowed_types=["ap", "gw"])


@pytest.fixture(scope="function")
def ensure_cache_group_cloned_gw_only():
    yield from _ensure_cache_group_cloned(allowed_types=["gw"])


@pytest.fixture(scope="function")
def ensure_cache_group_cloned_cx_only():
    yield from _ensure_cache_group_cloned(allowed_types=["cx"])


@pytest.fixture(scope="function")
def ensure_inv_cache_add_do_del_ap():
    if config.dev.mock_tests:
        cache_device = {
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
        assert asyncio.run(cache.update_inv_db(data=cache_device))
    yield

    # This was previously commented out... not sure why
    if config.dev.mock_tests:
        asyncio.run(cache.update_inv_db(data=cache_device, action=DBAction.DELETE))
    return


@pytest.fixture(scope="function")
def ensure_inv_cache_fake_archived_devs():
    if config.dev.mock_tests:
        cache_devices = [
            {
                "id": "a1b233cc-5545-1234-abcb-6551acaabbcc",
                "serial": "US18CEN103",
                "mac": "F0:5C:19:AB:CD:EF",
                "type": "ap",
                "model": "IAP-205-US",
                "sku": "JL185A",
                "services": None,
                "subscription_key": None,
                "subscription_expires": None,
                "assigned": True,
                "archived": True
            },
            {
                "id": "a1b233cc-5545-1234-abcb-6551acccbbaa",
                "serial": "US18CEN112",
                "mac": "F0:5C:19:12:34:56",
                "type": "ap",
                "model": "IAP-205-US",
                "sku": "JL185A",
                "services": None,
                "subscription_key": None,
                "subscription_expires": None,
                "assigned": True,
                "archived": True
            }
        ]
        assert asyncio.run(cache.update_inv_db(data=cache_devices))
    yield

    if config.dev.mock_tests:
        assert asyncio.run(cache.update_inv_db(data=cache_devices, action=DBAction.DELETE))


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
        cache_data = {
            "portal_id": "e5538808-0e05-4ecd-986f-4bdce8bf52a4",
            "name": "superlongemail",  # made diff than email to test completion
            "id": "7c9eb0df-b211-4225-94a6-437df0dfca59",
            "email": "superlongemail@kabrew.com",
            "phone": "+6155551212",
            "company": "central-api-cli test company",
            "enabled": True,
            "status": "Active",
            "created": 1758568643,
            "expires": 1761161342
        }
        if cache_data["id"] not in cache.guests_by_id:
            assert asyncio.run(cache.update_guest_db(data=[cache_data]))
    yield


@pytest.fixture(scope="function")
def ensure_no_cache_guest():
    def remove_test_guest():
        cache_data = [dict(g) for g in cache.guests if g["name"] == test_data["portal"]["guest"]["name"]]
        if cache_data:
            assert asyncio.run(cache.update_guest_db(data=cache_data, action=DBAction.DELETE))

    if config.dev.mock_tests:
        remove_test_guest()
    yield

    if config.dev.mock_tests:
        remove_test_guest()
    return


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
            assert asyncio.run(cache.update_template_db(data=cache_data, action=DBAction.INSERT))
    yield

    if config.dev.mock_tests:
        asyncio.run(cache.update_template_db(data=cache_data, action=DBAction.DELETE))
    return


# @pytest.fixture(scope="function")
# def ensure_no_cache_template():
#     cache_data = {
#         "name": "cencli_test_template",
#         "device_type": "sw",
#         "group": "cencli_test_group2",
#         "model": "ALL",
#         "version": "ALL",
#         "template_hash": "0976d6fef0f24e2d7cd38886f608757a"
#     }
#     if config.dev.mock_tests:
#         asyncio.run(cache.update_template_db(data=cache_data, action=DBAction.DELETE))
#     yield


@pytest.fixture(scope="function")
def ensure_cache_ap_template():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli_test_ap_template",
            "device_type": "ap",
            "group": "cencli_test_group2",
            "model": "ALL",
            "version": "ALL",
            "template_hash": "ece4e8651b45dcfd82f4cc2ae1ccfb4c"  # need to validate hash based on template from mock response
        }
        if f'{cache_data["name"]}_{cache_data["group"]}' not in cache.templates_by_name_group:
            assert asyncio.run(cache.update_template_db(data=cache_data, action=DBAction.INSERT))
    yield

    if config.dev.mock_tests:
        asyncio.run(cache.update_template_db(cache_data, DBAction.DELETE))


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
            assert asyncio.run(cache.update_template_db(data=cache_data, action=DBAction.INSERT))
    yield


@pytest.fixture(scope="function")
def ensure_cache_j2_var_yaml():
    test_j2_file = TEST_FILE_DIR / "test_runner_template.yaml"
    test_j2_file.write_text(
        "some_var: some_value\n"
    )
    assert test_j2_file.exists()
    yield

    test_j2_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def ensure_cache_j2_var_csv():
    test_j2_file = TEST_FILE_DIR / "test_runner_template.csv"
    test_j2_file.write_text(
        "some_var,\nsome_value,\n"
    )
    assert test_j2_file.exists()
    yield

    test_j2_file.unlink(missing_ok=True)


@pytest.fixture(scope="function")
def ensure_assign_dev_no_sub():
    test_assign_dev = cache.get_inv_identifier(test_data["subscription"]["assign_to_device"]["serial"])
    if test_assign_dev.services is not None:  # pragma: no cover
        cache_update_data = {**dict(test_assign_dev), "services": None, "subscription_expires": None, "subscription_key": None}
        asyncio.run(common.cache.update_inv_db(cache_update_data))
    yield


@pytest.fixture(scope="function")
def ensure_assign_dev_sub():
    test_assign_dev = cache.get_inv_identifier(test_data["subscription"]["assign_to_device"]["serial"])
    if test_assign_dev.services is None:  # pragma: no cover
        in_2_months = pendulum.now() + pendulum.duration(months=2)
        cache_update_data = {**dict(test_assign_dev), "services": test_data["subscription"]["name"], "subscription_expires": in_2_months.int_timestamp, "subscription_key": test_data["subscription"]["key"]}
        asyncio.run(common.cache.update_inv_db(cache_update_data))
    yield


@pytest.fixture(scope="function")
def ensure_not_cache_b4_adds():
    if config.dev.mock_tests:
        tables = [Group, Site, Label, Cert]
        statements = [delete(table).where(table.name.istartswith("cencli_test")) for table in tables]
        with SQLSession(cache.engine) as session:
            _ = [session.execute(stmt) for stmt in statements]
            session.commit()
    else:  # pragma: no cover
        ...

    yield


@pytest.fixture(scope="function")
def ensure_old_config():
    yield config._mock()
    return config._mock(True)
