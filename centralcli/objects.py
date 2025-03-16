"""object Classes"""

from __future__ import annotations

from typing import Literal
from json import JSONEncoder
import pendulum
from pathlib import Path


TimeFormat = Literal["day-datetime", "durwords", "durwords-short", "timediff", "timediff-past", "mdyt", "log", "date-string"]

class DateTime():
    """DateTime object with a number of timestamp to string converters for various representations used by the CLI.
    """
    def __init__(self, timestamp: int | float | str, format: TimeFormat = "day-datetime", tz: str = "local", pad_hour: bool = False, round_to_minute: bool = False, format_expiration: bool = False) -> None:
        """DateTime constructor.

        Args:
            timestamp (int | float): Epoch timestamp, int representing duration in seconds or iso formatted date string, TimeZone is expected to by UTC.
            format (TimeFormat, optional): Format assigned to the pretty attribute. Defaults to "day-datetime".
            tz (str, optional): TimeZone of the desired output timestamp. Defaults to "local".
            pad_hour (bool, optional): If True mdyt and log formats will zero pad the hour. Defaults to False.
            round_to_minute (bool, optional): If True durwords-short will strip the seconds and round to the nearest minute. Defaults to False.
            format_expiration (bool, optional): Applies when format is timediff. If True rich renderable will be color formatted based on # of months remaining.
                This is used to colorize expiration dates.  Within 6 months = Orange, within 3 months = red.  Defaults to False.
        """
        self.original = timestamp
        self.ts = self.normalize_epoch(timestamp)
        self.tz = tz
        self.pad_hour = pad_hour
        self.round_to_minute = round_to_minute
        self.format_expiration = format_expiration
        self.pretty = getattr(self, format.replace("-", "_"))

    def __str__(self):
        return self.pretty

    def __rich__(self):
        return self.pretty if not self.format_expiration else self.expiration

    def __bool__(self):
        return bool(self.ts and self.ts > 0)

    def __len__(self) -> int:
        return len(self.ts)

    def __lt__(self, other) -> bool:
        return True if self.ts is None else bool(self.ts < other)

    def __le__(self, other) -> bool:
        return False if self.ts is None else bool(self.ts <= other)

    def __eq__(self, other) -> bool:
        return False if self.ts is None else bool(self.ts == other)

    def __gt__(self, other) -> bool:
        return False if self.ts is None else bool(self.ts > other)

    def __ge__(self, other) -> bool:
        return False if self.ts is None else bool(self.ts >= other)

    def normalize_epoch(self, timestamp: int | float | str) -> int | float:
        """Normalize timestamp/epoch or iso date str to seconds.

        Args:
            timestamp (int | float | str): timestamp/epoch is seconds or milliseconds
                or iso date string

        Returns:
            int | float: timestamp/epoch in seconds
        """
        if isinstance(timestamp, str):
            if not timestamp.isdigit():
                return pendulum.parse(timestamp).timestamp()
            else:
                timestamp = int(timestamp)

        if str(timestamp).isdigit() and len(str(int(timestamp))) > 10:
            timestamp = timestamp / 1000

        return timestamp if not str(timestamp).endswith(".0") else int(timestamp)

    @property
    def expiration(self) -> str:
        """Render date/time in format provided during instantiation colorized to indicate how near expiration the date is.

        return is colorized:
          - orange: if expiration within 6 months
          - red: if expiration within 3 months

        Returns:
            str: Potentially colorized date str.
        """
        if pendulum.from_timestamp(self.ts).subtract(months=3).int_timestamp < pendulum.now(tz="UTC").int_timestamp:
            return f"[red]{self.pretty}[/]"  # TODO need to sort out how to have line 180 in render.py take a rich renderable
                                             # return f"\x1b[31m{self.pretty}\x1b[0m"  # Doing it this way messes up column spacing.
        elif pendulum.from_timestamp(self.ts).subtract(months=6).int_timestamp < pendulum.now(tz="UTC").int_timestamp:
            return f"[dark_orange3]{self.pretty}[/]"
        else:
            return self.pretty

    @property
    def day_datetime(self) -> str:
        """Render date in day_datetime format

        Returns:
            str: Date as string in format: 'Thu, May 7, 2020 3:49 AM'
        """
        return pendulum.from_timestamp(self.ts, tz=self.tz).to_day_datetime_string()

    @property
    def durwords(self) -> str:
        """Render elapsed time in seconds as duration string.

        Returns:
            str: Duration as string in format: '2 weeks 1 day 1 hour 21 minutes 2 seconds'
        """
        return pendulum.duration(seconds=int(self.ts)).in_words()

    @property
    def durwords_short(self) -> str:
        """Render timestamp as duration in short format.

        Strips off seconds and rounds to minute if Class instantiated with round_to_minutes=True

        Returns:
            str: Duration as string in format: '2w 1d 1h 21m 2s' (without seconds if round_to_minute = True)
        """
        if not self.ts:
            return ""

        _words = pendulum.duration(seconds=int(self.ts)).in_words()
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
        """Render duration words representing the difference between self.ts and now.

        Returns:
            str: The difference between now and the timestamp in the format: '47 minutes ago'.
        """
        return "" if self.ts is None else pendulum.from_timestamp(self.ts, tz=self.tz).diff_for_humans()

    @property
    def timediff_past(self) -> str:
        """Render past words representing the difference between self.ts and now.

        Returns:
            str: The difference between now and the timestamp in the format: 'past 47 minutes'.
        """
        return "" if self.ts is None else f'past {self.timediff.removesuffix(" ago")}'

    @property
    def mdyt(self) -> str:
        """Render date as human string like Mon day, year time AM/PM.

        Hour is zero-padded if Class is instantiated with pad_hour=True

        Returns:
            str: Date as string in format: 'May 7, 2020 3:49:24 AM' or 'May 7, 2020 03:49:24 AM' if pad_hour=True
        """
        return pendulum.from_timestamp(self.ts, tz=self.tz).format(f"MMM DD, YYYY {'h' if not self.pad_hour else 'hh'}:mm:ss A")

    @property
    def log(self) -> str:
        """Render date as human string in log format.

        Hour is zero-padded if Class is instantiated with pad_hour=True

        Returns:
            str: Date as string in format: 'Jan 08 7:59:00 PM' or 'Jan 08 07:59:00 PM' if pad_hour=True
        """
        if isinstance(self.ts, str):
            try:
                self.ts = float(self.ts)
            except TypeError:
                return self.ts

        return pendulum.from_timestamp(self.ts, tz=self.tz).format(f"MMM DD {'h' if not self.pad_hour else 'hh'}:mm:ss A")

    @property
    def date_string(self) -> str:
        """Render date as human string like 'Dec 10, 2019'.

        Returns:
            str: Date as string in format: 'Dec 10, 2019'
        """
        return pendulum.from_timestamp(self.ts, tz=self.tz).to_formatted_date_string()


