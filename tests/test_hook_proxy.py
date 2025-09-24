from typer.testing import CliRunner

from centralcli import config
from centralcli.cli import app

from . import capture_logs, mock_sleep

runner = CliRunner()


if config.classic.webhook.token:
    def test_show_webhook_not_running():
        result = runner.invoke(app, ["show", "hook-proxy"])
        capture_logs(result, "test_show_webhook_not_running", expect_failure=True)
        assert result.exit_code == 1
        assert "not running" in result.stdout


    def test_start_hook_proxy():
        result = runner.invoke(app, ["start", "hook-proxy", "-y"])
        capture_logs(result, "test_start_hook_proxy")
        assert result.exit_code == 0
        assert "Started" in result.stdout


    def test_show_webhook_running():
        result = runner.invoke(app, ["show", "hook-proxy"])
        capture_logs(result, "test_show_webhook_running")
        assert result.exit_code == 0
        assert "listening" in result.stdout


    def test_stop_hook_proxy(ensure_hook_proxy_started):
        with mock_sleep:
            result = runner.invoke(app, ["stop", "hook-proxy", "-y"])
        capture_logs(result, "test_stop_hook_proxy")
        assert result.exit_code <= 1
        assert "erminate" in result.stdout