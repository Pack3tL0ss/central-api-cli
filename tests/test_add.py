# from pathlib import Path
from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
# import json

# from . import TEST_DEVICES

runner = CliRunner()

# test_dev_file = Path(__file__).parent / 'test_devices.json'
# if test_dev_file.is_file():
#     TEST_DEVICES = json.loads(test_dev_file.read_text())


def test_add_group1():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group1", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group2_wired_tg():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group2", "--sw", "--wired-tg", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group3_wlan_tg():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group3", "--ap", "--wlan-tg", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group4_aos10_gw_wlan():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group4", "--ap", "--gw", "--aos10", "--gw-role", "wlan", "-Y"])
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]
