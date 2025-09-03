from pathlib import Path

from typer.testing import CliRunner

from centralcli import cache
from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


def clean_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").replace(".", "").lower()

# tty size is MonkeyPatched to 190, 55 the end result during pytest runs is 156, 31
# Not sure why but it's larger than the 80, 24 fallback which it was using.
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


def test_show_archived():
    result = runner.invoke(app, ["show", "archived"],)
    capture_logs(result, "test_show_archived")
    assert result.exit_code == 0
    assert "API" in result.stdout


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


# Output here will not be the same during mocked test run as it is outside of tests
# API returns csv, the Response.output attribute is converted in cloudauth.get_registered_macs()
# to list of dicts.  This is not done in the cleaner like most others. (To make the library more friendly when used outside CLI)
def test_show_cloud_auth_registered_macs():
    result = runner.invoke(app, ["show", "cloud-auth", "registered-macs"],)
    capture_logs(result, "test_show_cloud_auth_registered_macs")
    assert result.exit_code == 0
    assert "MAC" in result.stdout


def test_show_cluster():
    result = runner.invoke(app, ["show", "cluster", test_data["tunneled_ssid"]["group"], test_data["tunneled_ssid"]["ssid"]], "--debugv")
    capture_logs(result, "test_show_cluster")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--debug", "--table"],)
    capture_logs(result, "test_show_switches")
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways", "--table"],)
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


def test_show_inventory():
    result = runner.invoke(app, ["show", "inventory"],)
    capture_logs(result, "test_show_inventory")
    assert result.exit_code == 0
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
    result = runner.invoke(app, ["show", "sites"],)
    capture_logs(result, "test_show_sites")
    assert result.exit_code == 0
    assert "site" in result.stdout.lower()


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


def test_show_interfaces_switch():
    result = runner.invoke(app, ["show", "interfaces", "".join(test_data["switch"]["name"][0:-2]), "--table"],)
    capture_logs(result, "test_show_interfaces_switch")
    assert result.exit_code == 0
    assert "vlan" in result.stdout
    assert "status" in result.stdout


def test_show_interfaces_site_aps():
    result = runner.invoke(app, ["show", "interfaces", "--site", test_data["ap"]["site"], "--ap"],)
    capture_logs(result, "test_show_interfaces_site_aps")
    assert result.exit_code == 0
    assert "".join(test_data["ap"]["name"][0:6]) in result.stdout
    assert "mac" in result.stdout


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
    result = runner.invoke(app, ["show", "variables"],)
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


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "--group", test_data["template_switch"]["group"]],)
    capture_logs(result, "test_show_templates_by_group")
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


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


def test_show_template_by_name():
    result = runner.invoke(app, ["show", "templates", test_data["template"]["name"].lower(), "--group", test_data["template"]["group"].upper()])
    capture_logs(result, "test_show_template_by_name")
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_ts_commands():
    result = runner.invoke(app, ["show", "ts", "commands", "cx"])
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


def test_show_all_ap_lldp_neighbors():
    result = runner.invoke(app, ["show", "aps", "-n", "--site", test_data["ap"]["site"].lower(), "--table"],)
    capture_logs(result, "test_show_all_ap_lldp_neighbors")
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "switch" in result.stdout


def test_show_cx_switch_lldp_neighbors():
    result = runner.invoke(app, ["show", "lldp", test_data["switch"]["mac"].lower(),],)
    capture_logs(result, "test_show_cx_switch_lldp_neighbors")
    assert result.exit_code == 0
    assert "chassis" in result.stdout
    assert "remote port" in result.stdout.replace("_", " ")


def test_show_groups():
    result = runner.invoke(app, ["show", "groups", "--csv"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "aos10" in result.stdout


def test_show_certs():
    result = runner.invoke(app, ["show", "certs", "--yaml"],)
    assert result.exit_code == 0
    assert "expired" in result.stdout


def test_show_audit_logs_past():
    result = runner.invoke(app, ["show", "audit", "logs", "--past", "5d"],)
    capture_logs(result, "test_show_audit_logs_past")
    assert result.exit_code == 0
    if "Empty Response" not in result.stdout and "No Data" not in result.stdout:
        assert "audit" in result.stdout.lower()
        assert "id" in result.stdout


def test_show_audit_logs_by_id():
    result = runner.invoke(app, ["show", "audit", "logs", "1"],)
    capture_logs(result, "test_show_audit_logs_by_id")
    assert result.exit_code == 0
    if "Empty Response" not in result.stdout and "No Data" not in result.stdout:
        assert "Response" in result.stdout


def test_show_audit_logs_invalid_id():
    result = runner.invoke(app, ["show", "audit", "logs", "999"],)
    assert result.exit_code == 1
    assert "nable to gather" in result.stdout


def test_show_audit_acp_logs_count():
    result = runner.invoke(app, ["show", "audit", "acp-logs", "-n", "5"],)
    capture_logs(result, "test_show_audit_acp_logs_count")
    assert result.exit_code == 0
    if "Empty Response" not in result.stdout and "no data" not in result.stdout.lower():
        assert "acp audit logs" in result.stdout.lower()
        assert "id" in result.stdout


def test_show_logs_past():
    result = runner.invoke(app, ["show", "logs", "--past", "30m"],)
    capture_logs(result, "test_show_logs_past")
    assert result.exit_code == 0
    assert "event logs" in result.stdout.lower()
    assert "description" in result.stdout


def test_show_logs_by_id():
    result = runner.invoke(app, ["show", "logs", "1"],)
    capture_logs(result, "test_show_logs_by_id")
    assert result.exit_code == 0
    assert "Response" in result.stdout


def test_show_mpsk_networks():
    result = runner.invoke(app, ["show", "mpsk", "networks"],)
    capture_logs(result, "test_show_mpsk_networks")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_mpsk_named():
    result = runner.invoke(app, ["show", "mpsk", "named", test_data["mpsk_ssid"]],)
    capture_logs(result, "test_show_mpsk_named")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_switch_vlans_by_name():
    result = runner.invoke(app, ["show", "vlans", test_data["switch"]["name"], "--table"],)
    capture_logs(result, "test_show_switch_vlans_by_name")
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "pvid" in result.stdout


def test_show_clients_too_many_filters():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "clients", "--group", test_data["ap"]["group"], "--site", test_data["ap"]["site"]],)
    assert result.exit_code == 1
    assert "one of" in result.stdout


