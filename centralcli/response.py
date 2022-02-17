#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp.client_exceptions import ContentTypeError
from pycentral.base import ArubaCentralBase
from . import cleaner, constants
from typing import Union, List, Any
from rich import print
from yarl import URL
import aiohttp


from centralcli import config, utils, log
from halo import Halo

import sys
import typer
import json
from aiohttp import ClientSession, ClientResponse
import time


# FIXME  Based on logs failed req is logged in 2 places
# 02/09/2022 12:46:40 AM [1169][ERROR]: [Bad Request] https://internal-apigw.central.arubanetworks.com/platform/auditlogs/v1/logs/%5B'cencli'%5D Elapsed: 0.37046146392822266
# 02/09/2022 12:46:40 AM [1169][ERROR]: [GET][Bad Request] https://internal-apigw.central.arubanetworks.com/platform/auditlogs/v1/logs/['cencli']
# 02/09/2022 12:48:14 AM [1181][ERROR]: [Bad Request] https://internal-apigw.central.arubanetworks.com/platform/auditlogs/v1/logs/%5B'cencli'%5D Elapsed: 0.4578061103820801
# 02/09/2022 12:48:14 AM [1181][ERROR]: [GET][Bad Request] https://internal-apigw.central.arubanetworks.com/platform/auditlogs/v1/logs/['cencli']


DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
THROTTLE_BACKOFF = 0.5
INIT_TS = time.monotonic()
CENTRAL_MAX_CONNECTIONS = 7



class BatchRequest:
    def __init__(self, func: callable, args: Any = (), **kwargs: dict) -> None:
        """Constructor object for for api requests.

        Used to pass multiple requests into CentralApi batch_request method for parallel
        execution.

        Args:
            func (callable): The CentralApi method to execute.
            args (Any, optional): args passed on to method. Defaults to ().
            kwargs (dict, optional): kwargs passed on to method. Defaults to {}.
        """
        self.func = func
        self.args: Union[list, tuple] = args if isinstance(args, (list, tuple)) else (args, )
        self.kwargs = kwargs

class LoggedRequests:
    def __init__(self, url: str, method: str = "GET",):
        self.ts = float(f"{time.monotonic() - INIT_TS:.2f}")
        self.url = url
        self.method = method
        self.reason = None
        self.ok = None
        self.remain_day = None
        self.remain_sec = None

    def update(self, response: ClientResponse) -> None:
        rh = response.headers
        self.reason = response.reason
        self.ok = response.ok
        self.remain_day = int(f"{rh.get('X-RateLimit-Remaining-day', 0)}")
        self.remain_sec = int(f"{rh.get('X-RateLimit-Remaining-second', 0)}")

        return self


class RateLimit():
    def __init__(self, resp: ClientResponse = None):
        self.total_day, self.remain_day, self.total_sec, self.remain_sec = 0, 0, 0, 0
        if hasattr(resp, "headers"):
            rh = resp.headers
            self.total_day = int(f"{rh.get('X-RateLimit-Limit-day', 0)}")
            self.remain_day = int(f"{rh.get('X-RateLimit-Remaining-day', 0)}")
            self.total_sec = int(f"{rh.get('X-RateLimit-Limit-second', 0)}")
            self.remain_sec = int(f"{rh.get('X-RateLimit-Remaining-second', 0)}")
            self.call_performed = True
        else:
            self.call_performed = False

        self.used_day = self.total_day - self.remain_day
        self.used_sec = self.total_sec - self.remain_sec
        self.ok = True if all([self.remain_day != 0, self.remain_sec > 0]) else False
        self.near_limit = self.near_sec or self.near_day

    def __str__(self):
        if self.call_performed:
            return f"API Rate Limit: {self.remain_day} of {self.total_day} remaining."
        else:
            return "No API call was performed."

    @property
    def near_sec(self):
        return True if self.remain_sec <= 2 else False

    @property
    def near_day(self):
        return True if self.remain_day <= 100 else False

    @property
    def text(self):
        full_text = f"{self}\n{' ':16}{self.remain_sec}/sec of {self.total_sec}/sec remaining."
        return full_text if self.call_performed else str(self)


