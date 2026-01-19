import pytest
from typer.testing import CliRunner
from typing import Callable

from centralcli import config
from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, mock_sleep

runner = CliRunner()


if config.classic.webhook.token:
    def test_show_webhook_not_running():
        result = runner.invoke(app, ["show", "hook-proxy"])
        capture_logs(result, "test_show_webhook_not_running", expect_failure=True)
        assert result.exit_code == 1
        assert "not running" in result.stdout


    def test_start_hook_proxy():
        result = runner.invoke(app, ["start", "hook-proxy", "-yy"])
        capture_logs(result, "test_start_hook_proxy")
        assert result.exit_code == 0
        assert "Started" in result.stdout


    # start_hook_proxy needs to be ran for this to pass
    @pytest.mark.parametrize(
        "idx,args,pass_condition",
        [
            [1, (), lambda r: "listening" in r],
            [2, ("logs",), lambda r: "INFO" in r],
        ]
    )
    def test_show_webhook_running(idx: int, args: tuple[str], pass_condition: Callable):
        result = runner.invoke(app, ["show", "hook-proxy", *args])
        capture_logs(result, f"{env.current_test}-{idx}")
        assert result.exit_code == 0
        assert pass_condition(result.stdout)


    def test_stop_hook_proxy(ensure_hook_proxy_started):
        with mock_sleep:
            result = runner.invoke(app, ["stop", "hook-proxy", "-y"])
        capture_logs(result, "test_stop_hook_proxy")
        assert result.exit_code <= 1
        assert "erminate" in result.stdout

else:  # pragma: no cover
    ...