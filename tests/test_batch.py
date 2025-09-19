from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.exceptions import InvalidConfigException

from . import capture_logs, config
from ._test_data import test_data, test_device_file, test_group_file, test_rename_aps_file, test_site_file, test_sub_file_csv, test_sub_file_yaml, test_verify_file

runner = CliRunner()


def test_batch_add_groups():
    result = runner.invoke(app, ["batch", "add",  "groups", str(test_group_file), "-Y"])
    capture_logs(result, "test_batch_add_groups")
    assert result.exit_code == 0
    assert result.stdout.lower().count("created") == len(test_data["batch"]["groups_by_name"]) + 1  # Plus 1 as confirmation prompt includes "created"


def test_batch_add_macs():
    result = runner.invoke(app, ["batch", "add",  "macs", test_data["cloud_auth"]["mac_file"], "-Y"])
    capture_logs(result, "test_batch_add_macs")
    assert result.exit_code == 0
    assert "202" in result.stdout


def test_batch_add_sites():
    result = runner.invoke(app, ["batch", "add",  "sites", str(test_site_file), "-Y"])
    capture_logs(result, "test_batch_add_sites")
    assert result.exit_code == 0
    assert "city" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout
    assert "state" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout


def test_batch_unarchive_devices():
    result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
    capture_logs(result, "test_batch_unarchive_device")
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_batch_add_devices():
    result = runner.invoke(app, ["batch", "add",  "devices", f'{str(test_device_file)}', "-Y"])
    capture_logs(result, "test_batch_add_device")
    assert result.exit_code == 0
    assert "uccess" in result.stdout
    assert "200" in result.stdout  # /platform/device_inventory/v1/devices
    assert "201" in result.stdout  # /configuration/v1/preassign


def test_batch_assign_subscriptions_with_tags_yaml():
    result = runner.invoke(app, ["batch", "assign", "subscriptions", f'{str(test_sub_file_yaml)}', "--tags", "testtag1", "=", "testval1,", "testtag2=testval2", "--debug", "-d", "-Y"])
    if config.is_old_cfg:
        assert isinstance(result.exception, InvalidConfigException)
    else:
        capture_logs(result, "test_batch_assign_subscriptions_with_tags_yaml")
        assert result.exit_code == 0
        assert result.stdout.count("code: 202") == 2


def test_batch_assign_subscriptions_csv():
    result = runner.invoke(app, ["batch", "assign", "subscriptions", f'{str(test_sub_file_csv)}', "-d", "-Y"])
    if config.is_old_cfg:
        assert isinstance(result.exception, InvalidConfigException)
    else:
        capture_logs(result, "test_batch_assign_subscriptions_csv")
        assert result.exit_code == 0
        assert result.stdout.count("code: 202") >= 2


def test_batch_move_no_import_file():
    result = runner.invoke(app, ["batch", "move",  "devices",])
    capture_logs(result, "test_batch_move_too_many_args", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_batch_move_too_many_args():
    result = runner.invoke(app, ["batch", "move",  "devices", f'{str(test_device_file)}', f'{str(test_rename_aps_file)}', "--label"])
    capture_logs(result, "test_batch_move_too_many_args", expect_failure=True)
    assert result.exit_code == 1
    assert "oo many" in result.stdout


def test_batch_rename_aps():
    result = runner.invoke(app, ["batch", "rename",  "aps", f'{str(test_rename_aps_file)}', "-Y"])
    capture_logs(result, "test_batch_rename_aps")
    assert result.exit_code == 0
    assert "200" in result.stdout or "299" in result.stdout  # 299 when AP name already matches so no rename required


def test_batch_rename_aps_no_args():
    result = runner.invoke(app, ["batch", "rename",  "aps",])
    capture_logs(result, "test_batch_rename_aps_no_args", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_batch_verify():
    result = runner.invoke(app, ["batch", "verify", f'{str(test_verify_file)}'])
    capture_logs(result, "test_batch_verify")
    assert result.exit_code == 0
    assert "validation" in result.stdout