class Encoder(JSONEncoder):
    """A Custom JSON Encoder to handle custom DateTime object (and Path) during JSON serialization.
    """
    def default(self, obj):
        return obj if not isinstance(obj, DateTime) and not isinstance(obj, Path) else str(obj)

class ShowInterfaceFilters:
    def __init__(self, up: bool = False, down: bool = False, slow: bool = False, fast: bool = False):
        self.up = up
        self.down = down
        self.slow = slow
        self.fast = fast
        self._error = []
        self._title_sfx = []

    def __bool__(self) -> bool:
        """Returns a bool indicating if *any* filters are True
        """
        return any([self.up, self.down, self.slow, self.fast])

    @property
    def error(self) -> str:
        return ",".join(self._error)

    @property
    def title_sfx(self) -> str:
        if self.slow:
            return "[bright_red]Slow[/] "
        elif self.fast:
            return "[bright_magenta]Fast[/] "
        elif self.up:
            return "[bright_green]Up[/] "
        elif self.down:
            return "[bright_red]Down[/] "
        else:
            return ""

    @property
    def ok(self) -> bool:
        """Returns a bool indicating if filters are valid
        """
        valid=True
        if all([self.up, self.down]):
            valid = False
            self._error += ["[cyan]--up[/] & [cyan]--down[/]"]
            self.up = False
            self.down = False

        if all([self.slow, self.fast]):
            valid = False
            self._error += ["[cyan]--fast[/]|[cyan]-f[/] & [cyan]--slow[/]|[cyan]-s[/]"]
            self.slow = False
            self.fast = False

        if any([self.slow, self.fast]) and self.down:
            valid = False
            self._error += ["[cyan]--down[/] & [cyan]--fast[/]|[cyan]-f[/] or [cyan]--slow[/]|[cyan]-s[/]"]

        return valid

