import csv
from pathlib import Path
from typing import Any

from centralcli import api_clients, common, config, render, utils

from .response import Response

api = api_clients.classic


class BuildCLI:
    """Build equivalent cli commands for caas API from bulk-edit.csv import file"""
    def __init__(self, data: dict = None) -> None:
        # Values updated in build_cmds
        self.dev_info = None
        self.data = data
        self.cmds = []

    @staticmethod
    def get_bulkedit_data(filename: Path):  # pragma: no cover
        cli_data = {}
        _common = {}
        _vlans = []
        _mac = "error"
        _exclude_start = ''
        with filename.open() as csv_file:
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
                    elif k in [
                        "group",
                        "model",
                        "hostname",
                        "bg_peer_ip",
                        "controller_vlan",
                        "zs_site_to_site_map_name",
                        "source_fqdn"
                    ]:
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

    def build_cmds(self, data: dict = None, file: Path = config.bulk_edit_file) -> list:  # pragma: no cover
        if data:
            self.data = data
        else:
            self.data = self.get_bulkedit_data(file)

        for dev in self.data:
            common_data: dict[str, Any] = self.data[dev]["_common"]
            vlans = self.data[dev]["vlans"]
            _pretty_name = f"[bright_green]{common_data.get('hostname', dev)}[/]"
            resp = api.session.request(api.monitoring.get_devices, "gateways")
            gateways = resp.output
            self.dev_info = [_dev for _dev in gateways if _dev.get('mac', '').lower() == dev.lower()]

            # if dev already exists move to group defined in bulk-edit
            if self.dev_info:
                self.dev_info = self.dev_info[0]
                if common_data["group"] != self.dev_info["group"]:
                    render.console.print(f"Moving {_pretty_name} to Group [cyan]{common_data['group']}[/]")
                    res = api.session.request(api.configuration.move_devices_to_group, common_data["group"], serials=self.dev_info["serial"])
                    if not res:
                        common.exit(f"[red1]Error[/] Returned Moving [cyan]{common_data['hostname']}[/] to Group [cyan]{common_data['group']}[/]")

            render.console.print(f"Building cmds for {_pretty_name}")
            if common_data.get("hostname"):
                self.cmds += [f"hostname {common_data['hostname']}", "!"]

            for v in vlans:
                self.cmds += [f"vlan {v['vlan_id']}", "!"]
                if v.get("vlan_ip"):
                    if not v.get("vlan_subnet"):
                        render.econsole.print(f":warning:  [red1]Validation Error[/] No subnet mask for VLAN [cyan]{v['vlan_id']}[/]")
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
                    render.econsole.print(":warning:  bgp peer ip Not Supported by Script yet")

                if v.get("zs_site_to_site_map_name") or v.get("source_fqdn"):
                    render.econsole.print(":warning:  Zscaler Configuration Not Supported by Script Yet")

            return self.cmds

    async def show_config(self, group: str, dev_mac: str = None) -> Response:
        show_url = "/caasapi/v1/showcommand"
        url = f"{show_url}/object/committed?group_name={group}"
        if dev_mac:
            mac = utils.Mac(dev_mac)
            if mac:
                url = f"{url}/{mac.url}"
            else:  # pragma: no cover
                common.exit(f"{dev_mac} does not appear to be a valid MAC address.")

        return await api.session.get(url)


    # FIXME
    async def get_config_status(self, serial: str) -> Response:  # pragma: no cover
        """Bad API endpoint.  ignore this.

        // -- used by show config <gw> --status -- //

        The endpoint appears to be invalid though.
        """
        url = "/caas/v1/status/device"
        params = {"serial_num": serial}
        return await api.session.get(url, params=params)

class CaasAPI(BuildCLI):
    def __init__(self, data: dict = None, *, file: Path = None) -> None:
        self.data = data
        self.file = file
        self.dev_info = None
        self.cmds = []
        super().__init__(data=data)

    async def send_commands(self, group_dev: str, cli_cmds: list = None):
        key = "node_name" if ":" in group_dev and len(group_dev) == 17 else "group_name"
        url = "/caasapi/v1/exec/cmd"

        if not config.classic.customer_id:
            common.exit(f"customer_id attribute not found in {config.file}")  # pragma: no cover
        else:
            params = {"cid": config.classic.customer_id, key: group_dev}
            json_data = {"cli_cmds": cli_cmds or []}

            return await api.session.post(url, params=params, json_data=json_data)
