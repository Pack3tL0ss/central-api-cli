from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.exceptions import ConfigNotFoundException

from . import capture_logs
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
