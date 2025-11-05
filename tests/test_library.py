"""
tests for method/function branches that can't be tested via the CLI either because there
is not a command associated yet, or because the branch is only reachable when used as a library.

i.e. The CLI handles validation / errors prior to sending to the library modules that perform the API call.
So to test handling of invalid arguments to the library methods we need to test them directly (or via "cencli test method")
"""
from enum import Enum
from pathlib import Path
from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli.cache import api
from centralcli.cli import app
from centralcli.exceptions import MissingRequiredArgumentException

from . import capture_logs, config, test_data
from ._test_data import test_ap_ui_group_template, test_cert_file

runner = CliRunner()

class InvalidTimeRange(str, Enum):
    _9h = "9h"
INVALID_TIME_RANGE = InvalidTimeRange._9h

if config.wss.key:
    def test_validate_wss_key():
        result = runner.invoke(app, ["test", "method", "validate_wss_key", config.wss.base_url, config.wss.key])
        capture_logs(result, "test_validate_wss_key")
        assert result.exit_code == 0
        assert "200" in result.stdout
else:  # pragma: no cover
    ...


if config.dev.mock_tests:
    def test_ack_notification():  # TODO NEEDS COMMAND, and alert id to int cache (like logs/events)
        resp = api.session.request(api.central.central_acknowledge_notifications, "AZl5PdWQBnVd7wH8QpSa")
        assert resp.ok
        assert resp.status == 200

    def test_upload_certificate_no_cert_format():
        resp = api.session.request(api.configuration.upload_certificate, server_cert=True, cert_format="PEM", cert_file=str(test_cert_file))
        assert resp.status == 201

    # TODO need cencli update command
    @pytest.mark.parametrize(
        "args",
        [
            ("enabled=True",), ("enabled=False",), ("reset=True",)
        ]
    )
    def test_update_mpsk(ensure_cache_mpsk, args: tuple[str]):
        result = runner.invoke(
            app,
            [
                "test",
                "method",
                "update_named_mpsk",
                "1EBTWK86LPQ86S0B",
                "4e650830-d4d6-4a19-b9af-e0f776c69d24",
                *args
            ]
        )
        capture_logs(result, "test_update_mpsk")
        assert result.exit_code == 0
        assert "204" in result.stdout


    @pytest.mark.parametrize(
        "kwargs",
        [
            {
                "group": "cencli_test_group2",
                "name": "cencli_test_template",
                "payload": Path(test_data["template"]["template_file"]).read_text(),
                "device_type": "sw"
            },
            {
                "group": "cencli_test_group2",
                "name": "cencli_test_template",
                "payload": Path(test_data["template"]["template_file"]).read_text().encode("utf-8"),
                "device_type": "sw"
            }
        ]
    )
    def test_update_template_w_payload(ensure_cache_template, ensure_cache_group2, kwargs: dict[str, str]):
        resp = api.session.request(api.configuration.update_existing_template, **kwargs)
        assert resp.status == 200


    def test_visualrf_bldgs_for_campus_paged():
        resp = api.session.request(api.visualrf.get_buildings_for_campus, "5000692__default")
        assert resp.status == 200
        assert len(resp.raw["buildings"]) > 100
else:  # pragma: no cover
    ...


@pytest.mark.parametrize(
    "func,kwargs,expected_exception",
    [
        (api.configuration.update_existing_template, {"group": test_data["template_switch"]["group"], "name": "cencli-test-template", "template": "NoExistFile"}, FileNotFoundError),
        (api.configuration.update_existing_template, {"group": test_data["template_switch"]["group"], "name": "cencli-test-template"}, ValueError),
    ]
)
def test_configuration_classic_fail(func: Callable, kwargs: dict[str, str], expected_exception: Exception):
    try:
        api.session.request(func, **kwargs)
    except expected_exception:
        ... # test passes
    else:  # pragma: no cover
        raise AssertionError(f"test_configuration_classic_fail expected {expected_exception} {kwargs =}")


def test_get_ap_system_config():
    resp = api.session.request(api.configuration.get_ap_system_config, test_data["ap"]["group"])
    assert resp.ok
    assert resp.status == 200


def test_platform_get_valid_subscription_names_w_dev_type():
    resp = api.session.request(api.platform.get_valid_subscription_names, device_type="cx")
    assert resp.status == 200
    assert "foundation_switch" in str(resp.output)


# The cli doesn't use the reverse param to the API endpoint it's done in render
def test_get_labels():
    resp = api.session.request(api.central.get_labels, reverse=True)
    assert resp.status == 200


def test_kick_all_missing_argument():
    try:
        api.session.request(api.device_management.kick_users, test_data["ap"]["serial"])
    except MissingRequiredArgumentException:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_kick_all_missing_argument should have raised a MissingRequiredArgumentException but did not")


