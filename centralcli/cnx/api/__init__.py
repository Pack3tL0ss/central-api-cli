from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING
from .glp.devices import GreenLakeDevicesAPI
from .glp.subscriptions import GreenLakeSubscriptionsAPI
from .glp.service_managers import GreenLakeServiceManagerAPI
from ...client import Session
from ... import config as cfg
from ...config import Config
from .central.monitoring import MonitoringAPI


if TYPE_CHECKING:
    from ...typedefs import StrOrURL

class GreenLakeAPI:
    _by_workspace: dict[str, GreenLakeAPI] = {}

    def __init__(self, config: Config = None, *, base_url: StrOrURL = None, silent: bool = True):
        self.config = config or cfg
        self._session = Session(config=self.config, base_url=base_url or self.config.glp.base_url, silent=silent, cnx=True)

    def __new__(cls, config: Config = None, **kwargs):
        workspace = config and config.workspace or cfg.workspace
        if cls._by_workspace.get(workspace) is None:
            cls._by_workspace[workspace] = super().__new__(cls)

        return cls._by_workspace[workspace]

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session  # pragma: no cover  We don't use this currently

    @cached_property
    def devices(self) -> GreenLakeDevicesAPI:
        return GreenLakeDevicesAPI(self.session)

    @cached_property
    def subscriptions(self) -> GreenLakeSubscriptionsAPI:
        return GreenLakeSubscriptionsAPI(self.session)

    @cached_property
    def service_managers(self) -> GreenLakeServiceManagerAPI:
        return GreenLakeServiceManagerAPI(self.session)

class CentralAPI:
    _by_workspace: dict[str, CentralAPI] = {}

    def __init__(self, config: Config = None, *, base_url: StrOrURL = None, silent: bool = True):
        self.config = config or cfg
        self._session = Session(config=self.config, base_url=base_url or self.config.cnx.base_url, silent=silent, cnx=True)

    def __new__(cls, config: Config = None, **kwargs):
        workspace = config and config.workspace or cfg.workspace
        if cls._by_workspace.get(workspace) is None:
            cls._by_workspace[workspace] = super().__new__(cls)

        return cls._by_workspace[workspace]

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session  # pragma: no cover  We don't use this currently

    @cached_property
    def monitoring(self) -> MonitoringAPI:
        return MonitoringAPI(self.session)




