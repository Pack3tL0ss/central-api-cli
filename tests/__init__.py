"""cencli test setup

This file will ensure only the account specified via customer_id key in
test_devices.json is the only account tests are ran against.

Otherwise if the last command you've run was for an alternate account, and
forget_account_after is set, you could inadvertantly run tests against an
account you didn't intend to.

This would be fairly harmless, we do add a bunch of sites/groups/etc. but
we don't harm any existing devices/groups.  Any commands ran against devices
(we do bounce PoE), references devices in test_devices.json.

NOTE: Doing the imports here has the originally unintended consequence of using
the same cache object for all runs.  This means cache.updated will carry over
from one command to another, which is not the behavior under normal circumstances.

Turns out this is a good thing though.  Most cache.update_*_db methods first
check to see if the API call had already been done before running, with the
intent being to use the cache rather than make another request if it has been
ran.  Turns out this logic doesn't work for a number of functions.

i.e. update_client_db wasn't even returning a value if get_clients had already
been ran.  update_dev_db returns the cache response, but if the previous call
was at verbosity 0 and the subsequent call was verbosity > 0, the cache results
don't include the verbose details.

All this is to say we can use this to test and update that logic.  Currently
most tests impacted import config and set config.updated = [] before the run
to flush the previous results forcing a new API call, as under typically CLI
use this isn't going to be an issue.

Bottom Line.
  1. import config and set config.updated = [] inside any test method
     impacted by previous runs, and update_*_db resulting in unexpected failures.
  2. Leave config.updated unchanged to test caching behavior, which currently
     normal CLI operations don't really exercise.


"""
import sys
import time
import traceback
from functools import partial
from unittest import mock

import pytest
from click.testing import Result
from rich.console import Console
from rich.traceback import install

from centralcli import cache, config, log
from centralcli.cache import CacheDevice
from centralcli.clicommon import APIClients
from centralcli.exceptions import CentralCliException

from ._mock_request import mock_request
from ._test_data import test_data as test_data

install(show_locals=True)  # rich.traceback hook
api_clients = APIClients()

class NonDefaultWorkspaceException(CentralCliException): ...


def capture_logs(result: Result, test_func: str = None, log_output: bool = False, expect_failure: bool = False):
    test_func = test_func or "UNDEFINED"
    if result.exit_code != (0 if not expect_failure else 1) or log_output:
        log.error(f"{test_func} {'returned error' if not log_output else 'output'}:\n{result.stdout}", show=True)
        if "unable to gather device" in result.stdout:
            cache_devices = "\n".join([CacheDevice(d) for d in cache.devices])
            log.error(f"{repr(cache)} devices\n{cache_devices}")
    if result.exception and not isinstance(result.exception, SystemExit):
        log.exception(f"{test_func} {repr(result.exception)}", exc_info=True)
        with log.log_file.open("a") as log_file:
            traceback.print_exception(result.exception, file=log_file)


def ensure_default_account():
    if "--collect-only" in sys.argv:
        return  # pragma: no cover

    if config.workspace != config.default_workspace:  # pragma: no cover
        raise NonDefaultWorkspaceException(f"Test Run started with non default account {config.workspace}.  Aborting as a safety measure.  Use `cencli -d` to restore to default workspace, then re-run tests.")


def monkeypatch_terminal_size():
    TestConsole = partial(Console, height=55, width=190)
    def get_terminal_size(*args, **kwargs):
        return (190, 55)
    pytest.MonkeyPatch().setattr("rich.console.Console", TestConsole)
    pytest.MonkeyPatch().setattr("shutil.get_terminal_size", get_terminal_size)


aiosleep_mock = mock.AsyncMock()
aiosleep_mock.return_value = None


def store_tokens(*args, **kwargs) -> bool:
    log.info("mock store_tokens called.")
    return True

def refresh_tokens(_, old_token: dict) -> dict:
    log.info("mock refresh_tokens called.  Simulating token refresh.")
    return old_token

class MockSleep:
    real_sleep: bool = False

    @classmethod
    def real(cls, do_sleep: bool):
        cls.real_sleep = do_sleep  # pragma: no cover

    def __call__(self, sleep_time: int | float, *args, **kwargs) -> None:
        if self.real_sleep:
            start = time.perf_counter()
            while time.perf_counter() - start < sleep_time:
                continue
            log.info(f"slept for {time.perf_counter() - start}, {sleep_time = }, {args = }, {kwargs = }")

    def __enter__(self):
        self.real_sleep = True
        return self

    def __exit__(self, *args):
        self.real_sleep = False


mock_sleep = MockSleep()


if __name__ in ["tests", "__main__"]:
    monkeypatch_terminal_size()
    if config.dev.mock_tests:
        pytest.MonkeyPatch().setattr("aiohttp.client.ClientSession.request", mock_request)
        pytest.MonkeyPatch().setattr("pycentral.base.ArubaCentralBase.storeToken", store_tokens)
        pytest.MonkeyPatch().setattr("pycentral.base.ArubaCentralBase.refreshToken", refresh_tokens)
        # pytest.MonkeyPatch().setattr("time.sleep", lambda *args, **kwargs: None)  # We don't need to inject any delays when using mocked responses
        pytest.MonkeyPatch().setattr("time.sleep", mock_sleep)  # We don't need to inject any delays when using mocked responses
        pytest.MonkeyPatch().setattr("asyncio.sleep", aiosleep_mock)
    ensure_default_account()
    if "--collect-only" not in sys.argv:
        log.info(f"{' Test Run START ':{'-'}^{150}}")