def test_remove_label_from_devices_fail():
    try:
        api.session.request(api.central.remove_label_from_devices, 1106, serials="US123456789", device_type="INVALID_DEV_TYPE")
    except ValueError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_remove_label_from_devices_fail should have raised a ValueError due to invalid device_type, but did not")


@pytest.mark.parametrize(
    "kwargs",
    [
        {},  # missing required data
        {"serial": "US1234567", "mac": "bb:cc:dd:ee:ff:gg"},  # invalid MAC
        {"device_list": ["invalid", "data", "type"]},  # invalid data type for device_list
        {"device_list": [{"serial": "US1234567"}]},  # device_list missing mac
        {"device_list": [{"mac": "invalid"}]},  # device_list invalid mac
        {
            "device_list": [
                {"serial": "US1234567", "mac": "aa:bb:cc:dd:ee:ff", "license": "advanced_ap"}, # missing serial
                {"mac": "aa:bb:cc:dd:ee:f1", "license": "advanced_ap"}
            ]
        },
    ]
)
def test_add_devices_fail(kwargs: dict[str, str | bool]):
    try:
        resp = api.session.request(api.platform.add_devices, **kwargs)
    except ValueError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError(f"test_add_devices_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}\n{resp}")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "cencli_libtest_template", "group": "cencli_test_group2"},
    ]
)
def test_add_template(ensure_cache_group2, kwargs: dict[str, str | bool]):
    resp = api.session.request(api.configuration.add_template, **{**kwargs, "template": test_ap_ui_group_template.read_bytes()})
    assert resp.status == 201


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "cencli-fail-template", "group": "cencli_test_group2", "template": "no-exit-file.cencli.test"},
    ]
)
def test_add_template_fail(ensure_cache_group2, kwargs: dict[str, str | bool]):
    try:
        resp = api.session.request(api.configuration.add_template, **kwargs)
    except FileNotFoundError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError(f"test_add_template_fail should have raised a FileNotFoundError due to invalid params, but did not.  {kwargs =}\n{resp}")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"server_cert": True, "ca_cert": True},  # too many cert types provided
        {},  # no cert type provided
        {"server_cert": True, "cert_format": "INVALID"},  # invalid cert format
        {"server_cert": True},  # no cert_format provided
        {"server_cert": True, "cert_format": "PEM"},  # No cert_data or cert_file
        {"server_cert": True, "cert_format": "PEM", "cert_data": "cert_data", "cert_file": "cert_file"},  # both cert_data and cert_file
    ]
)
def test_upload_certificate_fail(kwargs: dict[str, str | bool]):
    try:
        api.session.request(api.configuration.upload_certificate, **kwargs)
    except ValueError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError(f"test_upload_certificate_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}")


@pytest.mark.parametrize(
    "func,kwargs",
    [
        (api.visualrf.get_clients_for_floor, {"floor_id": "5000692__ae78073d-a227-4c0e-9510-9f3002414304"}),
        (api.visualrf.get_ap_location, {"ap_id": "5000692__F0:1A:A0:2A:58:66"}),
    ]
)
def test_visualrf(func: Callable, kwargs: dict[str, str]):
    resp = api.session.request(func, **kwargs)
    assert resp.status == 200


@pytest.mark.parametrize(
    "kwargs",
    [
        {"group": "cencli-test-group-fail", "allowed_types": ["ap", "invalid_type"], "monitor_only_sw": True},  # smon only w/out sw as allowed type (warning) + invalid type
        {"group": "cencli-test-group-fail", "allowed_types": ["ap", "sdwan"]},  # sdwan needs to be only type
        {"group": "cencli-test-group-fail", "allowed_types": ["ap"], "microbranch": True},  # mb w/out aos10=True
        {"group": "cencli-test-group-fail", "allowed_types": ["ap"], "microbranch": True, "aos10": False},  # mb w/out aos10=True
        {"group": "cencli-test-group-fail", "allowed_types": ["ap", "gw"], "microbranch": True, "aos10": True},  # gw can't be in group w/ mb ap
        {"group": "cencli-test-group-fail", "allowed_types": ["cx"], "monitor_only_cx": True, "wired_tg": True},  # mon only and TG
    ]
)
def test_configuration_create_group_fail(kwargs: dict[str, str | bool]):
    try:
        api.session.request(api.configuration.create_group, **kwargs)
    except ValueError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError(f"test_configuration_create_group_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"time_window": INVALID_TIME_RANGE},
    ]
)
def test_cloud_auth_fail(kwargs: dict[str, str | bool]):
    try:
        api.session.request(api.cloudauth.get_authentications, **kwargs)
    except ValueError:
        ...
    else:  # pragma: no cover
        raise AssertionError(f"test_cloud_auth_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}")

