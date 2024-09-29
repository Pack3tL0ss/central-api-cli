from __future__ import annotations
from yarl import URL

from typing import Literal, List, Dict



StrOrURL = str | URL
Method = Literal['GET', 'POST', 'PUT', 'DELETE']
SiteData = List[Dict[str, str | int | float]] | Dict[str, str | int | float]