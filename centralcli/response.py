#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Union

from aiohttp import ClientResponse
from rich import print
from rich.console import Console
from rich.text import Text
from yarl import URL

from centralcli import config, log, utils
from centralcli.exceptions import CentralCliException

from . import render

if TYPE_CHECKING:
    from requests import Response as RequestsResponse


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

    @property
    def has_value(self) -> bool:
        return self.total_day > 0

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
        response: ClientResponse | RequestsResponse = None,
        url: Union[URL, str] = "",
        ok: bool = None,
        error: str = None,
        output: list[dict[str, Any]] | dict[str, Any] | str = None,
        raw: dict[str, Any] = None,
        status_code: int = None,
        elapsed: Union[int, float] = None,
        data_key: str = None,
        caption: str | list[str] = None
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
            data_key: (str, optional): The dict key where the actual data is held in the response.
            caption: (str | list[str], optional): Optional captions to be displayed with the response.
        """
        self.rl = RateLimit(response)
        self._response = response
        self.output = output or {}
        self.raw = raw or {}
        self._ok = ok
        self.method = ""
        self.elapsed = elapsed or 0
        self.data_key = data_key
        self.caption = caption
        if response is not None:
            self.url = response.url if isinstance(response.url, URL) else URL(response.url)
            self.error = response.reason
            if isinstance(response, ClientResponse):
                self.status = response.status
                self.method = response.method
            else:  # Using requests module for templates due to multi-part issue in aiohttp
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

            _log_msg = f"[{self.error}] {self.method}:{self.url.path}{_offset_str} Elapsed: {self.elapsed:.2f}"
            if not self.ok:
                self.output = self.output or self.error
                if isinstance(self.output, dict) and ("description" in self.output or "detail" in self.output):
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

    @ok.setter
    def ok(self, ok: bool):
        self._ok = ok

    def __repr__(self):
        return f"<{self.__module__}.{type(self).__name__} ({self.error}) object at {hex(id(self))}>"

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

        r = self._colorize_output(r)

        # sanitize sensitive data for demos
        if config.sanitize and config.sanitize_file.is_file():
            r = render.Output().sanitize_strings(r)

        return f"{status_code}{r}"

    def _colorize_output(self, output: str) -> str:
        re_word = {
            "ATHENA_ERROR_DEVICE_ALREADY_EXIST": "[italic dark_orange3]Device already exists[/]",
            "[bright_green][bright_green]": "[bright_green]",
            "[red][red]": "[red]",
            "[/][/]": "[/]",
            "[/]fully": "fully",
            "[/]_": "_"
        }
        green_words = [
            "success_list",
            "succeeded_devices",
            "successfully",
            "success",
        ]
        red_words = [
            "failed_list",
            "failed_devices",
            "invalid_device",
            "blocked_device",
            "failed",
            "invalid",
        ]
        words_by_color = {
            "bright_green": green_words,
            "red": red_words
        }
        funcs = [str.lower, str.capitalize, str.upper]
        for color, words in words_by_color.items():
            for word in words:
                for f in funcs:
                    word = f(word)
                    output = output.replace(word, f"[{color}]{word}[/]")

        for before, after in re_word.items():
            output = output.replace(before, after)

        return output

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

