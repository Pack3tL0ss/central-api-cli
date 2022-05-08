from pathlib import Path
from typer.testing import CliRunner
import pytest

from cli import app  # type: ignore # NoQA
import json

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
    result = runner.invoke(app, ["show", "cache", "groups", "--json"])
    del_groups = [g for g in json.loads(result.stdout) if g.startswith("cencli_test_")]
    result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
    assert "Success" in result.stdout
    assert result.exit_code == 0

def test_bounce_interface():
    result = runner.invoke(app, ["bounce",  "interface", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_bounce_poe():
    result = runner.invoke(app, ["bounce", "poe", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch():
    result = runner.invoke(app, ["blink", TEST_DEVICES["switch"]["name"].lower(),
                           "on", "-Y"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_wrong_dev_type():
    result = runner.invoke(
        app,
        [
            "blink",
            TEST_DEVICES["gateway"]["mac"],
            "on",
            "-Y"
        ]
    )
    assert result.exit_code == 1
    assert "Unable to gather" in result.stdout
    assert "excluded" in result.stdout


def test_clone_group(cleanup):
    result = runner.invoke(app, ["clone", "group", TEST_DEVICES["gateway"]["group"], TEST_DEVICES["clone"]["to_group"], "-Y"])
    assert result.exit_code == 0
    assert "201" in result.stdout
    assert "Created" in result.stdout
    cleanup()


# def test_do_move_dev_to_group():
#     result = runner.invoke(app, ["do", "move", "J9773A-80:C1:6E:CD:32:40",
#                            "wadelab", "-Y", "--debug"])
#     assert result.exit_code == 0
#     assert "Success" in result.stdout
