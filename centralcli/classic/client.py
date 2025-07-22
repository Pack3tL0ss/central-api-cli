from __future__ import annotations

from ..response import Response
from pycentral.base import ArubaCentralBase
from ..typedefs import StrOrURL, Method
from aiohttp.client import ClientSession, ClientResponse
from aiohttp.client_exceptions import ClientConnectorError, ClientOSError, ContentTypeError
from aiohttp.http_exceptions import ContentLengthError
from pycentral.base_utils import tokenLocalStoreUtil
from functools import wraps, cached_property
from .. import config, log, utils, cleaner
from .utils import Spinner
from ..constants import STRIP_KEYS, lib_to_api
from typing import List, Dict, Any, Tuple, TYPE_CHECKING
import asyncio
import time
import json
import sys
from yarl import URL
from rich.markup import escape
from pathlib import Path

if TYPE_CHECKING:
    ...


DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
DEFAULT_SPIN_TXT = "\U0001f4a9 DEFAULT_SPIN_TXT \U0001f4a9"  # should never see this, makes it more obvious we missed a spinner update
MAX_CALLS_PER_CHUNK = 6
INIT_TS = time.monotonic()

class LoggedRequests:
    def __init__(self, url: str, method: str = "GET",):
        self.ts = float(f"{time.monotonic() - INIT_TS:.2f}")
        self.url = url
        self.method = method
        self.reason = None
        self.ok = None
        self.status = None
        self.remain_day = None
        self.remain_sec = None

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.reason}) object at {hex(id(self))}>"

    def update(self, response: ClientResponse):
        rh = response.headers
        self.reason = response.reason
        self.ok = response.ok
        self.status = response.status
        self.remain_day = int(f"{rh.get('X-RateLimit-Remaining-day', 0)}")
        self.remain_sec = int(f"{rh.get('X-RateLimit-Remaining-second', 0)}")

        return self


class BatchRequest:
    def __init__(self, func: callable, *args, **kwargs) -> None:
        """Constructor object for for api requests.

        Used to pass multiple requests into CentralApi batch_request method for parallel
        execution.

        Args:
            func (callable): The CentralApi method to execute.
            args (Iterable, optional): args passed on to method. Defaults to ().
            kwargs (dict, optional): kwargs passed on to method. Defaults to {}.
        """
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.func.__name__}) object at {hex(id(self))}>"


