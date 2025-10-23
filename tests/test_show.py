from pathlib import Path
from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import cache
from centralcli.cli import api, app
from centralcli.client import Session

from . import capture_logs, clean_mac, config, test_data

runner = CliRunner()


# tty size is MonkeyPatched to 190, 55 the end result during pytest runs is 156, 31
# Not sure why but it's larger than the 80, 24 fallback which it was using.
def test_check_fw_available():
    result = runner.invoke(app, ["check", "firmware-available", "ap", "10.7.2.1_93286"],)
    capture_logs(result, "test_check_fw_available")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_show_alerts():
    result = runner.invoke(app, ["-d", "show", "alerts", "--debug"],)
    capture_logs(result, "test_show_alerts")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_aps():
    result = runner.invoke(app, ["show", "aps", "--debug", "--table"],)
    capture_logs(result, "test_show_aps")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


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


def test_show_bandwidth_uplink_gw():
    result = runner.invoke(app, ["show", "bandwidth", "uplink", test_data["gateway"]["name"]],)
    capture_logs(result, "test_show_bandwidth_uplink_gw")
    assert result.exit_code == 0
    assert "TX" in result.stdout


def test_show_bandwidth_uplink_switch():
    result = runner.invoke(app, ["show", "bandwidth", "uplink", test_data["switch"]["name"]],)
    capture_logs(result, "test_show_bandwidth_uplink_switch")
    assert result.exit_code == 0
    assert "TX" in result.stdout


def test_show_bandwidth_client():
    result = runner.invoke(app, ["show", "bandwidth", "client"],)
    capture_logs(result, "test_show_bandwidth_client")
    assert result.exit_code == 0
    assert "All" in result.stdout


def test_show_bandwidth_client_by_client():
    result = runner.invoke(app, ["show", "bandwidth", "client", test_data["client"]["wireless"]["mac"], "-S", "--dev", test_data["ap"]["name"], "--group", test_data["ap"]["group"]],)
    capture_logs(result, "test_show_bandwidth_client_by_client")
    assert result.exit_code == 0
    assert "ignored" in result.stdout  # -S --dev --group flags are ignored


def test_show_bandwidth_client_swarm_no_dev():
    result = runner.invoke(app, ["show", "bandwidth", "client", "-S"],)
    capture_logs(result, "test_show_bandwidth_client_swarm_no_dev", expect_failure=True)
    assert result.exit_code == 1
    assert "--dev" in result.stdout


def test_show_bandwidth_client_swarm():
    result = runner.invoke(app, ["show", "bandwidth", "client", "-S", "--dev", test_data["aos8_ap"]["name"]],)
    capture_logs(result, "test_show_bandwidth_client_swarm")
    assert result.exit_code == 0
    assert "API" in result.stdout or "TX" in result.stdout  # Empty response in mock data


def test_show_bandwidth_client_swarm_aos10():
    result = runner.invoke(app, ["show", "bandwidth", "client", "-S", "--dev", test_data["ap"]["name"]],)
    capture_logs(result, "test_show_bandwidth_client_swarm_aos10")
    assert result.exit_code == 0
    assert "AOS10" in result.stdout  # swarm is only valid for AOS8...


def test_show_bandwidth_client_dev_ap():
    result = runner.invoke(app, ["show", "bandwidth", "client", "--dev", test_data["ap"]["name"], "--group", test_data["ap"]["group"]],)
    capture_logs(result, "test_show_bandwidth_client_dev_ap")
    assert result.exit_code == 0
    assert "--group" in result.stdout  # --group flag is ignored


def test_show_bandwidth_client_group():
    result = runner.invoke(app, ["show", "bandwidth", "client", "--group", test_data["ap"]["group"]],)
    capture_logs(result, "test_show_bandwidth_client_group")
    assert result.exit_code == 0
    assert "TX" in result.stdout


def test_show_bandwidth_client_label(ensure_cache_label1: None):
    result = runner.invoke(app, ["show", "bandwidth", "client", "--label", "cencli_test_label1"],)
    capture_logs(result, "test_show_bandwidth_client_label")
    assert result.exit_code == 0
    assert "API" in result.stdout or "TX" in result.stdout  # Empty response in mock data


def test_show_bandwidth_client_gw():
    result = runner.invoke(app, ["show", "bandwidth", "client", "-S", "--dev", test_data["gateway"]["name"]],)
    capture_logs(result, "test_show_bandwidth_client_gw")
    assert result.exit_code == 0
    assert "only applies" in result.stdout  # -S flag ignored as --dev is a gateway

