# pragma: exclude file  Need to exclude for now as all routing endpoints return a 404 (tested on internal and us-west4)
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response


class RoutingAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_device_ip_routes(
        self,
        serial: str,
        api: str = "V1",
        marker: str = None,
        limit: int = 100
    ) -> Response:
        """Get routes for a device.

        Args:
            serial (str): Device serial number
            api (str, optional): API version (V0|V1), Defaults to V1.
            marker (str, optional): Pagination offset.
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/route"

        params = {
            'device': serial,
            'api': api,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_ospf_area(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Area Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/area"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_ospf_interface(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Interface Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_ospf_neighbor(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF neighbor Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/neighbor"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_ospf_database(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Link State Database Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/database"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_overlay_connection(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """Get information about overlay control connection.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def reset_overlay_connection(
        self,
        device: str,
    ) -> Response:
        """Reset overlay control connection.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection/reset"

        params = {
            'device': device
        }

        return await self.session.put(url, params=params)

    async def get_overlay_routes_learned(
        self,
        device: str,
        *,
        best: bool = False,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of learned routes from overlay.

        Args:
            device (str): Device serial number
            best (bool): Return only best / preferred routes
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/learned"
        if best:
            url = f'{url}/best'

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_overlay_routes_advertised(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of advertised routes to overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/advertised"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_overlay_interfaces(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of overlay interfaces (tunnels).

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.session.get(url, params=params)