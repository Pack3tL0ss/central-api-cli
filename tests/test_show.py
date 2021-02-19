from pathlib import Path
from typer.testing import CliRunner
import json

# you need to pip install -e centralcli from base directory
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
    result = runner.invoke(app, ["show", "aps", "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout
    # self.switch_serial = result.stdout.splitlines()[-1].split()[8]
    # self.switch_name = result.stdout.splitlines()[-1].split()[6]
    # self.switch_mac = result.stdout.splitlines()[-1].split()[3]
    # self.switch_ip = result.stdout.splitlines()[-1].split()[2]


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways", "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_all():
    result = runner.invoke(app, ["show", "all", "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_name():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["name"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_ip():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["ip"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_mac():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["mac"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_serial():
    result = runner.invoke(app, ["show", "switches", TEST_DEVICES["switch"]["serial"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_name():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["name"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    # TODO show ap details not showing site???
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_ip():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["ip"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_mac():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["mac"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_serial():
    result = runner.invoke(app, ["show", "aps", TEST_DEVICES["ap"]["serial"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_name():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["name"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_ip():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["ip"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_mac():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["mac"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_serial():
    result = runner.invoke(app, ["show", "gateways", TEST_DEVICES["gateway"]["serial"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_name():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["switch"]["name"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_ip():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["ap"]["ip"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_mac():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["gateway"]["mac"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_serial():
    result = runner.invoke(app, ["show", "devices", TEST_DEVICES["switch"]["serial"], "--debug", "--no-pager"],)
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_cache():
    result = runner.invoke(app, ["show", "cache", "--no-pager"],)
    assert result.exit_code == 0
    assert "devices" in result.stdout
    assert "sites" in result.stdout


def test_show_variables():
    result = runner.invoke(app, ["show", "variables", "--no-pager"],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_serial():
    result = runner.invoke(app, ["show", "variables", TEST_DEVICES["switch"]["serial"], "--no-pager"],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_name():
    result = runner.invoke(app, ["show", "variables", TEST_DEVICES["switch"]["name"].title(), "--no-pager"],)
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "--group", TEST_DEVICES["switch"]["group"], "--no-pager"],)
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_template_by_dev_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["switch"]["name"].lower(), "--no-pager"],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_dev_serial():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["switch"]["serial"], "--no-pager"],)
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["template"]["name"].lower(), "--no-pager"],)
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_lldp_by_ap_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["ap"]["name"].lower(), "--no-pager"],)
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


def test_show_groups():
    result = runner.invoke(app, ["show", "groups", "--no-pager"],)
    assert result.exit_code == 0
    assert "name" in result.stdout
    assert "template group" in result.stdout


def test_show_certs():
    result = runner.invoke(app, ["show", "certs", "--no-pager"],)
    assert result.exit_code == 0
    assert "expired" in result.stdout
    assert "checksum" in result.stdout


# def test_show_snapshots_by_group():
#     result = runner.invoke(app, ["show", "snapshots", TEST_DEVICES["switch"]["group"]])
#     assert result.exit_code == 0
#     assert "name" in result.stdout
#     assert "created" in result.stdout
