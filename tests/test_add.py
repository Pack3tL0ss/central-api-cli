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
    result = runner.invoke(app, ["add", "group",  "cencli_test_group1", "abcD1234", "-Y"])
    assert result.exit_code == 0
    assert "Created" in result.stdout


def test_add_group2_wired_tg():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group2", "abcD1234", "--wired-tg", "-Y"])
    assert result.exit_code == 0
    assert "Created" in result.stdout


def test_add_group3_wlan_tg():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group3", "abcD1234", "--wlan-tg", "-Y"])
    assert result.exit_code == 0
    assert "Created" in result.stdout