def test_show_clients():
    result = runner.invoke(app, ["show", "clients", "--table"],)
    capture_logs(result, "test_show_clients")
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wireless():
    cache.responses.client = None
    result = runner.invoke(app, ["show", "clients", "--wireless", "--table", "--debug"],)
    capture_logs(result, "test_show_clients_wireless")
    assert result.exit_code == 0
    assert "ip" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wired():
    cache.updated = []
    result = runner.invoke(app, ["show", "clients", "--wired", "--table", "--debug"],)
    capture_logs(result, "test_show_clients_wired")
    assert result.exit_code == 0
    assert "vlan" in result.stdout
    assert "mac" in result.stdout


def test_show_client_by_mac():
    mac = test_data["client"]["wireless"]["mac"]
    result = runner.invoke(app, ["show", "clients", mac],)
    capture_logs(result, f"test_show_client_by_mac ({mac})")
    assert result.exit_code == 0
    assert "role" in result.stdout
    assert f'mac {clean_mac(mac)}' in clean_mac(result.stdout)


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


# FIXME killing these tests as there is a problem with the API endpoint
# error: The requested URL was not found on the server. If you entered the URL  ... even when testing from swagger
# def test_show_ospf_neighbor():
#     result = runner.invoke(app, [
#             "show",
#             "ospf",
#             "neighbors",
#             test_data["gateway"]["name"],
#             "--debug",
#             "--table"
#         ]
#     )
#     assert result.exit_code == 0
#     assert "Router ID" in result.stdout


# def test_show_overlay_routes_learned():
#     result = runner.invoke(app, [
#             "show",
#             "overlay",
#             "routes",
#             test_data["gateway"]["name"],
#             "--debug"
#         ]
#     )
#     assert result.exit_code == 0
#     assert "nexthop" in result.stdout


# def test_show_overlay_routes_advertised():
#     result = runner.invoke(app, [
#             "show",
#             "overlay",
#             "routes",
#             test_data["gateway"]["name"],
#             "-a",
#             "--debug",
#             "--table"
#         ]
#     )
#     assert result.exit_code == 0
#     assert "nexthop" in result.stdout


# def test_show_overlay_interfaces():
#     result = runner.invoke(app, [
#             "show",
#             "overlay",
#             "interfaces",
#             test_data["gateway"]["name"],
#             "--debug",
#             "--table"
#         ]
#     )
#     assert result.exit_code == 0
#     assert "state" in result.stdout


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
            test_data["portal"]["name"]
        ]
    )
    capture_logs(result, "test_show_guests")
    assert result.exit_code == 0
    assert test_data["portal"]["name"] in result.stdout or "Empty Response" in result.stdout


def test_show_insights():
    result = runner.invoke(app, [
            "show",
            "insights",
        ]
    )
    capture_logs(result, "test_show_insights")
    assert result.exit_code == 0
    assert "API Rate Limit" in result.stdout


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


def test_show_insights_site():
    result = runner.invoke(app, [
            "show",
            "insights",
            "--site",
            test_data["ap"]["site"]
        ]
    )
    capture_logs(result, "test_show_insights_site")
    assert result.exit_code == 0
    assert "API Rate Limit" in result.stdout


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


def test_show_roaming():
    result = runner.invoke(app, [
            "show",
            "roaming",
            test_data["client"]["wireless"]["name"],
            "--refresh"
        ]
    )
    capture_logs(result, "test_show_roaming")
    assert result.exit_code == 0
    assert "API" in result.stdout


def test_show_run():
    result = runner.invoke(app, [
            "show",
            "run",
            test_data["ap"]["name"],
        ]
    )
    capture_logs(result, "test_show_run")
    assert result.exit_code == 0
    assert "version" in result.stdout


def test_show_swarms():
    result = runner.invoke(app, [
            "show",
            "swarms"
        ]
    )
    capture_logs(result, "test_show_swarms")
    assert result.exit_code == 0
    assert "API" in result.stdout


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


def test_show_subscriptions_details():  # glp
    result = runner.invoke(app, [
            "show",
            "subscriptions"
        ]
    )
    capture_logs(result, "test_show_subscriptions_details")
    assert result.exit_code == 0


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
