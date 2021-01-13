from pycentral.base import ArubaCentralBase
from typing import Union, List, Any

from centralcli import config, utils, log, constants
from halo import Halo

import sys
import typer
import json


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


class Spinner:
    def __init__(self):
        self.spinner = None

    def __bool__(self):
        return bool(self.spinner)

    def __call__(self, spin_txt: str, function: callable, url: str = None, *args, name: str = None,
                 spinner: str = "dots", **kwargs) -> Any:

        name = name or spin_txt.replace(" ", "_").rstrip(".").lower()
        if not name.startswith("spinner_"):
            name = f"spinner_{name}"

        spin = None
        if sys.stdin.isatty():
            if log.DEBUG:
                log.info(spin_txt)
            else:
                # This is just a catch to ensure we don't start multiple spinners
                if self.spinner:  # stop a spinner if one was already running
                    spin = self.spinner
                    log.warning(f"A Spinner was already running '{spin.text}' updating to '{spin_txt}'")
                    spin.text == spin_txt
                    spin.spinner == "dots12" if spin.spinner == spinner else spinner
                else:  # start a new spinner
                    spin = Halo(text=spin_txt, spinner=spinner)
                    spin._spinner_id = name
                    self.spinner = spin.start()

        if url:
            args = (url, *args)

        # -- // API CALL \\ --
        r = function(*args, **kwargs)

        if spin:
            spin.succeed() if r.ok else spin.fail(f"{spin.text}\n  {r.json().get('error_description', r.text)}")
            self.spinner = None

        return r


class Session:
    def __init__(self, central: ArubaCentralBase = None) -> None:
        self.central = central

    def clean_response(self):
        _keys = [k for k in constants.STRIP_KEYS if k in self.output]
        if len(_keys) == 1:
            return self.output[_keys[0]]
        elif _keys:
            print(f"More wrapping keys than expected from return {_keys}")
        return self.output

    def api_call(self, url: str = '', *args: Any, callback: callable = None,
                 callback_kwargs: Any = {}, **kwargs: Any) -> bool:

        if kwargs.get("params", {}).get("limit") and config.limit:
            log.info(f'paging limit being overriden by config: {kwargs.get("params", {}).get("limit")} --> {config.limit}')
            kwargs["params"]["limit"] = config.limit  # for debugging can set a smaller limit in config to test paging

        output = None
        while True:
            try:
                # -- // Attempt API Call \\ --
                r = self._api_call(url, *args, **kwargs)

                self._response = r
                self.ok = r.ok
                self.status_code = r.status_code

                if "requests.models.Response" in str(r.__class__):
                    log.info(f"[{r.reason}] {r.url} Elapsed: {r.elapsed}")
                else:
                    log.warning("DEV Note: Response wrapper being used for something other than request")

                try:
                    self.output = r.json()
                    self.output = self.clean_response()
                except json.decoder.JSONDecodeError:
                    self.output = r.text

                self.error = r.reason
            except Exception as e:
                self.ok = False
                self.error = f"Session.api_call() Exception occurred: {e.__class__.__name__}\n\t{e}"
                self.output = e
                self.status_code = 418

            if not self.ok:
                log.error(f"API Call ({self.url}) Returned Failure ({self.status_code})\n\t"
                          f"output: {self.output}\n\terror: {self.error}")
                break

            # data cleaner methods to strip any useless columns, change key names, etc.
            elif callback is not None:
                self.output = callback(self.output, **callback_kwargs)

            # -- // paging \\ --
            if not output:
                output = self.output
            else:
                if isinstance(self.output, dict):
                    output = {**output, **self.output}
                else:
                    output += self.output

            _limit = kwargs.get("params", {}).get("limit", 0)
            _offset = kwargs.get("params", {}).get("offset", 0)
            if kwargs.get("params", {}).get("limit") and len(self.output) == _limit:
                kwargs["params"]["offset"] = _offset + _limit
            else:
                self.output = output
                break

        return self.ok

    def _api_call(self, url: str, *args, **kwargs):
        spinner = Spinner()
        central = self.central
        resp = None
        _data_msg = ' ' if not url else f' ({url.split("arubanetworks.com/")[-1]}) '
        spin_txt_data = f"Collecting Data{_data_msg}from Aruba Central API Gateway..."
        for _ in range(0, 2):
            if _ > 0:
                spin_txt_data += f" retry {_}"
            try:
                log.debug(f"Attempt API Call to:{_data_msg}Try: {_ + 1}\n"
                          f"\taccess token: {central.central_info.get('token', {}).get('access_token', {})}\n"
                          f"\trefresh token: {central.central_info.get('token', {}).get('refresh_token', {})}"
                          )

                resp = spinner(f"{spin_txt_data}", central.requestUrl, url, *args, **kwargs)

                if resp.status_code == 401 and "invalid_token" in resp.text:
                    self.refresh_token()
                else:
                    break
            except Exception as e:
                log.error(f"_API Call{_data_msg}{e.__class__.__name__} {e}")
                _ += 1

        return resp

    def refresh_token(self, token_data: dict = None) -> None:
        central = self.central

        def _refresh_token(token_data: Union[dict, List[dict]] = []) -> bool:
            # spinner = Spinner()
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
                    token = central.refreshToken(t)
                    if token:
                        central.storeToken(token)
                        central.central_info["token"] = token
                        break
                except Exception as e:
                    log.exception(f"Attempt to refresh token returned {e.__class__.__name__} {e}")
            spin.succeed() if token else spin.fail()

            return token is not None

        if not token_data:
            token: Union[dict, None] = central.central_info.get("token")
            retry_token: Union[dict, None] = central.central_info.get("retry_token")
            token_data = [t for t in [token, retry_token] if t is not None]
        else:
            token_data: List[dict] = [token_data]

        if _refresh_token(token_data):
            return
        else:
            _refresh_token(self.get_token_from_user())

    def get_token_from_user(self) -> None:
        """Handle invalid or expired tokens

        For prod cluster it leverages ArubaCentralBase.handleTokenExpiry()
        For internal cluster it extends functionality to support user input
        copy paste of Download Token dict from Aruba Central GUI.

        Args:
            central (ArubaCentralBase): ArubaCentralBase class
        """
        central = self.central
        token_data: dict = None
        if sys.stdin.isatty():
            internal = "internal" in central.central_info["base_url"]
            if internal:
                prompt = f"\n{typer.style('Refresh Failed', fg='red')} Please Generate a new Token for:" \
                        f"\n    customer_id: {central.central_info['customer_id']}" \
                        f"\n    client_id: {central.central_info['client_id']}" \
                        "\n\nPaste result of `Download Tokens` from Central UI."\
                        f"\nUse {typer.style('CTRL-D', fg='magenta')} on empty line after contents to submit" \
                        f"\nEnter {typer.style('exit', fg='magenta')} --> {typer.style('Enter', fg='magenta')} " \
                        f"--> {typer.style('CTRL-D', fg='magenta')} to abort." \
                        f"\n{typer.style('Waiting for Input...', fg='cyan', blink=True)}\n"

                # typer.launch doesn't work on wsl attempts powershell
                # typer.launch(f'{central.central_info["base_url"]}/platform/frontend/#!/APIGATEWAY')
                token_data = utils.get_multiline_input(prompt, return_type="dict")
            else:
                central.handleTokenExpiry()
        else:
            central.handleTokenExpiry()

        return token_data


