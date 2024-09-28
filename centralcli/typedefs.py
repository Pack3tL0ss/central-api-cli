from __future__ import annotations
from yarl import URL

from typing import Literal



StrOrURL = str | URL
Method = Literal['GET', 'POST', 'PUT', 'DELETE']