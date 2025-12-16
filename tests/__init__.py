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
from traceback import print_exception
from functools import partial
from pathlib import Path
from unittest import mock

import pytest
import pendulum
from click.testing import Result
from rich.console import Console
from rich.markup import escape

from centralcli import cache, config, log
from centralcli.cache import CacheDevice
from centralcli.clicommon import APIClients
from centralcli.exceptions import CentralCliException
from aiohttp.client_exceptions import ClientConnectorError, ClientOSError, ContentTypeError
from aiohttp.http_exceptions import ContentLengthError

from ._mock_request import mock_request
from ._test_data import test_data as test_data

expected_exceptions = [SystemExit, ClientConnectorError, ClientOSError, ContentTypeError, ContentLengthError]
api_clients = APIClients()
econsole = Console(stderr=True)
in_45_mins = pendulum.now() + pendulum.duration(minutes=45)
_2_days_ago = pendulum.now() - pendulum.duration(days=2)
_180_days_ago = pendulum.now() - pendulum.duration(days=180)
at_str = in_45_mins.to_datetime_string().replace(" ", "T")[0:-3]
end_2_days_ago = _2_days_ago.to_datetime_string().replace(" ", "T")[0:-3]
now_str = pendulum.now().to_datetime_string().replace(" ", "T")[0:-3]
start_180_days_ago = _180_days_ago.to_datetime_string().replace(" ", "T")[0:-3]

class NonDefaultWorkspaceException(CentralCliException): ...  # pragma: no cover


def capture_logs(result: Result, test_func: str = None, log_output: bool = False, expect_failure: bool = False):
    test_func = test_func or "UNDEFINED"
    _msg = 'returned error' if not expect_failure else 'Passed when failure was expected'
    if result.exit_code != (0 if not expect_failure else 1) or log_output:  # pragma: no cover
        log.error(f"{test_func} {_msg if not log_output else 'output'}:\n{escape(f'{result.stdout = }')}", show=True)
        if "unable to gather device" in result.stdout:  # pragma: no cover
            cache_devices = "\n".join([CacheDevice(d) for d in cache.devices])
            log.error(f"{repr(cache)} devices\n{cache_devices}")
    if result.exception and not any([isinstance(result.exception, exc) for exc in expected_exceptions]):  # pragma: no cover
        with log.log_file.open("a") as log_file:
            print_exception(result.exception, file=log_file)


def ensure_default_account():  # pragma: no cover
    if "--collect-only" in sys.argv:
        return

    if config.workspace != config.default_workspace:
        raise NonDefaultWorkspaceException(f"Test Run started with non default account {config.workspace}.  Aborting as a safety measure.  Use `cencli -d` to restore to default workspace, then re-run tests.")


def clean_mac(mac: str) -> str:
    return mac.replace(":", "").replace("-", "").replace(".", "").lower()


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

def mock_write_file(outfile: Path, outdata: str) -> None:
    econsole.print(f"[cyan]Writing output to {outfile}... [italic green]Done[/]")

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
        else:  # pragma: no cover
            ...

    def __enter__(self):
        self.real_sleep = True
        return self

    def __exit__(self, *args):
        self.real_sleep = False


mock_sleep = MockSleep()

class MockConsoleDimensions():
    def __init__(self, *args, **kwargs):
        self.width: int = 190
        self.height: int = 55

    def __repr__(self):  # pragma: no cover
        return f"{self.__class__.__name__}(width={self.width}, height={self.height})"




if __name__ in ["tests", "__main__"]:  # pragma: no cover
    monkeypatch_terminal_size()
    if config.dev.mock_tests:
        pytest.MonkeyPatch().setattr("aiohttp.client.ClientSession.request", mock_request)
        pytest.MonkeyPatch().setattr("pycentral.base.ArubaCentralBase.storeToken", store_tokens)
        pytest.MonkeyPatch().setattr("pycentral.base.ArubaCentralBase.refreshToken", refresh_tokens)
        pytest.MonkeyPatch().setattr("time.sleep", mock_sleep)  # We don't need to inject any delays when using mocked responses
        pytest.MonkeyPatch().setattr("asyncio.sleep", aiosleep_mock)
        pytest.MonkeyPatch().setattr("centralcli.render.write_file", mock_write_file)
        pytest.MonkeyPatch().setattr("rich.console.ConsoleDimensions", MockConsoleDimensions)
    else:  # pragma: no cover
        ...
    ensure_default_account()
    if "--collect-only" not in sys.argv:
        log.info(f"{' Test Run START ':{'-'}^{140}}")
    else:  # pragma: no cover
        ...
