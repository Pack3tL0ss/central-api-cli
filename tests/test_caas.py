from typer.testing import CliRunner

from centralcli import config
from centralcli.cli import app

from . import capture_logs

runner = CliRunner()

if config.dev.mock_tests:
    def test_caas_import_vlan():
        result = runner.invoke(
            app,
            [
                "caas",
                "import-vlan",
                "add-vlan-66",
                str(config.stored_tasks_file),
                "-Y"
            ]
        )
        capture_logs(result, "test_caas_import_vlan")
        assert result.exit_code == 0
        assert "uccess" in result.stdout
        assert "API" in result.stdout


    def test_caas_send_cmds():
        result = runner.invoke(
            app,
            [
                "caas",
                "send-cmds",
                "device",
                "20:4c:03:26:28:4c",
                "commands",
                "interface vlan 66",
                "no ip address",
                "!",
                "no interface vlan 66",
                "no vlan delme-66 66",
                "no vlan-name delme-66",
                "no vlan 66",
                "-Y"
            ]
        )
        capture_logs(result, "test_caas_send_cmds")
        assert result.exit_code == 0
        assert "uccess" in result.stdout
        assert "API" in result.stdout