@pytest.mark.parametrize(
    "args,pass_condition",
    [
        (["switch", test_data["switch"]["mac"]], lambda r: "TX" in r),
        (["switch", test_data["switch"]["mac"], "--uplink"], lambda r: "TX" in r),
        (["switch", test_data["switch"]["mac"], test_data["switch"]["test_ports"][-1]], lambda r: "TX" in r),
        (["ap", test_data["ap"]["name"]], lambda r: "TX" in r),
        (["ap", "--ssid", "ignored"], lambda r: "--ssid" in r and "TX" in r),
        (["ap", "--band", "5"], lambda r: "--band" in r and "TX" in r),
        (["ap", test_data["ap"]["name"], "--group", test_data["ap"]["group"]], lambda r: "--group" in r and "TX" in r),
        (["ap", test_data["aos8_ap"]["name"], "--swarm"], lambda r: "TX" in r),
    ]
)
def test_show_bandwidth(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "bandwidth", *args],)
    capture_logs(result, "test_show_bandwidth")
    assert result.exit_code == 0
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


def test_show_bandwidth_too_many_flags():
    result = runner.invoke(app, ["show", "bandwidth", "wlan", test_data["tunneled_ssid"]["ssid"], "-S", test_data["ap"]["name"], "--site", test_data["ap"]["site"]],)
    capture_logs(result, "test_show_bandwidth_too_many_flags", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout


def test_show_branch_health():
    result = runner.invoke(app, ["show", "branch", "health"],)
    capture_logs(result, "test_show_branch_health")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_branch_health_for_site():
    result = runner.invoke(app, ["show", "branch", "health", test_data["gateway"]["site"]],)
    capture_logs(result, "test_show_branch_health_for_site")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_branch_health_down():
    result = runner.invoke(app, ["show", "branch", "health", "--down"],)
    capture_logs(result, "test_show_branch_health_down")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_branch_health_wan_down():
    result = runner.invoke(app, ["show", "branch", "health", "--wan-down"],)
    capture_logs(result, "test_show_branch_health_wan_down")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_bssids():
    result = runner.invoke(app, ["show", "bssids", "-S"],)  # also test warning for ignored -s without dev
    capture_logs(result, "test_show_bssids")
    assert result.exit_code == 0
    assert "Ignoring" in result.stdout


def test_show_bssids_yaml():
    result = runner.invoke(app, ["show", "bssids", "--yaml"],)  # also test warning for ignored -s without dev
    capture_logs(result, "test_show_bssids")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_bssids_by_ap():
    result = runner.invoke(app, ["show", "bssids", test_data["ap"]["name"]],)
    capture_logs(result, "test_show_bssids_by_ap")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_bssids_too_many_filters():
    result = runner.invoke(app, ["show", "bssids", "--group", test_data["ap"]["group"], "--site", test_data["ap"]["site"]],)
    capture_logs(result, "test_show_bssids_too_many_filters", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout


# Output here will not be the same during mocked test run as it is outside of tests
# API returns csv, the Response.output attribute is converted in cloudauth.get_registered_macs()
# to list of dicts.  This is not done in the cleaner like most others. (To make the library more friendly when used outside CLI)
def test_show_cloud_auth_registered_macs():
    result = runner.invoke(app, ["show", "cloud-auth", "registered-macs", "--sort", "mac"],)
    capture_logs(result, "test_show_cloud_auth_registered_macs")
    assert result.exit_code == 0
    assert "MAC" in result.stdout


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


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--group", test_data["switch"]["group"]],)
    capture_logs(result, "test_show_switches")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_switches_up():
    result = runner.invoke(app, ["show", "switches", "--up", "--sort", "ip"],)
    capture_logs(result, "test_show_switches_up")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways", "--up", "--table"],)
    capture_logs(result, "test_show_gateways")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_all():
    result = runner.invoke(app, ["show", "all"],)
    capture_logs(result, "test_show_all")
    assert result.exit_code == 0
    assert "mac" in result.stdout
    assert "serial" in result.stdout


@pytest.mark.parametrize(
    "pass_condition",
    [
        lambda res: ("API" in res.stdout and res.exit_code == 1) or ("Partial Failure" in res.stdout and res.exit_code ==0),
        lambda res: ("API" in res.stdout and res.exit_code == 1) or ("Partial Failure" in res.stdout and res.exit_code ==0),
    ]
)
def test_show_all_fail(pass_condition: Callable):
    result = runner.invoke(app, ["show", "all"],)
    capture_logs(result, "test_show_all", expect_failure="Partial Failure" not in result.stdout)
    assert pass_condition(result)


def test_show_insights():
    result = runner.invoke(app, ["show", "insights", "--past", "32d"],)
    capture_logs(result, "test_show_insights")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_by_id():
    result = runner.invoke(app, ["show", "insights", "609"],)
    capture_logs(result, "test_show_insights_by_id")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_by_site():
    result = runner.invoke(app, ["show", "insights", "--site", test_data["ap"]["site"]],)
    capture_logs(result, "test_show_insights_by_site")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_by_device():
    result = runner.invoke(app, ["show", "insights", "--dev", test_data["ap"]["name"]],)
    capture_logs(result, "test_show_insights_by_device")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_by_client():
    result = runner.invoke(app, ["show", "insights", "--client", test_data["client"]["wireless"]["name"]],)
    capture_logs(result, "test_show_insights_by_client")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_insights_low_severity():
    result = runner.invoke(app, [
            "show",
            "insights",
            "--severity",
            "low"
        ]
    )
    capture_logs(result, "test_show_insights_low_severity")
    assert result.exit_code == 0
    assert "API Rate Limit" in result.stdout


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


def test_show_inventory():
    result = runner.invoke(app, ["show", "inventory"],)
    capture_logs(result, "test_show_inventory")
    assert result.exit_code == 0
    assert "mac" in result.stdout


def test_show_inventory_failed_sub_call():
    result = runner.invoke(app, ["show", "inventory"],)
    capture_logs(result, "test_show_inventory_failed_sub_call")
    assert result.exit_code == 0
    assert "all to fetch subscription details failed" in result.stdout


def test_show_inventory_verbose():
    from centralcli.clitree.show.show import api as sapi
    Session.requests = api.session.requests = sapi.session.requests = []
    result = runner.invoke(app, ["show", "inventory", "-v"],)
    # capture_logs(result, "test_show_inventory_verbose")
    assert result.exit_code == 0  # verbose uses api.session.requests to determine exit code, which during test runs could have more than just the requests involved with this command.
    assert "mac" in result.stdout


def test_show_radios():
    result = runner.invoke(app, ["show", "radios", test_data["ap"]["name"]],)
    capture_logs(result, "test_show_radios")
    assert result.exit_code == 0
    assert "mac" in result.stdout


def test_show_radios_site():
    result = runner.invoke(app, ["show", "radios", "--site", test_data["ap"]["site"]],)
    capture_logs(result, "test_show_radios_site")
    assert result.exit_code == 0
    assert "mac" in result.stdout
    assert "band" in result.stdout


def test_show_all_verbose():
    cache.responses.dev = None  # Necessary as pytest treats all this as one session, so cache is already populated with clean data
    result = runner.invoke(app, ["show", "all", "-v"],)
    capture_logs(result, "test_show_all_verbose")
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "uptime" in result.stdout


def test_show_sites():
    cache.check_fresh(site_db=True)
    result = runner.invoke(app, ["show", "sites"],)  # also tests cached response
    capture_logs(result, "test_show_sites")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_site_by_name():
    result = runner.invoke(app, ["show", "sites", test_data["ap"]["site"]],)
    capture_logs(result, "test_show_site_by_name")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_switch_by_name():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["name"], "--debug"],)
    capture_logs(result, "test_show_switch_by_name")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


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

