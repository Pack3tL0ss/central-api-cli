import pytest
from typer.testing import CliRunner

from centralcli import config, utils
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, test_data

runner = CliRunner()


def test_unassign_label(ensure_cache_label1):
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "unassign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_unassign_label")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout


def test_unassign_label_multi(ensure_cache_label1):
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "unassign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            test_data["switch"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_unassign_label_multi")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["switch"]["serial"].upper() in result.stdout

if config.dev.mock_tests:
    @pytest.mark.parametrize(
        "idx,fixture,args",
        [
            [1, ["ensure_inv_cache_test_ap"], (test_data["test_devices"]["ap"]["serial"],)],
        ]
    )
    def test_unassign(idx: int, fixture: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixture:  # pragma: no cover
            [request.getfixturevalue(f) for f in utils.listify(fixture)]
        result = runner.invoke(app, ["unassign", "subscription", *args, "-y"])
        capture_logs(result, f"{env.current_test}{idx}")
        assert result.exit_code == 0
        assert "202" in result.stdout

else:  # pragma: no cover
    ...
