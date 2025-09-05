from typer.testing import CliRunner

from centralcli import cache
from centralcli.cli import app

from . import capture_logs
from ._test_data import test_data, test_device_file, test_group_file, test_site_file

runner = CliRunner()


def test_del_cert(ensure_cache_cert):  # we don't need to ensure it's in the cache as it will just refresh the cache if not and use the response from mocked show certs call
    result = runner.invoke(app, ["delete", "cert",  "cencli_test", "-Y"])
    capture_logs(result, "test_del_cert")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_wlan(ensure_cache_group1):
    result = runner.invoke(app, ["-d", "delete", "wlan",  "cencli_test_group1",  "delme", "--yes"])
    capture_logs(result, "test_del_wlan")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_device(ensure_inv_cache_add_do_del_ap):
    result = runner.invoke(app, ["delete",  "device", "CN63HH906Z", "-Y"])
    capture_logs(result, "test_del_device")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_batch_del_devices(ensure_cache_batch_del_devices):
    result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_device_file)}', "-Y"])
    capture_logs(result, "test_batch_del_devices")
    assert result.exit_code == 0
    assert "subscriptions successfully removed" in result.stdout.lower()
    assert "200" in result.stdout


def test_batch_del_groups(ensure_cache_batch_del_groups):
    cache.responses.group = None  # Necessary as pytest treats all this as one session, so it thinks cache has been refreshed already
    result = runner.invoke(app, ["batch", "delete",  "groups", str(test_group_file), "-Y"])
    capture_logs(result, "test_batch_del_groups")
    assert result.exit_code == 0
    assert "success" in result.stdout.lower()
    assert result.stdout.lower().count("success") == len(test_data["batch"]["groups_by_name"])


def test_batch_del_sites(ensure_cache_batch_del_sites):
    result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file), "-Y"])
    capture_logs(result, "test_batch_del_sites")
    assert result.exit_code == 0
    assert "success" in result.stdout
    assert result.stdout.count("success") == len(test_data["batch"]["sites"])


def test_del_group(ensure_cache_group1):
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group1",
        "-Y"
        ])
    capture_logs(result, "test_del_group")
    assert result.exit_code == 0
    assert "Success" in result.stdout


def test_del_group_multi(ensure_cache_group3, ensure_cache_group4):
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group3",
        "cencli_test_group4",
        "-Y"
        ])
    capture_logs(result, "test_del_group_multiple")
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert result.stdout.count("Success") == 2


def test_del_site_by_address(ensure_cache_site3):
    result = runner.invoke(app, [
        "delete",
        "site",
        "123 Main St.",
        "-Y"
        ])
    capture_logs(result, "test_del_site_by_address")
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_del_site4(ensure_cache_site4):
    result = runner.invoke(app, [
        "delete",
        "site",
        "cencli_test_site4",
        "-Y"
        ])
    capture_logs(result, "test_del_site4")
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_del_label(ensure_cache_label1):
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label1",
        "-Y"
        ])
    capture_logs(result, "test_del_label")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_label_multi(ensure_cache_label2, ensure_cache_label3):
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label2",
        "cencli_test_label3",
        "-Y"
        ])
    capture_logs(result, "test_del_label_multi")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_guest(ensure_cache_guest1):
    result = runner.invoke(app, ["delete", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--yes"])
    capture_logs(result, "test_del_guest")
    assert result.exit_code == 0
    assert "200" in result.stdout
