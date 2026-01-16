from __future__ import annotations

from pathlib import Path
from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import cache, utils
from centralcli.cli import api, app
from centralcli.environment import env

from . import capture_logs, clean_mac, config, end_2_days_ago, now_str, start_180_days_ago, test_data

runner = CliRunner()


# tty size is MonkeyPatched to 190, 55 the end result during pytest runs is 156, 31
# Not sure why but it's larger than the 80, 24 fallback which it was using.
def test_check_fw_available():
    result = runner.invoke(app, ["check", "firmware-available", "ap", "10.7.2.1_93286"],)
    capture_logs(result, "test_check_fw_available")
    assert result.exit_code == 0
    assert "200" in result.stdout


@pytest.mark.parametrize(
    "_,fixtures,args,pass_condition",
    [
        [1, None, ("-d", "--debug",), lambda r: "API" in r],
        [2, "ensure_cache_group1", ("--label", "cencli_test_label1", "--group", "cencli_test_group1"), lambda r: "API" in r and "ignored" in r],  # label ignored due to --group
        [3, "ensure_cache_label1", ("--label", "cencli_test_label1"), lambda r: "API" in r],
        [4, None, ("--type", "user"), lambda r: "API" in r],
        [5, None, ("--type", "ids"), lambda r: "API" in r],
        [6, None, ("--severity", "warning"), lambda r: "API" in r],
        [7, None, ("--severity", "info"), lambda r: "API" in r],
        [8, None, ("--end", end_2_days_ago), lambda r: "API" in r],
        [9, None, ("--past", "180d"), lambda r: "API" in r and "--past" in r],  # warning --past exceeds max days allowed
    ]
)
def test_show_alerts(_: int, fixtures: str | list[str] | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixtures:
        [request.getfixturevalue(f) for f in utils.listify(fixtures)]
    result = runner.invoke(app, ["show", "alerts", *args],)
    capture_logs(result, "test_show_alerts")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition",
    [
        [1, ("--start", start_180_days_ago, "--end", now_str), lambda r: "--start" in r],
    ]
)
def test_show_alerts_invalid(_: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "alerts", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_aps_dirty():
    result = runner.invoke(app, ["show", "aps", "--dirty", "--group", test_data["ap"]["group"]],)
    capture_logs(result, "test_show_aps_dirty")
    assert result.exit_code == 0
    assert "dirty" in result.stdout


def test_show_aps_dirty_missing_group():
    result = runner.invoke(app, ["show", "aps", "--dirty"])
    capture_logs(result, "test_show_aps_dirty_missing_group", expect_failure=True)
    assert result.exit_code == 1
    assert "group" in result.stdout.lower()


def test_show_archived():
    result = runner.invoke(app, ["show", "archived"],)
    capture_logs(result, "test_show_archived")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,fixture,args,pass_condition,expect_failure",
    [
        [1, None, (), lambda r: "All" in r, False],
        [2, None, (test_data["client"]["wireless"]["mac"], "-S", "--dev", test_data["ap"]["name"], "--group", test_data["ap"]["group"]), lambda r: "ignored" in r, False],  # -S --dev --group flags are ignored
        [3, None, (test_data["client"]["wireless"]["mac"],), lambda r: "TX" in r, False],
        [4, None, ("-S", "--dev", test_data["aos8_ap"]["name"]), lambda r: "API" in r, False],  # aos8
        [5, None, ("--dev", test_data["aos8_ap"]["name"]), lambda r: "TX" in r, False],  # aos8
        [6, None, ("-S", "--dev", test_data["ap"]["name"]), lambda r: "AOS10" in r, False],  # test with aos10, swarm is only valid for AOS8...
        [7, None, ("--dev", test_data["ap"]["name"], "--group", test_data["ap"]["group"]), lambda r: "--group" in r, False],  # --group flag is ignored
        [8, None, ("--group", test_data["ap"]["group"]), lambda r: "TX" in r, False],  # --group flag is ignored
        [9, "ensure_cache_label1", ("--label", "cencli_test_label1"), lambda r: "API" in r, False],
        [10, None, ("-S", "--dev", test_data["gateway"]["name"]), lambda r: "only applies" in r, False],  # -S flag ignored as --dev is a gateway
        [11, None, ("-S",), lambda r: "--dev" in r, True], # -S but no --dev flag
    ]
)
def test_show_bandwidth_client(idx: int, fixture: str | None, args: tuple[str], pass_condition: Callable, expect_failure: bool, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["show", "bandwidth", "client", *args],)
    capture_logs(result, "test_show_bandwidth_client", expect_failure=expect_failure)
    assert result.exit_code == (0 if not expect_failure else 1)
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("switch", test_data["switch"]["mac"]), lambda r: "TX" in r],
        [2, ("switch", test_data["switch"]["mac"], "--uplink"), lambda r: "TX" in r],
        [3, ("switch", test_data["switch"]["mac"], "--uplink", "--yaml"), lambda r: "API" in r],
        [4, ("switch", test_data["switch"]["mac"], test_data["switch"]["test_ports"][-1]), lambda r: "TX" in r],
        [5, ("ap", test_data["ap"]["name"]), lambda r: "TX" in r],
        [6, ("ap", "--ssid", "ignored"), lambda r: "--ssid" in r and "TX" in r],
        [7, ("ap", "--band", "5"), lambda r: "--band" in r and "TX" in r],
        [8, ("ap", test_data["ap"]["name"], "--group", test_data["ap"]["group"]), lambda r: "--group" in r and "TX" in r],
        [9, ("ap", test_data["aos8_ap"]["name"], "--swarm"), lambda r: "TX" in r],
        [10, ("uplink", test_data["gateway"]["name"]), lambda r: "TX" in r],
        [11, ("uplink", test_data["gateway"]["name"], "--yaml"), lambda r: "TX" in r],
        [12, ("uplink", test_data["switch"]["name"]), lambda r: "TX" in r],
    ]
)
def test_show_bandwidth(idx: int, args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "bandwidth", *args],)
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("switch", test_data["switch"]["mac"]), lambda r: "API" in r],
    ]
)
def test_show_bandwidth_fail(idx: int, args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "bandwidth", *args],)
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_bandwidth_wlan():
    result = runner.invoke(app, ["show", "bandwidth", "wlan", test_data["tunneled_ssid"]["ssid"]],)
    capture_logs(result, "test_show_bandwidth_wlan")
    assert result.exit_code == 0
    assert "TX" in result.stdout