def test_show_devices_all_up():
    result = runner.invoke(app, ["show", "devices", "all", "--up"],)
    capture_logs(result, "test_show_device_all_up")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_devices_down():
    result = runner.invoke(app, ["show", "devices", "--down"],)
    capture_logs(result, "test_show_devices_down")
    assert result.exit_code == 0
    assert "API" in result.stdout


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


def test_show_interfaces_gw():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["gateway"]["name"]), "--table"],)
    capture_logs(result, "test_show_interfaces_gw")
    assert result.exit_code == 0
    assert "vlan" in result.stdout
    assert "status" in result.stdout


def test_show_interfaces_switch():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["switch"]["name"][0:-2]), "--table"],)
    capture_logs(result, "test_show_interfaces_switch")
    assert result.exit_code == 0
    assert "vlan" in result.stdout
    assert "status" in result.stdout


def test_show_interfaces_ap_up():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["ap"]["name"]), "--up"],)
    capture_logs(result, "test_show_interfaces_ap_up")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_interfaces_ap_down():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["ap"]["name"]), "--down", "--group", "ingored"],)
    capture_logs(result, "test_show_interfaces_ap_down")
    assert result.exit_code == 0
    assert "API" in result.stdout
    assert "gnored" in result.stdout  # --group is ignored given device is provided


