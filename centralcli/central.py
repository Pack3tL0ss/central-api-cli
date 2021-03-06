#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from enum import Enum
import json
import time
from asyncio.proactor_events import _ProactorBasePipeTransport
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Literal, Tuple, Union

from aiohttp import ClientSession
import aiohttp
from pycentral.base_utils import tokenLocalStoreUtil

from . import ArubaCentralBase, MyLogger, cleaner, config, log, utils, constants
from .response import Response, Session


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


class WlanType(str, Enum):
    employee = "employee"
    guest = "guest"


def multipartify(data, parent_key=None, formatter: callable = None) -> dict:
    if formatter is None:
        formatter = lambda v: (None, v)  # noqa Multipart representation of value

    if type(data) is not dict:
        return {parent_key: formatter(data)}

    converted = []

    for key, value in data.items():
        current_key = key if parent_key is None else f"{parent_key}[{key}]"
        if type(value) is dict:
            converted.extend(multipartify(value, current_key, formatter).items())
        elif type(value) is list:
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
    ssl_verify = config.data.get("ssl_verify", True)

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


class BatchRequest:
    def __init__(self, func: callable, args: Any = (), **kwargs: dict) -> None:
        """Contructor object for for api requests.

        Used to pass multiple requests into CentralApi batch_request method for parallel
        execution.

        Args:
            func (callable): The CentralApi method to execute.
            args (Any, optional): args passed on to method. Defaults to ().
            kwargs (dict, optional): kwargs passed on to method. Defaults to {}.
        """
        self.func = func
        self.args: Union[list, tuple] = args if isinstance(args, (list, tuple)) else (args, )
        self.kwargs = kwargs


