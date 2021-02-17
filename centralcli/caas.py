import typer
import csv
from centralcli import config


def eval_caas_response(resp) -> None:
    if not resp.ok:
        typer.echo(f"[{resp.status_code}] {resp.error} \n{resp.output}")
        return
    else:
        resp = resp.output

    lines = "-" * 22
    typer.echo("")
    typer.echo(lines)
    if resp.get("_global_result", {}).get("status", '') == 0:
        typer.echo("Global Result: Success")
    else:
        typer.echo("Global Result: Failure")
    typer.echo(lines)
    _bypass = None
    if resp.get("cli_cmds_result"):
        typer.echo("\n -- Command Results --")
        for cmd_resp in resp["cli_cmds_result"]:
            for _c, _r in cmd_resp.items():
                _r_code = _r.get("status")
                if _r_code == 0:
                    _r_pretty = "OK"
                else:
                    _r_pretty = f"ERROR {_r_code}"
                _r_txt = _r.get("status_str")
                typer.echo(f" [{_bypass or _r_pretty}] {_c}")
                if not _r_code == 0:
                    _bypass = "bypassed"
                    if _r_txt:
                        typer.echo(f"\t{_r_txt}\n")
                    typer.echo("-" * 65)
                    typer.echo("!! Remaining Commands bypassed due to Error in previous object !!")
                    typer.echo("-" * 65)
                elif _r_txt and not _bypass:
                    typer.echo(f"\t{_r_txt}")
        typer.echo("")


# def caasapi(self, group_dev: str, cli_cmds: list = None):
#     if ":" in group_dev and len(group_dev) == 17:
#         key = "node_name"
#     else:
#         key = "group_name"

#     url = "/caasapi/v1/exec/cmd"

#     cfg_dict = self.central.central_info
#     params = {
#         "cid": cfg_dict["customer_id"],
#         key: group_dev
#     }

#     payload = {"cli_cmds": cli_cmds or []}

#     return self.post(url, params=params, payload=payload)


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
