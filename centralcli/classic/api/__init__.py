from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from ... import Session, config
from .aiops import AiOpsAPI
from .central import CentralAPI
from .cloudauth import CloudAuthAPI
from .configuration import ConfigAPI
from .device_management import DeviceManagementAPI
from .firmware import FirmwareAPI
from .guest import GuestAPI
from .kms import KmsAPI
from .monitoring import MonitoringAPI
from .other import OtherAPI
from .platform import PlatformAPI
from .rapids import RapidsAPI
from .routing import RoutingAPI
from .topology import TopologyAPI
from .troubleshooting import TroubleShootingAPI

if TYPE_CHECKING:
    from aiohttp.client import ClientSession

    from ...typedefs import StrOrURL

class ClassicAPI:
    def __init__(self, base_url: StrOrURL = None, *, aio_session: ClientSession = None, silent: bool = True):
        self._session = Session(base_url=base_url or config.classic.base_url, aio_session=aio_session, silent=silent)

    @property
    def session(self) -> Session:
        return self._session

    @session.setter
    def session(self, session: Session) -> None:
        self._session = session

    @cached_property
    def central(self) -> CentralAPI:
        return CentralAPI(self.session)

    @cached_property
    def cloudauth(self) -> CloudAuthAPI:
        return CloudAuthAPI(self.session)

    @cached_property
    def configuration(self) -> ConfigAPI:
        return ConfigAPI(self.session)

    @cached_property
    def device_management(self) -> DeviceManagementAPI:
        return DeviceManagementAPI(self.session)

    @cached_property
    def firmware(self) -> FirmwareAPI:
        return FirmwareAPI(self.session)

    @cached_property
    def guest(self) -> GuestAPI:
        return GuestAPI(self.session)

    @cached_property
    def monitoring(self) -> MonitoringAPI:
        return MonitoringAPI(self.session)

    @cached_property
    def other(self) -> OtherAPI:
        return OtherAPI(self.session)

    @cached_property
    def platform(self) -> PlatformAPI:
        return PlatformAPI(self.session)

    @cached_property
    def rapids(self) -> RapidsAPI:
        return RapidsAPI(self.session)

    @cached_property
    def routing(self) -> RoutingAPI:
        return RoutingAPI(self.session)

    @cached_property
    def topo(self) -> TopologyAPI:
        return TopologyAPI(self.session)

    @cached_property
    def tshooting(self) -> TroubleShootingAPI:
        return TroubleShootingAPI(self.session)

    @cached_property
    def aiops(self) -> AiOpsAPI:
        return AiOpsAPI(self.session)

    @cached_property
    def kms(self) -> KmsAPI:
        return KmsAPI(self.session)