class Response:
    '''wrapper ClientResponse object

    Assigns commonly evaluated attributes regardless of API execution result

    The following attributes will always be available:
        - ok (bool): indicates success/failure of aiohttp.ClientSession.request()
        - output (Any): The content returned from the response (outer keys removed)
        - raw (Any): The original un-cleaned response from the API request
        - error (str): Error message indicating the nature of a failed response
        - status (int): http status code returned from response

    Create instance by providing at minimum one of the following parameters:
        - response (ClientResponse): all other paramaters ignored if providing response
        - error (str): ok, output, status set to logical default if not provided
            OK / __bool__ is False if error is provided and ok is not.
        - output (Any): ok, error, status set to logical default if not provided
            OK / __bool__ is True if output provided with no error or ok arg.
    '''
    def __init__(
        self,
        response: ClientResponse = None,
        url: Union[URL, str] = "",
        ok: bool = None,
        error: str = None,
        output: Any = {},
        raw: Any = {},
        status_code: int = None,
        elapsed: Union[int, float] = 0,
        rl_str: str = None,
    ):
        self.rl = rl_str or RateLimit(response)
        self._response = response
        self.output = output
        self.raw = raw
        self.ok = ok
        self.method = ""
        if response:
            self.ok = response.ok
            self.url = response.url
            self.error = response.reason
            self.status = response.status
            self.method = response.method
            _offset_str = ""
            if "offset" in response.url.query and int(response.url.query['offset']) > 0:
                _offset_str = f" offset: {response.url.query['offset']} limit: {response.url.query.get('limit', '?')}"
            _log_msg = f"[{response.reason}] {response.method}:{response.url.path}{_offset_str} Elapsed: {elapsed:.2f}"
            if not self.ok:
                self.output = self.output or self.error
                log.error(_log_msg)
            else:
                log.info(_log_msg)
        else:
            if error:
                self.ok = ok or False
                self.error = error
                self.output = output or error
            elif output or isinstance(output, (list, dict)):  # empty list or dict, when used as constructor still ok
                self.ok = ok or True
                self.error = error or "OK"

            self.url = URL(url)
            self.status = status_code or 299 if self.ok else 418

        if self.output and "error" in self.output and "error_description" in self.output and isinstance(self.output, dict):
            self.output = f"{self.output['error']}: {self.output['error_description']}"

    def __bool__(self):
        return self.ok

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.error}) object at {hex(id(self))}>"

    @staticmethod
    def _split_inner(val):
        if isinstance(val, list):
            if len(val) == 1:
                val = val[0] if "\n" not in val[0] else "\n    " + "\n    ".join(val[0].split("\n"))
            elif all(isinstance(d, dict) for d in val):
                val = utils.output(outdata=val, tablefmt="yaml")
                val = "\n".join([f"    {line}" for line in val.file.splitlines()])

        if isinstance(val, dict):
            val = utils.output(outdata=[val], tablefmt="yaml")
            val = "\n".join([f"      {line}" for line in val.file.splitlines() if not line.endswith(": []")])

        return val

    def __str__(self):
        if self.status != 418:
            status_code = f"  status code: {self.status}\n"
        else:
            status_code = ""
        r = self.output

        # indent single line output
        if isinstance(self.output, str):
            if "\n" not in self.output:
                r = f"  {self.output}"
            elif "{\n" in self.output:
                try:
                    self.output = json.loads(self.output)
                except Exception:
                    r = "  {}".format(
                        self.output.replace('\n  ', '\n').replace('\n', '\n  ')
                    )

        if isinstance(self.output, dict):
            r = "\n".join(
                [
                    "  {}: {}".format(
                        k,
                        v if isinstance(v, (str, int)) else f"\n{self._split_inner(v)}",
                    ) for k, v in self.output.items() if k != "status" and (v or v is False)
                ]
            )

        # sanitize sensitive data for demos
        if config.sanitize and config.sanitize_file.is_file():
            r = utils.Output(config=config).sanitize_strings(r)

        return f"{status_code}{r}"

    def __setitem__(self, name: str, value: Any) -> None:
        print(f"set name {name} value {value}")
        if isinstance(name, (str, int)) and hasattr(self, "output") and name in self.output:
            self.output[name] = value

    def __len__(self):
        return(len(self.output))

    def __getitem__(self, key):
        return self.output[key]

    def __reversed__(self):
        return self.output[::-1]

    def __bytes__(self):
        if not self.output:
            return
        r = json.dumps(self.output)
        return r.encode("UTF-8")

    def __getattr__(self, name: str) -> Any:
        if hasattr(self, "output") and self.output:
            output = self.output

            if isinstance(output, list) and len(output) == 1:
                output = output[0]

            # return the responses list / dict attr if exist
            if hasattr(output, name):
                return getattr(output, name)

            if isinstance(output, dict) and name in output:
                return output[name]

        if hasattr(self._response, name):
            return getattr(self._response, name)

        raise AttributeError(f"'Response' object has no attribute '{name}'")

    def __iter__(self):
        try:
            for _dict in self.output:
                for k, v in _dict.items():
                    yield k, v
        except Exception:
            for k, v in self.output.items():
                yield k, v

    def get(self, key: Union[int, str], default: Any = None):
        if isinstance(self.output, dict):
            return self.output.get(key, default)

    def keys(self) -> list:
        if isinstance(self.output, dict):
            return self.output.keys()
        elif self.output and isinstance(self.output, (list, tuple)):
            return self.output[0].keys()
        else:
            raise TypeError("output attribute is not a valid type for keys method.")

    @property
    def status_code(self) -> int:
        """Make attributes used for status code for both aiohttp and requests valid."""
        return self.status


