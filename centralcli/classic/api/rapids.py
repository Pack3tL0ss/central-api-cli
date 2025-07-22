from __future__ import annotations

from ..client import Session
from ... import utils, log, Response, BatchRequest
from typing import List
from datetime import datetime


class RapidsAPI:
    def __init__(self, session: Session):
        self.session = session

    async def wids_get_rogue_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        swarm_id: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List Rogue APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            swarm_id (str, optional): Filter by Swarm ID
            from_time (int | float | datetime, optional): Start of timerange to collect data for.
                Default is now minus 3 hours
            to_time (int | float | datetime, optional): End of timerange to collect data for.
                Default is current time.
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = "/rapids/v1/rogue_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'swarm_id': swarm_id,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def wids_get_interfering_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        swarm_id: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List Interfering APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            swarm_id (str, optional): Filter by Swarm ID
            from_time (int | float | datetime, optional): Start of timerange to collect data for.
                Default is now minus 3 hours
            to_time (int | float | datetime, optional): End of timerange to collect data for.
                Default is current time.
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = "/rapids/v1/interfering_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'swarm_id': swarm_id,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def wids_get_suspect_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        swarm_id: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List suspect APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            swarm_id (str, optional): Filter by Swarm ID
            from_time (int | float | datetime, optional): Start of timerange to collect data for.
                Default is now minus 3 hours
            to_time (int | float | datetime, optional): End of timerange to collect data for.
                Default is current time.
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = "/rapids/v1/suspect_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'swarm_id': swarm_id,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def wids_get_neighbor_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        swarm_id: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List neighbor APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            swarm_id (str, optional): Filter by Swarm ID
            from_time (int | float | datetime, optional): Start of timerange to collect data for.
                Default is now minus 3 hours
            to_time (int | float | datetime, optional): End of timerange to collect data for.
                Default is current time.
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = "/rapids/v1/neighbor_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'swarm_id': swarm_id,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def wids_get_all(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        swarm_id: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List all wids classifications.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            swarm_id (str, optional): Filter by Swarm ID
            from_time (int | float | datetime, optional): Start of timerange to collect data for.
                Default is now minus 3 hours
            to_time (int | float | datetime, optional): End of timerange to collect data for.
                Default is current time.
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        params = {
            'group': group,
            'label': label,
            'site': site,
            'swarm_id': swarm_id,
            'from_time': from_time,
            'to_time': to_time,
            'offset': offset,
            'limit': limit
        }

        br = BatchRequest
        funcs = [
            self.wids_get_interfering_aps,
            self.wids_get_neighbor_aps,
            self.wids_get_suspect_aps,
            self.wids_get_rogue_aps,
        ]

        batch_req = [
            br(f, **params) for f in funcs
        ]

        # TODO send to CombinedResponse
        batch_res = await self.session._batch_request(batch_req)
        resp = batch_res[-1]
        ok_res = [idx for idx, res in enumerate(batch_res) if res.ok]
        if not len(ok_res) == len(funcs):
            failed = [x for x in range(0, len(funcs)) if x not in ok_res]
            for f in failed:
                if f in range(0, len(batch_res)):
                    log.error(f"{batch_res[f].method} {batch_res[f].url.path} Returned Error Status {batch_res[f].status}. {batch_res[f].output or batch_res[f].error}", show=True)
        raw_keys = ["interfering_aps", "neighbor_aps", "suspect_aps"]
        resp.raw = {"rogue_aps": resp.raw.get("rogue_aps", []), "_counts": {"rogues": resp.raw.get("total")}}
        for idx, key in enumerate(raw_keys):
            if idx in ok_res:
                resp.raw = {**resp.raw, **{key: batch_res[idx].raw.get(key, [])}}
                resp.raw["_counts"][key.rstrip("_aps")] = batch_res[idx].raw.get("total")
                resp.output = [*resp.output, *batch_res[idx].output]

        return resp