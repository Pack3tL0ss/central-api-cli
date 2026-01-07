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
from centralcli.typedefs import PrimaryDeviceTypes

from . import mock_sleep, test_data
from ._mock_request import test_responses
from ._test_data import test_device_file, test_files, test_group_file

runner = CliRunner()

cache_bak_file = config.cache_file.parent / f"{config.cache_file.name}.pytest.bak"


def pytest_configure(config):
    """
    Installs the rich traceback handler for all uncaught exceptions during pytest runs.
    """
    install(show_locals=True, suppress=[
        "pytester", # Suppress internal pytest frames
        "pytest",   # Suppress pytest frames
        # Add other modules to suppress if needed, e.g., "my_library"
    ])


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
    if "--collect-only" not in session.config.invocation_params.args and config.dev.mock_tests and session.testscollected > 120:  # pragma: no cover
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
    for file in test_files:
        if file.exists():
            if file.is_dir():
                file.rmdir()  # must be empty
            else:
                file.unlink()


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
    teardown()


@pytest.fixture(scope='function', autouse=True)
def clear_lru_caches():
    cache.get_inv_identifier.cache_clear()
    cache.get_combined_inv_dev_identifier.cache_clear()
    cache.get_name_id_identifier.cache_clear()
    for db in cache._tables:
        db.clear_cache()
    cache.responses.clear()
    Session.requests_clear()
    yield


@pytest.fixture(scope="function")
def ensure_cache_cert():
    if config.dev.mock_tests and "cencli-test" not in cache.certs_by_name:
        asyncio.run(cache.update_db(cache.CertDB, data={"name": "cencli-test", "type": "SERVER_CERT", "md5_checksum": "781b9320972dc571d9f3055c081e8a11", "expired": False, "expiration": 2071936577}, truncate=False))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test" in cache.certs_by_name:
        doc_id = cache.certs_by_name["cencli-test"].doc_id
        asyncio.run(cache.update_db(cache.CertDB, doc_ids=[doc_id]))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_cert_same_as_existing():
    if config.dev.mock_tests and "cencli-test-existing-cert" not in cache.certs_by_name:
        asyncio.run(cache.update_db(cache.CertDB, data={"name": "cencli-test-existing-cert", "type": "SERVER_CERT", "md5_checksum": "43e0c762fc2bc47d8c6847a4b7b27af4", "expired": False, "expiration": 2071936577}, truncate=False))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test-existing-cert" in cache.certs_by_name:
        doc_ids = [c.doc_id for c in cache.certs if c["name"] == "cencli-test-existing-cert"]
        asyncio.run(cache.update_db(cache.CertDB, doc_ids=doc_ids))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_cert_expired():
    if config.dev.mock_tests and "cencli-test-expired-cert" not in cache.certs_by_name:
        asyncio.run(cache.update_db(cache.CertDB, data={"name": "cencli-test-expired-cert", "type": "SERVER_CERT", "md5_checksum": "6bf2b4afbbe379f44589e4be994fa4c1", "expired": True, "expiration": 1736493627}, truncate=False))
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and "cencli-test-expired-cert" in cache.certs_by_name:
        doc_id = cache.certs_by_name["cencli-test-expired-cert"].doc_id
        asyncio.run(cache.update_db(cache.CertDB, doc_ids=[doc_id]))
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
        if cache_data["name"] not in cache.groups_by_name:
            assert asyncio.run(cache.update_group_db(data=cache_data))
        elif cache.groups_by_name[cache_data["name"]].allowed_types != cache_data["allowed_types"]:  # pragma: no cover
            update_data = {**cache.groups_by_name, **{cache_data["name"]: cache_data}}
            assert asyncio.run(cache.update_db(cache.GroupDB, data=list(update_data.values()), truncate=True))
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
        if cache_data["name"] not in cache.groups_by_name:
            assert asyncio.run(cache.update_group_db(data=cache_data))
        elif any(
            [
                    cache.groups_by_name[cache_data["name"]].allowed_types != cache_data["allowed_types"],
                    cache.groups_by_name[cache_data["name"]].aos10 != cache_data["aos10"],
            ]
        ):   # pragma: no cover
            update_data = {**cache.groups_by_name, **{cache_data["name"]: cache_data}}
            assert asyncio.run(cache.update_db(cache.GroupDB, data=list(update_data.values()), truncate=True))
    yield