def test_show_interfaces_switch_slow():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["switch"]["name"][0:-2]), "--slow"],)
    capture_logs(result, "test_show_interfaces_switch_slow")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_interfaces_switch_fast():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["switch"]["ip"]), "--fast"],)
    capture_logs(result, "test_show_interfaces_switch_fast")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_interfaces_site_aps():
    result = runner.invoke(app, ["show", "interfaces", "--site", test_data["ap"]["site"], "--ap", "--fast", "--slow"],)
    capture_logs(result, "test_show_interfaces_site_aps")
    assert result.exit_code == 0
    assert "".join(test_data["ap"]["name"][0:6]) in result.stdout
    assert "Contradictory" in result.stdout  # --fast and --slow contradict error is shown in caption


def test_show_interfaces_group_switches():
    result = runner.invoke(app, ["show", "interfaces", "--group", test_data["switch"]["group"].swapcase(), "--switch"],)
    capture_logs(result, "test_show_interfaces_group_switches")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_interfaces_group_gws():
    result = runner.invoke(app, ["show", "interfaces", "--group", test_data["gateway"]["group"].swapcase(), "--gw"],)
    capture_logs(result, "test_show_interfaces_group_gws")
    assert result.exit_code == 0
    assert test_data["gateway"]["name"] in result.stdout


def test_show_interfaces_invalid_flags():
    result = runner.invoke(app, ["show", "interfaces", "--ap", "--gw"],)
    capture_logs(result, "test_show_interfaces_invalid_flags", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout


def test_show_interfaces_invalid_all_no_type():
    result = runner.invoke(app, ["show", "interfaces"],)
    capture_logs(result, "test_show_interfaces_invalid_all_no_type", expect_failure=True)
    assert result.exit_code == 1
    assert "one of" in result.stdout.lower()


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


def test_show_vlans_site():
    result = runner.invoke(app, ["show", "vlans", test_data["switch"]["site"], "--raw"],)
    capture_logs(result, "test_show_vlans_site")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_vlans_gw():
    result = runner.invoke(app, ["show", "vlans", test_data["gateway"]["mac"]],)
    capture_logs(result, "test_show_vlans_gw")
    assert result.exit_code == 0
    assert "pvid" in result.stdout


def test_show_vlans_stack():
    result = runner.invoke(app, ["show", "vlans", test_data["vsf_switch"]["mac"]], "--down",)
    capture_logs(result, "test_show_vlans_stack")
    assert result.exit_code == 0
    assert "pvid" in result.stdout


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


if config.dev.mock_tests:
    def test_show_task_invalid_expired():
        result = runner.invoke(app, ["show", "task", "17580829612345"],)
        capture_logs(result, "test_show_task_invalid_expired")
        assert result.exit_code == 0
        assert "invalid" in result.stdout


def test_show_templates_all():
    result = runner.invoke(app, ["show", "templates"],)
    capture_logs(result, "test_show_templates_all")
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "group", test_data["template_switch"]["group"]],)
    capture_logs(result, "test_show_templates_by_group")
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_templates_dev_type():
    result = runner.invoke(app, ["show", "templates", "--dev-type", "sw"],)
    capture_logs(result, "test_show_templates_dev_type")
    assert result.exit_code == 0
    assert "group" in result.stdout


def test_show_template_by_dev_name():
    result = runner.invoke(app, ["show", "templates", test_data["template_switch"]["name"].lower()],)
    capture_logs(result, "test_show_template_by_dev_name")
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_dev_serial():
    result = runner.invoke(app, ["show", "templates", test_data["template_switch"]["serial"]],)
    capture_logs(result, "test_show_template_by_dev_serial")
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_name(ensure_cache_template_by_name: None):
    result = runner.invoke(app, ["show", "templates", test_data["template"]["name"].lower(), "--group", test_data["template"]["group"].upper()])
    capture_logs(result, "test_show_template_by_name")
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_ts_commands():
    result = runner.invoke(app, ["show", "ts", "commands", "cx", "--sort", "id"])
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

