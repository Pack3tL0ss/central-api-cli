"""object Classes"""

from __future__ import annotations

from typing import Literal
from json import JSONEncoder
import pendulum


TimeFormat = Literal["day-datetime", "durwords", "durwords-short", "timediff", "mdyt", "log"]



def _convert_epoch(self, epoch: float) -> str:
    # Thu, May 7, 2020 3:49 AM
    return pendulum.from_timestamp(epoch, tz="local").to_day_datetime_string()


def _duration_words(secs: int | str) -> str:
    return pendulum.duration(seconds=int(secs)).in_words()


def _duration_words_short(secs: int | str) -> str:
    words = pendulum.duration(seconds=int(secs)).in_words()
    # a bit cheesy, but didn't want to mess with regex
    replace_words = [
        (" years", "y"),
        (" year", "y"),
        (" weeks", "w"),
        (" week", "w"),
        (" days", "d"),
        (" day", "d"),
        (" hours", "h"),
        (" hour", "h"),
        (" minutes", "m"),
        (" minute", "m"),
        (" seconds", "s"),
        (" second", "s"),
    ]
    for orig, short in replace_words:
        words = words.replace(orig, short)
    return words



def _time_diff_words(epoch: float | None) -> str:
    return "" if epoch is None else pendulum.from_timestamp(epoch, tz="local").diff_for_humans()


def _log_timestamp(epoch: float) -> str:
    if isinstance(epoch, str):
        try:
            epoch = float(epoch)
        except TypeError:
            return epoch

    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD h:mm:ss A")


def _mdyt_timestamp(epoch: float) -> str:
    # May 07, 2020 3:49:24 AM
    return pendulum.from_timestamp(epoch, tz="local").format("MMM DD, YYYY h:mm:ss A")

TIME_FUNCS = {
    "day-datetime": _convert_epoch,
    "durwords": _duration_words,
    "durwords-short": _duration_words_short,
    "timediff": _time_diff_words,
    "mdyt": _mdyt_timestamp,
    "log": _log_timestamp
}

class DateTime():
    def __init__(self, epoch: int | float, format: TimeFormat = "day-datetime") -> None:
        self.epoch = self.normalize_epoch(epoch)
        self.pretty = TIME_FUNCS[format](self.epoch)

    def normalize_epoch(self, epoch: int | float) -> int | float:
        if str(epoch).isdigit() and len(str(int(epoch))) > 10:
            epoch = epoch / 1000

        return epoch

    def __str__(self):
        return self.pretty

    def __bool__(self):
        return self.epoch and self.epoch > 0

    def __len__(self) -> int:
        return len(self.epoch)

    def __lt__(self, other) -> bool:
        return self.epoch < other

    def __le__(self, other) -> bool:
        return self.epoch <= other

    def __eq__(self, other) -> bool:
        return self.epoch == other

    def __gt__(self, other) -> bool:
        return self.epoch > other

    def __ge__(self, other) -> bool:
        return self.epoch >= other


class Encoder(JSONEncoder):
    """
    A Custom JSON Encoder to handle custom DateTime object during JSON serialization.
    """
    def default(self, o):
        return o if not isinstance(o, DateTime) else str(o)

