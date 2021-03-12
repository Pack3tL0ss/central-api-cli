from pathlib import Path
from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
import json

# from . import TEST_DEVICES

runner = CliRunner()

test_dev_file = Path(__file__).parent / 'test_devices.json'
if test_dev_file.is_file():
    TEST_DEVICES = json.loads(test_dev_file.read_text())


def test_do_bounce_interface():
    result = runner.invoke(app, ["bounce",  "interface", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_do_bounce_poe():
    result = runner.invoke(app, ["bounce", "poe", TEST_DEVICES["switch"]["name"].lower(),
                           TEST_DEVICES["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


# def test_do_move_dev_to_group():
#     result = runner.invoke(app, ["do", "move", "J9773A-80:C1:6E:CD:32:40",
#                            "wadelab", "-Y", "--debug"])
#     assert result.exit_code == 0
#     assert "Success" in result.stdout