sfl = ["show", "overlay", "connection"]
@pytest.mark.parametrize("args", [[*sfl, test_data["gateway"]["name"]], [*sfl, test_data["wlan_gw"]["name"]]])
def test_show_overlay_connection(args: list[str]):
    result = runner.invoke(app, args,)
    capture_logs(result, "test_show_overlay_connection")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_overlay_interfaces():
    result = runner.invoke(app, ["show", "overlay", "interfaces", test_data["gateway"]["name"].lower()],)
    capture_logs(result, "test_show_overlay_interfaces")
    assert result.exit_code == 0
    assert "Routes" in result.stdout


def test_show_overlay_routes():
    result = runner.invoke(app, ["show", "overlay", "routes", test_data["gateway"]["name"].lower(), "--best"],)
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


def test_show_all_ap_lldp_neighbors():
    result = runner.invoke(app, ["show", "aps", "-n", "--site", test_data["ap"]["site"].lower(), "--table"],)
    capture_logs(result, "test_show_all_ap_lldp_neighbors")
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "switch" in result.stdout


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
        ("--csv",),
        ("--yaml",),
    ]
)
def test_show_groups(args: tuple[str]):
    result = runner.invoke(app, ["show", "groups", *args],)
    assert result.exit_code == 0
    assert "allowed_types" in result.stdout
    assert "aos10" in result.stdout


def test_show_certs():
    result = runner.invoke(app, ["show", "certs", "--yaml"],)
    assert result.exit_code == 0
    assert "expired" in result.stdout


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
        (["--dev", test_data["ap"]["serial"]], lambda r: "Empty Response" in r or "API" in r),
        (["--dev", test_data["ap"]["name"], "--group", "ignored"], lambda r: "ignored" in r and ("Empty Response" in r or "API" in r)),
        (["--group", test_data["ap"]["group"]], lambda r: "Empty Response" in r or "API" in r),
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


def test_show_audit_acp_logs_count():
    result = runner.invoke(app, ["show", "audit", "acp-logs", "-n", "5"],)
    capture_logs(result, "test_show_audit_acp_logs_count")
    assert result.exit_code == 0
    if "Empty Response" not in result.stdout and "no data" not in result.stdout.lower():
        assert "acp audit logs" in result.stdout.lower()
        assert "id" in result.stdout


sfl = ["show", "logs", "--past", "30m"]
@pytest.mark.parametrize("args", [sfl, [*sfl, "--dev", test_data["ap"]["name"], "-S"], [*sfl, "--dev", test_data["switch"]["name"], "-S"], [*sfl, "--group", test_data["ap"]["group"]]])
def test_show_logs(args: list[str]):
    result = runner.invoke(app, args,)
    capture_logs(result, "test_show_logs")
    assert result.exit_code == 0
    assert "event logs" in result.stdout.lower()
    assert "description" in result.stdout


def test_show_logs_by_id():
    result = runner.invoke(app, ["show", "logs", "1"],)
    capture_logs(result, "test_show_logs_by_id")
    assert result.exit_code == 0
    assert "Response" in result.stdout


sfl = ["show", "logs", "-a", "--client"]
@pytest.mark.parametrize("args", [[*sfl, test_data["client"]["wireless"]["mac"]], [*sfl, test_data["client"]["wireless"]["name"]]])
def test_show_logs_client(args: list[str]):
    result = runner.invoke(app, args,)
    capture_logs(result, "test_show_logs_client")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_show_logs_self():
    result = runner.invoke(app, ["show", "logs", "self"],)
    capture_logs(result, "test_show_logs_self")
    assert result.exit_code == 0
    assert "INFO" in result.stdout


def test_show_logs_pytest():
    result = runner.invoke(app, ["show", "logs", "pytest"],)
    capture_logs(result, "test_show_logs_pytest")
    assert result.exit_code == 0
    assert "INFO" in result.stdout


