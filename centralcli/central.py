#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import time
from asyncio.proactor_events import _ProactorBasePipeTransport
from functools import wraps
from pathlib import Path
from typing import Dict, List, Literal, Tuple, Union

from aiohttp import ClientSession
from pycentral.base_utils import tokenLocalStoreUtil

from . import ArubaCentralBase, MyLogger, cleaner, config, log, utils
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
    central_info = config.data[account_name]
    token_store = config.get("token_store", DEFAULT_TOKEN_STORE)
    ssl_verify = config.get("ssl_verify", True)

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
        self.auth = get_conn_from_file(account_name)
        super().__init__(auth=self.auth)

    async def _request(self, func, *args, **kwargs):
        async with ClientSession() as self.aio_session:
            return await func(*args, **kwargs)

    def request(self, func, *args, **kwargs):
        """non async to async wrapper for all API calls

        Args:
            func (callable): One of the CentralApi methods

        Returns:
            centralcli.Response object
        """
        return asyncio.run(self._request(func, *args, **kwargs))

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

    async def patch(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="PATCH", data=payload, params=params, headers=headers, **kwargs)

    async def delete(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.auth.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="DELETE", data=payload, params=params, headers=headers, **kwargs)

    @staticmethod
    def strip_none(_dict: Union[dict, None]) -> Union[dict, None]:
        """strip all keys from a dict where value is NoneType"""

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

    async def del_certificates(self, name: str) -> Response:  # VERIFIED
        url = "/configuration/v1/certificates"
        return await self.delete(url, name)

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
        device_type: str = None,
        version: str = None,
        model: str = None,
    ) -> Response:
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
            device_type (str, optional): Device type of the template.  Valid Values: IAP,
                ArubaSwitch, CX, MobilityController
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

        return self.patch(url, params=params, files={"template": template_data})

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

        template_groups = groups = [g["name"] for g in groups if True in g.get("template group", {}).values()]
        all_templates = []
        for group in template_groups:
            resp = await self.get_all_templates_in_group(group, **params)
            if not resp.ok:
                return resp
            else:
                all_templates += resp.output
        return Response(ok=True, output=all_templates)

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

        tasks = [self.get_devices(dev_type, **kwargs) for dev_type in dev_types]
        ap, sw, gw = await asyncio.gather(*tasks)
        resp = ap
        vals = [ap.output, sw.output, gw.output]
        _output = {k: utils.listify(v) for k, v in zip(dev_types, vals) if v}

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
        sw_url = "cx_switches" if cx else "switches"
        url = f"/monitoring/v1/{sw_url}/{serial}/ports"

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

    async def update_variables(self, serialnum: str, **var_dict: dict) -> bool:
        url = f"/configuration/v1/devices/{serialnum}/template_variables"
        var_dict = json.dumps(var_dict)
        return await self.patch(url, payload=var_dict)

    async def get_last_known_running_config(self, serialnum: str) -> Response:
        url = f"/configuration/v1/devices/{serialnum}/configuration"
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
            "status": status,
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
        name: str = None,
        kick_all: bool = False,
        mac: str = None,
        ssid: str = None,
        hint: Union[List[str], str] = None,
    ) -> Union[Response, None]:
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
            return await self.post(url, payload=payload)
        else:
            # TODO move this validation to the cli command
            return Response(ok=False, error="Missing Required Parameters")

    async def post_switch_ssh_creds(self, device_serial: str, username: str, password: str) -> Response:
        url = f"/configuration/v1/devices/{device_serial}/ssh_connection"
        payload = {"username": username, "password": password}
        # returns "Success"
        return await self.post(url, _json=payload)

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
        if not stack:
            sw_url = "cx_switches" if cx else "switches"
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

    async def add_dev(self, mac: str, serial_num: str):
        url = "/platform/device_inventory/v1/devices"
        payload = [{"mac": mac, "serial": serial_num}]

        return await self.post(url, payload=payload)

    async def verify_add_dev(self, mac: str, serial_num: str):
        url = "/platform/device_inventory/v1/devices/verify"
        payload = [{"mac": mac, "serial": serial_num}]

        return await self.post(url, payload=payload)
        # pprint.pprint(resp.json())

    async def move_dev_to_group(self, group: str, serial_num: Union[str, list]) -> bool:
        url = "/configuration/v1/devices/move"
        if not isinstance(serial_num, list):
            serial_num = [serial_num]

        payload = {"group": group, "serials": serial_num}

        return await self.post(url, json_data=payload)

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
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination Defaults to 0.
            limit (int, optional): Maximum number of audit events to be returned Defaults to 100.

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
            "app_id": app_id,
            "offset": offset,
            "limit": limit,
        }

        if log_id:
            url = f"{url}/{log_id}"
            params = None

        return await self.get(url, params=params, callback=cleaner.get_audit_logs)

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

    async def caasapi(self, group_dev: str, cli_cmds: list = None):
        if ":" in group_dev and len(group_dev) == 17:
            key = "node_name"
        else:
            key = "group_name"

        url = "/caasapi/v1/exec/cmd"

        cfg_dict = self.auth.central_info
        params = {"cid": cfg_dict["customer_id"], key: group_dev}

        payload = {"cli_cmds": cli_cmds or []}

        return self.post(url, params=params, payload=payload)


if __name__ == "__main__":
    pass
