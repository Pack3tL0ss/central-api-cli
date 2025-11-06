from typing import Callable

import pendulum
import pytest
from typer.testing import CliRunner

from centralcli import common, utils
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, config, test_data
from ._test_data import test_device_file, test_j2_file

runner = CliRunner()


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

@pytest.mark.parametrize(
    "args",
    [
        ([test_data["switch"]["name"], "on", "1"]),
        ([test_data["switch"]["name"], "on"]),
        ([test_data["switch"]["name"], "off"]),
    ]
)
def test_blink_switch(args: list[str]):
    result = runner.invoke(app, ["blink", *args])
    capture_logs(result, "test_blink_switch")
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


def test_bounce_poe_multiport_invalid_range():
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(), f'{"-".join(test_data["switch"]["test_ports"])}-1/1/22'])
    capture_logs(result, "test_bounce_poe_multiport_invalid_range", expect_failure=True)
    assert result.exit_code == 1
    assert "\u26a0" in result.stdout  # \u26a0 is warning emoji


def test_bounce_poe_multiport_invalid_range_across_members():
    invalid_range = f'{test_data["switch"]["test_ports"][0]}-{int(test_data["switch"]["test_ports"][0].split("/")[0]) + 1}/{"/".join(test_data["switch"]["test_ports"][0].split("/")[1:])}'
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(), invalid_range])
    capture_logs(result, "test_bounce_poe_multiport", expect_failure=True)
    assert result.exit_code == 1
    assert "\u26a0" in result.stdout  # \u26a0 is warning emoji


