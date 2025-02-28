#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import base64
import json
import time
from asyncio.proactor_events import _ProactorBasePipeTransport
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, List, Literal

# from aiohttp import ClientSession
import aiohttp
import tablib
import yaml
from pycentral.base_utils import tokenLocalStoreUtil
from yarl import URL
from copy import deepcopy

from . import ArubaCentralBase, MyLogger, cleaner, config, constants, log, utils
from .exceptions import CentralCliException
from .response import CombinedResponse, Response, Session
from .utils import Mac

# buried import: requests is imported in add_template and cloudauth_upload as a workaround until figure out aiohttp form data




color = utils.color


# https://github.com/aio-libs/aiohttp/issues/4324
def silence_event_loop_closed(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except RuntimeError as e:
            if str(e) != "Event loop is closed":
                raise

    return wrapper


_ProactorBasePipeTransport.__del__ = silence_event_loop_closed(_ProactorBasePipeTransport.__del__)


DEFAULT_TOKEN_STORE = {"type": "local", "path": f"{config.dir.joinpath('.cache')}"}
DEFAULT_ACCESS_RULES = {
    "ALLOW_ALL": [
        {
            "action": "allow",
            "eport": "any",
            "ipaddr": "any",
            "match": "match",
            "netmask": "any",
            "protocol": "any",
            "service_name": "",
            "service_type": "network",
            "sport": "any",
            "throttle_downstream": "",
            "throttle_upstream": ""
        }
    ],
}

START = time.monotonic()


def get_conn_from_file(account_name, logger: MyLogger = log) -> ArubaCentralBase:
    """Creates an instance of class`pycentral.ArubaCentralBase` based on config file.

    provided in the YAML/JSON config file:
        * keyword central_info: A dict containing arguments as accepted by class`pycentral.ArubaCentralBase`
        * keyword ssl_verify: A boolean when set to True, the python client validates Aruba Central's SSL certs.
        * keyword token_store: Optional. Defaults to None.

    Args:
        account_name (str): Account name defined in the config file.
        logger (MyLogger, optional): log method. Defaults to log.

    Returns:
        [pycentral.ArubaCentralBase]: An instance of class:`pycentral.ArubaCentralBase`,
            Used to manage Auth and Tokens.
    """
    if account_name in config.data:
        central_info = config.data[account_name]
    else:
        # Account name callback will kick back errors
        # falling back to default for load of central for auto completion
        central_info = config.data["central_info"]
    token_store = config.token_store
    ssl_verify = central_info.get("ssl_verify", config.data.get("ssl_verify", True))

    conn = ArubaCentralBase(central_info, token_store=token_store, logger=logger, ssl_verify=ssl_verify)
    token_cache = Path(tokenLocalStoreUtil(token_store, central_info["customer_id"], central_info["client_id"]))

    # always create token cache if it doesn't exist and always use it first
    # however if config has been modified more recently any tokens in the config will be tried first
    # if both fail user will be prompted for token if no user/pass or on Internal Cluster.
    if token_cache.is_file():
        cache_token = conn.loadToken()
        if cache_token:
            if token_cache.stat().st_mtime > config.file.stat().st_mtime:
                conn.central_info["retry_token"] = conn.central_info["token"]
                conn.central_info["token"] = cache_token
            else:
                conn.central_info["retry_token"] = cache_token

            # Compare tokens and remove retry token if they are the same.  Rare scenario
            if conn.central_info["retry_token"]["refresh_token"] == conn.central_info["token"]["refresh_token"]:
                del conn.central_info["retry_token"]
    else:
        if not conn.storeToken(conn.central_info.get("token")):
            log.warning("Failed to Store Token and token cache doesn't exist yet.", show=True)

    return conn

class CentralApi(Session):
    def __init__(self, account_name: str = "central_info"):
        self.silent = False  # toggled in _batch_request to squelch Auto logging in Response
        if config.valid and constants.do_load_pycentral():
            self.auth = get_conn_from_file(account_name)
            super().__init__(auth=self.auth)

    @staticmethod
    def _make_form_data(data: dict):
        # TODO how to package python data struct into form-data for API call
        # i.e. update_variables
        form = aiohttp.FormData()
        for key, value in data.items():
            form.add_field(
                key,
                json.dumps(value) if isinstance(value, (list, dict)) else value,
                content_type="multipart/form-data",
                filename="upload"
            )

        return form

    @staticmethod
    def strip_none(_dict: dict | None) -> dict | None:
        """strip all keys from a dict where value is NoneType"""
        if not isinstance(_dict, dict):
            return _dict

        return {k: v for k, v in _dict.items() if v is not None}

    async def get_swarms(
        self,
        group: str = None,
        status: str = None,
        public_ip_address: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        swarm_name: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Swarms.

        Args:
            group (str, optional): Filter by group name
            status (str, optional): Filter by Swarm status
            public_ip_address (str, optional): Filter by public ip address
            fields (str, optional): Comma separated list of fields to be returned
                Valid fields are: status, ip_address, public_ip_address, firmware_version
            calculate_total (bool, optional): Whether to calculate total Swarms
            sort (str, optional): Sort parameter may be one of +swarm_id, -swarm_id
            swarm_name (str, optional): Filter by swarm name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/swarms"

        params = {
            'group': group,
            'status': status,
            'public_ip_address': public_ip_address,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'swarm_name': swarm_name,
            'offset': offset,
            'limit': limit
        }

        params = utils.strip_none(params)

        return await self.get(url, params=params)

    async def get_swarm_details(self, swarm_id: str) -> Response:
        """Swarm Details.

        Args:
            swarm_id (str): Swarm ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def get_clients(
        self,
        client_type: constants.ClientType = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        mac: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get Clients details.

        Args:
            client_type (Literal['wired', 'wireless', 'all'], optional): Client type to retrieve.  Defaults to None.
                if not provided all client types will be returned, unless a filter specific to a client type is
                specified.  i.e. providing band will result in WLAN clients.
            group (str, optional): Filter by Group. Defaults to None.
            swarm_id (str, optional): Filter by swarm. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            network (str, optional): Filter by WLAN SSID. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            serial (str, optional): Filter by connected device serial. Defaults to None.
            os_type (str, optional): Filter by client OS type. Defaults to None.
            stack_id (str, optional): Filter by Stack ID. Defaults to None.
            cluster_id (str, optional): Filter by Cluster ID. Defaults to None.
            band (str, optional): Filter by band. Defaults to None.
            mac (str, optional): Filter by client MAC. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for.  Format:
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): API Paging offset. Defaults to 0.
            limit (int, optional): API record limit per request. Defaults to 1000 Max 1000.

        Returns:
            Response: CentralAPI Response Object
        """
        params = {
            "group": group,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "client_status": client_status,
            "past": past,
            "offset": offset,
            "limit": limit,
        }
        wlan_only_params = {
            "network": network,
            "os_type": os_type,
            "band": band,
            "swarm_id": swarm_id,
        }
        wired_only_params = {
            "stack_id": stack_id,
        }
        all_params = {**params, **wlan_only_params, **wired_only_params}
        wired_params = {**params, **wired_only_params}
        wlan_params = {**params, **wlan_only_params}

        if True in wlan_only_params.values():
            if client_type and client_type != "wireless":
                raise ValueError(f"Invalid combination of filters.  WLAN only filter provided which conflicts with client type {client_type}")
            client_type = "wireless"
        if True in wired_only_params.values():
            if client_type and client_type != "wired":
                raise ValueError(f"Invalid combination of filters.  WIRED only filter provided which conflicts with client type {client_type}")
            client_type = "wired"

        if mac:
            _mac = utils.Mac(
                mac,
                fuzzy=True,
            )

            if _mac.ok:
                mac = _mac
            else:
                return Response(error="INVALID MAC", output=f"The Provided MAC {_mac} Appears to be invalid.")

        if mac:
            return await self.get_client_details(mac,)

        if client_type == "wireless":
            return await self.get_wireless_clients(**wlan_params,)

        if client_type == "wired":
            return await self.get_wired_clients(**wired_params,)

        return await self.get_all_clients(**all_params,)

    async def get_all_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get All clients

        Args:
            group (str, optional): Return clients connected to devices in a given group. Defaults to None.
            swarm_id (str, optional): Return clients connected to swarm by swarm_id. Defaults to None.
            label (str, optional): Return clients connected to device with provided label.
                Defaults to None.
            network (str, optional): Return clients for given network (SSID). Defaults to None.
            site (str, optional): Return clients in a particular site. Defaults to None.
            serial (str, optional): Return clients connected to the device with given serial. Defaults to None.
            os_type (str, optional): Return clients with provided os_type. Defaults to None.
            stack_id (str, optional): Return clients connected to stack with provided id. Defaults to None.
            cluster_id (str, optional): Return clients connected to cluster with provided id. Defaults to None.
            band (str, optional): Return (WLAN) clients connected to provided band. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): API offset. Defaults to 0.
            limit (int, optional): API record limit. Defaults to 1000, Max 1000.

        Returns:
            Response: CentralCli.Response object
        """
        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "client_status": client_status,
            "past": past,
            "offset": offset,
            "limit": limit,
            "calculate_total": True
        }
        wlan_only_params = {"network": network, "os_type": os_type, "band": band}
        wired_only_params = {"stack_id": stack_id}

        reqs = [
            self.BatchRequest(self.get_wireless_clients, **{**params, **wlan_only_params}),
            self.BatchRequest(self.get_wired_clients, **{**params, **wired_only_params})
        ]

        # FIXME if wireless clients call passes but wired fails there is no indication in cencli show clients output
        # TODO need Response to have an attribute that stores failed calls so cli commands can display output of passed calls and details on errors (when some calls fail)
        resp = await self._batch_request(reqs)
        if len(resp) == 2:
            out = []
            for r in resp:
                if r.ok:
                    out += r.output
            raw = [
                {"raw_wireless_response": resp[0].raw},
                {"raw_wired_response": resp[1].raw}
            ]
            resp = resp[1] if resp[1].ok else resp[0]
            resp.output = out
            resp.raw = raw
            return resp

        return resp[-1]

    async def get_wireless_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        network: str = None,
        serial: str = None,
        os_type: str = None,
        cluster_id: str = None,
        band: str = None,
        fields: str = None,
        calculate_total: bool = True,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Wireless Clients.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            network (str, optional): Filter by network name
            serial (str, optional): Filter by AP serial number
            os_type (str, optional): Filter by client os type
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band. Value can be either "2.4" or "5"
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                name, ip_address, username, os_type, connection, associated_device, group_name,
                swarm_id, network, radio_mac, manufacturer, vlan, encryption_method, radio_number,
                speed, usage, health, labels, site, signal_strength, signal_db, snr
            calculate_total (bool, optional): Whether to calculate total wireless Clients
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000, max 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wireless"

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "network": network,
            "serial": serial,
            "os_type": os_type,
            "cluster_id": cluster_id,
            "band": band,
            "fields": fields,
            "calculate_total": str(calculate_total).lower(),
            "client_status": client_status,
            "timerange": past,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params,)

    async def get_wired_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        fields: str = None,
        calculate_total: bool = True,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Wired Clients.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by Switch or AP serial number
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                name, ip_address, username, associated_device, group_name, interface_mac, vlan
            calculate_total (bool, optional): Whether to calculate total wired Clients
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            FIXME sort (str, optional): Field to sort on.  Defaults to mac
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default 1000, max 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wired"

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "stack_id": stack_id,
            "fields": fields,
            "calculate_total": str(calculate_total).lower(),
            "client_status": client_status,
            "timerange": past,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params,)

    async def get_client_details(
        self,
        mac: Mac,
    ) -> Response:
        """Get Client Details.

        Args:
            mac (utils.Mac): MAC address of the Wireless Client to be queried
                API will return results matching a partial Mac

        Returns:
            Response: CentralAPI Response object
        """
        mac = mac if hasattr(mac, "url") else utils.Mac(mac, fuzzy=True,)
        url = f"/monitoring/v2/clients/{mac.url}"
        return await self.get(url)

    async def get_client_roaming_history(
        self,
        mac: str,
        calculate_total: bool = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Wireless Client Mobility Trail.

        Args:
            mac (str): MAC address of the Wireless Client to be queried
            calculate_total (bool, optional): Whether to calculate total transitions
            from_time (int | float | datetime, optional): Collect roaming history from this starting point.
                Default is now minus 3 hours.
            to_time (int | float | datetime, optional): End of time-range to collect roaming history for.
                Default is now.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000, max is 1000.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = f"/monitoring/v1/clients/wireless/{mac}/mobility_trail"

        params = {
            'calculate_total': calculate_total,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_certificates(
        self, q: str = None, offset: int = 0, limit: int = 20, callback: callable = None, callback_kwargs: dict = None
    ) -> Response:
        """Get Certificates details.

        Args:
            q (str, optional): Search for a particular certificate by its name, md5 hash or sha1_hash
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 20, Max 20.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/certificates"

        # offset and limit are both required by the API method.
        params = {"q": q, "offset": offset, "limit": limit}

        return await self.get(url, params=params, callback=callback, callback_kwargs=callback_kwargs)

    async def get_template(
        self,
        group: str,
        template: str,
    ) -> Response:
        """Get template text for a template in group.

        Args:
            group (str): Name of the group for which the templates are being queried.
            template (str): Name of template.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates/{template}"

        return await self.get(url)

    async def get_template_details_for_device(self, serial: str, details: bool = False) -> Response:
        """Get configuration details for a device (only for template groups).

        Args:
            serial (str): Serial number of the device.
            details (bool, optional): Usually pass false to get only the summary of a device's
                configuration status.
                Pass true only if detailed response of a device's configuration status is required.
                Passing true might result in slower API response and performance effect
                comparatively.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/config_details"
        headers = {"Accept": "multipart/form-data"}
        params = {"details": str(details)}
        return await self.get(url, params=params, headers=headers)

    async def get_all_templates_in_group(
        self,
        group: str,
        name: str = None,
        device_type: constants.DeviceTypes = None,
        version: str = None,
        model: str = None,
        query: str = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Response:
        """Get all templates in group.

        Args:
            group (str): Name of the group for which the templates are being queried.
            template (str, optional): Filter on provided name as template.
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Filter on device_type.  Valid Values: ap|gw|cx|sw.
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: ALL, 2920, J9727A etc.
            query (str, optional): Search for template OR version OR model, query will be ignored if any of
                filter parameters are provided.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of template records to be returned. Max 20. Defaults to
                20.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        if device_type:
            device_type = constants.lib_to_api(device_type, "template")

        params = {
            'template': name,
            'device_type': device_type,
            'version': version,
            'model': model,
            'q': query,
            'offset': offset,
            'limit': limit  # max 20
        }

        return await self.get(url, params=params)

    # FIXME # TODO # What the Absolute F?!  not able to send template as formdata properly with aiohttp
    #       requests module works, but no luck after hours messing with form-data in aiohttp
    async def add_template(
        self,
        name: str,
        group: str,
        template: Path | str | bytes,
        device_type: constants.DeviceTypes ="ap",
        version: str = "ALL",
        model: str = "ALL",
    ) -> Response:
        """Create new template.

        Args:
            name (str): Name of template.
            group (str): Name of the group for which the template is to be created.
            template (Path | str | bytes): Template File or encoded template content.
                For sw (AOS-Switch) device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.
                2. aruba-central url https://<URL | IP>/ws.
            device_type (str): Device type of the template.  Valid Values: ap, sw, cx, gw
                Defaults to ap.
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For sw (AOS-Switch) device_type, part number (J number) can be used for the model
                parameter. Example: 2920, J9727A, etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        if isinstance(template, bytes):
            files = {'template': ('template.txt', template)}
        else:
            template = template if isinstance(template, Path) else Path(str(template))
            if not template.exists():
                raise FileNotFoundError

            files = {'template': ('template.txt', template.read_bytes())}

        device_type = device_type if not hasattr(device_type, "value") else device_type.value
        device_type = constants.lib_to_api(device_type, "template")

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        # HACK This works but prefer to get aiohttp sorted for consistency
        import requests
        headers = {
            "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
            'Accept': 'application/json'
        }
        url=f"{self.auth.central_info['base_url']}{url}"
        for _ in range(2):
            resp = requests.request("POST", url=url, params=params, files=files, headers=headers)
            if "[\n" in resp.text and "\n]" in resp.text:
                output = "\n".join(json.loads(resp.text))
            else:
                output = resp.text.strip('"\n')
            resp = Response(resp, output=output, elapsed=round(resp.elapsed.total_seconds(), 2))
            if "invalid_token" in resp.output:
                self.refresh_token()
            else:
                break
        return resp

    async def update_existing_template(
        self,
        group: str,
        name: str,
        payload: str = None,
        template: Path | str | bytes = None,
        device_type: constants.DeviceTypes ="ap",
        version: str = "ALL",
        model: str = "ALL",
    ) -> Response:
        """Update existing template.

        Args:
            group (str): Name of the group for which the template is to be updated.
            name (str): Name of template.
            device_type (str, optional): Device type of the template.
                Valid Values: ap, sw (ArubaOS-SW), cx (ArubaOS-CX), gw (controllers/gateways)
            version (str, optional): Firmware version property of template.
                Example: ALL, 6.5.4 etc.  Defaults to "ALL".
            model (str, optional): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model.
                Example: 2920, J9727A etc.  Defaults to "ALL".
            template (Path | str | bytes, optional): Template text.
                For 'ArubaSwitch' device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.
                2. aruba-central url https://<URL | IP>/ws.
            payload (str, optional): template data passed as str.
                One of template or payload is required.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"

        if device_type:
            device_type = constants.lib_to_api(device_type, "template")

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        if template:
            template = template if isinstance(template, Path) else Path(str(template))
            if not template.exists():
                raise FileNotFoundError
            if template.is_file() and template.stat().st_size > 0:
                template_data: bytes = template.read_bytes()
        elif payload:
            payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")
            template_data: bytes = payload
        else:
            raise ValueError("One of template or payload is required")

        files = {'template': ('template.txt', template_data)}

        # HACK aiohttp has issue here similar to add_template
        import requests  # TODO MOVE to Session until aiohttp has file types sorted.
        full_url=f"{self.auth.central_info['base_url']}{url}"
        for _ in range(2):
            headers = {
                "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
                'Accept': 'application/json'
            }
            resp = requests.request("PATCH", url=full_url, params=params, files=files, headers=headers)
            _log = log.info if resp.ok else log.error
            _log(f"[PATCH] {resp.url} | {resp.status_code} | {'OK' if resp.ok else 'FAILED'} | {resp.reason}")
            try:
                output = resp.json()
            except json.JSONDecodeError:
                if "[\n" in resp.text and "\n]" in resp.text:
                    output = "\n".join(json.loads(resp.text))
                else:
                    output = resp.text.strip('"\n')
            resp.status, resp.method, resp.url = resp.status_code, "PATCH", URL(resp.url)
            resp = Response(resp, output=output, raw=output, elapsed=round(resp.elapsed.total_seconds(), 2))
            if "invalid_token" in resp.output:
                self.refresh_token()
            else:
                break
        return resp

    async def get_group_names(self) -> Response:
        """Get a listing of all group names defined in Aruba Central

        Returns:
            Response: CentralAPI Respose object
                output attribute will be List[str]
        """
        url = "/configuration/v2/groups"
        params = {"offset": 0, "limit": 100}  # 100 is the max
        resp = await self.get(url, params=params,)
        if resp.ok:
            # convert list of single item lists to a single list, remove unprovisioned group, move default group to front of list.
            resp.output = [g for _ in resp.output for g in _ if g != "unprovisioned"]
            if "default" in resp.output:
                resp.output.insert(0, resp.output.pop(resp.output.index("default")))

        return resp

    async def delete_template(
        self,
        group: str,
        template: str,
    ) -> Response:
        """Delete existing template.

        Args:
            group (str): Name of the group for which the template is to be deleted.
            template (str): Name of the template to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates/{template}"

        return await self.delete(url)

    async def get_all_groups(self) -> Response:
        """Get properties and template info for all groups

        This method will first call configuration/v2/groups to get a list of group names.

        It then combines the responses from /configuration/v2/groups/template_info
        and /configuration/v1/groups/properties to get the template details
        (template_group or not) and properties for each group.

         The template_info and properties endpoints both allow 20 groups per request.
         Multiple requests will be performed async if there are more than 20 groups.

        Raises:
            CentralCliException: Raised when validation of combined responses fails.

        Returns:
            Response: centralcli Response Object
        """
        resp = await self.get_group_names()
        if not resp.ok:
            return resp

        groups = resp.output
        groups_with_comma_in_name = list(filter(lambda g: "," in g, groups))
        if groups_with_comma_in_name:
            log.error(f"Ignoring group(s): {'|'.join(groups_with_comma_in_name)}.  Group APIs do not support groups with commas in name", show=True, caption=True, log=True)
            _ = [groups.pop(groups.index(g)) for g in groups_with_comma_in_name]

        batch_resp = await self._batch_request(
            [
                self.BatchRequest(self.get_groups_template_status, groups),
                self.BatchRequest(self.get_groups_properties, groups)
            ]
        )
        if all([not r.ok for r in batch_resp]):  # if first call fails possible to only have 1 call returned.
            return batch_resp
        template_resp, props_resp = batch_resp

        template_by_group = {d["group"]: d["template_details"] for d in deepcopy(template_resp.output)}
        props_by_group = {d["group"]: d["properties"] for d in deepcopy(props_resp.output)}

        combined = {tg: {"properties": pv, "template_details": tv} for (tg, tv), (pg, pv) in zip(template_by_group.items(), props_by_group.items()) if pg == tg}
        if len(set([len(combined), len(template_by_group), len(props_by_group)])) > 1:
            raise CentralCliException("Unexpected error in get_all_groups, length of responses differs.")

        combined_resp = Response(props_resp._response)
        combined_resp.output = [{"group": k, **v} for k, v in combined.items()]
        combined_resp.raw = {"properties": props_resp.raw, "template_info": template_resp.raw}

        return combined_resp


    async def get_groups_template_status(self, groups: List[str] | str = None) -> Response:
        """Get template group status for provided groups or all if none are provided.  (if it is a template group or not)

        Will return response from /configuration/v2/groups/template_info endpoint.
        If no groups are provided /configuration/v2/groups is first called to get a list of all group names.

        Args:
            groups (List[str] | str, optional): A single group or list of groups. Defaults to None (all groups).

        Returns:
            Response: centralcli Response Object
        """
        url = "/configuration/v2/groups/template_info"

        if isinstance(groups, str):
            groups = [groups]

        if not groups:
            resp = await self.get_group_names()
            if not resp.ok:
                return resp
            groups: List[str] = resp.output

        batch_reqs = []
        for chunk in utils.chunker(groups, 20):  # This call allows a max of 20
            params = {"groups": ",".join(chunk)}
            batch_reqs += [self.BatchRequest(self.get, url, params=params)]

        batch_resp = await self._batch_request(batch_reqs)
        failed = [r for r in batch_resp if not r.ok]
        passed = batch_resp if not failed else [r for r in batch_resp if r.ok]
        if failed:
            log.error(f"{len(failed)} of {len(batch_reqs)} API requests to {url} have failed.", show=True, caption=True)
            fail_msgs = list(set([r.output.get("description", str(r.output)) for r in failed]))
            for msg in fail_msgs:
                log.error(f"Failure description: {msg}", show=True, caption=True)

        output = [r for res in passed for r in res.output]
        resp = batch_resp[-1] if not passed else passed[-1]
        resp.output = output
        if "data" in resp.raw:
            resp.raw["data"] = output
        else:
            log.warning("raw attr in resp from get_all_groups lacks expected outer key 'data'")

        return resp


    async def get_all_templates(
        self, groups: List[dict] | List[str ] = None,
        template: str = None,
        device_type: constants.DeviceTypes = None,
        version: str = None,
        model: str = None,
        query: str = None,
    ) -> Response:
        """Get data for all defined templates from Aruba Central

        Args:
            groups (List[dict] | List[str], optional): List of groups.  If provided additional API
                calls to get group names for all template groups are not performed).
                If a list of str (group names) is provided all are queried for templates
                If a list of dicts is provided:  It should look like: [{"name": "group_name", "wired_tg": True, "wlan_tg": False}]
                Defaults to None.
            template (str, optional): Filter on provided name as template.
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Filter on device_type.  Valid Values: ap|gw|cx|sw.
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: ALL, 2920, J9727A etc.
            query (str, optional): Search for template OR version OR model, query will be ignored if any of
                filter parameters are provided.

        Returns:
            Response: centralcli Response Object
        """
        if not groups:
            resp = await self.get_groups_template_status()
            if not resp:
                return resp

            template_groups = [g["group"] for g in resp.output if True in g["template_details"].values()]
        elif isinstance(groups, list) and all([isinstance(g, str) for g in groups]):
                template_groups = groups
        else:
            template_groups = [g["name"] for g in groups if True in [g["wired_tg"], g["wlan_tg"]]]

        if not template_groups:
            return Response(
                url="No call performed",
                ok=True,
                output=[],
                raw=[],
                error="None of the configured groups are Template Groups.",
            )

        params = {
            'name': template,
            'device_type': device_type,
            'version': version,
            'model': model,
            'query': query,
        }

        reqs = [self.BatchRequest(self.get_all_templates_in_group, group, **params) for group in template_groups]
        # TODO maybe call the aggregator from _bath_request
        responses = await self._batch_request(reqs)
        failed = [r for r in responses if not r]
        if failed:
            return failed[-1]

        # combine result for all calls into 1
        # TODO aggregator Response object for multi response
        # maybe add property to Response that returns dict being done with dict comp below
        all_output = [rr for r in responses for rr in r.output]
        all_raw = {
            f"[{r.error}] {r.method} {r.url.path if not int(r.url.query.get('offset', 0)) else r.url.path_qs}": r.raw
            for r in responses
        }
        responses[-1].output = all_output
        responses[-1].raw = all_raw

        return responses[-1]

    # API-FLAW limit doesn't appear to have an upper limit, but took forever to return 5,000 records
    async def get_device_inventory(
        self,
        device_type: Literal['ap', 'gw', 'switch', 'all'] = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get devices from device inventory.

        Args:
            device_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        device_type = "all" if not device_type else constants.lib_to_api(device_type, "inventory")
        if config.is_cop and device_type == "gateway":
            device_type = "controller"

        params = {
            'sku_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_all_devices(
            self,
            cache: bool = False,
            dev_types: constants.GenericDeviceTypes | List[constants.GenericDeviceTypes] = None,
            group: str = None,
            site: str = None,
            label: str = None,
            serial: str = None,
            mac: str = None,
            model: str = None,
            stack_id: str = None,
            swarm_id: str = None,
            cluster_id: str = None,
            public_ip_address: str = None,
            status: constants.DeviceStatus = None,
            show_resource_details: bool = True,
            calculate_client_count: bool = True,
            calculate_ssid_count: bool = False,
            fields: list = None,
            offset: int = 0,
            limit: int = 1000,  # max allowed 1000
        ) -> CombinedResponse | List[Response]:
        """Get all devices from Aruba Central.

        Args:
            dev_types (Literal['ap', 'gw', 'cx', 'sw', 'sdwan', 'switch'], optional): Device Types to Update. Defaults to None.
            group (str, optional): Filter by devices in a Group. Defaults to None.
            site (str, optional): Filter by devices in a Site. Defaults to None.
            label (str, optional): Filter by devices with a label assigned. Defaults to None.
            serial (str, optional): Filter by Serial. Defaults to None.
            mac (str, optional): Filter by mac. Defaults to None.
            model (str, optional): Filter by model. Defaults to None.
            stack_id (str, optional): Filter by stack id (switches). Defaults to None.
            swarm_id (str, optional): Filter by swarm id (APs). Defaults to None.
            cluster_id (str, optional): Filter by cluster id. Defaults to None.
            public_ip_address (str, optional): Filter by public ip. Defaults to None.
            status (constants.DeviceStatus, optional): Filter by status. Defaults to None.
            show_resource_details (bool, optional): Show device resource utilization details. Defaults to True.
            calculate_client_count (bool, optional): Calculate client count. Defaults to True.
            calculate_ssid_count (bool, optional): Calculate SSID count. Defaults to False.
            fields (list, optional): fields to return. Defaults to None.
            offset (int, optional): pagination offset. Defaults to 0.
            limit (int, optional): pagination limit max 1000. Defaults to 1000.

        Returns:
            CombinedResponse: CombinedResponse object.
        """

        dev_types = ["aps", "switches", "gateways"]  if dev_types is None else [constants.lib_to_api(dev_type, "monitoring") for dev_type in dev_types]

        # We always get resource details for switches when cache=True as we need it for the switch_role (standalone/conductor/secondary/member) to store in the cache.
        # We used the switch with an IP to determine which is the conductor in the past, but found scenarios where no IP was showing in central for an extended period of time.
        reqs = [
            self.BatchRequest(
                self.get_devices,
                dev_type,
                calculate_client_count=calculate_client_count,
                show_resource_details=show_resource_details if not cache or dev_type != "switches" else True,
                group=group,
                label=label,
                stack_id=stack_id,
                swarm_id=swarm_id,
                serial=serial,
                status=status,
                fields=fields,
                cluster_id=cluster_id,
                model=model,
                calculate_ssid_count=calculate_ssid_count,
                mac=mac,
                public_ip_address=public_ip_address,
                site=site,
                offset=offset,
                limit=limit,
            )
            for dev_type in dev_types
        ]
        batch_resp = await self._batch_request(reqs)
        if all([not r.ok for r in batch_resp]):
            return utils.unlistify(batch_resp)

        combined = CombinedResponse(batch_resp)

        if combined.ok and combined.failed:  # combined.ok indicates at least 1 call was ok, if None are ok no need for Partial failure msg
            for r in combined.failed:
                log.error(f'Partial Failure {r.url.path} | {r.status} | {r.error}', caption=True)

        return combined

    # API-FLAW aos-sw always shows VLAN as 1 (allowed_vlans represents the PVID for an access port, include all VLANs on a trunk port, no indication of native)
    # API-FLAW aos-sw always shows mode as access, cx does as well, but has vlan_mode which is accurate
    # API-FLAW neither show interface name/description
    async def get_switch_ports(self, iden: str, slot: str = None, stack: bool = False, aos_sw: bool = False) -> Response:
        """Switch Ports Details.

        Args:
            iden (str): Serial number of switch to be queried or the stack_id if it's a stack
            slot (str, optional): Slot name of the ports to be queried {For chassis type switches
                only}.
            stack: (bool, optional) : Get details for stack vs individual switch (iden needs to be the stack_id)
                Defaults to False.
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False (indicating CX switch)

        Returns:
            Response: CentralAPI Response object
        """
        if stack:
            sw_path = "cx_switch_stacks" if not aos_sw else "switch_stacks"
        else:
            sw_path = "cx_switches" if not aos_sw else "switches"
        url = f"/monitoring/v1/{sw_path}/{iden}/ports"

        params = {"slot": slot}

        return await self.get(url, params=params)

    async def get_switch_poe_details(
        self,
        serial: str,
        port: str = None,
        aos_sw: bool = False,
    ) -> Response:
        """Get switch poe info.

        Args:
            serial (str): Switch serial
            port (str, optional): Filter by switch port
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False (CX Switch)

        Returns:
            Response: CentralAPI Response object
        """
        sw_path = "cx_switches" if not aos_sw else "switches"
        url = f"/monitoring/v1/{sw_path}/{serial}/poe_detail"

        params = {
            'port': str(port)
        }

        if not port:
            url = f"{url}s"
            params = {}

        return await self.get(url, params=params)

    async def get_gateway_ports(self, serial: str) -> Response:
        """Gateway Ports Details.

        Args:
            serial (str): Serial number of Gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports"

        return await self.get(url)

    async def get_variablised_template(self, serial: str) -> Response:
        """Get variablised template for an Aruba Switch.

        Args:
            serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/variablised_template"

        return await self.get(url)

    async def get_variables(
            self,
            serial: str = None,
            offset: int = 0,
            limit: int = 20,
        ) -> Response:
        """Get template variables for a device or all devices

        Args:
            serial (str): Serial number of the device, If None provided all templates for all devices
                will be fetched.  Defaults to None.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 20.

        offset and limit are ignored if serial is provided.

        Returns:
            Response: CentralAPI Response object
        """
        if serial and serial != "all":
            url = f"/configuration/v1/devices/{serial}/template_variables"
            params = {}
        else:
            url = "/configuration/v1/devices/template_variables"
            params = {"offset": offset, "limit": limit}

        return await self.get(url, params=params)

    async def create_device_template_variables(
        self,
        serial: str,
        mac: str,
        var_dict: dict,
    ) -> Response:
        """Create template variables for a device.

        Args:
            serial (str): Serial number of the device.
            mac (str): MAC address of the device.
            var_dict (dict): dict with variables to be updated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/template_variables"

        var_dict = {k: v for k, v in var_dict.items() if k not in ["_sys_serial", "_sys_lan_mac"]}
        mac = utils.Mac(mac)

        json_data = {
            'total': len(var_dict) + 2,
            "variables": {
                **{
                    '_sys_serial': serial,
                    '_sys_lan_mac': mac.cols,
                },
                **var_dict
            }
        }

        return await self.post(url, json_data=json_data)


    # TODO figure out how to make this work, need file like object
    async def update_device_template_variables(
        self,
        serial: str,
        mac: str,
        var_dict: dict,
    ) -> Response:
        """Update template variables for a device.

        Args:
            serial (str): Serial number of the device.
            mac (str): MAC address of the device.
            var_dict (dict): dict with variables to be updated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/template_variables"
        var_dict = {k: v for k, v in var_dict.items() if k not in ["_sys_serial", "_sys_lan_mac"]}
        # headers = {"Content-Type": "multipart/form-data"}

        json_data = {
            'total': len(var_dict) + 2,
            "variables": {
                **{
                    '_sys_serial': serial,
                    '_sys_lan_mac': mac,
                },
                **var_dict
            }
        }
        # data = self._make_form_data(json_data)
        # data = multipartify(json_data)

        # return await self.patch(url, headers=headers, data=data)
        return await self.patch(url, json_data=json_data)

    # API-FLAW  Seems to work fine for cx, ap, but gw the return is
    # "Fetching configuration in progress for Mobility Controller SERIAL/MAC"
    # subsequent calls for the same gw return 500 internal server error.
    # FIXME
    async def get_device_configuration(self, serial: str) -> Response:
        """Get last known running configuration for a device.

        // Used by show run <DEVICE-IDEN> //

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/configuration"
        headers = {"Accept": "multipart/form-data"}

        return await self.get(url, headers=headers)

    async def get_bssids(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        mac: str = None,
        cluster_id: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List BSSIDs.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by AP serial number
            mac (str, optional): Filter by AP MAC address
            cluster_id (str, optional): Filter by Mobility Controller serial number
            calculate_total (bool, optional): Whether to calculate total APs
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr,-macaddr,
                +swarm_id, -swarm_id.Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/bssids"

        params = {
            'serial': serial,
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            'macaddr': mac,
            'cluster_id': cluster_id,
            'calculate_total': calculate_total,
            'sort': sort,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

    async def get_devices(
        self,
        device_type: constants.GenericDeviceTypes,
        *,
        group: str = None,
        label: str = None,
        stack_id: str = None,
        swarm_id: str = None,
        serial: str = None,
        status: constants.DeviceStatus = None,
        fields: list = None,
        show_resource_details: bool = False,
        cluster_id: str = None,
        model: str = None,
        calculate_client_count: bool = True,
        calculate_ssid_count: bool = False,
        mac: str = None,
        public_ip_address: str = None,
        site: str = None,
        limit: int = 1000,  # max allowed 1000
        offset: int = 0,
    ) -> Response:
        """Get Devices from Aruba Central API Gateway

        Args:
            device_type (Literal["ap", "gw", "switch"): Type of devices to get.
            group (str, optional): Filter on specific group. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            stack_id (str, optional): Return switch with specific stack_id. Defaults to None.
            swarm_id (str, optional): Return APs with a specific swarm_id. Defaults to None.
            serial (str, optional): Return the device with serial number. Defaults to None.
            status (str, optional): Filter by status. Defaults to None.
            fields (list, optional): Return specific fields for device. Defaults to None.
            show_resource_details (bool, optional): Show resource utilization. Defaults to False.
            cluster_id (str, optional): Return gateways with a specific cluster_id. Defaults to None.
            model (str, optional): Filter by device model. Defaults to None.
            calculate_client_count (bool, optional): Calculate client count for each device. Defaults to False.
            calculate_ssid_count (bool, optional): Calculate SSID count for each AP. Defaults to False.
            mac (str, optional): Return device with specific MAC (fuzzy match). Defaults to None.
            public_ip_address (str, optional): Filter devices by Public IP. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object

        Raises:
            ValueError: Raised if device_type is not valid.
        """
        if device_type not in ["switches", "aps", "gateways"]:
            device_type = constants.lib_to_api(device_type, "monitoring")
            if device_type not in ["switches", "aps", "gateways"]:
                raise ValueError(f"device_type must be one of ap, gw, switch not {device_type}")

        dev_params = {
            "aps": {
                'serial': serial,
                'macaddr': mac,
                "swarm_id": swarm_id,
                'model': model,
                'cluster_id': cluster_id,
                'fields': fields,
                'calculate_client_count': str(calculate_client_count).lower(),
                'calculate_ssid_count': str(calculate_ssid_count).lower(),
                'show_resource_details': str(show_resource_details).lower(),
            },
            "switches": {
                'stack_id': stack_id,
                'show_resource_details': str(show_resource_details).lower(),
                'calculate_client_count': str(calculate_client_count).lower(),
                'public_ip_address': public_ip_address,
            },
            "gateways": {
                'macaddr': mac,
                'model': model,
                'fields': fields,
            }
        }
        dev_params["mobility_controllers"] = dev_params["gateways"]

        common_params = {
            "group": group,
            "label": label,
            'site': site,
            'status': None if not status else status.title(),
            'offset': offset,
            'limit': limit,
            "calculate_total": "true"  # So we know if we have multile calls that can be ran async
        }

        url = f"/monitoring/v1/{device_type}"
        if device_type == "aps":
            url = url.replace("v1", "v2")
        elif device_type == "gateways" and config.is_cop:
            url = url.replace("v1/gateways", "v2/mobility_controllers")
        params = {**common_params, **dev_params[device_type]}

        return await self.get(url, params=params)

    async def get_switch_stacks(
        self,
        hostname: str = None,
        group: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Switch Stacks.

        Args:
            hostname (str, optional): Filter by stack hostname
            group (str, optional): Filter by group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000 and max is 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switch_stacks"

        params = {
            'hostname': hostname,
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_switch_stack_details(
        self,
        stack_id: str,
    ) -> Response:
        """Switch Stack Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.get(url)

    async def get_dev_details(
        self,
        device_type: constants.GenericDeviceTypes,
        serial: str
    ) -> Response:
        """Return Details for a given device

        Args:
            device_type (Literal["ap", "gw", "switch"): Type of devices to get
            serial (str): Serial number of Device

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "monitoring")
        if device_type not in ["switches", "aps", "gateways"]:
            raise ValueError(f"device_type must be one of ap, gw, switch not {device_type}")

        url = f"/monitoring/v1/{device_type}/{serial}"

        return await self.get(url)

    async def get_wlans(
        self,
        name: str = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        calculate_client_count: bool = None,
        sort_by: str = None
    ) -> Response:
        """List all WLANs (SSIDs).

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            calculate_client_count (bool, optional): Whether to calculate client count per SSID
            sort_by (str, optional): Sort parameter may be one of +essid, -essid. Default is '+essid'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks"
        if name:
            url = f"{url}/{name}"

        if calculate_client_count in [True, False]:
            calculate_client_count = str(calculate_client_count)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'calculate_client_count': calculate_client_count,
            'sort': sort_by,
        }

        return await self.get(url, params=params)

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

        return await self.get(url)

    async def get_full_wlan_list(
        self,
        scope: str,
    ) -> Response:
        """Get WLAN list/details by (UI) group.

        Args:
            scope (str): Provide one of group name, swarm id, or serial number.
                Example: Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{scope}"

        # this endpoint returns a JSON string
        resp = await self.get(url)
        if isinstance(resp.output, str):
            resp.output = json.loads(resp.output)
        if isinstance(resp.output, dict) and "wlans" in resp.output:
            resp.output = resp.output["wlans"]

        return resp

    # API-FLAW This method returns next to nothing for reserved IPs.
    # Would be more ideal if it returned client_name pool pvid etc as it does with non resserved IPs
    async def get_dhcp_clients(
        self,
        serial: str,
        reservation: bool = True,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """Get DHCP Client information from Gateway.

        Args:
            serial (str): Serial number of mobility controller to be queried
            reservation (bool, optional): Flag to turn on/off listing DHCP reservations(if any).
                Defaults to True
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. max 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        gw_path = "mobility_controllers" if config.is_cop else "gateways"
        url = f"/monitoring/v1/{gw_path}/{serial}/dhcp_clients"

        params = {
            'reservation': str(reservation),
            "offset": offset,
            "limit": limit
        }

        return await self.get(url, params=params)

    async def get_dhcp_pools(self, serial: str) -> Response:
        """Gateway DHCP Pools details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/dhcp_pools"

        return await self.get(url)

    async def get_all_sites(
        self,
        calculate_total: bool = False,
        sort: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Sites.

        Args:
            calculate_total (bool, optional): Whether to calculate total Site Labels
            sort (str, optional): Sort parameter may be one of +site_name, -site_name. Default is
                +site_name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 1000 (max).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"

        params = {
            'calculate_total': str(calculate_total),
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    # async def get_site_details(self, site_id):
    #     return await self.get(f"/central/v2/sites/{site_id}", callback=cleaner.sites)

    async def get_site_details(
        self,
        site_id: int,
    ) -> Response:
        """Site details.

        Args:
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        return await self.get(url)

    # API-FLAW total changes during subsequent pagination calls i.e. offset: 0 limit: 1000 = total 2420, offset: 1000 limit: 1000 = total 2408 or 2426 could go up or down.
    # This is handled in Response __add__ method.
    async def get_events(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        client_mac: str = None,
        bssid: str = None,
        device_mac: str = None,
        hostname: str = None,
        device_type: constants.EventDeviceTypes = None,
        sort: str = None,
        site: str = None,
        serial: str = None,
        level: str = None,
        event_description: str = None,
        event_type: str = None,
        fields: str = None,
        calculate_total: bool = True,
        offset: int = 0,
        limit: int = 1000,
        count: int = None,
    ) -> Response:
        """Get device events

        Endpoint allows a max of 10,000 records to be retrieved.  The sum of offset + limit can not
        exceed 10,000

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_time: (int | float | datetime, optional): Start time of the event logs to retrieve.
                Default is current timestamp minus 3 hours.
            to_time (int | float | datetime, optional): End time of the event logs to retrieve.
                seconds. Default is current timestamp.
            client_mac (str, optional): Filter by client MAC address
            bssid (str, optional): Filter by bssid
            device_mac (str, optional): Filter by device_mac
            hostname (str, optional): Filter by hostname
            device_type (str, optional): Filter by device type.
                Valid Values: ap, gw, switch, client
            sort (str, optional): Sort by desc/asc using -timestamp/+timestamp. Default is
                '-timestamp'  Valid Values: -timestamp, +timestamp
            site (str, optional): Filter by site name
            serial (str, optional): Filter by switch serial number
            level (str, optional): Filter by event level
            event_description (str, optional): Filter by event description
            event_type (str, optional): Filter by event type
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                number, level
            calculate_total (bool, optional): Whether to calculate total events. Defaults to True.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 1000.
            count: Only return <count> results.

        Returns:
            Response: CentralAPI Response object
        """
        # sort needs to stay as default -timestamp for count to grab most recent events.
        url = "/monitoring/v2/events"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        if offset + limit > 10_000:
            if offset >= 10_000:
                log.error(f"get_events provided {offset=}, {limit=} endpoint allows max 10,000", show=True, log=True, caption=True)
                return Response()
            log.warning(f"get_events provided {offset=}, {limit=} adjusted limit to {10_000 - offset} to stay below max 10,000")
            limit = 10_000 - offset

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "from_timestamp": from_time,
            "to_timestamp": to_time,
            'macaddr': client_mac,
            'bssid': bssid,
            'device_mac': device_mac,
            'hostname': hostname,
            'device_type':  None if not device_type else constants.lib_to_api(device_type, "event"),
            'sort': sort,
            'site': site,
            'serial': serial,
            'level': level,
            'event_description': event_description,
            'event_type': event_type,
            'fields': fields,
            'calculate_total': str(calculate_total),
            "offset": offset,
            "limit": limit if not count or limit < count else count,
        }

        return await self.get(url, params=params, count=count)

    async def get_all_webhooks(self) -> Response:
        """List all defined webhooks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"

        return await self.get(url)

    async def add_webhook(
        self,
        name: str,
        urls: List[str],
    ) -> Response:
        """Add / update Webhook.

        Args:
            name (str): name of the webhook
            urls (List[str]): List of webhook urls

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"
        urls = utils.listify(urls)

        json_data = {
            'name': name,
            'urls': urls
        }

        return await self.post(url, json_data=json_data)

    async def update_webhook(
        self,
        wid: str,
        name: str,
        urls: List[str],
    ) -> Response:
        """Update webhook settings.

        Args:
            wid (str): id of the webhook
            name (str): name of the webhook
            urls (List[str]): List of webhook urls

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        json_data = {
            'name': name,
            'urls': urls
        }

        return await self.put(url, json_data=json_data)

    async def delete_webhook(
        self,
        wid: str,
    ) -> Response:
        """Delete Webhooks.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        return await self.delete(url)

    async def refresh_webhook_token(
        self,
        wid: str,
    ) -> Response:
        """Refresh the webhook token.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/token"

        return await self.put(url)

    # API-FLAW Test webhook does not send an "id", it's how you determine what to Close
    async def test_webhook(
        self,
        wid: str,
    ) -> Response:
        """Test for webhook notification.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/ping"

        return await self.get(url)

    async def get_site_vlans(self, site_id: int, search: str = None, offset: int = 0, limit: int = 100) -> Response:
        """Get vlan list of a site.

        Args:
            site_id (int): Site ID.
            search (str, optional): search.
            offset (int, optional): offset. Defaults to 0.
            limit (int, optional): limit Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/vlans/{site_id}"

        params = {"search": search, "offset": offset, "limit": limit}

        return await self.get(url, params=params)

    async def send_bounce_command_to_device(self, serial: str, command: str, port: str) -> Response:
        """Bounce interface or POE (power-over-ethernet) on switch port.  Valid only for Aruba Switches.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
            port (str): Specify interface port in the format of port number for devices of type HPPC
                Switch or slot/chassis/port for CX Switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v2/device/{serial}/action/{command}"

        json_data = {"port": str(port)}

        return await self.post(url, json_data=json_data)

    async def send_command_to_device(
        self,
        serial: str,
        command: Literal[
            "reboot",
            "blink_led_on",
            "blink_led_off",
            "blink_led",
            "erase_configuration",
            "save_configuration",
            "halt",
            "config_sync",
        ],
        duration: int = None,
    ) -> Response:
        """Generic commands for device.

        Supported Commands (str):
            - reboot: supported by AP/gateways/MAS Switches/Aruba Switches
            - blink_led_on: Use this command to enable the LED display, supported by IAP/Aruba Switches
            - blink_led_off: Use this command to enable the LED display, supported by IAP/Aruba Switches
            - blink_led: Use this command to blink LED display, Supported on Aruba Switches
            - erase_configuration : Factory default the switch.  Supported on Aruba Switches
            - save_configuration: Saves the running config. supported by IAP/Aruba Switches
            - halt : This command performs a shutdown of the device, supported by Controllers alone.
            - config_sync : This commands performs full refresh of the device config, supported by Controllers alone

        Args:
            serial (str): Serial of device
            command (str): Command to be executed
            duration (int, Optional): Number of seconds to blink_led only applies to blink_led and blink_led_on

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}"

        # TODO cacth invalid actions (not supported on dev)
        resp = await self.post(url)
        if resp and duration and "blink_led" in command and "off" not in command:
            print(f"Blinking Led... {duration}. ", end="")
            for i in range(1, duration + 1):
                time.sleep(1)
                print(f"{duration - i}. ", end="" if i % 20 else "\n")
            resp = await self.post(url.replace("_on", "_off"))
        return resp

    async def kick_users(
        self,
        serial: str = None,
        *,
        kick_all: bool = False,
        mac: str = None,
        ssid: str = None,
    ) -> Response:
        url = f"/device_management/v1/device/{serial}/action/disconnect_user"
        if kick_all:
            payload = {"disconnect_user_all": True}
        elif mac:
            payload = {"disconnect_user_mac": f"{mac}"}
        elif ssid:
            payload = {"disconnect_user_network": f"{ssid}"}
        else:
            payload = {}

        if payload:
            return await self.post(url, json_data=payload)
        else:
            return Response(error="Missing Required Parameters")

    async def get_task_status(
        self,
        task_id: str,
    ) -> Response:
        """Status.

        Args:
            task_id (str): Unique task id to get response of command

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/status/{task_id}"

        return await self.get(url)

    async def get_switch_vlans(
        self,
        iden: str,
        stack: bool = False,
        name: str = None,
        pvid: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = True,
        aos_sw: bool = False,
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """Get vlan info for switch (CX and SW).

        Args:
            iden (str): Serial Number or Stack ID, Identifies the dev to return VLANs from.
            stack (bool, optional): Set to True for stack. Default: False
            name (str, optional): Filter by vlan name
            id (int, optional): Filter by vlan id
            tagged_port (str, optional): Filter by tagged port name
            untagged_port (str, optional): Filter by untagged port name
            is_jumbo_enabled (bool, optional): Filter by jumbo enabled
            is_voice_enabled (bool, optional): Filter by voice enabled
            is_igmp_enabled (bool, optional): Filter by igmp enabled
            type (str, optional): Type of the vlan to be queried
            primary_vlan_id (int, optional): Primary Vlan Id of the vlan to be queried"
            status (str, optional): Filter by status of VLAN. Status can be Up/Down
            sort (str, optional): Sort parameter may be one of +name, -name
            calculate_total (bool, optional): Whether to calculate total vlans
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        sw_url = "switches" if not stack else "switch_stacks"
        sw_url = sw_url if aos_sw else f'cx_{sw_url}'
        url = f"/monitoring/v1/{sw_url}/{iden}/vlan"

        params = {
            "name": name,
            "id": pvid,
            "tagged_port": tagged_port,
            "untagged_port": untagged_port,
            "is_jumbo_enabled": is_jumbo_enabled,
            "is_voice_enabled": is_voice_enabled,
            "is_igmp_enabled": is_igmp_enabled,
            "type": type,
            "primary_vlan_id": primary_vlan_id,
            "status": status,
            "sort": sort,
            "calculate_total": None if not calculate_total else str(calculate_total),  # sending str of False/false will be interpreted as true.  None will strip the param
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

    async def get_gateway_vlans(self, serial: str) -> Response:
        """Get gateway VLAN details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/vlan"

        return await self.get(url)

    async def get_ts_commands(
        self,
        device_type: constants.DeviceTypes,
    ) -> Response:
        """List Troubleshooting Commands.

        Args:
            device_type (Literal['ap', 'cx', 'sw', 'gw']): Device Type.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/troubleshooting/v1/commands"

        params = {
            'device_type': constants.lib_to_api(device_type, "tshoot")
        }

        return await self.get(url, params=params)


    async def start_ts_session(
        self,
        serial: str,
        device_type: constants.DeviceTypes,
        commands: int | List[int, dict] | dict,
    ) -> Response:
        """Start Troubleshooting Session.

        Args:
            serial (str): Serial of device
            device_type (Literal['ap', 'cx', 'sw', 'gw']): Device Type.
            commands (int | List[int, dict] | dict): a single command_id, or a List of command_ids (For commands with no arguments)
                OR a dict {command_id: {argument1_name: argument1_value, argument2_name: argument2_value}}

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"
        commands = utils.listify(commands)
        cmds = []
        for cmd in commands:
            if isinstance(cmd, int):
                cmds += [{"command_id": cmd}]
            elif isinstance(cmd, dict):
                cmds += [
                    {
                        "command_id": cid,
                        "arguments": [{"name": k, "value": v} for k, v in cmd[cid].items()]
                    }
                    for cid in cmd
                ]

        json_data = {
            'device_type': constants.lib_to_api(device_type, "tshoot"),
            'commands': cmds
        }

        return await self.post(url, json_data=json_data)

    async def get_ts_output(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Get Troubleshooting Output.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        params = {
            'session_id': session_id
        }

        return await self.get(url, params=params)

    async def clear_ts_session(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Clear Troubleshooting Session and output for device.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for each troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        params = {
            'session_id': session_id
        }

        return await self.delete(url, params=params)

    # API-FLAW returns 404 if there are no sessions running
    async def get_ts_session_id(
        self,
        serial: str,
    ) -> Response:
        """Get Troubleshooting Session ID for a device.

        Args:
            serial (str): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/session"

        return await self.get(url)

    async def get_sdwan_dps_policy_compliance(self, time_frame: str = "last_week", order: str = "best") -> Response:
        url = "/sdwan-mon-api/external/noc/reports/wan/policy-compliance"
        params = {"period": time_frame, "result_order": order, "count": 250}
        return await self.get(url, params=params)

    async def get_topo_for_site(
        self,
        site_id: int,
    ) -> Response:
        """Get topology details of a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/{site_id}"

        return await self.get(url)

    async def get_ap_lldp_neighbor(self, serial: str) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{serial}"

        return await self.get(url)

    async def get_cx_switch_neighbors(
        self,
        serial: str,
    ) -> Response:
        """Get lldp device neighbor info for CX switch.

        If used on AOS-SW will only return neighbors that are CX switches
        For a stack this will return neighbors for the individual member
        use get_cx_switch_stack_neighbors to get neighbors for entire stack

        Args:
            serial (str): id of the switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/neighbors"

        return await self.get(url)

    async def get_cx_switch_stack_neighbors(
        self,
        stack_id: str,
    ) -> Response:
        """Get lldp device neighbor info for CX switch stack.

        Args:
            stack_id (str): Filter by stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switch_stacks/{stack_id}/neighbors"

        return await self.get(url)

    async def get_switch_vsx_detail(
        self,
        serial: str,
    ) -> Response:
        """Get switch vsx info for CX switch.

        Args:
            serial (str): Filter by switch serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/vsx"

        return await self.get(url)

    async def do_multi_group_snapshot(
        self,
        backup_name: str,
        include_groups: List[str] = None,
        exclude_groups: List[str] = None,
        do_not_delete: bool = False,
    ) -> Response:
        """Create new configuration backup for multiple groups.

        Either include_groups or exclude_groups should be provided, but not both.

        Args:
            backup_name (str): Name of Backup
            include_groups (List[str], optional): Groups to include in Backup. Defaults to None.
            exclude_groups (List[str], optional): Groups to Exclude in Backup. Defaults to None.
            do_not_delete (bool, optional): Flag to represent if the snapshot can be deleted automatically
                by system when creating new snapshot or not. Defaults to False.


        Returns:
            Response: Response Object
        """
        url = "/configuration/v1/groups/snapshot/backups"
        include_groups = utils.listify(include_groups)
        exclude_groups = utils.listify(exclude_groups)
        payload = {
            "backup_name": backup_name,
            "do_not_delete": do_not_delete,
            "include_groups": include_groups,
            "exclude_groups": exclude_groups,
        }
        payload = self.strip_none(payload)
        return await self.post(url, json_data=payload)

    async def get_snapshots_by_group(self, group: str):
        url = f"/configuration/v1/groups/{group}/snapshots"
        return await self.get(url)

    async def get_gw_tunnels(
        self, serial: str,
        timerange: constants.TimeRange = "1m",
        limit: int = 250,
        offset: int = 0
    ) -> Response:
        """Get gateway Uplink tunnel details.

        Used by wh_proxy, currently not used by a command will be in show gateway tunnels

        Args:
            serial (str): Serial number of mobility controller to be queried
            timerange (str): Time range for tunnel stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
            limit (int, optional): Pagination limit. Max: 1000 Defaults to 250.
            offset (int, optional): Pagination offset Defaults to 0.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/tunnels"

        params = {
            "timerange": timerange.upper(),
            "offset": offset,
            "limit": limit
        }

        return await self.get(url, params=params)


    async def get_gw_uplinks_details(
        self,
        serial: str,
        timerange: constants.TimeRange = "1m",
    ) -> Response:
        """Gateway Uplink Details.

        Args:
            serial (str): Serial number of gateway to be queried
            timerange (str): Time range for Uplink stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
                Valid Values: 3H, 1D, 1W, 1M, 3M

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks"

        params = {
            'timerange': timerange.upper()
        }

        return await self.get(url, params=params)

    async def get_gw_uplinks_bandwidth_usage(
        self,
        serial: str,
        uplink_id: str = None,
        interval: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """Gateway Uplink Bandwidth Usage.

        Args:
            serial (str): Gateway serial
            uplink_id (str, optional): Filter by uplink ID.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)


        params = {
            'uplink_id': uplink_id,
            'interval': interval,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.get(url, params=params)

    async def get_switch_ports_bandwidth_usage(
        self,
        serial: str,
        switch_type: Literal["cx", "sw"] = "cx",
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        port: str = None,
        show_uplink: bool = None,
    ) -> Response:
        """Ports Bandwidth Usage for Switch.

        Args:
            serial (str): Serial number of switch to be queried
            switch_type: (Literal["cx", "sw"], optional) = switch type. Valid 'cx', 'sw'.  Defaults to 'cx'
            from (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            show_uplink (bool, optional): Show usage for Uplink ports alone

        Returns:
            Response: CentralAPI Response object
        """
        if show_uplink in [True, False]:
            show_uplink = str(show_uplink).lower()

        url = f"/monitoring/v1/{'cx_' if switch_type == 'cx' else ''}switches/{serial}/ports/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'port': port,
            'show_uplink': show_uplink
        }

        return await self.get(url, params=params)

    #  TODO add monitoring_external_controller_get_ap_rf_summary_v3 similar to bandwidth calls, "samples" key has timestamp, noise_floor, and utilization.

    async def get_aps_bandwidth_usage(
        self,
        serial: str = None,
        group: str = None,
        site: str = None,
        label: str = None,
        swarm_id: str = None,
        cluster_id: str = None,
        band: str = None,
        radio_number: int = None,
        network: str = None,
        ethernet_interface_index: int = None,
        interval: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """AP Bandwidth Usage.

        Args:
            serial (str, optional): Filter by AP serial
            group (str, optional): Filter by group name
            site (str, optional): Filter by Site name
            label (str, optional): Filter by Label name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band (2.4, 5 or 6). Valid only when serial parameter is
                specified.
            radio_number (int, optional): Filter by radio_number (0, 1 or 2). Valid only when serial
                parameter is specified.
            network (str, optional): Filter by network name. Valid only when serial parameter is
                specified.
            ethernet_interface_index (int, optional): Filter by ethernet interface index. Valid only
                when serial parameter is specified. Valid range is 0-3.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
                API endpoint defaults to 5minutes when no value is provided.
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v3/aps/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'serial': serial,
            'cluster_id': cluster_id,
            'interval': interval,
            'band': band,
            'radio_number': radio_number,
            'ethernet_interface_index': ethernet_interface_index,
            'network': network,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.get(url, params=params)

    async def get_networks_bandwidth_usage(
        self,
        network: str,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """WLAN Network Bandwidth usage.

        Use get_wlans to fetch list of networks.

        Args:
            network (str): Network name (ssid) to return usage for
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'network': network,
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.get(url, params=params)

    async def get_clients_bandwidth_usage(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        serial: str = None,
        mac: str = None,
        from_time: int = None,
        to_time: int = None,
    ) -> Response:
        """Client Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            serial (str, optional): Filter by switch serial
            mac (str, optional): Filter by Client mac
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'serial': serial,
            'macaddr': mac,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.get(url, params=params)

    # API-FLAW max limit 100 enforced if you provide the limit parameter, otherwise no limit? returned 811 w/ no param provided
    async def get_audit_logs(
        self,
        log_id: str = None,
        username: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        description: str = None,
        target: str = None,
        classification: str = None,
        customer_name: str = None,
        ip_address: str = None,
        app_id: str = None,
        offset: int = 0,
        limit: int = 100,
        count: int = None,
    ) -> Response:
        """Get all audit logs.

        This API returns the first 10,000 results only.

        Args:
            log_id (str, optional): The id of the log to return details for. Defaults to None.
            username (str, optional): Filter audit logs by User Name
            from_time (int | float | datetime, optional): Start time of the audit logs to retrieve.
            to_time (int | float | datetime, optional): End time of the audit logs to retrieve.
            description (str, optional): Filter audit logs by Description
            target (str, optional): Filter audit logs by target (serial number).
            classification (str, optional): Filter audit logs by Classification
            customer_name (str, optional): Filter audit logs by Customer Name
            ip_address (str, optional): Filter audit logs by IP Address
            app_id (str, optional): Filter audit logs by app_id
            offset (int, optional): Number of items to be skipped before returning the data.
                Default to 0.
            limit (int, optional): Maximum number of audit events to be returned max: 100
                Defaults to 100.
            count: Only return <count> results.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/auditlogs/v1/logs"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            "username": username,
            "start_time": from_time,
            "end_time": to_time,
            "description": description,
            "target": target,
            "classification": classification,
            "customer_name": customer_name,
            "ip_address": ip_address,
            "app_id": app_id if not hasattr(app_id, "value") else app_id.value,
            "offset": offset,
            "limit": limit if not count or limit < count else count,
        }

        if log_id:
            url = f"{url}/{log_id}"
            params = {}

        return await self.get(url, params=params, count=count)

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

        return await self.get(url, params={} if log_id else params, count=count)

    async def create_site(
        self,
        site_name: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        country: str = None,
        zipcode: int | str = None,
        latitude: float = None,
        longitude: float = None,
        site_list: List[Dict[str, str | dict]] = None,  # TODO TypedDict
    ) -> Response:
        """Create Site

        Either address information or GeoLocation information is required.  For Geolocation attributes
        all attributes are required.  Or a List[dict] with multiple sites to be added containing either
        'site_address' or 'geolocation' attributes for each site.

        Args:
            site_name (str, optional): Site Name. Defaults to None.
            address (str, optional): Address. Defaults to None.
            city (str, optional): City. Defaults to None.
            state (str, optional): State. Defaults to None.
            country (str, optional): Country Name. Defaults to None.
            zipcode (int | str, optional): Zipcode. Defaults to None.
            latitude (float, optional): Latitude (in the range of -90 and 90). Defaults to None.
            longitude (float, optional): Longitude (in the range of -100 and 180). Defaults to None.
            site_list (List[Dict[str, str | dict]], optional): A list of sites to be created. Defaults to None.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"
        zipcode = None if not zipcode else str(zipcode)
        latitude = None if not latitude else str(latitude)
        longitude = None if not longitude else str(longitude)

        address_dict = utils.strip_none({"address": address, "city": city, "state": state, "country": country, "zipcode": zipcode})
        geo_dict = utils.strip_none({"latitude": latitude, "longitude": longitude})
        json_data = {"site_name": site_name}
        if address_dict:
            json_data["site_address"] = address_dict
        if geo_dict:
            json_data["geolocation"] = geo_dict

        # TODO revert this to single site add and use batch_add_site method for multi-add
        if site_list:
            resp = await self.post(url, json_data=site_list[0])
            if not resp:
                return resp
            if len(site_list) > 1:
                ret = await self._batch_request(
                    [
                        self.BatchRequest(self.post, url, json_data=_json, callback=cleaner._unlist)
                        for _json in site_list[1:]
                    ]
                )
                return [resp, *ret]
        else:
            return await self.post(url, json_data=json_data, callback=cleaner._unlist)  # TODO remove callback

    async def update_site(
        self,
        site_id: int,
        site_name: str,
        address: str = None,
        city: str = None,
        state: str = None,
        zipcode: str = None,
        country: str = None,
        latitude: str = None,
        longitude: str = None,
    ) -> Response:
        """Update Site.

        Provide geo-loc or address details, not both.
        Can provide both in subsequent calls, but apigw does not
        allow both in same call.

        Args:
            site_id (int): Site ID
            site_name (str): Site Name
            address (str): Address
            city (str): City Name
            state (str): State Name
            zipcode (str): Zipcode
            country (str): Country Name
            latitude (str): Latitude (in the range of -90 and 90)
            longitude (str): Longitude (in the range of -180 and 180)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"
        if zipcode:
            zipcode = str(zipcode)


        site_address = {"address": address, "city": city, "state": state, "country": country, "zipcode": zipcode}
        geolocation = {"latitude": latitude, "longitude": longitude}

        site_address = utils.strip_none(site_address)
        geolocation = utils.strip_none(geolocation)

        json_data = {
            "site_name": site_name,
            "site_address": site_address,
            "geolocation": geolocation
        }

        return await self.patch(url, json_data=json_data)

    # TODO all params required by API GW, need call to get current properties
    # if not all are provided
    async def update_ap_system_config(
        self,
        scope: str,
        dns_server: str = None,
        ntp_server: List[str] = None,
        username: str = None,
        password: str = None,
    ) -> Response:
        """Update system config.

        All params are required by Aruba Central

        Args:
            scope (str): Group name of the group or swarm_id.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            dns_server (str): DNS server IPs or domain name
            ntp_server (List[str]): List of ntp server,
                Example: ["192.168.1.1", "127.0.0.0", "xxx.com"].
                IPs or domain name.
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{scope}"

        json_data = utils.strip_none(
            {
                'dns_server': dns_server,
                'ntp_server': ntp_server,
                'username': username,
                'password': password
            }
        )

        return await self.post(url, json_data=json_data)

    async def create_group(
        self,
        group: str,
        allowed_types: constants.LibAllDevTypes | List[constants.LibAllDevTypes] = ["ap", "gw", "cx", "sw"],
        wired_tg: bool = False,
        wlan_tg: bool = False,
        aos10: bool = False,
        microbranch: bool = False,
        gw_role: constants.BranchGwRoleTypes = None,
        monitor_only_sw: bool = False,
        monitor_only_cx: bool = False,
        cnx: bool = False,
    ) -> Response:
        """Create new group with specified properties. v3

        Args:
            group (str): Group Name
            allowed_types (str, List[str]): Allowed Device Types in the group. Tabs for devices not allowed
                won't display in UI.  valid values "ap", "gw", "cx", "sw", "switch", "sdwan"
                ("switch" is generic, will enable both cx and sw)
                When sdwan (EdgeConnect SD-WAN) is allowed, it has to be the only type allowed.
            wired_tg (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            wlan_tg (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.
            aos10: (bool): if True use AOS10 architecture for the access points and gateways in the group.
                default False (Instant)
            microbranch (bool): True to enable Microbranch network role for APs is applicable only for AOS10 architecture.
            gw_role (GatewayRole): Gateway role valid values "branch", "vpnc", "wlan" ("wlan" only valid on AOS10 group)
                Defaults to None.  Results in "branch" unless "sdwan" is in allowed_types otherwise "vpnc".
            monitor_only_sw: Monitor only ArubaOS-SW switches, applies to UI group only
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only
            cnx (bool, optional): Make group compatible with cnx (New Central)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v3/groups"

        gw_role_dict = {
            "branch": "BranchGateway",
            "vpnc": "VPNConcentrator",
            "wlan": "WLANGateway",
            "sdwan": "VPNConcentrator"
        }
        dev_type_dict = {
            "ap": "AccessPoints",
            "gw": "Gateways",
            "switch": "Switches",
            "cx": "Switches",
            "sw": "Switches",
            "sdwan": "SD_WAN_Gateway",
        }

        gw_role = gw_role_dict.get(gw_role, "BranchGateway")

        allowed_types = utils.listify(allowed_types)
        allowed_switch_types = []
        if "switch" in allowed_types or ("cx" in allowed_types and "sw" in allowed_types):
            allowed_switch_types += ["AOS_CX", "AOS_S"]
        if "sw" in allowed_types and "AOS_S" not in allowed_switch_types:
            allowed_switch_types += ["AOS_S"]
        if "cx" in allowed_types and "AOS_CX" not in allowed_switch_types:
            allowed_switch_types += ["AOS_CX"]

        mon_only_switches = []
        if monitor_only_sw:
            mon_only_switches += ["AOS_S"]
        if monitor_only_cx:
            mon_only_switches += ["AOS_CX"]

        allowed_types = list(set([dev_type_dict.get(t) for t in allowed_types]))

        if mon_only_switches and "Switches" not in allowed_types:
            log.warning("ignoring monitor only switch setting as no switches were specified as being allowed in group", show=True)

        if None in allowed_types:
            raise ValueError('Invalid device type for allowed_types valid values: "ap", "gw", "sw", "cx", "switch", "sdwan')
        elif "sdwan" in allowed_types and len(allowed_types) > 1:
            raise ValueError('Invalid value for allowed_types.  When sdwan device type is allowed, it must be the only type allowed for the group')
        if microbranch:
            if not aos10:
                raise ValueError("Invalid combination, Group must be configured as AOS10 group to support Microbranch")
            if "Gateways" in allowed_types:
                raise ValueError("Gateways cannot be present in a group with microbranch network role set for Access points")
        if wired_tg and (monitor_only_sw or monitor_only_cx):
            raise ValueError("Invalid combination, Monitor Only is not valid for Template Group")

        json_data = {
            "group": group,
            "group_attributes": {
                "template_info": {
                    "Wired": wired_tg,
                    "Wireless": wlan_tg
                },
                "group_properties": {
                    "AllowedDevTypes": allowed_types,
                    "NewCentral": cnx,
                }
            }
        }
        if "SD_WAN_Gateway" in allowed_types:
            # SD_WAN_Gateway requires Architecture and GwNetworkRole (VPNConcentrator)
            json_data["group_attributes"]["group_properties"]["GwNetworkRole"] = "VPNConcentrator"
            json_data["group_attributes"]["group_properties"]["Architecture"] = "SD_WAN_Gateway"
        elif "Gateways" in allowed_types:
            json_data["group_attributes"]["group_properties"]["GwNetworkRole"] = gw_role
            json_data["group_attributes"]["group_properties"]["Architecture"] = \
                "Instant" if not aos10 else "AOS10"
        if "AccessPoints" in allowed_types:
            json_data["group_attributes"]["group_properties"]["ApNetworkRole"] = \
                "Standard" if not microbranch else "Microbranch"
            json_data["group_attributes"]["group_properties"]["Architecture"] = \
                "Instant" if not aos10 else "AOS10"
        if "Switches" in allowed_types:
            json_data["group_attributes"]["group_properties"]["AllowedSwitchTypes"] = \
                allowed_switch_types
            if mon_only_switches:
                json_data["group_attributes"]["group_properties"]["MonitorOnly"] = \
                    mon_only_switches

        return await self.post(url, json_data=json_data)

    async def clone_group(
        self,
        clone_group: str,
        new_group: str,
        upgrade_aos10: bool = False,
    ) -> Response:
        """Clone and create new group.

        Args:
            clone_group (str): Group to be cloned.
            new_group (str): Name of group to be created based on clone.
            upgrade_aos10 (bool): Set True to Update the new cloned group to AOS10.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups/clone"

        if upgrade_aos10:
            log.warning(
                "Group may not be upgraded to AOS10, API method appears to have some caveats... Doesn't always work."
            )

        json_data = {
            'group': new_group,
            'clone_group': clone_group,
            'upgrade_architecture': upgrade_aos10,
        }

        return await self.post(url, json_data=json_data)

    # API-FLAW add ap and gw to group with gw-role as wlan and upgrade to aos10.  Returns 200, but no changes made
    # TODO need to add flag for SD_WAN_Gateway architecture (Silver Peak), only valid associated GwNetworkRole is VPNConcentrator
    # TODO need to add SD_WAN_Gateway to AllowedDevTypes
    async def update_group_properties(
        self,
        group: str,
        allowed_types: constants.AllDevTypes | List[constants.AllDevTypes] = None,
        wired_tg: bool = None,
        wlan_tg: bool = None,
        aos10: bool = None,
        microbranch: bool = None,
        gw_role: constants.GatewayRole = None,
        monitor_only_sw: bool = None,
        monitor_only_cx: bool = None,
    ) -> Response:
        """Update properties for the given group.

        // Used by update group //

        - The update of persona and configuration mode set for existing device types is not permitted.
        - Can update from standard AP to MicroBranch, but can't go back
        - Can update to AOS10, but can't go back
        - Can Add Allowed Device Types, but can't remove.
        - Can Add Allowed Switch Types, but can't remove.
        - Can only change mon_only_sw and wired_tg when adding switches (cx, sw) to allowed_device_types


        Args:
            group (str): Group Name
            allowed_types (str, List[str]): Allowed Device Types in the group. Tabs for devices not allowed
                won't display in UI.  valid values "ap", "gw", "cx", "sw", "switch"
                ("switch" is generic, will enable both cx and sw)
            wired_tg (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            wlan_tg (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.
            aos10: (bool): if True use AOS10 architecture for the access points and gateways in the group.
                default False (Instant)
            microbranch (bool): True to enable Microbranch network role for APs is applicable only for AOS10 architecture.
            gw_role (GatewayRole): Gateway role valid values "branch", "vpnc", "wlan" ("wlan" only valid on AOS10 group)
            monitor_only_sw: Monitor only ArubaOS-SW switches, applies to UI group only
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/groups/{group}/properties"

        resp = await self.get_groups_properties(group)
        if resp:
            if not isinstance(resp.output, list):
                raise ValueError(f"Expected list of dicts from get_groups_properties got {type(resp.output)}")
            cur_group_props = resp.output[-1]["properties"]
        else:
            log.error(f"Unable to perform call to update group {group} properties.  Call to get current properties failed.")
            return resp

        if cur_group_props["AOSVersion"] == "AOS_10X" and aos10 is False:
            return Response(
                error=f"{group} is currently an AOS10 group.  Upgrading to AOS10 is supported, reverting back is not.",
                rl_str=resp.rl,
            )
        if aos10 is True:
            if "AccessPoints" in cur_group_props["AllowedDevTypes"] or \
                "Gateways" in cur_group_props["AllowedDevTypes"]:
                return Response(
                    error=f"{color('AOS10')} can only be set when APs or GWs are initially added to allowed_types of group"
                          f"\n{color(group)} can be cloned with option to upgrade during clone.",
                    rl_str=resp.rl,
                )

        if "AccessPoints" in cur_group_props["AllowedDevTypes"]:
            if microbranch is not None:
                return Response(
                    error=f"{group} already allows APs.  Microbranch/Standard AP can only be set "
                          "when initially adding APs to allowed_types of group",
                    rl_str=resp.rl,
                )
        if monitor_only_sw is False and "AOS_S" in cur_group_props["AllowedSwitchTypes"]:
            return Response(
                error=f"{group} already allows AOS-SW.  Monitor Only can only be set "
                      "when initially adding AOS-SW to allowed_types of group",
                rl_str=resp.rl,
            )
        if monitor_only_cx is False and "AOS_CX" in cur_group_props["AllowedSwitchTypes"]:
            return Response(
                error=f"{group} already allows AOS-CX.  Monitor Only can only be set "
                      "when initially adding AOS-CX to allowed_types of group",
                rl_str=resp.rl,
            )

        allowed_types = allowed_types or []
        allowed_switch_types = []
        if allowed_types:
            allowed_types = utils.listify(allowed_types)
            if "switch" in allowed_types or ("cx" in allowed_types and "sw" in allowed_types):
                allowed_switch_types += ["AOS_CX", "AOS_S"]
            elif "sw" in allowed_types:
                allowed_switch_types += ["AOS_S"]
            elif "cx" in allowed_types:
                allowed_switch_types += ["AOS_CX"]

        # TODO copy paste from create group ... common func to build payload
        gw_role_dict = {
            "branch": "BranchGateway",
            "vpnc": "VPNConcentrator",
            "wlan": "WLANGateway",
        }
        dev_type_dict = {
            "ap": "AccessPoints",
            "gw": "Gateways",
            "switch": "Switches",
            "cx": "Switches",
            "sw": "Switches",
        }
        gw_role = gw_role_dict.get(gw_role)

        mon_only_switches = []
        if monitor_only_sw:
            mon_only_switches += ["AOS_S"]
        if monitor_only_cx:
            mon_only_switches += ["AOS_CX"]

        arch = None
        if microbranch is not None:
            if aos10 is not None:
                arch = "Instant" if not aos10 else "AOS10"

        allowed_types = list(set([dev_type_dict.get(t) for t in allowed_types]))
        combined_allowed = [*allowed_types, *cur_group_props["AllowedDevTypes"]]

        if None in allowed_types:
            return Response(
                error='Invalid device type for allowed_types valid values: "ap", "gw", "sw", "cx", "switch"',
                rl_str=resp.rl,
            )
        if microbranch and not aos10:
            return Response(
                error="Invalid combination, Group must be configured as AOS10 group to support Microbranch",
                rl_str=resp.rl,
            )
        if microbranch and "AccessPoints" not in combined_allowed:
            return Response(
                error=f"Invalid combination, {color('Microbranch')} "
                      f"can not be enabled in group {color(group)}.  "
                      "APs must be added to allowed devices.\n"
                      f"[reset]Current Allowed Devices: {color(combined_allowed)}",
                rl_str=resp.rl,
            )
        if wired_tg and monitor_only_sw:
            return Response(
                error="Invalid combination, Monitor Only is not valid for Template Group",
                rl_str=resp.rl,
            )

        grp_props = {
            "AllowedDevTypes": combined_allowed,
            "Architecture": arch or cur_group_props.get("Architecture"),
            "AllowedSwitchTypes": allowed_switch_types or cur_group_props.get("AllowedSwitchTypes", []),
            "MonitorOnly": mon_only_switches or cur_group_props.get("MonitorOnlySwitch")
        }
        grp_props = {k: v for k, v in grp_props.items() if v}

        if gw_role and "Gateways" in allowed_types:
            grp_props["GwNetworkRole"] = gw_role
        if "AccessPoints" in allowed_types or "AccessPoints" in cur_group_props["AllowedDevTypes"]:
            if microbranch is not None:
                grp_props["ApNetworkRole"] = \
                    "Standard" if not microbranch else "Microbranch"

        tmplt_info = {
            "Wired": wired_tg,
            "Wireless": wlan_tg
        }
        tmplt_info = utils.strip_none(tmplt_info)

        grp_attrs = {}
        if tmplt_info:
            grp_attrs["template_info"] = tmplt_info
        if grp_props:
            grp_attrs["group_properties"] = {
                **{k: v for k, v in cur_group_props.items() if k not in ["AOSVersion", "MonitorOnly"]},
                **grp_props
            }
        json_data = grp_attrs

        if config.debugv:
            print(f"[DEBUG] ---- Sending the following to {url}")
            utils.json_print(json_data)
            print("[DEBUG] ----")

        return await self.patch(url, json_data=json_data)


    async def update_group_name(self, group: str, new_group: str) -> Response:
        """Update group name for the given group.

        Args:
            group (str): Group for which name need to be updated.
            new_group (str): The new name of the group.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO report flawed API method
        # This works for renaming 8x groups
        # if you try to rename a 10x group inappropriate error:
        # [
        #     {
        #         "description": "group already has AOS_10X version set",
        #         "error_code": "0001",
        #         "service_name": "Configuration"
        #     }
        # ]
        # I did try w/ full payload similar to get_group props resp
        # i.e.
        # {
        #     "group": "new_name",
        #     "properties": {
        #         "AOSVersion": "AOS_10X",  <- tried specifying group is already 10x
        #         "MonitorOnlySwitch": False
        #     }
        # }
        url = f"/configuration/v1/groups/{group}/name"

        json_data = {
            'group': new_group
        }

        return await self.patch(url, json_data=json_data)

    async def get_ap_settings(self, serial: str) -> Response:
        """Get an existing ap settings.

        Args:
            serial (str): AP serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial}"

        return await self.get(url)

    # API-FLAW no option for 6G radio currently
    # disable radio via UI and ap_settings uses radio-0-disable (5G), radio-1-disable (2.4G), radio-2-disable (6G)
    # disable radio via API and ap_settings uses dot11a_radio_disable (5G), dot11g_radio_disable(2.4G), no option for (6G)
    # however UI still shows radio as UP (in config, overview shows it down) if changed via the API, it's down in reality, but not reflected in the UI because they use different attributes
    # API doesn't appear to take radio-n-disable, tried it.
    async def update_ap_settings(
        self,
        serial: str,
        hostname: str = None,
        ip_address: str = None,
        zonename: str = None,
        achannel: str = None,
        atxpower: str = None,
        gchannel: str = None,
        gtxpower: str = None,
        dot11a_radio_disable: bool = None,
        dot11g_radio_disable: bool = None,
        usb_port_disable: bool = None,
    ) -> Response:
        """Update an existing ap settings.

        Args:
            serial (str): AP Serial Number
            hostname (str, optional): hostname
            ip_address (str, optional): ip_address Default (DHCP)
            zonename (str, optional): zonename. Default "" (No Zone)
            achannel (str, optional): achannel
            atxpower (str, optional): atxpower
            gchannel (str, optional): gchannel
            gtxpower (str, optional): gtxpower
            dot11a_radio_disable (bool, optional): dot11a_radio_disable
            dot11g_radio_disable (bool, optional): dot11g_radio_disable
            usb_port_disable (bool, optional): usb_port_disable

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial}"

        _json_data = {
            'hostname': hostname,
            'ip_address': ip_address,
            'zonename': zonename,
            'achannel': achannel,
            'atxpower': atxpower,
            'gchannel': gchannel,
            'gtxpower': gtxpower,
            'dot11a_radio_disable': dot11a_radio_disable,
            'dot11g_radio_disable': dot11g_radio_disable,
            'usb_port_disable': usb_port_disable,
        }
        if None in _json_data.values():
            resp: Response = await self._request(self.get_ap_settings, serial)
            if not resp:
                log.error(f"Unable to update AP settings for AP {serial}, API call to fetch current settings failed (all settings are required).")
                return resp

            json_data = self.strip_none(_json_data)
            if {k: v for k, v in resp.output.items() if k in json_data.keys()} == json_data:
                return Response(url=url, ok=True, output=f"{resp.output.get('hostname', '')}|{serial} Nothing to Update provided AP settings match current AP settings", error="OK",)

            json_data = {**resp.output, **json_data}

        return await self.post(url, json_data=json_data)

    async def get_dirty_diff(
        self,
        group: str,
        offset: int = 0,
        limit: int = 20
    ) -> Response:
        """Get AP dirty diff (config items not pushed) by group.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group config_mode records to be returned.
                Max: 20, Defaults to 20.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dirty_diff/{group}"

        params = {
            'offset': offset,
            'limit': limit if limit <= 20 else 20
        }

        return await self.get(url, params=params)

    async def get_groups_properties(self, groups: str | List[str] = None) -> Response:
        """Get properties set for groups.

        // Used by show groups when -v flag is provided //

        Args:
            groups (List[str], optional): Group list to fetch properties.
                Will fetch all if no groups provided.
                Maximum 20 comma separated group names allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/properties"

        # Central API method doesn't actually take a list it takes a string with
        # group names separated by comma (NO SPACES)
        if groups is None:
            resp = await self.get_group_names()
            if not resp.ok:
                return resp
            else:
                groups = resp.output

        batch_reqs = []
        for _groups in utils.chunker(utils.listify(groups), 20):  # This call allows a max of 20
            params = {"groups": ",".join(_groups)}
            batch_reqs += [self.BatchRequest(self.get, url, params=params)]
        batch_resp = await self._batch_request(batch_reqs)
        failed = [r for r in batch_resp if not r.ok]
        passed = batch_resp if not failed else [r for r in batch_resp if r.ok]
        if failed:
            log.error(f"{len(failed)} of {len(batch_reqs)} API requests to {url} have failed.", show=True, caption=True)
            fail_msgs = list(set([r.output.get("description", str(r.output)) for r in failed]))
            for msg in fail_msgs:
                log.error(f"Failure description: {msg}", show=True, caption=True)

        # TODO method to combine raw and output attrs of all responses into last resp
        output = [r for res in passed for r in res.output]
        resp = batch_resp[-1] if not passed else passed[-1]
        resp.output = output
        if "data" in resp.raw:
            resp.raw["data"] = output
        else:
            log.warning("raw attr in resp from get_groups_properties lacks expected outer key 'data'")

        return resp

    async def get_vc_firmware(
        self,
        swarm_id: str = None,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Firmware Details of Swarms.

        Args:
            swarm_id: (str, optional): Providing swarm_id results in details for that swarm.
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 100.

            Providing swarm_id is effectively a filter, it provides no additional detail.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/swarms"
        if swarm_id:
            url = f"{url}/{swarm_id}"
            params = {}
        else:
            params = {
                'group': group,
                'offset': offset,
                'limit': limit
            }

        return await self.get(url, params=params)

    async def get_firmware_version_list(
        self,
        device_type: constants.DeviceTypes = None,
        swarm_id: str = None,
        serial: str = None,
    ) -> Response:
        """List Firmware Version.

        Provide one and only one of the following.

        Args:
            device_type (str, optional): Specify one of ap, gw, sw, cx
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/versions"

        if [device_type, swarm_id, serial].count(None) != 2:
            raise ValueError("You must specify one and one of device_type, swarm_id, serial parameters")

        params = {
            'device_type': None if device_type is None else constants.lib_to_api(device_type, "firmware"),
            'swarm_id': swarm_id,
            'serial': serial
        }

        return await self.get(url, params=params)


    async def send_command_to_swarm(
        self,
        swarm_id: str,
        command: Literal[
            "reboot",
            "erase_configuration",
        ]
    ) -> Response:
        """Generic commands for swarm.

        Args:
            swarm_id (str): Swarm ID of device
            command (str): Command mentioned in the description that is to be executed
                valid: 'reboot', 'erase_configuration'

        Returns:
            Response: CentralAPI Response object
        """
        if command == "reboot":
            command = "reboot_swarm"

        url = f"/device_management/v1/swarm/{swarm_id}/action/{command}"

        return await self.post(url)

    async def run_speedtest(
        self,
        serial: str,
        host: str = "ndt-iupui-mlab1-den04.mlab-oti.measurement-lab.org",
        options: str = None
    ) -> Response:
        """Run speedtest from device (gateway only)

        Args:
            serial (str): Serial of device
            host (str, Optional): Speed-Test server IP address, Defaults to server in Central Indiana.
            options (str): Formatted string of optional arguments

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/speedtest"

        json_data = {
            'host': host,
            'options': options or ""
        }

        return await self.post(url, json_data=json_data)

    async def delete_certificate(self, certificate: str) -> Response:
        """Delete existing certificate.

        Args:
            certificate (str): Name of the certificate to delete.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/certificates/{certificate}"

        return await self.delete(url)

    # TODO accept List of str and batch delete
    async def delete_group(self, group: str) -> Response:
        """Delete existing group.

        Args:
            group (str): Name of the group that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}"

        return await self.delete(url)

    async def delete_site(self, site_id: int | List[int]) -> Response | List[Response]:
        """Delete Site.

        Args:
            site_id (int|List[int]): Either the site_id or a list of site_ids to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        b_url = "/central/v2/sites"
        if isinstance(site_id, list):
            return await self._batch_request(
                [
                    self.BatchRequest(self.delete, f"{b_url}/{_id}")
                    for _id in site_id
                ]
            )
        else:
            url = f"{b_url}/{site_id}"
            return await self.delete(url)

    async def delete_wlan(self, group: str, wlan_name: str) -> Response:
        """Delete an existing WLAN.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group}/{wlan_name}"

        return await self.delete(url)

    async def get_wlan(self, group: str, wlan_name: str) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group}/{wlan_name}"

        return await self.get(url)

    async def create_wlan(
        self,
        group: str,
        wlan_name: str,
        wpa_passphrase: str,
        # wpa_passphrase_changed: bool = True,
        vlan: str = "",
        type: constants.WlanType = "employee",
        essid: str = None,
        zone: str = "",
        captive_profile_name: str = "",
        bandwidth_limit_up: str = "",
        bandwidth_limit_down: str = "",
        bandwidth_limit_peruser_up: str = "",
        bandwidth_limit_peruser_down: str = "",
        access_rules: list = DEFAULT_ACCESS_RULES["ALLOW_ALL"],
        is_locked: bool = False,
        hide_ssid: bool = False,
    ) -> Response:
        """Create a new WLAN (SSID).

        Args:
            group (str): Aruba Central Group name or swarm guid
            wlan_name (str): Name of the WLAN/Network
            wpa_passphrase (str): WPA passphrase
            vlan (str): Client VLAN name or id. Defaults to "" (Native AP VLAN).
            type (WlanType, optional): Valid: ['employee', 'guest']. Defaults to "employee".
            essid (str, optional): SSID. Defaults to None (essid = wlan_name).
            zone (str, optional): AP Zone SSID will broadcast on. Defaults to "" (Broadcast on all APs).
            captive_profile_name (str, optional): Captive Portal Profile. Defaults to "" (No CP Profile).
            bandwidth_limit_up (str, optional): [description]. Defaults to "" (No BW Limit Up).
            bandwidth_limit_down (str, optional): [description]. Defaults to "" (No BW Limit Down).
            bandwidth_limit_peruser_up (str, optional): [description]. Defaults to "" (No per user BW Limit Up).
            bandwidth_limit_peruser_down (str, optional): [description]. Defaults to "" (No per user BW Limit Down).
            access_rules (list, optional): [description]. Default: unrestricted.
            is_locked (bool, optional): [description]. Defaults to False.
            hide_ssid (bool, optional): [description]. Defaults to False.
            wpa_passphrase_changed (bool, optional): indicates passphrase has changed. Defaults to True.

        Returns:
            Response: [description]
        """
        url = f"/configuration/v2/wlan/{group}/{wlan_name}"

        json_data = {
            "wlan": {
                'essid': essid or wlan_name,
                'type': type,
                'hide_ssid': hide_ssid,
                'vlan': vlan,
                'zone': zone,
                'wpa_passphrase': wpa_passphrase,
                # 'wpa_passphrase_changed': wpa_passphrase_changed,
                'is_locked': is_locked,
                'captive_profile_name': captive_profile_name,
                'bandwidth_limit_up': bandwidth_limit_up,
                'bandwidth_limit_down': bandwidth_limit_down,
                'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
                'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
                'access_rules': access_rules
            }
        }

        return await self.post(url, json_data=json_data)


    async def update_wlan(
        self,
        scope: str,
        wlan_name: str,
        essid: str = None,
        type: str = None,
        hide_ssid: bool = None,
        vlan: str = None,
        zone: str = None,
        wpa_passphrase: str = None,
        is_locked: bool = None,
        captive_profile_name: str = None,
        bandwidth_limit_up: str = None,
        bandwidth_limit_down: str = None,
        bandwidth_limit_peruser_up: str = None,
        bandwidth_limit_peruser_down: str = None,
        access_rules: list = None,
    ) -> Response:
        """Update an existing WLAN and clean up unsupported fields.

        Args:
            scope (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.
            essid (str): essid
            type (str): type  Valid Values: employee, guest
            hide_ssid (bool): hide_ssid
            vlan (str): vlan
            zone (str): zone
            wpa_passphrase (str): wpa_passphrase
            wpa_passphrase_changed (bool): wpa_passphrase_changed
            is_locked (bool): is_locked
            captive_profile_name (str): captive_profile_name
            bandwidth_limit_up (str): bandwidth_limit_up
            bandwidth_limit_down (str): bandwidth_limit_down
            bandwidth_limit_peruser_up (str): bandwidth_limit_peruser_up
            bandwidth_limit_peruser_down (str): bandwidth_limit_peruser_down
            access_rules (list): access_rules

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{scope}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase is not None,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }
        json_data = {'wlan': utils.strip_none(json_data)}

        return await self.patch(url, json_data=json_data)

    async def move_devices_to_group(
        self,
        group: str,
        serials: str | List[str],
        *,
        cx_retain_config: bool = True,  # TODO can we send this attribute even if it's not CX, will it ignore or error
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): Group Name to move device to.
            serials (str | List[str]): Serial numbers of devices to be added to group.

        Returns:
            Response: CentralAPI Response object
        """
        # API-FLAW report flawed API method
        # Returns 500 status code when result is essentially success
        # Please Confirm: move Aruba9004_81_E8_FA & PommoreGW1 to group WLNET? [y/N]: y
        # ✖ Sending Data [configuration/v1/devices/move]
        # status code: 500 <-- 500 on success.  At least for gw would need to double check others.
        # description:
        # Controller/Gateway group move has been initiated, please check audit trail for details
        # error_code: 0001
        # service_name: Configuration
        url = "/configuration/v1/devices/move"
        serials = utils.listify(serials)

        json_data = {
            'group': group,
            'serials': serials
        }

        if cx_retain_config:
            json_data["preserve_config_overrides"] = ["AOS_CX"]

        resp = await self.post(url, json_data=json_data)

        # This method returns status 500 with msg that move is initiated on success.
        if not resp and resp.status == 500:
            match_str = "group move has been initiated, please check audit trail for details"
            if match_str in resp.output.get("description", ""):
                resp._ok = True

        return resp

    # API-FLAW no API to upgrade cluster
    # https://internal-ui.central.arubanetworks.com/firmware/controller/clusters/upgrade is what the UI calls when you upgrade via UI
    # payload: {"reboot":true,"firmware_version":"10.5.0.0-beta_87046","devices":[],"clusters":[72],"when":0,"timezone":"+00:00","partition":"primary"}
    async def upgrade_firmware(
        self,
        scheduled_at: int = None,
        swarm_id: str = None,
        serial: str = None,
        group: str = None,
        device_type: constants.DeviceTypes = None,
        firmware_version: str = None,
        model: str = None,
        reboot: bool = False,
        forced: bool = False,
    ) -> Response:
        """Initiate firmware upgrade on device(s).

        You can only specify one of device_type, swarm_id or serial parameters

        // Used by upgrade [device|group|swarm] //

        Args:
            scheduled_at (int, optional): When to schedule upgrade (epoch seconds). Defaults to None (Now).
            swarm_id (str, optional): Upgrade a specific swarm by id. Defaults to None.
            serial (str, optional): Upgrade a specific device by serial. Defaults to None.
            group (str, optional): Upgrade devices belonging to group. Defaults to None.
            device_type (Literal["ap", "gw", "cx", "sw"]): Type of device to upgrade. Defaults to None.
            firmware_version (str, optional): Version to upgrade to. Defaults to None(recommended version).
            model (str, optional): To initiate upgrade at group level for specific model family. Applicable
                only for Aruba switches. Defaults to None.
            reboot (bool, optional): Automatically reboot device after firmware download. Defaults to False.
            forced (bool, optional): Use True for forcing the upgrade of a gateway which is part of a cluster. Defaults to False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade"

        json_data = {
            'firmware_scheduled_at': scheduled_at,
            'swarm_id': swarm_id,
            'serial': serial,
            'group': group,
            'device_type': None if not device_type else constants.lib_to_api(device_type, "firmware"),
            'firmware_version': firmware_version,
            'reboot': reboot,
            'model': model,
            'forced': forced
        }

        return await self.post(url, json_data=json_data)

    async def cancel_upgrade(
        self,
        device_type: constants.DeviceTypes = None,
        serial: str = None,
        swarm_id: str = None,
        group: str = None,
    ) -> Response:
        """Cancel scheduled firmware upgrade.

        You can only specify one of device_type, swarm_id or serial parameters

        Args:
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Specify one of "cx|sw|ap|gw  (sw = aos-sw)"
            serial (str, optional): Serial of device
            swarm_id (str): Swarm ID
            group (str): Specify Group Name to cancel upgrade for devices in that group

        Returns:
            Response: CentralAPI Response object
        """
        device_type = None if not device_type else constants.lib_to_api(device_type, 'firmware')
        url = "/firmware/v1/upgrade/cancel"

        json_data = {
            'swarm_id': swarm_id,
            'serial': serial,
            'device_type': device_type,
            'group': group
        }

        return await self.post(url, json_data=json_data)

    # API-FLAW only accepts swarm id for IAP, AOS10 show as IAP but no swarm id.  serial is rejected.
    # CX will return resp like it works, but nothing ever happens
    async def get_upgrade_status(self, swarm_id: str = None, serial: str = None) -> Response:
        """Get firmware upgrade status.

        // Used by show upgrade [device-iden] //

        Args:
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/status"

        params = {
            "swarm_id": swarm_id,
            "serial": serial
        }

        return await self.get(url, params=params)

    async def get_firmware_compliance(self, device_type: constants.DeviceTypes, group: str = None) -> Response:
        """Get Firmware Compliance Version.

        // Used by show firmware compliance [ap|gw|sw|cx] [group-name] //

        Args:
            device_type (str): Specify one of "ap|gw|sw|sx"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        # API method returns 404 if compliance is not set!
        url = "/firmware/v1/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.get(url, params=params)

    async def delete_firmware_compliance(self, device_type: constants.DeviceTypes, group: str = None) -> Response:
        """Clear Firmware Compliance Version.

        // Used by delete firmware compliance [ap|gw|sw|cx] [group] //

        Args:
            device_type (str): Specify one of "ap|gw|sw|cx"
            group (str, optional): Group name. Defaults to None (Global Compliance)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.delete(url, params=params)

    async def set_firmware_compliance(
        self,
        device_type: constants.DeviceTypes,
        group: str,
        version: str,
        compliance_scheduled_at: int,
        reboot: bool = True,  # Only applies to MAS all others reboot regardless.  cencli doesn't support MAS
        allow_unsupported_version: bool = False,
    ) -> Response:
        """Set Firmware Compliance version (for group/device-type).

        Args:
            device_type (str): Specify one of "ap|sw|cx|gw"
            group (str): Group name
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            compliance_scheduled_at (int): Firmware compliance will be schedule at,
                compliance_scheduled_at - current time. compliance_scheduled_at is epoch in seconds
                and default value is current time.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches, CX switches, and controller
                since IAP reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v2/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')


        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at
        }

        return await self.post(url, json_data=json_data)

    async def get_device_firmware_details(
        self,
        serial: str,
    ) -> Response:
        """Firmware Details of Device.

        Args:
            serial (str): Serial of the device for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/devices/{serial}"

        return await self.get(url)

    async def get_device_firmware_details_by_type(
        self,
        device_type: Literal["mas", "cx", "sw", "gw"],
        group: str = None,
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """List Firmware Details by type for switches or gateways (Not valid for APs).

        Args:
            device_type (str): Specify one of "mas|sw|cx|gw"
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. max 1000, Defaults to 500.

        Returns:
            Response: CentralAPI Response object

        Raises:
            ValueError: if device_type is not valid/supported by API endpoint.
        """
        url = "/firmware/v1/devices"
        device_type = constants.lib_to_api(device_type, "firmware")

        params = {
            'device_type': device_type,
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_all_swarms_firmware_details(
        self,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Firmware Details of all Swarms.

        Args:
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 20 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/swarms"

        params = {
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)


    async def get_swarm_firmware_details(
        self,
        swarm_id: str,
    ) -> Response:
        """Firmware Details of Swarm or AOS10 AP.

        Args:
            swarm_id (str): Swarm ID for which the firmware detail to be queried
                AOS10 APs provide serial as swarm_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def check_firmware_available(
        self,
        device_type: constants.DeviceTypes,
        firmware_version: str,
    ) -> Response:
        """Firmware Version.

        Args:
            device_type (str): Specify one of "cx", "sw", "ap", "gw"
            firmware_version (str): firmware version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/versions/{firmware_version}"
        device_type = constants.lib_to_api(device_type, "firmware")

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def get_default_group(self,) -> Response:
        """Get default group.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/default_group"

        return await self.get(url)

    async def move_devices_to_site(
        self,
        site_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Associate list of devices to a site.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. Valid Values: ap, gw switch
            serials (str | List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO make device_types consistent throughout
        device_type = constants.lib_to_api(device_type, "site")
        if not device_type:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_str}"
            )

        url = "/central/v2/sites/associations"
        serials = utils.listify(serials)

        json_data = {
            'site_id': site_id,
            'device_ids': serials,
            'device_type': device_type
        }

        return await self.post(url, json_data=json_data)

    async def remove_devices_from_site(
        self,
        site_id: int,
        serials: List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Remove a list of devices from a site.

        Args:
            site_id (int): Site ID
            serials (str | List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (Literal['ap', 'gw', 'switch']): Device type. Valid Values: ap, gw, switch.

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        url = "/central/v2/sites/associations"
        serials = utils.listify(serials)

        json_data = {
            'site_id': site_id,
            'device_ids': serials,
            'device_type': device_type
        }

        return await self.delete(url, json_data=json_data)  # API-FLAW: This method returns 200 when failures occur.

    async def create_label(
        self,
        label_name: str,
        category_id: int = 1,
    ) -> Response:
        """Create Label.

        Args:
            label_name (str): Label name
            category_id (int, optional): Label category ID defaults to 1
                1 = default label category, 2 = site

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels"

        json_data = {
            'category_id': category_id,
            'label_name': label_name
        }

        return await self.post(url, json_data=json_data)

    async def get_labels(
        self,
        calculate_total: bool = None,
        reverse: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Labels.

        Args:
            calculate_total (bool, optional): Whether to calculate total Labels
            reverse (bool, optional): List labels in reverse alphabetical order. Defaults to False
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels"

        params = {
            "calculate_total": calculate_total,
            "offset": offset,
            "limit": limit
        }
        if reverse:
            params["sort"] = "-label_name"

        return await self.get(url, params=params)

    async def assign_label_to_devices(
        self,
        label_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Associate Label to a list of devices.

        Args:
            label_id (int): Label ID
            serials (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (str): Device type. Valid Values: ap, gw, switch

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        url = "/central/v2/labels/associations"
        serials = utils.listify(serials)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serials
        }

        return await self.post(url, json_data=json_data)

    async def remove_label_from_devices(
        self,
        label_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """unassign a label from a list of devices.

        Args:
            label_id (int): Label ID
            serials (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (Literal['ap', 'gw', 'switch']): Device type. Valid Values: ap, gw, switch.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"

        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        serials = utils.listify(serials)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serials
        }

        return await self.delete(url, json_data=json_data)

    async def delete_label(
        self,
        label_id: int,
    ) -> Response:
        """Delete Label.

        Args:
            label_id (int): Label ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        return await self.delete(url)  # returns empty payload / response on success 200

    async def get_device_ip_routes(
        self,
        serial: str,
        api: str = "V1",
        marker: str = None,
        limit: int = 100
    ) -> Response:
        """Get routes for a device.

        Args:
            serial (str): Device serial number
            api (str, optional): API version (V0|V1), Defaults to V1.
            marker (str, optional): Pagination offset.
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/route"

        params = {
            'device': serial,
            'api': api,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    # TODO make add_device actual func sep and make this an aggregator that calls it and anything else based on params
    # TODO TypeDict for device_list
    async def add_devices(
        self,
        mac: str = None,
        serial: str = None,
        group: str = None,
        # site: int = None,
        part_num: str = None,
        license: str | List[str] = None,
        device_list: List[Dict[str, str]] = None
    ) -> Response | List[Response]:
        """Add device(s) using Mac and Serial number (part_num also required for CoP)
        Will also pre-assign device to group if provided

        Either mac and serial or device_list (which should contain a dict with mac serial) are required.

        Args:
            mac (str, optional): MAC address of device to be added
            serial (str, optional): Serial number of device to be added
            group (str, optional): Add device to pre-provisioned group (additional API call is made)
            site (int, optional): -- Not implemented -- Site ID
            part_num (str, optional): Part Number is required for Central On Prem.
            license (str|List(str), optional): The subscription license(s) to assign.
            device_list (List[Dict[str, str]], optional): List of dicts with mac, serial for each device
                and optionally group, part_num, license,

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        license_kwargs = []

        if license:
            license_kwargs = [{"serials": [serial], "services": utils.listify(license)}]
        if serial and mac:
            if device_list:
                raise ValueError("serial and mac are not expected when device_list is being provided.")

            to_group = None if not group else {group: [serial]}
            # to_site = None if not site else {site: [serial]}

            mac = utils.Mac(mac)
            if not mac:
                raise ValueError(f"mac {mac} appears to be invalid.")

            json_data = [
                {
                    "mac": mac.cols,
                    "serial": serial
                }
            ]
            if part_num:
                json_data[0]["partNumber"] = part_num

        elif device_list:
            if not isinstance(device_list, list) and not all(isinstance(d, dict) for d in device_list):
                raise ValueError("When using device_list to batch add devices, they should be provided as a list of dicts")

            json_data = []
            for d in device_list:
                mac = d.get("mac", d.get("mac_address"))
                if not mac:
                    raise ValueError(f"No Mac Address found for entry {d}")
                else:
                    mac = utils.Mac(mac)
                    if not mac:
                        raise ValueError(f"Mac Address {mac} appears to be invalid.")
                serial = d.get("serial", d.get("serial_num"))
                _this_dict = {"mac": mac.cols, "serial": serial}
                part_num = d.get("part_num", d.get("partNumber"))
                if part_num:
                    _this_dict["partNumber"] = part_num

                json_data += [_this_dict]

            to_group = {d.get("group"): [] for d in device_list if "group" in d and d["group"]}
            for d in device_list:
                if "group" in d and d["group"]:
                    to_group[d["group"]].append(d.get("serial", d.get("serial_num")))

            # to_site = {d.get("site"): [] for d in device_list if "site" in d and d["site"]}
            # for d in device_list:
            #     if "site" in d and d["site"]:
            #         to_site[d["site"]].append(d.get("serial", d.get("serial_num")))

            # Gather all serials for each license combination from device_list
            # TODO this needs to be tested
            _lic_kwargs = {}
            for d in device_list:
                if "license" not in d or not d["license"]:
                    continue

                d["license"] = utils.listify(d["license"])
                _key = f"{d['license'] if len(d['license']) == 1 else '|'.join(sorted(d['license']))}"
                _serial = d.get("serial", d.get("serial_num"))
                if not _serial:
                    raise ValueError(f"No serial found for device: {d}")

                if _key in _lic_kwargs:
                    _lic_kwargs[_key]["serials"] += utils.listify(_serial)
                else:
                    _lic_kwargs[_key] = {
                        "services": utils.listify(d["license"]),
                        "serials": utils.listify(_serial)
                    }
            license_kwargs = list(_lic_kwargs.values())

        else:
            raise ValueError("mac and serial or device_list is required")

        # Perform API call(s) to Central API GW
        if to_group or license_kwargs:
            # Add devices to central.  1 API call for 1 or many devices.
            br = self.BatchRequest
            reqs = [
                br(self.post, url, json_data=json_data),
            ]
            # Assign devices to pre-provisioned group.  1 API call per group
            if to_group:
                group_reqs = [br(self.preprovision_device_to_group, g, devs) for g, devs in to_group.items()]
                reqs = [*reqs, *group_reqs]

            # TODO You can add the device to a site after it's been pre-assigned (gateways only)
            # if to_site:
            #     site_reqs = [br(self.move_devices_to_site, s, devs, "gw") for s, devs in to_site.items()]
            #     reqs = [*reqs, *site_reqs]

            # Assign license to devices.  1 API call for all devices with same combination of licenses
            if license_kwargs:
                lic_reqs = [br(self.assign_licenses, **kwargs) for kwargs in license_kwargs]
                reqs = [*reqs, *lic_reqs]

            return await self._batch_request(reqs, continue_on_fail=True)
        # elif to_site:
        #     raise ValueError("Site can only be pre-assigned if device is pre-provisioned to a group")
        else:
            return await self.post(url, json_data=json_data)

    async def cop_delete_device_from_inventory(
        self,
        devices: List[str] = None,
    ) -> Response:
        """Delete devices using Serial number.  Only applies to CoP deployments.

        Device can not be archived in CoP inventory.

        Args:
            devices (list, optional): List of devices to be deleted from
                GreenLake inventory.  Only applies to CoP

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        devices = [{"serial": serial} for serial in devices]

        return await self.delete(url, json_data=devices)

    # TODO maybe helper method to delete_device that calls these
    async def delete_gateway(
        self,
        serial: str,
    ) -> Response:
        """Delete Gateway.

        Args:
            serial (str): Serial Number of Gateway to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/mobility_controllers/{serial}" if config.is_cop else f"/monitoring/v1/gateways/{serial}"

        return await self.delete(url)

    async def delete_switch(
        self,
        serial: str,
    ) -> Response:
        """Delete Switch.

        Args:
            serial (str): Serial number of switch to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}"

        return await self.delete(url)

    async def delete_stack(
        self,
        stack_id: str,
    ) -> Response:
        """Delete Switch Stack.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.delete(url)

    async def delete_ap(
        self,
        serial: str,
    ) -> Response:
        """Delete AP.

        Args:
            serial (str): Serial Number of AP to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/aps/{serial}"

        return await self.delete(url)

    async def preprovision_device_to_group(
        self,
        group: str,
        serials: str | List[str],
        tenant_id: str = None,
    ) -> Response:
        """Pre Provision devices to group.

        Args:
            group (str): Group name
            serials (str | List[str]): serial numbers
            tenant_id (str): Tenant id, (only applicable with MSP mode)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/preassign"

        json_data = {
            'device_id': utils.listify(serials),
            'group_name': group,
        }

        if tenant_id is not None:
            json_data["tenant_id"] = str(tenant_id)

        return await self.post(url, json_data=json_data)

    # TODO verify type-hint for device_list is the right way to do that.
    async def verify_device_addition(
        self,
        serial: str = None,
        mac: str = None,
        device_list: List[Dict[Literal["serial", "mac"], str]] = []
    ) -> Response:
        """Verify Device Addition

        Args:
            serial (str, optional): Serial Number of device to verify. Defaults to None.
            mac (str, optional): Mac Address of device to verify. Defaults to None.
            device_list (List[Dict[Literal[, optional): device_list list of dicts with
                "serial" and "mac" for each device to verify. Defaults to None.

        Must provide serial and mac for each device either via keyword argument or list.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/verify"
        if serial and mac:
            device_list += {
                "serial_num": serial,
                "mac_address": mac,
            }

        if not device_list:
            raise ValueError(
                "Invalid parameters expecting serial and mac for each device "
                "either via keyword argument or List[dict]."
            )

        return await self.post(url, json_data=device_list)

    async def upload_certificate(
        self,
        passphrase: str = "",
        cert_file: str | Path = None,
        cert_name: str = None,
        cert_format: Literal["PEM", "DER", "PKCS12"] = None,
        cert_data: str = None,
        server_cert: bool = False,
        ca_cert: bool = False,
        crl: bool = False,
        int_ca_cert: bool = False,
        ocsp_resp_cert: bool = False,
        ocsp_signer_cert: bool = False,
        ssh_pub_key: bool = False,
    ) -> Response:
        """Upload a certificate.

        Args:
            passphrase (str): passphrase
            cert_file (Path|str, optional): Cert file to upload, if file is provided cert_name
                and cert_format will be derived from file name / extension, unless those params
                are also provided.
            cert_name (str, optional): The name of the certificate.
            cert_format (Literal["PEM", "DER", "PKCS12"], optional): cert_format  Valid Values: PEM, DER, PKCS12
            cert_data (str, optional): Certificate content encoded in base64 for all format certificates.
            server_cert (bool, optional): Set to True if cert is a server certificate. Defaults to False.
            ca_cert (bool, optional): Set to True if cert is a CA Certificate. Defaults to False.
            crl (bool, optional): Set to True if data is a certificate revocation list. Defaults to False.
            int_ca_cert (bool, optional): Set to True if certificate is an intermediate CA cert. Defaults to False.
            ocsp_resp_cert (bool, optional): Set to True if certificate is an OCSP responder cert. Defaults to False.
            ocsp_signer_cert (bool, optional): Set to True if certificate is an OCSP signer cert. Defaults to False.
            ssh_pub_key (bool, optional): Set to True if certificate is an SSH Pub key. Defaults to False.
                ssh_pub_key needs to be in PEM format, ssh-rsa is not supported.

        Raises:
            ValueError: Raised if invalid combination of arguments is provided.

        Returns:
            Response: CentralAPI Response object
        """
        # API-FLAW API method, PUBLIC_CERT is not accepted
        url = "/configuration/v1/certificates"
        valid_types = [
            "SERVER_CERT",
            "CA_CERT",
            "CRL",
            "INTERMEDIATE_CA",
            "OCSP_RESPONDER_CERT",
            "OCSP_SIGNER_CERT",
            "PUBLIC_CERT"
        ]
        type_vars = [server_cert, ca_cert, crl, int_ca_cert, ocsp_resp_cert, ocsp_signer_cert, ssh_pub_key]
        if type_vars.count(True) > 1:
            raise ValueError("Provided conflicting certificate types, only 1 should be set to True.")
        elif all([not bool(var) for var in type_vars]):
            raise ValueError("No cert_type provided, one of the cert_types should be set to True")

        if cert_format and cert_format.upper() not in ["PEM", "DER", "PKCS12"]:
            raise ValueError(f"Invalid cert_format {cert_format}, valid values are 'PEM', 'DER', 'PKCS12'")
        elif not cert_format and not cert_file:
            raise ValueError("cert_format is required when not providing certificate via file.")

        if not cert_data and not cert_file:
            raise ValueError("One of cert_file or cert_data should be provided")
        elif cert_data and cert_file:
            raise ValueError("Only one of cert_file and cert_data should be provided")

        for cert_type, var in zip(valid_types, type_vars):
            if var:
                break

        if cert_file:
            cert_file = Path(cert_file) if not isinstance(cert_file, Path) else cert_file
            cert_name = cert_name or cert_file.stem
            if not cert_format:
                if cert_file.suffix.lower() in [".pfx", ".p12"]:
                    cert_format = "PKCS12"
                elif cert_file.suffix.lower() in [".pem", ".cer"]:
                    cert_format = "PEM"
                else:
                    # TODO determine format using cryptography lib
                    cert_format = "DER"
            else:
                cert_format = cert_format.upper()

            cert_data = cert_file.read_text()

        cert_bytes = cert_data.encode("utf-8")
        cert_b64 = base64.b64encode(cert_bytes).decode("utf-8")

        json_data = {
            'cert_name': cert_name,
            'cert_type': cert_type,
            'cert_format': cert_format,
            'passphrase': passphrase,
            'cert_data': cert_b64
        }

        return await self.post(url, json_data=json_data)

    async def get_subscriptions(
        self,
        license_type: str = None,
        device_type: constants.GenericDeviceTypes = None,
        offset: int = 0,
        limit: int = 1000,  # Doesn't appear to have max, allowed 10k limit in swagger
    ) -> Response:
        """Get user subscription keys.

        Args:
            license_type (str, optional): Supports Basic, Service Token and Multi Tier licensing types as well
            device_type (str, optional): Filter by device type ('ap', 'gw', or 'switch')
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of subscriptions to get Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions"
        if device_type:
            device_type = constants.lib_to_api(device_type, "licensing")
            device_type = device_type if not hasattr(device_type, "value") else device_type.value
        if license_type:
            if hasattr(license_type, "value"):
                license_type = license_type.value
            license_type = license_type.replace("-", " ").replace(" ", "_").upper()

        params = {
            'license_type': license_type,
            'device_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_subscription_stats(
        self,
        license_type: str = 'all',
        service: str = None,
        app_only_stats: bool = None,
    ) -> Response:
        """Get subscription stats.

        Args:
            license_type (str, optional): Supports basic/special/all.
                special - will fetch the statistics of special central services like pa, ucc, clarity etc.
                basic - will fetch the statistics of device management service licenses.
                all - will fetch both of these license types.

                Also supports multi tier license types such foundation_ap, advanced_switch_6300,
                foundation_70XX etc.

            service (str, optional): Service type: pa/pa,clarity,foundation_ap,
                advanced_switch_6300, foundation_70XX  etc.
            app_only_stats (bool, optional): If value is True, stats only for the current
                application returned rather than global stats

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/stats"

        params = {
            'license_type': license_type,
            'service': service,
            'app_only_stats': app_only_stats
        }

        return await self.get(url, params=params)

    async def get_valid_subscription_names(
        self,
        service_category: str = None,
        device_type: constants.GenericDeviceTypes = None,
    ) -> Response:
        """Get Valid subscription names from Central.

        Args:
            service_category (str, optional): Service category - dm/network
            device_type (Literal['ap', 'gw', 'switch'], optional): Device Type one of ap, gw, switch

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/config"
        if device_type:
            device_type = constants.lib_to_api(device_type, "licensing")

        params = {
            'service_category': service_category,
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def assign_licenses(self, serials: str | List[str], services: str | List[str]) -> Response:
        """Assign subscription to a device.

        // Used indirectly by add device when --license <license> is provided and batch add devices with license //

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Raises:
            ValueError: When more the 50 serials are provided, which exceeds the max allowed by the API endpoint.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/assign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        if len(serials) > 50:
            raise ValueError(f"{url} endpoint allows a max of 50 serials per call.  {len(serials)} were provided.")

        # Working code for doing 50 serial chunking here.  This results in _batch_request calling _batch_request and a list of lists.  Would need to flatted the lists
        # for display_results to handle the output.
        # requests = [self.BatchRequest(self.post, url, json_data={"serials": chunk, "services": services}) for chunk in utils.chunker(serials, 50)]
        # return await self._batch_request(requests)

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def unassign_licenses(self, serials: str | List[str], services: str | List[str]) -> Response:
        """Unassign subscription(s) from device(s).

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Raises:
            ValueError: When more the 50 serials are provided, which exceeds the max allowed by the API endpoint.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/unassign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        if len(serials) > 50:
            raise ValueError(f"{url} endpoint allows a max of 50 serials per call.  {len(serials)} were provided.")

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

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

        return await self.get(url, params=params)

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

        return await self.get(url, params=params)

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

        return await self.get(url, params=params)

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

        return await self.get(url, params=params)

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

        br = self.BatchRequest
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
        batch_res = await self._batch_request(batch_req)
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

        # try:
        #     wids_model = models.Wids(resp.output)
        #     resp.output = wids_model.model_dump()
        # except Exception as e:
        #     log.warning(f"dev note. pydantic conversion did not work\n{e}", show=True)

        return resp


    async def get_alerts(
        self,
        customer_id: str = None,
        group: str = None,
        label: str = None,
        serial: str = None,
        site: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        severity: str = None,
        type: str = None,
        search: str = None,
        # calculate_total: bool = False,  # Doesn't appear to impact always returns total
        ack: bool = None,
        fields: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """[central] List Notifications/Alerts.  Returns 1 day by default.

        Args:
            customer_id (str, optional): MSP user can filter notifications based on customer id
            group (str, optional): Used to filter the notification types based on group name
            label (str, optional): Used to filter the notification types based on Label name
            serial (str, optional): Used to filter the result based on serial number of the device
            site (str, optional): Used to filter the notification types based on Site name
            from_time (int | float | datetime, optional): start of duration within which alerts are raised
                Default now - 1 day (max 90) (API endpoint default is 30 days)
            to_time (int | float | datetime, optional): end of duration within which alerts are raised
                Default now.
            severity (str, optional): Used to filter the notification types based on severity
            type (str, optional): Used to filter the notification types based on notification type
                name
            search (str, optional): term used to search in name, category of the alert
            calculate_total (bool, optional): Whether to count total items in the response
            ack (bool, optional): Filter acknowledged or unacknowledged notifications. When query
                parameter is not specified, both acknowledged and unacknowledged notifications are
                included
            fields (str, optional): Comma separated list of fields to be returned
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'customer_id': customer_id,
            'group': group,
            'label': label,
            'serial': serial,
            'site': site,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'severity': severity,
            'search': search,
            # 'calculate_total': str(calculate_total),
            'type': type,
            'ack': None if ack is None else str(ack),
            'fields': fields,
            'offset': offset,
            'limit': limit,
        }

        return await self.get(url, params=params)

    async def central_acknowledge_notifications(
        self,
        NoName: List[str] = None,
    ) -> Response:
        """Acknowledge Notifications by ID List / All.

        Args:
            NoName (List[str], optional): Acknowledge notifications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"

        return await self.post(url)

    async def central_get_notification_config(
        self,
        search: str = None,
        sort: str = '-created_ts',
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """List Configuration/Settings for alerts that result in notification.

        Args:
            search (str, optional): term used to search in name, category of the alert
            sort (str, optional): Sort parameter may be one of +created_ts, -created_ts, Default is
                '-created_ts'  Valid Values: -created_ts, +created_ts
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/settings"

        params = {
            'search': search,
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_ap_config(
        self,
        group_swarmid: str,
        version: str = None,
    ) -> Response:
        """Get AP Group Level configuration for UI group.

        // Used by show config <AP MAC for AOS10 AP> //

        Args:
            group_swarmid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            version (str, optional): Version of AP.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_swarmid}"

        params = {
            'version': version
        }

        return await self.get(url, params=params)

    async def replace_ap_config(
        self,
        group_name_or_guid: str,
        clis: List[str],
    ) -> Response:
        """Replace AP Group Level configuration for UI group.

        Send AP configuration in CLI format as a list of strings where each item in the list is
        a line from the config.  Requires all lines of the config, not a partial update.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            clis (List[str]): Whole configuration List in CLI format.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_name_or_guid}"

        json_data = {
            'clis': clis
        }

        return await self.post(url, json_data=json_data)

    async def get_per_ap_config(
        self,
        serial: str,
    ) -> Response:
        """Get per AP setting.

        Args:
            serial (str): Serial Number of AP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        return await self.get(url)

    async def replace_per_ap_config(
        self,
        serial: str,
        clis: List[str],
    ) -> Response:
        """Replace per AP setting.

        Args:
            serial (str): Serial Number of AP
            clis (List[str]): All per AP setting List in CLI format
                Must provide all per AP settings, not partial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        json_data = {
            'clis': clis
        }

        return await self.post(url, json_data=json_data)

    # TODO not used # TODO types for below
    # FIXME effectively a dup of update_ap_settings, granted the other uses ap_settings vs this which uses ap_settings_cli (more complete coverage here)
    async def update_per_ap_settings(
            self,
            serial: str,
            hostname: str = None,
            ip: str = None,
            mask: str = None,
            gateway: str = None,
            dns: str | List[str] = None,
            domain: str = None,
            swarm_mode: str = None,
            radio_24_mode: str = None,
            radio_5_mode: str = None,
            radio_6_mode: str = None,
            radio_24_disable: bool = None,
            radio_5_disable: bool = None,
            radio_6_disable: bool = None,
            uplink_vlan: int = None,
            zone: str = None,
            dynamic_ant_mode: Literal["narrow", "wide"] = None,
            flex_dual_exclude: Literal["2.4", "5", "6"] = None,
    ) -> Response:
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        now_res = await self.get(url)
        if not now_res.ok:
            return now_res

        clis = now_res.output

        ip_address = None
        if ip:
            for param in [mask, gateway, dns]:
                if not param:
                    raise ValueError("mask, gateway, and dns are required when IP is updated")

            dns = ','.join(utils.listify(dns))

            domain = domain or '""'
            ip_address = f'{ip} {mask} {gateway} {dns} {domain}'.rstrip()
        flex_dual = None
        if flex_dual_exclude:
            flex_dual_exclude = str(flex_dual_exclude)
            if flex_dual_exclude.startswith("6"):
                flex_dual = "5GHz-and-2.4GHz"
            elif flex_dual_exclude.startswith("5"):
                flex_dual = "2.4GHz-and-6GHz"
            elif flex_dual_exclude.startswith("2.4") or flex_dual_exclude.startswith("24"):
                flex_dual = "5GHz-and-6GHz"

        cli_items = {
            "hostname": hostname,
            "ip-address": ip_address,
            "swarm-mode": swarm_mode,
            "wifi0-mode": radio_5_mode,
            "wifi1-mode": radio_24_mode,
            "wifi2-mode": radio_6_mode,
            "radio-0-disable": radio_5_disable,
            "radio-1-disable": radio_24_disable,
            "radio-2-disable": radio_6_disable,
            "zonename": zone,
            "uplink-vlan": uplink_vlan,
            "dynamic-ant": dynamic_ant_mode,
            "flex-dual-band": flex_dual
        }
        if all([v is None for v in cli_items.values()]):
            return Response(error="No Values provided to update")

        for idx, key in enumerate(cli_items, start=1):
            if cli_items[key] is not None:
                clis = [item for item in clis if not item.lstrip().startswith(key)]
                if key.endswith("-disable"):
                    if cli_items[key] is True:
                        clis.insert(idx, f"  {key}")
                else:
                    clis.insert(idx, f"  {key} {cli_items[key]}")

        json_data = {
            'clis': clis
        }

        # utils.json_print(json_data)
        # raise NotImplementedError("This helper function is currently under test, not implemented.")
        return await self.post(url, json_data=json_data)

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

        return await self.get(url, params=params)

    async def get_archived_devices(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> Response:
        """Get Archived devices from device inventory.

        Args:
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 50 (which is also the max).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/archive"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def archive_devices(
        self,
        serials: List[str],
    ) -> Response:
        """Archive devices using Serial list.

        Args:
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/archive"

        json_data = {
            'serials': utils.listify(serials)
        }

        return await self.post(url, json_data=json_data)

    # API-NOTE cencli remove archive [devices]
    async def unarchive_devices(
        self,
        serials: List[str],
    ) -> Response:
        """Unarchive devices using Serial list.

        Args:
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/unarchive"

        json_data = {
            'serials': utils.listify(serials)
        }

        return await self.post(url, json_data=json_data)

    async def get_portals(
        self,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all portals with limited data.

        Args:
            sort (str, optional): `+` is for ascending  and `-` for descending order, Valid Values: name prepended with `+` or `-` i.e. +name.
                Defaults to None.  Which results in use of API default +name.
            offset (int, optional): Starting index of element for a paginated query Defaults to 0.
            limit (int, optional): Number of items required per query Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/portals"

        params = {
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_portal_profile(
        self,
        portal_id: str,
    ) -> Response:
        """Get guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.get(url)

    async def delete_portal_profile(
        self,
        portal_id: str,
    ) -> Response:
        """Delete guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.delete(url)

    async def get_guests(
        self,
        portal_id: str,
        sort: str = '+name',
        filter_by: str = None,
        filter_value: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all guests created against a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            sort (str, optional): + is for ascending  and - for descending order, Valid Values: '+name', '-name'. Defaults to +name.
            filter_by (str, optional): filter by email or name  Valid Values: name, email
            filter_value (str, optional): filter value
            offset (int, optional): Starting index of element for a paginated query Defaults to 0.
            limit (int, optional): Number of items required per query Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors"

        params = {
            'sort': sort,
            'filter_by': filter_by,
            'filter_value': filter_value,
            'offset': offset,
            'limit': limit
        }
        params = utils.strip_none(params)

        return await self.get(url, params=params)


    async def add_guest(
        self,
        portal_id: str,
        name: str,
        # id: str,
        password: str = None,
        *,
        company_name: str = None,
        phone: str | None = None,
        email: str | None = None,
        valid_forever: bool = False,
        valid_days: int = 3,
        valid_hours: int = 0,
        valid_minutes: int = 0,
        notify: bool | None = None,
        notify_to: constants.NotifyToArgs | None = None,
        is_enabled: bool = True,
        # status: bool,
        # created_at: str,
        # expire_at: str,
    ) -> Response:
        """Create a new guest visitor of a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            name (str): Visitor account name
            password (str): Password
            company_name (str): Company name of the visitor
            phone (str): Phone number of the visitor; Format [+CountryCode][PhoneNumber]
            email (str): Email address of the visitor
            valid_forever (bool): Visitor account will not expire when this is set to true
            valid_days (int): Account validity in days
            valid_hours (int): Account validity in hours
            valid_minutes (int): Account validity in minutes
            notify (bool): Flag to notify the password via email or number
            notify_to (str): Notify to email or phone. Defualt is phone when it is provided
                otherwise email.  Valid Values: email, phone
            is_enabled (bool): Enable or disable the visitor account
            # id (str): NA for visitor post/put method. ID of the visitor
            # status (bool): This field provides status of the account. Returns true when enabled and
            #     not expired. NA for visitor post/put method. This is optional fields.
            # created_at (str): This field indicates the created date timestamp value. It is generated
            #     while creating visitor. NA for visitor post/put method. This is optional field.
            # expire_at (str): This field indicates expiry time timestamp value. It is generated based
            #     on the valid_till value and created_at time. NA for visitor post/put method. This is
            #     optional field

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors"

        user_data = {
            'phone': phone,
            'email': email
        }
        # API requires *both* phone and email, when either is provided, but they can be None/null

        json_data = {
            'name': name,
            'company_name': company_name,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_forever,
            'valid_till_days': valid_days,
            'valid_till_hours': valid_hours,
            'valid_till_minutes': valid_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password
        }
        json_data = utils.strip_none(json_data)
        if phone or email:
            json_data["user"] = user_data

        return await self.post(url, json_data=json_data)

    async def update_guest(
        self,
        portal_id: str,
        visitor_id: str,
        name: str,
        company_name: str = None,
        phone: str = None,
        email: str = None,
        is_enabled: bool = None,
        valid_till_no_limit: bool = None,
        valid_till_days: int = None,
        valid_till_hours: int = None,
        valid_till_minutes: int = None,
        notify: bool = None,
        notify_to: Literal["email", "phone"] = None,
        password: str = None,
    ) -> Response:
        """Update guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal
            name (str): Visitor account name
            company_name (str): Company name of the visitor
            phone (str): Phone number of the visitor; Format [+CountryCode][PhoneNumber]
            email (str): Email address of the visitor
            is_enabled (bool): Enable or disable the visitor account
            valid_till_no_limit (bool): Visitor account will not expire when this is set to true
            valid_till_days (int): Account validity in days
            valid_till_hours (int): Account validity in hours
            valid_till_minutes (int): Account validity in minutes
            notify (bool): Flag to notify the password via email or number
            notify_to (str): Notify to email or phone. Defualt is phone when it is provided
                otherwise email.  Valid Values: email, phone
            password (str): Password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        json_data = {
            'name': name,
            'company_name': company_name,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_till_no_limit,
            'valid_till_days': valid_till_days,
            'valid_till_hours': valid_till_hours,
            'valid_till_minutes': valid_till_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password
        }
        if any([phone, email]):
            json_data["user"] = {
                'phone': phone,
                'email': email,
            }

        return await self.put(url, json_data=json_data)

    async def delete_guest(
        self,
        portal_id: str,
        guest_id: str,
    ) -> Response:
        """Delete guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            guest_id (str): ID of Guest associated with the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{guest_id}"

        return await self.delete(url)

    # TODO build command
    async def get_guest_summary(
        self,
        ssids: List[str] | str,
        days: int = 28,
    ) -> Response:
        """Get summary statistics.

        Args:
            ssid (str): A comma separated list of SSIDs for which session data is required
            days (optional, int): Num of days for which session data is required  Valid Values: 1, 7, 28
                Default: 28

        Raises:
            ValueError: If days is not valid (1, 7, 28).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/summary"
        ssids = utils.listify(ssids)
        ssids = ",".join(ssids)
        if days and days not in [1, 7, 28]:
            return ValueError(f"days must be one of 1, 7, or 28.  {days} is invalid")

        params = {
            'days': days,
            'ssid': ssids
        }

        return await self.get(url, params=params)

    # TODO validate IP address format / Not used by CLI yet
    async def update_cx_properties(
        self,
        *,
        serial: str = None,
        group: str = None,
        name: str = None,
        contact: str = None,
        location: str = None,
        timezone: constants.TZDB = None,
        mgmt_vrf: bool = None,
        dns_servers: List[str] = [],
        ntp_servers: List[str] = [],
        admin_user: str = None,
        admin_pass: str = None,
    ) -> Response:
        """Update Properties (ArubaOS-CX).

        Args:
            serial (str, optional): Device serial number.
                Mandatory for device level configuration.
                1 and only 1 of serial or group are required
            group (str, optional): Group name.
                Mandatory for group level configuration.
                1 and only 1 of serial or group are required
            name (str): Only configurable at device-level.
            contact (str): Pattern: "^[^"?]*$"
            location (str): Pattern: "^[^"?]*$"
            timezone (str): timezone  Valid Values: use tz database format like "America/Chicago"
            mgmt_vrf (bool): Use mgmt VRF, indicates VRF for dns_servers and ntp_servers, if False or not provided default VRF is used.
            dns_servers (List[str]): ipv4/ipv6 address
            ntp_servers (List[str]): ipv4/ipv6 address
            admin_user (str): local admin user
            admin_pass (str): local admin password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/properties"

        params = {
            'device_serial': serial,
            'group_name': group
        }

        json_data = {
            'name': name,
            'contact': contact,
            'location': location,
            'timezone': timezone,
            'dns_servers': dns_servers,
            'ntp_servers': ntp_servers,
            'admin_username': admin_user,
            'admin_password': admin_pass
        }
        if mgmt_vrf is not None:
            json_data["vrf"] = "mgmt" if mgmt_vrf else "default"
        elif dns_servers or ntp_servers:
            json_data["vrf"] = "default"

        if len([x for x in [admin_user, admin_pass] if x is not None]) == 1:
            raise ValueError("If either admin_user or admin_pass are bing updated, *both* should be provided.")

        if len([x for x in [serial, group] if x is not None]) == 2:
            raise ValueError("provide serial to update device level properties, or group to update at the group level.  Providing both is invalid.")

        json_data = utils.strip_none(json_data, strip_empty_obj=True)

        return await self.post(url, json_data=json_data, params=params)

    async def get_ospf_area(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Area Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/area"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_ospf_interface(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Interface Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_ospf_neighbor(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF neighbor Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/neighbor"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_ospf_database(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Link State Database Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/database"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_overlay_connection(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """Get information about overlay control connection.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def reset_overlay_connection(
        self,
        device: str,
    ) -> Response:
        """Reset overlay control connection.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection/reset"

        params = {
            'device': device
        }

        return await self.put(url, params=params)

    async def get_overlay_routes_learned(
        self,
        device: str,
        *,
        best: bool = False,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of learned routes from overlay.

        Args:
            device (str): Device serial number
            best (bool): Return only best / preferred routes
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/learned"
        if best:
            url = f'{url}/best'

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_overlay_routes_advertised(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of advertised routes to overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/advertised"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_overlay_interfaces(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of overlay interfaces (tunnels).

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_denylist_clients(
        self,
        serial: str,
    ) -> Response:
        """Get all denylist client mac address in device.

        Args:
            serial (str): Device id of virtual controller (AOS8 IAP) or serial of AOS10 ap.
                Example:14b3743c01f8080bfa07ca053ef1e895df9c0680fe5a17bfd5

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/swarm/{serial}/blacklisting"

        return await self.get(url)


    # API-FLAW none of the auto_subscribe endpoints work
    async def get_auto_subscribe(
        self,
    ) -> Response:
        """Get the services which have auto subscribe enabled.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        return await self.get(url)

    async def enable_auto_subscribe(
        self,
        services: List[str] | str,
    ) -> Response:
        """Standalone Customer API: Assign licenses to all devices and enable auto subscribe for
        given services.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        if isinstance(services, str):
            services = [services]

        json_data = {
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def disable_auto_subscribe(
        self,
        services: List[str] | str,
    ) -> Response:
        """Standalone Customer API: Disable auto licensing for given services.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        if isinstance(services, str):
            services = [services]

        json_data = {
            'services': services
        }

        return await self.delete(url, json_data=json_data)

    # // -- Not used by commands yet.  undocumented kms api -- //
    async def kms_get_synced_aps(self, mac: str) -> Response:
        url = f"/keymgmt/v1/syncedaplist/{mac}"
        return await self.get(url)

    async def kms_get_client_record(self, mac: str) -> Response:
        url = f"/keymgmt/v1/keycache/{mac}"
        return await self.get(url)

    async def kms_get_hash(self) -> Response:
        url = "/keymgmt/v1/keyhash"
        return await self.get(url)

    async def kms_get_ap_state(self, serial: str) -> Response:
        url = f"/keymgmt/v1/Stats/ap/{serial}"
        return await self.get(url)

    # Bad endpoint URL 404
    async def kms_get_health(self) -> Response:
        url = "/keymgmt/v1/health"
        return await self.get(url)

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

        resp = await self.get(url, params=params)

        if resp:
            try:
                ds = tablib.Dataset().load(resp.output)
                resp.output = yaml.load(ds.json, Loader=yaml.SafeLoader)
            except Exception as e:
                log.error(f"cloudauth_get_registered_macs caught {e.__class__.__name__} trying to convert csv return from API to dict.", caption=True)

        return resp

    async def cloudauth_upload_fixme(
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

        return await self.post(url, headers=headers, params=params, payload=form_data)

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
            ssid (str, optional): MPSK network SSID, required if {upload_type} = 'mpsk'

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

        files = { "file": (file.name, file.open("rb"), "text/csv") }
        full_url=f"{self.auth.central_info['base_url']}{url}"
        headers = {
            "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
            'Accept': 'application/json'
        }

        for _ in range(2):
            _resp = requests.request("POST", url=full_url, params=params, files=files, headers=headers)
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
                self.refresh_token()
                headers["Authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"
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

        return await self.get(url, params=params)

    async def cloudauth_get_mpsk_networks(
        self,
    ) -> Response:
        """Read all configured MPSK networks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v2/mpsk"

        return await self.get(url)

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

        return await self.get(url, params=params)

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

        return await self.get(url, params=params)

    async def get_user_accounts(
        self,
        app_name: str = None,
        type: str = None,
        status: str = None,
        order_by: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List user accounts.

        Args:
            app_name (str, optional): Appname nms to filter Aruba Central users, and account_setting
                to filter HPE GreenLake Edge to Cloud Platform (CCS) application users  Valid
                Values: nms, account_setting
            type (str, optional): Filter based on system or federated user  Valid Values: system,
                federated
            status (str, optional): Filter user based on status (inprogress, failed)  Valid Values:
                inprogress, failed
            order_by (str, optional): Sort ordering (ascending or descending). +username signifies
                ascending order of username.  Valid Values: +username, -username
            offset (int, optional): Zero based offset to start from Defaults to 0.
            limit (int, optional): Maximum number of items to return Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/users"

        params = {
            'app_name': app_name,
            'type': type,
            'status': status,
            'order_by': order_by,
            'offset': offset,
            'limit': limit
        }

        # TODO this needs a fair amount of massaging to turn into a command, it's nested dicts
        # example response in private vscode dir.
        resp = await self.get(url, params=params)
        return resp

if __name__ == "__main__":
    pass
