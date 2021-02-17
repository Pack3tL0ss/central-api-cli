from aiohttp.client_exceptions import ContentTypeError
from pycentral.base import ArubaCentralBase
from . import cleaner
from typing import Union, List, Any

from centralcli import config, utils, log
from halo import Halo

import sys
import typer
import json
import aiohttp
import time
# import asyncio


DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}


class Response:
    '''wrapper aiohttp.ClientResponse object

    Assigns commonly evaluated attributes regardless of API execution result

    The following attributes will always be available:
        ok: (bool) indicates success/failure of aiohttp.ClientSession.request()
        output: (Any) The content returned from the response
        error: (str) Error message indicating the nature of a failed response
        status: (int) http status code returned from response

    Create instance by providing at minimum one of the following parameters:
        response: (aiohttp.ClientResponse) all other paramaters ignored if providing response
        error: (str) ok, output, status set to logical default if not provided
        output: (Any) ok, error, status set to logical default if not provided
        ** Only provide output orr
    '''
    def __init__(self, response: aiohttp.ClientResponse = None, url: str = None, ok: bool = None,
                 error: str = None, output: Any = {}, status_code: int = None, elapsed: Union[int, float] = 0):
        self._response = response
        self.output = output
        self.ok = ok
        if response:
            self.ok = response.ok
            self.url = response.url
            self.error = response.reason
            self.status = response.status
            if not self.ok:
                self.output = self.output or self.error
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

    def __bool__(self):
        return self.ok

    def __repr__(self):
        # f"<{self.__module__}.{type(self).__name__} ({'OK' if self.ok else 'ERROR'}) object at {hex(id(self))}>"
        return f"<{self.__module__}.{type(self).__name__} ({self.error}) object at {hex(id(self))}>"

    def __str__(self):
        if isinstance(self.output, dict):
            return "\n".join([f"  {k}: {v}" for k, v in self.output.items()])

        return str(self.output) if self.output else self.error

    def __setitem__(self, name: str, value: Any) -> None:
        if isinstance(name, (str, int)) and hasattr(self, "output") and name in self.output:
            self.output[name] = value

    def __getitem__(self, key):
        return self.output[key]

    def __getattr__(self, name: str) -> Any:
        if hasattr(self, "output") and self.output:
            if name in self.output:
                return self.output[name]

        if hasattr(self._response, name):
            return getattr(self._response, name)

        raise AttributeError(f"'Response' object has no attribute '{name}'")

    def __iter__(self):
        for _dict in self.output:
            for k, v in _dict.items():
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
    def __init__(self, auth: ArubaCentralBase = None, aio_session: aiohttp.ClientSession = None) -> None:
        self.auth = auth
        self._aio_session = aio_session
        self.headers = DEFAULT_HEADERS
        self.headers["authorization"] = f"Bearer {auth.central_info['token']['access_token']}"
        self.ssl = auth.ssl_verify

    @property
    def aio_session(self):
        return self._aio_session if self._aio_session and not self._aio_session.closed else aiohttp.ClientSession()

    @aio_session.setter
    def aio_session(self, session: aiohttp.ClientSession):
        self._aio_session = session

    async def exec_api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                            method: str = "GET", headers: dict = {}, params: dict = {}, **kwargs) -> Response:
        auth = self.auth
        resp, spin = None, None
        _data_msg = ' ' if not url else f' ({url.split("arubanetworks.com/")[-1]}) '
        spin_txt_data = f"Collecting Data{_data_msg}from Aruba Central API Gateway..."
        for _ in range(0, 2):
            if _ > 0:
                spin_txt_data += f" retry {_}"

            log.debug(f"Attempt API Call to:{_data_msg}Try: {_ + 1}\n"
                      f"\taccess token: {auth.central_info.get('token', {}).get('access_token', {})}\n"
                      f"\trefresh token: {auth.central_info.get('token', {}).get('refresh_token', {})}"
                      )

            try:
                with Halo(spin_txt_data, enabled=bool(utils.tty)) as spin:
                    _start = time.time()
                    headers = self.headers if not headers else {**self.headers, **headers}
                    # -- // THE API REQUEST \\ --
                    resp = await self.aio_session.request(method=method, url=url, params=params, data=data, json=json_data,
                                                          headers=headers, ssl=self.ssl, **kwargs)

                    elapsed = time.time() - _start

                    try:
                        output = await resp.json()
                        output = cleaner.strip_outer_keys(output)
                    except (json.decoder.JSONDecodeError, ContentTypeError):
                        output = await resp.text()

                resp = Response(resp, output=output, elapsed=elapsed)
            except Exception as e:
                resp = Response(error=str(e), url=url)
                _ += 1

            fail_msg = f"{spin.text}\n  {resp.output}"
            if not resp:
                spin.fail(fail_msg)
                if "invalid_token" in resp.output:
                    self.refresh_token()
                else:
                    log.error(f"API [{method}] {url} Error Returned: {resp.error}")
                    break
            else:
                spin.succeed()
                break

        return resp

    async def api_call(self, url: str, data: dict = None, json_data: Union[dict, list] = None,
                       method: str = "GET", headers: dict = {}, params: dict = {}, callback: callable = None,
                       callback_kwargs: Any = {}, **kwargs: Any) -> Response:

        if params and params.get("limit") and config.limit:
            log.info(f'paging limit being overriden by config: {params.get("limit")} --> {config.limit}')
            params["limit"] = config.limit  # for debugging can set a smaller limit in config to test paging

        # allow passing of default kwargs (None) for param/json_data, all keys with None Value are stripped here.
        # supports 2 levels beyond that needs to be done in calling method.
        # TODO handy to have this in one common place, but should move
        # to central.py so it's can be used as a central library independent of cli
        params = utils.strip_none(params)
        json_data = utils.strip_none(json_data)
        if json_data:  # strip second nested dict if all keys = NoneType
            y = json_data.copy()
            for k in y:
                if isinstance(y[k], dict):
                    y[k] = utils.strip_none(y[k])
                    if not y[k]:
                        del json_data[k]

        # Output pagination loop
        paged_output = None
        while True:
            # -- // Attempt API Call \\ --
            r = await self.exec_api_call(url, data=data, json_data=json_data, method=method, headers=headers,
                                         params=params, **kwargs)

            if not r.ok:
                break

            # data cleaner methods to strip any useless columns, change key names, etc.
            elif callback is not None:
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
                params["offset"] = _offset + _limit
            else:
                r.output = paged_output
                break

        return r

    def _refresh_token(self, token_data: Union[dict, List[dict]] = []) -> bool:
        auth = self.auth
        token_data = utils.listify(token_data)
        token = None
        spin = Halo("Attempting to Refresh Token")
        spin.start()
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
                    break
            except Exception as e:
                log.exception(f"Attempt to refresh token returned {e.__class__.__name__} {e}")

        if token:
            self.headers["authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"
            spin.succeed()
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
            self._refresh_token(self.get_token_from_user())

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
            # if internal:
            token_only = [
                auth.central_info.get("username") is None
                or auth.central_info["username"].endswith("@hpe.com") and internal,
                auth.central_info.get("password") is None
            ]
            # if not central.central_info["username"] or not central.central_info["password"]:
            if True in token_only:
                prompt = f"\n{typer.style('Refresh Failed', fg='red')} Please Generate a new Token for:" \
                        f"\n    customer_id: {auth.central_info['customer_id']}" \
                        f"\n    client_id: {auth.central_info['client_id']}" \
                        "\n\nPaste result of `Download Tokens` from Central UI."\
                        f"\nUse {typer.style('CTRL-D', fg='magenta')} on empty line after contents to submit." \
                        f"\n{typer.style('exit', fg='magenta')} to abort." \
                        f"\n{typer.style('Waiting for Input...', fg='cyan', blink=True)}\n"

                # typer.launch doesn't work on wsl attempts powershell
                # typer.launch(f'{central.central_info["base_url"]}/platform/frontend/#!/APIGATEWAY')
                token_data = utils.get_multiline_input(prompt, return_type="dict")
            else:
                auth.handleTokenExpiry()
        else:
            auth.handleTokenExpiry()

        return token_data
