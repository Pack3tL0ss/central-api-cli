from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, overload

import tablib
import yaml

from ... import log, utils
from ...client import Response

if TYPE_CHECKING:
    from centralcli.constants import TimeRange
    from centralcli.typedefs import CloudAuthTimeWindow, CloudAuthUploadTypes

    from ...client import Session

@overload
def parse_time_window(time_window: CloudAuthTimeWindow | TimeRange) -> str: ...


@overload
def parse_time_window(time_window: None) -> None: ...


def parse_time_window(time_window: CloudAuthTimeWindow | TimeRange) -> str:
    """Common helper to parse CLI time_window option and return format expected by cloud-auth

    Args:
        time_window (CloudAuthTimeWindow | TimeRange | None): time_window TimeRange enum or str like
            3M where M=Months, w=weeks, d=days, h=hours, m=minutes.
            Valid windows: "3h", "1d", "1w", "1M", "3M"

    Returns:
        str: returns time window in format required by cloud-auth API endpoints.

    Raises:
        ValueError if time window is invalid.
    """
    valid = ["3h", "1d", "1w", "1M", "3M"]
    cli_to_api = {
        "h": "hour",
        "d": "day",
        "w": "week",
        "M": "month"
    }

    time_window = time_window if not hasattr(time_window, "value") else time_window.value
    if time_window not in valid:
        raise ValueError(f"Invalid value for time_window {time_window}.  Valid values: {', '.join(valid)}")

    return f"{time_window[0]}-{cli_to_api[time_window[1]]}"


class CloudAuthAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_registered_macs(
        self,
        search: str = None,
        sort: str = None,
        filename: str = None,
    ) -> Response:
        """Fetch all Mac Registrations as a CSV file.

        Args:
            search (str, optional): Filter the Mac Registrations by Mac Address and Client Name.
                Does a 'contains' match.
            sort (str, optional): Sort order  Valid Values: +name, -name, +display_name,
                -display_name
            filename (str, optional): Suggest a file name for the downloading file via content
                disposition header.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudauth/api/v3/bulk/mac"

        params = {
            'search': search,
            'sort': sort,
            'filename': filename
        }

        resp = await self.session.get(url, params=params)

        if resp:
            try:
                ds = tablib.Dataset().load(resp.output, format="csv")
                resp.output = yaml.load(ds.json, Loader=yaml.SafeLoader)
            except Exception as e:  # pragma: no cover
                log.error(f"cloudauth_get_registered_macs caught {e.__class__.__name__} trying to convert csv return from API to dict.", caption=True, log=True)

        return resp

    async def upload(
        self,
        upload_type: CloudAuthUploadTypes,
        file: Path | str,
        ssid: str = None,
    ) -> Response:

        """Upload file.

        Args:
            upload_type (CloudAuthUploadType): Type of file upload  Valid Values: mpsk, mac
            file (Path | str): The csv file to upload
            ssid (str, optional): The MPSK network (SSID), required if {upload_type} = 'mpsk'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudauth/api/v3/bulk/{upload_type}"
        file = file if isinstance(file, Path) else Path(str(file))  # pragma: no cover
        params = {'ssid': ssid}
        files = {"file": (file.name, file.open("rb"), "text/csv")}

        form_data = utils.build_multipart_form_data(url, files=files, params=params, base_url=self.session.base_url)
        return await self.session.post(url, **form_data)

    async def get_upload_status(
        self,
        upload_type: CloudAuthUploadTypes,
        ssid: str = None,
    ) -> Response:
        """Get upload status of last file upload.

        Args:
            upload_type (CloudAuthUploadType): Type of file upload  Valid Values: mpsk, mac
            ssid (str, optional): MPSK network SSID, required if {upload_type} = 'mpsk'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudauth/api/v3/bulk/{upload_type}/status"

        params = {
            'ssid': ssid
        }

        return await self.session.get(url, params=params)

    async def get_mpsk_networks(
        self,
    ) -> Response:
        """Read all configured MPSK networks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v2/mpsk"

        return await self.session.get(url)

    async def get_named_mpsk(
        self,
        mpsk_id: str,
        name: str = None,
        role: str = None,
        status: str = None,
        cursor: str = None,
        sort: str = None,
        limit: int = 100,
    ) -> Response:
        """Get all named MPSK.

        Args:
            mpsk_id (str): The MPSK configuration ID
            name (str, optional): Filter by name of the named MPSK. Does a 'contains' match.
            role (str, optional): Filter by role of the named MPSK. Does an 'equals' match.
            status (str, optional): Filter by status of the named MPSK. Does an 'equals' match.
                Valid Values: enabled, disabled
            cursor (str, optional): For cursor based pagination.
            sort (str, optional): Sort order  Valid Values: +name, -name, +role, -role, +status,
                -status
            limit (int, optional): Number of items to be fetched Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v2/mpsk/{mpsk_id}/namedMPSK"

        params = {
            'name': name,
            'role': role,
            'status': status,
            'cursor': cursor,
            'sort': sort,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    # API-FLAW you can not set the mpsk or id
    async def add_named_mpsk(
        self,
        mpsk_id: str,
        name: str,
        role: str,
        enabled: bool = True,
    ) -> Response:
        """Add a named MPSK config.

        Args:
            mpsk_id (str): The MPSK configuration ID.  This is the ID associated with the MPSK SSID.
            name (str): Name to identify the mpsk password with
            role (str): Aruba Role to be assigned to device connected using this MPSK password.
            enabled (bool, optional): Set to False to create but disable this named MPSK. Defaults to True (enabled)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v2/mpsk/{mpsk_id}/namedMPSK"

        json_data = {
            'name': name,
            'role': role,
            'status': "enabled" if enabled else "disabled"
        }

        return await self.session.post(url, json_data=json_data)

    async def delete_named_mpsk(
        self,
        mpsk_id: str,
        named_mpsk_id: str,
    ) -> Response:
        """Delete a Named MPSK Config.

        Args:
            mpsk_id (str): The ID associated with the MPSK SSID
            named_mpsk_id (str): The Named MPSK Config ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v2/mpsk/{mpsk_id}/namedMPSK/{named_mpsk_id}"

        return await self.session.delete(url)

    # API-FLAW no way to update the mpsk (passphrase), even if sent in payload it has no impact
    # There is a PUT method for the below as well, don't see the point in ever using it.
    async def update_named_mpsk(
        self,
        mpsk_id: str,
        named_mpsk_id: str,
        mpsk: str = None,
        name: str = None,
        role: str = None,
        enabled: bool = None,
        reset: bool = False,
    ) -> Response:
        """Partially Edit a Named MPSK Config.

        Args:
            mpsk_id (str): The MPSK configuration ID
            named_mpsk_id (str): The Named MPSK Config ID
            mpsk (str): The password to be used to connect.
            name (str): Name to identify the mpsk password with
            role (str): Aruba Role to be assigned to device connected using this MPSK password.
            enable (bool, optional): set True to enbable the MPSK, False to disable it.  Defaults to None (No change)
            reset (bool, optional): If true, a new MPSK password is generated for this named
                MPSK config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v2/mpsk/{mpsk_id}/namedMPSK/{named_mpsk_id}"

        if enabled:
            status = "enabled"
        else:
            status = "disabled" if enabled is False else None

        params = {} if not reset else {'resetMPSK': "true"}

        json_data = {
            'id': named_mpsk_id,
            'mpsk': mpsk,
            'name': name,
            'role': role,
            'status': status
        }
        json_data = utils.strip_none(json_data)

        return await self.session.patch(url, json_data=json_data, params=params)

    async def download_mpsk_csv(
        self,
        ssid: str,
        filename: str = None,
        name: str = None,
        role: str = None,
        status: str = None,
        sort: str = None,
    ) -> Response:
        """Fetch all Named MPSK as a CSV file.

        Args:
            ssid (str): Configured MPSK SSID for which Named MPSKs are to be downloaded.
            filename (str, optional): Suggest a file name for the downloading file via content
                disposition header.
            name (str, optional): Filter by name of the named MPSK. Does a 'contains' match.
            role (str, optional): Filter by role of the named MPSK. Does an 'equals' match.
            status (str, optional): Filter by status of the named MPSK. Does an 'equals' match.
                Valid Values: enabled, disabled
            sort (str, optional): Sort order  Valid Values: +name, -name, +role, -role, +status,
                -status

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v2/download/mpsk"

        params = {
            'ssid': ssid,
            'filename': filename,
            'name': name,
            'role': role,
            'status': status,
            'sort': sort
        }

        return await self.session.get(url, params=params)


    async def get_authentications(
        self,
        from_time: str = None,
        time_window: CloudAuthTimeWindow | TimeRange = None,
        airpass: bool = False,
        cursor: str = None,
        limit: int = 1000
    ) -> Response:
        """Fetch list of authentications using Cloud Identity or AirPass.

        Args:
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.  Default to None, which results in "1h" if time_window is not provided.
            time_window (CloudAuthTimeWindow | TimeRange, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: "3h", "1d", "1w", "1M", "3M"
            airpass (bool, optional): Set to true to fetch airpass authentications.  Default is to fetch Cloud Identitiy authentications.
            cursor (str | None, optional): Pagination cursor.  Should be None for first call.  Use "cursor"
                in payload of previous call for subsequent calls to get the next page of results.
            limit (int, optional): Maximum number of authentication records to be returned. Allowed range is 1
                to 1000.  Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/auth/{'cloud_identity' if not airpass else 'air_pass'}/list"
        if time_window:
            time_window = parse_time_window(time_window)
        elif not from_time:
            from_time = "1h"

        params = {
            'from_time': from_time,
            'time_window': time_window,
            'cursor': cursor,
            'limit': limit,
        }

        return await self.session.get(url, params=params)


    async def get_sessions(
        self,
        from_time: str = None,
        time_window: CloudAuthTimeWindow | TimeRange = None,
        airpass: bool = False,
        cursor: str = None,
        limit: int = 1000
    ) -> Response:
        """Fetch list of sessions using Cloud Identity or AirPass.

        Args:
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.  Default to None, which results in "1h" if time_window is not provided.
            time_window (CloudAuthTimeWindow | TimeRange, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: "3h", "1d", "1w", "1M", "3M"
            airpass (bool, optional): Set to true to fetch airpass sessions.  Default is to fetch Cloud Identitiy sessions.
            cursor (str | None, optional): Pagination cursor.  Should be None for first call.  Use "cursor"
                in payload of previous call for subsequent calls to get the next page of results.
            limit (int, optional): Maximum number of authentication records to be returned. Allowed range is 1
                to 1000.  Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/session/{'cloud_identity' if not airpass else 'air_pass'}/list"
        if time_window:
            time_window = parse_time_window(time_window)
        elif not from_time:
            from_time = "1h"

        params = {
            'from_time': from_time,
            'time_window': time_window,
            'cursor': cursor,
            'limit': limit,
        }

        return await self.session.get(url, params=params)