def test_show_bandwidth_wlan_w_dev():
    result = runner.invoke(app, ["show", "bandwidth", "wlan", test_data["tunneled_ssid"]["ssid"], "--swarm", test_data["ap"]["name"]],)
    capture_logs(result, "test_show_bandwidth_wlan_w_dev")
    assert result.exit_code == 0
    assert "API" in result.stdout or "TX" in result.stdout  # Empty response in mock data


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("wlan", test_data["tunneled_ssid"]["ssid"], "-S", test_data["ap"]["name"], "--site", test_data["ap"]["site"]), lambda r: "one of" in r],
        [2, ("ap", "--swarm", test_data["ap"]["name"]), lambda r: "--swarm" in r],
    ]
)
def test_show_bandwidth_invalid(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "bandwidth", *args],)
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args",
    [
        (),
        (test_data["gateway"]["site"],),
        ("--down",),
        ("--wan-down",),
    ]
)
def test_show_branch_health(args: tuple[str]):
    result = runner.invoke(app, ["show", "branch", "health", *args],)
    capture_logs(result, "test_show_branch_health")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,args,pass_condition,expect_failure",
    [
        [1, ("-S",), lambda r: "Ignoring" in r, False],  # also test warning for ignored -S (swarm) without dev
        [2, ("--yaml",), lambda r: "API" in r, False],
        [3, (test_data["ap"]["name"],),lambda r: "API" in r, False],
        [4, ("--ssid", "HPE_Aruba"),lambda r: "API" in r, False],
        [5, ("--group", test_data["ap"]["group"], "--site", test_data["ap"]["site"]), lambda r: "one of" in r, True],  # too many filters
    ]
)
def test_show_bssids(idx: int, args: tuple[str], pass_condition: Callable, expect_failure: bool):
    result = runner.invoke(app, ["show", "bssids", *args],)
    capture_logs(result, "test_show_bssids", expect_failure=expect_failure)
    assert result.exit_code == (0 if not expect_failure else 1)
    assert pass_condition(result.stdout)


# Output here will not be the same during mocked test run as it is outside of tests
# API returns csv, the Response.output attribute is converted in cloudauth.get_registered_macs()
# to list of dicts.  This is not done in the cleaner like most others. (To make the library more friendly when used outside CLI)
@pytest.mark.parametrize("idx,sort_by", [[1, "mac"], [2, None]])
def test_show_cloud_auth_registered_macs(idx: int, sort_by: str | None):
    args = [] if not sort_by else ["--sort", sort_by]
    result = runner.invoke(app, ["show", "cloud-auth", "registered-macs", *args],)
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert "MAC" in result.stdout


def test_show_cloud_auth_registered_macs_fail():
    result = runner.invoke(app, ["show", "cloud-auth", "registered-macs", "--sort", "mac"],)
    capture_logs(result, "test_show_cloud_auth_registered_macs_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "Response" in result.stdout


def test_show_cluster():
    result = runner.invoke(app, ["show", "cluster", test_data["tunneled_ssid"]["group"], test_data["tunneled_ssid"]["ssid"], "--sort", "invalid-sort-field"])  # also testing invalid sort field
    capture_logs(result, "test_show_cluster")
    assert result.exit_code == 0
    assert "Sort Error" in result.stdout


def test_show_cluster_ssid_not_exist():
    result = runner.invoke(app, ["show", "cluster", test_data["tunneled_ssid"]["group"], "not_exist_ssid"])
    capture_logs(result, "test_show_cluster_ssid_not_exist")
    assert result.exit_code == 0
    assert "not_exist" in result.stdout


@pytest.mark.parametrize(
    "pass_condition,test_name_update",
    [
        [lambda res: ("API" in res.stdout and res.exit_code == 1) or ("Partial Failure" in res.stdout and res.exit_code ==0), None],
        [lambda res: ("API" in res.stdout and res.exit_code == 1) or ("Partial Failure" in res.stdout and res.exit_code ==0), None],
        [lambda res: ("500" in res.stdout and res.exit_code == 1) or ("Partial Failure" in res.stdout and res.exit_code ==0), "first_call"],
    ]
)
def test_show_all_fail(pass_condition: Callable, test_name_update: str | None):
    if test_name_update:
        env.current_test = f"{env.current_test}_{test_name_update}"
    result = runner.invoke(app, ["show", "all"],)
    capture_logs(result, env.current_test, expect_failure="Partial Failure" not in result.stdout)
    assert pass_condition(result)


@pytest.mark.parametrize(
    "args",
    [
        ("--past", "32d"),
        ("609",),
        ("--site", test_data["ap"]["site"]),
        ("--dev", test_data["ap"]["name"]),
        ("--client", test_data["client"]["wireless"]["name"]),
        ("--severity", "low"),
    ]
)
def test_show_insights(args: tuple[str]):
    result = runner.invoke(app, ["show", "insights", *args],)
    capture_logs(result, "test_show_insights")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_no_dev_type():
    result = runner.invoke(
        app,
        [
            "test",
            "method",
            "get_aiops_insights",
            f"serial={test_data['ap']['serial']}"
        ]
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)


def test_show_insights_too_many_filters():
    config.debugv = True
    result = runner.invoke(
        app,
        [
            "test",
            "method",
            "get_aiops_insights",
            f"serial={test_data['ap']['serial']}",
            "site_id=7"
        ]
    )
    config.debugv = config.debug = False
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)


@pytest.mark.parametrize(
    "idx,glp_ok,args,pass_condition",
    [
        [1, False, ("--key", "EC5C0481E85EB4DB79"), lambda r: "mac" in r],
        [2, False, ("--sub",), lambda r: "mac" in r],
        [3, False, ("--no-sub",), lambda r: "mac" in r],
        [4, False, ("-v",), lambda r: "mac" in r],
        [1, True, ("--key", "EC5C0481E85EB4DB79"), lambda r: "mac" in r],
        [2, True, ("--sub",), lambda r: "mac" in r],
        [3, True, ("--no-sub",), lambda r: "mac" in r],
        [4, True, ("-v",), lambda r: "mac" in r],
    ]
)
def test_show_inventory(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable):
    if idx == 1:
        config._mock(glp_ok)
    env.current_test = f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}"
    result = runner.invoke(app, ["show", "inventory", *args],)
    capture_logs(result, f"{env.current_test}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,glp_ok,args,pass_condition,test_name_append",
    [
        [1, False, (), lambda r: "500" in r, None],
        [2, False, (), lambda r: "fetch subscription details failed" in r, "sub_call"],
        [1, True, (), lambda r: "500" in r, None],
        [2, True, (), lambda r: "fetch subscription details failed" in r, "sub_call"],
    ]
)
def test_show_inventory_fail(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    if idx == 1:
        config._mock(glp_ok)
    if test_name_append:  # pragma: no cover
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "inventory", *args],)
    capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}", expect_failure=True)
    assert result.exit_code <= 1  # classic #2 needs work to return exit code based on partial/sub-call failure
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition",
    [
        [1, (test_data["ap"]["name"], "--up"), lambda r: "mac" in r],
        [2, ("--site", test_data["ap"]["site"], "--sort", "utilization"), lambda r: "mac" in r and "band" in r],
    ]
)
def test_show_radios(_: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "radios", *args],)
    capture_logs(result, "test_show_radios")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition,test_name_append",
    [
        [1, (test_data["aos8_ap"]["name"],), lambda r: "Response" in r, None],
        [2, (test_data["ap"]["name"], test_data["aos8_ap"]["name"]), lambda r: "Partial Failure" in r, None],
    ]
)
def test_show_radios_fail(_: int, args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    # no cover: start
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    # no cover: stop
    result = runner.invoke(app, ["show", "radios", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("-sc",), lambda r: "API" in r],
        [2, (test_data["ap"]["site"],), lambda r: "API" in r],
    ]
)
def test_show_sites(idx: int, args: tuple[str], pass_condition: Callable):
    if idx % 2 == 1:
        cache.check_fresh(site_db=True)  # tests cached response
    result = runner.invoke(app, ["show", "sites", *args],)
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,pass_condition,test_name_append",
    [
        [1, lambda r: "ClientConnectorError" in r, "exception_client_connector_error"],
        [2, lambda r: "ContentLengthError" in r, "exception_client_content_length_error"],
    ]
)
def test_show_sites_fail(_: int, pass_condition: Callable, test_name_append: str | None):
    env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "sites"],)
    capture_logs(result, "test_show_sites_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_switch_by_ip():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["ip"], "--debug"],)
    capture_logs(result, "test_show_switch_by_ip")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_mac():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["mac"], "--debug"],)
    capture_logs(result, "test_show_switch_by_mac")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_serial():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["serial"], "--debug"],)
    capture_logs(result, "test_show_switch_by_serial")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_name():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["name"], "--debug"],)
    capture_logs(result, "test_show_ap_by_name")
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_ip():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["ip"], "--debug"],)
    capture_logs(result, "test_show_ap_by_ip")
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_serial():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["serial"], "--debug"],)
    capture_logs(result, "test_show_ap_by_serial")
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_name():
    result = runner.invoke(app, ["show", "gateways", test_data["gateway"]["name"], "--debug"],)
    capture_logs(result, "test_show_gateway_by_name")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition",
    [
        [1, None, ("all",), lambda r: "mac" in r and "serial" in r],
        [2, None, ("all", "-v"), lambda r: "mac" in r and "serial" in r and "uptime" in r],
        [3, None, ("all", "--inv", "--up"), lambda r: "Counts" in r],
        [4, "ensure_cache_label1", ("all", "--label", "cencli_test_label1"), lambda r: "API" in r],
        [5, None, ("aps", "--site", test_data["ap"]["site"]), lambda r: "API" in r],
        [6, None, ("aps", "--inv"), lambda r: "Counts" in r],
        [7, None, ("aps", "--debug", "--table"), lambda r: "site" in r and "status" in r],
        [8, None, ("devices", "all", "--up"), lambda r: "API" in r],
        [9, None, ("gateways", "--down", "--table"), lambda r: "name" in r and "API" in r],
        [10, None, ("switches", "--inv"), lambda r: "Counts" in r],
        [11, None, ("switches", "--up", "--sort", "ip"), lambda r: "API" in r],
        [12, None, ("switches", "--group", test_data["switch"]["group"]), lambda r: "API" in r],
        [13, None, ("switches", test_data["switch"]["name"], "--debug"), lambda r: "site" in r and "status" in r],
        [14, None, ("switches", test_data["switch"]["name"], "--inv"), lambda r: "site" in r and "status" in r],

    ]
)
def test_show_devices(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["show", *args])
    capture_logs(result, "test_show_devices")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


