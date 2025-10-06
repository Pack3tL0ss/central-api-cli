from typer.testing import CliRunner

from centralcli import common
from centralcli.cache import api
from centralcli.cli import app
from centralcli.exceptions import MissingRequiredArgumentException

from . import capture_logs, config, test_data
from ._test_data import test_device_file, test_j2_file

runner = CliRunner()


# TODO NEEDS COMMAND, and alert id to int cache (like logs/events)
def test_ack_notification():
    resp = api.session.request(api.central.central_acknowledge_notifications, "AZl5PdWQBnVd7wH8QpSa")
    assert resp.ok
    assert resp.status == 200


def test_add_device_missing_mac():
    result = runner.invoke(app, ["add", "device", "serial", test_data["switch"]["serial"], "group", test_data["switch"]["group"], "--sub", "advanced-switch-6100", "-y"])
    capture_logs(result, "test_add_device_missing_mac", expect_failure=True)
    assert result.exit_code == 1
    assert "required" in result.stdout


def test_archive(ensure_inv_cache_test_ap):
    result = runner.invoke(app, ["archive", test_data["test_devices"]["ap"]["mac"], "-y"])
    capture_logs(result, "test_archive")
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_archive_multi(ensure_cache_batch_devices):
    devices = common._get_import_file(test_device_file, import_type="devices")
    serials = [dev["serial"] for dev in devices[::-1]][0:2]
    result = runner.invoke(app, ["archive", *serials, "-y"])
    capture_logs(result, "test_archive_multi")
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_convert_template():
    result = runner.invoke(app, ["convert", "template", test_data["j2_template"]])
    capture_logs(result, "test_convert_template")
    assert result.exit_code == 0
    assert "hash" in result.stdout


def test_convert_template_var_file_not_exist():
    result = runner.invoke(app, ["convert", "template", str(test_j2_file)])
    capture_logs(result, "test_convert_template_var_file_not_exist", expect_failure=True)
    assert result.exit_code == 1
    assert "no variable file found" in result.stdout.lower()


def test_convert_template_auto_var_file(ensure_cache_j2_var_yaml):
    result = runner.invoke(app, ["convert", "template", str(test_j2_file)])
    capture_logs(result, "test_convert_template_auto_var_file")
    assert result.exit_code == 0
    assert "some_value" in result.stdout


def test_convert_template_too_many_var_file_matches(ensure_cache_j2_var_yaml, ensure_cache_j2_var_csv):
    result = runner.invoke(app, ["convert", "template", str(test_j2_file)])
    capture_logs(result, "test_convert_template_too_many_var_file_matches", expect_failure=True)
    assert result.exit_code == 1
    assert "Too many matches" in result.stdout


def test_unarchive(ensure_inv_cache_test_ap):
    result = runner.invoke(app, ["unarchive", test_data["test_devices"]["ap"]["serial"]])
    capture_logs(result, "test_unarchive")
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_unarchive_multi(ensure_cache_batch_devices):
    devices = common._get_import_file(test_device_file, import_type="devices")
    serials = [dev["serial"] for dev in devices[::-1]][0:2]
    result = runner.invoke(app, ["unarchive", *serials])
    capture_logs(result, "test_unarchive_multi")
    assert result.exit_code == 0
    assert "succeeded" in result.stdout


def test_move_pre_provision(ensure_cache_group1, ensure_inv_cache_test_ap):
    result = runner.invoke(app, ["move", test_data["test_devices"]["ap"]["serial"], "group", "cencli_test_group1", "-y"])
    capture_logs(result, "test_move_pre_provision")
    assert result.exit_code == 0
    assert "201" in result.stdout


def test_move_group_and_site(ensure_cache_group3, ensure_cache_group1, ensure_cache_site3, ensure_cache_site1, ensure_inv_cache_test_ap, ensure_dev_cache_test_ap):
    result = runner.invoke(app, ["move", test_data["test_devices"]["ap"]["serial"], "group", "cencli_test_group3", "site", "cencli_test_site3", "--reset-group", "-y"])
    capture_logs(result, "test_move_group_and_site")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "ignored" in result.stdout  # reset group is ignored


