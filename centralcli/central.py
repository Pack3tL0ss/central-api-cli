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
import json
from typing import List, Tuple, Union
from pathlib import Path
from pycentral.base_utils import tokenLocalStoreUtil
import csv

from . import MyLogger, Response, config, cleaner, log, ArubaCentralBase

try:
    from . import utils
except ImportError:
    from utils import Utils  # type: ignore
    utils = Utils()


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

    kwargs = {
        "central_info": central_info,
        "token_store": token_store,
        "ssl_verify": ssl_verify,
        "logger": logger
    }

    # conn = utils.spinner(constants.MESSAGES["SPIN_TXT_AUTH"], ArubaCentralBase, name="init_ArubaCentralBase", **kwargs)
    conn = ArubaCentralBase(**kwargs)
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
    else:
        if not conn.storeToken(conn.central_info.get("token")):
            log.warning("Failed to Store Token and token cache doesn't exist yet.", show=True)

    return conn


class CentralApi:
    def __init__(self, account_name: str):
        self.central = get_conn_from_file(account_name)

        self.headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                    }

    def get(self, url, params: dict = {}, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        headers = self.headers if headers is None else {**self.headers, **headers}
        params = self.strip_none(params)
        return Response(self.central, f_url, params=params, headers=headers, **kwargs)

    def post(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        headers = self.headers if headers is None else {**self.headers, **headers}
        return Response(self.central, f_url, method="POST", data=payload, params=params, headers=headers, **kwargs)

    def patch(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        params = self.strip_none(params)
        headers = self.headers if headers is None else {**self.headers, **headers}
        return Response(self.central, f_url, method="PATCH", data=payload, params=params, headers=headers, **kwargs)

    def delete(self, url, params: dict = {}, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        headers = self.headers if headers is None else {**self.headers, **headers}
        params = self.strip_none(params)
        return Response(self.central, f_url, method="DELETE", data=payload, params=params, headers=headers, **kwargs)

    @staticmethod
    def strip_none(_dict: Union[dict, None]) -> Union[dict, None]:
        """strip all keys from a dict where value is NoneType"""

        return _dict if _dict is None else {k: v for k, v in _dict.items() if v is not None}

    # doesn't appear to work. referenced in swagger to get listing of types (New Device Inventory: Get Devices...)
    def get_dev_types(self):
        url = "/platform/orders/v1/skus?sku_type=all"
        return self.get(url)

    def get_ap(self) -> Response:  # VERIFIED
        url = "/monitoring/v1/aps"
        return self.get(url)

    def get_swarms_by_group(self, group: str):
        url = "/monitoring/v1/swarms"
        params = {"group": group}
        return self.get(url, params=params)

    def get_swarm_details(self, swarm_id: str):
        url = f"/monitoring/v1/swarms/{swarm_id}"
        return self.get(url)

    def get_clients(self, *args: Tuple[str], group: str = None, swarm_id: str = None,
                    label: str = None, ssid: str = None,
                    serial: str = None, os_type: str = None,
                    cluster_id: str = None, band: str = None, mac: str = None) -> Response:
        if not args.count(str) > 0 or "all" in args:
            return self._get_all_clients()
        elif "wired" in args:
            return self._get_wired_clients()
        elif "wireless" in args:
            return self._get_wireless_clients()
        elif mac:
            mac = utils.Mac(args)
            if mac.ok:
                return self._get_client_details(mac)
            else:
                print(f"Invalid mac {mac}")
        else:
            print(f"Invalid arg {args}")

    def _get_all_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                         serial: str = None, os_type: str = None, cluster_id: str = None, band: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "os_type", "cluster_id", "band"],
                        [group, swarm_id, label, ssid, serial, os_type, cluster_id, band]
                        ):
            if v:
                params[k] = v

        resp = self._get_wireless_clients(**params)
        if resp.ok:
            wlan_resp = resp
            resp = self._get_wired_clients(**params)
            if resp.ok:
                resp.output = wlan_resp.output + resp.output
                resp.output = cleaner.get_all_clients(resp.output)
        return resp

    def _get_wireless_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                              serial: str = None, os_type: str = None, cluster_id: str = None, band: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "os_type", "cluster_id", "band"],
                        [group, swarm_id, label, ssid, serial, os_type, cluster_id, band]
                        ):
            if v:
                params[k] = v

        url = "/monitoring/v1/clients/wireless"
        return self.get(url, params=params)

    def _get_wired_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                           serial: str = None, cluster_id: str = None, stack_id: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "cluster_id", "stack_id"],
                        [group, swarm_id, label, ssid, serial, cluster_id, stack_id]
                        ):
            if v:
                params[k] = v

        url = "/monitoring/v1/clients/wired"
        return self.get(url, params=params)

    def _get_client_details(self, mac: utils.Mac) -> Response:
        # TODO THIS IS SPECIFIC TO WIRED AS IS
        # need to check wireless if doesn't exist there check wired or see if there is generic wired/wlan method
        url = f"/monitoring/v1/clients/wired/{mac.url}"
        resp = self.get(url)
        return resp

    def get_certificates(self) -> Response:  # VERIFIED
        url = "/configuration/v1/certificates"
        params = {"limit": 20, "offset": 0}
        return self.get(url, params=params)

    def post_certificates(self, name: str, cert_type: str, passphrase: str, cert_data: str, format: str = "PEM") -> Response:
        """Upload a Certificate"""
        url = "/configuration/v1/certificates"
        payload = {
            "cert_name": name,
            "cert_type": cert_type,
            "cert_format": format,
            "passphrase": passphrase,
            "cert_data": cert_data
            }
        return self.post(url, payload=payload)

    def del_certificates(self, name: str) -> Response:  # VERIFIED
        url = "/configuration/v1/certificates"
        return self.delete(url, name)

    def get_template(self, group: str, template: str) -> Response:
        url = f"/configuration/v1/groups/{group}/templates/{template}"
        return self.get(url)

    # Query can be filtered by name, device_type, version, model or J number (for ArubaSwitch).
    def get_all_templates_in_group(self, group: str, name: str = None,
                                   device_type: str = None, version: str = None, model: str = None) -> Response:
        params = {"offset": 0, "limit": 20}  # 20 is the max
        url = f"/configuration/v1/groups/{group}/templates"
        params = {
            "offset": 0,
            "limit": 20,
            "template": name,
            "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
            "version": version,
            "model": model
        }
        return self.get(url, params=params)

    def update_existing_template(self, group: str, name: str, template: Path = None, payload: str = None,
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
    def _update_existing_template(self, group: str, name: str, template: Path = None, payload: str = None,
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

    def get_all_groups(self) -> Response:  # REVERIFIED
        url = "/configuration/v2/groups"
        params = {"offset": 0, "limit": 20}  # 20 is the max
        resp = self.get(url, params=params, callback=cleaner.get_all_groups)
        return resp

    def get_sku_types(self):  # FAILED - "Could not verify access level for the URL."
        url = "/platform/orders/v1/skus"
        params = {"sku_type": "all"}
        return self.get(url, params=params)

    def get_all_devices(self) -> Response:  # VERIFIED
        url = "/platform/device_inventory/v1/devices"
        _output = []
        resp = None
        for dev_type in ["iap", "switch", "gateway"]:
            params = {"sku_type": dev_type}
            resp = self.get(url, params=params)
            if not resp.ok:
                break
            _output = [*_output, *resp.output["devices"]]

        if _output:
            resp.output = _output

        return resp

    def get_all_devicesv2(self, **kwargs) -> Response:  # REVERIFIED
        _output = {}
        resp = None

        for dev_type in ["aps", "switches", "gateways"]:
            resp = self.get_devices(dev_type, **kwargs)
            if not resp.ok:
                break
            _output[dev_type] = resp.output  # [dict, ...]

        if _output:
            # return just the keys common across all device types
            dicts = [{**{"type": k.rstrip("es")}, **{kk: vv for kk, vv in idx.items()}} for k, v in _output.items() for idx in v]
            common_keys = set.intersection(*map(set, dicts))
            resp.output = [{k: v for k, v in d.items() if k in common_keys} for d in dicts]

        return resp

    def get_dev_by_type(self, dev_type: str) -> Response:  # VERIFIED
        url = "/platform/device_inventory/v1/devices"
        if dev_type.lower() in ["aps", "ap"]:
            dev_type = "iap"
        params = {"sku_type": dev_type}
        return self.get(url, params=params)

    def get_variablised_template(self, serialnum: str) -> Response:  # VERIFIED
        url = f"/configuration/v1/devices/{serialnum}/variablised_template"
        return self.get(url)

    def get_variables(self, serialnum: str = None) -> Response:
        if serialnum and serialnum != "all":
            url = f"/configuration/v1/devices/{serialnum}/template_variables"
            params = {}
        else:
            url = "/configuration/v1/devices/template_variables"
            params = {"limit": 20, "offset": 0}
            # TODO generator for returns > 20 devices
        return self.get(url, params=params)

    # TODO self.patch  --> Refactor to pycentral
    def update_variables(self, serialnum: str, var_dict: dict) -> bool:
        url = f"/configuration/v1/devices/{serialnum}/template_variables"
        var_dict = json.dumps(var_dict)
        return self.patch(url, payload=var_dict)
        # resp = requests.patch(self.central.vars["base_url"] + url, data=var_dict, headers=header)
        # return(resp.ok)

    # TODO ignore sort parameter and sort output from any field.  Central is inconsistent as to what they support via sort
    def get_devices(self, dev_type: str, group: str = None, label: str = None, stack_id: str = None,
                    status: str = None, fields: list = None, show_resource_details: bool = False,
                    calculate_client_count: bool = False, calculate_ssid_count: bool = False,
                    public_ip_address: str = None, limit: int = 100, offset: int = 0, sort: str = None):
        # pagenation limit default 100, max 1000
        # does not return _next... pager will need to page until count < limit
        _strip = ["self", "dev_type", "url", "_strip"]
        # if fields is not None:
        #     fields = json.dumps(fields)
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
        return self.get(url, params=params, callback=cleaner.get_devices)

    def get_dev_details(self, dev_type: str, serial: str) -> Response:
        # https://internal-apigw.central.arubanetworks.com/monitoring/v1/switches/CN71HKZ1CL
        if dev_type == "switch":
            dev_type = "switches"
        elif dev_type == "gateway":
            dev_type = "gateways"
        url = f"/monitoring/v1/{dev_type}/{serial}"
        return self.get(url, callback=cleaner.get_devices)

    def get_ssids_by_group(self, group):
        url = "/monitoring/v1/networks"
        params = {"group": group}
        return self.get(url, params=params)

    def get_gateways_by_group(self, group):
        url = "/monitoring/v1/mobility_controllers"
        params = {"group": group}
        return self.get(url, params=params)

    def get_group_for_dev_by_serial(self, serial_num):
        return self.get(f"/configuration/v1/devices/{serial_num}/group")

    def get_dhcp_client_info_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/dhcp_clients"
        params = {"reservation": False}
        return self.get(url, params=params)

    def get_vlan_info_by_gw(self, serial_num):
        return self.get(f"/monitoring/v1/mobility_controllers/{serial_num}/vlan")

    def get_uplink_info_by_gw(self, serial_num, timerange: str = "3H"):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks"
        params = {"timerange": timerange}
        return self.get(url, params)

    def get_uplink_tunnel_stats_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks/tunnel_stats"
        return self.get(url)

    def get_uplink_state_by_group(self, group: str) -> Response:
        url = "/monitoring/v1/mobility_controllers/uplinks/distribution"
        params = {"group": group}
        return self.get(url, params)

    def get_all_sites(self) -> Response:
        return self.get("/central/v2/sites", callback=cleaner.sites)

        # strip visualrrf_default site from response
        # if resp.ok:  # resp.output = List[dict, ...]

        #     # sorting logically and stripping tag column for now
        #     _sorted = ["site_name", "site_id", "address", "city", "state", "zipcode", "country", "longitude",
        #                "latitude", "associated_device_count"]  # , "tags"]
        #     key_map = {
        #         "associated_device_count": "associated_devices",
        #         "site_id": "id"
        #     }
        #     resp.output = [{key_map.get(k, k): s[k] for k in _sorted} for s in resp.output
        #                    if s.get("site_name", "") != "visualrf_default"]

        # return resp

    def get_site_details(self, site_id):
        return self.get(f"/central/v2/sites/{site_id}", callback=cleaner.sites)

    def get_events_by_group(self, group: str) -> Response:  # VERIFIED
        url = "/monitoring/v1/events"
        params = {"group": group}
        return self.get(url, params=params)

    def bounce_poe(self, port: Union[str, int], serial_num: str = None, name: str = None, ip: str = None) -> Response:
        """Bounce PoE on interface, valid only for switches
        """
        # TODO allow bounce by name or ip
        # v2 method returns 'CSRF token missing or incorrect.'
        url = f"/device_management/v1/device/{serial_num}/action/bounce_poe_port/port/{port}"
        # need to check get_task_status with response.output["task_id"] from this request to get status
        # During testing cetral always returned QUEUED
        return self.post(url)

    def bounce_interface(self, port: Union[str, int], serial_num: str = None, name: str = None, ip: str = None) -> Response:
        """Bounce interface, valid only for switches
        """
        # TODO allow bounce by name or ip
        url = f"/device_management/v1/device/{serial_num}/action/bounce_interface/port/{port}"
        return self.post(url)

    def kick_users(self, serial_num: str = None, name: str = None, kick_all: bool = False,
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
            return Response(self.post, url, payload=payload)
            # pprint.pprint(resp.json())
        else:
            # TODO adapt Response object so we can send error through it
            # without a function... resp.ok = False, resp.error = The Error
            log.error("Missing Required Parameters", show=True)

    def get_task_status(self, task_id):
        return self.get(f"/device_management/v1/status/{task_id}")

    def add_dev(self, mac: str, serial_num: str):
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

        return self.post(url, payload=payload)
        # resp = requests.post(self.central.vars["base_url"] + url, headers=header, json=payload)
        # pprint.pprint(resp.json())

    def verify_add_dev(self, mac: str, serial_num: str):
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

        return self.post(url, payload=payload)
        # resp = requests.post(self.central.vars["base_url"] + url, headers=header, json=payload)
        # pprint.pprint(resp.json())

    def move_dev_to_group(self, group: str, serial_num: Union[str, list]) -> bool:
        url = "/configuration/v1/devices/move"
        if not isinstance(serial_num, list):
            serial_num = [serial_num]

        payload = {
                    "group": group,
                    "serials": serial_num
                  }

        # resp = requests.post(self.central.vars["base_url"] + url, headers=headers, json=payload)
        return self.post(url, payload=payload)

    def caasapi(self, group_dev: str, cli_cmds: list = None):
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

        # f_url = self.central.central_info["base_url"] + url
        # return Response(requests.post, f_url, params=params, json=payload, headers=headers)
        return self.post(url, params=params, payload=payload)

        # return requests.post(self.central.vars["base_url"] + url, params=params, headers=header, json=payload)


# t = CentralApi()
# t.get_ap()
# t.get_swarms_by_group("Branch1")
# t.get_swarm_details("fbe90101014332bf0dabfa5d2cf4ae7a0917a04127f864e047")
# t.get_wlan_clients(group="Branch1")
# t.get_wired_clients()
# t.get_wired_clients(group="Branch1")
# t.get_client_details("20:4c:03:30:4c:4c")
# t.get_certificates()
# t.get_template("WadeLab", "2930F-8")
# t.get_all_groups()
# t.get_dev_by_type("iap")
# t.get_dev_by_type("switch")
# t.get_dev_by_type("gateway")
# t.get_variablised_template("CN71HKZ1CL")
# t.get_ssids_by_group("Branch1")
# t.get_gateways_by_group("Branch1")
# t.get_group_for_dev_by_serial("CNHPKLB030")
# t.get_dhcp_client_info_by_gw("CNF7JSP0N0")
# t.get_vlan_info_by_gw("CNHPKLB030")
# t.get_uplink_info_by_gw("CNF7JSP0N0")
# t.get_uplink_tunnel_stats_by_gw("CNF7JSP0N0")
# t.get_uplink_state_by_group("Branch1")
# t.get_all_sites()
# t.get_site_details(10)
# t.get_events_by_group("Branch1")
# t.bounce_poe("CN71HKZ1CL", 2)
# t.kick_users("CNC7J0T0GK", kick_all=True)
# t.get_task_status(15983230525575)
# group_dev = "Branch1/20:4C:03:26:28:4C"
# cli_cmds = ["netdestination delme", "host 1.2.3.4", "!"]
# t.caasapi(group_dev, cli_cmds)
# mac = "20:4C:03:81:E8:FA"
# serial_num = "CNHPKLB030"
# t.add_dev(mac, serial_num)
# t.verify_add_dev(mac, serial_num)
# t.move_dev_to_group("Branch1", serial_num)


class BuildCLI:
    def __init__(self, data: dict = None, session=None, filename: str = None):
        filename = filename or config.bulk_edit_file

        self.session = session
        self.dev_info = None
        if data:
            self.data = data
        else:
            self.data = self.get_bulkedit_data(filename)
        self.cmds = []
        self.build_cmds()

    @staticmethod
    def get_bulkedit_data(filename: str):
        cli_data = {}
        _common = {}
        _vlans = []
        _mac = "error"
        _exclude_start = ''
        with open(filename) as csv_file:
            csv_reader = csv.reader([line for line in csv_file.readlines() if not line.startswith('#')])

            csv_rows = [r for r in csv_reader]

            for data_row in csv_rows[1:]:
                vlan_data = {}
                for k, v in zip(csv_rows[0], data_row):
                    k = k.strip().lower().replace(' ', '_')
                    # print(f"{k}: {v}")
                    if k == "mac_address":
                        _mac = v
                        cli_data[v] = {}
                    elif k in ["group", "model", "hostname", "bg_peer_ip", "controller_vlan",
                               "zs_site_to_site_map_name", "source_fqdn"]:
                        _common[k] = v
                    elif k.startswith(("vlan", "dhcp", "domain", "dns", "vrrp", "access_port", "ppoe")):
                        if k == "vlan_id":
                            if vlan_data:
                                _vlans.append(vlan_data)
                            vlan_data = {k: v}
                        elif k.startswith("dns_server_"):
                            vlan_data["dns_servers"] = [v] if "dns_servers" not in vlan_data else \
                                                              [*vlan_data["dns_servers"], *[v]]
                        elif k.startswith("dhcp_default_router"):
                            vlan_data["dhcp_def_gws"] = [v] if "dhcp_def_gws" not in vlan_data else \
                                                               [*vlan_data["dhcp_def_gws"], *[v]]
                        elif k.startswith("dhcp_exclude_start"):
                            _exclude_start = v
                        elif k.startswith("dhcp_exclude_end"):
                            if _exclude_start:
                                _line = f"ip dhcp exclude-address {_exclude_start} {v}"
                                vlan_data["dhcp_excludes"] = [_line] if "dhcp_excludes" not in vlan_data else \
                                                                        [*vlan_data["dhcp_excludes"], *[_line]]
                                _exclude_start, _line = '', ''
                            else:
                                print(f"Validation Error DHCP Exclude End with no preceding start ({v})... Ignoring")
                        else:
                            vlan_data[k] = v

                _vlans.append(vlan_data)
                cli_data[_mac] = {"_common": _common, "vlans": _vlans}

        return cli_data

    def build_cmds(self):
        for dev in self.data:
            common = self.data[dev]["_common"]
            vlans = self.data[dev]["vlans"]
            _pretty_name = common.get('hostname', dev)
            print(f"Verifying {_pretty_name} is in Group {common['group']}...", end='')
            # group_devs = self.session.get_gateways_by_group(self.data[dev]["_common"]["group"])
            gateways = self.session.get_dev_by_type("gateway")
            self.dev_info = [_dev for _dev in gateways if _dev.get('macaddr', '').lower() == dev.lower()]
            if self.dev_info:
                self.dev_info = self.dev_info[0]
                if common["group"] == self.session.get_group_for_dev_by_serial(self.dev_info["serial"]):
                    print(' Confirmed', end='\n')
                else:
                    print(" it is *Not*", end="\n")
                    print(f"Moving {_pretty_name} to Group {common['group']}")
                    res = self.session.move_dev_to_group(common["group"], self.dev_info["serial"])
                    if not res:
                        print(f"Error Returned Moving {common['hostname']} to Group {common['group']}")

            print(f"Building cmds for {_pretty_name}")
            if common.get("hostname"):
                self.cmds += [f"hostname {common['hostname']}", "!"]

            for v in vlans:
                self.cmds += [f"vlan {v['vlan_id']}", "!"]
                if v.get("vlan_ip"):
                    if not v.get("vlan_subnet"):
                        print(f"Validation Error No subnet mask for VLAN {v['vlan_id']} ")
                        # TODO handle the error
                    self.cmds += [f"interface vlan {v['vlan_id']}", f"ip address {v['vlan_ip']} {v['vlan_subnet']}"]
                    # TODO should VLAN description also be vlan name - check what bulk edit does
                    if v.get("vlan_interface_description"):
                        self.cmds.append(f"description {v['vlan_interface_description']}")
                    if v.get("vlan_helper_addr"):
                        self.cmds.append(f"ip helper-address {v['vlan_helper_addr']}")
                    if v.get("vlan_interface_operstate"):
                        self.cmds.append(f"operstate {v['vlan_interface_operstate']}")
                    self.cmds.append("!")

                if v.get("pppoe_username"):
                    print("Warning PPPoE not supported by this tool yet")

                if v.get("access_port"):
                    if "thernet" not in v["access_port"] and not v["access_port"].startswith("g"):
                        _line = f"interface gigabitethernet {v['access_port']}"
                    else:
                        _line = f"interface {v['access_port']}"
                    self.cmds += [_line, f"switchport access vlan {v['vlan_id']}", "!"]

                if v.get("dhcp_pool_name"):
                    self.cmds.append(f"ip dhcp pool {v['dhcp_pool_name']}")
                    if v.get("dhcp_def_gws"):
                        for gw in v["dhcp_def_gws"]:
                            self.cmds.append(f"default-router {gw}")
                    if v.get("dns_servers"):
                        self.cmds.append(f"dns-server {' '.join(v['dns_servers'])}")
                    if v.get("domain_name"):
                        self.cmds.append(f"domain-name {v['domain_name']}")
                    if v.get("dhcp_network"):
                        if v.get("dhcp_mask"):
                            self.cmds.append(f"network {v['dhcp_network']} {v['dhcp_mask']}")
                        elif v.get("dhcp_network_prefix"):
                            self.cmds.append(f"network {v['dhcp_network']} /{v['dhcp_network_prefix']}")
                    self.cmds.append("!")

                if v.get("dhcp_excludes"):
                    # dhcp exclude lines are fully formatted as data is collected
                    for _line in v["dhcp_excludes"]:
                        self.cmds.append(_line)

                if v.get("vrrp_id"):
                    if v.get("vrrp_ip"):
                        self.cmds += [f"vrrp {v['vrrp_id']}", f"ip address {v['vrrp_ip']}", f"vlan {v['vlan_id']}"]
                        if v.get("vrrp_priority"):
                            self.cmds.append(f"priority {v['vrrp_priority']}")
                        self.cmds += ["no shutdown", "!"]
                    else:
                        print(f"Validation Error VRRP ID {v['vrrp_id']} VLAN {v['vlan_id']} No VRRP IP provided... Skipped")

                if v.get("bg_peer_ip"):
                    # _as = self.session.get_bgp_as()
                    # self.cmds.append(f"router bgp neighbor {v['bg_peer_ip']} as {_as}")
                    print("bgp peer ip Not Supported by Script yet")

                if v.get("zs_site_to_site_map_name") or v.get("source_fqdn"):
                    print("Zscaler Configuration Not Supported by Script Yet")


if __name__ == "__main__":
    cli = BuildCLI(session=CentralApi())
    for c in cli.cmds:
        print(c)
