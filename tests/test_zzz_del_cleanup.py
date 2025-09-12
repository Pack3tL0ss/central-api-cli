from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, config
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


def test_batch_del_devices(ensure_cache_batch_devices):
    result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_device_file)}', "-Y"])
    capture_logs(result, "test_batch_del_devices")
    assert result.exit_code == 0
    assert "subscriptions successfully removed" in result.stdout.lower()
    assert "200" in result.stdout


def test_batch_del_groups(ensure_cache_batch_del_groups):
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


def test_del_template(ensure_cache_template):
    result = runner.invoke(app, [
        "delete",
        "template",
        "cencli_test_template",
        "--group",
        "cencli_test_group2",
        "-Y"
        ])
    capture_logs(result, "test_del_template")
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


def test_del_mpsk(ensure_cache_mpsk):  # TODO need command for this
    result = runner.invoke(
        app,
        [
            "test",
            "method",
            "cloudauth_delete_namedmpsk",
            "1EBTWK86LPQ86S0B",
            "4e650830-d4d6-4a19-b9af-e0f776c69d24"
        ]
    )
    capture_logs(result, "test_del_mpsk")
    assert result.exit_code == 0
    assert "204" in result.stdout


def test_del_portal(ensure_cache_test_portal):
    result = runner.invoke(app, [
        "delete",
        "portal",
        "cencli_test_portal",
        "-Y"
        ])
    capture_logs(result, "test_del_portal")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_del_guest(ensure_cache_guest1):
    result = runner.invoke(app, ["delete", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--yes"])
    capture_logs(result, "test_del_guest")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_delete_template(ensure_cache_template, ensure_cache_group2):
    result = runner.invoke(app, ["delete", "template",  "cencli_test_template", "cencli_test_group2", "-Y"])
    capture_logs(result, "test_delete_template")
    assert result.exit_code == 0
    assert "200" in result.stdout


# This endpoint only works for devices that have checked in with Central, despite the fact you can pre-provision the variables
def test_delete_variables(ensure_inv_cache_test_switch):
    result = runner.invoke(app, ["delete", "variables",  test_data["test_devices"]["switch"]["serial"], "-Y"])
    capture_logs(result, "test_delete_variables")
    assert result.exit_code == 0
    assert "200" in result.stdout


if config.dev.mock_tests:
    def test_delete_webhook():
        result = runner.invoke(app, ["delete", "webhook",  "35c0d78e-2419-487f-989c-c0bed8ec57c7", "-y"])
        capture_logs(result, "test_delete_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout