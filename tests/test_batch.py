import pytest
from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.exceptions import InvalidConfigException

from . import capture_logs, config
from ._test_data import (
    test_data,
    test_deploy_file,
    test_device_file,
    test_group_file,
    test_label_file,
    test_mpsk_file,
    test_rename_aps_file,
    test_site_file,
    test_sub_file_csv,
    test_sub_file_yaml,
    test_update_aps_file,
    test_verify_file,
)

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


def test_batch_add_labels():
    result = runner.invoke(app, ["batch", "add",  "labels", str(test_label_file), "-Y"])
    capture_logs(result, "test_batch_add_labels")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_batch_add_mpsk():
    result = runner.invoke(app, ["batch", "add",  "mpsk", str(test_mpsk_file), "--ssid", test_data["mpsk_ssid"], "-Y"])
    capture_logs(result, "test_batch_add_mpsk")
    assert result.exit_code == 0
    assert "202" in result.stdout


def test_batch_add_mpsk_invalid_options():
    result = runner.invoke(app, ["batch", "add",  "mpsk", str(test_mpsk_file), "-Y"])
    capture_logs(result, "test_batch_add_mpsk_invalid_options", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


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


if config.dev.mock_tests:
    def test_batch_move(ensure_inv_cache_batch_devices, ensure_dev_cache_batch_devices, ensure_cache_label1):
        result = runner.invoke(app, ["batch", "move",  "devices", f"{str(test_device_file)}", "-y"])
        capture_logs(result, "test_batch_move", )
        assert result.exit_code == 0
        assert "200" in result.stdout


def test_batch_move_no_import_file():
    result = runner.invoke(app, ["batch", "move",  "devices"])
    capture_logs(result, "test_batch_move_no_import_file", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_batch_move_import_file_not_exists():
    result = runner.invoke(app, ["batch", "move",  "devices", "nonexistfile.fake.json"])
    capture_logs(result, "test_batch_move_import_file_not_exists", expect_failure=True)
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


def test_batch_update_aps():
    result = runner.invoke(app, ["batch", "update",  "aps", f'{str(test_update_aps_file)}', "-Y"])
    capture_logs(result, "test_batch_update_aps")
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


def test_batch_delete_devices_no_sub_gws():
    result = runner.invoke(app, ["batch", "delete", "devices", "--no-sub", "--dev-type", "gw", "-Y"])
    capture_logs(result, "test_batch_delete_devices_no_sub_gws")
    assert result.exit_code == 0
    assert "Devices updated" in result.stdout


def test_batch_delete_devices_invalid_no_sub():
    result = runner.invoke(app, ["batch", "delete", "devices", f'{str(test_verify_file)}', "--no-sub"])
    capture_logs(result, "test_batch_delete_devices_invalid_no_sub", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


sfl = ["batch", "delete", "devices"]
@pytest.mark.parametrize("args", [sfl, [*sfl, f'{str(test_verify_file)}', "--dev-type", "cx"]])
def test_batch_delete_devices_invalid(args):
    result = runner.invoke(app, args)
    capture_logs(result, "test_batch_delete_devices_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "\u26a0" in result.stdout


def test_batch_archive():
    result = runner.invoke(app, ["batch", "archive", str(test_device_file), "-y"])
    capture_logs(result, "test_batch_archive")
    assert result.exit_code == 0
    assert "True" in result.stdout


def test_batch_deploy():
    result = runner.invoke(app, ["batch", "deploy", str(test_deploy_file), "-yyyyy"])
    capture_logs(result, "test_batch_deploy")
    assert result.exit_code == 0
    assert "201" in result.stdout
    assert "200" in result.stdout