# TODO determine which is used.  same is in utils, can't recall if removed all refs one should be whacked
def get_multiline_input(prompt: str = None, print_func: callable = print,
                        return_type: str = None, **kwargs) -> Union[List[str], dict, str]:
    def _get_multiline_sub(prompt: str = prompt, print_func: callable = print_func, **kwargs):
        prompt = prompt or \
            "Enter/Paste your content. Then Ctrl-D or Ctrl-Z -> Enter ( windows ) to submit.\n Enter 'exit' to abort"
        print_func(prompt, **kwargs)
        contents, line = [], ''
        while line.strip().lower() != "exit":
            try:
                line = input()
                contents.append(line)
            except EOFError:
                break

        if line.strip().lower() == "exit":
            print("Aborted")
            exit()

        return contents

    contents = _get_multiline_sub(**kwargs)
    if return_type:
        if return_type == "dict":
            for _ in range(1, 3):
                try:
                    contents = json.loads("\n".join(contents))
                    break
                except Exception as e:
                    log.exception(f"get_multiline_input: Exception caught {e.__class__.__name__}\n{e}")
                    typer.secho("\n !!! Input appears to be invalid.  Please re-input "
                                "or Enter `exit` to exit !!! \n", fg="red")
                    contents = _get_multiline_sub(**kwargs)
        elif return_type == "str":
            contents = "\n".join(contents)

    return contents


