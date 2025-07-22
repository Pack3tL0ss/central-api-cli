from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING
from .glp.devices import GlpDevicesApi
from .glp.subscriptions import GlpSubscriptionsApi


if TYPE_CHECKING:
    from ...classic.client import Session

class GlpApi:
    def __init__(self, session: Session):
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session

    @cached_property
    def devices(self) -> GlpDevicesApi:
        return GlpDevicesApi(self.session)

    @cached_property
    def subscriptions(self) -> GlpSubscriptionsApi:
        return GlpSubscriptionsApi(self.session)



