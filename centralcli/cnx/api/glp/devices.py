from __future__ import annotations

from typing import TYPE_CHECKING

from .... import utils
from ....client import BatchRequest, Session

if TYPE_CHECKING:
    from ....response import Response

class GreenLakeDevicesAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_glp_devices(self) -> Response:
        url = "/devices/v1/devices"

        return await self.session.get(url)

    async def assign_subscription_to_devices(self, device_ids: list[str] | str, subscription_ids: list[str] | str) -> Response:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)
        subscription_ids = utils.listify(subscription_ids)

        payload = {
            "subscription": [
                {
                "id": sub
                } for sub in subscription_ids
            ]
        }

        batch_reqs = []
        for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
            # API-FLAW This is a horrible design. ?id=...&id=...&id=...  Should just be devices=<array>
            query_str = "&".join([f"id={dev}" for dev in chunk])
            url = f"{url}?{query_str}"
            batch_reqs += [BatchRequest(self.session.patch, url, json_data=payload, headers=header)]

        return await self.session._batch_request(batch_reqs)


    async def remove_devices(self, device_ids: list[str] | str, remove_app: bool = True) -> Response:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)

        payload = {
            "subscription": []
        }
        if remove_app:
            payload["application"] = {"id": None}

        batch_reqs = []
        for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
            query_str = "&".join([f"id={dev}" for dev in chunk])
            url = f"{url}?{query_str}"
            batch_reqs += [BatchRequest(self.session.patch, url, json_data=payload, headers=header)]

        return await self.session._batch_request(batch_reqs)