# TODO this will need to be folded into real command once show commands have ability to use cnx endpoints
@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, (), lambda r: "──" in r],
    ]
)
def test_show_devices_cnx(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["test", "command", *args])
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


def test_show_device_by_name():
    result = runner.invoke(app, ["show", "devices", test_data["switch"]["name"], "--debug"],)
    capture_logs(result, "test_show_device_by_name")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_ip():
    result = runner.invoke(app, ["show", "devices", test_data["ap"]["ip"], "--debug"],)
    capture_logs(result, "test_show_device_by_ip")
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_mac():
    result = runner.invoke(app, ["show", "devices", test_data["gateway"]["mac"], "--debug"],)
    capture_logs(result, "test_show_device_by_mac")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_serial():
    result = runner.invoke(app, ["show", "devices", test_data["switch"]["serial"], "--debug"],)
    capture_logs(result, "test_show_device_by_serial")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_dhcp_clients_gw():
    result = runner.invoke(app, ["show", "dhcp", "clients", test_data["dhcp_gateway"]["serial"], "--no-res"],)
    capture_logs(result, "test_show_dhcp_clients_gw")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_dhcp_clients_gw_verbose():
    result = runner.invoke(app, ["show", "dhcp", "clients", test_data["dhcp_gateway"]["name"], "-v"],)
    capture_logs(result, "test_show_dhcp_clients_gw_verbose")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_dhcp_pools_gw():
    result = runner.invoke(app, ["show", "dhcp", "pools", test_data["dhcp_gateway"]["ip"]],)
    capture_logs(result, "test_show_dhcp_pools_gw")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, (test_data["gateway"]["name"],), lambda r: test_data["gateway"]["name"] in r and "API" in r],
        [2, ("--group", test_data["gateway"]["group"].swapcase(), "--gw"), lambda r: "API" in r and "Counts" in r],
        [3, (test_data["ap"]["name"], "-v"), lambda r: "status" in r and "API" in r],
        [4, (test_data["ap"]["name"], "--down", "--group", "ingored"), lambda r: "name" in r and "⚠" in r],  # --group is ignored given device is provided
        [5, ("--site", test_data["ap"]["site"], "--ap", "--fast", "--slow"), lambda r: test_data["ap"]["name"][0:6] in r and "⚠" in r],  # ⚠ is for warning regarding --fast and --slow both being used
        [6, ("--site", test_data["ap"]["site"], "--ap", "--up", "--down"), lambda r: test_data["ap"]["name"][0:6] in r and "⚠" in r],  # ⚠ is for warning regarding --up and --down both being used
        [7, ("--site", test_data["ap"]["site"], "--ap", "--down", "--fast"), lambda r: "API" in r and "⚠" in r],  # ⚠ is for warning regarding --down and --fast both being used
        [8, (test_data["switch"]["name"], "--up", "--table"), lambda r: "vlan" in r and "status" in r],
        [9, (test_data["switch"]["name"], "--slow", "--table"), lambda r: "vlan" in r and "status" in r],
        [10, (test_data["switch"]["ip"], "--fast", "--table"), lambda r: "vlan" in r and "status" in r],
        [11, ("--group", test_data["switch"]["group"].swapcase(), "--switch"), lambda r: "API" in r and "Counts" in r],
        [12, ("--group", test_data["switch"]["group"].swapcase(), "--switch", "-v"), lambda r: "API" in r and "Counts" in r],

    ]
)
def test_show_interfaces(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "interfaces", *args],)
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "fixture,args,pass_condition,test_name_append",
    [
        [None, ("--ap", "--gw"), lambda r: "⚠" in r and "one of" in r.lower(), None],
        [None, (), lambda r: "⚠" in r and "one of" in r.lower(), None],
        ["ensure_cache_group2", ("--ap", "--group", "cencli_test_group2"), lambda r: "⚠" in r and "Combination" in r, None],
        ["ensure_cache_group2", ("--ap", "--group", "cencli_test_group2"), lambda r: "500" in r, "cache_refresh"],
    ]
)
def test_show_interfaces_fail(fixture: str | None | list[str], args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest, test_name_append: str | None):
    if fixture:
        request.getfixturevalue(fixture)
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "interfaces", *args],)
    capture_logs(result, "test_show_interfaces_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_cache():
    result = runner.invoke(app, ["show", "cache"],)
    capture_logs(result, "test_show_cache")
    assert result.exit_code == 0
    assert "devices" in result.stdout
    assert "sites" in result.stdout


def test_show_cache_tables():
    result = runner.invoke(app, ["show", "cache", "tables"],)
    capture_logs(result, "test_show_cache_tables")
    assert result.exit_code == 0
    assert "total" in result.stdout.lower()


def test_show_cache_devices_sites():
    result = runner.invoke(app, ["show", "cache", "devices", "sites"],)
    capture_logs(result, "test_show_cache_devices_sites")
    assert result.exit_code == 0
    assert "total" in result.stdout.lower()


def test_show_variables():
    result = runner.invoke(app, ["show", "variables", "all", "--table"],)  # Also tests logic that converts tablfmt to json
    capture_logs(result, "test_show_variables")
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_serial():
    result = runner.invoke(app, ["show", "variables", test_data["template_switch"]["serial"]],)
    capture_logs(result, "test_show_variables_by_serial")
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_name():
    result = runner.invoke(app, ["show", "variables", test_data["template_switch"]["name"].title()],)
    capture_logs(result, "test_show_variables_by_name")
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [(test_data["switch"]["site"], "--raw"), lambda r: "API" in r],
        [(test_data["gateway"]["mac"],), lambda r: "pvid" in r],
        [(test_data["vsf_switch"]["mac"], "--down"), lambda r: "pvid" in r],

    ]
)
def test_show_vlans(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "vlans", *args],)
    capture_logs(result, "test_show_vlans")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


