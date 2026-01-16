from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import utils
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, config
from ._test_data import test_data, test_device_file, test_group_file, test_site_file_none_exist, test_site_file_one_not_exist, test_invalid_site_file

runner = CliRunner()


if config.dev.mock_tests:
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
        assert "successfully" in result.stdout


    def test_batch_del_devices(ensure_inv_cache_batch_devices):
        result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_device_file)}', "-Y"])
        capture_logs(result, "test_batch_del_devices")
        assert result.exit_code == 0
        assert "devices updated" in result.stdout.lower()


    def test_batch_del_devices_invalid():
        result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_device_file)}', "--no-sub"])
        capture_logs(result, "test_batch_del_devices_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout


    def test_batch_del_groups(ensure_cache_batch_del_groups):
        result = runner.invoke(app, ["batch", "delete",  "groups", str(test_group_file), "-Y"])
        capture_logs(result, "test_batch_del_groups")
        assert result.exit_code == 0
        assert "success" in result.stdout.lower()
        assert result.stdout.lower().count("success") == len(test_data["batch"]["groups_by_name"])


    def test_batch_del_sites(ensure_cache_batch_del_sites):
        result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file_one_not_exist), "-Y"])
        capture_logs(result, "test_batch_del_sites")
        assert result.exit_code == 0
        assert "success" in result.stdout
        assert "kipping" in result.stdout  # Skipping ... site does not exist in Central


    @pytest.mark.parametrize(
        "_,args,pass_condition",
        [
            [1, ("sites", str(test_site_file_none_exist)), lambda r: "No sites" in r],
            [2, ("sites", str(test_invalid_site_file)), lambda r: "failed validation" in r],
        ]
    )
    def test_batch_del_fail(_: int, args: tuple[str], pass_condition: Callable):
        result = runner.invoke(app, ["batch", "delete",  *args, "-Y"])
        capture_logs(result, "test_batch_del_fail", expect_failure=True)
        assert result.exit_code == 1
        assert pass_condition(result.stdout)


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


    @pytest.mark.parametrize(
        "idx,args",
        [
            [1, ("cencli_test_template", "--group", "cencli_test_group2",)],
            [2, ("cencli_test_template",)],
        ]
    )
    def test_del_template(ensure_cache_template, ensure_cache_group2, idx: int, args: tuple[str]):
        result = runner.invoke(app, [
            "delete",
            "template",
            *args,
            "-Y"
            ])
        capture_logs(result, "test_del_template")
        assert result.exit_code == 0
        assert "uccess" in result.stdout


    @pytest.mark.parametrize(
        "fixture,args",
        [
            ["ensure_cache_label1", ("cencli_test_label1",)],
            [["ensure_cache_label2", "ensure_cache_label3"], ("cencli_test_label2", "cencli_test_label3")]
        ]
    )
    def test_del_labels(fixture: str | list[str], args: tuple[str], request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(app, [
            "delete",
            "label",
            *args,
            "-Y"
            ])
        capture_logs(result, "test_del_labels")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_del_mpsk(ensure_cache_mpsk):  # TODO need command for this
        result = runner.invoke(
            app,
            [
                "test",
                "method",
                "delete_named_mpsk",
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
        result = runner.invoke(app, ["delete", "guest", test_data["portal"]["name"], test_data["portal"]["guest"]["name"], "--yes"])
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


    @pytest.mark.parametrize(
        "idx,fixture,args,exit_code,pass_condition",
        [
            [1, "ensure_cache_group2", ("ap", "cencli_test_group2"), 0, lambda r: "200" in r],
            [2, None, ("ap",), 1, lambda r: "404" in r],
        ]
    )
    def test_delete_fw_compliance(idx: int, fixture: str | None, args: tuple[str], exit_code: int, pass_condition: Callable, request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        result = runner.invoke(app, ["delete", "firmware",  "compliance", *args, "-y"])
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=bool(exit_code))
        assert result.exit_code == exit_code
        assert pass_condition(result.stdout)


    def test_delete_fw_compliance_invalid():
        result = runner.invoke(app, ["delete", "firmware",  "compliance", "ap", "cencli_test_group2", "extra-invalid"])
        capture_logs(result, "test_delete_fw_compliance_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "\u26a0" in result.stdout


    def test_delete_fw_compliance_fail(ensure_cache_group1):
        result = runner.invoke(app, ["delete", "firmware",  "compliance", "ap", "cencli_test_group1", "--yes"])
        capture_logs(result, "test_delete_fw_compliance_fail", expect_failure=True)
        assert result.exit_code == 1
        assert "404" in result.stdout


    def test_delete_webhook():
        result = runner.invoke(app, ["delete", "webhook",  "35c0d78e-2419-487f-989c-c0bed8ec57c7", "-y"])
        capture_logs(result, "test_delete_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout

else:  # pragma: no cover
    ...