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

from centralcli import utils
from centralcli.cache import api
from centralcli.cli import app
from centralcli.constants import ShowArgs, arg_to_what
from centralcli.environment import env
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
    @pytest.mark.parametrize("args", [("enabled=True",), ("enabled=False",), ("reset=True",)])
    def test_update_mpsk(ensure_cache_mpsk, args: tuple[str]):
        result = runner.invoke(app, ["test", "method", "update_named_mpsk", "1EBTWK86LPQ86S0B", "4e650830-d4d6-4a19-b9af-e0f776c69d24", *args])
        capture_logs(result, "test_update_mpsk")
        assert result.exit_code == 0
        assert "204" in result.stdout

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"group": "cencli_test_group2", "name": "cencli_test_template", "payload": Path(test_data["template"]["template_file"]).read_text(), "device_type": "sw"},
            {
                "group": "cencli_test_group2",
                "name": "cencli_test_template",
                "payload": Path(test_data["template"]["template_file"]).read_text().encode("utf-8"),
                "device_type": "sw",
            },
        ],
    )
    def test_update_template_w_payload(ensure_cache_template, ensure_cache_group2, kwargs: dict[str, str]):
        resp = api.session.request(api.configuration.update_existing_template, **kwargs)
        assert resp.status == 200

    def test_visualrf_get_bldgs_for_campus_paged():
        resp = api.session.request(api.visualrf.get_buildings_for_campus, "5000692__default")
        assert resp.status == 200
        assert len(resp.raw["buildings"]) > 100

    def test_visualrf_get_bldgs_for_campus_fail():
        resp = api.session.request(api.visualrf.get_buildings_for_campus, "5000692__default")
        assert resp.ok is False

    def test_configuration_replace_per_ap_config():
        clis = [
            "per-ap-settings f0:5c:19:ce:7a:86",
            "  hostname cencli-test-ap",
            '  ip-address 0.0.0.0 0.0.0.0 0.0.0.0 0.0.0.0 ""',
            "  swarm-mode cluster",
            "  wifi0-mode access",
            "  wifi1-mode access",
            "  uplink-vlan 0",
            "  g-channel 0 -127",
            "  a-channel 0 -127",
            "  a-external-antenna 0",
            "  g-external-antenna 0",
        ]
        resp = api.session.request(api.configuration.replace_per_ap_config, test_data["test_devices"]["ap"]["serial"], clis=clis)
        assert resp.ok

else:  # pragma: no cover
    ...


@pytest.mark.parametrize(
    "kwargs,exception,pass_condition",
    [
        [{"client_type": "wired", "band": "5Ghz"}, ValueError, None],  # wired client_type w/ wlan filter
        [{"client_type": "wireless", "stack_id": "some-stack-id"}, ValueError, None],  # wireless client_type w/ wired filter
        [{"client_type": "wireless", "mac": "aa:bb:cc:gg:hh:01"}, None, lambda r: "invalid" in r.output],  # invalid mac
    ],
)
def test_monitoring_get_clients_fail(kwargs: dict[str, str | bool], exception: Exception, pass_condition: Callable):
    if exception:
        try:
            api.session.request(api.monitoring.get_clients, **kwargs)
        except ValueError:
            ...  # Test Passes
        else:  # pragma: no cover
            raise AssertionError(f"test_monitoring_get_clients_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}")
    else:
        result = api.session.request(api.monitoring.get_clients, **kwargs)
        assert pass_condition(result)


@pytest.mark.parametrize(
    "_,fixture,kwargs,exception,pass_condition,test_name_append",
    [
        [1, "ensure_cache_group4", {"group": "cencli_test_group4", "aos10": False}, None, lambda r: "reverting back" in r.error, None],
        [2, "ensure_cache_group4", {"group": "cencli_test_group4"}, None, lambda r: not r.ok, "fail"],
        [
            3,
            "ensure_cache_group4",
            {"group": "cencli_test_group4", "microbranch": True},
            None,
            lambda r: "can only be set" in "\n".join([res.output for res in utils.listify(r)]),
            None,
        ],
        [
            4,
            "ensure_cache_group1",
            {"group": "cencli_test_group1", "monitor_only_sw": True},
            None,
            lambda r: "can only be set" in "\n".join([res.output for res in utils.listify(r)]),
            None,
        ],
        [
            5,
            "ensure_cache_group1",
            {"group": "cencli_test_group1", "monitor_only_cx": True},
            None,
            lambda r: "can only be set" in "\n".join([res.output for res in utils.listify(r)]),
            None,
        ],
        [
            6,
            "ensure_cache_group4",
            {"group": "cencli_test_group4", "allowed_types": "invalid"},
            None,
            lambda r: "Invalid device type" in "\n".join([res.output for res in utils.listify(r)]),
            None,
        ],
    ],
)
def test_configuration_update_group_properties(
    _: int, fixture: str, kwargs: dict[str, str | bool], exception: Exception, pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest
):
    request.getfixturevalue(fixture)
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    if exception:  # pragma: no cover
        try:
            api.session.request(api.configuration.update_group_properties, **kwargs)
        except ValueError:
            ...  # Test Passes
        else:  # pragma: no cover
            raise AssertionError(f"{env.current_test} should have raised a ValueError due to invalid params, but did not.  {kwargs =}")
    else:
        result = api.session.request(api.configuration.update_group_properties, **kwargs)
        assert pass_condition(result)


