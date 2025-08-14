from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiohttp
import tablib
import yaml
from yarl import URL

from ... import constants, log, utils
from ...client import Response

if TYPE_CHECKING:
    from ...client import Session

class CloudAuthAPI:
    def __init__(self, session: Session):
        self.session = session

    async def cloudauth_get_registered_macs(
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
                ds = tablib.Dataset().load(resp.output)
                resp.output = yaml.load(ds.json, Loader=yaml.SafeLoader)
            except Exception as e:
                log.error(f"cloudauth_get_registered_macs caught {e.__class__.__name__} trying to convert csv return from API to dict.", caption=True)

        return resp

    async def cloudauth_upload_fixme(  # pragma: no cover
        self,
        upload_type: constants.CloudAuthUploadTypes,
        file: Path | str,
        ssid: str = None,
    ) -> Response:
        """Upload file.

        This doesn't work still sorting the format of FormData

        Args:
            upload_type (CloudAuthUploadType): Type of file upload  Valid Values: mpsk, mac
            file (Path | str): The csv file to upload
            ssid (str, optional): MPSK network SSID, required if {upload_type} = 'mpsk'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudauth/api/v3/bulk/{upload_type}"
        file = file if isinstance(file, Path) else Path(str(file))
        # data = multipartify(file.read_bytes())
        # data = aiohttp.FormData(file.open())

        params = {
            'ssid': ssid
        }
        files = { "file": (file.name, file.open("rb"), "text/csv") }
        form_data = aiohttp.FormData(files)
        # files = {f'{upload_type}_import': (f'{upload_type}_import.csv', file.read_bytes())}
        headers = {
            "Content-Type": "multipart/form-data",
            'Accept': 'application/json'
        }
        headers = {**headers, **dict(aiohttp.FormData(files)._writer._headers)}

        return await self.session.post(url, headers=headers, params=params, payload=form_data)

    async def cloudauth_upload(
        self,
        upload_type: constants.CloudAuthUploadTypes,
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
        file = file if isinstance(file, Path) else Path(str(file))
        params = {
            'ssid': ssid
        }

        # HACK need to make the above async function work
        import requests
        from requests import Response as RequestsResponse

        files = { "file": (file.name, file.open("rb"), "text/csv") }
        full_url=f"{self.session.base_url or ''}{url}"
        headers = {
            "Authorization": f"Bearer {self.session.auth.central_info['token']['access_token']}",
            'Accept': 'application/json'
        }

        for _ in range(2):
            _resp: RequestsResponse = requests.request("POST", url=full_url, params=params, files=files, headers=headers)
            _log = log.info if _resp.ok else log.error
            _log(f"[PATCH] {url} | {_resp.status_code} | {'OK' if _resp.ok else 'FAILED'} | {_resp.reason}")
            try:
                output = _resp.json()
            except Exception:
                output = f"[{_resp.reason}]" + " " + _resp.text.lstrip('[\n "').rstrip('"\n]')

            # Make requests Response look like aiohttp.ClientResponse
            _resp.status, _resp.method, _resp.url = _resp.status_code, "POST", URL(_resp.url)
            resp = Response(_resp, output=output, raw=output, error=None if _resp.ok else _resp.reason, url=URL(url), elapsed=round(_resp.elapsed.total_seconds(), 2))
            if "invalid_token" in resp.output:
                self.session.refresh_token()
                headers["Authorization"] = f"Bearer {self.session.auth.central_info['token']['access_token']}"
            else:
                break
        return resp

    async def cloudauth_upload_status(
        self,
        upload_type: constants.CloudAuthUploadTypes,
        ssid: str = None,
    ) -> Response:
        """Read upload status of last file upload.

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

    async def cloudauth_get_mpsk_networks(
        self,
    ) -> Response:
        """Read all configured MPSK networks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v2/mpsk"

        return await self.session.get(url)

    async def cloudauth_get_namedmpsk(
        self,
        mpsk_id: str,
        name: str = None,
        role: str = None,
        status: str = None,
        cursor: str = None,
        sort: str = None,
        limit: int = 100,
    ) -> Response:
        """Read all named MPSK.

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
    async def cloudauth_add_namedmpsk(
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

    async def cloudauth_delete_namedmpsk(
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
    async def cloudauth_update_namedmpsk(
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

        params = {} if not reset else {'resetMPSK': reset}

        json_data = {
            'id': named_mpsk_id,
            'mpsk': mpsk,
            'name': name,
            'role': role,
            'status': status
        }
        json_data = utils.strip_none(json_data)

        return await self.session.patch(url, json_data=json_data, params=params)

    async def cloudauth_download_mpsk_csv(
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