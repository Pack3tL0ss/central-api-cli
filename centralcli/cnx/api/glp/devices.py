from __future__ import annotations

import asyncio
from time import sleep
from typing import TYPE_CHECKING, Optional, TypedDict

from centralcli import utils, log, render
from centralcli.client import BatchRequest, Session
from centralcli.typedefs import UNSET
from centralcli.cnx.models.cache import Inventory

if TYPE_CHECKING:
    from centralcli.cache import Cache
    from centralcli.response import Response


class GLPDevice(TypedDict):
    serial: str
    mac: Optional[str]
    subscription: Optional[str]
    tags: Optional[list[dict[str, str]]]

class GreenLakeDevicesAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_progresss_of_async_ops(self, responses: list[Response]) -> list[Response]:
        """Given a list of GLP API responses, fetch status of async operation.

        For all responses that pass with 202 the "Location" header is used to fetch the status of async operation in GLP.
        All non 202 responses are returned as is.

        Args:
            responses (list[Response]): list of Response objects.

        Returns:
            list[Response]: list of response objects.
        """
        async_status_urls = {idx: r.async_status_url for idx, r in enumerate(responses)}
        async_status_reqs = {idx: responses[idx] if not url else BatchRequest(self.session.get, url) for idx, url in async_status_urls.items()}
        resp_idx_list = [idx for idx, req in async_status_reqs.items() if isinstance(req, BatchRequest)]
        return_responses = {idx: r for idx, r in enumerate(responses) if not r.async_status_url}
        original_responses = {idx: res for idx, res in enumerate(responses)}

        batch_reqs = [async_status_reqs[idx] for idx in resp_idx_list]
        async_status_resp = {idx: res for idx, res in zip(resp_idx_list, await self.session._batch_request(batch_reqs))}
        retry_reqs = {}
        for _ in range(3):
            if _ > 0:
                resp_idx_list = list(retry_reqs.keys())
                async_status_resp = {idx: res for idx, res in zip(resp_idx_list, await self.session._batch_request(list(retry_reqs.values())))}

            retry_reqs = {}
            for idx, r in async_status_resp.items():
                if r.ok and r.get("status") == "RUNNING" and _ < 2:
                    retry_reqs[idx] = async_status_reqs[idx]
                else:
                    responses[idx].output["async operation response"] = r.summary
                    return_responses[idx] = responses[idx]
                    # r.output["original response"] = responses[idx].summary
                    # return_responses[idx] = r

            if not retry_reqs:
                return list({**original_responses, **return_responses}.values())
            else:
                with render.Spinner(f"Allowing more time for {len(retry_reqs)} Async operations to complete..."):
                    sleep(2)



    async def get_devices(
            self,
            serial_numbers: str | list[str] = None,
            assigned: bool = None,
            archived: bool = None,
            sort_by: str | list[str] = None,
            reverse: bool = None,
            offset: int = 0,
            limit: int = 2000
        ) -> Response:
        """Retrieve a list of devices managed in a workspace

        Args:
            serial_numbers (str | list[str], optional): Fetch results for a specific set of provided serial numbers. Defaults to None.
            assigned (bool, optional): Filter results, fetching only devices assigned to a service (Aruba Central) if True or only devices lacking an assignment if set to False. Defaults to None.
            archived (bool, optional): Filter results, fetching only archived if True or only unarchived if set to False. Defaults to None.
            sort_by: (str | list[str], optional): Field to sort by (ascending by default). Defaults to None.
            reverse: (bool, optional): Reverse sort order. Defaults to None.
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
        filter_str = ""
        if serial_numbers:
            if archived is not None:
                raise ValueError("Can only provide serial_numers or archived, not both")
            filter_str = " or ".join([f"serialNumber eq '{serial.upper()}'" for serial in utils.listify(serial_numbers)])
        else:
            filter_str = " and ".join([f"{k} eq {str(v).lower()}" for k, v in bool_filters.items() if v is not None])

        if assigned is not None:
            filter_str = filter_str and f"{filter_str} and"
            filter_str = f"{filter_str} assignedState {'eq' if assigned else 'ne'} 'ASSIGNED_TO_SERVICE'".lstrip()

        if filter_str:
            params["filter"] = filter_str

        if sort_by:
            sort_by = ",".join(utils.listify(sort_by))
            if reverse:
                sort_by = f"{sort_by} desc"
            params["sort"] = sort_by

        return await self.session.get(url, params=params)

    async def add_devices(
            self,
            devices: GLPDevice | list[GLPDevice],
            tags: dict[str, str] | None = None,
            location_id: str | None = None,
            application_id: str | None = UNSET,
            region: str | None = None,
            subscription_ids: list[str] | str | None = UNSET,
            cache: Cache = None,
        ) -> list[Response]:  # pragma: no cover  still use classic for now
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/json"}
        devices = devices if isinstance(devices, list) else [devices]
        payloads = [
            {
                "serialNumber": d["serial"],
                "macAddress": d.get("mac"),
                "deviceType": "NETWORK",
                "tags": {**(tags or {}), **(d.get("tags") or {})} or None,
            } for d in devices
        ]
        payloads = [utils.strip_none(p) for p in payloads]
        if location_id:
            payloads = [{**p, "location": {"id": location_id}} for p in payloads]

        batch_reqs = [BatchRequest(self.session.post, url, json_data=payload, headers=header) for payload in payloads]
        add_resp = await self.session._batch_request(batch_reqs)
        passed = [r for r in add_resp if r.ok]
        if not passed:
            return add_resp

        async_add_resp = await self.get_progresss_of_async_ops(add_resp)

        devs_by_sub = {}
        if not subscription_ids:
            devices = utils.normalize_device_sub_field(devices)
            subs = [d["subscription"] for d in devices if "subscription" in d]
            if len(set(subs)) == 1:
                subscription_ids = subs[0]
            elif subs:
                [utils.update_dict(devs_by_sub, d["subscription"], d) for d in devices if d.get("subscription")]

        if not application_id and not subscription_ids and not devs_by_sub:
            log.info("Devices have been added to [green]GreenLake[/], but no application_id/subscription provided to add function, they are not associated with Aruba Central.", caption=True, show=True, log=False)
            return async_add_resp

        serials = [d["serial"] for d in devices]
        inv_resp = await self.get_devices(serial_numbers=serials)
        if not inv_resp.ok or not inv_resp.output:
            sfx = inv_resp.error if not inv_resp.ok else "Device add failed."
            log.error(f"Unable to perform service (Aruba Central) assignment, Subscription Assignment and Cache update due to failure fetching device_ids. {sfx}", caption=True, log=True)
            return [*async_add_resp, inv_resp]

        if cache:  # We update cache here, as we need to do the call to fetch device_ids here to process the service assignment/subscriptions.
            try:
                cache_data = Inventory(**inv_resp.raw)
                _ = await cache.update_inv_db(cache_data.model_dump()["items"])
            except Exception as e:
                log.exception(f"Exception ({repr(e)}) during cache update after device addition", caption=True)

        new_devs_by_serial = {dev["serialNumber"]: dev for dev in inv_resp.output}
        if devs_by_sub:
            update_tasks = set()
            for sub in devs_by_sub:
                update_tasks.add(asyncio.create_task(self.update_devices([new_devs_by_serial[dev["serial"]]["id"] for dev in devs_by_sub[sub]], subscription_ids=sub, application_id=application_id, region=region)))
            update_responses = [r for r_list in asyncio.gather(*update_tasks) for r in r_list]
            return [*async_add_resp, *update_responses]

        device_ids = [new_devs_by_serial[s]["id"] for s in serials if s in new_devs_by_serial]
        missing = len(serials) - len(device_ids)
        if missing:
            log.error(f"{missing} of {len(serials)} failed to be added to GreenLake Inventory.  Processing aborted for these devies.")
        ret = [
            *async_add_resp,
            *await self.update_devices(device_ids, subscription_ids=subscription_ids, application_id=application_id, region=region)
        ]
        return ret

    async def update_devices(
            self,
            device_ids: str | list[str],
            subscription_ids: list[str] | str | None = UNSET,
            tags: dict[str, str] | None = None,
            application_id: str | None = UNSET,
            region: str | None = None,
            archive: bool = None,
        ) -> list[Response]:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)

        # Same endpoint but operations need to be done via separate calls.
        payloads = []
        app_payload = {}
        async_app_resp = []
        if application_id is not UNSET:
            if not region:
                raise ValueError("region is required when assigning application")
            app_payload = {"application": {"id": application_id}, "region": region}
        if subscription_ids is not UNSET:
            payloads += [{"subscription": [] if subscription_ids is None else [{"id": sub} for sub in utils.listify(subscription_ids)]}]
        if tags:
            payloads += [{"tags": tags}]
        if archive is not None:
            payloads += [{"archived": archive}]

        # We need to assign the devices to Aruba Central first or any sub calls can fail (race condition)
        if app_payload:
            app_reqs = []
            for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
                query_str = "&".join([f"id={dev}" for dev in chunk])
                _url = f"{url}?{query_str}"
                app_reqs += [BatchRequest(self.session.patch, _url, json_data=app_payload, headers=header)]
            app_resp = await self.session._batch_request(app_reqs)
            async_app_resp = await self.get_progresss_of_async_ops(app_resp)

        batch_reqs = []
        for chunk in utils.chunker(device_ids, 25):  # MAX 25 per call
            query_str = "&".join([f"id={dev}" for dev in chunk])
            _url = f"{url}?{query_str}"
            for payload in payloads:
                batch_reqs += [BatchRequest(self.session.patch, _url, json_data=payload, headers=header)]

        update_resp = await self.session._batch_request(batch_reqs)
        return [*async_app_resp, *await self.get_progresss_of_async_ops(update_resp)]

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

        del_resp = await self.session._batch_request(batch_reqs)
        return await(self.get_progresss_of_async_ops(del_resp))