class Session():
    def __init__(
        self,
        base_url: StrOrURL = None,
        aio_session: ClientSession = None,
        silent: bool = True,
    ) -> None:
        self.silent = silent  # squelches out automatic display of failed Responses.
        self.base_url = f"{base_url.rstrip('/')}/"
        self._aio_session = aio_session
        self.ssl = config.ssl_verify
        self.req_cnt = 1
        self.requests: List[LoggedRequests] = []
        self.throttle: int = 0
        self.spinner = Spinner("Collecting Data...")
        self.updated_at = time.monotonic()
        self.rl_log = [f"{self.updated_at - INIT_TS:.2f} [INIT] {type(self).__name__} object at {hex(id(self))}"]
        self.BatchRequest = BatchRequest
        self.running_spinners: List[str] = []

    @cached_property
    def auth(self):
        return self.get_conn_from_file()

    @staticmethod
    def get_conn_from_file() -> ArubaCentralBase:
        """Creates an instance of class`pycentral.ArubaCentralBase` based on config file.

        Returns:
            [pycentral.ArubaCentralBase]: An instance of class:`pycentral.ArubaCentralBase`,
                Used to manage Auth and Tokens.
        """
        conn = ArubaCentralBase(config.central_info, token_store=config.token_store, logger=log, ssl_verify=config.ssl_verify)
        token_cache = Path(tokenLocalStoreUtil(config.token_store, config.central_info["customer_id"], config.central_info["client_id"]))

        # always create token cache if it doesn't exist and always use it first
        # unless config has been modified more recently, if so,  any tokens in the config will be tried first.
        # if both fail user will be prompted for token if no user/pass or on Internal Cluster w/ @hpe.com user.
        if token_cache.is_file():
            cache_token = conn.loadToken()
            if cache_token:
                if token_cache.stat().st_mtime > config.file.stat().st_mtime:
                    conn.central_info["retry_token"] = conn.central_info["token"]
                    conn.central_info["token"] = cache_token
                else:
                    conn.central_info["retry_token"] = cache_token

                # Compare tokens and remove retry token if they are the same.  Rare scenario
                if conn.central_info["retry_token"]["refresh_token"] == conn.central_info["token"]["refresh_token"]:
                    del conn.central_info["retry_token"]
        else:
            if not conn.storeToken(conn.central_info.get("token")):
                log.warning("Failed to Store Token and token cache doesn't exist yet.", show=True)

        return conn

    @property
    def aio_session(self):
        if self._aio_session is None or self._aio_session.closed:
            self._aio_session = ClientSession(base_url=self.base_url)

        return self._aio_session


    @aio_session.setter
    def aio_session(self, session: ClientSession):
        self._aio_session = session

    async def close(self) -> None:
        if self._aio_session is not None and not self._aio_session.closed:
            await self._aio_session.close()

    @property
    def headers(self) -> Dict[str, str]:
        headers = DEFAULT_HEADERS
        if self.auth is not None:
            headers["authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"

        return headers


    def _get_spin_text(self, spin_txt: str = None):
        if spin_txt:
            if "retry" in spin_txt:
                return spin_txt

            self.running_spinners = [*self.running_spinners, spin_txt]
        elif not self.running_spinners:
            return "missing spin text"

        try:
            if len(self.running_spinners) > 1 and len(set([x.split("...")[0] for x in self.running_spinners])) == 1:
                return f'{self.running_spinners[0].split("...")[0]}... Request:{",".join(x.split(":")[1] for x in self.running_spinners)}'.replace("...,", "...")

            return spin_txt if not self.running_spinners else self.running_spinners[0]
        except Exception as e:
            log.warning(f"DEV NOTE: {e.__class__.__name__} exception in combined spinner update")

            return spin_txt if not self.running_spinners else self.running_spinners[0]

    async def vlog_api_req(self, method: Method, url: StrOrURL, params: Dict[str, Any] = None, data: Any = None, json_data: Dict[str, Any] = None, kwargs: Dict[str, Any] = None) -> None:
        if not config.debugv:
            return
        call_data = {
            "method": method,
            "url": url,
            "url_params": params,
            "data": data,
            "json_data": json_data,
        }
        if kwargs:
            call_data["Additional kwargs"] = kwargs
        print("[bold magenta]VERBOSE DEBUG[reset]")
        call_data = utils.strip_none(call_data, strip_empty_obj=True)
        utils.json_print(call_data)

    async def exec_api_call(self, url: str, data: dict = None, json_data: dict | list = None,
                            method: str = "GET", headers: dict = {}, params: dict = {}, **kwargs) -> Response:
        auth = self.auth
        resp = None
        _url = URL(url).with_query(params)
        _data_msg = ' ' if not url else f' {escape(f"[{_url.path}]")}'  #  Need to cancel [ or rich will eval it as a closing markup
        end_name = _url.name if _url.name not in ["aps", "gateways", "switches"] else lib_to_api(_url.name)
        if config.sanitize and utils.is_serial(end_name):
            end_name = "USABCD1234"
        if _url.query.get("offset") and _url.query["offset"] != "0":
            _data_msg = f'{_data_msg.rstrip("]")}?offset={_url.query.get("offset")}&limit={_url.query.get("limit")}...]'
        run_sfx = '' if self.req_cnt == 1 else f' Request: {self.req_cnt}'
        spin_word = "Collecting" if method == "GET" else "Sending"
        spin_txt_run = f"{spin_word} ({end_name}) Data...{run_sfx}"
        spin_txt_retry = DEFAULT_SPIN_TXT  # helps detect if this was not set correctly after previous failure :poop:
        spin_txt_fail = f"{spin_word} ({end_name}) Data{_data_msg}"
        self.spinner.update(DEFAULT_SPIN_TXT)
        for _ in range(0, 2):
            spin_txt_run = spin_txt_run if _ == 0 else f"{spin_txt_run} {spin_txt_retry}".rstrip()

            token_msg = ""
            if auth is not None:
                token_msg = (
                    f"\n    access token: {auth.central_info.get('token', {}).get('access_token', {})}"
                    f"\n    refresh token: {auth.central_info.get('token', {}).get('refresh_token', {})}"
                )
            # TODO This DEBUG messasge won't hit for COP, need conditional to compare url to config.base_url
            # token_msg is only a conditional for show version (non central API call).
            # could update attribute in clicommonm cli.call_to_central
            log.debug(
                f'Attempt API Call to:{_data_msg}Try: {_ + 1}{token_msg if self.req_cnt == 1 and "arubanetworks.com" in url else ""}'
            )
            if config.debugv:
                asyncio.create_task(self.vlog_api_req(method=method, url=url, params=params, data=data, json_data=json_data, kwargs=kwargs))

            headers = self.headers if not headers else {**self.headers, **headers}
            try:
                req_log = LoggedRequests(_url.path_qs, method)

                _start = time.perf_counter()
                now = time.perf_counter() - INIT_TS

                _try_cnt = [u.url for u in self.requests].count(_url.path_qs) + 1
                self.rl_log += [
                    f'{now:.2f} [{method}]{_url.path_qs} Try: {_try_cnt}'
                ]

                self.spinner.start(self._get_spin_text(spin_txt_run), spinner="dots")
                self.req_cnt += 1  # TODO may have deprecated now that logging requests

                # async with self.aio_session as client:
                async with ClientSession(base_url=self.base_url) as client:
                    resp = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        json=json_data,
                        headers=headers,
                        ssl=self.ssl,
                        **kwargs
                    )
                    elapsed = time.perf_counter() - _start
                    self.requests += [req_log.update(resp)]

                    try:
                        output = await resp.json()
                        try:
                            raw_output = output.copy()
                        except AttributeError:
                            raw_output = output

                        # Strip outer key sent by central
                        output = cleaner.strip_outer_keys(output)
                    except (json.decoder.JSONDecodeError, ContentTypeError):
                        output = raw_output = await resp.text()

                    resp = Response(resp, output=output, raw=raw_output, elapsed=elapsed)

            except (ClientOSError, ClientConnectorError) as e:
                log.exception(f'[{method}:{URL(url).path}]{e}')
                resp = Response(error=str(e.__class__.__name__), output=str(e), url=_url.path_qs)
            except ContentLengthError as e:
                log.exception(f'[{method}:{URL(url).path}]{e}')
                resp = Response(error=str(e.__class__.__name__), output=str(e), url=_url.path_qs)
            except Exception as e:
                log.exception(f'[{method}:{URL(url).path}]{e}')
                resp = Response(error=str(e.__class__.__name__), output=str(e), url=_url.path_qs)
                _ += 1

            fail_msg = spin_txt_fail if self.silent else f"{spin_txt_fail}\n  {resp.output}"
            self.running_spinners = [s for s in self.running_spinners if s != spin_txt_run]
            if not resp:
                self.spinner.fail(fail_msg) if not self.silent else self.spinner.stop()
                if self.running_spinners:
                    self.spinner.start(self._get_spin_text(), spinner="dots")

                # TODO need CNX retry here
                # status code: 401
                # Access Forbidden
                # Unformatted response from Aruba Central API GW
                # {
                #     'httpStatusCode': 401,
                #     'errorCode': 'HPE_GL_ERROR_FORBIDDEN',
                #     'message': 'JWT verification failed, JWT verification failed for claims: Signature has expired',
                #     'debugId': 'hHtoh-ahwJ6IwMT6Qp3OyhDNBWUB8LpFnWeNH30NkWse-SzdjJ-swA=='
                # }
                if "invalid_token" in resp.output:
                    spin_txt_retry =  "(retry after token refresh)"
                    self.refresh_token()
                elif "errorCode" in resp.raw and "HPE_GL_ERROR" in resp.raw["errorCode"] and "signature has expired" in resp.raw.get("message", "").lower():
                    spin_txt_retry =  "(retry after token refresh)"
                    if hasattr(self.auth, "handle_expired_token"):
                        self.auth.handle_expired_token()
                elif resp.status == 500:
                    spin_txt_retry = ":shit:  [bright_red blink]retry[/] after 500: [cyan]Internal Server Error[/]"
                    log.warning(f'{resp.url.path_qs} forced to retry after 500 (Internal Server Error) from Central API gateway')
                    # returns JSON: {'message': 'An unexpected error occurred'}
                elif resp.status == 503:
                    spin_txt_retry = ":shit:  [bright_red blink]retry[/]  after 503: [cyan]Service Unavailable[/]"
                    log.warning(f'{resp.url.path_qs} forced to retry after 503 (Service Unavailable) from Central API gateway')
                    # returns a string: "upstream connect error or disconnect/reset before headers. reset reason: connection termination"
                elif resp.status == 504:
                    spin_txt_retry = ":shit:  [bright_red blink]retry[/]  after 504: [cyan]Gatewat Time-out[/]"
                    log.warning(f'{resp.url.path_qs} forced to retry after 504 (Gateway Timeout) from Central API gateway')
                elif resp.status == 429:  # per second rate limit.
                    # _msg = fail_msg.replace(f'{spin_word} Data', '').replace(' \[', ' [')
                    # log.warning(f"Per second rate limit hit {_msg}")
                    spin_txt_retry = ":shit:  [bright_red blink]retry[/]  after hitting per second rate limit"
                    self.rl_log += [f"{now:.2f} [:warning: [bright_red]RATE LIMIT HIT[/]] p/s: {resp.rl.remain_sec}: {_url.path_qs}"]
                    _ -= 1
                elif resp.status == 418:  # Spot to handle retries for any caught exceptions
                    if resp.error == "ContentLengthError":
                        spin_txt_retry = ":shit:  [bright_red blink]retry[/]  after [cyan]ContentLengthError[/]"
                        log.warning(f'{resp.url.path_qs} forced to retry after ContentLengthError')
                    else:
                        log.error(f'{resp.url.path_qs} {resp.error} Exception is not configured for retry')
                        break
                else:
                    break
            else:
                if resp.rl.near_sec:
                    self.rl_log += [
                        f"{time.perf_counter() - INIT_TS:.2f} [[bright_green]{resp.error}[/] but [dark_orange3]NEARING RATE LIMIT[/]] p/s: {resp.rl.remain_sec} {_url.path_qs}"
                    ]
                else:
                    self.rl_log += [
                        f"{time.perf_counter() - INIT_TS:.2f} [[bright_green]{resp.error}[/]] p/s: {resp.rl.remain_sec} {_url.path_qs}"
                    ]

                # This handles long running API calls where subsequent calls finish before the previous...
                if self.running_spinners:
                    self.spinner.update(self._get_spin_text(), spinner="dots2")
                else:
                    self.spinner.stop()
                break

        return resp

    async def handle_pagination(self, res: Response, paged_raw: Dict | List | None = None, paged_output: Dict | List | None = None,) -> Tuple:
        if not paged_output:
            paged_output = res.output
        else:
            if isinstance(res.output, dict):
                paged_output = {**paged_output, **res.output}
            else:  # FIXME paged_output += r.output was also changing contents of paged_raw dunno why
                try:
                    paged_output = paged_output + res.output  # This does work different than += which would turn a string into a list of chars and append
                except TypeError:
                    log.error(f"Not adding {res.output} to paged output. Call Result {res.error}")

        if not paged_raw:
            paged_raw = res.raw
        else:
            if isinstance(res.raw, dict):
                for outer_key in STRIP_KEYS:
                    if outer_key in res.raw and outer_key in paged_raw:
                        if isinstance(res.raw[outer_key], dict):
                            paged_raw[outer_key] = {**paged_raw[outer_key], **res.raw[outer_key]}
                        else:  # TODO use response magic method to do adds have Response figure this out
                            paged_raw[outer_key] += res.raw[outer_key]
                        if all(["count" in var for var in [paged_raw, res.raw]]):
                            paged_raw["count"] += res.raw["count"]
                        break
            else:
                try:
                    paged_raw += res.raw
                except TypeError:
                    log.error(f"Not adding {res.raw} to paged raw. Call Result {res.error}")

        return paged_raw, paged_output

    async def api_call(self, url: StrOrURL, data: dict = None, json_data: dict | list = None,
                       method: str = "GET", headers: dict = {}, params: dict = {}, callback: callable = None,
                       callback_kwargs: Any = {}, count: int = None, **kwargs: Any) -> Response:
        """Perform API calls and handle paging

        Args:
            url (StrOrURL): The API Endpoint URL
            data (dict, optional): Data passed to aiohttp.ClientSession. Defaults to None.
            json_data (dict | list, optional): passed to aiohttp.ClientSession. Defaults to None.
            method (str, optional): Request Method (POST, GET, PUT,...). Defaults to "GET".
            headers (dict, optional): headers dict passed to aiohttp.ClientSession. Defaults to {}.
            params (dict, optional): url parameters passed to aiohttp.ClientSession. Defaults to {}.
            callback (callable, optional): DEPRECATED callback to be performed on result prior to return. Defaults to None.
            callback_kwargs (Any, optional): DEPRECATED kwargs to pass to the callback. Defaults to {}.
            count (int, optional): upper limit on # of records to return (used to return last 'count' audit logs). Defaults to None.

        Returns:
            Response: CentralAPI Response object
        """

        # TODO cleanup, if we do strip_none here can remove from calling funcs.
        params = utils.strip_none(params)

        # /routing endpoints use "marker" rather than "offset" for pagination
        offset_key = "marker" if "marker" in params or "/api/routing/" in url else "offset"

        # for debugging can set a smaller limit in config or via --debug-limit flag to test paging
        if params and params.get("limit") and config.dev_options.limit:
            log.info(f'paging limit being overridden by config: {params.get("limit")} --> {config.dev_options.limit}')
            params["limit"] = config.dev_options.limit

        # allow passing of default kwargs (None) for param/json_data, all keys with None Value are stripped here.
        # supports 2 levels beyond that needs to be done in calling method.
        json_data = utils.strip_none(json_data)
        if json_data:  # strip second nested dict if all keys = NoneType
            y = json_data.copy()
            for k in y:
                if isinstance(y, dict) and isinstance(y[k], dict):
                    y[k] = utils.strip_none(y[k])
                    if not y[k]:
                        del json_data[k]

        # Output pagination loop
        paged_output = None
        paged_raw = None
        failures = []
        while True:
            # -- // Attempt API Call \\ --
            r = await self.exec_api_call(url, data=data, json_data=json_data, method=method, headers=headers,
                                         params=params, **kwargs)
            if not r.ok:
                failures = [r]
                break

            # TODO OK to remove confirmed not used anywhere
            elif callback is not None:
                # TODO [remove] moving callbacks to display output in cli, leaving methods to return raw output
                log.debug(f"DEV NOTE CALLBACK IN centralapi lib {r.url.path} -> {callback}")
                r.output = callback(r.output, **callback_kwargs or {})

            paged_raw, paged_output = await self.handle_pagination(r, paged_raw=paged_raw, paged_output=paged_output)


            # On 1st call determine if remaining calls can be made in batch
            # total is provided for some calls with the total # of records available
            is_events = True if url.endswith("/monitoring/v2/events") else False
            if params.get(offset_key, 99) == 0 and isinstance(r.raw, dict) and r.raw.get("total") and (len(r.output) + params.get("limit", 0) < r.raw.get("total", 0)):
                _total = count or r.raw["total"] if not is_events or r.raw["total"] <= 10_000 else 10_000  # events endpoint will fail if offset + limit > 10,000
                if _total > len(r.output):
                    _limit = params.get("limit", 100)
                    _offset = params.get(offset_key, 0)
                    br = BatchRequest
                    _reqs = [
                        br(self.exec_api_call, url, data=data, json_data=json_data, method=method, headers=headers, params={**params, offset_key: i, "limit": _limit}, **kwargs)
                        for i in range(len(r.output), _total, _limit)
                    ]

                    batch_res: List[Response] = await self._batch_request(_reqs)
                    failures: List[Response] = [r for r in batch_res if not r.ok]  # A failure means both the original attempt and the retry failed.
                    successful: List[Response] = batch_res if not failures else [r for r in batch_res if r.ok]

                    # Handle failures during batch execution
                    if not successful and failures:
                        log.error(f"Error returned during batch {method} calls to {url}. Stopping execution.", show=True, caption=True)
                        await self.close()
                        return failures
                    elif failures:
                        log_sfx = "" if len(failures) > 1 else f"?{offset_key}={failures[-1].url.query.get(offset_key)}&limit={failures[-1].url.query.get('limit')}..."
                        log.error(f"Output incomplete.  {len(failures)} failure occured: [{failures[-1].method}] {failures[-1].url.path}{log_sfx}", caption=True)

                    for res in successful:  # Combines responses into a sigle Response object
                        r += res
                    break

            _limit = params.get("limit", 0)
            if offset_key == "offset":
                _offset = params.get(offset_key, 0)
                if params.get("limit") and r.output and len(r.output) == _limit:
                    if count and len(paged_output) >= count:
                        r.output = paged_output
                        r.raw = paged_raw
                        break
                    elif count and len(paged_output) < count:
                        next_limit = count - len(paged_output)
                        next_limit = _limit if next_limit > _limit else next_limit
                        params[offset_key] = _offset + next_limit
                    else:
                        params[offset_key] = _offset + _limit
                else:
                    r.output = paged_output
                    r.raw = paged_raw
                    break
            elif isinstance(r.raw, dict):  # The routing api endpoints use an opaque handle representing the next page or results, so they can not be batched, as we need the result to get the marker for the next call
                if r.raw.get("marker"):
                    params["marker"] = r.raw["marker"]
                else:
                    r.raw, r.output = paged_raw, paged_output
                    if r.raw.get("marker"):
                        del r.raw["marker"]
                    break
            else:
                break  # oto reset returns empty string (PUT)

        # No errors but the total provided by Central doesn't match the # of records
        try:
            if not count and not failures and isinstance(r.raw, dict)  and "total" in r.raw and isinstance(r.output, list) and len(r.output) < r.raw["total"]:
                log.warning(f"[{r.method}]{r.url.path} Total records {len(r.output)} != the total field ({r.raw['total']}) in raw response", show=True, caption=True, log=True)
        except Exception:
            ...  # r.raw could be bool for some POST endpoints

        await self.close()
        return r

    def _refresh_token(self, token_data: dict | List[dict], silent: bool = False) -> bool:
        """Refresh Aruba Central API tokens.  Get new set of access/refresh token.

        This method performs the actual refresh API call (via pycentral).

        Args:
            token_data (dict | List[dict]): Dict or list of dicts, where each dict is a
                pair of tokens ("access_token", "refresh_token").  If list, a refresh is attempted with
                each pair in order.  Stops once a refresh is successful.  Defaults to [].
            silent (bool, optional): Setting to True disables spinner. Defaults to False.

        Returns:
            bool: Bool indicating success/failure.
        """
        auth = self.auth
        token_data = utils.listify(token_data)
        token = None
        if not silent:
            self.spinner.start("Attempting to Refresh Tokens")
        for idx, t in enumerate(token_data):
            try:
                if idx == 1:
                    if not silent:
                        self.spinner.fail()
                        self.spinner.start(f"{self.spinner.status} [bright_red blink]retry[/]")
                token = auth.refreshToken(t)

                # TODO make req_cnt a property that fetches len of requests
                self.requests += [LoggedRequests("/oauth2/token", "POST")]
                self.requests[-1].ok = True if token else False
                self.req_cnt += 1

                if token:
                    auth.storeToken(token)
                    auth.central_info["token"] = token
                    if not silent:
                        self.spinner.stop()
                    break
            except Exception as e:
                log.exception(f"Attempt to refresh token returned {e.__class__.__name__} {e}")

        if token:
            self.headers["authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"
            if not silent:
                self.spinner.succeed()
        elif not silent:
            self.spinner.fail()

        return token is not None

    def refresh_token(self, token_data: dict = None, silent: bool = False) -> None:
        """Refresh Aruba Central API tokens.  Get new set of access/refresh token.

        This method calls into _refresh_token which performs the API call.

        Args:
            token_data (Union[dict, List[dict]], optional): Dict or list of dicts, where each dict is a
                pair of tokens ("access_token", "refresh_token").  If list, a refresh is attempted with
                each pair in order.  Stops once a refresh is successful.  If no token_data is provided
                it is collected from cache or config.
            silent (bool, optional): Setting to True disables spinner. Defaults to False.

        Returns:
            bool: Bool indicating success/failure.
        """
        auth = self.auth
        if not token_data:
            token: dict | None = auth.central_info.get("token")
            retry_token: dict | None = auth.central_info.get("retry_token")
            token_data = [t for t in [token, retry_token] if t is not None]
        else:
            token_data = [token_data]

        success = self._refresh_token(token_data, silent=silent)
        if success:
            return True
        elif not silent:
            token_data = self.get_token_from_user()
            return self._refresh_token(token_data)
        else:
            return False

    def get_token_from_user(self) -> dict:
        """Handle invalid or expired tokens

        For prod cluster it leverages ArubaCentralBase.handleTokenExpiry()
        For internal cluster it extends functionality to support user input
        copy paste of Download Token dict from Aruba Central GUI.

        Returns:
            dict: access and refresh tokens extracted from user provided json
        """
        auth = self.auth
        token_data: dict = None
        if sys.stdin.isatty():
            internal = "internal" in auth.central_info["base_url"]

            token_only = [
                auth.central_info.get("username") is None
                or auth.central_info["username"].endswith("@hpe.com") and internal,
                auth.central_info.get("password") is None
            ]

            # TODO allow new client_id client_secret and accept paste from "Download Tokens"
            if True in token_only:
                prompt = "\n".join(
                    [
                        "[red]:warning:  Refresh Failed[/]: please generate new tokens for:",
                        f"    customer_id: [bright_green]{auth.central_info['customer_id']}[/]",
                        f"    client_id: [bright_green]{auth.central_info['client_id']}[/]",
                        "\n[grey42 italic]:information:  If you create new tokens using the same [cyan]Application Name[/], the [cyan]client_id[/]/[cyan]client_secret[/] will stay consistent.[/]\n",
                        "Paste the text from the [cyan]View Tokens[/] -> [cyan]Download Tokens[/] popup in Central UI.",
                    ]
                )

                token_data = utils.get_multiline_input(prompt, return_type="dict")
            else:
                auth.handleTokenExpiry()
                token_data = auth.getToken()
        else:
            auth.handleTokenExpiry()
            token_data = auth.getToken()

        return token_data

    async def _request(self, func: callable, *args, **kwargs):
        # async with ClientSession() as self.aio_session:
        async with self.aio_session:
            return await func(*args, **kwargs)

    def request(self, func: callable, *args, **kwargs) -> Response:
        """non async to async wrapper for all API calls

        Args:
            func (callable): One of the CentralApi methods

        Returns:
            centralcli.response.Response object
        """
        log.debug(f"sending request to {func.__name__} with args {args}, kwargs {kwargs}")
        return asyncio.run(self._request(func, *args, **kwargs))

    async def _batch_request(self, api_calls: List[BatchRequest], continue_on_fail: bool = False, retry_failed: bool = False) -> List[Response]:
        # TODO implement retry_failed
        # TODO return Response objects for all requests, when first fails build empty Response for remainder so not to cause issue when unpacking
        self.silent = True
        m_resp: List[Response] = []
        _tot_start = time.perf_counter()

        if self.requests: # a call has been made no need to verify first call (token refresh)
            chunked_calls = utils.chunker(api_calls, MAX_CALLS_PER_CHUNK)
        else:
            resp: Response = await api_calls[0].func(
                *api_calls[0].args,
                **api_calls[0].kwargs
                )
            if (not resp and not continue_on_fail) or len(api_calls) == 1:
                return [resp]

            m_resp: List[Response] = [resp]
            chunked_calls = utils.chunker(api_calls[1:], MAX_CALLS_PER_CHUNK)

        # Make calls 6 at a time ensuring timing so that 7 per second limit is not exceeded
        # Doing 7 at a time resulted in rate_limit hits.  some failures result in retries which could cause a rate_limit hit within the chunk
        for chunk in chunked_calls:
            _start = time.perf_counter()

            _calls_per_chunk = len(chunk)
            if chunk != chunked_calls[-1]:
                chunk += [self.BatchRequest(asyncio.sleep, 1)]

            m_resp += await asyncio.gather(
                *[call.func(*call.args, **call.kwargs) for call in chunk]
            )

            _elapsed = time.perf_counter() - _start
            log.debug(f"chunk of {_calls_per_chunk} took {_elapsed:.2f}.")
            # await self.pause(_start)  # pause to next second

        # strip out the pause/limiter (asyncio.sleep) responses (None)
        m_resp = utils.strip_none(m_resp)

        log.info(f"Batch Requests exec {len(api_calls)} calls, Total time {time.perf_counter() - _tot_start:.2f}")

        self.silent = False

        if all([hasattr(r, "rl") for r in m_resp]):
            log.debug(f"API per sec rate-limit as reported by Central: {[r.rl.remain_sec for r in m_resp]}")

        return m_resp

    # TODO retry_failed not implemented remove if not going to use it.
    def batch_request(self, api_calls: List[BatchRequest], continue_on_fail: bool = False, retry_failed: bool = False) -> List[Response]:
        """non async to async wrapper for multiple parallel API calls

        First entry is ran alone, if successful the remaining calls
        are made in parallel.

        Args:
            api_calls (List[BatchRequest]): List of BatchRequest objects.
            continue_on_fail (bool, optional): Continue with subsequent requests if first request fails.
                defaults to False.  Only the first request is validated for success.
            retry_failed (bool, optional): Retry failed requests
                some return codes result in retry regardless. Defaults to False

        Returns:
            List[Response]: List of centralcli.response.Response objects.
        """
        return asyncio.run(self._batch_request(api_calls, continue_on_fail=continue_on_fail, retry_failed=retry_failed))

    def build_url(func):
        @wraps(func)
        def wrapper(self: Session, url: StrOrURL, *args, **kwargs):
            url = url if url.startswith("http") or self.base_url is not None else self.auth.central_info["base_url"] + url
            return func(self, url, *args, **kwargs)

        return wrapper

    @build_url
    async def get(self, url, params: dict = {}, headers: dict = None, count: int = None, **kwargs) -> Response:
        return await self.api_call(url, params=params, headers=headers, count=count, **kwargs)

    @build_url
    async def post(
        self,
        url: StrOrURL,
        params: dict = {},
        payload: dict = None,
        json_data: dict | list = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        return await self.api_call(url, method="POST", data=payload, json_data=json_data, params=params, headers=headers, **kwargs)

    @build_url
    async def put(
        self,
        url: StrOrURL,
        params: dict = {},
        payload: dict = None,
        json_data: dict | list = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        return await self.api_call(url, method="PUT", data=payload, json_data=json_data, params=params, headers=headers, **kwargs)

    @build_url
    async def patch(
        self,
        url: StrOrURL,
        params: dict = {},
        payload: dict = None,
        json_data: dict | list = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        return await self.api_call(url, method="PATCH", data=payload, json_data=json_data, params=params, headers=headers, **kwargs)

    @build_url
    async def delete(
        self,
        url: StrOrURL,
        params: dict = {},
        payload: dict = None,
        json_data: dict | list = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        return await self.api_call(url, method="DELETE", data=payload, json_data=json_data, params=params, headers=headers, **kwargs)