@pytest.fixture(scope="function")
def ensure_cache_mpsk_network():
    if config.dev.mock_tests:
        cache_data = {
            "name": "cencli-test-mpsknet",
            "id": "1ABCDE23FGH45I6K"
        }
        if cache_data["name"] not in [m["name"] for m in cache.mpsk_networks]:  # pragma: no cover
            assert asyncio.run(cache.update_db(cache.MpskNetDB, data=cache_data, truncate=False))
    yield

    if config.dev.mock_tests:
        doc_ids = [m.doc_id for m in cache.mpsk_networks if m["name"] == cache_data["name"]]
        if doc_ids:  # pragma: no cover
            assert asyncio.run(cache.update_mpsk_net_db(data=doc_ids, remove=True))
        doc_ids = [m.doc_id for m in cache.mpsk if m["ssid"] == cache_data["name"]]
        if doc_ids:  # pragma: no cover
            assert asyncio.run(cache.update_db(cache.MpskDB, doc_ids=doc_ids))


@pytest.fixture(scope="function")
def ensure_hook_proxy_started():  # pragma: no cover
    if config.dev.mock_tests and not [p.pid for p in psutil.process_iter(attrs=["name", "cmdline"]) if p.info["cmdline"] and True in ["wh_proxy" in x for x in p.info["cmdline"][1:]]]:
        with mock_sleep:
            result = runner.invoke(app, ["start", "hook-proxy", "-y"])
        assert result.exit_code == 0
        assert "Started" in result.stdout

    yield


@pytest.fixture(scope="function")
def ensure_no_cache():
    cache_file = config.cache_dir / "db.mocked.json"
    cache_file_bak = config.cache_dir / "db.mocked.json.bak"
    cache_file_bak.write_text(cache_file.read_text())
    cache_file.unlink()
    yield

    cache_file.write_text(cache_file_bak.read_text())
    cache_file_bak.unlink()


@pytest.fixture(scope="function")
def ensure_inv_cache_batch_devices():
    if config.dev.mock_tests:
        devices = [
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
            }
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.inventory_by_serial]
        if missing:
            assert asyncio.run(cache.update_inv_db(data=devices))
    yield


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
            # {
            #     "id": "f26c4528-4260-5e38-8167-2f4a08a214a4",
            #     "serial": "CNKJKV309D",
            #     "mac": "D0:D3:E0:CD:08:24",
            #     "type": "ap",
            #     "model": "AP-575-US",
            #     "sku": "R4H18A",
            #     "services": "advanced-ap",
            #     "subscription_key": "ENCYHFWQLJNQCWDU",
            #     "subscription_expires": 1788715367,
            #     "assigned": True,
            #     "archived": False
            # },
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
            }
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.devices_by_serial]
        if missing:  # pragma: no cover
            assert asyncio.run(cache.update_dev_db(data=devices))
    yield

    if config.dev.mock_tests and missing:  # pragma: no cover
        doc_ids = [cache.devices_by_serial[s].doc_id for s in missing if s in cache.devices_by_serial]
        if doc_ids:
            assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=doc_ids))
    return



