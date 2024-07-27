"""object Classes"""

from __future__ import annotations

from typing import Literal
from json import JSONEncoder
import pendulum
from pathlib import Path


TimeFormat = Literal["day-datetime", "durwords", "durwords-short", "timediff", "mdyt", "log"]

class DateTime():
    """DateTime object with a number of timestamp to string converters for various representations used by the CLI.
    """
    def __init__(self, epoch: int | float, format: TimeFormat = "day-datetime", tz: str = "local", pad_hour: bool = False, round_to_minute: bool = False,) -> None:
        """DateTime constructor.

        Args:
            epoch (int | float): Epoch timestamp.
            format (TimeFormat, optional): Format assigned to the pretty attribute. Defaults to "day-datetime".
            tz (str, optional): TimeZone of the timestamp. Defaults to "local".
            pad_hour (bool, optional): If True mdyt and log formats will zero pad the hour. Defaults to False.
            round_to_minute (bool, optional): If True durwords-short will strip the seconds and round to the nearest minute. Defaults to False.
        """
        self.epoch = self.normalize_epoch(epoch)
        self.tz = tz
        self.pad_hour = pad_hour
        self.round_to_minute = round_to_minute
        self.pretty = getattr(self, format.replace("-", "_"))

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

    def normalize_epoch(self, epoch: int | float) -> int | float:
        """normalize timestamp/epoch to seconds

        Args:
            epoch (int | float): timestamp/epoch is seconds or milliseconds

        Returns:
            int | float: timestamp/epoch in seconds
        """
        if str(epoch).isdigit() and len(str(int(epoch))) > 10:
            epoch = epoch / 1000

        return epoch if not str(epoch).endswith(".0") else int(epoch)

    @property
    def day_datetime(self) -> str:
        """Render date in day_datetime format

        Returns:
            str: Date as string in format: 'Thu, May 7, 2020 3:49 AM'
        """
        return pendulum.from_timestamp(self.epoch, tz=self.tz).to_day_datetime_string()

    @property
    def durwords(self) -> str:
        """Render elapsed time in seconds as duration string.

        Returns:
            str: Duration as string in format: '2 weeks 1 day 1 hour 21 minutes 2 seconds'
        """
        return pendulum.duration(seconds=int(self.epoch)).in_words()

    @property
    def durwords_short(self) -> str:
        """Render timestamp as duration in short format.

        Strips off seconds and rounds to minute if Class instantiated with round_to_minutes=True

        Returns:
            str: Duration as string in format: '2w 1d 1h 21m 2s' (without seconds if round_to_minute = True)
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
        """Render duration words representing the difference between self.epoch and now.

        Returns:
            str: The difference between now and the timestamp in the format: '47 minutes ago'.
        """
        return "" if self.epoch is None else pendulum.from_timestamp(self.epoch, tz=self.tz).diff_for_humans()

    @property
    def mdyt(self) -> str:
        """Render date as human string like Mon day, year time AM/PM.

        Hour is zero-padded if Class is instantiated with pad_hour=True

        Returns:
            str: Date as string in format: 'May 7, 2020 3:49:24 AM' or 'May 7, 2020 03:49:24 AM' if pad_hour=True
        """
        return pendulum.from_timestamp(self.epoch, tz=self.tz).format(f"MMM DD, YYYY {'h' if not self.pad_hour else 'hh'}:mm:ss A")

    @property
    def log(self) -> str:
        """Render date as human string in log format.

        Hour is zero-padded if Class is instantiated with pad_hour=True

        Returns:
            str: Date as string in format: 'Jan 08 7:59:00 PM' or 'Jan 08 07:59:00 PM' if pad_hour=True
        """
        if isinstance(self.epoch, str):
            try:
                self.epoch = float(self.epoch)
            except TypeError:
                return self.epoch

        return pendulum.from_timestamp(self.epoch, tz=self.tz).format(f"MMM DD {'h' if not self.pad_hour else 'hh'}:mm:ss A")


class Encoder(JSONEncoder):
    """A Custom JSON Encoder to handle custom DateTime object (and Path) during JSON serialization.
    """
    def default(self, obj):
        return obj if not isinstance(obj, DateTime) and not isinstance(obj, Path) else str(obj)

