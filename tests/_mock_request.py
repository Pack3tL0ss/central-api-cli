import asyncio
from typing import Any, Optional, Type, Union
from unittest.mock import Mock
from urllib.parse import unquote_plus

import jsonref as json
import pytest
from aiohttp import RequestInfo, StreamReader
from aiohttp.client import ClientResponse, ClientSession, hdrs
from aiohttp.client_proto import ResponseHandler
from aiohttp.helpers import TimerNoop
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

from centralcli import config, log, utils
from centralcli.environment import env

responses: list[dict[str, dict[str, Any]]] = {} if not config.closed_capture_file.exists() else json.loads(config.closed_capture_file.read_text())

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
    if isinstance(payload, str):
        body = payload.encode()
    elif payload is not None:
        body = json.dumps(payload)
    if not isinstance(body, bytes):
        body = str.encode(body)
    if request_headers is None:
        request_headers = {}
    loop = Mock()
    loop.get_debug = Mock()
    loop.get_debug.return_value = True
    kwargs: dict[str, Any] = {}
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
        resp.cookies.load(hdr)  # pragma: no cover

    # Reified attributes
    resp._headers = _headers
    resp._raw_headers = raw_headers

    resp.status = status
    resp.reason = reason
    resp.content = stream_reader_factory(loop)
    resp.content.feed_data(body)
    resp.content.feed_eof()
    # if str(resp.url) == "/cloudauth/api/v3/bulk/mac":
    return resp

class TestResponses:
    used_responses: list[int] = []

    @staticmethod
    def _get_candidates(key: str) -> dict[str, Any]:  # LEFT-OFF-HERE  Add support for regex match of url key str within test block  i.e. "GET_/configuration/v1/ap_settings_cli/.*"
        if env.current_test in responses:
            if key in responses[env.current_test]:
                return responses[env.current_test][key]

        ok_responses = responses["ok_responses"]
        parts = key.split("_")
        method = parts[0]
        url = "_".join(parts[1:])
        key = url.replace("/", "_").lstrip("_")
        # strip audit_trail id from url, so any id will match.  this is for showing audit details for a specific log id.
        if "_audit_trail_" in key:
            key = f'{key.split("_audit_trail_")[0]}_audit_trail_'
            return [ok_responses[method][[k for k in ok_responses[method].keys() if key in k][0]]]

        res = ok_responses[method].get(key, responses["failed_responses"][method].get(key))
        return [] if not res else [res]

    @property
    def unused(self) -> list[str]:  # pragma: no cover
        return []
        # return [
        #     f"{idx}:{k}" for idx, r in enumerate(responses, start=1) for k, v in r.items() if hash(str(v)) not in self.used_responses
        # ]  # start=1 to account for '[' at the top of the raw_capture file.  So idx is line # in raw_capture file.

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

        if resp_candidates:  # pragma: no cover
            log.info(f"Reusing previously used response for {url.path}")
            return resp_candidates[-1]

        log.error(f"{env.current_test} - No Mock Response found for {key}.  Returning failed response.")  # pragma: no cover
        return {"url": url, "status": 418, "reason": f"No Mock Response Found for {key}"}  # pragma: no cover

test_responses = TestResponses()

@pytest.mark.asyncio
async def mock_request(session: ClientSession, method: str, url: str, params: dict[str, Any] = None, **kwargs):
    return _build_response(**test_responses.get_test_response(method, url, params=params))
