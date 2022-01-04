#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp.client_exceptions import ContentTypeError
from pycentral.base import ArubaCentralBase
from . import cleaner
from typing import Union, List, Any
from rich import print


from centralcli import config, utils, log
from halo import Halo

import sys
import typer
import json
import aiohttp
import time


DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


class RateLimit:
    def __init__(self, resp: aiohttp.ClientResponse = None):
        self.total, self.remain, self.total_per_sec, self.remain_per_sec = 0, 0, 0, 0
        if resp and hasattr(resp, "headers"):
            rh = resp.headers
            self.total = int(f"{rh.get('X-RateLimit-Limit-day', 0)}")
            self.remain = int(f"{rh.get('X-RateLimit-Remaining-day', 0)}")
            self.total_per_sec = int(f"{rh.get('X-RateLimit-Limit-second', 0)}")
            self.remain_per_sec = int(f"{rh.get('X-RateLimit-Remaining-second', 0)}")
        self.used = self.total - self.remain
        self.used_per_sec = self.total_per_sec - self.remain_per_sec
        # self.ok = True if sum([self.total, self.used]) > 0 else False
        self.ok = True if all([self.remain != 0, self.remain_per_sec > 1]) else False
        self.call_performed = False if resp is None else True

    def __str__(self):
        if self.call_performed:
            return f"API Rate Limit: {self.remain} of {self.total} remaining." if self.ok else ""
        else:
            return "No API call was performed."


