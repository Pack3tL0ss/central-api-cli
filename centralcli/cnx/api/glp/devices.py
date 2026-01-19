from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli.typedefs import UNSET

from .... import utils
from ....client import BatchRequest, Session

if TYPE_CHECKING:
    from ....response import Response

class GreenLakeDevicesAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_glp_devices(
            self,
            sort_by: str | list[str] = None,
            reverse: bool = None,
            archived: bool = None,
            offset: int = 0,
            limit: int = 2000
        ) -> Response:
        """Retrieve a list of devices managed in a workspace

        Args:
            offset (int, optional): Specifies the zero-based resource offset to start the response from. Defaults to 0.
            limit (int, optional): Specifies the number of results to be returned. Max 2000, Defaults to 2000.

        Returns:
            Response: centralcli.response.Response object
        """
        url = "/devices/v1/devices"

        params = {
            "offset": offset,
            "limit": limit
        }
        bool_filters = {
            "archived": archived,
        }

        filter_str = " and ".join([f"{k} eq {str(v).lower()}" for k, v in bool_filters.items() if v is not None])
        if filter_str:
            params["filter"] = filter_str

        if sort_by:
            sort_by = ",".join(utils.listify(sort_by))
            if reverse:
                sort_by = f"{sort_by} desc"
            params["sort"] = sort_by

        return await self.session.get(url, params=params)


    async def update_devices(
            self,
            device_ids: str | list[str],
            subscription_ids: list[str] | str | None = UNSET,
            tags: dict[str, str] | None = None,
            application_id: str | None = UNSET,
            archive: bool = None,
        ) -> list[Response]:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)

        # Same endpoint but operations need to be done via separate calls.
        payloads = []
        if subscription_ids is not UNSET:
            payloads += [{"subscription": [] if subscription_ids is None else [{"id": sub} for sub in utils.listify(subscription_ids)]}]
        if tags:
            payloads += [{"tags": tags}]
        if archive is not None:
            payloads += [{"archived": archive}]
        if application_id is not UNSET:
            payloads += {"application": {"id": application_id}}

        batch_reqs = []
        for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
            query_str = "&".join([f"id={dev}" for dev in chunk])
            for payload in payloads:
                _url = f"{url}?{query_str}"
                batch_reqs += [BatchRequest(self.session.patch, _url, json_data=payload, headers=header)]

        return await self.session._batch_request(batch_reqs)

    async def remove_devices(self, device_ids: list[str] | str, remove_app: bool = True) -> list[Response]:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)

        # Subscription and other updates can't be in same API call.
        if remove_app:  # removing app association also frees up subs
            payload = {"application": {"id": None}, "region": None}
        else:
            payload = {"subscription": []}

        batch_reqs = []
        for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
            query_str = "&".join([f"id={dev}" for dev in chunk])
            url = f"{url}?{query_str}"
            batch_reqs += [BatchRequest(self.session.patch, url, json_data=payload, headers=header)]

        return await self.session._batch_request(batch_reqs)