def test_move_reset_group(ensure_cache_group3, ensure_cache_group1, ensure_cache_site3, ensure_cache_site1, ensure_inv_cache_test_ap, ensure_dev_cache_test_ap):
    result = runner.invoke(app, ["move", test_data["test_devices"]["ap"]["serial"], "--reset-group", "-y"])
    capture_logs(result, "test_move_reset_group")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_move_missing_args():
    result = runner.invoke(app, ["move", test_data["test_devices"]["ap"]["serial"]])
    capture_logs(result, "test_move_missing_args", expect_failure=True)
    assert result.exit_code == 1
    assert "issing" in result.stdout


def test_remove_test_ap_from_site(ensure_inv_cache_test_ap, ensure_dev_cache_test_ap, ensure_cache_site1):
    result = runner.invoke(app, ["remove", test_data["test_devices"]["ap"]["serial"], "site", "cencli_test_site1", "-y"])
    capture_logs(result, "test_remove_test_ap_from_site")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_blink_switch_on_timed():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "on", "1"])
    capture_logs(result, "test_blink_switch_on_timed")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch_on():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "on"])
    capture_logs(result, "test_blink_switch_on")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch_off():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(), "off"])
    capture_logs(result, "test_blink_switch_off")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_wrong_dev_type():
    result = runner.invoke(
        app,
        [
            "blink",
            test_data["gateway"]["mac"],
            "on"
        ]
    )
    capture_logs(result, "test_blink_wrong_dev_type", expect_failure=True)
    assert result.exit_code == 1
    assert "Unable to gather" in result.stdout
    assert "excluded" in result.stdout


def test_bounce_interface():
    result = runner.invoke(app, ["bounce",  "interface", test_data["switch"]["name"].lower(), test_data["switch"]["test_ports"][0], "-Y", "--debug"])
    capture_logs(result, "test_bounce_interface")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_bounce_poe_multiport():
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(), ",".join(test_data["switch"]["test_ports"]), "-Y", "--debug"])
    capture_logs(result, "test_bounce_poe_multiport")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_bounce_poe_multiport_range():
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(), "-".join(test_data["switch"]["test_ports"]), "-Y", "--debug"])
    capture_logs(result, "test_bounce_poe_multiport")
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_clone_group():
    result = runner.invoke(app, ["clone", "group", test_data["aos8_ap"]["group"], "cencli_test_cloned", "--aos10", "-Y"])
    capture_logs(result, "test_clone_group")
    assert result.exit_code == 0
    assert "201" in result.stdout
    assert "Created" in result.stdout


def test_kick_client():
    result = runner.invoke(app, ["kick",  "client", test_data["client"]["wireless"]["name"][0:-2], "--refresh", "--yes"])
    capture_logs(result, "test_kick_client")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_invalid_client():
    result = runner.invoke(app, ["kick",  "client", "aabb.ccdd.1122", "--yes"])
    capture_logs(result, "test_kick_invalid_client", expect_failure=True)
    assert result.exit_code == 1
    assert "nable to gather" in result.stdout


def test_kick_client_not_connected_w_refresh(ensure_cache_client_not_connected):
    result = runner.invoke(app, ["kick",  "client", "aabb.ccdd.eeff", "-R", "--yes"])
    capture_logs(result, "test_kick_client_not_connected_w_refresh", expect_failure=True)
    assert result.exit_code == 1
    assert "not connected" in result.stdout


def test_kick_client_not_connected(ensure_cache_client_not_connected):
    result = runner.invoke(app, ["kick",  "client", "aabb.ccdd.eeff", "--yes"])
    capture_logs(result, "test_kick_client_not_connected")
    assert result.exit_code == 0
    assert "API" in result.stdout  # This passes as we use previous mock response, but hits logic in kick otherwise not hit


