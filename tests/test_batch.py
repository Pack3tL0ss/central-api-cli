from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import utils
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, config, log
from ._test_data import (
    test_banner_devices_file,
    test_banner_file_j2,
    test_banner_groups_file,
    test_cloud_auth_mac_file,
    test_cloud_auth_mac_file_invalid,
    test_data,
    test_deploy_file,
    test_device_file,
    test_device_file_none_exist,
    test_device_file_one_not_exist,
    test_device_file_txt,
    test_device_file_w_dup,
    test_group_file,
    test_invalid_device_file_csv,
    test_invalid_empty_file,
    test_invalid_var_file,
    test_invalid_var_file_bad_json,
    test_label_file,
    test_mpsk_file,
    test_outfile,
    test_rename_aps_file,
    test_site_file,
    test_sub_file_csv,
    test_sub_file_test_ap,
    test_sub_file_yaml,
    test_switch_var_file_flat,
    test_switch_var_file_json,
    test_update_aps_file,
    test_verify_file,
)

runner = CliRunner()


def test_batch_add_groups(ensure_cache_group4):  # TODO may need to adjust fixture to remove group4 from cache if it already being there interferes with subsequent tests
    result = runner.invoke(app, ["batch", "add",  "groups", str(test_group_file), "-Y"])
    capture_logs(result, "test_batch_add_groups")
    assert result.exit_code == 0
    assert "⚠" in result.stdout  # group4 already exists, so skipped
    assert result.stdout.lower().count("created") == len(test_data["batch"]["groups_by_name"])  # confirmation prompt includes "created" but group4 is skipped