def test_show_logs_invalid():
    result = runner.invoke(app, ["show", "logs", "-a", "--past", "30m"],)
    capture_logs(result, "test_show_logs_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "\u26a0" in result.stdout


def test_show_mpsk_networks():
    result = runner.invoke(app, ["show", "mpsk", "networks"],)
    capture_logs(result, "test_show_mpsk_networks")
    assert result.exit_code == 0
    assert "API" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        ([], lambda r: "API" in r),
        ([test_data["mpsk_ssid"]], lambda r: "API" in r),
        (["-E"], lambda r: "disabled" not in r),
        (["-D"], lambda r: "enabled" not in r),
        (["--import"], lambda r: "ssid argument is required" in r)
    ]
)
def test_show_mpsk_named(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "mpsk", "named", *args],)
    capture_logs(result, "test_show_mpsk_named")
    assert result.exit_code == 0
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
    "args,pass_condition",
    [
        (["--table"], lambda r: "name" in r and "mac" in r),
        (["--table", "-w", "--band", "6"], lambda r: "name" in r and "mac" in r),
        (["--wired", "--table"], lambda r: "vlan" in r and "mac" in r),
        (["--dev", test_data["vsf_switch"]["name"], "--sort", "last-connected"], lambda r: "API" in r),
        ([cmac], lambda r: f'mac {clean_mac(cmac)}' in clean_mac(r)),
        (["--dev", test_data["ap"]["name"], "--site", test_data["ap"]["site"]], lambda r: "ignored" in r and "API" in r),  # site is ignored
    ]
)
def test_show_clients(args: list[str], pass_condition: Callable):
    result = runner.invoke(app, ["show", "clients", *args],)
    capture_logs(result, "test_show_clients")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        (["--group", test_data["ap"]["group"], "--site", test_data["ap"]["site"]], lambda r: "one of" in r),
        ([], lambda r: "API" in r)
    ]
)
def test_show_clients_fail(args: list[str], pass_condition: Callable):
    api.session.requests = []  # Clearing class var Session.requests did not work for some reason, this does.  Need requests cleared or first call is not run by itself
    cache.responses.client = None
    result = runner.invoke(app, ["show", "clients", *args],)
    capture_logs(result, "test_show_clients_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_show_denylisted():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "denylisted", "clients", test_data["ap"]["name"]],)  # "clients" is unnecessary and should be stripped
    capture_logs(result, "test_show_denylisted")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_group_level_config():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["gateway"]["group"],
            "--gw",
            "--out",
            f"{Path(__file__).parent.parent / 'config' / '.cache' / 'test_runner_gw_grp_config'}",
            "--debug"
        ]
    )
    capture_logs(result, "test_show_group_level_config")
    assert result.exit_code == 0
    assert "!" in result.stdout
    assert "mgmt-user" in result.stdout


def test_show_config_gw_group():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["gateway"]["group"],
            "--gw"
        ]
    )
    capture_logs(result, "test_show_config_gw_group")
    assert result.exit_code == 0
    assert "mgmt-user" in result.stdout


def test_show_config_gw_dev():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["gateway"]["name"]
        ]
    )
    capture_logs(result, "test_show_config_gw_dev")
    assert result.exit_code == 0
    assert "firewall" in result.stdout


def test_show_config_ap_group():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["group"],
            "--ap"
        ]
    )
    capture_logs(result, "test_show_config_ap_group")
    assert result.exit_code == 0
    assert "rule any any" in result.stdout


def test_show_config_ap_dev():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["name"]
        ]
    )
    capture_logs(result, "test_show_config_ap_dev")
    assert result.exit_code == 0
    assert "wlan" in result.stdout


def test_show_config_ap_env_w_group():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["group"],
            test_data["ap"]["name"],
            "--env"
        ]
    )
    capture_logs(result, "test_show_config_ap_env_w_group")
    assert result.exit_code == 0
    assert "per-ap" in result.stdout


def test_show_config_group_no_type():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["group"]
        ]
    )
    capture_logs(result, "test_show_config_group_no_type", expect_failure=True)
    assert result.exit_code == 1
    assert "nvalid" in result.stdout


def test_show_config_invalid_2_devs():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["name"],
            test_data["switch"]["name"],
        ]
    )
    capture_logs(result, "test_show_config_invalid_2_devs", expect_failure=True)
    assert result.exit_code == 1
    assert "nvalid" in result.stdout


def test_show_config_invalid_ap_w_gw_flag():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["name"],
            "--gw",
        ]
    )
    capture_logs(result, "test_show_config_invalid_ap_w_gw_flag", expect_failure=True)
    assert result.exit_code == 1
    assert "nvalid" in result.stdout


def test_show_config_group_no_type_ap_only_group(ensure_cache_group3: None):
    result = runner.invoke(app, [
            "show",
            "config",
            "cencli_test_group3"
        ]
    )
    capture_logs(result, "test_show_config_group_no_type_ap_only_group")
    assert result.exit_code == 0
    assert "--ap" in result.stdout
    assert "hash" in result.stdout


def test_show_config_sw_tg():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["template_switch"]["name"],
            "this-is-ignored",  # test branch logic that displays warning for ignored extra arg

        ]
    )
    capture_logs(result, "test_show_config_sw_tg")
    assert result.exit_code == 0
    assert "TEMPLATE" in result.stdout
    assert "this-is-ignored" in result.stdout


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


