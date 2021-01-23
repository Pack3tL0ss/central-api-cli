# MIT License
#
# Copyright (c) 2020 Aruba, a Hewlett Packard Enterprise company
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# from pycentral.base import ArubaCentralBase
# import sys
# from centralcli import constants
# import pycentral.base
import asyncio
import json
# import functools
from typing import List, Tuple, Union
from pathlib import Path
from pycentral.base_utils import tokenLocalStoreUtil
from aiohttp import ClientSession

from . import MyLogger, config, cleaner, utils, log, ArubaCentralBase
from .response import Session, Response


DEFAULT_TOKEN_STORE = {
  "type": "local",
  "path": f"{config.dir.joinpath('.cache')}"
}


def get_conn_from_file(account_name, logger: MyLogger = log):
    """Creates an instance of class`pycentral.ArubaCentralBase` based on config file

    provided in the YAML/JSON config file:
        * keyword central_info: A dict containing arguments as accepted by class`pycentral.ArubaCentralBase`
        * keyword ssl_verify: A boolean when set to True, the python client validates Aruba Central's SSL certs.
        * keyword token_store: Optional. Defaults to None.

    :param filename: Name of a JSON/YAML file containing the keywords required for class:`pycentral.ArubaCentralBase`
    :type filename: str
    :return: An instance of class:`pycentral.ArubaCentralBase` to make API calls and manage access tokens.
    :rtype: class:`pycentral.ArubaCentralBase`
    """
    '''
    if "token" in self.central_info and self.central_info["token"]:
        if "access_token" not in self.central_info["token"]:
            self.central_info["token"] = self.getToken()
    else:
        self.central_info["token"] = self.getToken()

    if not self.central_info["token"]:
    '''
    central_info = config.data[account_name]
    token_store = config.get("token_store", DEFAULT_TOKEN_STORE)
    ssl_verify = config.get("ssl_verify", True)

    conn = ArubaCentralBase(central_info, token_store=token_store, logger=logger, ssl_verify=ssl_verify)
    token_cache = Path(tokenLocalStoreUtil(token_store,
                                           central_info["customer_id"],
                                           central_info["client_id"]))

    # always create token cache if it doesn't exist and always use it first
    # however if config has been modified more recently the tokens in the config will be tried first
    # if both fail user will be prompted for token (assuming no password in file)
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
        self.central = get_conn_from_file(account_name)
        super().__init__(central=self.central)

    # def prepare_request(func):
    #     @functools.wraps(func)
    #     async def aio_api_call(self, url: str, *args, params: dict = {}, headers: dict = None, **kwargs):
    #         f_url = self.central.central_info["base_url"] + url
    #         params = self.strip_none(params)
    #         headers = self.headers if headers is None else {**self.headers, **headers}
    #         return await func(self, f_url, *args, params=params, headers=headers, **kwargs)
    #     return aio_api_call

    # @prepare_request
    # def get(self, url, params: dict = {}, headers: dict = None, **kwargs) -> Response:
    #     pass
    async def _request(self, func, *args, **kwargs):
        async with ClientSession() as self.aio_session:
            return await func(*args, **kwargs)

    def request(self, func, *args, **kwargs):
        return asyncio.run(self._request(func, *args, **kwargs))

    async def get(self, url, params: dict = {}, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, params=params, headers=headers, **kwargs)

    async def post(self, url, params: dict = {}, payload: dict = None,
                   json_data: Union[dict, list] = None, headers: dict = None, **kwargs) -> Response:
        # if _json and payload:
        #     raise UserWarning("post method expects 1 of the 2 keys payload, json.  Providing Both is invalid\n"
        #                       f"post was provided:\n    payload: {payload}\n    _json: {_json}")
        # elif _json:
        #     payload = json.dumps(_json)

        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="POST", data=payload,
                                   json_data=json_data, params=params, headers=headers, **kwargs)
        # return Response(self.central, f_url, method="POST", data=payload, params=params, headers=headers, **kwargs)

    async def patch(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        # return Response(self.central, f_url, method="PATCH", data=payload, params=params, headers=headers, **kwargs)
        return await self.api_call(f_url, method="PATCH", data=payload, params=params, headers=headers, **kwargs)

    async def delete(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        return await self.api_call(f_url, method="DELETE", data=payload, params=params, headers=headers, **kwargs)
        # return Response(self.central, f_url, method="DELETE", data=payload, params=params, headers=headers, **kwargs)

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

    async def get_clients(self, *args: Tuple[str], group: str = None, swarm_id: str = None,
                          label: str = None, ssid: str = None,
                          serial: str = None, os_type: str = None,
                          cluster_id: str = None, band: str = None, mac: str = None) -> Response:
        if not args.count(str) > 0 or "all" in args:
            return await self._get_all_clients()
        elif "wired" in args:
            return await self._get_wired_clients()
        elif "wireless" in args:
            return await self._get_wireless_clients()
        elif mac:
            mac = utils.Mac(args)
            if mac.ok:
                return await self._get_client_details(mac)
            else:
                print(f"Invalid mac {mac}")
        else:
            print(f"Invalid arg {args}")

    async def _get_all_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                               serial: str = None, os_type: str = None, cluster_id: str = None, band: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "os_type", "cluster_id", "band"],
                        [group, swarm_id, label, ssid, serial, os_type, cluster_id, band]
                        ):
            if v:
                params[k] = v

        resp = await self._get_wireless_clients(**params)
        if resp.ok:
            wlan_resp = resp
            resp = await self._get_wired_clients(**params)
            if resp.ok:
                resp.output = wlan_resp.output + resp.output
                resp.output = cleaner.get_all_clients(resp.output)
        return resp

    async def _get_wireless_clients(self, group: str = None, swarm_id: str = None, label: str = None,
                                    ssid: str = None, serial: str = None, os_type: str = None,
                                    cluster_id: str = None, band: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "os_type", "cluster_id", "band"],
                        [group, swarm_id, label, ssid, serial, os_type, cluster_id, band]
                        ):
            if v:
                params[k] = v

        url = "/monitoring/v1/clients/wireless"
        return await self.get(url, params=params)

    async def _get_wired_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                                 serial: str = None, cluster_id: str = None, stack_id: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "cluster_id", "stack_id"],
                        [group, swarm_id, label, ssid, serial, cluster_id, stack_id]
                        ):
            if v:
                params[k] = v

        url = "/monitoring/v1/clients/wired"
        return await self.get(url, params=params)

    async def _get_client_details(self, mac: utils.Mac) -> Response:
        # TODO THIS IS SPECIFIC TO WIRED AS IS
        # need to check wireless if doesn't exist there check wired or see if there is generic wired/wlan method
        url = f"/monitoring/v1/clients/wired/{mac.url}"
        resp = await self.get(url)
        # check if client mac found then retry wireless if not
        return resp

    async def get_certificates(self) -> Response:  # VERIFIED
        url = "/configuration/v1/certificates"
        params = {"limit": 20, "offset": 0}
        return await self.get(url, params=params)

    async def post_certificates(self, name: str, cert_type: str, passphrase: str,
                                cert_data: str, format: str = "PEM") -> Response:
        """Upload a Certificate"""
        url = "/configuration/v1/certificates"
        payload = {
            "cert_name": name,
            "cert_type": cert_type,
            "cert_format": format,
            "passphrase": passphrase,
            "cert_data": cert_data
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

    # Query can be filtered by name, device_type, version, model or J number (for ArubaSwitch).
    async def get_all_templates_in_group(self, group: str, name: str = None,
                                         device_type: str = None,
                                         version: str = None, model: str = None) -> Response:
        params = {
            "offset": 0,
            "limit": 20,  # 20 is the max
            "template": name,
            "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
            "version": version,
            "model": model
        }
        url = f"/configuration/v1/groups/{group}/templates"
        return await self.get(url, params=params)

    async def update_existing_template(self, group: str, name: str, template: Path = None, payload: str = None,
                                       device_type: str = None, version: str = None, model: str = None) -> Response:
        url = f"/configuration/v1/groups/{group}/templates"
        params = {
            "name": name,
            "device_type": device_type,
            "version": version,
            "model": model
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
    async def _update_existing_template(self, group: str, name: str, template: Path = None, payload: str = None,
                                        device_type: str = None, version: str = None, model: str = None) -> Response:
        from pycentral.configuration import Templates
        templates = Templates()
        kwargs = {
            "group_name": group,
            "template_name": name,
            "device_type": device_type,
            "version": version,
            "model": model,
            "template_filename": str(template)
        }

        return templates.update_template(self.central, **kwargs)

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
        return Response(ok=True, output=all_templates, error="OK")

    async def get_sku_types(self):  # FAILED - "Could not verify access level for the URL."
        url = "/platform/orders/v1/skus"
        params = {"sku_type": "all"}
        return await self.get(url, params=params)

    async def get_all_devices(self) -> Response:  # VERIFIED
        url = "/platform/device_inventory/v1/devices"
        dev_types = ["iap", "switch", "gateway"]

        # loop = asyncio.get_event_loop()
        tasks = [self.get(url, params={"sku_type": dev_type})
                 for dev_type in dev_types]
        _ap, _switch, _gateway = await asyncio.gather(*tasks)
        # loop.close()

        _ap.output = [*_ap.output, *_switch.output, *_gateway.output]
        _ap.url = str(_ap.url).replace("sku_type=iap", "sku_type=<3 calls: ap, switch, gw>")
        return _ap

    async def get_all_devicesv2(self, **kwargs) -> Response:  # REVERIFIED
        dev_types = ["aps", "switches", "gateways"]
        _output = {}

        tasks = [self.get_devices(dev_type, **kwargs)
                 for dev_type in dev_types]
        ap, sw, gw = await asyncio.gather(*tasks)
        resp = ap
        vals = [ap.output, sw.output, gw.output]
        _output = {k: utils.listify(v) for k, v in zip(dev_types, vals) if v}

        if _output:
            # return just the keys common across all device types
            dicts = [{**{"type": k.rstrip("es")}, **{kk: vv for kk, vv in idx.items()}} for k, v in _output.items() for idx in v]
            common_keys = set.intersection(*map(set, dicts))
            resp.output = [{k: v for k, v in d.items() if k in common_keys} for d in dicts]

        return resp

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

    async def update_variables(self, serialnum: str, var_dict: dict) -> bool:
        url = f"/configuration/v1/devices/{serialnum}/template_variables"
        var_dict = json.dumps(var_dict)
        return await self.patch(url, payload=var_dict)

    async def get_last_known_running_config(self, serialnum: str) -> Response:
        url = f"/configuration/v1/devices/{serialnum}/configuration"
        headers = {"Accept": "multipart/form-data"}
        return await self.get(url, headers=headers)

    # TODO ignore sort parameter and sort output from any field.  Central is inconsistent as to what they support via sort
    async def get_devices(self, dev_type: str, group: str = None, label: str = None, stack_id: str = None,
                          status: str = None, fields: list = None, show_resource_details: bool = False,
                          calculate_client_count: bool = False, calculate_ssid_count: bool = False,
                          public_ip_address: str = None, limit: int = 100, offset: int = 0, sort: str = None):
        # pagenation limit default 100, max 1000

        _strip = ["self", "dev_type", "url", "_strip"]

        params = {k: v for k, v in locals().items() if k not in _strip and v}
        if dev_type == "switch":
            dev_type = "switches"
        elif dev_type == "gateway":
            dev_type = "gateways"

        if dev_type in ["aps", "gateways"]:  # TODO remove in favor of our own sort
            if params.get("sort", "").endswith("name"):
                del params["sort"]
                log.warning(f"name is not a valid sort option for {dev_type}, Output will have default Sort", show=True)
        url = f"/monitoring/v1/{dev_type}"  # (inside brackets = same response) switches, aps, [mobility_controllers, gateways]
        return await self.get(url, params=params, callback=cleaner.get_devices)

    async def get_dev_details(self, dev_type: str, serial: str) -> Response:
        dev_type = "switches" if dev_type == "switch" else dev_type
        dev_type = "gateways" if dev_type == "gateway" else dev_type
        dev_type = "aps" if dev_type == "ap" else dev_type
        url = f"/monitoring/v1/{dev_type}/{serial}"
        return await self.get(url, callback=cleaner.get_devices)

    async def get_ssids_by_group(self, group):
        url = "/monitoring/v1/networks"
        params = {"group": group}
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
        payload = {
                "name": name,
                "urls": utils.listify(urls)
                }
        return await self.post(url, _json=payload)

    async def bounce_poe(self, port: Union[str, int], serial_num: str = None, name: str = None, ip: str = None) -> Response:
        """Bounce PoE on interface, valid only for switches
        """
        # TODO allow bounce by name or ip
        # v2 method returns 'CSRF token missing or incorrect.'
        url = f"/device_management/v1/device/{serial_num}/action/bounce_poe_port/port/{port}"
        # need to check get_task_status with response.output["task_id"] from this request to get status
        # During testing cetral always returned QUEUED
        return await self.post(url)

    async def bounce_interface(self, port: Union[str, int], serial_num: str = None, name: str = None, ip: str = None) -> Response:
        """Bounce interface, valid only for switches
        """
        # TODO allow bounce by name or ip
        url = f"/device_management/v1/device/{serial_num}/action/bounce_interface/port/{port}"
        return await self.post(url)

    async def kick_users(self, serial_num: str = None, name: str = None, kick_all: bool = False,
                         mac: str = None, ssid: str = None, hint: Union[List[str], str] = None) -> Union[Response, None]:
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
            # pprint.pprint(resp.json())
        else:
            # TODO move this validation to the cli command
            return Response(ok=False, error="Missing Required Parameters")

    async def post_switch_ssh_creds(self, device_serial: str, username: str, password: str) -> Response:
        url = f"/configuration/v1/devices/{device_serial}/ssh_connection"
        payload = {
            "username": username,
            "password": password
        }
        # returns "Success"
        return await self.post(url, _json=payload)

    async def get_task_status(self, task_id):
        return await self.get(f"/device_management/v1/status/{task_id}")

    async def add_dev(self, mac: str, serial_num: str):
        """
        {'code': 'ATHENA_ERROR_NO_DEVICE',
        'extra': {'error_code': 'ATHENA_ERROR_NO_DEVICE',
                'message': {'available_device': [],
                            'blocked_device': [],
                            'invalid_device': [{'mac': '20:4C:03:26:28:4c',
                                                'serial': 'CNF7JSP0N0',
                                                'status': 'ATHENA_ERROR_DEVICE_ALREADY_EXIST'}]}},
        'message': 'Bad Request'}
        """
        url = "/platform/device_inventory/v1/devices"
        payload = [
                {
                    "mac": mac,
                    "serial": serial_num
                }
            ]

        return await self.post(url, payload=payload)
        # resp = requests.post(self.central.vars["base_url"] + url, headers=header, json=payload)
        # pprint.pprint(resp.json())

    async def verify_add_dev(self, mac: str, serial_num: str):
        """
        {
            'available_device': [],
            'blocked_device': [],
            'invalid_device': [
                                {
                                    'mac': '20:4C:03:26:28:4c',
                                    'serial': 'CNF7JSP0N0',
                                    'status': 'ATHENA_ERROR_DEVICE_ALREADY_EXIST'
                                }
                              ]
        }
        """
        url = "/platform/device_inventory/v1/devices/verify"
        payload = [
                {
                    "mac": mac,
                    "serial": serial_num
                }
            ]

        return await self.post(url, payload=payload)
        # resp = requests.post(self.central.vars["base_url"] + url, headers=header, json=payload)
        # pprint.pprint(resp.json())

    async def move_dev_to_group(self, group: str, serial_num: Union[str, list]) -> bool:
        url = "/configuration/v1/devices/move"
        if not isinstance(serial_num, list):
            serial_num = [serial_num]

        payload = {
                    "group": group,
                    "serials": serial_num
                  }

        # resp = requests.post(self.central.vars["base_url"] + url, headers=headers, json=payload)
        return await self.post(url, json_data=payload)

    async def get_audit_logs(self, log_id: str = None) -> Response:
        """Get all audit logs or details about a specifc log from Aruba Central

        Args:
            log_id (str, optional): The id of the log to return details for. Defaults to None.

        Returns:
            Response: Response object
        """
        # max limit 100 if you provide the parameter, otherwise no limit? returned 811 w/ no param
        url = "/platform/auditlogs/v1/logs"
        params = {"offset": 0, "limit": 100}
        if log_id:
            url = f"{url}/{log_id}"
            params = None
        return await self.get(url, params=params)

    async def get_ts_commands(self, dev_type: str) -> Response:
        # iap, mas, switch, controller
        url = "/troubleshooting/v1/commands"
        params = {"device_type": dev_type}
        return await self.get(url, params=params)

    async def start_ts_session(self, device_serial: str, dev_type: str, commands: Union[dict, List[dict]]) -> Response:
        url = f"/troubleshooting/v1/devices/{device_serial}"
        payload = {
            "device_type": dev_type,
            "commands": commands
        }
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
        params = {
            "period": time_frame,
            "result_order": order,
            "count": 250
        }
        return await self.get(url, params=params)

    async def get_ap_lldp_neighbor(self, device_serial: str) -> Response:
        url = f"/topology_external_api/apNeighbors/{device_serial}"
        return await self.get(url)

    async def do_multi_group_snapshot(self, backup_name: str, include_groups: Union[list, List[str]] = None,
                                      exclude_groups: Union[list, List[str]] = None, do_not_delete: bool = False) -> Response:
        """"Create new configuration backup for multiple groups."

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
            "exclude_groups": exclude_groups
        }
        payload = self.strip_none(payload)
        return await self.post(url, json_data=payload)

    async def get_snapshots_by_group(self, group: str):
        url = f"/configuration/v1/groups/{group}/snapshots"
        return await self.get(url)

    # TODO move to caas.py
    async def caasapi(self, group_dev: str, cli_cmds: list = None):
        if ":" in group_dev and len(group_dev) == 17:
            key = "node_name"
        else:
            key = "group_name"

        url = "/caasapi/v1/exec/cmd"

        cfg_dict = self.central.central_info
        params = {
            "cid": cfg_dict["customer_id"],
            key: group_dev
        }

        payload = {"cli_cmds": cli_cmds or []}

        return self.post(url, params=params, payload=payload)


if __name__ == "__main__":
    pass