def test_show_vlans_invalid_dev_type():
    result = runner.invoke(app, ["show", "vlans", test_data["ap"]["serial"]],)
    capture_logs(result, "test_show_vlans_invalid_dev_type", expect_failure=True)
    assert result.exit_code == 1
    assert "valid" in result.stdout


if config.dev.mock_tests:
    def test_show_task():
        result = runner.invoke(app, ["show", "task", "17580829600233"],)
        capture_logs(result, "test_show_task")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_show_task_invalid_expired():
        result = runner.invoke(app, ["show", "task", "17580829612345"],)
        capture_logs(result, "test_show_task_invalid_expired")
        assert result.exit_code == 0
        assert "invalid" in result.stdout
else:  # pragma: no cover
    ...


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition,test_name_append",
    [
        [1, None, (), lambda r: "group" in r and "version" in r, None],
        [2, None, ("group", test_data["template_switch"]["group"]), lambda r: "group" in r and "version" in r, None],
        [3, None, ("--dev-type", "sw"), lambda r: "group" in r, None],
        [4, None, (test_data["template_switch"]["name"].lower(),), lambda r: "BEGIN TEMPLATE" in r and "%_sys_hostname%" in r, None],
        [5, None, (test_data["template_switch"]["serial"],), lambda r: "BEGIN TEMPLATE" in r and "%_sys_hostname%" in r, None],
        [6,
            "ensure_cache_template_by_name",
            (
                test_data["template"]["name"].lower(), "--group", test_data["template"]["group"].upper()
            ),
            lambda r: "_sys_hostname%" in r and "_sys_ip_address%" in r,
            None
        ],
        [7, None, ("--dev-type", "cx"), lambda r: "None" in r and "template groups" in r.lower(), "no_template_groups"],
    ]
)
def test_show_templates(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest, test_name_append: str | None):
    if fixture:
        request.getfixturevalue(fixture)
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "templates", *args],)
    capture_logs(result, "test_show_templates")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition,test_name_append",
    [
        [1, (), lambda r: "400" in r, None],
        [2, ("--dev-type", "cx"), lambda r: "400" in r, "get_names"],
        [3, (), lambda r: "400" in r, "get_names"],
    ]
)
def test_show_templates_fail(_: int, args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "templates", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args",
    [
        ("cx", "--sort", "id"),
        ("cx", "--sort", "category"),
    ]
)
def test_show_ts_commands(args: tuple[str]):
    result = runner.invoke(app, ["show", "ts", "commands", *args])
    capture_logs(result, "test_show_ts_commands")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_ts_results():
    result = runner.invoke(app, ["show", "ts", "results", test_data["switch"]["name"]])
    capture_logs(result, "test_show_ts_results")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_lldp_by_ap_name():
    result = runner.invoke(app, ["show", "lldp", test_data["ap"]["name"].lower()],)
    capture_logs(result, "test_show_lldp_by_ap_name")
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "neighbor" in result.stdout


@pytest.mark.parametrize("args", [[test_data["gateway"]["name"]], [test_data["wlan_gw"]["name"]]])
def test_show_overlay_connection(args: list[str]):
    result = runner.invoke(app, ["show", "overlay", "connection", *args])
    capture_logs(result, "test_show_overlay_connection")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_overlay_interfaces():
    result = runner.invoke(app, ["show", "overlay", "interfaces", test_data["gateway"]["name"].lower()],)
    capture_logs(result, "test_show_overlay_interfaces")
    assert result.exit_code == 0
    assert "Routes" in result.stdout