@pytest.mark.parametrize(
    "fixture,args,pass_condition",
    [
        [None, (test_data["aos8_ap"]["group"], "cencli_test_cloned"), lambda r: "Created" in r],
        ["ensure_cache_group_cloned_w_gw", ("cencli_test_cloned", "cencli_test_cloned_upgdaos10", "--aos10"), lambda r: "⚠" in r],
    ]
)
def test_clone_group(fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["clone", "group", *args, "-y"])
    capture_logs(result, "test_clone_group")
    assert result.exit_code == 0
    assert "201" in result.stdout
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args",
    [
        ([test_data["aos8_ap"]["group"], "cencli_test_cloned", "--aos10", "-Y"]),
    ]
)
def test_clone_group_fail(args: list[str]):
    result = runner.invoke(app, ["clone", "group", *args])
    capture_logs(result, "test_clone_group_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout

@pytest.mark.parametrize(
    "args",
    [
        ("client", test_data["client"]["wireless"]["name"][0:-2], "--refresh"),
        ("all", test_data["ap"]["serial"]),
        ("all", test_data["ap"]["serial"], "--ssid", test_data["kick_ssid"]),
    ]
)
def test_kick(args: tuple[str]):
    result = runner.invoke(app, ["kick", *args, "--yes"])
    capture_logs(result, "test_kick_client")
    assert result.exit_code == 0
    assert "200" in result.stdout


@pytest.mark.parametrize(
    "fixture,args,expected,test_name_append",
    [
        ["ensure_cache_client_not_connected", ("aabb.ccdd.eeff", "-R"), "not connected", None],
        ["ensure_cache_client_not_connected", ("aabb.ccdd.eeff",), "failure", "refresh"],
        [None, ("aabb.ccdd.1122",), "nable to gather", None],
    ]
)
def test_kick_fail(fixture: str | None, args: list[str], expected: str, test_name_append: str | None, request: pytest.FixtureRequest):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, ["kick", "client", *args, "--yes"],)
    capture_logs(result, env.current_test, expect_failure=True)
    assert result.exit_code == 1
    assert expected in result.stdout


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


    def test_nuke_unsupported_type():
        result = runner.invoke(app, ["nuke", test_data["switch"]["serial"]])
        capture_logs(result, "test_nuke_unsupported_type", expect_failure=True)
        assert result.exit_code == 1
        assert "only applies to" in result.stdout

    @pytest.mark.parametrize(
        "args",
        [
            ([test_data["aos8_ap"]["name"], "-sy"]),
            ([test_data["template_switch"]["serial"], "-sy"]),  # also testing path with warning msg due to -s (swarm) used with switch
        ]
    )
    def test_nuke(args: list[str]):
        result = runner.invoke(app, ["nuke", *args])
        capture_logs(result, "test_nuke")
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


    def test_upgrade_ap(ensure_dev_cache_test_ap):
        result = runner.invoke(app, ["upgrade",  "device", test_data["ap"]["serial"], test_data["test_devices"]["ap"]["serial"], "10.7.1.0-beta_91138", "-y"])
        capture_logs(result, "test_upgrade_ap")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_upgrade_switch_scheduled():
        result = runner.invoke(app, ["upgrade",  "device", test_data["switch"]["serial"], "10.16.1006", "--at", "9/6/2025-05:00", "-Ry"])
        capture_logs(result, "test_upgrade_switch")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_upgrade_group():
        result = runner.invoke(app, ["upgrade",  "group", test_data["upgrade_group"], "--dev-type", "ap", "10.7.1.0-beta_91138", "--in", "10m", "-y"])
        capture_logs(result, "test_upgrade_group")
        assert result.exit_code == 0
        assert "200" in result.stdout

    def test_upgrade_group_by_model_invalid():
        result = runner.invoke(app, ["upgrade",  "group", test_data["upgrade_group"], "--model", "2930F", "--dev-type", "sw", "-y"])
        capture_logs(result, "test_upgrade_group_by_model_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout

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


    in_45_mins = pendulum.now() + pendulum.duration(minutes=45)
    at_str = in_45_mins.to_datetime_string().replace(" ", "T")[0:-3]
    @pytest.mark.parametrize(
        "args",
        [
            (["ap", "cencli_test_group2", "10.7.2.1_93286"]),
            (["ap", "cencli_test_group2", "10.7.2.1_93286", "--at", at_str]),
        ]
    )
    def test_set_fw_compliance(ensure_cache_group2, args: list[str]):
        result = runner.invoke(app, ["set", "firmware", "compliance", *args, "-y"])
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


    @pytest.mark.parametrize(
        "new_name,pass_condition",
        [
            [test_data["ap"]["name"][0:-5], lambda r: "200" in r],
            [test_data["ap"]["name"], lambda r: "299" in r]
        ]
    )
    def test_rename_ap(ensure_dev_cache_ap, new_name: str, pass_condition: Callable):
        result = runner.invoke(app, ["rename", "ap",  test_data["ap"]["serial"], new_name, "--yes"])
        capture_logs(result, "test_rename_ap")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


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


    def test_reset_overlay_connection():
        result = runner.invoke(app, ["reset", "overlay", test_data["gateway"]["name"], "-y"])
        capture_logs(result, "test_reset_overlay_connection")
        assert result.exit_code == 0
        assert "200" in result.stdout


    @pytest.mark.parametrize(
        "fixture,args,pass_condition",
        [
            [
                [
                    "ensure_inv_cache_test_switch",
                    "ensure_inv_cache_test_ap",
                    "ensure_inv_cache_test_stack",
                    "ensure_dev_cache_test_switch",
                    "ensure_dev_cache_test_ap",
                    "ensure_dev_cache_test_stack",
                    "ensure_cache_group1",
                    "ensure_cache_site1",
                ],
                (test_data["test_devices"]["switch"]["serial"], *[sw["serial"] for sw in test_data["test_devices"]["stack"]], test_data["test_devices"]["ap"]["serial"]),
                lambda r: "200" in r
            ]
        ]
    )
    def test_delete_devices(fixture: str | list[str] | None, args: list[str], pass_condition: Callable, request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        else:  # pragma: no cover
            ...
        result = runner.invoke(app, ["delete", "device", *args, "-y"])
        capture_logs(result, "test_delete_devices")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "fixture,args",
        [
            ["ensure_inv_cache_test_ap", (test_data["test_devices"]["ap"]["serial"],)],
            ["ensure_cache_batch_devices", ("from_import",)],
            [None, ("US18CEN103", "US18CEN112")],  # this passes as it reuses real response, but these serials don't exist in cache.
        ]
    )
    def test_unarchive(fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        if "from_import" in args:
            devices = common._get_import_file(test_device_file, import_type="devices")
            args = [dev["serial"] for dev in devices[::-1]][0:2]
        result = runner.invoke(app, ["unarchive", *args])
        capture_logs(result, "test_unarchive")
        assert result.exit_code == 0
        assert "succeeded" in result.stdout

else:  # pragma: no cover  Coverage shows untested branch without this
    ...
