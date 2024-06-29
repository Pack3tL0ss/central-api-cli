#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import base64
import json
import time
import tablib
import yaml
from asyncio.proactor_events import _ProactorBasePipeTransport
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Dict, List, Literal, Tuple, Union
from yarl import URL

# from aiohttp import ClientSession
import aiohttp
from pycentral.base_utils import tokenLocalStoreUtil

from . import (ArubaCentralBase, MyLogger, cleaner, config, constants, log,
               models, utils)
from .utils import Mac
from .response import Response, Session
from .exceptions import CentralCliException
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

class WlanType(str, Enum):
    employee = "employee"
    guest = "guest"

CloudAuthUploadType = constants.CloudAuthUploadType

def multipartify(data, parent_key=None, formatter: callable = None) -> dict:
    if formatter is None:
        formatter = lambda v: (None, v)  # noqa Multipart representation of value

    if not isinstance(data, dict):
        return {parent_key: formatter(data)}

    converted = []

    for key, value in data.items():
        current_key = key if parent_key is None else f"{parent_key}[{key}]"
        if isinstance(value, dict):
            converted.extend(multipartify(value, current_key, formatter).items())
        elif isinstance(value, list):
            for ind, list_value in enumerate(value):
                iter_key = f"{current_key}[{ind}]"
                converted.extend(multipartify(list_value, iter_key, formatter).items())
        else:
            converted.append((current_key, formatter(value)))

    return dict(converted)