@pytest.mark.parametrize("args", [(test_data["gateway"]["name"].lower(), "--best"), (test_data["gateway"]["name"].lower(),)])
def test_show_overlay_routes(args: tuple[str]):
    result = runner.invoke(app, ["show", "overlay", "routes", *args],)
    capture_logs(result, "test_show_overlay_routes")
    assert result.exit_code == 0
    assert "Routes" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        (["database", test_data["gateway"]["name"], "--debug", "--table"], lambda r: "Router ID" in r),
        (["database", test_data["wlan_gw"]["name"]], lambda r: "not enabled" in r),
        (["interfaces", test_data["gateway"]["name"]], lambda r: "Router ID" in r),
        (["interfaces", test_data["wlan_gw"]["name"]], lambda r: "not enabled" in r),
        (["neighbors", test_data["gateway"]["name"]], lambda r: "Router ID" in r),
        (["neighbors", test_data["wlan_gw"]["name"]], lambda r: "not enabled" in r),
        (["area", test_data["gateway"]["name"]], lambda r: "area" in r),
        (["area", test_data["wlan_gw"]["name"]], lambda r: "not enabled" in r),
    ]
)
def test_show_ospf(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, [
            "show",
            "ospf",
            *args
        ]
    )
    capture_logs(result, "test_show_ospf")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args",
    [
        [1, ("database", test_data["gateway"]["name"],)],
        [2, ("interfaces", test_data["gateway"]["name"])],
        [3, ("neighbors", test_data["gateway"]["name"])],
        [4, ("area", test_data["gateway"]["name"])],
    ]
)
def test_show_ospf_fail(idx: int, args: tuple[str]):
    result = runner.invoke(app, [
            "show",
            "ospf",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert "Response" in result.stdout


def test_show_overlay_routes_advertised():
    result = runner.invoke(app, [
            "show",
            "overlay",
            "routes",
            test_data["gateway"]["name"],
            "-a",
            "--debug",
            "--table"
        ]
    )
    assert result.exit_code == 0
    assert "nexthop" in result.stdout


@pytest.mark.parametrize(
    "_,args",
    [
        [1, ("--site", test_data["ap"]["site"].lower(), "--table")],
        [2, ("--site", test_data["ap"]["site"].lower(), "--up")],
        [3, ("--site", test_data["ap"]["site"].lower(), "--down")],
    ]
)
def test_show_ap_lldp_neighbors(_:int, args: tuple[str]):  #, pass_condition: Callable):
    result = runner.invoke(app, ["show", "aps", "-n", *args],)
    capture_logs(result, "test_show_ap_lldp_neighbors")
    assert result.exit_code == 0
    assert "ap" in result.stdout
    assert "API" in result.stdout


def test_show_all_ap_lldp_neighbors_no_site():
    result = runner.invoke(app, ["show", "aps", "-n"],)
    capture_logs(result, "test_show_all_ap_lldp_neighbors_no_site", expect_failure=True)
    assert result.exit_code == 1
    assert "site" in result.stdout


def test_show_cx_switch_lldp_neighbors():
    result = runner.invoke(app, ["show", "lldp", test_data["switch"]["mac"].lower(),],)
    capture_logs(result, "test_show_cx_switch_lldp_neighbors")
    assert result.exit_code == 0
    assert "chassis" in result.stdout
    assert "remote port" in result.stdout.replace("_", " ")


def test_show_cx_switch_stack_lldp_neighbors():
    result = runner.invoke(app, ["show", "lldp", test_data["vsf_switch"]["mac"],],)
    capture_logs(result, "test_show_cx_switch__stack_lldp_neighbors")
    assert result.exit_code == 0
    assert "chassis" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("--csv",),
        ("--yaml",),
    ]
)
def test_show_groups(args: tuple[str]):
    result = runner.invoke(app, ["show", "groups", *args],)
    assert result.exit_code == 0
    assert "allowed" in result.stdout
    assert "aos10" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition,test_name_append",
    [
        [(), lambda r: "500" in r, None],
        [(), lambda r: "Ignoring" in r and "comma" in r, "comma"],
    ]
)
def test_show_groups_fail(args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "groups", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition,test_name_update",
    [
        [1, ("--yaml", "--valid", "--svr"), lambda r: "expired" in r, None],
        [2, ("--ca",), lambda r: "⚠" in r, None],  # No data after applying filters
        [3, (), lambda r: "Empty" in r, "no_payload"],  # empty_response
        [4, ("aruba_default",), lambda r: "API" in r, None],
    ]
)
def test_show_certs(_: int, args: tuple[str], pass_condition: Callable, test_name_update: None | str):
    if test_name_update:
        env.current_test = f"{env.current_test}_{test_name_update}"
    result = runner.invoke(app, ["show", "certs", *args],)
    capture_logs(result, env.current_test)
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args,pass_condition",
    [
        [3, (), lambda r: "Response" in r],
    ]
)
def test_show_certs_fail(_: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "certs", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_labels():
    result = runner.invoke(app, ["show", "labels", "-r"],)
    capture_logs(result, "test_show_labels")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_last():
    result = runner.invoke(app, ["show", "last"],)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        (["--past", "5d"], lambda r: "Empty Response" in r or ("audit" in r and "id" in r)),
        (["1"], lambda r: "Empty Response" in r or "API" in r),
        (["audit_trail_2025_8,AZjC-zcQEfpkmc__0HZa"], lambda r: "Empty Response" in r or "API" in r),
        (["--all"], lambda r: "Empty Response" in r or "API" in r),
        (["--dev", test_data["ap"]["serial"], "-vv"], lambda r: "Empty Response" in r or "API" in r),
        (["--dev", test_data["ap"]["name"], "--group", "ignored"], lambda r: "ignored" in r and ("Empty Response" in r or "API" in r)),
        (["--group", test_data["ap"]["group"],], lambda r: "Empty Response" in r or "API" in r),
    ]
)
def test_show_audit_logs(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "audit", "logs", *args],)
    capture_logs(result, "test_show_audit_logs")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


sal = ["show", "audit", "logs"]
@pytest.mark.parametrize("args", [[*sal, "999"], [*sal, "not_an_int"]])
def test_show_audit_logs_invalid(args: list[str]):
    result = runner.invoke(app, args,)
    capture_logs(result, "test_show_audit_logs_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


@pytest.mark.parametrize("args", [("-n", "5"), ("-vv",)])
def test_show_audit_acp_logs(args: tuple[str]):
    result = runner.invoke(app, ["show", "audit", "acp-logs", *args],)
    capture_logs(result, "test_show_audit_acp_logs")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("--dev", test_data["ap"]["name"], "-S", "--past", "30m"), lambda r: "description" in r],
        [2, ("--dev", test_data["switch"]["name"], "-S", "--past", "30m"), lambda r: "description" in r],
        [3, ("--dev", test_data["switch"]["name"], "--start", "11/1/2025", "--past", "30m"), lambda r: "description" in r and "ignored" in r],  # --start ignored due to --past
        [4, ("--group", test_data["ap"]["group"], "--end", "12/31/2025", "--past", "30m"), lambda r: "description" in r and "ignored" in r],  # --end flag ignored due to --past
        [5, ("1", "--past", "30m"), lambda r: "299" in r],
        [6, ("-a", "--client", test_data["client"]["wireless"]["mac"]), lambda r: "200" in r],
        [7, ("-a", "--client", test_data["client"]["wireless"]["name"]), lambda r: "200" in r],
        [8, ("self",), lambda r: "INFO" in r],
        [9, ("pytest",), lambda r: "INFO" in r],
    ]
)
def test_show_logs(idx: int, args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "logs", *args,])
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("9999",), lambda r: "⚠" in r],
        [2, ("-a", "--past", "30m",), lambda r: "⚠" in r],
    ]
)
def test_show_logs_invalid(idx: int, args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "logs", *args,])
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_mpsk_networks():
    result = runner.invoke(app, ["show", "mpsk", "networks"],)
    capture_logs(result, "test_show_mpsk_networks")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition,test_name_append",
    [
        [1, None, (), lambda r: "API" in r, None],
        [2, "ensure_cache_mpsk_network", (), lambda r: "API" in r, "multiple_mpsk_nets"],
        [3, None, (test_data["mpsk_ssid"],), lambda r: "API" in r, None],
        [4, None, ("-E",), lambda r: "disabled" not in r, None],
        [5, None, ("-D",), lambda r: "enabled" not in r, None],
        [6, None, ("--import",), lambda r: "ssid argument is required" in r, None],
    ]
)
def test_show_mpsk_named(_: int, fixture: str | None, args: list[str], pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["show", "mpsk", "named", *args],)
    capture_logs(result, env.current_test)
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition,test_name_append",
    [
        [1, None, (), lambda r: "500" in r, "networks"],
        [2, None, (), lambda r: "500" in r, None],
        [3, "ensure_cache_mpsk_network", ("--import",), lambda r: "⚠" in r, None],
    ]
)
def test_show_mpsk_named_fail(_: int, fixture: str | None, args: list[str], pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["show", "mpsk", "named", *args],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_switch_vlans_by_name():
    result = runner.invoke(app, ["show", "vlans", test_data["switch"]["name"], "--table"],)
    capture_logs(result, "test_show_switch_vlans_by_name")
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "pvid" in result.stdout

@pytest.mark.parametrize(
    "args,pass_condition",
    [
        (["--up", "--group", test_data["vsf_switch"]["group"]], lambda r: "API" in r),
        ([test_data["vsf_switch"]["mac"]], lambda r: "API" in r),
    ]
)
def test_show_stacks(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "stacks", *args],)
    capture_logs(result, "test_show_stacks")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


def test_show_client_location_no_client():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "clients", "--location"],)
    capture_logs(result, "test_show_client_location_no_client", expect_failure=True)
    assert result.exit_code == 1
    assert "required" in result.stdout


