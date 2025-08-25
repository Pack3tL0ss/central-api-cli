import pendulum
from typer.testing import CliRunner

from centralcli.cli import app

from . import capture_logs, test_data

runner = CliRunner()


def test_show_wids_group():
    result = runner.invoke(app, [
            "show",
            "wids",
            "--group",
            test_data["ap"]["group"]
        ]
    )
    capture_logs(result, "test_show_wids_group")
    assert result.exit_code == 0
    assert "ogue" in result.stdout


def test_show_wids_rogues_by_site():
    result = runner.invoke(app, [
            "show",
            "wids",
            "rogues",
            "--site",
            test_data["ap"]["site"]
        ]
    )
    capture_logs(result, "test_show_wids_rogues_by_site")
    assert result.exit_code == 0
    assert "ogue" in result.stdout


def test_show_wids_neighbors_by_label():
    result = runner.invoke(app, [
            "show",
            "wids",
            "neighbors",
            "--label",
            "cencli_test_label1"
        ]
    )
    capture_logs(result, "test_show_wids_neighbors_by_label")
    assert result.exit_code == 0
    assert "ogue" in result.stdout or "Empty Response" in result.stdout


def test_show_wids_interfering():
    now = pendulum.now()
    result = runner.invoke(app, [
            "show",
            "wids",
            "interfering",
            "--end",
            f"{now.month}/{now.day}/{now.year}-{now.hour}:{now.minute}"
        ]
    )
    capture_logs(result, "test_show_wids_interfering")
    assert result.exit_code == 0
    assert "Interfering" in result.stdout


def test_show_wids_wrong_swarm_version():
    result = runner.invoke(app, [
            "show",
            "wids",
            "interfering",
            "-S",
            test_data["ap"]["mac"]
        ]
    )
    capture_logs(result, "test_show_wids_wrong_swarm_version")
    assert result.exit_code != 0
    assert "AOS8" in result.stdout
