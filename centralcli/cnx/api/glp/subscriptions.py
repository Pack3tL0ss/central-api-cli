from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli.constants import GenericDevTypes, LicenseTypes

if TYPE_CHECKING:
    from centralcli.client import Session
    from centralcli.response import Response


class GreenLakeSubscriptionsAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_subscriptions(
        self,
        sub_type: LicenseTypes = None,
        dev_type: GenericDevTypes = None,
        offset: int = 0,
        limit: int = 200
    ) -> Response:
        url = "/subscriptions/v1/subscriptions"
        query = []
        if dev_type:
            query += [f"subscriptionType eq 'CENTRAL_{dev_type.value.upper()}'"]
        if sub_type:
            query += [f'tier eq \'{sub_type.value.replace("-", "_").upper()}\'']
        query = None if not query else " and ".join(query)


        params = {
            "filter": query,
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)
