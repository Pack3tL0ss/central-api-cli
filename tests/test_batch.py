import traceback

from rich import print
from rich.traceback import Traceback
from typer.testing import CliRunner

from centralcli.cli import app  # type: ignore # NoQA

from ._test_data import test_data, test_device_file, test_group_file, test_site_file

runner = CliRunner()


def test_batch_add_groups():
    result = runner.invoke(app, ["batch", "add",  "groups", str(test_group_file), "-Y"])
    assert result.exit_code == 0
    assert result.stdout.lower().count("created") == len(test_data["batch"]["groups_by_name"]) + 1  # Plus 1 as confirmation prompt includes "created"


def test_batch_add_sites():
    result = runner.invoke(app, ["batch", "add",  "sites", str(test_site_file), "-Y"])
    assert result.exit_code == 0
    assert "city" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout
    assert "state" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout


def test_batch_unarchive_devices():
    result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
    assert result.exit_code == 0
    assert "uccess" in result.stdout
    if result.exception:
        print(Traceback())
        traceback.print_exception(result.exception)


def test_batch_add_devices():
    result = runner.invoke(app, ["batch", "add",  "devices", f'{str(test_device_file)}', "-Y"])
    assert result.exit_code == 0
    assert "uccess" in result.stdout
    assert "200" in result.stdout  # /platform/device_inventory/v1/devices
    assert "201" in result.stdout  # /configuration/v1/preassign
    if result.exception:
        print(Traceback())
        traceback.print_exception(result.exception)
