from typer.testing import CliRunner
from cli import app
from . import test_data, gw_group_config_file, ConfigNotFoundError
import pytest


runner = CliRunner()


def do_nothing():
    ...

@pytest.fixture(scope='session', autouse=True)
def cleanup():
    # Will be executed before the first test
    yield do_nothing
    # executed after test is run
    result = runner.invoke(app, ["delete", "group", test_data["clone"]["to_group"], "-Y"])
    assert "Success" in result.stdout
    assert result.exit_code == 0

def test_update_gw_group_config(cleanup):
    if not gw_group_config_file.is_file():
        msg = f"{gw_group_config_file} Needs to be populated for this test.  Run 'cencli show config <group> --gw' for an example of GW group level config."
        raise ConfigNotFoundError(msg)
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
    assert result.exit_code == 0
    assert "Global Result:" in result.stdout
    assert "[OK]" in result.stdout