class CentralApi(Session):
    def __init__(self, account_name: str = "central_info"):
        self.silent = False  # toggled in _batch_request to squelch Auto logging in Response
        self.BatchRequest = BatchRequest
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

    async def _request(self, func, *args, **kwargs):
        async with ClientSession() as self.aio_session:
            return await func(*args, **kwargs)

    def request(self, func: callable, *args, **kwargs) -> Response:
        """non async to async wrapper for all API calls

        Args:
            func (callable): One of the CentralApi methods

        Returns:
            centralcli.response.Response object
        """
        return asyncio.run(self._request(func, *args, **kwargs))

    async def _batch_request(self, api_calls: List[BatchRequest],) -> List[Response]:
        async with ClientSession() as self.aio_session:
            # Always run first call solo to ensure access token validity
            self.silent = True
            resp = await api_calls[0].func(
                *api_calls[0].args,
                **api_calls[0].kwargs
                )
            if not resp or len(api_calls) == 1:
                return [resp]

            m_resp = await asyncio.gather(
                *[call.func(*call.args, **call.kwargs) for call in api_calls[1:]]
            )
            self.silent = False

            return [resp, *m_resp]

    def batch_request(self, api_calls: List[BatchRequest],) -> List[Response]:
        """non async to async wrapper for multiple parallel API calls

        First entry is ran alone, if successful the remaining calls
        are made in parallel.

        Args:
            api_calls (List[BatchRequest]): List of BatchRequest objects.

        Returns:
            List[Response]: List of centralcli.response.Response objects.
        """
        return asyncio.run(self._batch_request(api_calls))

    async def get(self, url, params: dict = {}, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, params=params, headers=headers, **kwargs)

    async def post(
        self, url, params: dict = {}, payload: dict = None, json_data: Union[dict, list] = None, headers: dict = None, **kwargs
    ) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        if json_data:
            json_data = self.strip_none(json_data)
        return await self.api_call(
            f_url, method="POST", data=payload, json_data=json_data, params=params, headers=headers, **kwargs
        )

    async def put(
        self, url, params: dict = {}, payload: dict = None, json_data: Union[dict, list] = None, headers: dict = None, **kwargs
    ) -> Response:

        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(
            f_url, method="PUT", data=payload, json_data=json_data, params=params, headers=headers, **kwargs
        )

    async def patch(self, url, params: dict = {}, payload: dict = None,
                    json_data: Union[dict, list] = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="PATCH", data=payload,
                                   json_data=json_data, params=params, headers=headers, **kwargs)

    async def delete(
        self,
        url,
        params: dict = {},
        payload: dict = None,
        json_data: Union[dict, list] = None,
        headers: dict = None,
        **kwargs
    ) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="DELETE", data=payload,
                                   json_data=json_data, params=params, headers=headers, **kwargs)

    @staticmethod
    def strip_none(_dict: Union[dict, None]) -> Union[dict, None]:
        """strip all keys from a dict where value is NoneType"""
        if not isinstance(_dict, dict):
            return _dict

        return _dict if _dict is None else {k: v for k, v in _dict.items() if v is not None}

    # doesn't appear to work. referenced in swagger to get listing of types (New Device Inventory: Get Devices...)
    async def get_dev_types(self):
        url = "/platform/orders/v1/skus?sku_type=all"
        return await self.get(url)

    async def get_ap(self) -> Response:
        url = "/monitoring/v1/aps"
        return await self.get(url)

    async def get_swarms_by_group(self, group: str) -> Response:
        url = "/monitoring/v1/swarms"
        params = {"group": group}
        return await self.get(url, params=params)

    async def get_swarm_details(self, swarm_id: str) -> Response:
        url = f"/monitoring/v1/swarms/{swarm_id}"
        return await self.get(url)

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
        sort_by: str = None,
        offset: int = 0,
        limit: int = 500,
        # **kwargs,
    ) -> Response:
        """Get client details."""
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

        if "mac" in args and args.index("mac") < len(args):
            _mac = utils.Mac(
                args[args.index("mac") + 1],
                fuzzy=True,
            )
            if _mac.ok:
                mac = _mac
            else:
                return Response(error="INVALID MAC", output=f"The Provided MAC {_mac} Appears to be invalid.")

        # if not args.count(str) > 0 or "all" in args:
        if not args or "all" in args:
            if mac:
                return await self.get_client_details(mac.cols,)  # **kwargs)
            else:
                return await self.get_all_clients(**all_params,)  # **kwargs)
        elif "wired" in args:
            if mac:
                return await self.get_client_details(mac.cols, dev_type="wired",)  # **kwargs)
            else:
                return await self.get_wired_clients(**wired_params,)  # **kwargs)
        elif "wireless" in args:
            if mac:
                return await self.get_client_details(mac.cols, dev_type="wireless",)  # **kwargs)
            else:
                return await self.get_wireless_clients(**wlan_params,)  # **kwargs)
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
        sort_by: str = None,
        offset: int = 0,
        limit: int = 500,
        # **kwargs,
    ) -> Response:
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

        resp = await self.get_wireless_clients(**{**params, **wlan_only_params},)  # **kwargs)
        if resp.ok:
            wlan_resp = resp
            wired_resp = await self.get_wired_clients(**{**params, **wired_only_params},)  # **kwargs)
            if wired_resp.ok:
                resp.output = wlan_resp.output + wired_resp.output
                # resp.output = cleaner.get_clients(resp.output)
                if sort_by:  # TODO
                    print("sort_by not implemented yet.")
        return resp

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
        calculate_total: bool = None,
        sort_by: str = None,
        offset: int = 0,
        limit: int = 500,
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
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

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
            "calculate_total": calculate_total,
            # 'sort': sort_by,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params,)  # callback=cleaner.get_clients, **kwargs)

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
        calculate_total: bool = None,
        sort_by: str = None,
        offset: int = 0,
        limit: int = 500,
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
            # sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
            #     '+macaddr'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

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
            "calculate_total": calculate_total,
            # 'sort': sort_by,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params,)  # callback=cleaner.get_clients, **kwargs)

    async def get_client_details(self, macaddr: str, dev_type: str = None, **kwargs) -> Response:
        """Get Wired/Wireless Client Details.

        Args:
            macaddr (str): MAC address of the Wireless Client to be queried
                API will return results matching a partial Mac

        Returns:
            Response: CentralAPI Response object
        """
        # This logic is here because Central has both methods, but given a wlan client mac
        # central will return the client details even when using the wired url

        # Mac match logic is jacked in central
        # given a client with a MAC of ac:37:43:4a:8e:fa
        #
        # Make MAC invlalid (changed last octet):
        #   ac:37:43:4a:8e:ff No Match
        #   ac37434a8eff No Match
        #   ac:37:43:4a:8e-ff  Returns MATCH
        #   ac:37:43:4a:8eff  Returns MATCH
        #   ac:37:43:4a:8eff  Returns MATCH
        #   ac37434a8e:ff  Returns MATCH
        #   ac-37-43-4a-8e-ff Return MATCH
        #   ac37.434a.8eff Returns MATCH
        if not dev_type:
            for _dev_type in ["wired", "wireless"]:
                url = f"/monitoring/v1/clients/{_dev_type}/{macaddr}"
                resp = await self.get(url, callback=cleaner.get_clients, **kwargs)
                if resp:
                    break

            return resp
        else:
            url = f"/monitoring/v1/clients/{dev_type}/{macaddr}"
            return await self.get(url, callback=cleaner.get_clients, **kwargs)

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

    async def post_certificates(
        self, name: str, cert_type: str, passphrase: str, cert_data: str, format: str = "PEM"
    ) -> Response:
        """Upload a Certificate"""
        url = "/configuration/v1/certificates"
        payload = {
            "cert_name": name,
            "cert_type": cert_type,
            "cert_format": format,
            "passphrase": passphrase,
            "cert_data": cert_data,
        }
        return await self.post(url, payload=payload)

    async def get_template(self, group: str, template: str) -> Response:
        url = f"/configuration/v1/groups/{group}/templates/{template}"
        return await self.get(url)

    async def get_template_details_for_device(self, device_serial: str, details: bool = False) -> Response:
        url = f"/configuration/v1/devices/{device_serial}/config_details"
        headers = {"Accept": "multipart/form-data"}
        params = {"details": details}
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
    # and it doesn't catch all exceptions so possible to get exception when eval resp... our Response object is better IMHO
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

    async def _get_group_names(self) -> Response:  # REVERIFIED
        url = "/configuration/v2/groups"
        params = {"offset": 0, "limit": 20}  # 20 is the max
        resp = await self.get(url, params=params, callback=cleaner._get_group_names)
        return resp

    async def get_all_groups(self) -> Response:
        url = "/configuration/v2/groups/template_info"
        resp = await self._get_group_names()
        if not resp.ok:
            return resp
        else:
            all_groups = ",".join(resp.output)
            params = {"groups": all_groups}
        return await self.get(url, params=params, callback=cleaner.get_all_groups)

    async def get_all_templates(self, groups: List[dict] = None, **params) -> Response:
        """Get data for all defined templates from Aruba Central

        Args:
            groups (List[dict], optional): List of group dictionaries (Used to send cache vs trigerring a fresh API call).
                                           Defaults to None (Central will first be queried for all groups)

        Returns:
            Response: centralcli Response Object
        """
        if not groups:
            resp = await self.get_all_groups()
            if resp:
                groups = resp.output
            else:
                return resp

        template_groups = [g["name"] for g in groups if True in g.get("template group", {}).values()]
        reqs = [self.BatchRequest(self.get_all_templates_in_group, group, **params) for group in template_groups]
        responses = await self._batch_request(reqs)
        failed = [r for r in responses if not r]
        if failed:
            return failed[-1]

        all_templates = [rr for r in responses for rr in r.output]
        responses[-1].output = all_templates

        return responses[-1]

    async def get_sku_types(self):  # FAILED - "Could not verify access level for the URL."
        url = "/platform/orders/v1/skus"
        params = {"sku_type": "all"}
        return await self.get(url, params=params)

    async def get_all_devices(self) -> Response:
        """Get All Devices. Not Used by CLI replaced with get_all_devicesv2"""
        url = "/platform/device_inventory/v1/devices"
        dev_types = ["iap", "switch", "gateway"]

        tasks = [self.get(url, params={"sku_type": dev_type}) for dev_type in dev_types]
        _ap, _switch, _gateway = await asyncio.gather(*tasks)

        _ap.output = [*_ap.output, *_switch.output, *_gateway.output]
        _ap.url = str(_ap.url).replace("sku_type=iap", "sku_type=<3 calls: ap, switch, gw>")
        return _ap

    async def get_all_devicesv2(self, **kwargs) -> Response:
        dev_types = ["aps", "switches", "gateways"]  # mobility_controllers seems same as gw
        _output = {}

        reqs = [self.BatchRequest(self.get_devices, dev_type, **kwargs) for dev_type in dev_types]
        res = await self._batch_request(reqs)
        _failures = [idx for idx, r in enumerate(res) if not (r)]
        if _failures:
            return res[_failures[0]]

        resp = res[-1]
        _output = {k: utils.listify(v) for k, v in zip(dev_types, [r.output for r in res]) if v}
        resp.raw = {k: utils.listify(v) for k, v in zip(dev_types, [r.raw for r in res]) if v}

        if _output:
            # return just the keys common across all device types
            dicts = [{**{"type": k.rstrip("es")}, **{kk: vv for kk, vv in idx.items()}} for k, v in _output.items() for idx in v]
            common_keys = set.intersection(*map(set, dicts))

            _output = [{k: d[k] for k in common_keys} for d in dicts]
            resp.output = _output

        return resp

    async def get_switch_ports(self, serial: str, slot: str = None, cx: bool = False) -> Response:
        """Switch Ports Details.

        Args:
            serial (str): Serial number of switch to be queried
            slot (str, optional): Slot name of the ports to be queried {For chassis type switches
                only}.
            cx (bool, optional): Set to True for ArubaOS-CX switches.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO remove once confirmed the cx_ urls have been depricated in favor of the logical route of having the
        # one url work for both.
        # sw_url = "cx_switches" if cx else "switches"
        # url = f"/monitoring/v1/{sw_url}/{serial}/ports"
        url = f"/monitoring/v1/switches/{serial}/ports"

        params = {"slot": slot}

        return await self.get(url, params=params)

    async def get_dev_by_type(self, dev_type: str) -> Response:  # VERIFIED
        url = "/platform/device_inventory/v1/devices"
        # iap, switch, gateway|boc
        if dev_type.lower() in ["aps", "ap"]:
            dev_type = "iap"
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
        headers = {"Content-Type": "multipart/form-data"}

        json_data = {device_serial: var_dict}
        #     **{
        #         'total': len(var_dict),
        #         '_sys_serial': device_serial,
        #         '_sys_lan_mac': device_mac,
        #     },
        #     **var_dict
        # }
        # data = self._make_form_data(json_data)
        data = multipartify(json_data)
        # TODO this doesn't work yet. Trying to figure out what API expects

        return await self.patch(url, headers=headers, payload=data)

    async def get_device_configuration(self, device_serial: str) -> Response:
        """Get last known running configuration for a device.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/configuration"
        headers = {"Accept": "multipart/form-data"}

        return await self.get(url, headers=headers)

    async def get_devices(
        self,
        dev_type: Literal["switches", "aps", "gateways", "mobility_controllers"],
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
        calculate_client_count: bool = False,
        calculate_ssid_count: bool = False,
        macaddr: str = None,
        public_ip_address: str = None,
        site: str = None,
        limit: int = 500,  # max allowed 1000
        offset: int = 0,
        sort: str = None,
    ) -> Response:

        params = {
            "group": group,
            "label": label,
            "swarm_id": swarm_id,
            "site": site,
            "serial": serial,
            "macaddr": macaddr,
            "model": model,
            "cluster_id": cluster_id,
            "stack_id": stack_id,
            "status": None if not status else status.title(),
            "fields": fields,
            "show_resource_details": str(show_resource_details).lower(),
            "calculate_client_count": str(calculate_client_count).lower(),
            "calculate_ssid_count": str(calculate_ssid_count).lower(),
            "public_ip_address": public_ip_address,
            "limit": limit,
            "offset": offset,
        }

        url = f"/monitoring/v1/{dev_type}"  # (inside brackets = same response) switches, aps, [mobility_controllers, gateways]
        if dev_type == "aps" and "internal" in self.auth.central_info["base_url"]:
            url = url.replace("v1", "v2")
        # TODO move cleaner into cli ... make this sep library dependency
        # TODO sort not implemented yet
        return await self.get(url, params=params, callback=cleaner.get_devices, callback_kwargs={"sort": sort})

    async def get_dev_details(self, dev_type: str, serial: str) -> Response:
        url = f"/monitoring/v1/{dev_type}/{serial}"
        return await self.get(url, callback=cleaner.get_devices)

    async def monitoring_get_mcs(
        self,
        group: str = None,
        label: str = None,
        site: str = None,
        status: str = None,
        macaddr: str = None,
        model: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Mobility Controllers.

        You can only specify one of group, label, site

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            status (str, optional): Filter by Mobility Controller status
            macaddr (str, optional): Filter by Mobility Controller MAC address
            model (str, optional): Filter by Mobility Controller Model
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, ip_address, model, firmware_version, labels, ap_count, usage
            calculate_total (bool, optional): Whether to calculate total Mobility Controllers
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr, -macaddr.
                Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/mobility_controllers"

        params = {
            "group": group,
            "label": label,
            "site": site,
            "status": status,
            "macaddr": macaddr,
            "model": model,
            "fields": fields,
            "calculate_total": calculate_total,
            "sort": sort,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

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

    async def get_gateways_by_group(self, group):
        url = "/monitoring/v1/mobility_controllers"
        params = {"group": group}
        return await self.get(url, params=params)

    async def get_group_for_dev_by_serial(self, serial_num):
        return await self.get(f"/configuration/v1/devices/{serial_num}/group")

    async def get_dhcp_client_info_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/dhcp_clients"
        params = {"reservation": False}
        return await self.get(url, params=params)

    async def get_vlan_info_by_gw(self, serial_num):
        return await self.get(f"/monitoring/v1/mobility_controllers/{serial_num}/vlan")

    async def get_uplink_info_by_gw(self, serial_num, timerange: str = "3H"):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks"
        params = {"timerange": timerange}
        return await self.get(url, params)

    async def get_uplink_tunnel_stats_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks/tunnel_stats"
        return await self.get(url)

    async def get_uplink_state_by_group(self, group: str) -> Response:
        url = "/monitoring/v1/mobility_controllers/uplinks/distribution"
        params = {"group": group}
        return await self.get(url, params)

    async def get_all_sites(self) -> Response:
        return await self.get("/central/v2/sites", callback=cleaner.sites)

    async def get_site_details(self, site_id):
        return await self.get(f"/central/v2/sites/{site_id}", callback=cleaner.sites)

    async def get_events_by_group(self, group: str) -> Response:  # VERIFIED
        url = "/monitoring/v1/events"
        params = {"group": group}
        return await self.get(url, params=params)

    async def get_all_webhooks(self) -> Response:
        url = "/central/v1/webhooks"
        return await self.get(url)

    async def post_add_webhook(self, name: str, *urls: Union[str, List[str]]) -> Response:
        url = "/central/v1/webhooks"
        payload = {"name": name, "urls": utils.listify(urls)}
        return await self.post(url, _json=payload)

    async def get_ap_neighbors(self, device_serial: str) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{device_serial}"

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
        """Generic Action Command for bouncing interface or POE (power-over-ethernet) port.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
            port (str): Specify interface port in the format of port number for devices of type HPPC
                Switch or slot/chassis/port for CX Switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v2/device/{serial}/action/{command}"

        json_data = {"port": port}

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

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
                reboot: supported by IAP/Controllers/MAS Switches/Aruba Switches
                blink_led_on: Use this command to enable the LED display, supported by IAP/Aruba Switches
                blink_led_off: Use this command to enable the LED display, supported by IAP/Aruba Switches
                blink_led: Use this command to blink LED display, Supported on Aruba Switches
                erase_configuration : Factory default the switch.  Supported on Aruba Switches
                save_configuration: Saves the running config and displays the running configuration on the screen
                    supported by IAP/Aruba Switches
                halt : This command performs a shutdown of the device, supported by Controllers alone.
                config_sync : This commands performs full refresh of the device config, supported by Controllers alone
            duration (int, Optional): Number of seconds to blink_led only applies to blink_led and blink_led_on

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}"

        resp = await self.post(url)
        if resp and duration and "blink_led" in command and "off" not in command:
            print(f"Blinking Led... {duration}. ", end="")
            for i in range(1, duration):
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

    async def update_ssh_creds(self, device_serial: str, username: str, password: str) -> Response:
        """Set Username, password required for establishing SSH connection to switch.

        This method only applies to switches

        Args:
            device_serial (str): Serial number of the switch.
            username (str): SSH username
            password (str): SSH password

        Returns:
            Response: CentralAPI Response object
            Successful Response body (Response.output): "Success"
        """
        url = f"/configuration/v1/devices/{device_serial}/ssh_connection"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def get_task_status(self, task_id):
        return await self.get(f"/device_management/v1/status/{task_id}")

    async def get_switch_vlans(
        self,
        iden: str,
        stack: bool = False,
        cx: bool = False,
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
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """Get vlan info for switch (CX and SW).

        Args:
            iden (str): Serial Number of Stack ID, Identifies the dev to return VLANs from.
            stack (bool, optional): Set to True for stack. Default: False
            cx: (bool, optional): Set to True for ArubaOS-CX. Default: False
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
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO looks like we can remove references to cx specific methods, they don't work
        # schema not reflecting that wasted my time.
        if not stack:
            # sw_url = "cx_switches" if cx else "switches"
            sw_url = "switches"
        else:
            sw_url = "cx_switch_stacks" if cx else "switch_stacks"

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
            "calculate_total": calculate_total,
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

    async def get_controller_vlans(self, serial: str) -> Response:
        """Get Mobility Controllers VLAN details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/vlan"

        return await self.get(url)

    async def get_ts_commands(self, dev_type: Literal['iap', 'mas', 'switch', 'controller']) -> Response:
        url = "/troubleshooting/v1/commands"
        params = {"device_type": dev_type}
        return await self.get(url, params=params)

    async def start_ts_session(self, device_serial: str, dev_type: str, commands: Union[dict, List[dict]]) -> Response:
        url = f"/troubleshooting/v1/devices/{device_serial}"
        payload = {"device_type": dev_type, "commands": commands}
        return await self.post(url, _json=payload)

    async def get_ts_output(self, device_serial: str, ts_id: int) -> Response:
        url = f"/troubleshooting/v1/devices/{device_serial}"
        params = {"session_id": ts_id}
        return await self.get(url, params=params)

    async def clear_ts_session(self, device_serial: str, ts_id: int) -> Response:
        # returns a str
        url = f"/troubleshooting/v1/devices/{device_serial}"
        params = {"session_id": ts_id}
        return await self.get(url, params=params)

    async def get_ts_id_by_serial(self, device_serial: str) -> Response:
        url = f"/troubleshooting/v1/devices/{device_serial}/session"
        return await self.get(url)

    async def get_sdwan_dps_policy_compliance(self, time_frame: str = "last_week", order: str = "best") -> Response:
        url = "/sdwan-mon-api/external/noc/reports/wan/policy-compliance"
        params = {"period": time_frame, "result_order": order, "count": 250}
        return await self.get(url, params=params)

    async def get_ap_lldp_neighbor(self, device_serial: str) -> Response:
        url = f"/topology_external_api/apNeighbors/{device_serial}"
        return await self.get(url)

    async def do_multi_group_snapshot(
        self,
        backup_name: str,
        include_groups: Union[list, List[str]] = None,
        exclude_groups: Union[list, List[str]] = None,
        do_not_delete: bool = False,
    ) -> Response:
        """ "Create new configuration backup for multiple groups."

        Args:
            backup_name (str): Name of Backup
            include_groups (Union[list, List[str]], optional): Groups to include in Backup. Defaults to None.
            exclude_groups (Union[list, List[str]], optional): Groups to Exclude in Backup. Defaults to None.
            do_not_delete (bool, optional): Flag to represent if the snapshot can be deleted automatically
                by system when creating new snapshot or not. Defaults to False.

        *Either include_groups or exclude_groups should be provided, but not both.

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

    async def get_mc_tunnels(self, serial: str, timerange: str, limit: int = 250, offset: int = 0) -> Response:
        """Mobility Controllers Uplink Tunnel Details.

        Args:
            serial (str): Serial number of mobility controller to be queried
            timerange (str): Time range for tunnel stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
            limit (int, optional): Pagination limit. Max: 1000 Defaults to 250.
            offset (int, optional): Pagination offset Defaults to 0.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/tunnels"

        params = {"timerange": timerange, offset: offset, limit: limit}

        return await self.get(url, params=params)

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
        # max limit 100 if you provide the parameter, otherwise no limit? returned 811 w/ no param
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

        json_data = {
            "site_name": site_name,
            "site_address": {"address": address, "city": city, "state": state, "country": country, "zipcode": zipcode},
            "geolocation": {"latitude": latitude, "longitude": longitude},
        }
        if site_list:
            resp = await self.post(url, json_data=site_list[0])
            if not resp:
                return resp
            if len(site_list) > 1:
                resp_list = cleaner._unlist(
                    [await asyncio.gather(self.post(url, json_data=_json, callback=cleaner._unlist)) for _json in site_list[1:]]
                )
                # TODO make multi response packing function
                resp.output = utils.listify(resp.output)
                resp.output += [r.output for r in resp_list]
                return resp
        else:
            return await self.post(url, json_data=json_data, callback=cleaner._unlist)

    async def create_group(
        self,
        group: str,
        group_password: str,
        wired_tg: bool = False,
        wlan_tg: bool = False
    ) -> Response:
        """Create new group.

        Args:
            group (str): Group Name
            group_password (str): local admin password used to access devices added to the group.
            wired_tg (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            wlan_tg (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups"

        json_data = {
            "group": group,
            "group_attributes": {
                "group_password": group_password,
                "template_info": {
                    "Wired": wired_tg,
                    "Wireless": wlan_tg
                }
            }
        }

        return await self.post(url, json_data=json_data)

    async def clone_group(self, clone_group: str, new_group: str) -> Response:
        """Clone and create new group.

        Args:
            clone_group (str): Group to be cloned.
            new_group (str): Name of group to be created based on clone.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups/clone"

        json_data = {
            'group': new_group,
            'clone_group': clone_group
        }

        return await self.post(url, json_data=json_data)

    async def update_group(
        self,
        group: str,
        group_password: str,
        template_group: bool
    ) -> Response:
        """Update existing group.

        Args:
            group (str): Name of the group to be updated.
            group_password (str): - GET API will always return empty,  This is mandatory for POST
                and PATCH APIs.
                - The password set in the group API is applicable for configuration that are done
                from UI, we ignore the password for templates.
                - To set the password for template group devices please use the following CLI in
                template file.                                     mgmt-user admin <actual_password>
                OR mgmt-user admin %admin_password%
            template_group (bool): Set to true if group is of type template.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}"

        json_data = {
            'group_password': group_password,
            'template_group': template_group
        }

        return await self.patch(url, json_data=json_data)

    async def update_group_properties(
        self,
        group: str,
        aos10: bool = None,
        monitor_only_switch: bool = None,
    ) -> Response:
        """Update properties for the given group.

        If aos10 argument is not provided an additional API call is made to gather the current aos_version
        and use the current setting as the argument is required by the Central API gw.

        Args:
            group (str): Group for which properties need to be updated.
            aos10 (bool, optional): If True will upgrade the group to AOS10
                Note: AOS10 groups can not be downgraded back to AOS8
            MonitorOnlySwitch (bool, optional): Indicates if the Monitor Only mode for switches is enabled for
                the group.  Defaults to False

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/properties"
        json_data = {}

        if aos10 is None:
            resp = await self.get_groups_properties(group)
            if not resp:
                return resp
            json_data['AOSVersion'] = resp[0]["properties"]["AOSVersion"]
        else:
            json_data['AOSVersion'] = "AOS_10X" if aos10 else "AOS_8X"

        if monitor_only_switch is not None:
            json_data['MonitorOnlySwitch'] = monitor_only_switch

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

    async def get_ap_settings(self, serial_number: str) -> Response:
        """Get an existing ap settings.

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
                    error=f"Update payload is missing required attributes: {missing}",
                    reason="INVALID"
                )

        return await self.post(url, json_data=json_data)

    # TODO NotUsed Yet
    async def get_dirty_diff(
        self,
        group: str,
        offset: int = 0,
        limit: int = 20
    ) -> Response:
        """Get dirty diff.

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

    # TODO NotUsed Yet
    async def get_groups_properties(self, groups: Union[str, List[str]]) -> Response:
        """Get properties set for groups.

        Args:
            groups (List[str]): Group list to fetch properties.
                Maximum 20 comma separated group names allowed.

        Returns:
            Response: CentralAPI Response object
        [
            {
                "data": [
                    {
                        "group": "Branch1",
                        "properties": {
                            "AOSVersion": "AOS_10X",
                            "MonitorOnlySwitch": false
                        }
                    }
                ]
            }
        ]
        """
        url = "/configuration/v1/groups/properties"

        # Central API method doesn't actually take a list it takes a string with
        # group names separated by comma (NO SPACES)
        groups = ",".join(utils.listify(groups))

        params = {
            'groups': groups
        }

        return await self.get(url, params=params)

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

    async def send_command_to_swarm(
        self,
        swarm_id: str,
        command: Literal[
            "reboot_swarm",
            "erase_configuration",
        ]
    ) -> Response:
        """Generic commands for swarm.

        Args:
            swarm_id (str): Swarm ID of device
            command (str): Command mentioned in the description that is to be executed
                valid: 'reboot_swarm', 'erase_configuration'

        Returns:
            Response: CentralAPI Response object
        """
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
                    BatchRequest(self.delete, (f"{b_url}/{_id}",))
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

    async def configuration_clean_up_and_update_wlan_v2(self, group_name_or_guid: str,
                                                        wlan_name: str, essid: str, type: str,
                                                        hide_ssid: bool, vlan: str, zone: str,
                                                        wpa_passphrase: str,
                                                        wpa_passphrase_changed: bool,
                                                        is_locked: bool,
                                                        captive_profile_name: str,
                                                        bandwidth_limit_up: str,
                                                        bandwidth_limit_down: str,
                                                        bandwidth_limit_peruser_up: str,
                                                        bandwidth_limit_peruser_down: str,
                                                        access_rules: list) -> Response:
        """Update an existing WLAN and clean up unsupported fields.

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

        return await self.patch(url, json_data=json_data)

    async def configuration_update_wlan_v2(self, group_name_or_guid: str, wlan_name: str,
                                           essid: str, type: str, hide_ssid: bool, vlan: str,
                                           zone: str, wpa_passphrase: str,
                                           wpa_passphrase_changed: bool, is_locked: bool,
                                           captive_profile_name: str, bandwidth_limit_up: str,
                                           bandwidth_limit_down: str,
                                           bandwidth_limit_peruser_up: str,
                                           bandwidth_limit_peruser_down: str, access_rules: list) -> Response:
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

    async def get_upgrade_status(self, swarm_id: str = None, serial: str = None) -> Response:
        """Get firmware upgrade status.

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

    async def get_firmware_compliance(self, device_type: DevType, group: str = None) -> Response:
        """Get Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name. Defaults to None (Global Compliance)

        Returns:
            Response: CentralAPI Response object
        """
        # API method returns 404 if compliance is not set!
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.get(url, params=params)

    async def delete_firmware_compliance(self, device_type: str, group: str = None) -> Response:
        """Clear Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name. Defaults to None (Global Compliance)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.delete(url, params=params)

    async def move_devices_to_group(
        self,
        group: str,
        serial_nums: Union[str, List[str]],
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): Group Name to move device to.
            serials (List[str]): Serial numbers of devices to be added to group.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO report flawed API method
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

        resp = await self.post(url, json_data=json_data)

        # This method returns status 500 with msg that move is initiated on success.
        if not resp and resp.status == 500:
            match_str = "group move has been initiated, please check audit trail for details"
            if match_str in resp.output.get("description", ""):
                resp.ok = True

        return resp

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
        """Unassociate a site from a list of devices.

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

        # NOTE: This method returns 200 when failures occur.
        return await self.delete(url, json_data=json_data)

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

    async def add_devices(
        self,
        mac_address: str = None,
        serial_num: str = None,
        group: str = None,
        part_num: str = None,
        license: Union[str, List[str]] = None,
        device_list: List[Dict[str, str]] = None
    ) -> Response:
        """Add device(s) using Mac and Serial number (part_num also required for CoP)

        Either mac_address and serial_num or device_list (which should contain a dict with mac serial) are required.

        Args:
            mac_address (str, optional): MAC address of device to be added
            serial_num (str, optional): Serial number of device to be added
            group (str, optional): Add device to pre-provisioned group (additional API call is made)
            part_num (str, optional): Part Number is required for Central On Prem.
            license (str, optional): The subscription license to assign to device.
            device_list (List[Dict[str, str]], optional): List of dicts with mac, serial for each device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        if license:
            license_kwargs = [{"serials": [serial_num], "services": utils.listify(license)}]
        if serial_num and mac_address:
            if group:
                to_group = {group: [serial_num]}

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

            json_data = [{_keys.get(k, k): v for k, v in d.items() if k != "group"} for d in device_list]

            to_group = {d["group"]: [] for d in device_list}
            _ = [to_group[d["group"]].append(d.get("serial_num", d.get("serial"))) for d in device_list]

            # license_args = [[], []]
            # by_ser = {d["serial_num"]: utils.listify(d.get("license")) for d in device_list if d.get("license")}
            # TODO most efficient pairing of possible lic/dev for fewest call
            # TODO license via list not implemented yet.

        else:
            raise ValueError("mac_address and serial_num or device_list is required")

        if to_group or license_kwargs:
            br = self.BatchRequest
            reqs = [
                br(self.post, url, json_data=json_data),
            ]
            if to_group:
                group_reqs = [br(self.assign_devices_to_group, (g, devs)) for g, devs in to_group.items()]
                reqs = [*reqs, *group_reqs]

            if license_kwargs:
                lic_reqs = [br(self.assign_licenses, **kwargs) for kwargs in license_kwargs]
                reqs = [*reqs, *lic_reqs]

            return await self._batch_request(reqs)
        else:
            return await self.post(url, json_data=json_data)

    async def assign_devices_to_group(self,  group: str, serial_nums: Union[List[str], str]) -> Response:
        """Assign devices to pre-provisioned group.

        Args:
            group (str): Group name
            serials (List[str]|str): Device serial number or list of device serial numbers.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/group/assign"
        serial_nums = utils.listify(serial_nums)

        json_data = {
            'serials': serial_nums,
            'group': group
        }

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
        passphrase: str,
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
        # TODO flawed API method, PUBLIC_CERT is not accepted
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
        elif not cert_file:
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

            # TODO converting from other formats to Base64 not implemented yet
            cert_data = cert_file.read_text()

        json_data = {
            'cert_name': cert_name,
            'cert_type': cert_type,
            'cert_format': cert_format,
            'passphrase': passphrase,
            'cert_data': cert_data
        }

        return await self.post(url, json_data=json_data)

    async def get_services_config(
        self,
        service_category: str = None,
        device_type: str = None
    ) -> Response:
        """Get services licensing config.

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

        Args:
            serials (List[str]): List of serial number of device.
            services (List[str]): List of service names. Call services/config API to get the list of
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


if __name__ == "__main__":
    pass
