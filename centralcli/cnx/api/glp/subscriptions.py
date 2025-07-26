from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli.response import Session

if TYPE_CHECKING:
    from centralcli import Response


class GlpSubscriptionsApi:
    def __init__(self, session: Session):
        self.session = session

    async def get_subscriptions(self) -> Response:
        url = "/subscriptions/v1/subscriptions"

        return await self.session.get(url)
