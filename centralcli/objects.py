"""object Classes"""

from __future__ import annotations

from typing import Literal
from json import JSONEncoder
import pendulum
from pathlib import Path


TimeFormat = Literal["day-datetime", "durwords", "durwords-short", "timediff", "mdyt", "log"]

class DateTime():
    def __init__(self, epoch: int | float, format: TimeFormat = "day-datetime", tz: str = "local", pad_hour: bool = False, round_to_minute: bool = False,) -> None:
        self.epoch = self.normalize_epoch(epoch)
        self.tz = tz
        self.pad_hour = pad_hour
        self.round_to_minute = round_to_minute
        self.pretty = getattr(self, format.replace("-", "_"))

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

    @property
    def day_datetime(self) -> str:
        """Thu, May 7, 2020 3:49 AM"""
        return pendulum.from_timestamp(self.epoch, tz=self.tz).to_day_datetime_string()

    @property
    def durwords(self) -> str:
        """2 weeks 1 day 1 hour 21 minutes 2 seconds
        """
        return pendulum.duration(seconds=int(self.epoch)).in_words()

    @property
    def durwords_short(self) -> str:
        """2w 1d 1h 21m 2s (without seconds if round_to_minute = True)
        """
        if not self.epoch:
            return ""

        _words = pendulum.duration(seconds=int(self.epoch)).in_words()
        value_pairs = [(int(_words.split()[idx]), _words.split()[idx + 1])  for idx in range(0, len(_words.split()), 2)]
        words, minute = "", None
        for value, word in value_pairs:
            if self.round_to_minute:
                if word.startswith("minute"):
                    minute = value
                elif word.startswith("second"):
                    if minute:
                        if minute > 30:
                            words = words.replace(f"{minute}m", f"{minute + 1}m")
                    continue
            words = f'{words} {value}{list(word)[0]}'

        return words.strip()

    @property
    def timediff(self) -> str:
        """47 minutes ago"""
        return "" if self.epoch is None else pendulum.from_timestamp(self.epoch, tz=self.tz).diff_for_humans()

    @property
    def mdyt(self) -> str:
        """May 07, 2020 3:49:24 AM"""
        return pendulum.from_timestamp(self.epoch, tz=self.tz).format(f"MMM DD, YYYY {'h' if not self.pad_hour else 'hh'}:mm:ss A")

    @property
    def log(self) -> str:
        """Jan 08 7:59:00 PM"""
        if isinstance(self.epoch, str):
            try:
                self.epoch = float(self.epoch)
            except TypeError:
                return self.epoch

        return pendulum.from_timestamp(self.epoch, tz=self.tz).format(f"MMM DD {'h' if not self.pad_hour else 'hh'}:mm:ss A")


class Encoder(JSONEncoder):
    """
    A Custom JSON Encoder to handle custom DateTime object (and Path) during JSON serialization.
    """
    def default(self, obj):
        return obj if not isinstance(obj, DateTime) and not isinstance(obj, Path) else str(obj)

