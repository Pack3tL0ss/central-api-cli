from pathlib import Path
from typer.testing import CliRunner
import json

# you need to pip install -e centralcli from the root of the cloned repo
try:
    from cli import app  # type: ignore # NoQA
except (ImportError, ModuleNotFoundError):
    print('\nYou need to `pip install -e centralcli` from base directory\n')
    raise

runner = CliRunner()

test_dev_file = Path(__file__).parent / 'test_devices.json'
if test_dev_file.is_file():
    TEST_DEVICES = json.loads(test_dev_file.read_text())
else:
    raise UserWarning(f'\nYou need to populate {test_dev_file}\n')


def test_show_aps():
    result = runner.invoke(app, ["show", "aps", "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_all():
    result = runner.invoke(app, ["show", "all"],)
    assert result.exit_code == 0
    assert "mac" in result.stdout
    assert "serial" in result.stdout


def test_show_all_w_client_counts():
    """We Use csv output as rich will truncate cols and clients is last col

    tty size for test runner is 80 cols, 24 rows
    """
    result = runner.invoke(app, ["show", "all", "--clients", "--csv"],)
    assert result.exit_code == 0
    assert "serial" in result.stdout.splitlines()[0]
    assert "clients" in result.stdout.splitlines()[0]


def test_show_switch_by_name():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_ip():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_mac():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_serial():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_name():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["name"], "--debug"],)
    assert result.exit_code == 0
    # TODO show ap details not showing site???
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_ip():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_mac():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_serial():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_name():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_ip():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_mac():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_serial():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["serial"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_name():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["switch"]["name"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_ip():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["ap"]["ip"], "--debug"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_mac():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["gateway"]["mac"], "--debug"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_serial():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["switch"]["serial"], "--debug"],)
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
    result = runner.invoke(app, ["show", "variables", TEST_DEVICES["template_switch"]["serial"]],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_name():
    result = runner.invoke(app, ["show", "variables", TEST_DEVICES["template_switch"]["name"].title()],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "--group", TEST_DEVICES["template_switch"]["group"]],)
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_template_by_dev_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["template_switch"]["name"].lower()],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_dev_serial():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["template_switch"]["serial"]],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["template"]["name"].lower(), "--group", TEST_DEVICES["template"]["group"].upper()])
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_lldp_by_ap_name():
    result = runner.invoke(app, ["show", "lldp", TEST_DEVICES["ap"]["name"].lower()],)
    print(result.stdout)
    assert result.exit_code == 0
    assert "serial" in result.stdout
    assert "neighbor" in result.stdout


def test_show_groups():
    result = runner.invoke(app, ["show", "groups"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "template group" in result.stdout


def test_show_certs():
    result = runner.invoke(app, ["show", "certs"],)
    assert result.exit_code == 0
    assert "expired" in result.stdout
    assert "checksum" in result.stdout


def test_show_logs_past():
    result = runner.invoke(app, ["show", "logs", "--past", "5d"],)
    print(result.stdout)
    assert result.exit_code == 0
    if "Empty Response" in result.stdout:
        assert "Empty" in result.stdout
    else:
        assert "Audit Logs" in result.stdout
        assert "id" in result.stdout


def test_show_switch_vlans_by_name():
    result = runner.invoke(app, ["show", "vlans", TEST_DEVICES["switch"]["name"]],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "pvid" in result.stdout


def test_show_events_past():
    result = runner.invoke(app, ["show", "events", "--past", "30m"],)
    assert result.exit_code == 0
    assert "Event Logs" in result.stdout
    assert "description" in result.stdout


def test_show_clients():
    result = runner.invoke(app, ["show", "clients"],)
    assert result.exit_code == 0
    assert "All Clients" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wireless():
    result = runner.invoke(app, ["show", "clients", "--wireless"],)
    assert result.exit_code == 0
    assert "All Wireless Clients" in result.stdout
    assert "mac" in result.stdout


def test_show_clients_wired():
    result = runner.invoke(app, ["show", "clients", "--wired"],)
    assert result.exit_code == 0
    assert "All Wired Clients" in result.stdout
    assert "mac" in result.stdout


def test_show_client_by_mac():
    TEST_DEVICES["client_mac"] = TEST_DEVICES.get("client_mac", TEST_DEVICES["wlan_client_mac"])
    result = runner.invoke(app, ["show", "clients", TEST_DEVICES["client_mac"]],)
    assert result.exit_code == 0
    assert "role" in result.stdout
    assert f"mac: {TEST_DEVICES['wlan_client_mac']}" in result.stdout


def test_show_group_level_config():
    result = runner.invoke(app, [
            "show",
            "config",
            TEST_DEVICES["gateway"]["group"],
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
            TEST_DEVICES["gateway"]["name"],
            "--debug"
        ]
    )
    assert result.exit_code == 0
    assert "Router ID" in result.stdout


def test_show_overlay_routes_learned():
    result = runner.invoke(app, [
            "show",
            "overlay",
            "routes",
            TEST_DEVICES["gateway"]["name"],
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
            TEST_DEVICES["gateway"]["name"],
            "-a",
            "--debug"
        ]
    )
    assert result.exit_code == 0
    assert "nexthop" in result.stdout


def test_show_overlay_interfaces():
    result = runner.invoke(app, [
            "show",
            "overlay",
            "interfaces",
            TEST_DEVICES["gateway"]["name"],
            "--debug"
        ]
    )
    assert result.exit_code == 0
    assert "state" in result.stdout