@pytest.fixture(scope="function")
def ensure_inv_cache_test_ap():
    if config.dev.mock_tests:
        devices = [
            {
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
        ]
        missing = [dev["serial"] for dev in devices if dev["serial"] not in cache.inventory_by_serial]
        if missing:  # pragma: no cover
            assert asyncio.run(cache.update_inv_db(data=devices))
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
            assert asyncio.run(cache.update_inv_db(data=test_switch))
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
        missing = [dev["serial"] for dev in test_switches if dev["serial"] not in cache.inventory_by_serial]
        if missing:  # pragma: no cover
            assert asyncio.run(cache.update_inv_db(data=test_switches))
            cache.InvDB.clear_cache()
    yield

    doc_ids = [cache.inventory_by_serial[dev["serial"]].doc_id for dev in test_switches if dev["serial"] in cache.inventory_by_serial]
    if doc_ids:  # pragma: no cover
        assert asyncio.run(cache.update_inv_db(data=doc_ids, remove=True))


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
            cache.DevDB.clear_cache()
    yield

    doc_ids = [cache.devices_by_serial[dev["serial"]].doc_id for dev in test_switches if dev["serial"] in cache.devices_by_serial]
    if doc_ids:  # pragma: no cover
        assert asyncio.run(cache.update_dev_db(data=doc_ids, remove=True))


@pytest.fixture(scope="function")
def ensure_dev_cache_ap():
    if config.dev.mock_tests:
        cache_data =   {
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
        if cache_data["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=cache_data, truncate=False))  # pragma: no cover
        clean_cache_data = cache.devices.copy()
    else:  # pragma: no cover
        ...
    yield

    if config.dev.mock_tests and cache_data["name"] not in [ap["name"] for ap in cache.devices if ap["type"] == "ap"]:
        assert asyncio.run(cache.update_db(cache.DevDB, data=clean_cache_data, truncate=True))
    else:  # pragma: no cover
        ...
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
        if test_data["test_devices"]["ap"]["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_ap, truncate=False))
    else:  # pragma: no cover
        ...

    yield


    if test_data["test_devices"]["ap"]["serial"] in cache.devices_by_serial:
        serial = test_data["test_devices"]["ap"]["serial"]
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[serial].doc_id]))
    else:  # pragma: no cover
        ...

    return


@pytest.fixture(scope="function")
def ensure_dev_cache_no_last_rename_ap():
    if config.dev.mock_tests:
        if "CNP7KZ2422" in cache.devices_by_serial:
            doc_id = cache.devices_by_serial["CNP7KZ2422"].doc_id
            assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=doc_id))
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
        if test_ap["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_ap, truncate=False))
    else:  # pragma: no cover
        ...

    yield

    if test_ap["serial"] in cache.devices_by_serial:
        serial = test_ap["serial"]
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[serial].doc_id]))
    else:  # pragma: no cover
        ...

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
        if test_ap["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_ap, truncate=False))
    else:  # pragma: no cover
        ...

    yield

    if test_ap["serial"] in cache.devices_by_serial:
        serial = test_ap["serial"]
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[serial].doc_id]))
    else:  # pragma: no cover
        ...
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
        if test_sw["serial"] not in cache.devices_by_serial:
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_sw, truncate=False))
    yield

    if test_sw["serial"] in cache.devices_by_serial:
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[test_sw["serial"]].doc_id]))
    else:  # pragma: no cover
        ...

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
            resp = common.batch_add_devices(data=missing, yes=True)
            assert all([r.ok for r in resp])
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
            assert asyncio.run(cache.update_db(cache.DevDB, data=test_switch, truncate=False))  # pragma: no cover
    yield

    if config.dev.mock_tests and test_switch["serial"] in cache.devices_by_serial:
        serial = test_switch["serial"]
        assert asyncio.run(cache.update_db(cache.DevDB, doc_ids=[cache.devices_by_serial[serial].doc_id]))
    else:  # pragma: no cover
        ...

    return