class Response:
    '''wrapper aiohttp.ClientResponse object

    Assigns commonly evaluated attributes regardless of API execution result

    The following attributes will always be available:
        - ok (bool): indicates success/failure of aiohttp.ClientSession.request()
        - output (Any): The content returned from the response (outer keys removed)
        - raw (Any): The original un-cleaned response from the API request
        - error (str): Error message indicating the nature of a failed response
        - status (int): http status code returned from response

    Create instance by providing at minimum one of the following parameters:
        - response (aiohttp.ClientResponse): all other paramaters ignored if providing response
        - error (str): ok, output, status set to logical default if not provided
            OK / __bool__ is False if error is provided and ok is not.
        - output (Any): ok, error, status set to logical default if not provided
            OK / __bool__ is True if output provided with no error or ok arg.
    '''
    def __init__(
        self,
        response: aiohttp.ClientResponse = None,
        url: str = None,
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
            if not self.ok:
                self.output = self.output or self.error
                log.error(f"[{response.reason}] {response.url} Elapsed: {elapsed}")
            else:
                log.info(f"[{response.reason}] {response.url} Elapsed: {elapsed}")
        else:
            if error:
                self.ok = ok or False
                self.error = error
                self.output = output or error
            elif output or isinstance(output, (list, dict)):  # empty list or dict, when used as constructor still ok
                self.ok = ok or True
                self.error = error or "OK"

            self.url = str(url)
            self.status = status_code or 299 if self.ok else 418

        if self.output and "error" in self.output and "error_description" in self.output and isinstance(self.output, dict):
            self.output = f"{self.output['error']}: {self.output['error_description']}"

    # @property
    # def output(self) -> int:
    #     return self.output

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
            # val = "".join([f"\n    {k}: {val[k] if not isinstance(val[k], (dict, list) else )}" for k in val if val[k]])

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
                    # r = self.output

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

    def get(self, key: Any, default: Any = None):
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


def get_multiline_input(prompt: str = None, print_func: callable = print,
                        return_type: str = None, **kwargs) -> Union[List[str], dict, str]:
    def _get_multiline_sub(prompt: str = prompt, print_func: callable = print_func, **kwargs):
        prompt = prompt or \
            "Enter/Paste your content. Then Ctrl-D or Ctrl-Z ( windows ) to submit.\n Enter 'exit' to abort"
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


class Session:
    def __init__(
        self,
        auth: ArubaCentralBase = None,
        aio_session: aiohttp.ClientSession = None,
        silent: bool = True,
    ) -> None:
        self.silent = silent  # squelches out automatic display of failed Responses.
        self.auth = auth
        self._aio_session = aio_session
        self.headers = DEFAULT_HEADERS
        self.headers["authorization"] = f"Bearer {auth.central_info['token']['access_token']}"
        self.ssl = auth.ssl_verify
        self.req_cnt = 1
        self.spinner = Halo("Collecting Data...", enabled=bool(utils.tty))
        self.spinner._spinner_id = "spin_thread"

    @property
    def aio_session(self):
        return self._aio_session if self._aio_session and not self._aio_session.closed else aiohttp.ClientSession()

    @aio_session.setter
    def aio_session(self, session: aiohttp.ClientSession):
        self._aio_session = session

    async def exec_api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                            method: str = "GET", headers: dict = {}, params: dict = {}, **kwargs) -> Response:
        auth = self.auth

        resp = None
        _data_msg = ' ' if not url else f' [{url.split("arubanetworks.com/")[-1]}]'
        run_sfx = '' if self.req_cnt == 1 else f' Request: {self.req_cnt}'
        spin_word = "Collecting" if method == "GET" else "Sending"
        spin_txt_run = f"{spin_word} Data...{run_sfx}"
        spin_txt_fail = f"{spin_word} Data{_data_msg}"
        self.spinner.text = spin_txt_run
        self.req_cnt += 1
        for _ in range(0, 2):
            if _ > 0:
                spin_txt_run = f"{spin_txt_run} (retry after token refresh)"

            log.debug(f"Attempt API Call to:{_data_msg}Try: {_ + 1}\n"
                      f"    access token: {auth.central_info.get('token', {}).get('access_token', {})}\n"
                      f"    refresh token: {auth.central_info.get('token', {}).get('refresh_token', {})}"
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

            try:
                _start = time.time()
                headers = self.headers if not headers else {**self.headers, **headers}
                # -- // THE API REQUEST \\ --
                self.spinner.start(spin_txt_run)
                resp = await self.aio_session.request(
                    method=method,
                    url=url,
                    params=params,
                    data=data,
                    json=json_data,
                    headers=headers,
                    ssl=self.ssl,
                    **kwargs
                )

                elapsed = time.time() - _start

                try:
                    output = await resp.json()
                    try:
                        raw_output = output.copy()
                    except AttributeError:
                        raw_output = output
                    output = cleaner.strip_outer_keys(output)
                except (json.decoder.JSONDecodeError, ContentTypeError):
                    output = raw_output = await resp.text()

                resp = Response(resp, output=output, raw=raw_output, elapsed=elapsed)
            except Exception as e:
                resp = Response(error=str(e), url=url)
                _ += 1

            fail_msg = spin_txt_fail if self.silent else f"{spin_txt_fail}\n  {resp.output}"
            if not resp:
                self.spinner.fail(fail_msg)
                if "invalid_token" in resp.output:
                    self.refresh_token()
                else:
                    log.error(f"[{method}][{resp.error}] {url}")
                    break
            else:
                # self.spinner.succeed()
                self.spinner.stop()
                break

        return resp

    async def api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                       method: str = "GET", headers: dict = {}, params: dict = {}, callback: callable = None,
                       callback_kwargs: Any = {}, count: int = None, **kwargs: Any) -> Response:

        # Debugging flag to lower paging limit to test paging with smaller chunks.
        if params and params.get("limit") and config.limit:
            log.info(f'paging limit being overridden by config: {params.get("limit")} --> {config.limit}')
            params["limit"] = config.limit  # for debugging can set a smaller limit in config to test paging

        # allow passing of default kwargs (None) for param/json_data, all keys with None Value are stripped here.
        # supports 2 levels beyond that needs to be done in calling method.
        params = utils.strip_none(params)
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
        while True:
            # -- // Attempt API Call \\ --
            r = await self.exec_api_call(url, data=data, json_data=json_data, method=method, headers=headers,
                                         params=params, **kwargs)

            if r.status == 429:
                log.warning(f"Rate Limit hit on call to {r.url} slowing down", show=True)
                time.sleep(1)
                continue

            if not r.ok:
                break

            # data cleaner methods to strip any useless columns, change key names, etc.
            elif callback is not None:
                # TODO [remove] moving callbacks to display output in cli, leaving methods to return raw output
                log.debug(f"DEV NOTE CALLBACK IN centralapi lib {url} -> {callback}")
                r.output = callback(r.output, **callback_kwargs or {})

            # -- // paging \\ --
            if not paged_output:
                paged_output = r.output
            else:
                if isinstance(r.output, dict):
                    paged_output = {**paged_output, **r.output}
                else:
                    paged_output += r.output

            _limit = params.get("limit", 0)
            _offset = params.get("offset", 0)
            if params.get("limit") and len(r.output) == _limit:
                if count and len(paged_output) >= count:
                    r.output = paged_output
                    break
                elif count and len(paged_output) < count:
                    next_limit = count - len(paged_output)
                    next_limit = _limit if next_limit > _limit else next_limit
                    params["offset"] = _offset + next_limit
                else:
                    params["offset"] = _offset + _limit
            else:
                r.output = paged_output
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
        auth = self.auth
        if not token_data:
            token: Union[dict, None] = auth.central_info.get("token")
            retry_token: Union[dict, None] = auth.central_info.get("retry_token")
            token_data = [t for t in [token, retry_token] if t is not None]
        else:
            token_data: List[dict] = [token_data]

        if self._refresh_token(token_data):
            return
        else:
            token_data = self.get_token_from_user()
            self._refresh_token(token_data)

    def get_token_from_user(self) -> None:
        """Handle invalid or expired tokens

        For prod cluster it leverages ArubaCentralBase.handleTokenExpiry()
        For internal cluster it extends functionality to support user input
        copy paste of Download Token dict from Aruba Central GUI.

        Args:
            central (ArubaCentralBase): ArubaCentralBase class
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
