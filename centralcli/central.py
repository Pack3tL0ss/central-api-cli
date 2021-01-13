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

from . import MyLogger, config, cleaner, log, ArubaCentralBase
from .response import Response
# from response import Response

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
    def __init__(self, account_name: str = "central_info"):
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
        params = {
            "offset": 0,
            "limit": 20,  # 20 is the max
            "template": name,
            "device_type": device_type,  # valid = IAP, ArubaSwitch, MobilityController, CX
            "version": version,
            "model": model
        }
        url = f"/configuration/v1/groups/{group}/templates"
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

    def _get_group_names(self) -> Response:  # REVERIFIED
        url = "/configuration/v2/groups"
        params = {"offset": 0, "limit": 20}  # 20 is the max
        resp = self.get(url, params=params, callback=cleaner._get_group_names)
        return resp

    def get_all_groups(self) -> Response:
        url = "/configuration/v2/groups/template_info"
        resp = self._get_group_names()
        if not resp.ok:
            return resp
        else:
            all_groups = ",".join(resp.output)
            params = {"groups": all_groups}
        return self.get(url, params=params, callback=cleaner.get_all_groups)

    def get_all_templates(self, groups: List[dict] = None, **params) -> Response:
        """Get data for all defined templates from Aruba Central

        Args:
            groups (List[dict], optional): List of group dictionaries (Used to send cache vs trigerring a fresh API call).
                                           Defaults to None (Central will first be queried for all groups)

        Returns:
            Response: centralcli Response Object
        """
        if not groups:
            resp = self.get_all_groups()
            if resp:
                groups = resp.output
            else:
                return resp

        template_groups = groups = [g["name"] for g in groups if True in g.get("template group", {}).values()]
        all_templates = []
        for group in template_groups:
            resp = self.get_all_templates_in_group(group, **params)
            if not resp.ok:
                return resp
            else:
                all_templates += resp.output
        return Response(ok=True, output=all_templates, error="OK")

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
        # iap, switch, gateway|boc
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
        return self.get(url, params=params)

    def update_variables(self, serialnum: str, var_dict: dict) -> bool:
        url = f"/configuration/v1/devices/{serialnum}/template_variables"
        var_dict = json.dumps(var_dict)
        return self.patch(url, payload=var_dict)

    # TODO ignore sort parameter and sort output from any field.  Central is inconsistent as to what they support via sort
    def get_devices(self, dev_type: str, group: str = None, label: str = None, stack_id: str = None,
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
        return self.get(url, params=params, callback=cleaner.get_devices)

    def get_dev_details(self, dev_type: str, serial: str) -> Response:
        dev_type = "switches" if dev_type == "switch" else dev_type
        dev_type = "gateways" if dev_type == "gateway" else dev_type
        dev_type = "aps" if dev_type == "ap" else dev_type
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
            # TODO move this validation to the cli command
            return Response(ok=False, error="Missing Required Parameters")

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

    # TODO move to caas.py
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

        return self.post(url, params=params, payload=payload)


if __name__ == "__main__":
    pass
