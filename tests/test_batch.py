from pathlib import Path
from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
import json

runner = CliRunner()

test_file = Path(__file__).parent / 'test_devices.json'
if test_file.is_file():
    TEST_DATA = json.loads(test_file.read_text())

test_site_file = test_file.parent.parent / "config" / ".cache" / "test_runner_sites.json"


test_site_file.write_text(
    json.dumps(TEST_DATA["batch"]["sites"])
)


def test_batch_add_sites():
    result = runner.invoke(app, ["batch", "add",  "sites", str(test_site_file), "-Y"])
    assert result.exit_code == 0
    assert "city" in result.stdout
    assert "state" in result.stdout


def test_batch_del_sites():
    result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file), "-Y"])
    if test_site_file.is_file():
        test_site_file.unlink()
    assert result.exit_code == 0
    assert "success" in result.stdout
    assert result.stdout.count("success") == len(TEST_DATA["batch"]["sites"])
