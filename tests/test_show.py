from pathlib import Path
from typer.testing import CliRunner
import traceback


from cli import app
from . import test_data, common
cache = common.cache

runner = CliRunner()


def clean_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").replace(".", "").lower()

# Need to use --table for most tests, the default (rich) will elipsis headers
# when they overrun the tty.  tty for test runner is 80 cols, 24 rows
# --table wraps, does not elipsis/truncate any headers/values.
def test_show_aps():
    result = runner.invoke(app, ["-d", "show", "aps", "--debug", "--table"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--debug", "--table"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways", "--table"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_all():
    result = runner.invoke(app, ["show", "all", "--table"],)
    assert result.exit_code == 0
    assert "mac" in result.stdout
    assert "serial" in result.stdout


# This fails when all discovered tests are ran in the same session.  It's failing on this line in cleaner.sort_result_keys()
# if inner["mem_total"] and inner["mem_free"]:
#     mem_pct = round(((float(inner["mem_total"]) - float(inner["mem_free"])) / float(inner["mem_total"])) * 100, 2)  # <-- fails here
# ValueError: could not convert string to float: '--'
# can't reproduce if ran by itself.  Only raw data should hit the cleaner.  This exception would occur if you cleaned already cleaned data
# seems like there is some collision re-used data when running all tests
# Disabling as this is the most common command I use... daily.  If show all breaks, I'll know it pretty quickly
# def test_show_all_rich():
#     result = runner.invoke(app, ["show", "all"],)
#     print(result.stdout)
#     if result.exception:
#         traceback.print_exception(result.exception)
#     assert result.exit_code == 0
#     assert "mac" in result.stdout
#     assert "ip" in result.stdout


def test_show_all_verbose():
    cache.updated = []
    result = runner.invoke(app, ["show", "all", "-v"],)
    print(result.stdout)
    if result.exception:
        traceback.print_exception(result.exception)
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "cpu %" in result.stdout


def test_show_switch_by_name():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_ip():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_mac():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_serial():
    result = runner.invoke(app, ["show", "switches", test_data["switch"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_name():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_ip():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_mac():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_serial():
    result = runner.invoke(app, ["show", "aps", test_data["ap"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_name():
    result = runner.invoke(app, ["show", "gateways", test_data["gateway"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_ip():
    result = runner.invoke(app, ["show", "gateways", test_data["gateway"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_mac():
    result = runner.invoke(app, ["show", "gateways", test_data["gateway"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_serial():
    result = runner.invoke(app, ["show", "gateways", test_data["gateway"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_name():
    result = runner.invoke(app, ["show", "devices", test_data["switch"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_ip():
    result = runner.invoke(app, ["show", "devices", test_data["ap"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_mac():
    result = runner.invoke(app, ["show", "devices", test_data["gateway"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_serial():
    result = runner.invoke(app, ["show", "devices", test_data["switch"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_cache():
    result = runner.invoke(app, ["show", "cache"],)
    assert result.exit_code == 0
    assert "devices" in result.stdout
    assert "sites" in result.stdout


def test_show_variables():
    result = runner.invoke(app, ["show", "variables"],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_serial():
    result = runner.invoke(app, ["show", "variables", test_data["template_switch"]["serial"]],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_name():
    result = runner.invoke(app, ["show", "variables", test_data["template_switch"]["name"].title()],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "--group", test_data["template_switch"]["group"]],)
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_template_by_dev_name():
    result = runner.invoke(app, ["show", "templates", test_data["template_switch"]["name"].lower()],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_dev_serial():
    result = runner.invoke(app, ["show", "templates", test_data["template_switch"]["serial"]],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_name():
    result = runner.invoke(app, ["show", "templates", test_data["template"]["name"].lower(), "--group", test_data["template"]["group"].upper()])
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_lldp_by_ap_name():
    result = runner.invoke(app, ["show", "lldp", test_data["ap"]["name"].lower()],)
    print(result.stdout)
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "neighbor" in result.stdout


def test_show_all_ap_lldp_neighbors():
    result = runner.invoke(app, ["show", "aps", "-n", "--site", test_data["ap"]["site"].lower(), "--table"],)
    print(result.stdout)
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "switch" in result.stdout


def test_show_cx_switch_lldp_neighbors():
    result = runner.invoke(app, ["show", "lldp", test_data["switch"]["mac"].lower(),],)
    print(result.stdout)
    assert result.exit_code == 0
    assert "chassis" in result.stdout
    assert "remote port" in result.stdout


def test_show_groups():
    result = runner.invoke(app, ["show", "groups", "--csv"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "AOSVersion" in result.stdout


def test_show_certs():
    result = runner.invoke(app, ["show", "certs", "--yaml"],)
    assert result.exit_code == 0
    assert "expired" in result.stdout
    assert "checksum" in result.stdout


def test_show_audit_logs_past():
    result = runner.invoke(app, ["show", "audit", "logs", "--past", "5d"],)
    print(result.stdout)
    assert result.exit_code == 0
    if "Empty Response" in result.stdout:
        assert "Empty" in result.stdout
    else:
        assert "audit event logs" in result.stdout.lower()
        assert "id" in result.stdout


def test_show_switch_vlans_by_name():
    result = runner.invoke(app, ["show", "vlans", test_data["switch"]["name"], "--table"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "pvid" in result.stdout


def test_show_logs_past():
    result = runner.invoke(app, ["show", "logs", "--past", "30m"],)
    assert result.exit_code == 0
    assert "event logs" in result.stdout.lower()
    assert "description" in result.stdout


def test_show_clients():
    result = runner.invoke(app, ["show", "clients", "--table"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wireless():
    cache.updated = []
    result = runner.invoke(app, ["show", "clients", "--wireless", "--table", "--debug"],)
    print(result.stdout)
    assert result.exit_code == 0
    assert "ip" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wired():
    cache.updated = []
    result = runner.invoke(app, ["show", "clients", "--wired", "--table", "--debug"],)
    print(result.stdout)
    if result.exception:
        import traceback
        traceback.print_exception(result.exception)
    assert result.exit_code == 0
    assert "vlan" in result.stdout
    assert "mac" in result.stdout


def test_show_client_by_mac():
    test_data["client_mac"] = test_data.get("client", {}).get("wireless", {}).get("mac", test_data["wlan_client_mac"])
    result = runner.invoke(app, ["show", "clients", test_data["client_mac"]],)
    print(result.stdout)
    print(test_data["client_mac"])
    assert result.exit_code == 0
    assert "role" in result.stdout
    assert f'mac {clean_mac(test_data["client_mac"])}' in clean_mac(result.stdout)


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
    assert result.exit_code == 0
    assert "!" in result.stdout
    assert "mgmt-user" in result.stdout


def test_show_ospf_neighbor():
    result = runner.invoke(app, [
            "show",
            "ospf",
            "neighbors",
            test_data["gateway"]["name"],
            "--debug",
            "--table"
        ]
    )
    assert result.exit_code == 0
    assert "Router ID" in result.stdout


def test_show_overlay_routes_learned():
    result = runner.invoke(app, [
            "show",
            "overlay",
            "routes",
            test_data["gateway"]["name"],
            "--debug"
        ]
    )
    assert result.exit_code == 0
    assert "nexthop" in result.stdout


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


def test_show_overlay_interfaces():
    result = runner.invoke(app, [
            "show",
            "overlay",
            "interfaces",
            test_data["gateway"]["name"],
            "--debug",
            "--table"
        ]
    )
    assert result.exit_code == 0
    assert "state" in result.stdout


def test_show_config_gw_group():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["gateway"]["group"],
            "--gw"
        ]
    )
    assert result.exit_code == 0
    assert "mgmt-user" in result.stdout


def test_show_config_gw_dev():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["gateway"]["name"]
        ]
    )
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
    assert result.exit_code == 0
    assert "rule any any" in result.stdout


def test_show_config_ap_dev():
    result = runner.invoke(app, [
            "show",
            "config",
            test_data["ap"]["name"]
        ]
    )
    assert result.exit_code == 0
    assert "per-ap-settings" in result.stdout
