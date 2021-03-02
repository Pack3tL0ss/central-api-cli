from typer.testing import CliRunner

from cli import app  # type: ignore # NoQA

runner = CliRunner()

# test_dev_file = Path(__file__).parent / 'test_devices.json'
# if test_dev_file.is_file():
#     TEST_DEVICES = json.loads(test_dev_file.read_text())


def test_del_group():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group1",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout


def test_del_group_multiple():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group2",
        "cencli_test_group3",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert result.stdout.count("Success") == 2
