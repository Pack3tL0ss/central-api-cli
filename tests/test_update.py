from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.exceptions import ConfigNotFoundException

from . import capture_logs, config, test_data
from ._test_data import gw_group_config_file

runner = CliRunner()


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
            "'100 Bledsoe Park Rd'",
            "Gallatin",
            "TN",
            "37066",
            "-Y"
        ]
    )
    capture_logs(result, "test_update_site")
    assert result.exit_code == 0
    assert "API" in result.stdout


# TODO need cencli update command
def test_update_mpsk(ensure_cache_mpsk):
    result = runner.invoke(
        app,
        [
            "test",
            "method",
            "update_named_mpsk",
            "1EBTWK86LPQ86S0B",
            "4e650830-d4d6-4a19-b9af-e0f776c69d24",
            "enabled=True",
            "reset=True"
        ]
    )
    capture_logs(result, "test_update_mpsk")
    assert result.exit_code == 0
    assert "204" in result.stdout


# TODO need cencli update command
def test_update_guest(ensure_cache_guest1):
    result = runner.invoke(
        app,
        [
            "test",
            "method",
            "update_guest",
            "portal_id=e5538808-0e05-4ecd-986f-4bdce8bf52a4",
            "visitor_id=7c9eb0df-b211-4225-94a6-437df0dfca59",
            "name=superlongemail@kabrew.com",
            "company_name=ConsolePi",
            "phone=+16155551212",
            "email=superlongemail@kabrew.com",
            "valid_till_days=30"
        ]
    )
    capture_logs(result, "test_update_guest")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_update_template(ensure_cache_template):
    result = runner.invoke(
        app,
        [
            "update",
            "template",
            "cencli_test_template",
            test_data["template"]["template_file"],
            "--yes",
        ]
    )
    capture_logs(result, "test_update_template")
    assert result.exit_code == 0
    assert "200" in result.stdout

if config.dev.mock_tests:
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
