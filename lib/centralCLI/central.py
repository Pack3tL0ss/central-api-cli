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

from pycentral.base import ArubaCentralBase
import requests
import json
from typing import List, Tuple, Union
import csv
from . import MyLogger, Response, config, log

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
    conn = None
    if account_name not in config.data:
        exit(f"exiting... {account_name} missing from {config.file}")
    central_info = config.data[account_name]
    token_store = config.get("token_store", DEFAULT_TOKEN_STORE)
    ssl_verify = config.get("ssl_verify", True)

    conn = ArubaCentralBase(central_info=central_info,
                            token_store=token_store,
                            ssl_verify=ssl_verify,
                            logger=logger
                            )
    return conn


class CentralApi:
    def __init__(self, account_name):
        self.central = get_conn_from_file(account_name)

        cfg_dict = self.central.central_info
        tok_dict = cfg_dict["token"]

        # Temp Refactor to use ArubaBaseClass without changing all my methods
        self.central.get = self.get

        self.headers = {
            "authorization": f"{tok_dict.get('token_type', 'Bearer')} {tok_dict['access_token']}",
            "Content-type": "application/json"
        }

        # def get(self, url: str, params: dict = {}, data: dict = {},
        #         headers: dict = {}, files: dict = {}, retry_api_call: bool = True) -> dict:
        #     return self.central.command("GET", apiPath=url, apiData=data, apiParams=params,
        #                                 headers=headers, files=files, retry_api_call=retry_api_call)

    def get(self, url, params: dict = None, headers: dict = None):
        f_url = self.central.central_info["base_url"] + url
        return Response(self.central.requestUrl, f_url, params=params, headers=headers)

    def post(self, url, params: dict = None, payload: dict = None, headers: dict = None, **kwargs) -> Response:
        f_url = self.central.central_info["base_url"] + url
        return Response(self.central.requestUrl, f_url, data=payload, params=params, headers=headers, **kwargs)

    # doesn't appear to work. referenced in swagger to get listing of types (New Device Inventory: Get Devices...)
    def get_dev_types(self):
        url = "/platform/orders/v1/skus?sku_type=all"
        return self.central.get(url)

    def get_ap(self):
        """GET call for AP data

        :param access_token: Access token from tokens func
        :type access_token: String
        """
        url = "/monitoring/v1/aps"
        # return self.central.get(url)
        return self.central.get(url)

    def get_swarms_by_group(self, group: str):
        url = "/monitoring/v1/swarms"
        params = {"group": group}
        return self.central.get(url, params=params)

    def get_swarm_details(self, swarm_id: str):
        url = f"/monitoring/v1/swarms/{swarm_id}"
        return self.central.get(url)

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

        # return structure:  {'clients': [], 'count': 0}
        resp = self._get_wireless_clients(**params)
        if resp.ok:
            wlan_resp = resp
            resp = self._get_wired_clients(**params)
            if resp.ok:
                resp.output = wlan_resp.output.get("clients") + resp.output.get("clients")
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
        return self.central.get(url, params=params)

    def _get_wired_clients(self, group: str = None, swarm_id: str = None, label: str = None, ssid: str = None,
                           serial: str = None, cluster_id: str = None, stack_id: str = None) -> Response:
        params = {}
        for k, v in zip(["group", "swarm_id", "label", "ssid", "serial", "cluster_id", "stack_id"],
                        [group, swarm_id, label, ssid, serial, cluster_id, stack_id]
                        ):
            if v:
                params[k] = v

        url = "/monitoring/v1/clients/wired"
        return self.central.get(url, params=params)

    def _get_client_details(self, mac: utils.Mac) -> Response:
        url = f"/monitoring/v1/clients/wired/{mac.url}"
        resp = self.central.get(url)
        return resp
        # TODO need to check wireless if doesn't exist there check wired or see if there is generic wired/wlan method
        # if resp.ok
        #     if not resp.output:

    def get_certificates(self):
        url = "/configuration/v1/certificates"
        params = {"limit": 20, "offset": 0}
        return self.central.get(url, params=params)

    def get_template(self, group, template):
        url = f"/configuration/v1/groups/{group}/templates/{template}"
        return self.central.get(url)

    def get_all_groups(self):  # DONE
        url = "/configuration/v2/groups"
        params = {"limit": 20, "offset": 0}  # 20 is the max
        resp = self.central.get(url, params=params)
        if resp.ok and resp.get("data"):
            resp["data"] = [g for _ in resp["data"] for g in _ if g != "unprovisioned"]
        return resp

    def get_sku_types(self):
        url = "/platform/orders/v1/skus"
        params = {"sku_type": "all"}
        return self.central.get(url, params=params)

    def get_dev_by_type(self, dev_type: str):
        url = "/platform/device_inventory/v1/devices"
        if dev_type.lower() in ["aps", "ap"]:
            dev_type = "iap"
        params = {"sku_type": dev_type}
        return self.central.get(url, params=params)

    def get_variablised_template(self, serialnum: str) -> Response:
        url = f"/configuration/v1/devices/{serialnum}/variablised_template"
        return self.central.get(url)

    def get_variables(self, serialnum: str = None):
        if serialnum:
            url = f"/configuration/v1/devices/{serialnum}/template_variables"
            params = {}
        else:
            url = "/configuration/v1/devices/template_variables"
            params = {"limit": 20, "offset": 0}
            # TODO generator for returns > 20 devices
        return self.central.get(url, params=params)

    # TODO self.patch
    def update_variables(self, serialnum: str, var_dict: dict):
        url = f"/configuration/v1/devices/{serialnum}/template_variables"
        header = {
                    "authorization": f"Bearer {self.central.access_token}",
                    "Content-type": "application/json"
                 }
        var_dict = json.dumps(var_dict)
        resp = requests.patch(self.central.vars["base_url"] + url, data=var_dict, headers=header)
        return(resp.ok)

    def get_devices(self, dev_type: str, group: str = None, label: str = None, stack_id: str = None,
                    status: str = None, fields: list = None, show_stats: bool = False, calc_clients: bool = False,
                    pub_ip: str = None, limit: int = None, offset: int = None, sort: str = None):
        _strip = ["self", "dev_type", "url", "_strip"]
        params = {k: v for k, v in locals().items() if k not in _strip and v}
        url = f"/monitoring/v1/{dev_type}"
        return self.central.get(url, params=params)

    def get_ssids_by_group(self, group):
        url = "/monitoring/v1/networks"
        params = {"group": group}
        return self.central.get(url, params=params)

    def get_gateways_by_group(self, group):
        url = "/monitoring/v1/mobility_controllers"
        params = {"group": group}
        return self.central.get(url, params=params)

    def get_group_for_dev_by_serial(self, serial_num):
        return self.central.get(f"/configuration/v1/devices/{serial_num}/group")

    def get_dhcp_client_info_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/dhcp_clients"
        params = {"reservation": False}
        return self.central.get(url, params=params)

    def get_vlan_info_by_gw(self, serial_num):
        return self.central.get(f"/monitoring/v1/mobility_controllers/{serial_num}/vlan")

    def get_uplink_info_by_gw(self, serial_num, timerange: str = "3H"):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks"
        params = {"timerange": timerange}
        return self.central.get(url, params)

    def get_uplink_tunnel_stats_by_gw(self, serial_num):
        url = f"/monitoring/v1/mobility_controllers/{serial_num}/uplinks/tunnel_stats"
        return self.central.get(url)

    def get_uplink_state_by_group(self, group):
        url = f"/monitoring/v1/mobility_controllers/uplinks/distribution?group={group}"
        return self.central.get(url)

    def get_all_sites(self):
        resp = self.central.get("/central/v2/sites")

        # strip visualrrf_default site from response
        if resp.ok:
            _ = resp.output.get("sites", "")
            resp["sites"] = [s for s in _ if s.get("site_name", "") != "visualrf_default"]
            # TODO move site_name to front of dict

        return resp

    def get_site_details(self, site_id):
        return self.central.get(f"/central/v2/sites/{site_id}")

    def get_events_by_group(self, group):
        url = f"/monitoring/v1/events?group={group}"
        params = {"group": group}
        return self.central.get(url, params=params)

    def bounce_poe(self, port: Union[str, int], serial_num: str = None, name: str = None, ip: str = None) -> Response:
        # TODO allow bounce by name or ip
        url = f"/device_management/v1/device/{serial_num}/action/bounce_poe_port/port/{port}"
        print(url)
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
        return self.central.get(f"/device_management/v1/status/{task_id}")

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

        return Response(self.post, url, payload=payload)
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

        return Response(self.post, url, payload=payload)
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
        return Response(self.post, url, payload=payload)

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
        return Response(self.post, url, params=params, payload=payload)

        # return requests.post(self.central.vars["base_url"] + url, params=params, headers=header, json=payload)
        # TODO use my resp generator


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