def test_show_client_location():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "clients", "--location", test_data["client"]["wireless"]["mac"]],)
    capture_logs(result, "test_show_client_location")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_get_floor_details():
    cache.responses.client = None
    result = runner.invoke(app, ["test", "method", "get_floor_details", "5000692__ae78073d-a227-4c0e-9510-9f3002414304"],)
    capture_logs(result, "test_get_floor_details")
    assert result.exit_code == 0
    assert "floor" in result.stdout


cmac = test_data["client"]["wireless"]["mac"]
@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("--table",), lambda r: "name" in r and "mac" in r],
        [2, ("--table", "-w", "--band", "6"), lambda r: "name" in r and "mac" in r],
        [3, ("-w",), lambda r: "name" in r and "mac" in r],
        [4, ("--wired", "--table"), lambda r: "vlan" in r and "mac" in r],
        [5, ("--dev", test_data["vsf_switch"]["name"], "--sort", "last-connected"), lambda r: "API" in r],
        [6, (cmac,), lambda r: f'mac {clean_mac(cmac)}' in clean_mac(r)],
        [7, ("--dev", test_data["ap"]["name"], "--site", test_data["ap"]["site"]), lambda r: "ignored" in r and "API" in r],  # --site ignored
        [8, ("--failed", "--past", "1w"), lambda r: "past 1 week" in r and "API" in r],
    ]
)
def test_show_clients(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "clients", *args],)
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition,test_name_append",
    [
        [1, ("--group", test_data["ap"]["group"], "--site", test_data["ap"]["site"]), lambda r: "one of" in r, None],
        [2, (), lambda r: "API" in r, None],
        [3, (), lambda r: "⚠" in r, "wired"],
    ]
)
def test_show_clients_fail(idx: int, args: list[str], pass_condition: Callable, test_name_append: str | None):
    api.session.requests = []  # Clearing class var Session.requests did not work for some reason, this does.  Need requests cleared or first call is not run by itself
    cache.responses.client = None
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "clients", *args],)
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_denylisted():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "denylisted", "clients", test_data["ap"]["name"]],)  # "clients" is unnecessary and should be stripped
    capture_logs(result, "test_show_denylisted")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition",
    [
        [1, None, (test_data["gateway"]["group"], "--gw", "--out", f"{Path(__file__).parent.parent / 'config' / '.cache' / 'test_runner_gw_grp_config'}",), lambda r: "mgmt-user" in r and "!" in r],
        [2, None, (test_data["gateway"]["group"], "--gw"), lambda r: "mgmt-user" in r],
        [3, None, (test_data["gateway"]["name"],), lambda r: "firewall" in r],
        [4, None, (test_data["ap"]["group"], "--ap"), lambda r: "rule any any" in r],
        [5, None, (test_data["ap"]["name"],), lambda r: "wlan" in r],
        [6, None, (test_data["ap"]["group"], test_data["ap"]["name"], "--env"), lambda r: "per-ap" in r],
        [7, None, (test_data["template_switch"]["name"], "this-is-ignored"), lambda r: "Running" in r and "this-is-ignored" in r],  # Also tests branch logic that displays warning for ignored extra arg
        [8, None, ("cencli",), lambda r: "current_workspace" in r],
        [9, None, ("self", "-f"), lambda r: "client_id" in r],
        [10, None, ("self", "-v"), lambda r: "workspaces" in r],
        [11, "ensure_cache_group3", ("cencli_test_group3",), lambda r: "--ap" in r],  # no flag but --ap assumed as gw not allowed in group
        [12, None, (test_data["aos8_ap"]["name"], "--env"), lambda r: "per-ap-settings" in r],
        [13, None, (test_data["aos8_ap"]["serial"],), lambda r: "swarm" in r],
    ]
)
def test_show_config(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        if not config.dev.mock_tests:  # pragma: no cover
            return
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "config",
            *args
        ]
    )
    capture_logs(result, "test_show_config")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,fixture,args,pass_condition",
    [
        [1 ,None, (test_data["ap"]["group"],), lambda r: "⚠" in r],  # no --ap/--gw for group config
        [2 ,None, (test_data["ap"]["name"], test_data["switch"]["name"],), lambda r: "⚠" in r],  # multiple devs
        [3 ,None, (test_data["ap"]["name"], "--gw"), lambda r: "⚠" in r],  # ap dev but --gw flag
    ]
)
def test_show_config_fail(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:  # pragma: no cover
        if not config.dev.mock_tests:  # pragma: no cover
            return
        request.getfixturevalue(fixture)
    result = runner.invoke(
        app,
        [
            "show",
            "config",
            *args,
        ]
    )
    capture_logs(result, "test_show_config_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize("ensure_cache_group4", [True], indirect=True)
def test_show_config_gw_group_no_flag(ensure_cache_group4):
    result = runner.invoke(app, [
            "show",
            "config",
            "cencli_test_group4"
        ]
    )
    capture_logs(result, "test_show_config_gw_group_no_flag")
    assert result.exit_code == 0
    assert "--gw" in result.stdout


# separate from test_show_config as it has a specific response in the capture file
def test_show_config_sw_ui():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["switch"]["name"].replace("-", "_")
        ]
    )
    capture_logs(result, "test_show_config_sw_ui")
    assert result.exit_code == 0
    assert "Troubleshooting" in result.stdout



@pytest.mark.parametrize(
    "idx,args",
    [
        [1, (test_data["switch"]["ip"], "-p"),],
        [2, (test_data["switch"]["ip"], "1/1/6"),],
        [3, (test_data["template_switch"]["serial"],)],
    ]
)
def test_show_poe(idx: int, args: tuple[str]):
    result = runner.invoke(app, [
            "show",
            "poe",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [(), lambda r: "API" in r],
        [(test_data["portal"]["name"],), lambda r: test_data["portal"]["name"] in r],
        [(test_data["portal"]["name"], "--logo", str(config.cache_dir / "test_runner_portal_logo_download.png")), lambda r: "Logo saved" in r],
    ]
)
def test_show_portals(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, [
            "show",
            "portals",
            *args
        ]
    )
    capture_logs(result, "test_show_portals")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)
    if "--logo" in args:
        logo_file = Path(args[args.index("--logo") + 1])
        assert logo_file.exists()
        logo_file.unlink()



@pytest.mark.parametrize(
    "_,fixture,args,pass_condition",
    [
        [1, None, (test_data["portal"]["name"], "fake1", "fake2"), lambda r: "too many" in r.lower()],
        [2, "ensure_cache_portal", ("cencli-test", "-L"), lambda r: "unable to download" in r.lower()],
        [3, None, (test_data["portal"]["name"], "-L", "/root"), lambda r: "not writable" in r.lower()],
    ]
)
def test_show_portal_fail(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        if not config.dev.mock_tests:  # pragma: no cover
            return
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "portals",
            *args
        ]
    )
    capture_logs(result, "test_show_portal_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,args",
    [
        [1, ()],
        [2, ("-R",)],
        [3, (test_data["portal"]["name"],)],
    ]
)
def test_show_guests(_: int, args: tuple[str]):
    result = runner.invoke(app, [
            "show",
            "guests",
            *args
        ]
    )
    capture_logs(result, "test_show_guests")
    assert result.exit_code == 0
    assert test_data["portal"]["name"] in result.stdout or "Empty Response" in result.stdout


