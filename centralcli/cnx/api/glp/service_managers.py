from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli.typedefs import UNSET

if TYPE_CHECKING:
    from centralcli.client import Session
    from centralcli.response import Response


class GreenLakeServiceManagerAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_service_managers(
        self,
        service_id: str = None,
        provisioned: bool = UNSET,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:
        url = f"/service-catalog/v1/service-managers{'' if not service_id else '/'}{service_id or ''}"
        query = []
        if provisioned is not UNSET:
            status_word = "PROVISIONED" if provisioned else "UNPROVISIONED"
            query += [f"status eq '{status_word}'"]
        query = None if not query else " and ".join(query)


        params = {
            "filter": query,
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_service_managers_by_region(
        self,
        msp_supported: bool = None,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:
        url = "/service-catalog/v1/per-region-service-managers"
        query = []
        if msp_supported is not None:
            query += [f"mspsupported eq {str(msp_supported).lower()}"]  # Not tested
        query = None if not query else " and ".join(query)


        params = {
            "filter": query,
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_service_manager_provisions(
        self,
        sm_id: str = None,
        provisioned: bool = UNSET,
        region: str = None,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:  # pragma: no cover returns 403 The token wasnt issued to perform operation
        url = "/service-catalog/v1/service-manager-provisions"
        query = []
        if sm_id is not None:
            query += [f"serviceManagerId eq {str(sm_id).lower()}"]  # Not tested
        if region:
            query += [f"region eq {str(region).lower()}"]  # Not tested
        if provisioned is not UNSET:
            status_word = "PROVISIONED" if provisioned else "UNPROVISIONED"
            query += [f"status eq '{status_word}'"]

        query = None if not query else " and ".join(query)


        params = {
            "filter": query,
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_my_services(
        self,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:  # pragma: no cover returns 403 The token wasnt issued to perform operation
        url = "https://global.api.greenlake.hpe.com/service-catalog/v1beta1/my-services"
        params = {
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_service_offers(
        self,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:  # pragma: no cover returns 403 The token wasnt issued to perform operation
        url = "https://global.api.greenlake.hpe.com/service-catalog/v1beta1/service-offers"
        params = {
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_service_offer_regions(
        self,
        offset: int = 0,
        limit: int = 2000
    ) -> Response:  # pragma: no cover returns 403 The token wasnt issued to perform operation
        url = "https://global.api.greenlake.hpe.com/service-catalog/v1beta1/service-offer-regions"
        params = {
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)