@pytest.mark.parametrize(
    "idx,file,debug,exit_code,pass_condition",
    [
        [1, str(test_cloud_auth_mac_file), True, 0, lambda r: "202" in r],
        [2, str(test_cloud_auth_mac_file_invalid), False, 1, lambda r: "validation error" in r],
    ]
)
def test_batch_add_macs(idx: int, file: str, debug: bool, exit_code: int, pass_condition: Callable):
    log.DEBUG = debug
    result = runner.invoke(app, ["batch", "add",  "macs", file, "-Y"])
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=bool(exit_code))
    assert result.exit_code == exit_code
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "_,fixture,test_name_append",
    [
        [1, None, None],
        [2, "ensure_cache_label5", None],
    ]
)
def test_batch_add_labels(_:int, fixture: str | None, test_name_append: str | None, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    # no cover: start
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    # no cover: stop
    result = runner.invoke(app, ["batch", "add",  "labels", str(test_label_file), "-Y"])
    capture_logs(result, env.current_test)
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_batch_delete_labels(ensure_cache_batch_labels):
    result = runner.invoke(app, ["batch", "delete",  "labels", str(test_label_file), "-Y"])
    capture_logs(result, "test_batch_delete_labels")
    assert result.exit_code == 0
    assert "200" in result.stdout


@pytest.mark.parametrize("args", [(str(test_label_file), "--no-devs"), ()])
def test_batch_delete_labels_invalid(args: tuple[str]):
    result = runner.invoke(app, ["batch", "delete",  "labels", *args])
    capture_logs(result, "test_batch_delete_labels_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


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


def test_batch_add_devices():
    result = runner.invoke(app, ["batch", "add",  "devices", f'{str(test_device_file)}', "-Y"])
    capture_logs(result, "test_batch_add_device")
    assert result.exit_code == 0
    assert "uccess" in result.stdout
    assert "200" in result.stdout  # /platform/device_inventory/v1/devices
    assert "201" in result.stdout  # /configuration/v1/preassign


@pytest.mark.parametrize(
    "_,args",
    [
        [1, ("devices", f'{str(test_invalid_device_file_csv)}')],
        [2, ("devices", f'{str(test_invalid_empty_file)}')],
    ]
)
def test_batch_add_fail(_: int, args: tuple[str]):
    result = runner.invoke(app, ["batch", "add",  *args, "-Y"])
    capture_logs(result, "test_batch_add_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "⚠" in result.stdout


if config.dev.mock_tests:
    @pytest.mark.parametrize(
        "idx,fixture,glp_ok,args,exit_code,pass_condition",
        [
            [1, None, False, (str(test_sub_file_yaml),), 1, lambda r: "⚠" in r and "Valid" in r],
            [2, None, True, (str(test_sub_file_yaml), "--tags", "testtag1", "=", "testval1,", "testtag2=testval2"), 0, lambda r: r.count("code: 202") == 2],  # glp w tags
            [3, None, True, (str(test_sub_file_csv),), 0, lambda r: r.count("code: 202") >= 2],
            [4, "ensure_inv_cache_add_do_del_ap", True, (str(test_sub_file_test_ap), "--sub", "advanced-ap"), 0, lambda r: "code: 202" in r],
        ]
    )
    def test_batch_subscribe(idx: int, fixture: str, glp_ok: bool, args: tuple[str], exit_code: int, pass_condition: Callable, request: pytest.FixtureRequest):
        if idx == 0:
            request.getfixturevalue("ensure_cache_subscription")
        if fixture:
            request.getfixturevalue(fixture)
        config._mock(glp_ok)
        cmd = f"{'_' if not glp_ok else ''}subscribe"
        result = runner.invoke(app, ["batch", cmd, *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}-{'glp' if glp_ok else 'classic'}", expect_failure=bool(exit_code))
        assert result.exit_code == exit_code
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,args,pass_condition",
        [
            [1, (str(test_device_file), "--cx-retain"), lambda r: "API" in r],
            [2, (str(test_device_file_one_not_exist),), lambda r: "skipped" in r],
        ]
    )
    def test_batch_move(ensure_inv_cache_batch_devices, ensure_dev_cache_batch_devices, ensure_cache_label1, ensure_cache_site1, idx: int, args: tuple[str], pass_condition: Callable):
        result = runner.invoke(app, ["batch", "move",  "devices", *args, "-y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert "200" in result.stdout
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,file,pass_condition",
        [
            [1, str(test_switch_var_file_json), lambda r: "200" in r],
        ]
    )
    def test_batch_add_variables(idx: int, file: str, pass_condition: Callable):
        result = runner.invoke(app, ["batch", "add",  "variables", file, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    def test_batch_rename_aps(ensure_dev_cache_no_last_rename_ap):
        result = runner.invoke(app, ["batch", "rename",  "aps", f'{str(test_rename_aps_file)}', "-Y"])
        capture_logs(result, "test_batch_rename_aps")
        assert result.exit_code == 0
        assert "200" in result.stdout or "299" in result.stdout  # 299 when AP name already matches so no rename required


    @pytest.mark.parametrize("what", ["aps", "ap-banner"])
    def test_batch_update_aps(what: str):
        if what != "ap-banner":
            result = runner.invoke(app, ["batch", "update",  what, f'{str(test_update_aps_file)}', "-Y"])
        else:
            result = runner.invoke(app, ["batch", "update",  "aps", f'{str(test_update_aps_file)}', "--banner-file", str(test_banner_file_j2), "-Y"])
        capture_logs(result, "test_batch_update_aps")
        assert result.exit_code == 0
        assert "200" in result.stdout or "299" in result.stdout  # 299 when AP name already matches so no rename required


    @pytest.mark.parametrize(
        "idx,fixtures,args,test_name_append",
        [
            [1, ["ensure_cache_group1", "ensure_cache_group2", "ensure_cache_group3"], (str(test_banner_groups_file), str(test_banner_file_j2), "-G",), None],
            [2, "ensure_dev_cache_test_ap", (str(test_banner_devices_file), "--banner-file", str(test_banner_file_j2),), None],
            [3, "ensure_dev_cache_test_ap", (str(test_banner_devices_file), "--banner-file", str(test_banner_file_j2),), "has_current_banner"],
            [4, "ensure_dev_cache_test_ap", (str(test_banner_devices_file), "--banner-file", str(test_banner_file_j2),), "has_current_matching_banner"],
        ]
    )
    def test_batch_update_ap_banner(idx: int, fixtures: str | list[str] | None, args: tuple[str], test_name_append: str | None, request: pytest.FixtureRequest):
        if fixtures:
            [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        if test_name_append:  # pragma: no cover
            env.current_test = f"{env.current_test}_{test_name_append}"
        result = runner.invoke(app, ["batch", "update",  "ap-banner", *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert "200" in result.stdout or "299" in result.stdout  # 299 when AP name already matches so no rename required


    @pytest.mark.parametrize(
        "idx,fixtures,args",
        [
            [1, None, ("-G",)],
            [2, None, (str(test_banner_devices_file),)],
            [3, "ensure_dev_cache_test_ap", (str(test_banner_devices_file), str(test_banner_file_j2))],
        ]
    )
    def test_batch_update_ap_banners_fail(idx: int, fixtures: str | list[str] | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixtures:
            [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        result = runner.invoke(app, ["batch", "update",  "ap-banner", *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout or "ERROR" in result.stdout


    @pytest.mark.parametrize(
        "idx,fixtures,args,pass_condition",
        [
            [1, None, (test_data["batch"]["variable_file"],), lambda r: r.count("200") == 2],
            [2, None, (test_data["batch"]["variable_file"], "-R"), lambda r: r.count("200") == 2],
        ]
    )
    def test_batch_update_variables(idx: int, fixtures: str | list[str] | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
        if fixtures:  # pragma: no cover
            [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        result = runner.invoke(app, ["batch", "update",  "variables", *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,args,pass_condition",
        [
            [1, (), lambda r: "⚠" in r],
            [2, (str(test_invalid_var_file),), lambda r: "⚠" in r],
            [3, (str(test_invalid_var_file_bad_json),), lambda r: "JSONDecodeError" in r],
        ]
    )
    def test_batch_update_variables_fail(idx: int, args: tuple[str], pass_condition: Callable):
        result = runner.invoke(app, ["batch", "update",  "variables", *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
        assert result.exit_code == 1
        assert pass_condition(result.stdout)

    @pytest.mark.parametrize(
        "idx,fixtures,args,test_name_append",
        [
            [1, None, (str(test_device_file), "--tags", "fuel=''"), None],
        ]
    )
    def test_batch_update_devices(idx: int, fixtures: str | list[str] | None, args: tuple[str], test_name_append: str | None, request: pytest.FixtureRequest):
        if fixtures:
            [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        if test_name_append:  # pragma: no cover
            env.current_test = f"{env.current_test}_{test_name_append}"
        result = runner.invoke(app, ["batch", "update",  "devices", *args, "-Y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert "202" in result.stdout


    @pytest.mark.parametrize(
        "idx,glp_ok,args,pass_condition",
        [
            [1, False, ("--no-sub", "--dev-type", "gw"), lambda r: "Devices updated" in r],
            [2, True, ("--no-sub", "--dev-type", "gw"), lambda r: "code: 202" in r],
        ]
    )
    def test_batch_delete_devices(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable):
        config._mock(glp_ok)
        result = runner.invoke(app, ["batch", "delete", "devices", *args, "-Y"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)

else:  # pragma: no cover
    ...


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("devices",), lambda r: "Invalid" in r],
        [2, ("devices", "nonexistfile.fake.json"), lambda r: "Invalid" in r],
        [3, ("devices", f'{str(test_device_file)}', f'{str(test_rename_aps_file)}', "--label"), lambda r: "oo many" in r],
        [4, ("devices", f'{str(test_site_file)}'), lambda r: "missing required field" in r],
        [5, ("devices", f'{str(test_switch_var_file_flat)}'), lambda r: "AttributeError" in r],
        [6, ("devices", f'{str(test_device_file_none_exist)}'), lambda r: "No devices found" in r],
        [7, ("devices", f'{str(test_device_file_w_dup)}'), lambda r: "Duplicates exist" in r],
    ]
)
def test_batch_move_fail(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["batch", "move",  *args])
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


def test_batch_rename_aps_no_args():
    result = runner.invoke(app, ["batch", "rename",  "aps",])
    capture_logs(result, "test_batch_rename_aps_no_args", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_batch_verify():
    result = runner.invoke(app, ["batch", "verify", f'{str(test_verify_file)}', "--out", test_outfile])
    capture_logs(result, "test_batch_verify")
    assert result.exit_code == 0
    assert "validation" in result.stdout


@pytest.mark.parametrize(
    "args,pass_condition",
    [
        [(), lambda r: "⚠" in r],
        [(f'{str(test_verify_file)}', "--dev-type", "cx"), lambda r: "⚠" in r],
        [(f'{str(test_verify_file)}', "--no-sub"), lambda r: "Invalid" in r],
    ]
)
def test_batch_delete_devices_fail(args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["batch", "delete", "devices", *args])
    capture_logs(result, "test_batch_delete_devices_fail", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)


@pytest.mark.parametrize("file", [test_device_file, test_device_file_txt])
def test_batch_archive(file: str):
    for idx in range(2):
        config._mock(bool(idx))
        result = runner.invoke(app, ["batch", "archive", str(file), "-y"])
        capture_logs(result, "test_batch_archive")
        assert result.exit_code == 0
        assert "Accepted" in result.stdout or "True" in result.stdout

@pytest.mark.parametrize("glp_ok", [False, True])
def test_batch_archive_fail(glp_ok: bool):
    config._mock(glp_ok)
    result = runner.invoke(app, ["batch", "archive", str(test_device_file), "-y"])
    capture_logs(result, "test_batch_archive_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "Response" in result.stdout


@pytest.mark.parametrize("glp_ok", [False, True])
def test_batch_unarchive_devices(glp_ok: bool):
    config._mock(glp_ok)
    result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
    capture_logs(result, "test_batch_unarchive_device")
    assert result.exit_code == 0
    assert "Accepted" in result.stdout or "uccess" in result.stdout


@pytest.mark.parametrize("glp_ok", [False, True])
def test_batch_unarchive_devices_fail(glp_ok: bool):
    config._mock(glp_ok)
    result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
    capture_logs(result, "test_batch_unarchive_device_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "Response" in result.stdout


def test_batch_deploy():
    result = runner.invoke(app, ["batch", "deploy", str(test_deploy_file), "-yyyyy"])
    capture_logs(result, "test_batch_deploy")
    assert result.exit_code == 0
    assert "201" in result.stdout
    assert "200" in result.stdout


@pytest.mark.parametrize(
    "idx,args,pass_condition",
    [
        [1, ("add", "devices"), lambda r: "cencli batch add devices" in r],
        [2, ("add", "groups"), lambda r: "cencli batch add groups" in r],
        [3, ("add", "labels"), lambda r: "cencli batch add labels" in r],
        [4, ("add", "macs"), lambda r: "cencli batch add macs" in r],
        [5, ("add", "mpsk"), lambda r: "cencli batch add mpsk" in r],
        [6, ("add", "sites"), lambda r: "cencli batch add sites" in r],
        [7, ("archive",), lambda r: "cencli batch archive" in r],
        [8, ("delete", "devices"), lambda r: "cencli batch delete devices" in r],
        [9, ("delete", "groups"), lambda r: "cencli batch delete groups" in r],
        [10, ("delete", "labels"), lambda r: "cencli batch delete labels" in r],
        [11, ("delete", "sites"), lambda r: "cencli batch delete sites" in r],
        [12, ("move",), lambda r: "cencli batch move" in r],
        [13, ("rename", "aps"), lambda r: "cencli batch rename aps" in r],
        [14, ("subscribe",), lambda r: "cencli batch subscribe" in r],
        [15, ("unarchive",), lambda r: "cencli batch unarchive" in r],
        [16, ("unsubscribe",), lambda r: "cencli batch unsubscribe" in r],
        [17, ("update", "aps"), lambda r: "cencli batch update aps" in r],
        [18, ("update", "devices"), lambda r: "serial" in r],  # TODO this needs full example
        [19, ("verify",), lambda r: "cencli batch verify" in r],
        [20, ("update", "ap-banner"), lambda r: "example" in r],
        [21, ("update", "variables"), lambda r: "cencli batch update variables" in r],
        [22, ("add", "variables"), lambda r: "cencli batch add variables" in r],
        [23, ("deploy",), lambda r: "deploy" in r.lower()],  # TODO this only has a placeholder no example
    ]
)
def test_batch_examples(idx: int, args: tuple[str], pass_condition: Callable):
    result = runner.invoke(app, ["batch", *args, "--example"])
    capture_logs(result, f"{env.current_test}{idx}")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)
