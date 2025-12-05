from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from ... import log, utils
from ...client import BatchRequest
from centralcli.response import BatchResponse

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response

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
        funcs = {
            "interfering_aps": self.wids_get_interfering_aps,
            "neighbor_aps": self.wids_get_neighbor_aps,
            "suspect_aps": self.wids_get_suspect_aps,
            "rogue_aps": self.wids_get_rogue_aps,
        }

        batch_req = [
            br(f, **params) for f in funcs.values()
        ]

        batch_res = BatchResponse(await self.session._batch_request(batch_req))
        if not batch_res.passed:
            return batch_res.failed[-1]  # should only be 1 item given batch_request will abort if first call fails

        if batch_res.failed:
            for f in batch_res.failed:
                log.error(f"Partial Failure {f.method}:{f.url.path} returned {f.status} {f.error} [italic]see logs[/]", caption=True)

        resp = batch_res.last
        resp.raw["_counts"] = {}
        resp.raw["_exit_code"] = 0
        for key, res in zip(funcs.keys(), batch_res.responses):
            if res.ok:
                resp.raw["_counts"][key.rstrip("_aps")] = res.raw.get("total")
                resp.output = [*resp.output, *res.output]
            else:
                resp.raw["_exit_code"] = 1

        return resp