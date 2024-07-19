"""object Classes"""

from __future__ import annotations

from typing import Literal
from json import JSONEncoder
import pendulum
from pathlib import Path


TimeFormat = Literal["day-datetime", "durwords", "durwords-short", "timediff", "mdyt", "log"]


def _convert_epoch(epoch: float) -> str:
    """Thu, May 7, 2020 3:49 AM"""
    return pendulum.from_timestamp(epoch, tz="local").to_day_datetime_string()


def _log_timestamp(epoch: float) -> str:
    """Jan 08 7:59:00 PM"""
    if isinstance(epoch, str):
        try:
            epoch = float(epoch)
        except TypeError:
            return epoch

    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD h:mm:ss A")


def _mdyt_timestamp(epoch: float) -> str:
    """May 07, 2020 3:49:24 AM"""
    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD, YYYY h:mm:ss A")


def _duration_words(secs: int | str) -> str:
    """2 weeks 1 day 1 hour 21 minutes 2 seconds"""
    return pendulum.duration(seconds=int(secs)).in_words()


def _duration_words_short(secs: int | str, round_to_minute: bool = False) -> str:
    """2w 1d 1h 21m 2s (without seconds if round_to_minute = True)"""
    if not secs:
        return ""

    _words = pendulum.duration(seconds=int(secs)).in_words()
    value_pairs = [(int(_words.split()[idx]), _words.split()[idx + 1])  for idx in range(0, len(_words.split()), 2)]
    words, minute = "", None
    for value, word in value_pairs:
        if round_to_minute:
            if word.startswith("minute"):
                minute = value
            elif word.startswith("second"):
                if minute:
                    if minute > 30:
                        words = words.replace(f"{minute}m", f"{minute + 1}m")
                continue
        words = f'{words} {value}{list(word)[0]}'

    return words.strip()


def _time_diff_words(epoch: float | None) -> str:
    """47 minutes ago"""
    return "" if epoch is None else pendulum.from_timestamp(epoch, tz="local").diff_for_humans()


TIME_FUNCS = {
    "day-datetime": _convert_epoch,
    "durwords": _duration_words,
    "durwords-short": _duration_words_short,
    "timediff": _time_diff_words,
    "mdyt": _mdyt_timestamp,
    "log": _log_timestamp
}

class DateTime():
    def __init__(self, epoch: int | float, format: TimeFormat = "day-datetime", *formatter_args, **formatter_kwargs) -> None:
        self.epoch = self.normalize_epoch(epoch)
        self.pretty = TIME_FUNCS[format](self.epoch, *formatter_args, **formatter_kwargs)

    def normalize_epoch(self, epoch: int | float) -> int | float:
        if str(epoch).isdigit() and len(str(int(epoch))) > 10:
            epoch = epoch / 1000

        return epoch if not str(epoch).endswith(".0") else int(epoch)

    def __str__(self):
        return self.pretty

    def __bool__(self):
        return bool(self.epoch and self.epoch > 0)

    def __len__(self) -> int:
        return len(self.epoch)

    def __lt__(self, other) -> bool:
        return True if self.epoch is None else bool(self.epoch < other)

    def __le__(self, other) -> bool:
        return False if self.epoch is None else bool(self.epoch <= other)

    def __eq__(self, other) -> bool:
        return False if self.epoch is None else bool(self.epoch == other)

    def __gt__(self, other) -> bool:
        return False if self.epoch is None else bool(self.epoch > other)

    def __ge__(self, other) -> bool:
        return False if self.epoch is None else bool(self.epoch >= other)


class Encoder(JSONEncoder):
    """
    A Custom JSON Encoder to handle custom DateTime object during JSON serialization.
    """
    def default(self, o):
        return o if not isinstance(o, DateTime) and not isinstance(o, Path) else str(o)

