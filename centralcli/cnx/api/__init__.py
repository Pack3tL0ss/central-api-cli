from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING
from .glp.devices import GreenLakeDevicesAPI
from .glp.subscriptions import GreenLakeSubscriptionsAPI
from ...client import Session
from ... import config
from .central.monitoring import MonitoringAPI


if TYPE_CHECKING:
    from ...typedefs import StrOrURL
    from aiohttp.client import ClientSession

class GreenLakeAPI:
    def __init__(self, base_url: StrOrURL = None, aio_session: ClientSession = None, silent: bool = True):
        self._session = Session(base_url=base_url or config.glp.base_url, aio_session=aio_session, silent=silent, cnx=True)

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session

    @cached_property
    def devices(self) -> GreenLakeDevicesAPI:
        return GreenLakeDevicesAPI(self.session)

    @cached_property
    def subscriptions(self) -> GreenLakeSubscriptionsAPI:
        return GreenLakeSubscriptionsAPI(self.session)

class CentralAPI:
    def __init__(self, base_url: StrOrURL = None, *, aio_session: ClientSession = None, silent: bool = True):
        self._session = Session(base_url=base_url or config.cnx.base_url, aio_session=aio_session, silent=silent, cnx=True)

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session  # pragma: no cover  We don't use this currently

    @cached_property
    def monitoring(self) -> MonitoringAPI:
        return MonitoringAPI(self.session)