class Session():
    RATE = 1
    MAX_TOKENS = 6

    def __init__(
        self,
        auth: ArubaCentralBase = None,
        aio_session: ClientSession = None,
        silent: bool = True,
    ) -> None:
        self.silent = silent  # squelches out automatic display of failed Responses.
        self.auth = auth
        self._aio_session = aio_session
        self.headers = DEFAULT_HEADERS
        self.headers["authorization"] = f"Bearer {auth.central_info['token']['access_token']}"
        self.ssl = auth.ssl_verify
        self.req_cnt = 1
        self.requests: List[LoggedRequests] = []
        self.throttle: int = 0
        self.spinner = Halo("Collecting Data...", enabled=bool(utils.tty))
        self.spinner._spinner_id = "spin_thread"
        self.tokens = self.MAX_TOKENS
        self.updated_at = time.monotonic()
        self.rl_log = [f"{self.updated_at - INIT_TS:.2f} [INIT] {type(self).__name__} object at {hex(id(self))}"]
        self.BatchRequest = BatchRequest

    @property
    def aio_session(self):
        if self._aio_session:
            if self._aio_session.closed:
                # TODO finiish refactor
                # log.warning("DEV NOTE: Client Session is closed. Providing new session.", show=True)
                return ClientSession()
            return self._aio_session
        else:
            # connector = aiohttp.TCPConnector(limit=CENTRAL_MAX_CONNECTIONS)
            # return ClientSession(connector=connector)
            return ClientSession()
        # return self._aio_session if self._aio_session and not self._aio_session.closed else ClientSession()

    @aio_session.setter
    def aio_session(self, session: ClientSession):
        self._aio_session = session

    async def exec_api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                            method: str = "GET", headers: dict = {}, params: dict = {}, **kwargs) -> Response:
        auth = self.auth
        resp = None
        # _url = URL(url).with_query({k: v for k, v in params.items() if k in {"offset", "limit"}})
        _url = URL(url).with_query(params)
        _data_msg = ' ' if not url else f' [{_url.path}]'
        run_sfx = '' if self.req_cnt == 1 else f' Request: {self.req_cnt}'
        spin_word = "Collecting" if method == "GET" else "Sending"
        spin_txt_run = f"{spin_word} Data...{run_sfx}"
        spin_txt_retry = ""
        spin_txt_fail = f"{spin_word} Data{_data_msg}"
        self.spinner.text = spin_txt_run
        for _ in range(0, 2):
            if _ > 0:
                spin_txt_run = f"{spin_txt_run} {spin_txt_retry}".rstrip()

            token_msg = (
                f"\n    access token: {auth.central_info.get('token', {}).get('access_token', {})}"
                f"\n    refresh token: {auth.central_info.get('token', {}).get('refresh_token', {})}"
            )
            log.debug(
                f"Attempt API Call to:{_data_msg}Try: {_ + 1}{token_msg if self.req_cnt == 1 else ''}"
            )
            if config.debugv:
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

            headers = self.headers if not headers else {**self.headers, **headers}
            try:
                req_log = LoggedRequests(_url.path_qs, method)

                # -- // THE API REQUEST \\ --
                #  -- // RATE LIMIT TEST \\ --
                # await self.wait_for_token()
                _start = time.monotonic()
                now = time.monotonic() - INIT_TS
                _try_cnt = [u.url for u in self.requests].count(_url.path_qs) + 1
                self.rl_log += [
                    f'{now:.2f} [{method}]{_url.path_qs} Try: {_try_cnt}'
                ]
                #  -- // RATE LIMIT TEST \\ --
                self.spinner.start(spin_txt_run)
                self.req_cnt += 1
                # TODO move batch_request _bacth_request, get, put, etc into Session
                # change where client is instantiated to _request / _batch_requests pass in the client
                # remove aio_session property call ClientSession() direct
                async with self.aio_session as client:
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
                    elapsed = time.monotonic() - _start
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

            except Exception as e:
                resp = Response(error=str(e), url=_url.path_qs)
                _ += 1

            fail_msg = spin_txt_fail if self.silent else f"{spin_txt_fail}\n  {resp.output}"
            if not resp:
                self.spinner.fail(fail_msg)
                if "invalid_token" in resp.output:
                    spin_txt_retry =  "(retry after token refresh)"
                    self.refresh_token()
                elif resp.status == 429:  # per second rate limit.
                    # log.error(f"[{method}][{resp.error}] {resp.url.path}{_offset_msg}")  # should be logged on Response __init__
                    spin_txt_retry = "(retry after hitting per second rate limit)"
                    self.rl_log += [f"{now:.2f} [:warning: [bright_red]RATE LIMIT HIT[/]] p/s: {resp.rl.remain_sec}: {_url.path_qs}"]
                    _ -= 1
                else:  # else
                    break
            else:
                if resp.rl.near_sec:
                    self.rl_log += [
                        f"{time.monotonic() - INIT_TS:.2f} [[bright_green]{resp.error}[/] but [dark_orange3]NEARING RATE LIMIT[/]] p/s: {resp.rl.remain_sec} {_url.path_qs}"
                    ]
                else:
                    self.rl_log += [
                        f"{time.monotonic() - INIT_TS:.2f} [[bright_green]{resp.error}[/]] p/s: {resp.rl.remain_sec} {_url.path_qs}"
                    ]
                self.spinner.stop()
                break

        return resp

    async def api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                       method: str = "GET", headers: dict = {}, params: dict = {}, callback: callable = None,
                       callback_kwargs: Any = {}, count: int = None, **kwargs: Any) -> Response:

        params = utils.strip_none(params)
        # if isinstance(url, URL):
        #     print(f"{url} is already yarl.URL")
        # url: URL = URL(url).with_query(params)  #  .update_query(params)

        # Debugging flag to lower paging limit to test paging with smaller chunks.
        if params and params.get("limit") and config.limit:
            log.info(f'paging limit being overridden by config: {params.get("limit")} --> {config.limit}')
            params["limit"] = config.limit  # for debugging can set a smaller limit in config to test paging

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
        while True:
            # -- // Attempt API Call \\ --
            r = await self.exec_api_call(url, data=data, json_data=json_data, method=method, headers=headers,
                                         params=params, **kwargs)
            if not r.ok:
                break

            # data cleaner methods to strip any useless columns, change key names, etc.
            elif callback is not None:
                # TODO [remove] moving callbacks to display output in cli, leaving methods to return raw output
                log.debug(f"DEV NOTE CALLBACK IN centralapi lib {r.url.path} -> {callback}")
                r.output = callback(r.output, **callback_kwargs or {})

            # -- // paging \\ --
            if not paged_output:
                paged_output = r.output
            else:
                if isinstance(r.output, dict):
                    paged_output = {**paged_output, **r.output}
                else:  # FIXME paged_output += r.output was also changed contents of paged_raw dunno why
                    paged_output = paged_output + r.output

            if not paged_raw:
                paged_raw = r.raw
            else:
                if isinstance(r.raw, dict):
                    for outer_key in constants.STRIP_KEYS:
                        if outer_key in r.raw and outer_key in paged_raw:
                            if isinstance(r.raw[outer_key], dict):
                                paged_raw[outer_key] = {**paged_raw[outer_key], **r.raw[outer_key]}
                            else:  # TODO use response magic method to do adds have Response figure this out
                                paged_raw[outer_key] += r.raw[outer_key]
                            break
                else:
                    paged_raw += r.raw

            _limit = params.get("limit", 0)
            _offset = params.get("offset", 0)
            if params.get("limit") and len(r.output) == _limit:
                if count and len(paged_output) >= count:
                    r.output = paged_output
                    r.raw = paged_raw
                    break
                elif count and len(paged_output) < count:
                    next_limit = count - len(paged_output)
                    next_limit = _limit if next_limit > _limit else next_limit
                    params["offset"] = _offset + next_limit
                else:
                    params["offset"] = _offset + _limit
            else:
                r.output = paged_output
                r.raw = paged_raw
                break

        return r

    def _refresh_token(self, token_data: Union[dict, List[dict]] = []) -> bool:
        auth = self.auth
        token_data = utils.listify(token_data)
        token = None
        spin = self.spinner
        spin.start("Attempting to Refresh Tokens")
        for idx, t in enumerate(token_data):
            try:
                if idx == 1:
                    spin.fail()
                    spin.text = spin.text + " retry"
                    spin.start()
                token = auth.refreshToken(t)
                if token:
                    auth.storeToken(token)
                    auth.central_info["token"] = token
                    spin.stop()
                    break
            except Exception as e:
                log.exception(f"Attempt to refresh token returned {e.__class__.__name__} {e}")

        if token:
            self.headers["authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"
            spin.succeed()
            # spin.stop()
        else:
            spin.fail()

        return token is not None

    def refresh_token(self, token_data: dict = None) -> None:
        # TODO update self.requests
        auth = self.auth
        if not token_data:
            token: Union[dict, None] = auth.central_info.get("token")
            retry_token: Union[dict, None] = auth.central_info.get("retry_token")
            token_data = [t for t in [token, retry_token] if t is not None]
        else:
            token_data = [token_data]

        if self._refresh_token(token_data):
            return
        else:
            token_data = self.get_token_from_user()
            self._refresh_token(token_data)

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

            if True in token_only:
                prompt = f"\n{typer.style('Refresh Failed', fg='red')} Please Generate a new Token for:" \
                        f"\n    customer_id: {auth.central_info['customer_id']}" \
                        f"\n    client_id: {auth.central_info['client_id']}" \
                        "\n\nPaste result of `Download Tokens` from Central UI."\
                        f"\nUse {typer.style('CTRL-D', fg='magenta')} on empty line after contents to submit." \
                        f"\n{typer.style('exit', fg='magenta')} to abort." \
                        f"\n{typer.style('Waiting for Input...', fg='cyan', blink=True)}\n"

                token_data = utils.get_multiline_input(prompt, return_type="dict")
            else:
                auth.handleTokenExpiry()
        else:
            auth.handleTokenExpiry()

        return token_data

    async def _request(self, func: callable, *args, **kwargs):
        async with ClientSession() as self.aio_session:
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

    async def _batch_request(self, api_calls: List[BatchRequest],) -> List[Response]:
        # async with ClientSession() as self.aio_session:
        # async with self.aio_session as client:
        # Always run first call solo to ensure access token validity
        self.silent = True
        _tot_start = time.monotonic()
        resp: Response = await api_calls[0].func(
            *api_calls[0].args,
            **api_calls[0].kwargs
            )
        if not resp or len(api_calls) == 1:
            return [resp]
        # client.close()

        chunked_calls = utils.chunker(api_calls, 7)
        # remove first call performed above from first chunk
        chunked_calls[0] = chunked_calls[0][1:]

        m_resp: List[Response] = [resp]

        # Make calls 7 at a time ensuring timing so that 7 per second limit is not exceeded
        for chunk in chunked_calls:
            # tasks = [asyncio.ensure_future(call.func(*call.args, **call.kwargs)) for call in chunk]

            # async with self.aio_session as client:
            _start = time.monotonic()
            # m_resp += await asyncio.gather(*tasks)
            m_resp += await asyncio.gather(
                *[call.func(*call.args, **call.kwargs) for call in chunk]
            )
            _elapsed = time.monotonic() - _start
            log.debug(f"chunk of {len(chunk)} took {_elapsed:.2f}.")

            if _elapsed < 1 and len(m_resp) < len(api_calls):
                time.sleep(1 - _elapsed)
                log.debug(f"sleeping {1 - _elapsed:.2f}")
            # client.close()

        log.debug(f"Batch Requests exec {len(api_calls)} calls, Total time {time.monotonic() - _tot_start:.2f}")

        self.silent = False

        log.debug(f"API per sec ratelimit as reported by Central: {[r.rl.remain_sec for r in m_resp]}")

        return m_resp

    # TODO return a BatchResponse object (subclass Response) where OK indicates all OK
    # and method that returns merged output from all resp...
    def batch_request(self, api_calls: List[BatchRequest],) -> List[Response]:
        """non async to async wrapper for multiple parallel API calls

        First entry is ran alone, if successful the remaining calls
        are made in parallel.

        Args:
            api_calls (List[BatchRequest]): List of BatchRequest objects.

        Returns:
            List[Response]: List of centralcli.response.Response objects.
        """
        return asyncio.run(self._batch_request(api_calls))

    async def get(self, url, params: dict = {}, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, params=params, headers=headers, **kwargs)

    async def post(
        self, url, params: dict = {}, payload: dict = None, json_data: Union[dict, list] = None, headers: dict = None, **kwargs
    ) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        if json_data:
            json_data = self.strip_none(json_data)
        return await self.api_call(
            f_url, method="POST", data=payload, json_data=json_data, params=params, headers=headers, **kwargs
        )

    async def put(
        self, url, params: dict = {}, payload: dict = None, json_data: Union[dict, list] = None, headers: dict = None, **kwargs
    ) -> Response:

        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(
            f_url, method="PUT", data=payload, json_data=json_data, params=params, headers=headers, **kwargs
        )

    async def patch(self, url, params: dict = {}, payload: dict = None,
                    json_data: Union[dict, list] = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="PATCH", data=payload,
                                   json_data=json_data, params=params, headers=headers, **kwargs)

    async def delete(
        self,
        url,
        params: dict = {},
        payload: dict = None,
        json_data: Union[dict, list] = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="DELETE", data=payload,
                                   json_data=json_data, params=params, headers=headers, **kwargs)