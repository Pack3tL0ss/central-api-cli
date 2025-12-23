from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import utils
from centralcli.cli import app
from centralcli.environment import env
from centralcli.exceptions import ConfigNotFoundException

from . import cache, capture_logs, config, test_data
from ._test_data import gw_group_config_file, test_ap_ui_group_template, test_ap_ui_group_variables, test_banner_file

runner = CliRunner()


if config.dev.mock_tests:
    def test_update_ap_same_as_current():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"], "-a", test_data["mesh_ap"]["altitude"], "-y"])
        capture_logs(result, "test_update_ap_same_as_current")
        assert result.exit_code == 0
        assert "skipped" in result.stdout


    def test_update_ap_no_change():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"]])
        capture_logs(result, "test_upgrade_group_no_change", expect_failure=True)
        assert result.exit_code == 1
        assert "NO CHANGES" in result.stdout.upper()


    @pytest.mark.parametrize(
        "fixture,args,pass_condition,test_name_append",
        [
            [
                "ensure_dev_cache_test_ap",
                (
                    test_data["mesh_ap"]["serial"],
                    "-a",
                    test_data["mesh_ap"]["altitude"] - 0.1
                ),
                None,
                None
            ],
            [
                "ensure_dev_cache_test_ap",
                (
                    test_data["mesh_ap"]["serial"],
                    "-a",
                    test_data["mesh_ap"]["altitude"]
                ),
                None,
                "no_gps_in_config",
            ],
            [
                "ensure_dev_cache_test_ap",
                (
                    test_data["test_devices"]["ap"]["serial"],
                    "--ip",
                    "10.0.31.6",
                    "--mask",
                    "255.255.255.0",
                    "--gateway",
                    "10.0.31.1",
                    "--dns",
                    "10.0.30.51,10.0.30.52",
                    "--domain",
                    "consolepi.com"
                ),
                None,
                None
            ],
            [
                "ensure_dev_cache_test_ap",
                (
                    test_data["test_devices"]["ap"]["serial"],
                    "-u",
                    "31",
                    "-R"
                ),
                None,
                None
            ],
            [
                "ensure_dev_cache_test_ap",
                (
                    test_data["mesh_ap"]["serial"],
                    test_data["test_devices"]["ap"]["serial"],
                    "-w",
                    "narrow",
                ),
                lambda r: "skipped" in r,
                None
            ],
            [
                [
                    "ensure_dev_cache_test_ap",
                    "ensure_dev_cache_test_flex_dual_ap"
                ],
                (
                    "cencli-test-flex-dual-ap",
                    test_data["test_devices"]["ap"]["serial"],
                    "-e",
                    "2.4",
                ),
                lambda r: "skipped" in r,
                None
            ],
            [
                "ensure_dev_cache_test_flex_dual_ap",
                (
                    "cencli-test-flex-dual-ap",
                    "-e",
                    "5",
                ),
                None,
                None
            ],
            [
                "ensure_dev_cache_test_flex_dual_ap",
                (
                    "cencli-test-flex-dual-ap",
                    "-e",
                    "6",
                ),
                None,
                None
            ],
            [
                "ensure_dev_cache_test_dyn_ant_ap",
                (
                    "cencli-test-dyn-ant-ap",
                    "-w",
                    "wide",
                ),
                None,
                None
            ],
        ]
    )
    def test_update_ap(fixture: str | list[str] | None, args: tuple[str], pass_condition: Callable | None, test_name_append: str | None, request: pytest.FixtureRequest):
        if test_name_append:
            env.current_test = f"{env.current_test}_{test_name_append}"
        [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(app, ["update",  "ap", *args, "-y"])
        capture_logs(result, env.current_test)
        assert result.exit_code == 0
        assert "200" in result.stdout
        if pass_condition:
            assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,fixture,args,pass_condition,test_name_append",
        [
            [
                1,
                "ensure_dev_cache_test_ap",
                (
                    test_data["test_devices"]["ap"]["serial"],
                    "--ip",
                    "10.0.31.6",
                    "--mask",
                    "255.255.255.0",
                    "--gateway",
                    "10.0.31.1",
                    "--dns",
                    "10.0.30.51,10.0.30.52",
                    "--domain",
                    "consolepi.com"
                ),
                lambda r: "403" in r,
                None
            ],
            [
                2,
                None,
                (
                    test_data["mesh_ap"]["serial"],
                    "-a",
                    test_data["mesh_ap"]["altitude"] - 0.1
                ),
                lambda r: "500" in r,
                None
            ],
            [
                3,
                None,
                (
                    test_data["mesh_ap"]["serial"],
                    "-a",
                    test_data["mesh_ap"]["altitude"] - 0.1
                ),
                lambda r: "500" in r,
                "get"
            ],
            [
                4,
                "ensure_dev_cache_test_ap",
                (
                    test_data["mesh_ap"]["serial"],
                    test_data["ap"]["serial"],
                    "--hostname",
                    "this_will_fail"
                ),
                lambda r: "⚠" in r,
                None
            ]
        ]
    )
    def test_update_ap_fail(idx: int, fixture: str | None, args: tuple[str], pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest):
        if test_name_append:
            env.current_test = f"{env.current_test}_{test_name_append}"
        if fixture:
            request.getfixturevalue(fixture)
        result = runner.invoke(app, ["update",  "ap", *args, "-y"])
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
        assert result.exit_code == 1
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "args",
        [
            (test_data["update_wlan"]["ssid"], "--psk", "cencli_test_psk"),
            (test_data["update_wlan"]["ssid"], test_data["update_wlan"]["group"], "--psk", "cencli_test_psk"),
        ]
    )
    def test_update_wlan(args: tuple[str]):
        result = runner.invoke(app, ["update",  "wlan", *args, "-y"])
        capture_logs(result, "test_upgrade_wlan")
        assert result.exit_code == 0
        assert test_data["update_wlan"]["ssid"].upper() in result.stdout.upper()


    @pytest.mark.parametrize(
        "_,fixture,args,pass_condition,test_name_append",
        [
            [1, None, (test_data["update_wlan"]["ssid"], "--psk", "cencli_test_psk"), lambda r: "Response" in r, None],
            [2, None, (test_data["update_wlan"]["ssid"], "--psk", "cencli_test_psk"), lambda r: "⚠" in r, "no_groups_w_ssid"],
            [3, None, (test_data["update_wlan"]["ssid"], test_data["update_wlan"]["group"], "--psk", "cencli_test_psk"), lambda r: "⚠" in r, None],
            [4, "ensure_cache_group1", (test_data["update_wlan"]["ssid"], "cencli_test_group1", "--psk", "cencli_test_psk"), lambda r: "Response" in r, None],
        ]
    )
    def test_update_wlan_fail(_: int, fixture: str | None, args: tuple[str], pass_condition: Callable, test_name_append: str | None, request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        if test_name_append:
            env.current_test = f"{env.current_test}_{test_name_append}"
        result = runner.invoke(app, ["update",  "wlan", *args, "-y"])
        capture_logs(result, "test_upgrade_wlan_fail", expect_failure=True)
        assert result.exit_code == 1
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "fixture,args",
        [
            [None, ("cencli_test_template", test_data["template"]["template_file"],)],
            ["ensure_cache_group2", ("cencli_test_template", "--group", "cencli_test_group2", test_data["template"]["template_file"])],
            ["ensure_dev_cache_test_switch", ("cencli-test-sw", "--version", "16.11.0026", test_data["template"]["template_file"])],
        ]
    )
    def test_update_template(ensure_cache_template, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        result = runner.invoke(
            app,
            [
                "update",
                "template",
                *args,
                "--yes",
            ]
        )
        capture_logs(result, "test_update_template")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_variable():
        result = runner.invoke(
            app,
            [
                "update",
                "variables",
                test_data["test_devices"]["switch"]["serial"],
                "mac_auth_ports",
                "=",
                "5",
                "-y"
            ]
        )
        capture_logs(result, "test_update_variable")
        assert result.exit_code == 0
        assert "200" in result.stdout

    def test_update_webhook():
        result = runner.invoke(
            app,
            [
                "update",
                "webhook",
                "851cb87d-8e10-49f9-84a6-a256bad891ea",
                "cencli_test",
                "https://wh.consolepi.com",
                "--yes",
            ]
        )
        capture_logs(result, "test_update_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout

    @pytest.mark.parametrize(
        "_,fixture,args,test_name_append",
        [
            [1, "ensure_cache_group_cloned", ("--gw", "--sw"), None],
            [2, "ensure_cache_group_cloned", ("--sw", "--mo-sw", "--cx", "--mo-cx"), None],
            [3, "ensure_cache_group_cloned", ("--wlan-tg", "--cx", "--wired-tg"), None],  # Not sure you can actually update a non TG to a TG
            [4, "ensure_cache_group_cloned_cx_only", ("--ap", "--aos10",), "cx_only"],
            [5, "ensure_cache_group_cloned_cx_only", ("--ap", "--aos10", "--mb"), "cx_only"],
        ]
    )
    def test_update_group(_: int, fixture: str, args: tuple[str], test_name_append: str | None, request: pytest.FixtureRequest):
        cache.responses.clear()
        request.getfixturevalue(fixture)
        if test_name_append:
            env.current_test = f"{env.current_test}_{test_name_append}"
            config.debugv = True  # also test debugv condition in update_group_properties
        result = runner.invoke(
            app,
            [
                "update",
                "group",
                "cencli_test_cloned",
                *args,
                "-Y"
            ]
        )
        capture_logs(result, "test_update_group")
        assert result.exit_code == 0
        assert "200" in result.stdout
        assert "uccess" in result.stdout


    @pytest.mark.parametrize(
        "_,args,pass_condition",
        [
            [1 ,(), lambda r: "⚠" in r],
            [2 ,("--mb",), lambda r: "⚠" in r],
            [3 ,("--mo-sw",), lambda r: "⚠" in r],  # --mo-sw without --sw
            [4 ,("--mo-cx",), lambda r: "⚠" in r],  # --mo-cx without --cx
            [5 ,("--mo-cx", "--wired-tg"), lambda r: "⚠" in r],  # --mo-cx and tg
            [6 ,("--aos10", "--mb", "--gw-role", "wlan"), lambda r: "initially added" in r],  # aos10 can only be set when initially adding ap as valid type
        ]
    )
    def test_update_group_fail(ensure_cache_group_cloned, _: int, args: tuple[str], pass_condition: Callable):
        result = runner.invoke(
            app,
            [
                "update",
                "group",
                "cencli_test_cloned",
                *args,
                "-Y"
            ]
        )
        capture_logs(result, "test_update_group_fail", expect_failure=True)
        assert result.exit_code == 1
        assert pass_condition(result.stdout)



    def test_update_gw_group_config(ensure_cache_group_cloned):
        if not gw_group_config_file.is_file():  # pragma: no cover
            msg = f"{gw_group_config_file} Needs to be populated for this test.  Run 'cencli show config <group> --gw' for an example of GW group level config."
            raise ConfigNotFoundException(msg)
        result = runner.invoke(
            app,
            [
                "update",
                "config",
                "cencli_test_cloned",
                str(gw_group_config_file),
                "--gw",
                "-Y"
            ]
        )
        capture_logs(result, "test_update_gw_group_config")
        assert result.exit_code == 0
        assert "Global Result:" in result.stdout
        assert "[OK]" in result.stdout


    def test_update_site(ensure_cache_site4):
        result = runner.invoke(
            app,
            [
                "update",
                "site",
                "cencli_test_site4",
                "'400 Zieglers Fort Rd'",
                "Gallatin,",
                "TN",
                "37066",
                "-Y"
            ]
        )
        capture_logs(result, "test_update_site")
        assert result.exit_code == 0
        assert "API" in result.stdout


    def test_update_site_no_data(ensure_cache_site4):
        result = runner.invoke(
            app,
            [
                "update",
                "site",
                "cencli_test_site4",
            ]
        )
        capture_logs(result, "test_update_site_no_data", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout


    def test_update_guest_disable(ensure_cache_guest1):
        result = runner.invoke(
            app,
            [
                "update",
                "guest",
                test_data["portal"]["name"],
                test_data["portal"]["guest"]["name"],
                "-DY",
            ]
        )
        capture_logs(result, "test_update_guest_disable")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_guest_enable(ensure_cache_guest1):
        result = runner.invoke(
            app,
            [
                "update",
                "guest",
                test_data["portal"]["name"],
                test_data["portal"]["guest"]["name"],
                "-EY",
            ]
        )
        capture_logs(result, "test_update_guest_enable")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_guest_phone(ensure_cache_guest1):
        result = runner.invoke(
            app,
            [
                "update",
                "guest",
                test_data["portal"]["name"],
                test_data["portal"]["guest"]["name"],
                "--phone",
                test_data["portal"]["guest"]["phone"],
                "-Y",
            ]
        )
        capture_logs(result, "test_update_guest_phone")
        assert result.exit_code == 0
        assert "200" in result.stdout


    def test_update_guest_invalid():
        result = runner.invoke(
            app,
            [
                "update",
                "guest",
                test_data["portal"]["name"],
                test_data["portal"]["guest"]["name"],
                "-EDY",
            ]
        )
        capture_logs(result, "test_update_guest_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "Invalid" in result.stdout


    @pytest.mark.parametrize(
        "idx,fixtures,args,test_name_append",
        [
            [1, "ensure_cache_group4", ("cencli_test_group4", "--ap"), None],
            [2, "ensure_cache_group4", ("cencli_test_group4", str(test_ap_ui_group_variables), "--ap"), None],
            [3, ["ensure_cache_group1", "ensure_dev_cache_test_ap"], ("cencli-test-ap", "--banner-file", str(test_banner_file)), None],
        ]
    )
    def test_update_config(fixtures: str | list[str] | None, idx: int, args: tuple[str], test_name_append: str | None, request: pytest.FixtureRequest):
        if test_name_append:  # pragma: no cover
            env.current_test = f"{env.current_test}_{test_name_append}"
        if fixtures:
            [request.getfixturevalue(fixture) for fixture in utils.listify(fixtures)]
        _args = args if "--banner-file" in args else [args[0], str(test_ap_ui_group_template), *args[1:]]
        result = runner.invoke(
            app,
            [
                "update",
                "config",
                *_args,
                "--yes",
            ]
        )
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert "200" in result.stdout


    @pytest.mark.parametrize(
        "idx,fixture,args",
        [
            [1, None, (test_data["ap"]["serial"], "--gw")],
            [2, None, (test_data["gateway"]["serial"], "--ap")],
            [3, "ensure_cache_group4", ("cencli_test_group4",)],
            [4, None, (test_data["gateway"]["serial"], "--banner-file", str(test_banner_file))],
        ]
    )
    def test_update_config_invalid(fixture: str | None, idx: int, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        _args = args if "--banner-file" in args else [args[0], str(test_ap_ui_group_template), *args[1:]]
        result = runner.invoke(
            app,
            [
                "update",
                "config",
                *_args,
            ]
        )
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout


    @pytest.mark.parametrize(
        "idx,fixture,args,expect_failure,pass_condition",
        [
            [1, ["ensure_cache_cert", "ensure_cache_group1"], ("cencli_test", "-G", "cencli_test_group1",), False, lambda r: "200" in r],
            [2, "ensure_cache_cert", ("cencli_test",), True, lambda r: "⚠" in r],  # no group
            [3, ["ensure_cache_cert", "ensure_cache_group4"], ("cencli_test", "-G", "cencli_test_group4",), True, lambda r: "⚠" in r], # invalid group (no aps/gws)
            [4, ["ensure_cache_cert_same_as_existing", "ensure_cache_group1"], ("cencli_test-existing-cert", "-G", "cencli_test_group1",), True, lambda r: "skipped" in r], # cert same as existing
            [5, ["ensure_cache_cert_expired", "ensure_cache_group1"], ("cencli-test-expired-cert", "-G", "cencli_test_group1",), True, lambda r: "xpired" in r], # cert expired
        ]
    )
    def test_update_cp_cert(idx: int, fixture: str | None, args: tuple[str], expect_failure: bool, pass_condition: Callable, request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(
            app,
            [
                "update",
                "cp-cert",
                *args,
                "--yes",
            ]
        )
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=expect_failure)
        assert result.exit_code == (0 if not expect_failure else 1)
        assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "idx,fixture,args,expect_failure,pass_condition",
        [
            [1, "ensure_cache_group1", ("cencli_test", "-G", "cencli_test_group1",), True, lambda r: "Response" in r],
        ]
    )
    def test_update_cp_cert_fail(ensure_cache_cert, idx: int, fixture: str | None, args: tuple[str], expect_failure: bool, pass_condition: Callable, request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(
            app,
            [
                "update",
                "cp-cert",
                *args,
                "--yes",
            ]
        )
        capture_logs(result, f"{env.current_test}{idx}", expect_failure=expect_failure)
        assert result.exit_code == (0 if not expect_failure else 1)
        assert pass_condition(result.stdout)

else:  # pragma: no cover
    ...