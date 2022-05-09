# from pathlib import Path
from typer.testing import CliRunner
import pytest

from cli import app  # type: ignore # NoQA
import json
from pathlib import Path

# from . import TEST_DEVICES

runner = CliRunner()

test_dev_file = Path(__file__).parent / 'test_devices.json'
if test_dev_file.is_file():
    TEST_DEVICES = json.loads(test_dev_file.read_text())


def do_nothing():
    ...

@pytest.fixture(scope='session', autouse=True)
def cleanup():
    # Will be executed before the first test
    yield do_nothing
    # executed after test is run
    result = runner.invoke(app, ["delete", "group", TEST_DEVICES["clone"]["to_group"], "-Y"])
    assert "Success" in result.stdout
    assert result.exit_code == 0

def test_update_gw_group_config(cleanup):
    result = runner.invoke(
        app,
        [
            "update",
            "config",
            TEST_DEVICES["clone"]["to_group"],
            f"{Path(__file__).parent.parent / 'config' / '.cache' / 'test_runner_gw_grp_config'}",
            "--gw",
            "-Y"
        ]
    )
    assert result.exit_code == 0
    assert "Global Result:" in result.stdout
    assert "[OK]" in result.stdout
    cleanup()


# Lots of rules around what can be updated once the group is created
# def test_update_group():
#     result = runner.invoke(
#         app,
#         [
#             "update",
#             "group",
#             "cencli_test_group2",
#             "--aos10",
#             "--gw",
#             "--ap",
#             "--gw-role",
#             "wlan",
#             "-Y"
#         ]
#     )
#     assert result.exit_code == 0
#     assert "Success" in result.stdout



