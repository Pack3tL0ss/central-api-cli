import asyncio
import datetime
from typing import Any, Optional, Type, Union
from unittest.mock import Mock
from urllib.parse import unquote_plus
from zoneinfo import ZoneInfo

import jsonref as json
import pytest
from aiohttp import RequestInfo, StreamReader
from aiohttp.client import ClientResponse, ClientSession, hdrs
from aiohttp.client_proto import ResponseHandler
from aiohttp.helpers import TimerNoop
from jinja2 import Environment, FileSystemLoader
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL
from aiohttp.client_exceptions import ClientConnectorError, ClientOSError, ContentTypeError
from aiohttp.client_reqrep import ConnectionKey
from aiohttp.http_exceptions import ContentLengthError
from pathlib import Path

from centralcli import config, log, utils
from centralcli.environment import env


str_to_exc = {
    "ClientConnectorError": ClientConnectorError,
    "ClientOSError": ClientOSError,
    "ContentTypeError": ContentTypeError,
    "ContentLengthError": ContentLengthError
}

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

    def __init__(self):
        self.responses = self._get_responses_from_capture_file()

    @staticmethod
    def _get_responses_from_capture_file() -> list[dict[str, dict[str, Any]]]:
        if not config.closed_capture_file.exists():
            return {}  # pragma: no cover
        else:
            now = datetime.datetime.now(tz=ZoneInfo("UTC"))
            in_five_months = now + datetime.timedelta(days=5 * 30)  # approx
            in_two_months = now + datetime.timedelta(days=2 * 30)  # approx
            # Set up Jinja2 environment
            j2env = Environment(loader=FileSystemLoader(config.closed_capture_file.parent)) # Assuming template is in the same directory
            template = j2env.get_template(config.closed_capture_file.name)

            # Render the template with the dates
            return json.loads(template.render(in_five_months=in_five_months, in_two_months=in_two_months))

    def _get_candidates(self, key: str) -> dict[str, Any]:  # LEFT-OFF-HERE  Add support for regex match of url key str within test block  i.e. "GET_/configuration/v1/ap_settings_cli/.*"
        parts = key.split("_")
        method = parts[0]
        url = "_".join(parts[1:])
        path = url.split("?")[0]

        if env.current_test in self.responses:
            if key in self.responses[env.current_test]:
                if isinstance(self.responses[env.current_test][key], str):
                    if self.responses[env.current_test][key] == "ClientConnectorError":
                        con_key = ConnectionKey(host=Path(config.base_url).name, port=443, proxy=None, proxy_auth=None, is_ssl=True, ssl=True, proxy_headers_hash=None)
                        raise ClientConnectorError(connection_key=con_key, os_error=OSError())
                    elif self.responses[env.current_test][key] == "ContentLengthError":
                        raise ContentLengthError("mock content length error")
                    else:  # pragma: no cover
                        raise str_to_exc[self.responses[env.current_test][key]]

                candidates = utils.listify(self.responses[env.current_test][key])
                return (True, [{**c, "url": path, "method": method} for c in candidates])

        key = url.replace("/", "_").lstrip("_")
        ok_responses = self.responses["ok_responses"]
        # strip audit_trail id from url, so any id will match.  this is for showing audit details for a specific log id.
        if "_audit_trail_" in key:
            key = f'{key.split("_audit_trail_")[0]}_audit_trail_'
            return (False, [ok_responses[method][[k for k in ok_responses[method].keys() if key in k][0]]])

        res = ok_responses[method].get(key, self.responses["failed_responses"].get(method, {}).get(key))
        return (False, []) if not res else (False, [{**res, "url": path, "method": method}])

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

        has_per_test_res, resp_candidates = self._get_candidates(key)

        for resp in resp_candidates:
            res_hash = hash(str(resp))
            if res_hash not in self.used_responses:
                self.used_responses += [res_hash]
                log.info(f"{env.current_test} - returning {resp['status']} MOCK response{'.' if not has_per_test_res else ' (per test deffinition).'}")
                return resp

        if resp_candidates:  # pragma: no cover
            log.info(f"{env.current_test} - Reusing previously used {resp['status']} response for {url.path}")
            return resp_candidates[-1]

        log.error(f"{env.current_test} - No Mock Response found for {key}.  Returning failed (418) response.")  # pragma: no cover
        return {
            "url": url,
            "method": method,
            "status": 418,
            "reason": f"No Mock Response Found for {key}",
            "payload": {"description": f"No Mock Response Found for {key}"}
        }  # pragma: no cover

test_responses = TestResponses()

@pytest.mark.asyncio
async def mock_request(session: ClientSession, method: str, url: str, params: dict[str, Any] = None, **kwargs):
    return _build_response(**test_responses.get_test_response(method, url, params=params))
