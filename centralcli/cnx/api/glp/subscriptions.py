from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from centralcli.client import Session
    from centralcli.response import Response


class GreenLakeSubscriptionsAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_subscriptions(self, offset: int = 0, limit: int = 200) -> Response:
        url = "/subscriptions/v1/subscriptions"

        params = {
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)