# Ensures subscription has 0 available for certain tests
@pytest.fixture(scope="function")
def ensure_cache_subscription(request: pytest.FixtureRequest):
    avail = 0 if not hasattr(request, "param") else request.param
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
        if test_sub["id"] not in cache.subscriptions_by_id:  # pragma: no cover
            update_data = {**test_sub, "available": avail}
            assert asyncio.run(cache.update_db(cache.SubDB, data=update_data, truncate=False))
        else:  # pragma: no cover
            update_data = [*[v for k, v in cache.subscriptions_by_id.items() if k != test_sub["id"]], {**cache.subscriptions_by_id[test_sub["id"]], "available": avail}]
            assert asyncio.run(cache.update_db(cache.SubDB, data=update_data, truncate=True))
    yield

    update_data = [*[v for k, v in cache.subscriptions_by_id.items() if k != test_sub["id"]], test_sub]
    assert asyncio.run(cache.update_db(cache.SubDB, data=update_data, truncate=True))
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
            assert asyncio.run(cache.update_db(cache.MpskDB, data=cache_data, truncate=False))
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
            assert asyncio.run(cache.update_site_db(data=sites))
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
        cache_data =   {
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
            assert asyncio.run(cache.update_db(cache.ClientDB, cache_data, truncate=False))
        else:  # pragma: no cover
            ...
    yield

    client = cache.get_client_identifier(cache_data["mac"])
    asyncio.run(cache.update_db(cache.ClientDB, doc_ids=client.doc_id))


@pytest.fixture(scope="function")
def ensure_cache_portal():
    if config.dev.mock_tests:
        cache_data =   {
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
            asyncio.run(cache.update_db(cache.PortalDB, data=cache_data, truncate=False))
    else:  # pragma: no cover
        ...

    yield


    if config.dev.mock_tests and cache_data["id"] in cache.portals_by_id:
        doc_id = cache.portals_by_id[cache_data["id"]].doc_id
        asyncio.run(cache.update_db(cache.PortalDB, doc_ids=[doc_id]))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_no_defined_portals():
    if config.dev.mock_tests:
        defined = [p for p in cache.portals if p["name"] != "default"]
        doc_ids = [p.doc_id for p in defined]
        if doc_ids:
            asyncio.run(cache.update_portal_db(doc_ids, remove=True))
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
        assert asyncio.run(cache.update_portal_db(cache_data))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_label1():
    if config.dev.mock_tests and "cencli_test_label1" not in cache.labels_by_name:
        asyncio.run(cache.update_db(cache.LabelDB, data={"id": 1106, "name": "cencli_test_label1", "devices": 0}, truncate=False))
    else:  # pragma: no cover
        ...

    yield

    if config.dev.mock_tests and "cencli_test_label1" in cache.labels_by_name:
        doc_id = cache.labels_by_name["cencli_test_label1"].doc_id
        asyncio.run(cache.update_db(cache.LabelDB, doc_ids=[doc_id]))
    else:  # pragma: no cover
        ...


@pytest.fixture(scope="function")
def ensure_cache_label5():
    if config.dev.mock_tests and "cencli_test_label5" not in cache.labels_by_name:  # pragma: no cover
        asyncio.run(cache.update_db(cache.LabelDB, data={"id": 1110, "name": "cencli_test_label5", "devices": 0}, truncate=False))
    else:  # pragma: no cover
        ...

    yield

    if config.dev.mock_tests and "cencli_test_label5" in cache.labels_by_name:
        doc_id = cache.labels_by_name["cencli_test_label5"].doc_id
        asyncio.run(cache.update_db(cache.LabelDB, doc_ids=[doc_id]))
    else:  # pragma: no cover
        ...


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
def ensure_cache_batch_labels():
    if config.dev.mock_tests:
        batch_del_labels = [
            {"id":1109,"name":"cencli_test_label4","devices":0},
            {"id":1110,"name":"cencli_test_label5","devices":0},
            {"id":1111,"name":"cencli_test_label6","devices":0},
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

        doc_ids = cache.FloorPlanAPDB.insert_multiple(update_data)
        assert len(doc_ids) == len(serials)

    yield

    if config.dev.mock_tests:
        assert asyncio.run(cache.update_db(cache.FloorPlanAPDB, doc_ids=doc_ids))


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
        if cache_data["name"] not in cache.groups_by_name:
            assert asyncio.run(cache.update_group_db(data=cache_data))
        elif allowed_types and sorted(cache.groups_by_name[cache_data["name"]]["allowed_types"]) != allowed_types:
            cache_group = cache.groups_by_name[cache_data["name"]]
            cache_group["allowed_types"] = allowed_types
            update_data = {**cache.groups_by_name, cache_data["name"]: cache_group}
            assert asyncio.run(cache.update_db(cache.GroupDB, data=list(map(dict, update_data.values())), truncate=True))
        else:  # pragma: no cover
            ...

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
        doc_ids = [g.doc_id for g in cache.guests if g["name"] == test_data["portal"]["guest"]["name"]]
        if doc_ids:
            assert asyncio.run(cache.update_db(cache.GuestDB, doc_ids=doc_ids))

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
            assert asyncio.run(cache.update_db(cache.TemplateDB, data=cache_data, truncate=False))
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


@pytest.fixture(scope="function")
def ensure_cache_j2_var_yaml():
    test_j2_file = config.cache_dir / "test_runner_template.yaml"
    test_j2_file.write_text(
        "some_var: some_value\n"
    )
    assert test_j2_file.exists()
    yield

    test_j2_file.unlink(missing_ok=True)

@pytest.fixture(scope="function")
def ensure_cache_j2_var_csv():
    test_j2_file = config.cache_dir / "test_runner_template.csv"
    test_j2_file.write_text(
        "some_var,\nsome_value,\n"
    )
    assert test_j2_file.exists()
    yield

    test_j2_file.unlink(missing_ok=True)
