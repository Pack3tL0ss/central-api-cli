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
    "idx,args,pass_condition,test_name_append", [
        [1, ("interfering", "-S", test_data["ap"]["mac"]), lambda r: "AOS8" in r, None],
        [2, (), lambda r: "⚠" in r, "partial"],  # TODO partial failure should return 1 as exit_code (currently does not)
        [3, (), lambda r: "Response" in r, "all"],
    ]
)
def test_show_wids_fail(idx: int, args: tuple[str], pass_condition: Callable, test_name_append: str | None):
    if test_name_append:
        env.current_test = f"{env.current_test}_{test_name_append}"
    result = runner.invoke(app, ["show", "wids", *args])
    capture_logs(result, f"{env.current_test}{idx}", expect_failure=True)
    assert result.exit_code == 1
    assert pass_condition(result.stdout)