@pytest.mark.parametrize(
    "_,func,kwargs,expected_exception",
    [
        (1, api.configuration.update_existing_template, {"group": test_data["template_switch"]["group"], "name": "cencli-test-template", "template": "NoExistFile"}, FileNotFoundError),
        (2, api.configuration.update_existing_template, {"group": test_data["template_switch"]["group"], "name": "cencli-test-template"}, ValueError),
        (3, api.configuration.update_cx_properties, {"serial": "USZYX123ABC45", "group": "fake-group"}, ValueError),
        (4, api.configuration.update_cx_properties, {"serial": "USZYX123ABC45", "admin_user": "fake-user"}, ValueError),
        (5, api.configuration.update_group_cp_cert, {"group": "fake-group"}, ValueError),
        (6, api.configuration.update_group_cp_cert, {}, ValueError),
    ],
)
def test_configuration_classic_fail(_: int, func: Callable, kwargs: dict[str, str], expected_exception: Exception):
    try:
        api.session.request(func, **kwargs)
    except expected_exception:
        ...  # test passes
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
                {"serial": "US1234567", "mac": "aa:bb:cc:dd:ee:ff", "license": "advanced_ap"},  # missing serial
                {"mac": "aa:bb:cc:dd:ee:f1", "license": "advanced_ap"},
            ]
        },
    ],
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
    ],
)
def test_add_template(ensure_cache_group2, kwargs: dict[str, str | bool]):
    resp = api.session.request(api.configuration.add_template, **{**kwargs, "template": test_ap_ui_group_template.read_bytes()})
    assert resp.status == 201


@pytest.mark.parametrize(
    "kwargs",
    [
        {"name": "cencli-fail-template", "group": "cencli_test_group2", "template": "no-exit-file.cencli.test"},
    ],
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
    ],
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
    ],
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
    ],
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
    ],
)
def test_cloud_auth_fail(kwargs: dict[str, str | bool]):
    try:
        api.session.request(api.cloudauth.get_authentications, **kwargs)
    except ValueError:
        ...
    else:  # pragma: no cover
        raise AssertionError(f"test_cloud_auth_fail should have raised a ValueError due to invalid params, but did not.  {kwargs =}")


@pytest.mark.parametrize(
    "kwargs,expected_exception",
    [
        [{"ip": "10.0.31.5"}, ValueError],  # No serial
        [{"as_dict": {test_data["test_devices"]["ap"]["serial"]: {"ip": "10.0.31.5"}}}, ValueError],  # IP without mask, gateway, etc.
        [{"as_dict": {test_data["test_devices"]["ap"]["serial"]: {"flex_dual_exclude": "9"}}}, ValueError],  # Invalid value for flex_dual_exclude
    ],
)
def test_configuration_update_per_ap_settings_exceptions(ensure_dev_cache_test_ap, kwargs: dict[str, str | bool], expected_exception: Exception):
    try:
        api.session.request(api.configuration.update_per_ap_settings, **kwargs)
    except expected_exception:
        ...
    else:  # pragma: no cover
        raise AssertionError(f"test_configuration_update_per_ap_settings should have raised a {expected_exception} due to invalid params, but did not.  {kwargs =}")


@pytest.mark.parametrize(
    "kwargs,pass_condition",
    [
        [{"serial": test_data["test_devices"]["ap"]["serial"]}, lambda resp: "No Values" in "\n".join([str(r) for r in resp])],  # No values
    ],
)
def test_configuration_update_per_ap_settings_fail(ensure_dev_cache_test_ap, kwargs: dict[str, str | bool], pass_condition: Callable):
    resp = api.session.request(api.configuration.update_per_ap_settings, **kwargs)
    assert not any([r.ok for r in resp])
    assert pass_condition(resp)


@pytest.mark.parametrize(
    "kwargs,pass_condition,test_name_append",
    [
        [{}, lambda r: r.ok, None],
        [{}, lambda r: not r.ok, "fail_names"],
        [{}, lambda r: not r.ok, "fail"],
    ],
)
def test_configuration_get_groups_properties(kwargs: dict[str, str | bool], pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    resp = api.session.request(api.configuration.get_groups_properties, **kwargs)
    assert pass_condition(resp)


def test_get_user_accounts():
    result = runner.invoke(app, ["test", "method", "get_user_accounts"])
    capture_logs(result, "get_user_accounts")
    assert result.exit_code == 0
    assert "200" in result.stdout


@pytest.mark.parametrize(
    "cmd,key,expected",
    [
        ["refresh", "webhooks", "webhook"],
        ["assign", "subscriptions", "subscription"],
        ["unassign", "labels", "label"],
        ["cancel", ShowArgs.groups, "group"],
        ["update", "swarms", "swarm"],
        ["rename", ShowArgs.sites, "site"],
        ["delete", "guests", "guest"],
        ["upgrade", "groups", "group"],
        ["add", "groups", "group"],
        ["test", "webhooks", "webhook"],
        ["convert", "templates", "template"],
        ["ts", "aps", "ap"],
        ["clone", "groups", "group"],
        ["kick", ShowArgs.clients, "client"],
        ["bounce", "ports", "interface"],
        ["caas", "send_cmd", "send_cmds"],
    ],
)
def test_arg_to_what(cmd: str, key: str | ShowArgs, expected: str):
    assert arg_to_what(key=key, default="", cmd=cmd) == expected
