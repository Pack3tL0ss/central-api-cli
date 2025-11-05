from typing import Callable

import pendulum
import pytest
from typer.testing import CliRunner

from centralcli.cli import app
from centralcli.environment import env

from . import capture_logs, test_data

runner = CliRunner()

now = pendulum.now()
@pytest.mark.parametrize(
    "fixture,args,pass_condition", [
        [None, ("--group", test_data["ap"]["group"]), lambda r: "ogue" in r],
        [None, ("rogues", "--site", test_data["ap"]["site"]), lambda r: "ogue" in r],
        ["ensure_cache_label1", ("neighbors", "--label", "cencli_test_label1"), lambda r: "ogue" in r or "Empty Response" in r],
        [None, ("interfering", "--end", f"{now.month}/{now.day}/{now.year}-{now.hour}:{now.minute}"), lambda r: "Interfering" in r],
        [None, ("suspect",), lambda r: "Suspect" in r],
    ]
)
def test_show_wids(fixture: str | None, args: tuple[str], pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = runner.invoke(app, [
            "show",
            "wids",
            *args
        ]
    )
    capture_logs(result, "test_show_wids")
    assert result.exit_code == 0
    assert pass_condition(result.stdout)


@pytest.mark.parametrize(
    "args,pass_condition,test_name_append", [
        [("interfering", "-S", test_data["ap"]["mac"]), lambda result: result.exit_code == 1 and "AOS8" in result.stdout, None],
        [(), lambda result: result.exit_code <= 1 and "⚠" in result.stdout, "partial"],
    ]
)
def test_show_wids_fail(args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, [
            "show",
            "wids",
            *args
        ]
    )
    capture_logs(result, "test_show_wids_fail", log_output=pass_condition(result))
    assert pass_condition(result)
