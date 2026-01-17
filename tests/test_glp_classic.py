"""This test file contains all tests that need to be ran against both GLP and classic flows
"""
import pytest
from typer.testing import CliRunner

from typing import Callable
from centralcli import config, utils, common
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, test_data
from ._test_data import test_device_file, test_device_file_txt, test_sub_file_yaml, test_sub_file_csv, test_sub_file_test_ap, test_sub_file_classic_yaml

runner = CliRunner()

if config.dev.mock_tests:
    @pytest.mark.parametrize(
        "idx,glp_ok,args,pass_condition",
        [
            [1, False, ("--key", "EC5C0481E85EB4DB79"), lambda r: "mac" in r],
            [2, False, ("--sub",), lambda r: "mac" in r],
            [3, False, ("--no-sub",), lambda r: "mac" in r],
            [4, False, ("-v",), lambda r: "mac" in r],
            [1, True, ("--key", "EC5C0481E85EB4DB79"), lambda r: "mac" in r],
            [2, True, ("--sub",), lambda r: "mac" in r],
            [3, True, ("--no-sub",), lambda r: "mac" in r],
            [4, True, ("-v",), lambda r: "mac" in r],
        ]
    )
    def test_show_inventory(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable):
        if idx == 1:
            config._mock(glp_ok)
        env.current_test = f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}"
        result = runner.invoke(app, ["show", "inventory", *args],)
        capture_logs(result, f"{env.current_test}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,args,pass_condition,test_name_append",
        [
            [1, (), lambda r: "500" in r, None],
            [2, (), lambda r: "500" in r, None],
            [3, (), lambda r: "fetch subscription details failed" in r, "sub_call"],
            [4, (), lambda r: "fetch subscription details failed" in r, "sub_call"],
        ]
    )
    def test_show_inventory_fail(idx: int, args: tuple[str], pass_condition: Callable, test_name_append: str | None):
        glp_ok = True if idx % 2 != 0 else False
        config._mock(glp_ok)
        if test_name_append:  # pragma: no cover
            env.current_test = f"{env.current_test}_{test_name_append}"
        result = runner.invoke(app, ["show", "inventory", *args],)
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}", expect_failure=bool(result.exit_code))
        assert result.exit_code <= 1  # classic #2 needs work to return exit code based on partial/sub-call failure
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,glp_ok,args,pass_condition",
        [
            [1, False, ("--csv",), lambda r: "status" in r],
            [2, True, ("--csv",), lambda r: "ounts" in r],
            [3, False, ("--sort", "end-date", "-r"), lambda r: "ounts" in r],
            [4, True, ("--sort", "end-date", "-r"), lambda r: "ounts" in r],
            [5, False, ("stats",), lambda r: "used" in r],
            [6, False, ("names",), lambda r: "advance" in r],
            [7, False, ("auto",), lambda r: "API" in r],
            [8, False, ("--dev-type", "switch"), lambda r: "ounts" in r],
            [9, True, ("--dev-type", "switch"), lambda r: "ounts" in r],
            [10, False, ("--type", "foundation-switch-6200"), lambda r: "foundation-switch" in r.lower()],  # response now comes back as Foundation-Switch-Class-2
            [11, True, ("--type", "foundation-switch-6200"), lambda r: "foundation-switch" in r.lower()],
        ]
    )
    def test_show_subscriptions(idx: int, glp_ok: bool, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
        config._mock(glp_ok)
        env.current_test = f"{env.current_test}-{'glp' if glp_ok else 'classic'}"
        result = runner.invoke(app, ["show", "subscriptions", *args])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,file",
        [
            [1, test_device_file],
            [2, test_device_file],
            [3, test_device_file_txt],
            [4, test_device_file_txt],
        ]
    )
    def test_batch_archive(idx, file: str):
        glp_ok = True if idx % 2 != 0 else False
        config._mock(glp_ok)
        result = runner.invoke(app, ["batch", "archive", str(file), "-y"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}")
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
    def test_batch_unarchive(glp_ok: bool):
        config._mock(glp_ok)
        result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
        capture_logs(result, "test_batch_unarchive_device")
        assert result.exit_code == 0
        assert "Accepted" in result.stdout or "uccess" in result.stdout


    @pytest.mark.parametrize("glp_ok", [False, True])
    def test_batch_unarchive_fail(glp_ok: bool):
        config._mock(glp_ok)
        result = runner.invoke(app, ["batch", "unarchive",  "--yes", f'{str(test_device_file)}'])
        capture_logs(result, "test_batch_unarchive_device_fail", expect_failure=True)
        assert result.exit_code == 1
        assert "Response" in result.stdout


    @pytest.mark.parametrize(
        "idx,fixture,glp_ok,args,exit_code,pass_condition",
        [
            [1, None, False, (str(test_sub_file_classic_yaml),), 0, lambda r: "200" in r],
            [2, None, True, (str(test_sub_file_yaml), "--tags", "testtag1", "=", "testval1,", "testtag2=testval2"), 0, lambda r: r.count("code: 202") == 2],  # glp w tags
            [3, None, False, (str(test_sub_file_yaml),), 1, lambda r: "⚠" in r and "Valid" in r],
            [4, None, True, (str(test_sub_file_csv),), 0, lambda r: r.count("code: 202") >= 2],
            [5, None, True, (str(test_sub_file_test_ap), "--sub", "advanced-ap"), 0, lambda r: "code: 202" in r],
        ]
    )
    def test_batch_subscribe(ensure_inv_cache_batch_sub_devices, idx: int, fixture: str, glp_ok: bool, args: tuple[str], exit_code: int, pass_condition: Callable, request: pytest.FixtureRequest):
        if idx == 1:
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


    @pytest.mark.parametrize("glp_ok", [False, True])
    def test_archive(ensure_inv_cache_test_ap, glp_ok: bool):
        config._mock(glp_ok)
        result = runner.invoke(app, ["archive", test_data["test_devices"]["ap"]["mac"], "99-:CD:not-a:cd:-serial", "USD8H1R1KG", "--yes"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}")
        assert result.exit_code == 0
        assert "succeeded" or "Accepted" in result.stdout
        assert "⚠" in result.stdout  # "99-not-a-serial" is skipped as it's not a serial number and is not found in inventory/cache
        assert "💿" not in result.stdout


    @pytest.mark.parametrize("glp_ok", [False, True])
    def test_archive_multi(ensure_inv_cache_batch_devices, glp_ok: bool):
        config._mock(glp_ok)
        devices = common._get_import_file(test_device_file, import_type="devices")
        serials = [dev["serial"] for dev in devices[::-1]][0:2]
        result = runner.invoke(app, ["archive", *serials, "-y"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}")
        assert result.exit_code == 0
        assert "succeeded" or "Accepted" in result.stdout
        assert "💿" not in result.stdout


    @pytest.mark.parametrize("glp_ok", [False, True])
    def test_archive_fail(ensure_inv_cache_test_ap, glp_ok: bool):
        config._mock(glp_ok)
        result = runner.invoke(app, ["archive", test_data["test_devices"]["ap"]["mac"], "USD8H1R1KG", "--yes"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}")
        assert result.exit_code == 1
        assert "Response" in result.stdout
        assert "💿" not in result.stdout


    @pytest.mark.parametrize(
        "idx,glp_ok,fixture,args",
        [
            [1, False, "ensure_inv_cache_test_ap", (test_data["test_devices"]["ap"]["serial"],)],
            [2, True, "ensure_inv_cache_test_ap", (test_data["test_devices"]["ap"]["serial"],)],
            [3, False, "ensure_inv_cache_batch_devices", ("from_import",)],
            [4, True, "ensure_inv_cache_batch_devices", ("from_import",)],
            [5, False, "ensure_inv_cache_fake_archived_devs", ("US18CEN103", "US18CEN112")],
            [6, True, "ensure_inv_cache_fake_archived_devs", ("US18CEN103", "US18CEN112")],
        ]
    )
    def test_unarchive(idx: int, glp_ok: bool, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:  # pragma: no cover
            request.getfixturevalue(fixture)
        if "from_import" in args:
            devices = common._get_import_file(test_device_file, import_type="devices")
            args = [dev["serial"] for dev in devices[::-1]][0:2]
        config._mock(glp_ok)
        result = runner.invoke(app, ["unarchive", *args])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}")
        assert result.exit_code == 0
        assert "Accepted" in result.stdout or "successfully unarchived" in result.stdout
        assert "🆎" not in result.stdout


    @pytest.mark.parametrize(
        "idx,glp_ok,fixture,args",
        [
            [1, False, "ensure_inv_cache_test_ap", (test_data["test_devices"]["ap"]["serial"],)],
            [2, True, "ensure_inv_cache_test_ap", (test_data["test_devices"]["ap"]["serial"],)],
        ]
    )
    def test_unarchive_fail(idx: int, glp_ok: bool, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:  # pragma: no cover
            request.getfixturevalue(fixture)
        config._mock(glp_ok)
        result = runner.invoke(app, ["unarchive", *args])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}", expect_failure=True)
        assert result.exit_code == 1
        assert "Response" in result.stdout
        assert "🆎" not in result.stdout


    @pytest.mark.parametrize(
        "idx,glp_ok,fixture,args,pass_condition",
        [
            [
                1,
                False,
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
                lambda r: "code: 20" in r  # 200 classic / 202 glp
            ],
            [
                2,
                True,
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
                lambda r: "code: 20" in r  # 200 classic / 202 glp
            ]
        ]
    )
    def test_delete_devices(idx: int, glp_ok: bool, fixture: str | list[str] | None, args: list[str], pass_condition: Callable, request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        else:  # pragma: no cover
            ...
        config._mock(glp_ok)
        result = runner.invoke(app, ["delete", "device", *args, "-y"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    def test_assign_subscription_glp(ensure_cache_subscription_none_available):  # ensure cache sub... ensures the sub is there but with 0 remaining, forces it to hit a branch that log/shows a warning (glp only)
        result = runner.invoke(
            app,
            [
                "assign",
                "subscription",
                "advanced-ap",
                test_data["ap"]["name"],
                "-Y"
            ]
        )
        capture_logs(result, env.current_test)
        assert result.exit_code == 0
        assert "Response" in result.stdout
        assert "⚠" in result.stdout


    def test_assign_subscription_classic(ensure_old_config):
        result = runner.invoke(
            app,
            [
                "assign",
                "_subscription",  #  determination on which should be hidden is performed before we mock non glp config
                "advanced-ap",
                test_data["ap"]["name"],
                "-Y"
            ]
        )
        capture_logs(result, env.current_test)
        assert result.exit_code == 0
        assert "Response" in result.stdout


    @pytest.mark.parametrize(
        "idx,glp_ok,fixture,args",
        [
            [1, False, ["ensure_inv_cache_test_ap"], ("foundation-ap", test_data["test_devices"]["ap"]["serial"],)],
            [2, True, ["ensure_inv_cache_test_ap"], (test_data["test_devices"]["ap"]["serial"],)],
        ]
    )
    def test_unassign(idx: int, glp_ok: bool, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if not glp_ok:
            fixture = fixture or []
            fixture += ["ensure_old_config"]
        else:
            from centralcli.config import Config
            config = Config()
            assert config.glp.ok == glp_ok  # HACK something prior to this is wiping out the Glp._client_id class attributes so config._mock(True) is unable to restore... So re instantiating config
        if fixture:  # pragma: no cover
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        cmd = f"{'' if glp_ok else '_'}subscription"
        result = runner.invoke(app, ["unassign", cmd, *args, "-y"])
        capture_logs(result, f"{env.current_test}-{'glp' if glp_ok else 'classic'}-{idx}")
        assert result.exit_code == 0
        assert "code: 20" in result.stdout  # glp 202 / classic 200

else:  # pragma: no cover
    ...
