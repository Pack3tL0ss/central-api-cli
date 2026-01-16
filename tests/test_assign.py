import pytest
from typer.testing import CliRunner

from centralcli import config
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, test_data

runner = CliRunner()


def test_assign_label(ensure_cache_label1):
    """Relies on label created in test_add.test_add_label"""
    result = runner.invoke(
        app,
        [
            "assign",
            "label",
            "cencli_test_label1",
            test_data["ap"]["name"],
            test_data["switch"]["name"],
            "-Y"
        ]
    )
    capture_logs(result, "test_assign_label")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert test_data["ap"]["serial"].upper() in result.stdout


if config.dev.mock_tests:
    @pytest.mark.parametrize("glp_ok", [False, True])
    def test_assign_subscription(glp_ok: bool, request: pytest.FixtureRequest):  # ensure cache sub... ensures the sub is there but with 0 remaining, forces it to hit a branch that log/shows a warning (glp only)
        if glp_ok:
            request.getfixturevalue("ensure_cache_subscription_none_available")  # No sub cache for non glp
        config._mock(glp_ok)
        result = runner.invoke(
            app,
            [
                "assign",
                f"{'_' if not glp_ok else ''}subscription",  #  determination on which should be hidden is performed before we mock non glp config
                "advanced-ap",
                test_data["ap"]["name"],
                "-Y"
            ]
        )
        capture_logs(result, f"{env.current_test}-{'glp' if config.glp.ok else 'classic'}")
        assert result.exit_code == 0
        assert "Response" in result.stdout
        if glp_ok:
            assert "⚠" in result.stdout
