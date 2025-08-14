from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ... import utils

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response


class OtherAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_wlan_cluster_by_group(
        self,
        group_name: str,
        ssid: str
    ) -> Response:
        """Retrieve Cluster mapping for given group/SSID.

        Args:
            group_name (str): The name of the group.
            ssid (str): Wlan ssid name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/GROUP/{group_name}/config/ssid_cluster/{ssid}/WIRELESS_PROFILE/"

        return await self.session.get(url)

    async def get_audit_event_logs(
        self,
        log_id: str = None,
        group_name: str = None,
        device_id: str = None,
        classification: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100,
        count: int = None,
    ) -> Response:
        """Get all audit events for all groups.

        This API returns the first 10,000 results only.

        Args:
            log_id (str, optional): The id of the audit event log to return details for. Defaults to None.
            group_name (str, optional): Filter audit events by Group Name
            device_id (str, optional): Filter audit events by Target / Device ID. Device ID for AP
                is VC Name and Serial Number for Switches
            classification (str, optional): Filter audit events by classification
            from_time (int | float | datetime, optional): Start of Time Range to filter audit logs by.
            to_time (int | float | datetime, optional): End of Time Range to filter audit logs by.
                Defaults to now.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination Defaults to 0.
            limit (int, optional): Maximum number of audit events to be returned Defaults to 100. Max 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/auditlogs/v1/events" if not log_id else f"/auditlogs/v1/event_details/{log_id}"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'group_name': group_name,
            'device_id': device_id,
            'classification': classification,
            'start_time': from_time,
            'end_time': to_time,
            'offset': offset,
            "limit": limit if not count or limit < count else count,
        }

        return await self.session.get(url, params={} if log_id else params, count=count)



    async def get_branch_health(
        self,
        name: str = None,
        # column: int = None,  # API-FLAW schema says it takes an int, but with int or string did not seem to impact sort
        reverse: bool = False,
        # filters: dict = None,  # Needs testing
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        r"""Get data for all sites.

        Args:
            name (str, optional): site / label name or part of its name
            reverse (bool, optional): Sort in reverse order (sort is by device count):
                Valid Values: asc, desc

            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/branchhealth/v1/site"

        params = {
            "name": name,
            "order": "asc" if not reverse else "desc",
            # **filters,
            "offset": offset,
            "limit": limit,
        }

        return await self.session.get(url, params=params)
