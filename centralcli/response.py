#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any, Dict, List, Literal, Tuple, Union, Optional, TYPE_CHECKING

from aiohttp import ClientResponse, ClientSession
from aiohttp.client_exceptions import ClientConnectorError, ClientOSError, ContentTypeError
from aiohttp.http_exceptions import ContentLengthError
from pycentral.base import ArubaCentralBase
from rich import print
from rich.console import Console
from rich.status import Status
from rich.text import Text
from rich.markup import escape

if TYPE_CHECKING:
    from rich.style import StyleType
    from rich.console import RenderableType

from yarl import URL

from centralcli import config, log, utils
from centralcli.constants import lib_to_api
from centralcli.exceptions import CentralCliException


from . import cleaner, constants, render
from .typedefs import Method, StrOrURL


DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
INIT_TS = time.monotonic()
MAX_CALLS_PER_CHUNK = 6
DEFAULT_SPIN_TXT = "\U0001f4a9 DEFAULT_SPIN_TXT \U0001f4a9"  # should never see this, makes it more obvious we missed a spinner update
err_console = Console(stderr=True)


# TODO args should be expanded here *args simplifies instantiation
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
        self.near_limit = self.near_sec or self.near_day

    def __bool__(self) -> bool:
        return self.ok

    def __str__(self):
        if self.call_performed:
            return f"API Rate Limit: {self.remain_day} of {self.total_day} remaining."
        else:
            return "No API call was performed."

    def __rich__(self):
        return f"[reset][italic dark_olive_green2]{str(self)}[/]"

    def __len__(self) -> int:
        return len(self.__str__())

    def __lt__(self, other) -> bool:
        return True if self.remain_day is None else bool(self.remain_day < other)

    def __le__(self, other) -> bool:
        return False if self.remain_day is None else bool(self.remain_day <= other)

    def __eq__(self, other) -> bool:
        return False if self.remain_day is None else bool(self.remain_day == other)

    def __gt__(self, other) -> bool:
        return False if self.remain_day is None else bool(self.remain_day > other)

    def __ge__(self, other) -> bool:
        return False if self.remain_day is None else bool(self.remain_day >= other)

    @property
    def ok(self) -> bool:
        if self.used_sec + self.remain_sec + self.total_sec == 0:
            secs_ok = True
        else:
            secs_ok = True if self.remain_sec > 0 else False
        return True if self.remain_day != 0 and secs_ok else False

    @property
    def near_sec(self) -> bool:
        return True if self.remain_sec <= 2 else False

    @property
    def near_day(self) -> bool:
        return True if self.remain_day <= 100 else False

    @property
    def text(self) -> str:
        full_text = f"{self}\n{' ':16}{self.remain_sec}/sec of {self.total_sec}/sec remaining."
        return full_text if self.call_performed else str(self)


