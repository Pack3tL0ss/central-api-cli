import pytest
from typer.testing import CliRunner

from centralcli import config, utils
from centralcli.cli import app

from . import capture_logs
from ._test_data import test_caas_devs_commands_file, test_caas_empty_commands_file, test_caas_groups_commands_file, test_caas_invalid_commands_file, test_caas_sites_commands_file

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

    mock_commands = [
        "interface vlan 66",
        "no ip address",
        "!",
        "no interface vlan 66",
        "no vlan delme-66 66",
        "no vlan-name delme-66",
        "no vlan 66",
    ]
    @pytest.mark.parametrize(
        "_,fixtures,args", [
            [1, "ensure_cache_group_cloned_w_gw", ("device", "mock-gw", "commands", *mock_commands)],
            [2, "ensure_cache_group_cloned_w_gw", ("group", "cencli_test_cloned", "commands", *mock_commands)],
            [3, "ensure_cache_group_cloned_w_gw", ("group", "cencli_test_cloned", "-A", "command", *mock_commands)],
            [4, "ensure_cache_site1", ("site", "cencli_test_site1", "commands", *mock_commands)],
            [5, ["ensure_cache_site1", "ensure_cache_group_cloned_w_gw"], ("file", str(test_caas_devs_commands_file))],
            [6, ["ensure_cache_group1", "ensure_cache_group4", "ensure_cache_group_cloned_w_gw"], ("file", str(test_caas_groups_commands_file))],
            [7, ["ensure_cache_site1", "ensure_cache_site4"], ("file", str(test_caas_sites_commands_file))],
        ]
    )
    def test_caas_send_cmds(_: int, ensure_dev_cache_batch_devices, fixtures: str | list[str] | None, args: tuple[str], request: pytest.FixtureRequest):
        [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        result = runner.invoke(app, ["caas", "send-cmds", *args, "--yes"])
        capture_logs(result, "test_caas_send_cmds")
        assert result.exit_code == 0
        assert "uccess" in result.stdout
        assert "API" in result.stdout

    @pytest.mark.parametrize(
        "_,fixtures,args", [
            [1, None, ("device", "20:4c:03:26:28:4c")],  # device doesn't exist
            [2, "ensure_cache_group4", ("group", "cencli_test_group4", "-A", *mock_commands)],  # no gateways in group
            [3, ["ensure_cache_site1", "ensure_cache_group_cloned_w_gw"], ("file", str(test_caas_devs_commands_file), "commands", "extra", "commands")],
            [4, None, ("file", str(test_caas_empty_commands_file),)],  # empty file no data parsed ...
            [5, None, ("file", str(test_caas_invalid_commands_file),)],  # invalid file (invalid keys) ...
        ]
    )
    def test_caas_send_cmds_invalid(_: int, fixtures: str | None, args: tuple[str], request: pytest.FixtureRequest):
        if fixtures:
            [request.getfixturevalue(f) for f in utils.listify(fixtures)]
        result = runner.invoke(
            app,
            [
                "caas",
                "send-cmds",
                *args
            ]
        )
        capture_logs(result, "test_caas_send_cmds_invalid", expect_failure=True)
        assert result.exit_code == 1
        assert "⚠" in result.stdout

else:  # pragma: no cover
    ...
