from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli import utils
from centralcli.client import Session
from centralcli.constants import DeviceStatusFilter, APDeployment


if TYPE_CHECKING:
    from centralcli.response import Response


class MonitoringAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_aps(
            self,
            site_id: int | None = None,
            model: str | None = None,
            status: DeviceStatusFilter | None = None,
            deployment: APDeployment | None = None,
            limit: int = 100,
            next: int | None = 1
        ) -> Response:
        url = "/network-monitoring/v1alpha1/aps"
        filters = {
            "siteId": site_id,
            "model": model,
            "status": status if status is None or not hasattr(status, "value") else status.value,
            "deployment": deployment if deployment is None or not hasattr(deployment, "value") else deployment.value,
        }
        filters = utils.strip_none(filters)

        params = {
            "filter": " and ".join(f"{k} eq '{v}'" for k, v in filters.items()) or None,  # TODO need to test if Enum works without sending .value
            "limit": limit,
            "next": next
        }

        return await self.session.get(url, params=params)




