from typer.testing import CliRunner

from centralcli import log
from centralcli.cli import app
from centralcli.exceptions import ConfigNotFoundException

from . import test_data
from ._test_data import gw_group_config_file

runner = CliRunner()


def test_update_gw_group_config(ensure_cache_group_cloned):
    """Relies on group created in test_do.test_clone_group"""
    if not gw_group_config_file.is_file():  # pragma: no cover
        msg = f"{gw_group_config_file} Needs to be populated for this test.  Run 'cencli show config <group> --gw' for an example of GW group level config."
        raise ConfigNotFoundException(msg)
    result = runner.invoke(
        app,
        [
            "update",
            "config",
            test_data["clone"]["to_group"],
            str(gw_group_config_file),
            "--gw",
            "-Y"
        ]
    )
    if result.exit_code != 0:  # pragma: no cover
        log.error(f"Error in test_update_gw_group_config: {result.stdout}")
    assert result.exit_code == 0
    assert "Global Result:" in result.stdout
    assert "[OK]" in result.stdout