def test_show_config_cencli():  # output is yaml
    result = runner.invoke(app, [
            "show",
            "config",
            "cencli",
        ]
    )
    capture_logs(result, "test_show_config_cencli")
    assert result.exit_code == 0
    assert "current_workspace" in result.stdout


def test_show_config_cencli_file():
    result = runner.invoke(app, [
            "show",
            "config",
            "self",
            "-f"
        ]
    )
    capture_logs(result, "test_show_config_cencli_file")
    assert result.exit_code == 0
    assert "client_id" in result.stdout


def test_show_config_cencli_verbose():  # output is yaml
    result = runner.invoke(app, [
            "show",
            "config",
            "cencli",
            "-v"
        ]
    )
    capture_logs(result, "test_show_config_cencli_verbose")
    assert result.exit_code == 0
    assert "workspaces" in result.stdout


def test_show_poe():
    result = runner.invoke(app, [
            "show",
            "poe",
            test_data["switch"]["ip"],
            "-p"
        ]
    )
    capture_logs(result, "test_show_poe")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_portals():
    result = runner.invoke(app, [
            "show",
            "portals"
        ]
    )
    capture_logs(result, "test_show_portals")
    assert result.exit_code == 0
    assert "name" in result.stdout or "Empty Response" in result.stdout


def test_show_portal_by_name():
    result = runner.invoke(app, [
            "show",
            "portals",
            test_data["portal"]["name"]
        ]
    )
    capture_logs(result, "test_show_portal_by_name")
    assert result.exit_code == 0
    assert test_data["portal"]["name"] in result.stdout


def test_show_portal_too_many_args():
    result = runner.invoke(app, [
            "show",
            "portals",
            test_data["portal"]["name"],
            "fake1",
            "fake2"
        ]
    )
    capture_logs(result, "test_show_portal_too_many_args", expect_failure=True)
    assert result.exit_code == 1
    assert "too many" in result.stdout.lower()


def test_show_guests():
    result = runner.invoke(app, [
            "show",
            "guests",
        ]
    )
    capture_logs(result, "test_show_guests")
    assert result.exit_code == 0
    assert test_data["portal"]["name"] in result.stdout or "Empty Response" in result.stdout


def test_show_guests_for_portal():
    result = runner.invoke(app, [
            "show",
            "guests",
            test_data["portal"]["name"]
        ]
    )
    capture_logs(result, "test_show_guests_for_portal")
    assert result.exit_code == 0
    assert test_data["portal"]["name"] in result.stdout or "Empty Response" in result.stdout


def test_show_notifications():
    result = runner.invoke(app, [
            "show",
            "notifications",
        ]
    )
    capture_logs(result, "test_show_notifications")
    assert result.exit_code == 0
    assert "category" in result.stdout


def test_show_firmware_swarm():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "swarm",
            test_data["aos8_ap"]["name"],
        ]
    )
    capture_logs(result, "test_show_firmware_swarm")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_swarm_multi():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "swarm",
            test_data["aos8_ap"]["name"],
            test_data["ap"]["serial"]
        ]
    )
    capture_logs(result, "test_show_firmware_swarm_multi")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_swarm_by_group():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "swarm",
            "--group",
            test_data["aos8_ap"]["group"],
        ]
    )
    capture_logs(result, "test_show_firmware_swarm_by_group")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_device_multi():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
            test_data["ap"]["name"],
            test_data["switch"]["name"],
        ]
    )
    capture_logs(result, "test_show_firmware_device_multi")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_device_dev_type_cx():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
            "--dev-type",
            "cx",
        ]
    )
    capture_logs(result, "test_show_firmware_dev_type_cx")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_device_dev_type_ap():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
            "--dev-type",
            "ap",
        ]
    )
    capture_logs(result, "test_show_firmware_dev_type_ap")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_firmware_device_no_args():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "device",
        ]
    )
    capture_logs(result, "test_show_firmware_device_no_args", expect_failure=True)
    assert result.exit_code == 1
    assert "--dev-type" in result.stdout


def test_show_firmware_list_verbose():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "list",
            test_data["switch"]["name"],
            "-v"
        ]
    )
    capture_logs(result, "test_show_firmware_list_verbose")
    assert result.exit_code == 0
    assert "API" in result.stdout

