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
from typing import Any, Dict, Optional, Type, Union
from unittest.mock import Mock

import pytest
from aiohttp import RequestInfo, StreamReader
from aiohttp.client import ClientResponse, ClientSession, hdrs
from aiohttp.client_proto import ResponseHandler
from aiohttp.helpers import TimerNoop
from aioresponses import aioresponses
from multidict import CIMultiDict, CIMultiDictProxy
from rich.console import Console
from yarl import URL

from centralcli.cli import config, log
from centralcli.clicommon import APIClients

api_clients = APIClients()
responses = {} if not config.closed_capture_file.exists() else json.loads(config.closed_capture_file.read_text())


class InvalidAccountError(Exception): ...
class BatchImportFileError(Exception): ...
class ConfigNotFoundError(Exception): ...


# MOCKED aiohttp.client.ClientResponse object
# vendored/customized from aioresponses
def _build_raw_headers(headers: Dict) -> tuple:
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
        request_headers: Optional[Dict] = None,
        status: int = 200,
        body: Union[str, bytes] = '',
        content_type: str = 'application/json',
        payload: Optional[Dict] = None,
        headers: Optional[Dict] = None,
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
    kwargs = {}  # type: Dict[str, Any]
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
    test_file = Path(__file__).parent / 'test_devices.json'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")
    return json.loads(test_file.read_text())

def setup_batch_import_file(test_data: dict, import_type: str = "sites") -> Path:
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

def monkeypatch_rich_console():
    test_console = partial(Console, height=55, width=190)
    pytest.MonkeyPatch().setattr("rich.console.Console", test_console)


def get_test_response(method: str, url_path: str):
    key = f"{method.upper()}_{url_path}"
    resp_candidates = [r[key] for r in responses if key in r]
    for resp in resp_candidates:
        return resp

@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m

@pytest.mark.asyncio
async def mock_request(session: ClientSession, method: str, url: str, params: dict[str, Any], **kwargs):
    return _build_response(**get_test_response(method, url))


if __name__ in ["tests", "__main__"]:
    test_log_file: Path = log.log_file.parent / "pytest.log"
    # update_log(f"\n__init__: cache: {id(common.cache)}")
    monkeypatch_rich_console()
    if config.dev.mock_tests:
        pytest.MonkeyPatch().setattr("aiohttp.client.ClientSession.request", mock_request)
    test_data: Dict[str, Any] = get_test_data()
    ensure_default_account(test_data=test_data)
    test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
    test_site_file: Path = setup_batch_import_file(test_data=test_data)
    gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"
    test_batch_device_file: Path = test_data["batch"]["devices"]