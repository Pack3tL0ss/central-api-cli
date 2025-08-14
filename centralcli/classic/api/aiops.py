from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Literal

from ... import constants, utils
from ...response import Response

if TYPE_CHECKING:
    from ...client import Session

class AiOpsAPI:
    def __init__(self, session: Session):
        self.session = session

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