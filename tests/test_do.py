from typer.testing import CliRunner
import pytest

from cli import app  # type: ignore # NoQA
from . import test_data
import json


runner = CliRunner()


def do_nothing():
    ...


@pytest.fixture(scope='session', autouse=True)
def cleanup():
    # Will be executed before the first test
    yield do_nothing()
    # executed after test is run
    result = runner.invoke(app, ["show", "cache", "groups", "--json"])
    del_groups = [g["name"] for g in json.loads(result.stdout) if g["name"].startswith("cencli_test_")]
    if del_groups:
        result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0

def test_bounce_interface():
    result = runner.invoke(app, ["bounce",  "interface", test_data["switch"]["name"].lower(),
                           test_data["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_bounce_poe():
    result = runner.invoke(app, ["bounce", "poe", test_data["switch"]["name"].lower(),
                           test_data["switch"]["test_port"], "-Y", "--debug"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_switch():
    result = runner.invoke(app, ["blink", test_data["switch"]["name"].lower(),
                           "on", "-Y"])
    assert result.exit_code == 0
    assert "state:" in result.stdout
    assert "task_id:" in result.stdout


def test_blink_wrong_dev_type():
    result = runner.invoke(
        app,
        [
            "blink",
            test_data["gateway"]["mac"],
            "on",
            "-Y"
        ]
    )
    assert result.exit_code == 1
    assert "Unable to gather" in result.stdout
    assert "excluded" in result.stdout


# This group remains as it is deleted in cleanup of test_update
def test_clone_group(cleanup):
    result = runner.invoke(app, ["-d", "clone", "group", test_data["gateway"]["group"], test_data["clone"]["to_group"], "-Y"])
    assert result.exit_code == 0  # TODO check this we are not returning a 1 exit_code on resp.ok = False?
    assert "201" in result.stdout or "400" in result.stdout
    assert "Created" in result.stdout or "already exists" in result.stdout