def get_conn_from_file(account_name, logger: MyLogger = log):
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
    def strip_none(_dict: Union[dict, None]) -> Union[dict, None]:
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

    # TODO not a fan of *args see if we can define all params
    async def get_clients(
        self,
        *args: Tuple[str],
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
        # sort_by: str = None,
        offset: int = 0,
        limit: int = 1000,
        # **kwargs,
    ) -> Response:
        """Get Clients details.

        Args:
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
            offset (int, optional): API Paging offset. Defaults to 0.
            limit (int, optional): API record limit per request. Defaults to 1000 Max 1000.

        Returns:
            Response: CentralAPI Response Object
        """
        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            # 'fields': fields,
            # 'sort_by': sort_by,
            "offset": offset,
            "limit": limit,
        }
        wlan_only_params = {"network": network, "os_type": os_type, "band": band}
        wired_only_params = {"stack_id": stack_id}
        all_params = {**params, **wlan_only_params, **wired_only_params}
        wired_params = {**params, **wired_only_params}
        wlan_params = {**params, **wlan_only_params}
        if True in [network, os_type, band] and "wireless" not in args:
            args = ("wireless", *args)
        if stack_id and "wired" not in args:
            args = ("wired", *args)

        if mac or ("mac" in args and args.index("mac") < len(args)):
            if mac:
                _mac = utils.Mac(
                    mac,
                    fuzzy=True,
                )
            else:
                _mac = utils.Mac(
                    args[args.index("mac") + 1],
                    fuzzy=True,
                )
            if _mac.ok:
                mac = _mac
            else:
                return Response(error="INVALID MAC", output=f"The Provided MAC {_mac} Appears to be invalid.")

        if not args or "all" in args:
            if mac:
                return await self.get_client_details(mac,)
            else:
                return await self.get_all_clients(**all_params,)
        elif "wired" in args:
            if mac:
                return await self.get_client_details(mac, dev_type="wired",)
            else:
                return await self.get_wired_clients(**wired_params,)
        elif "wireless" in args:
            if mac:
                return await self.get_client_details(mac, dev_type="wireless",)
            else:
                return await self.get_wireless_clients(**wlan_params,)
        else:
            return Response(
                error="INVALID ARGUMENT",
                output=f"{args} appears to be invalid",
            )

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
        # sort_by: str = None,
        offset: int = 0,
        limit: int = 1000,
        # **kwargs,
    ) -> Response:
        """Get All clients

        // Used indirectly by show clients //

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
            FIXME sort_by (str, optional): Sort Output on provided key field. Defaults to None.
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
            # 'fields': fields,
            # 'sort_by': sort_by,
            "offset": offset,
            "limit": limit,
            "calculate_total": True
        }
        wlan_only_params = {"network": network, "os_type": os_type, "band": band}
        wired_only_params = {"stack_id": stack_id}

        # resp = await self.get_wireless_clients(**{**params, **wlan_only_params},)  # **kwargs)
        # if resp.ok:
        #     wlan_resp = resp
        #     wired_resp = await self.get_wired_clients(**{**params, **wired_only_params})  # **kwargs)
        #     if wired_resp.ok:
        #         resp.output = wlan_resp.output + wired_resp.output

        reqs = [
            self.BatchRequest(self.get_wireless_clients, **{**params, **wlan_only_params}),
            self.BatchRequest(self.get_wired_clients, **{**params, **wired_only_params})
        ]
        # FIXME if wireless clients call passes but wired fails there is no indication in cencli show clients output
        resp = await self._batch_request(reqs)
        if len(resp) == 2:  # and all(x.ok for x in resp):
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
            # TODO need Response to have an attribute that stores failed calls so cli commands can display output of passed calls and details on errors (when some calls fail)

        return resp

    async def get_client_roaming_history(
        self,
        macaddr: str,
        calculate_total: bool = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Wireless Client Mobility Trail.

        Args:
            macaddr (str): MAC address of the Wireless Client to be queried
            calculate_total (bool, optional): Whether to calculate total transitions
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000, max is 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wireless/{macaddr}/mobility_trail"

        params = {
            'calculate_total': calculate_total,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
        # sort_by: str = None,
        offset: int = 0,
        limit: int = 1000,
        # **kwargs,
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
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
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
            # 'sort': sort_by,
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
        # sort_by: str = None,
        offset: int = 0,
        limit: int = 1000,
        # **kwargs,
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
            # 'sort': sort_by,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params,)

    async def get_client_details(
        self,
        mac: Mac,
        dev_type: str = None,
        # sort_by: str = None,
        **kwargs
    ) -> Response:
        """Get Wired/Wireless Client Details.

        Args:
            mac (utils.Mac): MAC address of the Wireless Client to be queried
                API will return results matching a partial Mac

        Returns:
            Response: CentralAPI Response object
        """
        # API-FLAW This logic is here because Central has both methods, but given a wlan client mac
        # central will return the client details even when using the wired url

        # Mac match logic is jacked in central
        # given a client with a MAC of ac:37:43:4a:8e:fa
        #
        # Make MAC invalid (changed last octet):
        #   ac:37:43:4a:8e:ff No Match
        #   ac37434a8eff No Match
        #   ac:37:43:4a:8e-ff  Returns MATCH
        #   ac:37:43:4a:8eff  Returns MATCH
        #   ac:37:43:4a:8eff  Returns MATCH
        #   ac37434a8e:ff  Returns MATCH
        #   ac-37-43-4a-8e-ff Return MATCH
        #   ac37.434a.8eff Returns MATCH
        if not dev_type:
            for _dev_type in ["wireless", "wired"]:
                url = f"/monitoring/v1/clients/{_dev_type}/{mac.url}"
                resp = await self.get(url,)  # callback=cleaner.get_clients, **kwargs)
                if resp:
                    # resp.output = [{**{"client_type": _dev_type.upper()}, **d} for d in resp.output]
                    break

            return resp
        else:
            url = f"/monitoring/v1/clients/{dev_type}/{mac.url}"
            return await self.get(url,)  # callback=cleaner.get_clients, **kwargs)

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

    async def get_template(self, group: str, template: str) -> Response:
        url = f"/configuration/v1/groups/{group}/templates/{template}"
        return await self.get(url)

    async def get_template_details_for_device(self, device_serial: str, details: bool = False) -> Response:
        """Get configuration details for a device (only for template groups).

        Args:
            device_serial (str): Serial number of the device.
            details (bool, optional): Usually pass false to get only the summary of a device's
                configuration status.
                Pass true only if detailed response of a device's configuration status is required.
                Passing true might result in slower API response and performance effect
                comparatively.

        Returns:
            Response: CentralAPI Response object
        """
        # API-NOTE returns form-data (a big str)
        #  A cleaner has been created that parses the resp into dict
        #  with summary(dict) and running/central_side configs (str)
        # Need cleaner to parse and convert to dict
        # --fd3longalphanumericstring63
        # Content-Disposition: form-data; name="Summary"
        # Content-Type: application/json

        # {
        #     "Device_serial": "redacted",
        #     "Device_type": "ArubaSwitch",
        #     "Group": "WadeLab",
        #     "Configuration_error_status": false,
        #     "Override_status": false,
        #     "Template_name": "2930F-8",
        #     "Template_hash": "46a-redacted-0d",
        #     "Template_error_status": false
        # }
        # --fd3longalphanumericstring63
        url = f"/configuration/v1/devices/{device_serial}/config_details"
        headers = {"Accept": "multipart/form-data"}
        params = {"details": str(details)}
        return await self.get(url, params=params, headers=headers)

    async def get_all_templates_in_group(
        self,
        group: str,
        name: str = None,
        device_type: Literal["ap", "sw", "cx", "gw"] = None,
        version: str = None,
        model: str = None,
    ) -> Response:
        if device_type:
            device_type = constants.lib_to_api("template", device_type)

        params = {
            "offset": 0,
            "limit": 20,  # 20 is the max
            "template": name,
            "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
            "version": version,
            "model": model,
        }
        url = f"/configuration/v1/groups/{group}/templates"
        return await self.get(url, params=params)

    # FIXME # TODO # What the Absolute F?!  not able to send template as formdata properly with aiohttp
    #       requests module works, but no luck after hours messing with form-data in aiohttp
    async def add_template(
        self,
        name: str,
        group: str,
        template: Union[Path, str, bytes],
        device_type: constants.DevTypes ="ap",
        version: str = "ALL",
        model: str = "ALL",
    ) -> Response:
        """Create new template.

        Args:
            name (str): Name of template.
            group (str): Name of the group for which the template is to be created.
            template (Union[Path, str, bytes]): Template File or encoded template content.
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
        # formdata = aiohttp.FormData()
        if isinstance(template, bytes):
            # formdata.add_field("template", {"template": template}, filename="template.txt")
            # files = aiohttp.FormData([("template", ("template.txt", template),)])
            files = {'template': ('template.txt', template)}
        else:
            template = template if isinstance(template, Path) else Path(str(template))
            if not template.exists():
                raise FileNotFoundError

            files = {'template': ('template.txt', template.read_bytes())}
            # files = aiohttp.FormData([("template", ("template.txt", template.read_bytes()),)])
            # formdata.add_field("template", template.read_bytes(), filename="template.txt")
            # formdata.add_field("template", template.read_bytes())

            # formdata.add_field(
            #     "template",
            #     template.read_text(),
            #     filename="template.txt",
            #     content_type="multipart/form-data"
            # )

        # wr = formdata()
        # data = f'--{wr.boundary}\r\nContent-Disposition: form-data; name="template";filename="template.txt"{wr._parts[0][0]._value.decode()}\r\n--{wr.boundary}'.encode("utf-8")

        # -- Working form from wh2snow
        # # Create a FormData object
        # _form = aiohttp.FormData()

        # # Add some data to the form
        # _form.add_field('grant_type', 'refresh_token')
        # _form.add_field('client_id', config.snow.client_id)
        # _form.add_field('client_secret', config.snow.client_secret)
        # _form.add_field('refresh_token', tok.refresh)
        # async with aiohttp.ClientSession() as session:
        #     response = await session.post(str(config.snow.refresh_url), data=_form)
        device_type = device_type if not hasattr(device_type, "value") else device_type.value
        device_type = constants.lib_to_api("template", device_type)

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }
        # WTF Missing formdata parameter 'template'
        # return await self.post(url, params=params, payload=formdata,)  #


        # No difference vs the above
        # headers = {
        #     "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
        #     'Accept': 'application/json',
        #     "Content-Type": "multipart/form-data"
        # }
        # async with aiohttp.ClientSession(self.auth.central_info["base_url"]) as session:
        #     resp = await session.post(url, params=params, data=formdata, headers=headers, ssl=True)
        #     try:
        #         output = await resp.content.read()
        #         output = output.decode()
        #         output = json.loads(output)
        #     except Exception as e:
        #         output = None
        #         print(e)
        # return Response(resp, output=output)

        # HACK This works but prefer to get aiohttp sorted for consistency
        import requests
        headers = {
            "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
            'Accept': 'application/json'
        }
        url=f"{self.auth.central_info['base_url']}{url}"
        for _ in range(2):
            resp = requests.request("POST", url=url, params=params, files=files, headers=headers)
            output = f"[{resp.reason}]" + " " + resp.text.lstrip('[\n "').rstrip('"\n]')
            resp = Response(output=output, ok=resp.ok, url=url, elapsed=round(resp.elapsed.total_seconds(), 2), status_code=resp.status_code, rl_str="-")
            if "invalid_token" in resp.output:
                self.refresh_token()
            else:
                break
        return resp

    async def update_existing_template(
        self,
        group: str,
        name: str,
        template: Path = None,
        payload: str = None,
        device_type: str = None,
        version: str = None,
        model: str = None,
    ) -> Response:
        """Update existing template.

        Args:
            group (str): Name of the group for which the template is to be updated.
            name (str): Name of template.
            device_type (str, optional): Device type of the template.
                Valid Values: ap, sw (ArubaOS-SW), cx (ArubaOS-CX), gw (controllers/gateways)
            version (str, optional): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model.
                Example: 2920, J9727A etc.
            template (Union[Path, str], optional): Template text.
                For 'ArubaSwitch' device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.
                2. aruba-central url https://<URL | IP>/ws.
            payload (str, optional): json representation of the required params.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        template = template if isinstance(template, Path) else Path(str(template))

        if device_type:
            device_type = constants.lib_to_api("template", device_type)

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        if template and template.is_file() and template.stat().st_size > 0:
            template_data: bytes = template.read_bytes()
        elif payload:
            template_data: bytes = payload
        else:
            template_data = None

        return await self.patch(url, params=params, payload=template_data)

    # Tested and works but not used.  This calls pycentral method directly, but it has an error in base.py command re url concat
    # and it doesn't catch all exceptions so possible to get exception when eval resp our Response object is better IMHO
    async def _update_existing_template(
        self,
        group: str,
        name: str,
        template: Path = None,
        payload: str = None,
        device_type: str = None,
        version: str = None,
        model: str = None,
    ) -> Response:
        from pycentral.configuration import Templates

        templates = Templates()
        kwargs = {
            "group_name": group,
            "template_name": name,
            "device_type": device_type,
            "version": version,
            "model": model,
            "template_filename": str(template),
        }

        return templates.update_template(self.auth, **kwargs)

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
            resp.output = cleaner.get_group_names(resp.output)
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

        template_resp, props_resp = await self._batch_request(
            [
                self.BatchRequest(self.get_groups_template_status, (groups,)),
                self.BatchRequest(self.get_groups_properties, (groups,))
            ]
        )

        template_by_group = {d["group"]: d["template_details"] for d in template_resp.output}
        props_by_group = {d["group"]: d["properties"] for d in props_resp.output}

        combined = {tg: {"properties": pv, "template_details": tv} for (tg, tv), (pg, pv) in zip(template_by_group.items(), props_by_group.items()) if pg == tg}
        if len(set([len(combined), len(template_by_group), len(props_by_group)])) > 1:
            raise CentralCliException("Unexpected error in get_all_groups, length of responses differs.")

        resp = props_resp
        resp.output = [{"group": k, **v} for k, v in combined.items()]
        resp.raw = {"properties": resp.raw, "template_info": template_resp.raw}

        return resp


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
        output = [r for res in batch_resp for r in res.output]
        resp = batch_resp[-1]
        resp.output = output
        if "data" in resp.raw:
            resp.raw["data"] = output
        else:
            log.warning("raw attr in resp from get_all_groups lacks expected outer key 'data'")

        return resp


    async def get_all_templates(self, groups: List[dict] = None, **params) -> Response:
        """Get data for all defined templates from Aruba Central

        Args:
            groups (List[dict], optional): List of group dictionaries (If provided additional API
                calls to get group names for all template groups are not performed).
                Defaults to None.

        Returns:
            Response: centralcli Response Object
        """
        if not groups:
            resp = await self.get_groups_template_status()
            if not resp:
                return resp
            groups = cleaner.get_all_groups(resp.output)

        template_groups = [g["name"] for g in groups if True in g["template group"].values()]

        if not template_groups:
            return Response(
                url="No call performed",
                ok=True,
                output=[],
                raw=[],
                error="None of the configured groups are Template Groups.",
            )

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

    async def get_sku_types(self):  # FAILED - "Could not verify access level for the URL."
        url = "/platform/orders/v1/skus"
        params = {"sku_type": "all"}
        return await self.get(url, params=params)

    # TODO total is returned with first request can batch remaining requests with limit/offset adjusted
    # API-FLAW limit doesn't appear to have an upper limit, but took forever to return 5,000 records
    async def get_device_inventory(
        self,
        sku_type: str = "all",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get devices from device inventory.

        Args:
            sku_type (str, optional): all/iap/switch/controller/gateway/vgw/cap/boc/all_ap/all_controller/others
                Defaults to all.
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        params = {
            'sku_type': sku_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    # TODO cleanup the way raw is combined, see show wids all.
    # TODO add full kwargs and type-hints
    async def get_all_devicesv2(self, cache: bool = False, calculate_client_count: bool = True, show_resource_details: bool = False, **kwargs) -> Response:
        """Get all devices from Aruba Central

        Returns:
            Response: CentralAPI Response object

            raw attribute has all keys returned for the devices, the output attribute
            includes only keys common across all device types in central.
        """
        dev_types = ["aps", "switches", "gateways"]  # mobility_controllers seems same as gw
        lib_dev_types = {
            "aps": "ap",
            "gateways": "gw",
        }
        _output = {}

        # We always get resource details for switches when cache=True as we need it for the switch_role (standalone/conductor/secondary/member) to store in the cache.
        # We used the switch with an IP to determine which is the conductor in the past, but found scenarios where no IP was showing in central for an extended period of time.
        reqs = [self.BatchRequest(self.get_devices, dev_type, calculate_client_count=calculate_client_count, show_resource_details=show_resource_details if not cache or dev_type != "switches" else True, **kwargs) for dev_type in dev_types]
        res = await self._batch_request(reqs)
        _failure_idxs = [idx for idx, r in enumerate(res) if not r]
        if _failure_idxs:
            resp = res[_failure_idxs[-1]]
            resp.output = [{"dev_type": dev_types[f], "error": res[f].output} for f in _failure_idxs]
            if len(res) == len(_failure_idxs):  # all calls failed
                return resp
            else:
                failed_calls = [r for r in res if not r.ok]
                res = [r for r in res if r.ok]
                for r in failed_calls:
                    log.error(f'API call failed to [{r.method}]{r.url.path}: status code: {r.status}, Error: {r.error}', log=False, caption=True)


        resp = res[-1]
        if calculate_client_count:
            _output = {k: [{"client_count": inner.get("client_count", "-"), **inner} for inner in utils.listify(v)] for k, v in zip(dev_types, [r.output for r in res]) if v}
        else:
            _output = {k: utils.listify(v) for k, v in zip(dev_types, [r.output for r in res]) if v}
        resp.raw = {k: utils.listify(v) for k, v in zip(dev_types, [r.raw for r in res]) if v}

        # TODO use below once everything that references it has been refactored so resp.raw["aps"][0]["aps"] becomes resp.raw["aps"]["aps"]
        # resp.raw = {k: v for k, v in zip(dev_types, [r.raw for r in res]) if v}
        def _get_swack_id(dev_type: str, dev_data: dict) -> str | None:
            if dev_type == "gateways":
                return None
            elif dev_type == "switches":
                return dev_data.get("stack_id")
            elif dev_type == "aps":
                return dev_data.get("swarm_id") if dev_data.get("firmware_version", "8").split(".")[0] == 8 else dev_data.get("serial")

        if _output:
            # Add type key to all dicts covert "switch-type" to cencli type (cx or sw)
            # Add switch_role and swack_id (swarm/stack id) to all devices, both for the sake of cache
            # TODO move to cleaner? set type to switch_type for switches let cleaner change value to lib vals
            dicts = [
                {
                    **{
                        "type": lib_dev_types.get(k, k) if k != "switches" else
                        constants.get_cencli_devtype(inner_dict.get("switch_type", "switch")),
                        "swack_id": _get_swack_id(k, inner_dict),
                        "switch_role": inner_dict.get("switch_role")
                    },
                    **{
                        kk: vv for kk, vv in inner_dict.items()
                    }
                } for k, v in _output.items() for inner_dict in v
            ]
            # TODO keep all fields in output dict, let cleaner define field for normal and verbose options
            #      if user selects --json or --yaml keep all fields
            # return just the keys common across all device types
            common_keys = set.intersection(*map(set, dicts))
            _output = [{k: d[k] for k in common_keys} for d in dicts]

            resp.output = _output

        return resp

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

    async def get_dev_by_type(
            self,
            dev_type: str,
        ) -> Response:  # VERIFIED
        url = "/platform/device_inventory/v1/devices"
        # iap, switch, gateway|boc
        if dev_type.lower() in ["aps", "ap"]:
            dev_type = "all_ap"
        params = {"sku_type": dev_type}
        return await self.get(url, params=params)

    async def get_variablised_template(self, serialnum: str) -> Response:  # VERIFIED
        url = f"/configuration/v1/devices/{serialnum}/variablised_template"
        return await self.get(url)

    async def get_variables(self, serialnum: str = None) -> Response:
        if serialnum and serialnum != "all":
            url = f"/configuration/v1/devices/{serialnum}/template_variables"
            params = {}
        else:
            url = "/configuration/v1/devices/template_variables"
            params = {"limit": 20, "offset": 0}
        return await self.get(url, params=params)

    # async def update_variables(self, serialnum: str, **var_dict: dict) -> bool:
    #     url = f"/configuration/v1/devices/{serialnum}/template_variables"
    #     var_dict = json.dumps(var_dict)
    #     return await self.patch(url, payload=var_dict)

    # TODO figure out how to make this work, need file like object
    async def update_device_template_variables(
        self,
        device_serial: str,
        device_mac: str,
        # total: int,
        # _sys_serial: str,
        # _sys_lan_mac: str,
        var_dict: dict,
    ) -> Response:
        """Update template variables for a device.

        Args:
            device_serial (str): Serial number of the device.
            total (int): total
            _sys_serial (str): _sys_serial
            _sys_lan_mac (str): _sys_lan_mac
            var_dict (dict): dict with variables to be updated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"
        # headers = {"Content-Type": "multipart/form-data"}

        json_data = {
            'total': len(var_dict) + 2,
            "variables": {
                **{
                    '_sys_serial': device_serial,
                    '_sys_lan_mac': device_mac,
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
    async def get_device_configuration(self, device_serial: str) -> Response:
        """Get last known running configuration for a device.

        // Used by show run <DEVICE-IDEN> //

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/configuration"
        headers = {"Accept": "multipart/form-data"}

        return await self.get(url, headers=headers)

    async def get_bssids(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        macaddr: str = None,
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
            macaddr (str, optional): Filter by AP MAC address
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
            'macaddr': macaddr,
            'cluster_id': cluster_id,
            'calculate_total': calculate_total,
            'sort': sort,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

    # TODO change dev_type to use [gw, sw, cx, ap, switch]  make consistent for all calls
    async def get_devices(
        self,
        dev_type: Literal["switches", "aps", "gateways"],
        group: str = None,
        label: str = None,
        stack_id: str = None,
        swarm_id: str = None,
        serial: str = None,
        status: str = None,
        fields: list = None,
        show_resource_details: bool = False,
        cluster_id: str = None,
        model: str = None,
        calculate_client_count: bool = True,
        calculate_ssid_count: bool = False,
        macaddr: str = None,
        public_ip_address: str = None,
        site: str = None,
        limit: int = 1000,  # max allowed 1000
        offset: int = 0,
        # sort: str = None,
    ) -> Response:
        """Get Devices from Aruba Central API Gateway

        // Used by show <"aps"|"gateways"|"switches"> //

        Args:
            dev_type (Literal["switches", "aps", "gateways"): Type of devices to get.
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
            macaddr (str, optional): Return device with specific MAC (fuzzy match). Defaults to None.
            public_ip_address (str, optional): Filter devices by Public IP. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        dev_params = {
            "aps": {
                'serial': serial,
                'macaddr': macaddr,
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
                'macaddr': macaddr,
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

        url = f"/monitoring/v1/{dev_type}"
        if dev_type == "aps":
            url = url.replace("v1", "v2")
        elif dev_type == "gateways" and config.is_cop:
            url = url.replace("v1/gateways", "v2/mobility_controllers")
        params = {**common_params, **dev_params[dev_type]}

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
        dev_type: Literal["switches", "aps", "gateways"],
        serial: str
    ) -> Response:
        """Return Details for a given device

        // Used by show device[s] <device iden> //

        Args:
            dev_type (str): Device Type
                Valid Values: "gateways", "aps", "switches"
            serial (str): Serial number of Device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/{dev_type}/{serial}"
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

    # TODO Under test 3/7/2024
    async def get_full_wlan_list(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN list/details by (UI) group.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    # API-FLAW This method returns next to nothing for reserved IPs.
    # Would be more ideal if it returned client_name pool pvid etc as it does with non resserved IPs
    async def get_dhcp_clients(
        self,
        serial_num: str,
        reservation: bool = True,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """Get DHCP Client information from Gateway.

        Args:
            serial_num (str): Serial number of mobility controller to be queried
            reservation (bool, optional): Flag to turn on/off listing DHCP reservations(if any).
                Defaults to True
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. max 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        gw_path = "mobility_controllers" if config.is_cop else "gateways"
        url = f"/monitoring/v1/{gw_path}/{serial_num}/dhcp_clients"

        params = {
            'reservation': str(reservation),
            "offset": offset,
            "limit": limit
        }

        return await self.get(url, params=params)

    async def get_dhcp_server(self, serial_num: str) -> Response:
        """Get DHCP Server details from Gateway.

        Args:
            serial_num (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        gw_path = "mobility_controllers" if config.is_cop else "gateways"
        url = f"/monitoring/v1/{gw_path}/{serial_num}/dhcp_servers"

        return await self.get(url)

    async def get_group_for_dev_by_serial(self, serial_num):
        return await self.get(f"/configuration/v1/devices/{serial_num}/group")

    async def get_vlan_info_by_gw(self, serial_num):
        return await self.get(f"/monitoring/v1/mobility_controllers/{serial_num}/vlan")

    async def get_uplink_info_by_gw(self, serial_num, timerange: str = "3H"):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks"
        params = {"timerange": timerange}
        return await self.get(url, params)

    async def get_uplink_tunnel_stats_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks/tunnel_stats"
        return await self.get(url)

    # TODO move cleaner
    async def get_all_sites(
        self,
        calculate_total: bool = False,
        offset: int = 0,
        limit: int = 1000
    ) -> Response:
        params = {
            "calculate_total": str(calculate_total),
            "offset": offset,
            "limit": limit
        }
        return await self.get("/central/v2/sites", params=params, callback=cleaner.sites)

    async def get_site_details(self, site_id):
        return await self.get(f"/central/v2/sites/{site_id}", callback=cleaner.sites)

    # TODO make command this shows events from devices (User ack rec from DHCP server, EAP response for client)
    async def get_events(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        from_ts: int = None,
        to_ts: int = None,
        macaddr: str = None,
        bssid: str = None,
        device_mac: str = None,
        hostname: str = None,
        device_type: str = None,
        sort: str = '-timestamp',
        site: str = None,
        serial: str = None,
        level: str = None,
        event_description: str = None,
        event_type: str = None,
        fields: str = None,
        calculate_total: bool = True,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Events. v2

        Endpoint allows a max of 10000 records to be retrieved.  The sum of offset + limit can not
        exceed 10,000

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_ts (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_ts (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            macaddr (str, optional): Filter by client MAC address
            bssid (str, optional): Filter by bssid
            device_mac (str, optional): Filter by device_mac
            hostname (str, optional): Filter by hostname
            device_type (str, optional): Filter by device type.
                Valid Values: ACCESS POINT, SWITCH, GATEWAY, CLIENT
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

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/events"

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "from_timestamp": from_ts,
            "to_timestamp": to_ts,
            'macaddr': macaddr,
            'bssid': bssid,
            'device_mac': device_mac,
            'hostname': hostname,
            'device_type': device_type,
            'sort': sort,
            'site': site,
            'serial': serial,
            'level': level,
            'event_description': event_description,
            'event_type': event_type,
            'fields': fields,
            'calculate_total': str(calculate_total),
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

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
            - reboot: supported by IAP/Controllers/MAS Switches/Aruba Switches
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
        serial_num: str = None,
        kick_all: bool = False,
        mac: str = None,
        ssid: str = None,
    ) -> Response:
        url = f"/device_management/v1/device/{serial_num}/action/disconnect_user"
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
        device_type: Literal['iap', 'mas', 'switch', 'controller', 'cx'],
    ) -> Response:
        """List Troubleshooting Commands.

        Args:
            device_type (str): Specify one of "IAP" for swarm, "MAS" for MAS switches, "SWITCH" for
                aruba switches,"CX" for CX switches, "CONTROLLER" for controllers respectively.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/troubleshooting/v1/commands"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)


    async def start_ts_session(
        self,
        serial: str,
        dev_type: str,
        commands: Union[int, list, dict],
    ) -> Response:
        """Start Troubleshooting Session.

        Args:
            serial (str): Serial of device
            dev_type (str): Specify one of "IAP/SWITCH/CX/MAS/CONTROLLER" for  IAPs, Aruba
                switches, CX Switches, MAS switches and controllers respectively.
            commands (int, List[int | dict], dict): a single command_id, or a List of command_ids (For commands with no arguments)
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
            'device_type': dev_type,
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

    async def get_ap_lldp_neighbor(self, device_serial: str) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{device_serial}"

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
        include_groups: Union[list, List[str]] = None,
        exclude_groups: Union[list, List[str]] = None,
        do_not_delete: bool = False,
    ) -> Response:
        """ "Create new configuration backup for multiple groups."

        Either include_groups or exclude_groups should be provided, but not both.

        Args:
            backup_name (str): Name of Backup
            include_groups (Union[list, List[str]], optional): Groups to include in Backup. Defaults to None.
            exclude_groups (Union[list, List[str]], optional): Groups to Exclude in Backup. Defaults to None.
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
        timerange: str = "1M",
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
            "timerange": timerange,
            "offset": offset,
            "limit": limit
        }

        return await self.get(url, params=params)

    # API-FLAW max limit 100 enforced if you provide the limit parameter, otherwise no limit? returned 811 w/ no param provided
    # API-FLAW does not return all logs available in UI wtf??
    async def get_audit_logs(
        self,
        log_id: str = None,
        username: str = None,
        start_time: int = None,
        end_time: int = None,
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

        Args:
            log_id (str, optional): The id of the log to return details for. Defaults to None.
            username (str, optional): Filter audit logs by User Name
            start_time (int, optional): Filter audit logs by Time Range. Start time of the audit
                logs should be provided in epoch seconds
            end_time (int, optional): Filter audit logs by Time Range. End time of the audit logs
                should be provided in epoch seconds
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

        params = {
            "username": username,
            "start_time": start_time,
            "end_time": end_time,
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

    async def get_audit_logs_events(
        self,
        group_name: str = None,
        device_id: str = None,
        classification: str = None,
        start_time: int = None,
        end_time: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all audit events for all groups.

        Args:
            group_name (str, optional): Filter audit events by Group Name
            device_id (str, optional): Filter audit events by Target / Device ID. Device ID for AP
                is VC Name and Serial Number for Switches
            classification (str, optional): Filter audit events by classification
            start_time (int, optional): Filter audit logs by Time Range. Start time of the audit
                logs should be provided in epoch seconds
            end_time (int, optional): Filter audit logs by Time Range. End time of the audit logs
                should be provided in epoch seconds
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination Defaults to 0.
            limit (int, optional): Maximum number of audit events to be returned Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/auditlogs/v1/events"

        params = {
            'group_name': group_name,
            'device_id': device_id,
            'classification': classification,
            'start_time': start_time,
            'end_time': end_time,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def create_site(
        self,
        site_name: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        country: str = None,
        zipcode: str = None,
        latitude: int = None,
        longitude: int = None,
        site_list: List[Dict[str, Union[str, dict]]] = None,
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
            zipcode (str, optional): Zipcode. Defaults to None.
            latitude (int, optional): Latitude (in the range of -90 and 90). Defaults to None.
            longitude (int, optional): Longitude (in the range of -100 and 180). Defaults to None.
            site_list (List[Dict[str, Union[str, dict]]], optional): A list of sites to be created. Defaults to None.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"

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
                        self.BatchRequest(self.post, (url,), json_data=_json, callback=cleaner._unlist)
                        for _json in site_list[1:]
                    ]
                )
                return [resp, *ret]
                # resp_list = cleaner._unlist(
                #     [await asyncio.gather(self.post(url, json_data=_json, callback=cleaner._unlist)) for _json in site_list[1:]]
                # )
                # # TODO make multi response packing function
                # resp.output = utils.listify(resp.output)
                # resp.output += [r.output for r in resp_list]
                # return resp
        else:
            return await self.post(url, json_data=json_data, callback=cleaner._unlist)

    # TODO add cli
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

        // Used by cencli update site [name|id|address] OR --lat <lat> --lon <lon> //

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
        group_swarmid: str,
        dns_server: str = None,
        ntp_server: List[str] = None,
        username: str = None,
        password: str = None,
    ) -> Response:
        """Update system config.

        All params are required by Aruba Central

        Args:
            group_swarmid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            dns_server (str): DNS server IPs or domain name
            ntp_server (List[str]): List of ntp server,
                Example: ["192.168.1.1", "127.0.0.0", "xxx.com"].
                IPs or domain name.
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{group_swarmid}"

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
        allowed_types: Union[constants.AllDevTypes, List[constants.AllDevTypes]] = ["ap", "gw", "cx", "sw"],
        wired_tg: bool = False,
        wlan_tg: bool = False,
        aos10: bool = False,
        microbranch: bool = False,
        gw_role: constants.GatewayRole = "branch",
        monitor_only_sw: bool = False,
        monitor_only_cx: bool = False,
    ) -> Response:
        """Create new group with specified properties. v3

        // Used by add group batch add group //

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
                Default: "branch"
            monitor_only_sw: Monitor only ArubaOS-SW switches, applies to UI group only
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v3/groups"

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
            raise ValueError('Invalid device type for allowed_types valid values: "ap", "gw", "sw", "cx", "switch"')
        if microbranch and not aos10:
            raise ValueError("Invalid combination, Group must be configured as AOS10 group to support Microbranch")
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
                }
            }
        }
        if gw_role and "Gateways" in allowed_types:
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
    async def update_group_properties(
        self,
        group: str,
        allowed_types: Union[constants.AllDevTypes, List[constants.AllDevTypes]] = None,
        wired_tg: bool = None,
        wlan_tg: bool = None,
        aos10: bool = None,
        microbranch: bool = None,
        gw_role: constants.GatewayRole = None,
        monitor_only_sw: bool = None,
        monitor_only_cx: bool = None,  # Not supported by central yet
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
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only (Future capability)

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

        # print("[DEBUG] ---- Current Properties of group")
        # utils.json_print(cur_group_props)
        # print("[DEBUG] ----")
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
            raise NotImplementedError("AOS_CX Monitor Only not supported in Central yet.")

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
        # if "Gateways" in combined_allowed or "AccessPoints" in combined_allowed:
        #     if aos10 is not None:
        #         return Response(
        #             error=f"{color('AOS10')} can only be set when APs or GWs are initially added to allowed_types of group"
        #                   f"\n{color(group)} can be cloned with option to upgrade during clone.",
        #             rl_str=resp.rl,
        #         )
        # if wired_tg and monitor_only_sw or monitor_only_cx:
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

        # json_data = {"group": group}
        # if grp_attrs:
        #     json_data["group_attributes"] = grp_attrs



        # if len(json_data) == 1:
        #     raise ValueError("No Changes Detected")
        # else:
        if config.debugv:
            print(f"[DEBUG] ---- Sending the following to {url}")
            utils.json_print(json_data)
            print("[DEBUG] ----")

        return await self.patch(url, json_data=json_data)
        # # FIXME remove debug prints
        # print(url)
        # from rich import print_json
        # print_json(data=json_data)

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

    async def get_ap_settings(self, serial_number: str) -> Response:
        """Get an existing ap settings.

        // Used indirectly (update_ap_settings) by batch rename AP //

        Args:
            serial_number (str): AP serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial_number}"

        return await self.get(url)

    async def update_ap_settings(
        self,
        serial_number: str,
        hostname: str,
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

        // Used by batch rename aps and rename ap //

        Args:
            serial_number (str, optional): AP Serial Number
            hostname (str): hostname
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
        url = f"/configuration/v2/ap_settings/{serial_number}"

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
            'usb_port_disable': usb_port_disable
        }
        if None in _json_data.values():
            resp = await self._request(self.get_ap_settings, serial_number)
            if not resp:
                return resp

            json_data = self.strip_none(_json_data)
            json_data = {**resp.output, **json_data}
            if not sorted(_json_data.keys()) == sorted(json_data.keys()):
                missing = ", ".join([f"'{k}'" for k in json_data.keys() if k not in _json_data.keys()])
                return Response(
                    ok=False,
                    error=f"Update payload is missing required attributes: {missing}",
                    reason="INVALID"
                )

        return await self.post(url, json_data=json_data)

    # TODO NotUsed Yet.  Shows any updates not yet pushed to the device (device offline, etc)
    # Only valid for APs.
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
        # TODO method to combine raw and output attrs of all responses into last resp
        output = [r for res in batch_resp for r in res.output]
        resp = batch_resp[-1]
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

    async def get_fw_version_list(
        self,
        device_type: str = None,
        swarm_id: str = None,
        serial: str = None,
    ) -> Response:
        """List Firmware Version.

        Args:
            device_type (str, optional): Specify one of "IAP/MAS/HP/CONTROLLER/CX"
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/versions"

        params = {
            'device_type': device_type,
            'swarm_id': swarm_id,
            'serial': serial
        }

        return await self.get(url, params=params)

    # Not used in a command yet
    async def check_image_available(
        self,
        device_type: str,
        firmware_version: str,
    ) -> Response:
        """Firmware Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_version (str): firmware version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/versions/{firmware_version}"

        params = {
            'device_type': device_type
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

    async def send_speed_test(
        self,
        serial: str,
        host: str = "ndt-iupui-mlab1-den04.mlab-oti.measurement-lab.org",
        options: str = None
    ) -> Response:
        """Speed Test.

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

    async def delete_site(self, site_id: Union[int, List[int]]) -> Response:
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
                    self.BatchRequest(self.delete, (f"{b_url}/{_id}",))
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
        type: WlanType = "employee",
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

    async def configuration_update_wlan_v2(
            self, group_name_or_guid: str, wlan_name: str,
            essid: str, type: str, hide_ssid: bool, vlan: str,
            zone: str, wpa_passphrase: str,
            wpa_passphrase_changed: bool, is_locked: bool,
            captive_profile_name: str, bandwidth_limit_up: str,
            bandwidth_limit_down: str,
            bandwidth_limit_peruser_up: str,
            bandwidth_limit_peruser_down: str, access_rules: list
        ) -> Response:
        """Update an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
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
        url = f"/configuration/v2/wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase_changed,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }

        return await self.put(url, json_data=json_data)

    # TODO changte to use consistent dev tpe ap gw cx sw
    # convert to the stuff apigw wants inside method
    # API-FLAW no API to upgrade cluster
    # https://internal-ui.central.arubanetworks.com/firmware/controller/clusters/upgrade is what the UI calls when you upgrade via UI
    # payload: {"reboot":true,"firmware_version":"10.5.0.0-beta_87046","devices":[],"clusters":[72],"when":0,"timezone":"+00:00","partition":"primary"}
    # device_type CX is not valid
    async def upgrade_firmware(
        self,
        scheduled_at: int = None,
        swarm_id: str = None,
        serial: str = None,
        group: str = None,
        device_type: Literal["IAP", "MAS", "HP", "CONTROLLER"] = None,
        firmware_version: str = None,
        model: str = None,
        reboot: bool = False,
    ) -> Response:
        """Initiate firmware upgrade on device(s).

        You can only specify one of device_type, swarm_id or serial parameters

        // Used by upgrade [device|group|swarm] //

        Args:
            scheduled_at (int, optional): When to schedule upgrade (epoch seconds). Defaults to None (Now).
            swarm_id (str, optional): Upgrade a specific swarm by id. Defaults to None.
            serial (str, optional): Upgrade a specific device by serial. Defaults to None.
            group (str, optional): Upgrade devices belonging to group. Defaults to None.
            device_type (str["IAP"|"MAS"|"HP"|"CONTROLLER"]): Type of device to upgrade. Defaults to None.
            firmware_version (str, optional): Version to upgrade to. Defaults to None(recommended version).
            model (str, optional): To initiate upgrade at group level for specific model family. Applicable
                only for Aruba switches. Defaults to None.
            reboot (bool, optional): Automatically reboot device after firmware download. Defaults to False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade"

        json_data = {
            'firmware_scheduled_at': scheduled_at,
            'swarm_id': swarm_id,
            'serial': serial,
            'group': group,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'reboot': reboot,
            'model': model
        }

        return await self.post(url, json_data=json_data)

    async def cancel_upgrade(
        self,
        device_type: str,
        serial: str = None,
        swarm_id: str = None,
        group: str = None,
    ) -> Response:
        """Cancel scheduled firmware upgrade.

        Args:
            device_type (str): Specify one of "cx|sw|ap|gw  (sw = aos-sw)"
            serial (str): Serial of device
            swarm_id (str): Swarm ID
            group (str): Specify Group Name to cancel upgrade for devices in that group

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api('firmware', device_type)
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

    DevType = Literal["IAP", "HP", "CONTROLLER"]

    async def get_firmware_compliance(self, device_type: constants.DevTypes, group: str = None) -> Response:
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
        device_type = constants.lib_to_api('firmware', device_type)

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.get(url, params=params)

    async def delete_firmware_compliance(self, device_type: constants.DevTypes, group: str = None) -> Response:
        """Clear Firmware Compliance Version.

        // Used by delete firmware compliance [ap|gw|sw|cx] [group] //

        Args:
            device_type (str): Specify one of "ap|gw|sw|cx"
            group (str, optional): Group name. Defaults to None (Global Compliance)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"
        device_type = constants.lib_to_api('firmware', device_type)

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.delete(url, params=params)

    async def set_firmware_compliance(
        self,
        device_type: constants.DevTypes,
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
        device_type = constants.lib_to_api('firmware', device_type)


        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at
        }

        return await self.post(url, json_data=json_data)

    async def move_devices_to_group(
        self,
        group: str,
        serial_nums: Union[str, List[str]],
        *,
        cx_retain_config: bool = True,  # TODO can we send this attribute even if it's not CX, will it ignore or error
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): Group Name to move device to.
            serials (List[str]): Serial numbers of devices to be added to group.

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
        serial_nums = utils.listify(serial_nums)

        json_data = {
            'group': group,
            'serials': serial_nums
        }

        if cx_retain_config:
            json_data["preserve_config_overrides"] = ["AOS_CX"]

        resp = await self.post(url, json_data=json_data)

        # This method returns status 500 with msg that move is initiated on success.
        if not resp and resp.status == 500:
            match_str = "group move has been initiated, please check audit trail for details"
            if match_str in resp.output.get("description", ""):
                resp.ok = True

        return resp

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
        serial_nums: Union[str, List[str]],
        device_type: Literal["ap", "cx", "sw", "switch", "gw"],
    ) -> Response:
        """Associate list of devices to a site.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. Valid Values: ap, cx, sw, switch, gw
                cx and sw are the same as the more generic switch.
            serial_nums (List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO make device_types consistent throughout
        device_type = constants.lib_to_api("site", device_type)
        if not device_type:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_str}"
            )

        url = "/central/v2/sites/associations"
        serial_nums = utils.listify(serial_nums)

        json_data = {
            'site_id': site_id,
            'device_ids': serial_nums,
            'device_type': device_type
        }

        return await self.post(url, json_data=json_data)

    async def remove_devices_from_site(
        self,
        site_id: int,
        serial_nums: List[str],
        device_type: Literal["ap", "cx", "sw", "switch", "gw"],
    ) -> Response:
        """Remove a list of devices from a site.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. Valid Values: ap, cx, sw, switch, gw
                cx and sw are the same as the more generic switch.
            serial_nums (List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api("site", device_type)
        if not device_type:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_str}"
            )

        url = "/central/v2/sites/associations"
        serial_nums = utils.listify(serial_nums)

        json_data = {
            'site_id': site_id,
            'device_ids': serial_nums,
            'device_type': device_type
        }

        # API-FLAW: This method returns 200 when failures occur.
        return await self.delete(url, json_data=json_data)

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
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

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
        device_type: constants.GenericDevTypes,
        serial_nums: Union[str, List[str]],
    ) -> Response:
        """Associate Label to a list of devices.

        Args:
            label_id (int): Label ID
            device_type (str): Device type. Valid Values: ap, gw, switch
            serial_nums (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"
        serial_nums = utils.listify(serial_nums)
        device_type = constants.lib_to_api("site", device_type)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serial_nums
        }

        return await self.post(url, json_data=json_data)

    # TODO make format of this and other label methods match site methods
    async def remove_label_from_devices(
        self,
        label_id: int,
        device_type: str,
        serial_nums: List[str],
    ) -> Response:
        """unassign a label from a list of devices.

        Args:
            label_id (int): Label ID
            device_type (str): Device type. One of ap, gw, switch
            serial_nums (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"
        serial_nums = utils.listify(serial_nums)
        device_type = constants.lib_to_api("site", device_type)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serial_nums
        }

        return await self.delete(url, json_data=json_data)

    # API-FLAW returns empty payload / response on success 200
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

        return await self.delete(url)

    async def get_device_ip_routes(
        self,
        serial_num: str,
        api: str = "V1",
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """Get routes for a device.

        Args:
            serial_num (str): Device serial number
            api (str, optional): API version (V0|V1), Defaults to V1.
            offset (str, optional): Pagination offset.
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/route"

        params = {
            'device': serial_num,
            'api': api,
            'marker': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    # TODO make add_device actual func sep and make this an aggregator that calls it and anything else based on params
    async def add_devices(
        self,
        mac_address: str = None,
        serial_num: str = None,
        group: str = None,
        # site: int = None,
        part_num: str = None,
        license: Union[str, List[str]] = None,
        device_list: List[Dict[str, str]] = None
    ) -> Union[Response, List[Response]]:
        """Add device(s) using Mac and Serial number (part_num also required for CoP)
        Will also pre-assign device to group if provided

        Either mac_address and serial_num or device_list (which should contain a dict with mac serial) are required.
        // Used by add device and batch add devices //

        Args:
            mac_address (str, optional): MAC address of device to be added
            serial_num (str, optional): Serial number of device to be added
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
            license_kwargs = [{"serials": [serial_num], "services": utils.listify(license)}]
        if serial_num and mac_address:
            if device_list:
                raise ValueError("serial_num and mac_address are not expected when device_list is being provided.")

            to_group = None if not group else {group: [serial_num]}
            # to_site = None if not site else {site: [serial_num]}

            mac = utils.Mac(mac_address)
            if not mac:
                raise ValueError(f"mac_address {mac_address} appears to be invalid.")

            json_data = [
                {
                    "mac": mac.cols,
                    "serial": serial_num
                }
            ]
            if part_num:
                json_data[0]["partNumber"] = part_num

        elif device_list:
            if not isinstance(device_list, list) and not all(isinstance(d, dict) for d in device_list):
                raise ValueError("When using device_list to batch add devices, they should be provided as a list of dicts")

            _keys = {
                "mac_address": "mac",
                "serial_num": "serial",
                "part_num": "partNumber"
            }

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

            to_group = {d.get("group"): [] for d in device_list if "group" in d}
            for d in device_list:
                if "group" in d:
                    to_group[d["group"]].append(d.get("serial_num", d.get("serial")))

            # to_site = {d.get("site"): [] for d in device_list if "site" in d}
            # for d in device_list:
            #     if "site" in d:
            #         to_site[d["site"]].append(d.get("serial_num", d.get("serial")))

            # Gather all serials for each license combination from device_list
            # TODO this needs to be tested
            _lic_kwargs = {}
            for d in device_list:
                if "license" not in d:
                    continue

                d["license"] = utils.listify(d["license"])
                _key = f"{d['license'] if len(d['license']) == 1 else '|'.join(sorted(d['license']))}"
                _serial = d.get("serial_num", d.get("serial"))
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

            # license_args = [[], []]
            # by_ser = {d["serial_num"]: utils.listify(d.get("license")) for d in device_list if d.get("license")}
            # TODO most efficient pairing of possible lic/dev for fewest call
            # TODO license via list not implemented yet.

        else:
            raise ValueError("mac_address and serial_num or device_list is required")

        # Perform API call(s) to Central API GW
        # TODO break out the add device call into it's own method.
        if to_group or license_kwargs:
            # Add devices to central.  1 API call for 1 or many devices.
            br = self.BatchRequest
            reqs = [
                br(self.post, url, json_data=json_data),
            ]
            # Assign devices to pre-provisioned group.  1 API call per group
            # TODO test that this is 1 API call per group.
            if to_group:
                group_reqs = [br(self.preprovision_device_to_group, (g, devs)) for g, devs in to_group.items()]
                reqs = [*reqs, *group_reqs]

            # TODO You can add the device to a site after it's been pre-assigned
            # if to_site:
            #     site_reqs = [br(self.move_devices_to_site, (s, devs, "gw")) for s, devs in to_site.items()]
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
        group_name: str,
        serial_nums: List[str] | str,
        tenant_id: str = None,
    ) -> Response:
        """Pre Provision a group to the device.

        Args:
            device_id (List[str]): device_id
            group_name (str): Group name
            tenant_id (str): Tenant id, (only applicable with MSP mode)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/preassign"

        json_data = {
            'device_id': utils.listify(serial_nums),
            'group_name': group_name,
        }

        if tenant_id is not None:
            json_data["tenant_id"] = str(tenant_id)

        return await self.post(url, json_data=json_data)

    # TODO verify type-hint for device_list is the right way to do that.
    async def verify_device_addition(
        self,
        serial_num: str = None,
        mac_address: str = None,
        device_list: List[Dict[Literal["mac_address", "serial_num"], str]] = []
    ) -> Response:
        """Verify Device Addition

        Args:
            serial_num (str, optional): Serial Number of device to verify. Defaults to None.
            mac_address (str, optional): Mac Address of device to verify. Defaults to None.
            device_list (List[Dict[Literal[, optional): device_list list of dicts with
                "serial_num" and "mac_address" for each device to verify. Defaults to None.

        Must provide serial_num and mac_address for each device either via keyword argument or list.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/verify"
        if serial_num and mac_address:
            device_list += {
                "serial_num": serial_num,
                "mac_address": mac_address,
            }

        if not device_list:
            raise ValueError(
                "Invalid parameters expecting serial_num and mac_address for each device "
                "either via keyword argument or List[dict]."
            )

        return await self.post(url, json_data=device_list)

    async def upload_certificate(
        self,
        passphrase: str = "",
        cert_file: Union[str, Path] = None,
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
        offset: int = 0,
        limit: int = 1000,  # Doesn't appear to have max, allowed 10k limit in swagger
    ) -> Response:
        """Get user subscription keys.

        Args:
            license_type (str, optional): Supports Basic, Service Token and Multi Tier licensing types as well
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of subscriptions to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions"

        params = {
            'license_type': license_type,
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
        device_type: str = None,
    ) -> Response:
        """Get Valid subscription names from Central.

        Args:
            service_category (str, optional): Service category - dm/network
            device_type (str, optional): Device Type - iap/cap/switch/boc/controller

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/config"

        params = {
            'service_category': service_category,
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def assign_licenses(self, serials: Union[str, List[str]], services: Union[str, List[str]]) -> Response:
        """Assign subscription to a device.

        // Used indirectly by add device when --license <license> is provided and batch add devices with license //

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/assign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def unassign_licenses(self, serials: Union[str, List[str]], services: Union[str, List[str]]) -> Response:
        """Unassign subscription(s) from device(s).

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/unassign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    # TODO build aggregator to run report showing rogues/interfering/neighbors
    # async def wids_get_all(self):

    async def wids_get_rogue_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List Rogue APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/rogue_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def wids_get_interfering_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List Interfering APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/interfering_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def wids_get_suspect_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List suspect APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/suspect_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def wids_get_neighbor_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List neighbor APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/neighbor_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def wids_get_all(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """List all wids classifications.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
        # resp.output = [*resp.output, *batch_res[0].output, *batch_res[1].output, *batch_res[2].output]
        try:
            resp.output = [models.WIDS(**d).dict() for d in resp.output]
        except Exception as e:
            log.warning(f"dev note. pydantic conversion did not work\n{e}", show=True)

        return resp


    async def get_alerts(
        self,
        customer_id: str = None,
        group: str = None,
        label: str = None,
        serial: str = None,
        site: str = None,
        from_ts: int = None,
        to_ts: int = None,
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
            from_ts (int, optional): 1)start of duration within which alerts are raised
                2)described using Unix Epoch time in seconds  Default 30 days (max 90)
            to_ts (int, optional): 1)end of duration within which alerts are raised
                2)described using Unix Epoch time in seconds
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

        if not from_ts:
            from_ts = int(datetime.timestamp(datetime.today() - timedelta(days=1)))
        if ack in [True, False]:
            ack = str(ack).lower()

        if to_ts and to_ts <= from_ts:
            return Response(error=f"To timestamp ({to_ts}) can not be less than from timestamp ({from_ts})")

        params = {
            'customer_id': customer_id,
            'group': group,
            'label': label,
            'serial': serial,
            'site': site,
            'from_timestamp': from_ts,
            'to_timestamp': to_ts,
            'severity': severity,
            'search': search,
            # 'calculate_total': str(calculate_total),
            'type': type,
            'ack': ack,
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

    async def get_brach_health(
        self,
        name: str = None,
        column: int = None,
        reverse: bool = False,
        filters: dict = {},
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get data for all sites.

        Args:
            name (str, optional): site / label name or part of its name
            column (int, optional): Column to sort on
            reverse (bool, optional): Sort in reverse order:
                Valid Values: asc, desc
                * asc - Ascending, from A to Z.
                * desc - Descending, from Z to A.


            filters (str, optional): Site thresholds
                Valid Values: gt  (Greater than), lt  (Less than), gte (Greater than or equal to),
                lte (Less than or equal to)
                * All properties of a site can be used as filter parameters with a threshold
                * The range filters can be combined with the column names with "\__"  # noqa
                * For eg. /site?device_down\__gt=0 - Lists all sites that have more than 1 device in down state # noqa
                * For eg. /site?wan_uplinks_down\__lt=1 - Lists all sites that have less than 1 wan in down state # noqa
                * For eg. /site?device_up__gt=1&device_up\__lt=10 - Lists all sites that have 1-10 devices up # noqa


            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/branchhealth/v1/site"

        params = {
            "name": name,
            # "column": column,
            "order": "asc" if not reverse else "desc",
            # "wan_tunnels_down\__gt": "0",
            # "wan_uplinks_down\__gt": "0",
            # **filters,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

    async def get_archived_devices(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get Archived devices from device inventory.

        // Used by show archived //

        Args:
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 100.

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
        sort: str = '+name',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all portals with limited data.

        Args:
            sort (str, optional): + is for ascending  and - for descending order, Valid Values: name prepended with + or - i.e. +name.  Defaults to +name.
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

    async def get_visitors(
        self,
        portal_id: str,
        sort: str = '+name',
        filter_by: str = None,
        filter_value: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all visitors created against a portal.

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


    async def add_visitor(
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
        # API requires phone and email, but allows None/null as value depending on how portal is configured
        # user_data = utils.strip_none(user_data)

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
        if user_data:
            json_data["user"] = user_data

        return await self.post(url, json_data=json_data)

    # TODO validate IP address format
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
        upload_type: CloudAuthUploadType,
        file: Union[Path, str],
        ssid: str = None,
    ) -> Response:
        """Upload file.

        This doesn't work still sorting the format of FormData

        Args:
            upload_type (CloudAuthUploadType): Type of file upload  Valid Values: mpsk, mac
            file (Union[Path, str]): The csv file to upload
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
        upload_type: CloudAuthUploadType,
        file: Union[Path, str],
        ssid: str = None,
    ) -> Response:

        """Upload file.

        Args:
            upload_type (CloudAuthUploadType): Type of file upload  Valid Values: mpsk, mac
            file (Union[Path, str]): The csv file to upload
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
        headers = {
            "Authorization": f"Bearer {self.auth.central_info['token']['access_token']}",
            'Accept': 'application/json'
        }

        files = { "file": (file.name, file.open("rb"), "text/csv") }
        url=f"{self.auth.central_info['base_url']}{url}"

        for _ in range(2):
            _resp = requests.request("POST", url=url, params=params, files=files, headers=headers)
            output = f"[{_resp.reason}]" + " " + _resp.text.lstrip('[\n "').rstrip('"\n]')
            # Make requests Response look like aiohttp.ClientResponse
            _resp.status, _resp.method, _resp.url = _resp.status_code, "POST", URL(_resp.url)
            resp = Response(_resp, output=output, error=None if _resp.ok else _resp.reason, url=URL(url), elapsed=round(_resp.elapsed.total_seconds(), 2), status_code=_resp.status_code, rl_str="-")
            if "invalid_token" in resp.output:
                self.refresh_token()
                headers["Authorization"] = f"Bearer {self.auth.central_info['token']['access_token']}"
            else:
                break
        return resp

    async def cloudauth_upload_status(
        self,
        upload_type: CloudAuthUploadType,
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