sfl = ["show", "firmware", "list"]
@pytest.mark.parametrize("args", [sfl, [*sfl, test_data["ap"]["name"], "--swarm-id", "asdf"]])
def test_show_firmware_list_invalid(args: list[str]):
    result = runner.invoke(app, args)
    capture_logs(result, "test_show_firmware_list_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


def test_show_firmware_compliance_raw():
    result = runner.invoke(app, [
            "show",
            "firmware",
            "compliance",
            "cx",
            test_data["switch"]["group"],
            "--raw"
        ]
    )
    capture_logs(result, "test_show_firmware_compliance_raw")
    assert result.exit_code == 0


@pytest.mark.parametrize(
    "args",
    [
        ([test_data["client"]["wireless"]["name"], "--refresh"]),
        ([test_data["client"]["wireless"]["mac"]]),
    ]
)
def test_show_roaming(args: list[str]):
    result = runner.invoke(app, [
            "show",
            "roaming",
            *args
        ]
    )
    capture_logs(result, "test_show_roaming")
    assert result.exit_code == 0
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


def test_show_cloud_auth_upload_mac():
    result = runner.invoke(app, [
            "show",
            "cloud-auth",
            "upload",
        ]  # default is mac
    )
    capture_logs(result, "test_show_cloud_auth_upload_mac")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_show_version():
    result = runner.invoke(app, [
            "show",
            "version"
        ]
    )
    capture_logs(result, "test_show_version")
    assert result.exit_code == 0
    assert "version" in result.stdout.lower()


def test_show_subscriptions_auto():
    result = runner.invoke(app, [
            "show",
            "subscriptions",
            "auto"
        ]
    )
    capture_logs(result, "test_show_subscriptions_auto")
    assert result.exit_code == 0


def test_show_tunnels():
    result = runner.invoke(app, [
            "show",
            "tunnels",
            test_data["gateway"]["name"]
        ]
    )
    capture_logs(result, "test_show_tunnels")
    assert result.exit_code == 0
    assert "API" in result.stdout

base = ["show", "subscriptions"]
@pytest.mark.parametrize("args", (base, [*base, "--sort", "end-date", "-r"],))
def test_show_subscriptions_details(args: list[str]):  # glp
    result = runner.invoke(app, args)
    capture_logs(result, "test_show_subscriptions_details")
    assert result.exit_code == 0


def test_show_subscription_stats():
    result = runner.invoke(app, [
            "show",
            "subscriptions",
            "stats",
        ]
    )
    capture_logs(result, "test_show_subscription_stats")
    assert result.exit_code == 0
    assert "used" in result.stdout


def test_show_subscription_names():
    result = runner.invoke(app, [
            "show",
            "subscriptions",
            "names",
        ]
    )
    capture_logs(result, "test_show_subscription_names")
    assert result.exit_code == 0
    assert "advance" in result.stdout


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


def test_show_wlans():
    result = runner.invoke(app, [
            "show",
            "wlans",
        ]
    )
    capture_logs(result, "test_show_wlans")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_verbose():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "-v"
        ]
    )
    capture_logs(result, "test_show_wlans_verbose")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_group():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--group",
            test_data["ap"]["group"]
        ]
    )
    capture_logs(result, "test_show_wlans_by_group")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_name():
    result = runner.invoke(app, [
            "show",
            "wlans",
            test_data["tunneled_ssid"]["ssid"]
        ]
    )
    capture_logs(result, "test_show_wlans_by_name")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_swarm():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--swarm",
            test_data["aos8_ap"]["name"]
        ]
    )
    capture_logs(result, "test_show_wlans_by_swarm")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_site():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--site",
            test_data["ap"]["site"]
        ]
    )
    capture_logs(result, "test_show_wlans_by_site")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_label(ensure_cache_label1: None):
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--label",
            "cencli_test_label1"
        ]
    )
    capture_logs(result, "test_show_wlans_by_label")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_wlans_by_site_verbose_invalid():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--site",
            test_data["ap"]["site"],
            "-v"
        ]
    )
    capture_logs(result, "test_show_wlans_by_site_verbose_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "not" in result.stdout


def test_show_wlans_too_many_flags():
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--site",
            test_data["ap"]["site"],
            "--label",
            "cencli_test_label1"
        ]
    )
    capture_logs(result, "test_show_wlans_too_many_flags", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_show_wlans_by_tg_invalid(ensure_cache_group2: None):
    result = runner.invoke(app, [
            "show",
            "wlans",
            "--group",
            "cencli_test_group2"
        ]
    )
    capture_logs(result, "test_show_wlans_by_tg_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "template group" in result.stdout.lower()


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