class Spinner(Status):
    """A Spinner Object that adds methods to rich.status.Status object

        Args:
            status (RenderableType): A status renderable (str or Text typically).
            console (Console, optional): Console instance to use, or None for global console. Defaults to None.
            spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
            spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
            speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
            refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5.
    """
    def __init__(
        self,
        status: RenderableType,
        *,
        console: Optional[Console] = None,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        super().__init__(status, console=console, spinner=spinner, spinner_style=spinner_style, speed=speed, refresh_per_second=refresh_per_second)

    def fail(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":x:  {self.status}") if not text else self.console.print(f":x:  {text}")

    def succeed(self, text: RenderableType = None) -> None:
        if self._live.is_started:
            self._live.stop()
        self.console.print(f":heavy_check_mark:  {self.status}") if not text else self.console.print(f":heavy_check_mark:  {text}")

    def start(
            self,
            text: RenderableType = None,
            *,
            spinner: str = None,
            spinner_style: StyleType = None,
            speed: float = None,
        ) -> None:
        if any([text, spinner, spinner_style, speed]):
            self.update(text, spinner=spinner, spinner_style=spinner_style, speed=speed)
        if not self._live.is_started:
            self._live.start()



class Response:
    '''wrapper ClientResponse object

    Assigns commonly evaluated attributes regardless of API execution result

    The following attributes will always be available:
        - ok (bool): indicates success/failure of aiohttp.ClientSession.request()
        - output (Any): The content returned from the response (outer keys removed)
        - raw (Any): The original un-cleaned response from the API request
        - error (str): Error message indicating the nature of a failed response
        - status (int): http status code returned from response
        - rl (RateLimit): Rate Limit info extracted from aiohttp.ClientResponse headers.

    Create instance by providing at minimum one of the following parameters:
        - response (ClientResponse) and output(typically List[dict]): all other parameters ignored if providing response
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
        data_key: str = None,
    ):
        """Response Constructor

        Provide response: (aiohttp.ClientResponse), and
                output: Normally a List[Dict], extracted from whatever key in the raw response
                holds the actual data

        Can be used to create a Response without doing an API call by providing any of
            url, output, error, status_code, ok (OK is calculated based on existence of error if not provided)

        Args:
            response (ClientResponse, optional): aiohttp.ClientResponse. Defaults to None.
            url (Union[URL, str], optional): Request URL. Defaults to "".
            ok (bool, optional): bool indicating success. Defaults to None.
            error (str, optional): Error info. Defaults to None.
            output (Any, optional): Main payload of the response. Defaults to {}.
            raw (Any, optional): raw response payload. Defaults to {}.
            status_code (int, optional): Response http status code. Defaults to None.
            elapsed (Union[int, float], optional): Amount of time elapsed for request. Defaults to 0.
            rl_str (str, optional): Rate Limit String. Defaults to None.
            data_key: (str, optional): The dict key where the actual data is held in the response.
        """
        self.rl = rl_str or RateLimit(response)
        self._response = response
        self.output = output
        self.raw = raw
        self._ok = ok
        self.method = ""
        self.elapsed = elapsed
        self.data_key = data_key
        if response is not None:
            self.url = response.url if isinstance(response.url, URL) else URL(response.url)
            self.error = response.reason
            try:
                self.status = response.status
                self.method = response.method
            except AttributeError:  # Using requests module for templates due to multi-part issue in aiohttp
                self.status = response.status_code
                self.method = response.request.method

            _offset_str = ""
            # /routing endpoints use "marker" rather than "offset" for pagination
            offset_key = "marker" if "marker" in self.url.query or self.url.path.startswith("/api/routing/") else "offset"
            if offset_key in self.url.query:
                if offset_key == "offset" and int(self.url.query[offset_key]) > 0:  # only show full query_str if call is beyond first page of results.
                    _offset_str = f" {offset_key}: {self.url.query[offset_key]} limit: {self.url.query.get('limit', '?')}"
                else:  # marker is not an int
                    _offset_str = f" {offset_key}: {self.url.query[offset_key]} limit: {self.url.query.get('limit', '?')}"

            _log_msg = f"[{self.error}] {self.method}:{self.url.path}{_offset_str} Elapsed: {elapsed:.2f}"
            if not self.ok:
                self.output = self.output or self.error
                if isinstance(self.output, dict) and "description" in self.output or "detail" in self.output:
                    log.error(_log_msg.replace("Elapsed:", f'{self.output.get("description", self.output.get("detail", ""))} Elapsed:'))
                else:
                    log.error(_log_msg)
            elif not isinstance(self, CombinedResponse):
                log.info(_log_msg)
        else:
            if error:
                self.error = error
                self.output = output or error
            elif output or isinstance(output, (list, dict)):  # empty list or dict, when used as constructor still ok
                self.error = error or "OK"

            self.url = URL(url)
            self.status = status_code or 299 if self.ok else 418

        if isinstance(self.output, dict) and "error" in self.output and "error_description" in self.output:
            self.output = f"{self.output['error']}: {self.output['error_description']}"

    def __bool__(self):
        if self._response:
            return self._response.ok

        if self.error and self.error != "OK":
            return self._ok or False

        if self.output or isinstance(self.output, (list, dict)):
            return self._ok or True

        raise CentralCliException("Unable to determine success status of Response")

    @property
    def ok(self):
        return self.__bool__()

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.error}) object at {hex(id(self))}>"

    # DEPRECATED cab be removed once we ensure no ill effects of simplifying __rich__
    @staticmethod
    def _split_inner(val):
        pfx = ''
        if isinstance(val, list):
            pfx = '\n'
            if len(val) == 1:
                val = val[0] if "\n" not in val[0] else "\n    " + "\n    ".join(val[0].split("\n"))
            elif all(isinstance(d, dict) for d in val):
                val = render.output(outdata=val, tablefmt="yaml")
                val = "\n".join([f"    {line}" for line in val.file.splitlines()])

        if isinstance(val, dict):
            pfx = '\n'
            val = render.output(outdata=[val], tablefmt="yaml")
            val = "\n".join([f"      {line}" for line in val.file.splitlines() if not line.endswith(": []")])

        val = f'{pfx}{val}' if not hasattr(val, "__rich__") else val.__rich__()

        return val

    def __rich__(self):
        fg = "red" if not self.ok else "bright_green"
        if self.status != 418:
            status_code = f"  status code: [{fg}]{self.status}[/]\n"
        else:
            status_code = ""

        # Shouldn't happen but if we got what looks like a JSON decoded string try to convert it.  Log so we can fix... convert prior to instantiation
        if isinstance(self.output, str) and "{\n" in self.output:
            try:
                log.warning(f"Response was sent JSON formatted output from [{self.method}]{self.url}")
                self.output = json.loads(self.output)
            except json.JSONDecodeError:
                log.error(f"Failed to decode output from [{self.method}]{self.url}")

        # indent single line output
        if isinstance(self.output, str) and "{\n" in self.output:
            if "\n" not in self.output:
                r = f"  {self.output}"
            elif "{\n" in self.output:
                r = "  {}".format(
                    self.output.replace('\n  ', '\n').replace('\n', '\n  ')
                )
        elif isinstance(self.output, dict):  # TODO just use yaml.safe_dump here
            data = utils.strip_none(self.output, strip_empty_obj=True)
            # remove redundant status_code if response includes it in output
            stripped_status = False
            if "status_code" in self.output and self.output["status_code"] == self.status:
                del data["status_code"]
                stripped_status = True

            if data:
                r = render.output([data], tablefmt="yaml")
                r = Text.from_ansi(r.tty)
                r = "\n".join([f"  {line}" for line in str(r).splitlines()])
            else:
                emoji = '\u2139' if self.ok else '\u26a0'
                r = "" if stripped_status else f"  {emoji}  Empty Response.  This may be normal."
        elif not self.output:
            emoji = '\u2139' if self.ok else '\u26a0'  # \u2139 = :information:, \u26a0 = :warning:
            r = f"  {emoji}  Empty Response.  This may be normal."
        else:
            r = f"  {self.output}"

        if not self.ok:
            if self.error:
                if isinstance(self.error, dict) and self.url.path in self.error:  # CombinedResponse.__super__()
                    r = f"  {self.error[self.url.path]}\n{r}"
                elif str(self.error) != str(self.output):
                    r = f"  {self.error}\n{r}"
            if isinstance(self.output, dict) and "message" in self.output and isinstance(self.output["message"], str) and '\n' not in self.output["message"]:
                r = r.replace("message: ", "").replace(self.output["message"], f'[red italic]{self.output["message"]}[/]')

        r = r.replace("failed:", "[red]failed[/]:").replace("FAILED", "[red]FAILED[/red]").replace("failed_devices", "[red]failed_devices[/]").replace("INVALID", "[red]INVALID[/]")
        r = r.replace("SUCCESS", "[bright_green]SUCCESS[/]").replace("Success", "[bright_green]Success[/]").replace("Success[/]fully", "Successfully[/]")
        r = r.replace("Success", "[bright_green]Success[/]").replace("success", "[bright_green]success[/]").replace("success[/]fully", "successfully[/]").replace("succeeded_devices", "[bright_green]succeeded_devices[/]")
        r = r.replace("invalid_device", "[red]invalid_device[/]").replace("blocked_device", "[red]blocked_device[/red]").replace("ATHENA_ERROR_DEVICE_ALREADY_EXIST", "[italic dark_orange3]Device already exists[/]")

        # sanitize sensitive data for demos
        if config.sanitize and config.sanitize_file.is_file():
            r = utils.Output().sanitize_strings(r)

        return f"{status_code}{r}"

    def __str__(self):
        console = Console(force_terminal=False)
        with console.capture() as cap:
            console.print(self.__rich__())
        return cap.get()

    def __setitem__(self, name: str, value: Any) -> None:
        print(f"set name {name} value {value}")
        if isinstance(name, (str, int)) and hasattr(self, "output") and name in self.output:
            self.output[name] = value

    def __len__(self):
        return(len(self.output)) if not isinstance(self.output, str) else 0

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

    def __add__(self, other):
        if not isinstance(self.raw, dict) or not isinstance(other.raw, dict):
            raise TypeError("raw attribute is expected to be a dict")
        if not isinstance(self.output, list) or not isinstance(other.output, list):
            raise TypeError("output attribute is expected to be a list")

        if not self.data_key:
            found_keys = [k for k in self.raw if self.raw[k] == self.output]
            if len(found_keys) != 1:
                raise ValueError(f"Unable to add Response, unable to determine primary key with data.  Found {len(found_keys)} potential data keys.")

        key = self.data_key or found_keys[0]

        self.raw[key] = self.raw[key] + other.raw[key]
        if "count" in self.raw and "count" in other.raw:
            self.raw["count"] += other.raw["count"]
        if self.url.path == "/monitoring/v2/events":  # events url will change the total on subsequent pagination events could go up or down.
            self.raw["total"] = other.raw["total"]


        if isinstance(self.output, list) and isinstance(other.output, list):
            self.output += other.output
        else:
            raise TypeError("Output attribute is expected to be a list")

        self.rl = min([r.rl for r in [self, other]])

        return self

    @property
    def table(self) -> List[Dict[str, Any]]:
        """Returns output with only the keys that are common across all items.

        Returns:
            List[Dict[str, Any]]: resp.output with only keys common across all items.
        """
        if isinstance(self.output, list) and all([isinstance(d, dict) for d in self.output]):
            common_keys = set.intersection(*map(set, self.output))
            return [{k: d[k] for k in common_keys} for d in self.output]

        return self.output

    @property
    def status_code(self) -> int:
        """Make attributes used for status code for both aiohttp and requests valid."""
        return self.status


class Session():
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
        self.spinner = Spinner("Collecting Data...")
        self.updated_at = time.monotonic()
        self.rl_log = [f"{self.updated_at - INIT_TS:.2f} [INIT] {type(self).__name__} object at {hex(id(self))}"]
        self.BatchRequest = BatchRequest
        self.running_spinners: List[str] = []

    @property
    def aio_session(self):
        if self._aio_session:
            if self._aio_session.closed:
                return ClientSession()
            return self._aio_session
        else:
            self._aio_session = ClientSession()
            return self._aio_session

    @aio_session.setter
    def aio_session(self, session: ClientSession):
        self._aio_session = session

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

    async def exec_api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
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

                if "invalid_token" in resp.output:
                    spin_txt_retry =  "(retry after token refresh)"
                    self.refresh_token()
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

    async def handle_pagination(self, res: Response, paged_raw: Union[Dict, List, None] = None, paged_output: Union[Dict, List, None] = None,) -> Tuple:
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
                for outer_key in constants.STRIP_KEYS:
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

    async def api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                       method: str = "GET", headers: dict = {}, params: dict = {}, callback: callable = None,
                       callback_kwargs: Any = {}, count: int = None, **kwargs: Any) -> Response:
        """Perform API calls and handle paging

        Args:
            url (str): The API Endpoint URL
            data (dict, optional): Data passed to aiohttp.ClientSession. Defaults to None.
            json_data (Union[dict, list], optional): passed to aiohttp.ClientSession. Defaults to None.
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
        if params and params.get("limit") and config.limit:
            log.info(f'paging limit being overridden by config: {params.get("limit")} --> {config.limit}')
            params["limit"] = config.limit

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
            token: Union[dict, None] = auth.central_info.get("token")
            retry_token: Union[dict, None] = auth.central_info.get("retry_token")
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

    async def get(self, url, params: dict = {}, headers: dict = None, count: int = None, **kwargs) -> Response:
        f_url = url if url.startswith("http") else self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, params=params, headers=headers, count=count, **kwargs)

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


class CombinedResponse(Response):
    def flatten_resp(responses: List[Response]) -> Response:
        _failed = [r for r in responses if not r.ok]
        _passed = responses if not _failed else [r for r in responses if r.ok]

        elapsed = 0
        raw = {}
        output = []
        for idx, r in enumerate(_passed or _failed):  # if no requests passed we loop through _failed to retain output {"message": "error message..."}
            this_output = r.output.copy()
            this_raw = r.raw.copy()
            if idx == 0:
                output = this_output
                output_type = type(r.output)
                raw = {r.url.path: this_raw}
            else:
                raw[r.url.path] = this_raw
                if output_type is list:
                    output += this_output
                elif output_type is dict:
                    output = {**output, **this_output}
                else:
                    raise CentralCliException(f"flatten_resp received unexpected output attribute type {type(r.output)}.  Expected dict or list.")
            if r.elapsed:
                elapsed += r.elapsed

        # failed responses are added to end of raw output
        if _passed:
            for r in _failed:
                raw[r.url.path] = r.raw.copy()


        # for combining device calls, adds consistent "type" to all devices
        def _get_type(data: dict) -> Literal["ap", "gw", "sw", "cx"] | None:
            if "ap_deployment_mode" in data:
                return "ap"

            if "switch_type" in data:
                switch_types = {
                    "AOS-S": "sw",
                    "AOS-CX": "cx"
                }
                return switch_types.get(data["switch_type"], data["switch_type"])

            if "device_type" in data:
                if data["device_type"].lower() == "mc":
                    return "gw"
                else:
                    raise CentralCliException(f'Unexpected device type {data["device_type"]}')

        if all(
            [
                u.startswith("/monitoring") and any([u.endswith(s)] for s in ["/gateways", "/aps", "/switches"]) for u in [r.url.path for r in responses]
            ]
        ):
            if isinstance(output, list) and all([isinstance(inner, dict) for inner in output]):
                output = [
                    {
                        **inner,
                        "type": _get_type(inner)
                    }
                    for inner in output
                ]

        resp = _passed[-1] if _passed else _failed[-1]

        return {"response": resp._response, "output": output, "raw": raw, "elapsed": elapsed}

    def __init__(self, responses: List[Response], combiner_func: callable = flatten_resp):
        self.responses = responses
        combined_kwargs: dict = combiner_func(responses)
        super().__init__(**combined_kwargs)
        self.error = self.errors = {r.url.path: r.error for r in responses}
        self.rl = self._rl

    def __bool__(self):
        return any([r.ok for r in self.responses])

    def __len__(self):
        return sum([len(r) for r in self.responses if r.ok])

    def __repr__(self):
        _errors = list(self.errors.values())
        _unique_errors = set(_errors)
        err_msg = '|'.join([f'{e}:{_errors.count(e)}' for e in _unique_errors])

        return f"<{self.__module__}.{type(self).__name__} ({err_msg}) object at {hex(id(self))}>"

    @property
    def ok(self):
        return self.__bool__()

    @property
    def all_ok(self):
        return all([r.ok for r in self.responses])

    @property
    def passed(self):
        return [r for r in self.responses if r.ok]

    @property
    def failed(self):
        return [r for r in self.responses if not r.ok]

    @property
    def urls(self) -> List[URL]:
        return [r.url for r in self.responses]

    @property
    def _rl(self) -> RateLimit:
        calls = [r for r in self.responses if r.rl.ok]
        return sorted([r for r in calls or self.responses], key=lambda r: r.rl)[0].rl

