from typing import Callable

import pytest
from typer.testing import CliRunner

from centralcli import utils
from centralcli.cli import app
from centralcli.environment import env
from centralcli.exceptions import ConfigNotFoundException

from . import capture_logs, config, test_data
from ._test_data import gw_group_config_file, test_ap_ui_group_template, test_ap_ui_group_variables

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
        "fixture,args,pass_condition",
        [
            ["ensure_dev_cache_test_ap",
                (
                    test_data["mesh_ap"]["serial"],
                    "-a",
                    test_data["mesh_ap"]["altitude"] - 0.1
                ),
                None
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
                lambda r: "skipped" in r
            ],
            [
                [
                    "ensure_dev_cache_test_flex_dual_ap",
                    "ensure_dev_cache_test_ap",
                ],
                (
                    "cencli-test-flex-dual-ap",
                    test_data["test_devices"]["ap"]["serial"],
                    "-e",
                    "2.4",
                ),
                lambda r: "skipped" in r
            ],
        ]
    )
    def test_update_ap(fixture: str | list[str] | None, args: tuple[str], pass_condition: Callable | None, request: pytest.FixtureRequest):
        if fixture:
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(app, ["update",  "ap", *args, "-y"])
        capture_logs(result, "test_upgrade_ap")
        assert result.exit_code == 0
        assert "200" in result.stdout
        if pass_condition:
            assert pass_condition(result.stdout)


    @pytest.mark.parametrize(
        "fixture,args",
        [
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
            ],
        ]
    )
    def test_update_ap_fail(fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:
            request.getfixturevalue(fixture)
        result = runner.invoke(app, ["update",  "ap", *args, "-y"])
        capture_logs(result, env.current_test, expect_failure=True)
        assert result.exit_code == 1
        assert "403" in result.stdout


    def test_update_ap_invalid():
        result = runner.invoke(app, ["update",  "ap", test_data["mesh_ap"]["serial"], test_data["ap"]["serial"], "--hostname", "this_will_fail"])
        capture_logs(result, "test_update_ap_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "multiple" in result.stdout


    def test_update_wlan():
        result = runner.invoke(app, ["update",  "wlan", test_data["update_wlan"]["ssid"], "--psk", "cencli_test_psk", "-y"])
        capture_logs(result, "test_upgrade_wlan")
        assert result.exit_code == 0
        assert test_data["update_wlan"]["ssid"].upper() in result.stdout.upper()


    def test_update_wlan_by_group():
        result = runner.invoke(app, ["update",  "wlan", test_data["update_wlan"]["ssid"], test_data["update_wlan"]["group"], "--psk", "cencli_test_psk", "-y"])
        capture_logs(result, "test_upgrade_wlan_by_group")
        assert result.exit_code == 0
        assert test_data["update_wlan"]["ssid"].upper() in result.stdout.upper()

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

else:  # pragma: no cover
    ...


def test_update_cloned_group(ensure_cache_group_cloned):
    result = runner.invoke(
        app,
        [
            "update",
            "group",
            "cencli_test_cloned",
            "--gw",
            "-Y"
        ]
    )
    capture_logs(result, "test_update_cloned_group")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "uccess" in result.stdout


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
    "args",
    [
        ([]),
        ([str(test_ap_ui_group_variables)]),
    ]
)
def test_update_config(ensure_cache_group4, args: list[str]):
    result = runner.invoke(
        app,
        [
            "update",
            "config",
            "--yes",
            "--ap",
            "cencli_test_group4",
            str(test_ap_ui_group_template),
            *args
        ]
    )
    capture_logs(result, "test_update_config")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_update_cp_cert(ensure_cache_group1, ensure_cache_cert):
    result = runner.invoke(
        app,
        [
            "update",
            "cp-cert",
            "cencli_test",
            "-G",
            "cencli_test_group1",
            "--yes",
        ]
    )
    capture_logs(result, "test_update_cp_cert")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_update_cp_cert_no_group(ensure_cache_cert):
    result = runner.invoke(
        app,
        [
            "update",
            "cp-cert",
            "cencli_test"
        ]
    )
    capture_logs(result, "test_update_cp_cert_no_group", expect_failure=True)
    assert result.exit_code == 1
    assert "Invalid" in result.stdout


def test_update_cp_cert_invalid_group(ensure_cache_cert, ensure_cache_group4):
    result = runner.invoke(
        app,
        [
            "update",
            "cp-cert",
            "cencli_test",
            "cencli_test_group4"
        ]
    )
    capture_logs(result, "test_update_cp_cert_invalid_group", expect_failure=True)
    assert result.exit_code == 1
    assert "not supported" in result.stdout
