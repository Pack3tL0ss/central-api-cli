from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
from . import TEST_DEVICES

runner = CliRunner()


# class Switch:
#     def __init__(self) -> None:
#         self.data = None
#         self.get_data()

#     def __getattr__(self, key: str):
#         if hasattr(self, key):
#             return getattr(self, key)
#         elif self.data and self.data.get(key):
#             return self.data[key]
#         else:
#             raise AttributeError(f"{self.__name__} object has no Attribute {key}")

#     def get_data(self):
#         cache = Identifires()
#         self.data = cache.DevDB.search(self.Q.type == "switch")


# class TestShow:
# def __init__(self) -> None:
#     self.switch = Switch()

def test_show_aps():
    result = runner.invoke(app, ["show", "aps", "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switches():
    result = runner.invoke(app, ["show", "switches", "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout
    # self.switch_serial = result.stdout.splitlines()[-1].split()[8]
    # self.switch_name = result.stdout.splitlines()[-1].split()[6]
    # self.switch_mac = result.stdout.splitlines()[-1].split()[3]
    # self.switch_ip = result.stdout.splitlines()[-1].split()[2]


def test_show_gateways():
    result = runner.invoke(app, ["show", "gateways", "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_all():
    result = runner.invoke(app, ["show", "all", "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_name():
    result = runner.invoke(app, ["show", "switch", TEST_DEVICES["switch"]["name"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_ip():
    result = runner.invoke(app, ["show", "switch", TEST_DEVICES["switch"]["ip"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_mac():
    result = runner.invoke(app, ["show", "switch", TEST_DEVICES["switch"]["mac"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_switch_by_serial():
    result = runner.invoke(app, ["show", "switch", TEST_DEVICES["switch"]["serial"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_name():
    result = runner.invoke(app, ["show", "ap", TEST_DEVICES["ap"]["name"], "--debug"])
    assert result.exit_code == 0
    # TODO show ap details not showing site???
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_ip():
    result = runner.invoke(app, ["show", "ap", TEST_DEVICES["ap"]["ip"], "--debug"])
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_mac():
    result = runner.invoke(app, ["show", "ap", TEST_DEVICES["ap"]["mac"], "--debug"])
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_ap_by_serial():
    result = runner.invoke(app, ["show", "ap", TEST_DEVICES["ap"]["serial"], "--debug"])
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_name():
    result = runner.invoke(app, ["show", "gateway", TEST_DEVICES["gateway"]["name"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_ip():
    result = runner.invoke(app, ["show", "gateway", TEST_DEVICES["gateway"]["ip"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_mac():
    result = runner.invoke(app, ["show", "gateway", TEST_DEVICES["gateway"]["mac"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_gateway_by_serial():
    result = runner.invoke(app, ["show", "gateway", TEST_DEVICES["gateway"]["serial"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_name():
    result = runner.invoke(app, ["show", "device", TEST_DEVICES["switch"]["name"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_ip():
    result = runner.invoke(app, ["show", "device", TEST_DEVICES["ap"]["ip"], "--debug"])
    assert result.exit_code == 0
    assert "model" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_mac():
    result = runner.invoke(app, ["show", "device", TEST_DEVICES["gateway"]["mac"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_device_by_serial():
    result = runner.invoke(app, ["show", "device", TEST_DEVICES["switch"]["serial"], "--debug"])
    assert result.exit_code == 0
    assert "site" in result.stdout
    assert "status" in result.stdout


def test_show_cache():
    result = runner.invoke(app, ["show", "cache"])
    assert result.exit_code == 0
    assert "devices" in result.stdout
    assert "sites" in result.stdout


def test_show_variables():
    result = runner.invoke(app, ["show", "variables"])
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_variables_by_name():
    result = runner.invoke(app, ["show", "variables", TEST_DEVICES["switch"]["serial"]])
    assert result.exit_code == 0
    assert "_sys_serial" in result.stdout
    assert "_sys_lan_mac" in result.stdout


def test_show_templates_by_group():
    result = runner.invoke(app, ["show", "templates", "--group", TEST_DEVICES["switch"]["group"]])
    assert result.exit_code == 0
    assert "group" in result.stdout
    assert "version" in result.stdout


def test_show_template_by_dev_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["switch"]["serial"].lower()])
    assert result.exit_code == 0
    assert "BEGIN TEMPLATE" in result.stdout
    assert "%_sys_hostname%" in result.stdout


def test_show_template_by_name():
    result = runner.invoke(app, ["show", "templates", TEST_DEVICES["template"]["name"].lower()])
    assert result.exit_code == 0
    assert "_sys_hostname%" in result.stdout
    assert "_sys_ip_address%" in result.stdout


# def test_show_snapshots_by_group():
#     result = runner.invoke(app, ["show", "snapshots", TEST_DEVICES["switch"]["group"]])
#     assert result.exit_code == 0
#     assert "name" in result.stdout
#     assert "created" in result.stdout
