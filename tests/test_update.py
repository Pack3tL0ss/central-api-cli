# from pathlib import Path
from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
import json
from pathlib import Path

# from . import TEST_DEVICES

runner = CliRunner()

test_dev_file = Path(__file__).parent / 'test_devices.json'
if test_dev_file.is_file():
    TEST_DEVICES = json.loads(test_dev_file.read_text())


def test_update_gw_group_config():
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



