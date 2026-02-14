from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli import utils
from centralcli.client import Session
from centralcli.constants import DeviceStatusFilter, APDeployment, CNXDevTypes


if TYPE_CHECKING:
    from centralcli.response import Response


class MonitoringAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_devices(
            self,
            serial: str = None,
            name: str = None,
            dev_type: CNXDevTypes = None,
            site: int | str | None = None,
            model: str | None = None,
            version: str = None,
            cluster: str = None,
            status: DeviceStatusFilter | None = None,
            deployment: APDeployment | None = None,
            fuzzy: bool = False,
            limit: int = 1000,
            next: int | None = 1
        ) -> Response:
        url = "/network-monitoring/v1/devices"
        _dev_type = dev_type if not hasattr(dev_type, "value") else dev_type.value
        filters = {
            "serialNumber": serial,
            "deviceName": name,
            "deviceType": _dev_type,
            "model": model,
            "status": status if status is None or not hasattr(status, "value") else status.value,
            "deployment": deployment if deployment is None or not hasattr(deployment, "value") else deployment.value,
            "firmwareVersion": version,
            "clusterName": cluster,
        }
        if site:
            filters = {"siteId" if str(site).isdigit() else "siteName": site, **filters}
        filters = utils.strip_none(filters)

        operator = "eq" if not fuzzy else "in"
        params = {
            "filter": " and ".join(f"{k} {operator} '{v}'" for k, v in filters.items()) or None,  # TODO need to test if Enum works without sending .value
            "limit": limit,
            "next": next
        }

        return await self.session.get(url, params=params)

    async def get_aps(
            self,
            serial: str = None,
            name: str = None,
            dev_type: CNXDevTypes = None,
            site: int | str | None = None,
            model: str | None = None,
            version: str = None,
            cluster: str = None,
            status: DeviceStatusFilter | None = None,
            deployment: APDeployment | None = None,
            fuzzy: bool = False,
            limit: int = 1000,
            next: int | None = 1
        ) -> Response:
        url = "/network-monitoring/v1/aps"
        _dev_type = dev_type if not hasattr(dev_type, "value") else dev_type.value
        filters = {
            "serialNumber": serial,
            "deviceName": name,
            "deviceType": _dev_type,
            "model": model,
            "status": status if status is None or not hasattr(status, "value") else status.value,
            "deployment": deployment if deployment is None or not hasattr(deployment, "value") else deployment.value,
            "firmwareVersion": version,
            "clusterName": cluster,
        }
        if site:
            filters = {"siteId" if str(site).isdigit() else "siteName": site, **filters}
        filters = utils.strip_none(filters)

        operator = "eq" if not fuzzy else "in"
        params = {
            "filter": " and ".join(f"{k} {operator} '{v}'" for k, v in filters.items()) or None,  # TODO need to test if Enum works without sending .value
            "limit": limit,
            "next": next
        }

        return await self.session.get(url, params=params)