def test_kick_all():
    result = runner.invoke(app, ["kick",  "all", test_data["ap"]["serial"], "--yes"])
    capture_logs(result, "test_kick_all")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all_by_ssid():
    result = runner.invoke(app, ["kick",  "all", test_data["ap"]["serial"], "--ssid", test_data["kick_ssid"], "--yes"])
    capture_logs(result, "test_kick_all_by_ssid")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_kick_all_missing_argument():
    try:
        api.session.request(api.device_management.kick_users, test_data["ap"]["serial"])
    except MissingRequiredArgumentException:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_kick_all_missing_argument should have raised a MissingRequiredArgumentException but did not")


def test_save():
    result = runner.invoke(app, ["save",  test_data["switch"]["serial"]])
    capture_logs(result, "test_save")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_sync_gw():
    result = runner.invoke(app, ["sync", test_data["gateway"]["name"]])
    capture_logs(result, "test_sync_gw")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_ts_mesh():
    result = runner.invoke(app, ["ts", "mesh", test_data["mesh_ap"]["name"]])
    capture_logs(result, "test_ts_mesh")
    assert result.exit_code == 0
    assert "COMMAND" in result.stdout


if config.dev.mock_tests:
    def test_nuke_wrong_ap():
        result = runner.invoke(app, ["nuke", test_data["ap"]["serial"], "-y"])
        capture_logs(result, "test_nuke_wrong_ap", expect_failure=True)
        assert result.exit_code == 1
        assert "valid" in result.stdout


    def test_nuke_swarm():
        result = runner.invoke(app, ["nuke", test_data["aos8_ap"]["name"], "-sy"])
        capture_logs(result, "test_nuke_swarm")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_reboot_swarm():
        result = runner.invoke(app, ["reboot",  test_data["aos8_ap"]["name"], "-sy"])
        capture_logs(result, "test_reboot_swarm")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_reboot_device():
        result = runner.invoke(app, ["reboot",  test_data["ap"]["name"], "-sy"])  # -s is ignored as it doesn't apply to AOS10
        capture_logs(result, "test_reboot_device")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_enable_auto_sub():
        result = runner.invoke(app, ["enable",  "auto-sub", "advanced-ap", "-y"])
        capture_logs(result, "test_enable_auto_sub")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_disable_auto_sub():
        result = runner.invoke(app, ["disable",  "auto-sub", "advanced-ap", "-y"])
        capture_logs(result, "test_disable_auto_sub")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_upgrade_ap():
        result = runner.invoke(app, ["upgrade",  "device", test_data["ap"]["serial"], "10.7.2.1_93286", "-y"])
        capture_logs(result, "test_upgrade_ap")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_upgrade_switch_scheduled():
        result = runner.invoke(app, ["upgrade",  "device", test_data["switch"]["serial"], "10.16.1006", "--at", "9/6/2025-05:00", "-Ry"])
        capture_logs(result, "test_upgrade_switch")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_upgrade_group():
        result = runner.invoke(app, ["upgrade",  "group", test_data["upgrade_group"], "--dev-type", "ap", "10.7.2.1_93286", "-y"])
        capture_logs(result, "test_upgrade_group")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_ap_no_change():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"], "-a", test_data["mesh_ap"]["altitude"], "-y"])
        capture_logs(result, "test_upgrade_group_no_change")
        assert result.exit_code == 0
        assert "NO CHANGES" in result.stdout.upper()


    def test_update_ap():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"], "-a", test_data["mesh_ap"]["altitude"] - 0.1, "-y"])
        capture_logs(result, "test_upgrade_group")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_ap_invalid():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"], test_data["ap"]["serial"], "--hostname", "this_will_fail"])
        capture_logs(result, "test_update_ap_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "multiple" in result.stdout


    def test_update_wlan():
        result = runner.invoke(app, ["update",  "wlan", test_data["update_wlan"]["ssid"], test_data["update_wlan"]["group"], "--psk", "cencli_test_psk", "-y"])
        capture_logs(result, "test_upgrade_wlan")
        assert result.exit_code == 0
        assert test_data["update_wlan"]["ssid"].upper() in result.stdout.upper()


    def test_cancel_upgrade_ap():
        result = runner.invoke(app, ["cancel", "upgrade",  "device", test_data["ap"]["serial"], "-y"])
        capture_logs(result, "test_cancel_upgrade_ap")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_cancel_upgrade_switch():
        result = runner.invoke(app, ["cancel", "upgrade",  "device", test_data["switch"]["serial"], "-y"])
        capture_logs(result, "test_upgrade_switch")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_cancel_upgrade_swarm():
        result = runner.invoke(app, ["cancel", "upgrade",  "swarm", test_data["aos8_ap"]["serial"], "-y"])
        capture_logs(result, "test_cancel_upgrade_swarm")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_cancel_upgrade_group():
        result = runner.invoke(app, ["cancel", "upgrade",  "group", test_data["upgrade_group"], "--dev-type", "ap", "-y"])
        capture_logs(result, "test_cancel_upgrade_group")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_cancel_upgrade_group_no_dev_type():
        result = runner.invoke(app, ["cancel", "upgrade",  "group", test_data["upgrade_group"], "-y"])
        capture_logs(result, "test_cancel_upgrade_group_no_dev_type", expect_failure=True)
        assert result.exit_code == 1
        assert "dev-type" in result.stdout


    def test_set_fw_compliance(ensure_cache_group2):
        result = runner.invoke(app, ["set", "firmware", "compliance", "ap", "cencli_test_group2", "10.7.2.1_93286", "-y"])
        capture_logs(result, "test_set_fw_compliance")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_assign_subscription_by_key():
        result = runner.invoke(app, ["assign", "subscription", test_data["subscription"]["key"], test_data["subscription"]["assign_to_device"]["serial"], "-y"])
        capture_logs(result, "test_assign_subscription_by_key")
        assert result.exit_code == 0
        assert "202" in result.stdout


    def test_refresh_cache():
        result = runner.invoke(app, ["refresh", "cache"])
        capture_logs(result, "test_refresh_cache")
        assert result.exit_code == 0
        assert "refresh completed" in result.stdout.lower()


    def test_refresh_token():
        result = runner.invoke(app, ["refresh", "token"])
        capture_logs(result, "test_refresh_token")
        assert result.exit_code == 0
        assert "✔" in result.stdout


    def test_refresh_webhook_token():
        result = runner.invoke(app, ["refresh", "webhook",  "35c0d78e-2419-487f-989c-c0bed8ec57c7"])
        capture_logs(result, "test_refresh_webhook")
        assert result.exit_code == 0
        assert "secure_token" in result.stdout


    def test_rename_ap(ensure_dev_cache_ap):
        result = runner.invoke(app, ["rename", "ap",  test_data["ap"]["name"], test_data["ap"]["name"][0:-5], "--yes"])
        capture_logs(result, "test_rename_ap")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_rename_group(ensure_cache_group3):
        result = runner.invoke(app, ["rename", "group",  "cencli_test_group3", "cencli_test_group30", "--yes"])
        capture_logs(result, "test_rename_group", expect_failure=True)
        assert result.exit_code == 1
        assert "400" in result.stdout


    def test_rename_site(ensure_cache_site4):
        result = runner.invoke(app, ["rename", "site",  "cencli_test_site4", "cencli_test_site40", "--yes"])
        capture_logs(result, "test_rename_site")
        assert result.exit_code == 0
        assert "address" in result.stdout


    def test_test_webhook():
        result = runner.invoke(app, ["test", "webhook", "35c0d78e-2419-487f-989c-c0bed8ec57c7"])
        capture_logs(result, "test_test_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout

if config.wss.key:
    def test_validate_wss_key():
        result = runner.invoke(app, ["test", "method", "validate_wss_key", config.wss.base_url, config.wss.key])
        capture_logs(result, "test_validate_wss_key")
        assert result.exit_code == 0
        assert "200" in result.stdout