@pytest.mark.parametrize(
    "_,fixture,args,exit_code,pass_condition,test_name_append",
    [
        [1, "ensure_cache_no_defined_portals", (), 0, lambda r: "No portals" in r, "no_portals"],
        [2, "ensure_cache_no_defined_portals", ("-R",), 0, lambda r: "No portals" in r, "no_portals"],
        [3, None, (), 1, lambda r: "⚠" in r or "Response" in r, "partial_failure"],
        [4, None, (), 1, lambda r: "⚠" in r or "Response" in r, "first_call"],
    ]
)
def test_show_guests_fail(_: int, fixture: str | None, args: tuple[str], exit_code: int, pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    if test_name_append:  # pragma: no cover
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, [
            "show",
            "guests",
            *args
        ]
    )
    capture_logs(result, env.current_test, expect_failure=False if exit_code == 0 else True)
    assert result.exit_code == exit_code
    assert pass_condition(result.stdout)


def test_show_notifications():
    result = runner.invoke(app, [
            "show",
            "notifications",
        ]
    )
    capture_logs(result, "test_show_notifications")
    assert result.exit_code == 0
    assert "category" in result.stdout


@pytest.mark.parametrize(
    "idx,args,should_fail,test_name_append,pass_condition",
    [
        [1, (test_data["aos8_ap"]["name"],), False, None, None],
        [2, (test_data["aos8_ap"]["name"], test_data["ap"]["serial"]), False, None, None],
        [3, ("--group", test_data["aos8_ap"]["group"]), False, None, None],
        [4, ("--group", test_data["aos8_ap"]["group"]), False, None, None],
        [5, (), False, None, None],
        [6, (test_data["aos8_ap"]["name"], "--table"), False, "same_name", lambda r: "swarm name" not in r],
        [7, (test_data["aos8_ap"]["name"],), True, "fail", lambda r: "500" in r],
        [8, (test_data["ap"]["name"], test_data["aos8_ap"]["name"],), True, "fail", lambda r: "⚠" in r],  # partial failure
    ]
)
def test_show_firmware_swarm(idx: int, args: tuple[str], should_fail: bool, test_name_append: str | None, pass_condition: Callable):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, [
            "show",
            "firmware",
            "swarm",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=should_fail)
    assert result.exit_code == (0 if not should_fail else 1)
    assert "API" in result.stdout
    if pass_condition:
        assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args,pass_condition,test_name_append",
    [
        [(test_data["ap"]["name"], test_data["switch"]["name"],), None, None],
        [(test_data["ap"]["name"], test_data["switch"]["name"],), lambda r: "⚠" in r, "partial_failure"],  # Partial Failure
        [("--dev-type", "cx"), None, None],
        [("--dev-type", "ap"), None, None],
        [(test_data["switch"]["name"], "--dev-type", "ap"), lambda r: "--dev-type" in  r, None],  # warning ignore --dev-type
    ]
)
def test_show_firmware_device(args: tuple[str], pass_condition: Callable | None, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
            *args
        ]
    )
    capture_logs(result, "test_show_firmware_device")
    assert result.exit_code == 0
    if pass_condition:
        assert pass_condition(result.stdout)
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, (), lambda r: "--dev-type" in r],
        [2, (test_data["ap"]["name"], test_data["switch"]["name"]), lambda r: "Response" in r],
    ]
)
def test_show_firmware_device_fail(idx: int, args: tuple[str], pass_condition: Callable | None):
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args",
    [
        (test_data["switch"]["name"], "-v"),
        (test_data["aos8_ap"]["serial"], "-S", "--json"),
        (test_data["gateway"]["name"],),
        ("--dev-type", "cx"),

    ]
)
def test_show_firmware_list(args: tuple[str]):
    result = runner.invoke(app, [
            "show",
            "firmware",
            "list",
            *args
        ]
    )
    capture_logs(result, "test_show_firmware_list")
    assert result.exit_code == 0
    assert "API" in result.stdout


sfl = ["show", "firmware", "list"]
@pytest.mark.parametrize("args", [sfl, [*sfl, test_data["ap"]["name"], "--swarm-id", "asdf"]])
def test_show_firmware_list_invalid(args: list[str]):
    result = runner.invoke(app, args)
    capture_logs(result, "test_show_firmware_list_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


@pytest.mark.parametrize(
    "idx,fixture,args,pass_condition",
    [
        [1, "ensure_cache_group2", ("ap", "cencli_test_group2"), lambda r: "API" in r],
        [2, None, ("cx",), lambda r: "No compliance set" in r],
    ]
)
def test_show_firmware_compliance(idx: int, fixture: str | None, args: tuple[str], pass_condition: Callable | None, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "firmware",
            "compliance",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    if pass_condition:
        assert pass_condition(result.stdout)
    else:  # pragma: no cover
        ...


def test_show_firmware_compliance_invalid():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "compliance",
            "cx",
            test_data["ap"]["group"],
            test_data["switch"]["group"]
        ]
    )
    capture_logs(result, "test_show_firmware_compliance_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


@pytest.mark.parametrize(
    "args,should_pass,test_name_update",
    [
        [([test_data["client"]["wireless"]["name"], "--refresh"]), True, None],
        [([test_data["client"]["wireless"]["mac"]]), True, None],
        [([test_data["client"]["wireless"]["mac"]]), False, "fail"],
    ]
)
def test_show_roaming(args: list[str], should_pass: bool, test_name_update: None | str):
    if test_name_update:
        env.current_test = f"{env.current_test}_{test_name_update}"
    result = runner.invoke(app, [
            "show",
            "roaming",
            *args
        ]
    )
    capture_logs(result, env.current_test)
    assert result.exit_code == 0 if should_pass else 1
    assert "API" in result.stdout


def test_show_routes():
    result = runner.invoke(app, [
            "show",
            "routes",
            test_data["gateway"]["name"],
            "-r"
        ]
    )
    capture_logs(result, "test_show_routes")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_run_ap():
    result = runner.invoke(app, [
            "show",
            "run",
            test_data["ap"]["name"],
        ]
    )
    capture_logs(result, "test_show_run")
    assert result.exit_code == 0
    assert "version" in result.stdout


def test_show_run_cx():
    result = runner.invoke(app, [
            "show",
            "run",
            test_data["switch"]["serial"],
        ]
    )
    capture_logs(result, "test_show_run")
    assert result.exit_code == 0
    assert "Troubleshooting" in result.stdout


# There is no CLI command for this currently testing the API directly via test method command
def test_show_sdwan_dps_compliance():
    result = runner.invoke(app, [
            "test",
            "method",
            "get_sdwan_dps_policy_compliance",
        ]
    )
    capture_logs(result, "test_show_sdwan_dps_compliance")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_show_swarms():
    result = runner.invoke(app, [
            "show",
            "swarms",
            "--up"
        ]
    )
    capture_logs(result, "test_show_swarms")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_swarm_specific_ap():
    result = runner.invoke(app, [
            "show",
            "swarms",
            test_data["aos8_ap"]["name"],
            "--up",
            "--sort",
            "version"
        ]
    )  # --up and --sort are ignored in this case, given a specific AP is provided. Improves coverage/hits branch
    capture_logs(result, "test_show_swarm_specific_ap")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_swarm_config():
    result = runner.invoke(app, [
            "show",
            "swarms",
            test_data["aos8_ap"]["name"],
            "-c"
        ]
    )
    capture_logs(result, "test_show_swarm_config")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_swarm_invalid_aos10_ap():
    result = runner.invoke(app, [
            "show",
            "swarms",
            test_data["ap"]["name"]
        ]
    )
    capture_logs(result, "test_show_swarm_invalid_aos10_ap", expect_failure=True)
    assert result.exit_code == 1
    assert "AOS8" in result.stdout


def test_show_token():
    result = runner.invoke(app, [
            "show",
            "token"
        ]
    )
    capture_logs(result, "test_show_token")
    assert result.exit_code == 0
    assert "refresh" in result.stdout.lower()  # Attempting to Refresh Tokens
    assert "access" in result.stdout.lower()   # Access Token: ...


def test_show_upgrade_multi():
    result = runner.invoke(app, [
            "show",
            "upgrade",
            test_data["ap"]["name"],
            test_data["gateway"]["name"]
        ]
    )
    capture_logs(result, "test_show_upgrade_multi")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_upgrade_no_dev():
    result = runner.invoke(app, [
            "show",
            "upgrade",
            "status"
        ]
    )
    capture_logs(result, "test_show_upgrade_no_dev", expect_failure=True)
    assert result.exit_code == 1
    assert "required" in result.stdout


def test_show_uplinks():
    result = runner.invoke(app, [
            "show",
            "uplinks",
            test_data["gateway"]["name"]
        ]
    )
    capture_logs(result, "test_show_uplinks")
    assert result.exit_code == 0
    assert "uplink" in result.stdout.lower()

@pytest.mark.parametrize("mac", [True, False])
def test_show_cloud_auth_upload(mac: bool):
    args = [] if mac else ["mpsk"]  # default is mac
    result = runner.invoke(app, [
            "show",
            "cloud-auth",
            "upload",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}:{'mac' if mac else 'mpsk'}")
    assert result.exit_code == 0
    assert "200" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [("authentications", "--time-window", "3h"), lambda r: "API" in r],
        [("authentications", "--past", "3h"), lambda r: "API" in r],
        [("authentications", "--airpass",), lambda r: "API" in r],
        [("sessions", "--time-window", "3h"), lambda r: "API" in r],
        [("sessions", "--past", "3h"), lambda r: "API" in r],
        [("sessions", "--airpass",), lambda r: "API" in r],
    ]
)
def test_show_cloud_auth_sessions_authentications(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, [
            "show",
            "cloud-auth",
            *args
        ]
    )
    capture_logs(result, "test_show_cloud_auth_sessions_authentications")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("authentications",), lambda r: "412" in r],
        [2, ("sessions",), lambda r: "Response" in r],
    ]
)
def test_show_cloud_auth_sessions_authentications_fail(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, [
            "show",
            "cloud-auth",
            *args
        ]
    )
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,exit_code,pass_condition,test_name_append",
    [
        [1, 0, lambda r: "version" in r.lower(), None],
        [2, 1, lambda r: "version" in r.lower(), "fail"],
    ]
)
def test_show_version(_: int, exit_code: int, pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, [
            "show",
            "version"
        ]
    )
    capture_logs(result, env.current_test, expect_failure=False if exit_code == 0 else True)
    assert result.exit_code == exit_code
    assert pass_condition(result.output)


