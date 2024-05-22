from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA
from . import test_site_file, test_data

runner = CliRunner()

def test_batch_add_sites():
    result = runner.invoke(app, ["batch", "add",  "sites", str(test_site_file), "-Y"])
    assert result.exit_code == 0
    assert "city" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout
    assert "state" in result.stdout or "_DUPLICATE_SITE_NAME" in result.stdout


def test_batch_del_sites():
    result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file), "-Y"])
    if test_site_file.is_file():
        test_site_file.unlink()
    assert result.exit_code == 0
    assert "success" in result.stdout
    assert result.stdout.count("success") == len(test_data["batch"]["sites"])
