from __future__ import annotations

from typing import TYPE_CHECKING

from ... import Response

if TYPE_CHECKING:
    from ... import Session


class TopologyAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_site_vlans(self, site_id: int, search: str = None, offset: int = 0, limit: int = 100) -> Response:
        """Get vlan list of a site.

        Args:
            site_id (int): Site ID.
            search (str, optional): search.
            offset (int, optional): offset. Defaults to 0.
            limit (int, optional): limit Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/vlans/{site_id}"

        params = {"search": search, "offset": offset, "limit": limit}

        return await self.session.get(url, params=params)

    async def get_sdwan_dps_policy_compliance(self, time_frame: str = "last_week", order: str = "best") -> Response:
        url = "/sdwan-mon-api/external/noc/reports/wan/policy-compliance"
        params = {"period": time_frame, "result_order": order, "count": 250}
        return await self.session.get(url, params=params)

    async def get_topo_for_site(
        self,
        site_id: int,
    ) -> Response:
        """Get topology details of a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/{site_id}"

        return await self.session.get(url)

    async def get_ap_lldp_neighbor(self, serial: str) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{serial}"

        return await self.session.get(url)