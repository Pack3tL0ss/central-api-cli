from __future__ import annotations

from ....client import Session
from .... import utils
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from centralcli import Response

class GlpDevicesApi:
    def __init__(self, session: Session):
        self.session = session

    async def get_glp_devices(self) -> Response:
        url = "/devices/v1/devices"

        return await self.session.get(url)

    async def assign_subscription_to_device(self, device_ids: list[str] | str, subscription_ids: list[str] | str) -> Response:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)
        subscription_ids = utils.listify(subscription_ids)
        # TODO MAX 25 DEVICES

        query_str = "&".join([f"id={serial}" for serial in device_ids])
        url = f"{url}?{query_str}"

        payload = {
            "subscription": [
                {
                "id": sub
                } for sub in subscription_ids
            ]
        }

        return await self.session.patch(url, json_data=payload, headers=header)


