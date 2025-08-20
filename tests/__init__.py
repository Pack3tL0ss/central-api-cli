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
import asyncio
import json
from functools import partial
from pathlib import Path
from typing import Any, Optional, Type, Union
from unittest.mock import Mock
from urllib.parse import unquote_plus

import pytest
from aiohttp import RequestInfo, StreamReader
from aiohttp.client import ClientResponse, ClientSession, hdrs
from aiohttp.client_proto import ResponseHandler
from aiohttp.helpers import TimerNoop
from multidict import CIMultiDict, CIMultiDictProxy
from rich.console import Console
from yarl import URL

from centralcli import config, log, utils
from centralcli.clicommon import APIClients

api_clients = APIClients()
responses: list[dict[str, dict[str, Any]]] = {} if not config.closed_capture_file.exists() else json.loads(config.closed_capture_file.read_text())


class InvalidAccountError(Exception): ...
class BatchImportFileError(Exception): ...
class ConfigNotFoundError(Exception): ...


# MOCKED aiohttp.client.ClientResponse object
# vendored/customized from aioresponses
def _build_raw_headers(headers: dict[str, str]) -> tuple[tuple[bytes, bytes]]:
    """
    Convert a dict of headers to a tuple of tuples

    Mimics the format of ClientResponse.
    """
    raw_headers = []
    for k, v in headers.items():
        raw_headers.append((k.encode('utf8'), v.encode('utf8')))
    return tuple(raw_headers)

def stream_reader_factory(  # noqa
    loop: 'Optional[asyncio.AbstractEventLoop]' = None
) -> StreamReader:
    protocol = ResponseHandler(loop=loop)
    return StreamReader(protocol, limit=2 ** 16, loop=loop)

def _build_response(
        url: 'Union[URL, str]',
        method: str = hdrs.METH_GET,
        request_headers: Optional[dict] = None,
        status: int = 200,
        body: Union[str, bytes] = '',
        content_type: str = 'application/json',
        payload: Optional[dict] = None,
        headers: Optional[dict] = None,
        response_class: Optional[Type[ClientResponse]] = None,
        reason: Optional[str] = "OK"
    ) -> ClientResponse:
    if response_class is None:
        response_class = ClientResponse
    if payload is not None:
        body = json.dumps(payload)
    if not isinstance(body, bytes):
        body = str.encode(body)
    if request_headers is None:
        request_headers = {}
    loop = Mock()
    loop.get_debug = Mock()
    loop.get_debug.return_value = True
    kwargs = {}  # type: dict[str, Any]
    url = URL(url)
    kwargs['request_info'] = RequestInfo(
        url=url,
        method=method,
        headers=CIMultiDictProxy(CIMultiDict(**request_headers)),
        real_url=url
    )
    kwargs['writer'] = None
    kwargs['continue100'] = None
    kwargs['timer'] = TimerNoop()
    kwargs['traces'] = []
    kwargs['loop'] = loop
    kwargs['session'] = None

    # We need to initialize headers manually
    _headers = CIMultiDict({hdrs.CONTENT_TYPE: content_type})
    if headers:
        _headers.update(headers)
    raw_headers = _build_raw_headers(_headers)
    resp = response_class(method, url, **kwargs)

    for hdr in _headers.getall(hdrs.SET_COOKIE, ()):
        resp.cookies.load(hdr)

    # Reified attributes
    resp._headers = _headers
    resp._raw_headers = raw_headers

    resp.status = status
    resp.reason = reason
    resp.content = stream_reader_factory(loop)
    resp.content.feed_data(body)
    resp.content.feed_eof()
    return resp


def update_log(txt: str):
    with test_log_file.open("a") as f:
        f.write(f'{txt.rstrip()}\n')


def get_test_data():
    test_file = Path(__file__).parent / 'test_data.yaml'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")
    return config.get_file_data(test_file)


def setup_batch_import_file(test_data: dict | str | Path, import_type: str = "sites") -> Path:
    if isinstance(test_data, (str, Path)):
        return test_data if isinstance(test_data, Path) else Path(test_data)

    test_batch_file = config.cache_dir / f"test_runner_{import_type}.json"
    res = test_batch_file.write_text(
        json.dumps(test_data["batch"][import_type])
    )
    if not res:
        raise BatchImportFileError("Batch import file creation from test_data returned 0 chars written")
    return test_batch_file


def ensure_default_account(test_data: dict):
    api = api_clients.classic
    if api.session.auth.central_info["customer_id"] != str(test_data["customer_id"]):
        msg = f'customer_id {api.session.auth.central_info["customer_id"]} script initialized with does not match customer_id in test_data.\nRun a command with -d to revert to default account'
        raise InvalidAccountError(msg)


def monkeypatch_terminal_size():
    TestConsole = partial(Console, height=55, width=190)
    def get_terminal_size(*args, **kwargs):
        return (190, 55,)
    pytest.MonkeyPatch().setattr("rich.console.Console", TestConsole)
    pytest.MonkeyPatch().setattr("shutil.get_terminal_size", get_terminal_size)

class TestResponses:
    used_responses: list[int] = []

    @staticmethod
    def _get_candidates(key: str) -> dict[str, Any]:
        if "/audit_trail_" in key:
            key = f'{key.split("/audit_trail_")[0]}/audit_trail_'
            return [v for r in responses for k, v in r.items() if key in k]

        return [r[key] for r in responses if key in r]

    @property
    def unused(self) -> list[str]:  # pragma: no cover
        return [
            f"{idx}:{k}" for idx, r in enumerate(responses) for k, v in r.items() if hash(str(v)) not in self.used_responses
        ]

    def get_test_response(self, method: str, url: str, params: dict[str, Any] = None):  # url here is just the path portion
        url: URL = URL(unquote_plus(url))  # url with mac would be 24%3A62%3Aab... without unquote_plus
        if params:
            params = utils.remove_time_params(params)
            url = url.with_query(params)
        key = f"{method.upper()}_{url.path_qs}"

        resp_candidates = self._get_candidates(key)

        for resp in resp_candidates:
            res_hash = hash(str(resp))
            if res_hash not in self.used_responses:
                self.used_responses += [res_hash]
                return resp

        # If they hit this it's repeated test, but we are out of unique responses, so repeat the last response (useful for testing different output formats)
        log.warning(f"No Mock Response found for {key}")
        return {"url": url} if not resp_candidates else  resp_candidates[-1]

test_responses = TestResponses()


@pytest.mark.asyncio
async def mock_request(session: ClientSession, method: str, url: str, params: dict[str, Any] = None, **kwargs):
    return _build_response(**test_responses.get_test_response(method, url, params=params))


if __name__ in ["tests", "__main__"]:
    test_log_file: Path = log.log_file.parent / "pytest.log"
    # update_log(f"\n__init__: cache: {id(common.cache)}")
    monkeypatch_terminal_size()
    if config.dev.mock_tests:
        pytest.MonkeyPatch().setattr("aiohttp.client.ClientSession.request", mock_request)
    test_data: dict[str, Any] = get_test_data()
    ensure_default_account(test_data=test_data)
    test_batch_device_file: Path = setup_batch_import_file(test_data=test_data, import_type="devices")
    test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
    test_site_file: Path = setup_batch_import_file(test_data=test_data)
    gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"
    # test_batch_device_file: Path = test_data["batch"]["devices"]