class Response(Session):
    '''wrapper for requests.response object

    Assigns commonly evaluated attributes regardless of success
    Otherwise resp.ok  and bool(resp) will always be assigned and will be True or False
    '''
    def __init__(self, central: ArubaCentralBase = None, url: str = '', *args: Any, callback: callable = None,
                 callback_kwargs: Any = {}, ok: bool = False, error: str = '', output: Any = {},
                 status_code: int = 418, **kwargs: Any):
        self.url = url
        self._response = None
        self.ok = ok
        self.error = error
        self.status_code = status_code
        self.output = output
        if output:  # used to create consistent Response object without API call (data already collected from cache)
            self.output = output
            self.ok = True
            self.error = "OK"
            self.status_code = 299
        else:
            super().__init__(central)

            if central is not None:
                if args:  # TODO determining if I've passed any additional args now that url was specified
                    log.warning(f"Developer Note args exist {args}")
                self.api_call(url, *args, callback=callback, callback_kwargs=callback_kwargs, **kwargs)

    def __bool__(self):
        return self.ok

    def __repr__(self):
        f"<{self.__module__}.{type(self).__name__} ({'OK' if self.ok else 'ERROR'}) object at {hex(id(self))}>"

    def __str__(self):
        return str(self.output) if self.output else self.error

    def __setitem__(self, name: str, value: Any) -> None:
        if isinstance(name, (str, int)) and hasattr(self, "output") and name in self.output:
            self.output[name] = value

    def __getitem__(self, key):
        return self.output[key]

    def __getattr__(self, name: str) -> Any:
        # print(f"hit {name}")
        if hasattr(self, "output") and self.output:
            if name in self.output:
                return self.output[name]
            else:
                # TODO can likely remove now that all responses go through cleaner to strip these keys
                # return from 2nd level of dict if 2nd level value is a dict
                _keys = [k for k in constants.STRIP_KEYS if k in self.output]
                if _keys and name in self.output[_keys[0]] and isinstance(self.output[_keys[0]], dict):
                    return self.output[_keys[0]]

        if hasattr(self._response, name):
            return getattr(self._response, name)

        raise AttributeError(f"'Response' object has no attribute '{name}'")

    def __iter__(self):
        for _dict in self.output:
            for k, v in _dict.items():
                yield k, v

    def get(self, key, default: Any = None):
        if isinstance(self.output, dict):
            return self.output.get(key, default)

    def keys(self):
        return self.output.keys()