def test_show_tunnels():
    result = runner.invoke(app, [
            "show",
            "tunnels",
            test_data["gateway"]["name"],
            "--json"
        ]
    )
    capture_logs(result, "test_show_tunnels")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "idx,glp_ok,args,pass_condition",
    [
        [1, False, ("--csv",), lambda r: "status" in r],
        [2, True, ("--csv",), lambda r: "ounts" in r],
        [3, False, ("--sort", "end-date", "-r"), lambda r: "ounts" in r],
        [4, True, ("--sort", "end-date", "-r"), lambda r: "ounts" in r],
        [5, False, ("stats",), lambda r: "used" in r],
        [6, False, ("names",), lambda r: "advance" in r],
        [7, False, ("auto",), lambda r: "API" in r],
        [8, False, ("--dev-type", "switch"), lambda r: "ounts" in r],
        [9, True, ("--dev-type", "switch"), lambda r: "ounts" in r],
        [10, False, ("--type", "foundation-switch-6200"), lambda r: "foundation-switch" in r.lower()],  # response now comes back as Foundation-Switch-Class-2
        [11, True, ("--type", "foundation-switch-6200"), lambda r: "foundation-switch" in r.lower()],
    ]
)
def test_show_subscriptions(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    config._mock(glp_ok)
    env.current_test = f"{env.current_test}-{'glp' if glp_ok else 'classic'}"
    result = runner.invoke(app, ["show", "subscriptions", *args])
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


def test_show_vsx(ensure_dev_cache_test_vsx_switch: None):
    result = runner.invoke(app, [
            "show",
            "vsx",
            test_data["vsx_switch"]["serial"]
        ]
    )
    capture_logs(result, "test_show_vsx")
    assert result.exit_code == 0
    assert "config_sync" in result.stdout


def test_show_vsx_invalid_sw():
    result = runner.invoke(app, [
            "show",
            "vsx",
            test_data["template_switch"]["serial"]
        ]
    )
    capture_logs(result, "test_show_vsx_invalid_sw", expect_failure=True)
    assert result.exit_code == 1
    assert "only valid" in result.stdout


def test_show_webhooks():
    result = runner.invoke(app, [
            "show",
            "webhooks",
            "--sort",
            "token-created"
        ]
    )
    capture_logs(result, "test_show_webhooks")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "_,fixture,args",
    [
        [1, None, ()],
        [2, None, ("-v",)],
        [3, None, ("--group", test_data["ap"]["group"], "--csv")],
        [4, None, (test_data["tunneled_ssid"]["ssid"],)],
        [5, None, ("--swarm", test_data["aos8_ap"]["name"])],
        [6, None, ("--site", test_data["ap"]["site"])],
        [7, "ensure_cache_label1", ("--label", "cencli_test_label1")],
    ]
)
def test_show_wlans(_: int, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "wlans",
            *args
        ]
    )
    capture_logs(result, "test_show_wlans")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "fixture,args,pass_condition",
    [
        [None, ("--site", test_data["ap"]["site"], "-v"), lambda r: "not" in r],
        [None, ("--site", test_data["ap"]["site"], "--label", "cencli_test_label1"), lambda r: "Invalid" in r],  # too many flags
        ["ensure_cache_group2", ("--group", "cencli_test_group2"), lambda r: "template group" in r.lower()],
    ]
)
def test_show_wlans_invalid(fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "wlans",
            *args
        ]
    )
    capture_logs(result, "test_show_wlans_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_cron():
    result = runner.invoke(app, [
            "show",
            "cron",
        ]
    )
    capture_logs(result, "test_show_cron")
    assert result.exit_code == 0
    assert "cron.weekly" in result.stdout


def test_show_guest_summary():
    result = runner.invoke(app, [
            "test",
            "method",
            "get_guest_summary",
            test_data["portal"]["ssid"]
        ]
    )
    capture_logs(result, "test_show_guest_summary")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_show_guest_summary_invalid_days():
    result = runner.invoke(app, [
            "test",
            "method",
            "get_guest_summary",
            test_data["portal"]["ssid"],
            "days=30"
        ]
    )
    assert isinstance(result.exception, ValueError)
