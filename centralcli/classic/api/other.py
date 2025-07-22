from __future__ import annotations

from ..client import Session
from ... import Response, utils, constants
from datetime import datetime, timezone
from typing import Literal


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

    # // -- Not used by commands yet.  undocumented kms api -- //
    async def kms_get_synced_aps(self, mac: str) -> Response:
        url = f"/keymgmt/v1/syncedaplist/{mac}"
        return await self.session.get(url)

    async def kms_get_client_record(self, mac: str) -> Response:
        url = f"/keymgmt/v1/keycache/{mac}"
        return await self.session.get(url)

    async def kms_get_hash(self) -> Response:
        url = "/keymgmt/v1/keyhash"
        return await self.session.get(url)

    async def kms_get_ap_state(self, serial: str) -> Response:
        url = f"/keymgmt/v1/Stats/ap/{serial}"
        return await self.session.get(url)

    # Bad endpoint URL 404
    async def kms_get_health(self) -> Response:
        url = "/keymgmt/v1/health"
        return await self.session.get(url)

    async def get_aiops_insights(
        self,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        *,
        site_id: int = None,
        client_mac: str = None,
        serial: str = None,
        device_type: Literal["ap", "gw", "cx", "sw", "switch"] = None
    ) -> Response:
        """List AI Insights.

        returns global insights unless site_id, serial (and dev_type), or client_mac is provided

        Args:
            from_time (int | float | datetime, optional): Start of Time Range to collect insights for.
            to_time (int | float | datetime, optional): End of Time Range to collect insights for.
                Defaults to now.
            site_id (int, optional): Site ID. Return insights for as specific site. Defaults to None
            client_mac (str, optional): Client Mac. Return insights for as specific client. Defaults to None
            serial (str, optional): AP Serial. Return insights for as specific device (device_type is required). Defaults to None
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): required if serial number is provided.  Valid Values: ap|gw|cx|sw|switch.
                Defaults to None

        Returns:
            Response: CentralAPI Response object
        """
        from_time = from_time or datetime.fromtimestamp(datetime.now(tz=timezone.utc).timestamp() - 10800) # Now - 3 hours (UTC)
        from_time, to_time = utils.parse_time_options(from_time, to_time, in_milliseconds=True)
        if serial:
            if not device_type:
                raise ValueError("device_type must be provided if serial is provided")
            device_type = constants.lib_to_api(device_type, "aiops")
        if len([param for param in [site_id, client_mac, serial] if param is not None]) > 1:
            raise ValueError("Too many filtering arguments provided.  Only one of site_id, client_mac, or serial is expected.")

        base_url = "/aiops/v2/insights"
        if site_id is not None:
            url = f"{base_url}/site/{site_id}/list"
        elif serial is not None:
            url = f"{base_url}/{device_type}/{serial}/list"
        elif client_mac is not None:
            url = f"{base_url}/client/{client_mac}/list"
        else:
            url = f"{base_url}/global/list"

        return await self.session.get(url, params={"from": from_time, "to": to_time})

    async def get_aiops_insight_details(
        self,
        insight_id: int,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """Get AI Insight Details by insight id.

        Args:
            insight_id (int): Insight ID
            from_time (int | float | datetime, optional): Start of Time Range to collect insights for.
            to_time (int | float | datetime, optional): End of Time Range to collect insights for.
                Defaults to now.

        Returns:
            Response: CentralAPI Response object
        """
        from_time = from_time or datetime.fromtimestamp(datetime.now(tz=timezone.utc).timestamp() - 10800) # Now - 3 hours (UTC)
        from_time, to_time = utils.parse_time_options(from_time, to_time, in_milliseconds=True)
        url = f"/aiops/v2/insights/global/id/{insight_id}/export"

        return await self.session.get(url, params={"from": from_time, "to": to_time})