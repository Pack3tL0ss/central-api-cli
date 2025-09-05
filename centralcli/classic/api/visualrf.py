from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response


class VisualRFAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_all_campuses(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """ Get list of all campuses.

        Args:
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/campus"

        return await self.session.get(url)

    async def get_buildings_for_campus(
        self,
        campus_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """ Get a specific campus and its buildings.

        Args:
            campus_id (str):  Provide campus_id returned by /visualrf_api/v1/campus api. Example:
                /visualrf_api/v1/campus/201610193176__1b99400c-f5bd-4a17-9a1c-87da89941381
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/campus/{campus_id}"

        return await self.session.get(url)

    async def get_floors_for_building(
        self,
        building_id: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get a specific building and its floors.

        Args:
            building_id (str): Provide building_id returned by /visualrf_api/v1/campus/{campus_id}
                api. Example:
                /visualrf_api/v1/building/201610193176__f2267635-d1b5-4e33-be9b-2bf7dbd6f885
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/building/{building_id}"

        return await self.session.get(url)

    async def get_floor_details(
        self,
        floor_id: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get details of a specific floor.

        Same as response for get_floors_for_building, for a single floor.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}"

        return await self.session.get(url)

    async def get_aps_for_floor(
        self,
        floor_id: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get a specific floor and location of all its access points.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/access_point_location"

        return await self.session.get(url)

    async def get_ap_location(
        self,
        ap_id: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get location of a specific access point.

        ap_id is not the serial number.  Use get_aps_for_floor to retrieve id.

        Args:
            ap_id (str): Provide ap_id returned by
                /visualrf_api/v1/floor/{floor_id}/access_point_location api. Example:
                /visualrf_api/v1/access_point_location/201610193176__B4:5D:50:C5:DA:5A
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/access_point_location/{ap_id}"

        return await self.session.get(url)

    async def get_client_location(
        self,
        macaddr: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get location of a specific client.

        Args:
            macaddr (str): Provide a macaddr returned by
                /visualrf_api/v1/floor/{floor_id}/*_location api. Example:
                /visualrf_api/v1/client_location/ac:37:43:a9:ec:10
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/client_location/{macaddr}"

        params = {
            'offset': offset,
            'limit': limit,
            'units': units
        }

        return await self.session.get(url, params=params)

    async def get_clients_for_floor(
        self,
        floor_id: str,
        offset: int = 0,
        limit: int = 100,
        units: str = 'FEET',
    ) -> Response:
        """Get a specific floor and location of all its clients.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 100 Defaults to 100 (max).
            units (str, optional): Valid Values: 'METERS', 'FEET'. Defaults to 'FEET'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/client_location"

        return await self.session.get(url)