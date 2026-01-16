#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Literal

import tablib
import yaml
from pygments.lexers.data import JsonLexer, YamlLexer
from rich.console import Console
from rich.markup import escape
from rich.syntax import Syntax

from centralcli import log, utils
from centralcli.render import tty
from centralcli.vendored.csvlexer.csv import CsvLexer

console = Console(emoji=False)

# [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]  # TODO implement this device del

# TODO build examples for json yaml a master import for all make example the same for add and delete
# (noting that delete only requires 1 field)
# provide estimate on number of API calls.

# TODO These Examples run on import need to make properties of class or something to avoid running on import


TabLibFormats = Literal['json', 'yaml', 'csv', 'tsv', 'dbf', 'html', 'jira', 'latex', 'df', 'rst', 'cli']
ExampleType = Literal["devices", "sites", "groups", "labels", "macs", "mpsk", "variables"]
Action = Literal["add", "delete", "move", "rename", "other"]

_pad = " " * 6
ADD_FIELDS = {
    "devices": {
        "required": ["serial", "mac"],
        "optional": {
            "group": "Pre-provision device to group",
            "subscription": "Apply subscription to device"
        }
    },
    "groups": {
        "required": ["name"],
        "optional": {
            "types": f'Defines what type of devices are allowed in the group.\n{_pad}Valid values: ["ap", "gw", "cx", "sw"] [dim]{escape("[default: All but sdwan allowed]")}[/]\n{_pad}For csv the field can be blank (all device types) or any of these formats: "cx" or "cx,ap" or {escape("[cx,ap,gw]")}',
            "wired-tg": f"Set to true to make the group a template group for switches. [dim]{escape('[default: False]')}[/]",
            "wlan-tg": f"Set to true to make the group a template group for APs.  [dim]{escape('[default: False]')}[/]",
            "gw-role": f"[cyan]branch[/], [cyan]vpnc[/] or [cyan]wlan[/] only applies if gw type is allowed. [dim]{escape('[default: branch]')}[/]",
            "aos10": f"Set to true to enable group as aos10 group (APs).  [dim]{escape('[default: AOS8 IAP]')}[/]",
            "microbranch": f"Set to true to configure APs in the group as micro-branch APs (implies aos_10). [dim]{escape('[default: False]')}[/]",
            "monitor-only-cx": "Set to true to enable CX switches as monitor only.",
            "monitor-only-sw": "Set to true to enable AOS-SW switches as monitor only.",
            "cnx": f"Make group compatible with New Central (cnx)\n{_pad}:warning:  All configurations will be pushed from New Central configuration model. [dim]{escape('[default: False]')}[/]",
            "gw-config": "Path to file containing gw group level config or jinja2 template.",
            "ap-config": "Path to file containing ap group level config or jinja2 template.",
            "gw-vars": "Path to variables used if gw-config is a j2 template.",
            "ap-vars": "Path to variables used if ap-config is a j2 template.",
        }
    }
}
MOVE_FIELDS = {
     "devices": {
          "required": ["serial"],
          "optional": {
              "mac": "Device MAC address",
              "group": "Move device to group",
              "site": "Move device to site",
              "label": "Assign label to device",
              "retain_config": "Retain devices current configuration as device level override. [dim](Applies to CX switches Only)[/]"
          }
    }
}
VERIFY_FIELDS = {
     "devices": {
          "required": ["serial"],
          "optional": {
              "mac": "Device MAC address",
              "group": "Verify device is in group",
              "site": "Verify device is assigned to site",
              "label": "Verify device is assigned label",
              "subscription": "Verify subscription assigned to device"
          }
    }
}
FIELDS = {
    "add": ADD_FIELDS,
    "move": MOVE_FIELDS,
    "verify": VERIFY_FIELDS
}
COMMAND_TEXT = {
    "devices": {
        "add": "[italic cyan]cencli batch add devices [OPTIONS] IMPORT_FILE[/]",
        "delete": "[italic cyan]cencli batch delete devices [OPTIONS] IMPORT_FILE[/]",
        "move": "[italic cyan]cencli batch move devices [OPTIONS] IMPORT_FILE[/]",
        "verify": "[italic cyan]cencli batch verify [OPTIONS] IMPORT_FILE[/]",
    },
    "groups": {
        "add": "[italic cyan]cencli batch add groups [OPTIONS] IMPORT_FILE[/]"
    }
}


LEXERS = {
        "csv":  CsvLexer(ensurenl=False),
        "json": JsonLexer(ensurenl=False),
        "yaml": YamlLexer(ensurenl=False)
}


@dataclass
class Warnings:
    no_outfile = "[deep_sky_blue1]\u2139[/]  [cyan]--out <FILE PATH>[/] not provided.  The command can be repeated without doing API calls with [cyan]cencli show last --out <FILE PATH>[/]"


class ExampleSegment:
    def __init__(self, example_text: str, example_type: Literal["csv", "yaml", "json"] = "csv", example_title: str = None) -> None:
        self.original = example_text
        self.example_type = example_type
        self.example_text = self._format_example_text(example_text, example_type)
        example_title = None if not example_title else f" {example_title.strip()} "
        self.title = example_title or f" .{example_type} example "
        max_len = max([len(line.strip()) for line in example_text.splitlines()])
        self.max_len = (max_len if max_len >= 57 else 57) if max_len <= tty.cols else tty.cols


    def __str__(self):
        return "\n".join(self.list)

    def __rich__(self):
        return str(self)  # pragma: no cover

    def _format_example_text(self, example_text: str, example_type: Literal["csv", "yaml", "json"] = None) -> Syntax:
        example_type = example_type or self.example_type
        out = Syntax(code=example_text, lexer=LEXERS[self.example_type], theme="native")

        return out.highlight(out.code.rstrip()).markup

    @property
    def list(self):
        return [
            f'[reset]{self.title:{"-"}^{self.max_len}s}'.replace("- ", "- [bright_green]").replace(" -", "[/] -"),
            self.example_text,
            "-" * self.max_len,
            "",
            # f"{len(self.title)=} {self.first_half=} {self.second_half=} {self.max_len=} {self.end_len=} {[len(line) for line in self.original.splitlines()]}",  # DEBUG
        ]

class Example:
    """
    convert csv data as string into csv, json, and yaml
    """
    def __init__(self, data: str, type: ExampleType = None, action: Action = None, data_format: TabLibFormats = "csv", by_text_field: str = None) -> None:
        self.data = data.strip()
        self.type = type or "devices"
        self.action = action or "add"
        self.ds = tablib.Dataset().load(self.data, format=data_format)
        self.clean = self._get_clean_data(self.ds,)
        self.json = self.get_json()
        self.yaml = self.get_yaml()
        self.csv = self.get_csv()
        self.mac_text = "[italic]:information:  MAC Address can be nearly any format imaginable.[/]"
        self.ignore_text = f"[italic]:information:  {self.type.capitalize()} with either [cyan]ignore[/], or [cyan]retired[/] keys set to true are ignored.[/]"
        self.by_text_field = by_text_field

    def __str__(self):
        ret = [*ExampleSegment(self.csv, "csv").list, *ExampleSegment(self.json, "json").list, *ExampleSegment(self.yaml, "yaml").list,]
        if self.txt_file_example:
            ret += [self.txt_file_example]

        _by_key = self.by_parent_key
        if _by_key:
            ret += [_by_key]

        return "\n".join(ret)

    @property
    def full_text(self) -> str:
        ret = [
            self.command_text,
            "",
            self.header,
            "",
            self.mac_text,
            self.ignore_text,
            "",
            str(self),
            "",
            self.parent_key_text,
            common_add_delete_end if self.action in ["add", "delete"] else generic_end
        ]
        return "\n".join(ret)

    def _get_clean_data(self, data: tablib.Dataset = None) -> List[Dict[str, Any]]:
        data = data or self.ds
        out = self._handle_bools(data)
        out = [utils.strip_none(inner) for inner in out]
        if not self.type == "variables":
            return out
        else:
            return {dev["_sys_serial"]: dev for dev in out}

    def _handle_bools(self, data: tablib.Dataset) -> List[Dict[str, Any]]:
        bool_strings = ["true", "false", "yes", "no"]
        def _convert_bool(value: str, expecting_list: bool = False) -> str | bool | int | list:
            if expecting_list:
                if " " in value:
                    return value.split()
                elif "," in value:  # csv should only support space seperated, but leaving this in for now.
                    return value.lstrip("[").rstrip("]").split(",")  # pragma: no cover
                elif value == "":
                    return None
                else:
                    return [value]  # pragma: no cover
            elif value.lower() in bool_strings:
                return True if value.lower() in ["true", "yes"] else False
            elif value.isdigit():
                return int(value)
            elif value == "":
                return None
            else:
                return value

        return [{k: _convert_bool(v, expecting_list=k in ["types"]) for k, v in inner_dict.items()} for inner_dict in data.dict]

    def get_json(self):
        return json.dumps(self.clean, sort_keys=False, indent=4)

    def get_yaml(self):
        return yaml.safe_dump(self.clean, sort_keys=False).rstrip()

    def get_csv(self):
        return self.ds.csv.rstrip()

    @property
    def header(self):
        header =  ["Accepts the following keys (include as header row for csv import):"]
        field_dict = FIELDS[self.action]
        required_strings =  utils.color(field_dict[self.type]["required"], "red")
        header += [f'    {required_strings}']
        # if field_dict[self.type].get("optional"):  # currently all defined have optional fields
        header[-1] = f'{header[-1]}, {utils.color(list(field_dict[self.type]["optional"].keys()), "cyan")} [italic red](red=required)[/]'
        if self.action == "move":
            header += [f'    [italic]At least one of {utils.color(["group", "site", "label"], "cyan")} is also required[/]']
        header += [""]
        for idx, (field, description) in enumerate(field_dict[self.type]["optional"].items(), start=1):
            header += [f"{'Where ' if idx == 1 else '      '}[cyan]{field}[/]: [italic dark_olive_green2]{description}[/]"]

        return "\n".join(header)

    @property
    def parent_key_text(self) -> str:
        return (
            f"[italic]:information:  The examples above can also be under a parent [cyan]{self.type}[/] key ([dark_olive_green2]json[/] or [dark_olive_green2]yaml[/]).\n"
            "   This allows one import file with [cyan]devices[/], [cyan]groups[/], [cyan]labels[/], and [cyan]sites[/] to be used for multiple batch operations.[/italic]"
        )

    @property
    def command_text(self) -> str:
        return COMMAND_TEXT[self.type][self.action]

    @property
    def by_parent_key(self) -> str:
        if "serial" in self.ds.headers:
            key = "serial"
        elif "name" in self.ds.headers and self.action not in ["delete", "other"]:
            key = "name"
        else:
            return

        _by_key = {self.clean[-1].get(key, "err"): {k: v for k, v in self.clean[-1].items() if k != key and v}}
        segment = ExampleSegment(yaml.safe_dump(_by_key), example_type="yaml", example_title=f".yaml by {key} example")
        segment_title = f"[italic]:information:  {self.type.capitalize()} keyed by [cyan]{key}[/] is also acceptable ([dark_olive_green2]json[/] or [dark_olive_green2]yaml[/]).[/italic]"

        return f"{segment_title}\n{segment}"

    @property
    def txt_file_example(self) -> List[str] | None:
        if not self.by_text_field:
            return
        if self.by_text_field not in self.ds.dict[0]:  # pragma: no cover
            log.error(f"Example provided by_text_field {self.by_text_field}, but it does not exist in the example data")
            return

        return "\n".join(
            [
                "----------- [bright_green].txt example[/] ---------------",
                f"{self.by_text_field}  <-- [dim italic]header is optional for txt[/]",
                *[d[self.by_text_field] for d in self.ds.dict],
                "----------------------------------------\n"
            ]
        )



common_add_delete_end = """
[italic]:information:  Batch add and batch delete operations are designed so the same import file can be used.[/]
[italic]   The delete operation does not require as many fields, the cli will ignore the fields it does not need.[/]
"""

generic_end = """
[italic]:information:  Most batch operations are designed so the same file can be used for multiple automations.
   the fields not required for a particular automation will be ignored.[/]
"""

device_verify_data = """
serial,mac,group,site,label,subscription
CN12345678,aabbccddeeff,phl-access,WadeLab,label1,foundation_switch_6300
CN12345679,aa:bb:cc:00:11:22,phl-access,Barn,,advanced_ap
"""

# -- // ADD DEVICES \\ --  NOT USED
# This uses example.full_text property, retaining for reference
device_add_data = """
serial,mac,group,subscription
CN12345678,aabbccddeeff,phl-access,foundation_switch_6300
CN12345679,aa:bb:cc:00:11:22,phl-access,advanced_ap
"""

example = Example(device_add_data, type="devices", action="add")
clibatch_add_devices = f"""{example.command_text}

{example.header}

{example.mac_text}
{example.ignore_text}

{example}

[italic]:information:  Devices keyed by [cyan]serial[/] is also acceptable (json and yaml).[/italic]
{"-":{"-"}<16}[bright_green] .yaml by serial example[reset]: {"-":{"-"}<15}
USABC1234:
  mac: aabb.ccdd.eeff
  group: SNANTX
  licence: advanced_ap
{"-" * 57}

{example.parent_key_text}
{common_add_delete_end}
"""

# -- // MOVE DEVICES \\ --
device_move_data="""
serial,mac,group,site,label,retain_config
CN12345678,aabbccddeeff,phl-access,snantx-1201,,false
CN12345679,aa:bb:cc:00:11:22,phl-access,pontmi-102,label1,false
CN12345680,aabb-ccdd-8899,chi-access,main,core-devs,true
"""
example = Example(device_move_data, type="devices", action="move")
clibatch_move_devices = f"""{example.command_text}

{example.header}

{example.mac_text}
{example.ignore_text}

{example}

{example.parent_key_text}
{common_add_delete_end}
"""

# -- // RENAME DEVICES \\ --
data="""
serial,hostname
CN12345678,barn.615.ab12
CN12345679,snantx.655.afb1
CN12345680,ind.755.af9b
"""

example = Example(data, type="devices", action="rename")
clibatch_rename_aps = f"""[italic cyan]cencli batch rename aps IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]hostname[/]

Where [cyan]serial[/] The serial of the AP to be renamedd
      [cyan]hostname[/] The desired name to be applied to the AP

{example}

{example.parent_key_text}
{generic_end}"""

# -- // UPDATE APs \\ --
fields = [
    'serial',
    'hostname',
    'ip',
    'mask',
    'gateway',
    'dns',
    'domain',
    'disable_radios',
    'enable_radios',
    'access_radios',
    'monitor_radios',
    'spectrum_radios',
    'flex_dual_exclude',
    'antenna_width',
    'uplink_vlan',
    'gps_altitude',
    'ant_24_gain',
    'ant_5_gain',
    'ant_6_gain',
]
data=f"""
{','.join(fields)}
CN12345678,barn.615.ab12,,,,,consolepi.com,2.4,,,,,,,,,,
CN12345679,snantx.655.afb1,10.0.31.101,255.255.255.0,10.0.31.1,10.0.30.51 10.0.30.52,consolepi.com,,,,,,6,,,,,
CN12345680,ind.755.af9b,,,,,,,,,,2.4 5 6,,,,,,
"""

example = Example(data, type="devices", action="update")
clibatch_update_aps = f"""[italic cyan]cencli batch update aps IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [red]serial[/], {utils.color(fields[1:], "cyan")} [italic red](red=required)[/]

Where [cyan]serial[/] The serial of the AP to be updated
      [cyan]hostname[/] The desired name to be applied if renaming AP

      [italic]The following are only required and only valid if setting static IP[/]
        [cyan]ip[/] The IP of the AP if setting static IP
        [cyan]mask[/] The subnet mask (i.e. 255.255.255.0)
        [cyan]gateway[/] The default gateway
        [cyan]dns[/] DNS server addresses (space separated)
        [cyan]domain[/] domain name (dns search suffix)

      [italic]The following radio settings accept a list or a space separated string. valid values: '2.4, 5, 6'[/]
        [italic][bright_green]i.e.[/]: "2.4 6" or [2.4, 6] or "2.4"[/]
        [cyan]disable_radios[/] Radio(s) to disable
        [cyan]enable_radios[/] Radio(s) to enable
        [cyan]access_radios[/]  Radio(s) to set to access mode [dim italic](the default)[/]
        [cyan]monitor_radios[/] Radio(s) to set to monitor mode
        [cyan]spectrum_radios[/] Radio(s) to set to spectrum mode

      [cyan]flex_dual_exclude[/] Specify the radio to exclude for flex dual radio APs.  i.e. specify 6 to ensure AP always uses [cyan]2.4 and 5Ghz[/] radios
      [cyan]antenna_width[/] Only valid for APs that support dynamic antenna width (i.e.: 679).  Valid values: [cyan]narrow[/], [cyan]wide[/]
      [cyan]uplink_vlan[/] Provide PVID for VLAN if AP is to be managed over a [bright_green]tagged[/] VLAN
      [cyan]gps_altitude[/] For 6Ghz Standard Power: APs installation height / the number of meters from the ground
      [cyan]ant_24_gain[/] Set External antenna gain for 2.4Ghz radio
      [cyan]ant_5_gain[/] Set External antenna gain for 2.4Ghz radio
      [cyan]ant_6_gain[/] Set External antenna gain for 2.4Ghz radio

{example}

{example.parent_key_text}
{generic_end}"""

# -- // DELETE DEVICES \\ --
data = """
serial,subscription
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap
"""
example = Example(data, type="devices", action="delete")
clibatch_delete_devices = f"""[italic cyan]cencli batch delete devices IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [bright_green]-[/] [cyan]serial[/] [italic](any other keys will be ignored)[/]

{example.ignore_text}

[italic]Examples show extra [cyan]subscription[/] field which is ignored:
{example}
{example.parent_key_text}
{common_add_delete_end}
"""

# -- // ADD SITES \\ --
data = """
name,address,city,state,zipcode,country
site1,123 Privacy Dr,Anytown,TN,37066,US
site2,,Noblesville,IN,46060,US
"""
example = Example(data, type="sites", action="add")

clibatch_add_sites = f"""[italic cyan]cencli batch add sites IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    {utils.color(['name'], "red")}, {utils.color(['address', 'city', 'state', 'zipcode', 'country', 'longitude', 'latitude'], "cyan")} [italic red](red=required)[/]

[italic]:information:   Provide address fields, or geo-location ({utils.color(['longitude' ,'latitude'])}) [red]not both[/].
[italic]   Central will calc long/lat if address is provided,[/]
[italic]   but does not determine address from long/lat

{example.ignore_text}

{example}

{example.parent_key_text}
{common_add_delete_end}
"""

# -- // DELETE DEVICES \\ --
data = """
name
site1
site2
site3
"""
example = Example(data, type="sites", action="delete")

clibatch_delete_sites = f"""[italic cyan]cencli batch delete sites IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [bright_green]-[/] [cyan]name[/] [italic](any other keys will be ignored)[/]

{example}
{example.ignore_text}
{common_add_delete_end}
"""

clibatch_add_labels = f"""[italic cyan]cencli batch add labels IMPORT_FILE[/]:

For {utils.color(['yaml', 'json'], color_str='cyan')}, & [cyan]csv[/] formats, labels should be under a 'labels' key/header.
The 'labels' key/header is optional if import file is a simple text file.

-------------- [cyan]yaml[/] --------------------
labels:
  - example1
  - example2
  - example3

[bright_green]- OR -[/]

labels: {escape('[example1, example2, example3]')}
----------------------------------------
[italic]Both are valid yaml[/]

-------------- [cyan]json[/] --------------------
"labels": [
  "example1",
  "example2",
  "example3"
]
----------------------------------------

----------- [cyan]csv or txt[/] -----------------
labels     [magenta]<-- this is the header column[/] [grey42](optional for txt)[/]
example1       [magenta]<-- these are label names[/]
example2
example3
----------------------------------------
"""

clibatch_delete_labels = clibatch_add_labels.replace('batch add labels', 'batch delete labels')
clibatch_migrate_devs_by_site = clibatch_add_labels.replace('batch add labels IMPORT_FILE', 'migrate IMPORT_FILE --import-sites...').replace("labels", "sites")

# -- // ADD GROUPS \\ --
data = """
name,types,wired-tg,wlan-tg,gw-role,aos10,cnx,gw-config,ap-config,gw-vars,ap-vars
main,,,,vpnc,true,true,,,,
san-branch,gw ap cx,,,,true,,/home/wade/san-branch-group-gw.j2,/home/wade/san-branch-group-gw.j2,,
"""
example = Example(data=data, type="groups", action="add")

# TODO verify aos10 default. make functional only tested with deploy yaml file need to make work for csv
    # [red]name[/],[cyan]types[/],[cyan]wired-tg[/],[cyan]wlan-tg[/],[cyan]gw-role[/],[cyan]aos10[/],[cyan]gw-config[/],[cyan]ap-config[/],[cyan]gw-vars[/],[cyan]ap-vars[/] [italic red](red=required)[/]
_default_false = escape("[default: False]")
def type_str(_type: str):
    return f"[dim]({_type})[/]"

clibatch_add_groups = f"""{example.command_text}

Accepts the following keys (include as header row for csv import):
    {utils.color(ADD_FIELDS['groups']["required"], color_str="red")}, {utils.color(list(ADD_FIELDS['groups']["optional"].keys()))} [italic red](red=required)[/]

[bold dark_olive_green2]Field Summary[/]:
  [cyan]name[/] {type_str('str')}: The name of the group. [dim red]{escape('[required]')}[/]
  [cyan]types[/] {type_str('str | list')}: defines what type of devices are allowed in the group.
    Valid values: ["ap", "gw", "cx", "sw" "sdwan"] [dim]{escape('[default: ap, gw, cx, sw]')}[/]
    :information:  For csv the field can be blank {escape('[use default: ap, gw, cx, sw]')}: or a space seperated list of device types.
    :information:  "sdwan" is for EdgeConnect SD-WAN portfolio (SilverPeak), when allowed it has to be the only type allowed.
  [cyan]wired-tg[/] {type_str('bool')}: Set to true to make the group a template group for switches. [dim]{_default_false}[/]
  [cyan]wlan-tg[/] {type_str('bool')}: Set to true to make the group a template group for APs.  [dim]{_default_false}[/]
  [cyan]gw-role[/] {type_str('str')}: [cyan]branch[/], [cyan]vpnc[/], or [cyan]wlan[/] only valid if gw type is allowed. [dim]{escape('[default: branch]')}[/]
  [cyan]aos10[/] {type_str('bool')}: set to true to enable group as aos10 group.  [dim]{escape('[default: AOS8 IAP]')}[/]
  [cyan]microbranch[/] {type_str('bool')}: Set to true to configure APs in the group as micro-branch APs [dim]{_default_false}[/]
  [cyan]monitor-only-cx[/] {type_str('bool')}: Set to true to enable CX switches as monitor only [dim]{_default_false}[/]
  [cyan]monitor-only-sw[/] {type_str('bool')}: Set to true to enable AOS-SW switches as monitor only [dim]{_default_false}[/]
  [cyan]cnx[/] {type_str('bool')}: Make group compatible with New Central (cnx).
    :warning:  All configurations will be pushed from New Central configuration model. [dim]{_default_false}[/]
    :information:  [cyan]cencli[/] does not support New Central APIs yet.
  [cyan]gw-config[/] {type_str('Path')}: Path to file containing gw group level config or jinja2 template.
  [cyan]ap-config[/] {type_str('Path')}: Path to file containing ap group level config or jinja2 template.
  [cyan]gw-vars[/] {type_str('Path')}: Path to variables used if gw-config is a j2 template.
  [cyan]ap-vars[/] {type_str('Path')}: Path to variables used if ap-config is a j2 template.

[dark_orange3]:warning:[/]  USE [cyan]ap-config[/] / [cyan]gw-config[/] variables with caution. Best to be familiar with these and the caveats before using.
If [cyan]gw-config[/] or [cyan]ap-config[/] is a j2 file and the associated [cyan]gw-vars[/] / [cyan]ap-vars[/] key is not provided
the cli will look for a yaml/json/csv variable file with the same name as the j2 file.

{example.ignore_text}

{example}

{example.parent_key_text}
{common_add_delete_end}
"""

# -- // DELETE GROUPS \\ --
data = "name\nphl-access\nsan-dc-tor\ncom-branches"
example = Example(data=data, type="groups", action="delete")

clibatch_delete_groups = f"""[italic cyan]cencli batch delete groups IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [bright_green]-[/] [cyan]name[/] [italic](any other keys will be ignored)[/]

{example}
{example.parent_key_text}

{common_add_delete_end}
"""

# -- // DEPLOY \\ --
clibatch_deploy = """
[bright_green]Batch Deploy[/]

This is a placeholder
TODO add deploy example
"""

# TODO REMOVE
# -- // CLASSIC SUBSCRIBE DEVICES \\ --
data="""serial,license
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap"""
example = Example(data, type="devices", action="other")
clibatch_subscribe_deprecated_delme = f"""[italic cyan]cencli batch subscribe IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]license[/] [italic](both are required)[/]
    [italic]Other keys/columns are allowed, but will be ignored.


{example}
{example.parent_key_text}
{generic_end}
"""

# -- // VARIABLES \\ --
data="""_sys_serial,_sys_lan_mac,_sys_hostname,_sys_gateway,_sys_module_command,user_var1,user_var2
US12345678,aabbccddeeff,snantx-idf1-sw1,10.0.30.1,type jl728a,value1,value2
SG12345679,ffee.ddcc.bbaa,snantx-idf1-sw2,10.0.30.1,type jl728a,value1,value2
TW12345680,01:aa:bb:cc:dd:ee,snantx-idf1-sw3,10.0.30.1,type jl728a,value1,value2"""
example = Example(data, type="variables", action="other")
clibatch_update_variables = f"""[italic cyan]cencli batch update variables IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]_sys_serial[/], [cyan]_sys_lan_mac[/] [italic](both are required)[/].


{example}
"""


# -- // ARCHIVE / UNARCHIVE \\ --
clibatch_archive = f"""[italic cyan]cencli batch archive IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/]  [dim italic]Other keys/columns are allowed, but will be ignored.[/dim italic]


[italic]:information:  A text file with a simple list of [cyan]serial numbers[/] is also acceptable[/]
----- [bright_green]csv or txt[/] ------
serial     [magenta]<-- this is the header column[/] [grey42](optional for txt)[/]
CN12345678
CN12345679
CN12345680
-----------------------

-------- .json example --------
[
    {{
        "serial": "CN12345678"
    }},
    {{
        "serial": "CN12345679"
    }},
    {{
        "serial": "CN12345680"
    }}
]
------------------------------

------ .yaml example ------
- serial: CN12345678
- serial: CN12345679
- serial: CN12345680
---------------------------

{example.parent_key_text}
{generic_end}
"""


# -- // GLP SUBSCRIBE DEVICES \\ --
data="""serial,subscription
CN12345678,foundation_switch_6300
CN12345679,0f468bdf-e485-087f-abff-fc881f54373c
CN12345680,advanced_ap"""
example = Example(data, type="devices", action="other")
clibatch_subscribe = f"""[italic cyan]cencli batch subscribe IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]subscription[/] [italic](both are required)[/]
    [italic]Other keys/columns are allowed, but will be ignored.


{example}
[italic]:information:  A simple list of [cyan]serial numbers[/] is acceptable when subscription is provided via [cyan]--sub[/] flag[/]
i.e. [cyan]cencli batch subscribe --sub advanced-switch-6200 import-file.txt[/]
----------- [cyan]csv or txt[/] -----------------
serial     [magenta]<-- this is the header column[/] [grey42](optional for txt)[/]
CN12345678
CN12345679
CN12345680
----------------------------------------

[italic]:information:  A simplified yaml keyed by [cyan]subscription [dim](name or id)[/dim][/cyan] followed by a list of [cyan]serial numbers[/]
to be assigned to the subscription. i.e.[/italic]
----------- Simplified [bright_green].yaml example[/] ---------------
foundation_switch_6300:  [dim italic]<-- Can be subscription Name or ID[/]
  - CN12345678
  - CN12345679
  - CN12345680
0f468bdf-e485-087f-abff-fc881f54373c:
  - US12345678
  - US87654321
  - TW01234565
--------------------------------------------------

[italic]:information:  If Subscription name is used, and multiple subscriptions with that name are available the
   subscription with with unused subscriptions available and the most remaining time is used.  Specify the
   subscription by id to assign devices to a specific subscription.  Use [cyan]cencli show subscriptions[/] to see
   subscription IDs.[/italic]

{example.parent_key_text}
{generic_end}
"""

# -- // UNSUBSCRIBE DEVICES \\ --
data = """
serial,license
CN12345678,foundation_switch_6300
CN12345679,foundation_switch_6200
CN12345680,advanced_switch_6300
"""
example = Example(data, type="devices", action="other")
clibatch_unsubscribe = f"""[italic cyan]cencli batch unsubscribe IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]license[/]

[italic]Other fields can be included, but only serial, and license are evaluated
any subscriptions associated with the serial will be removed.

{example}
{example.parent_key_text}
{generic_end}
"""

# -- // ADD MACS (cloud-auth) \\ --
data="""mac,name
00:09:B0:75:65:D1,Integra
00:1B:4F:23:8A:3E,Avaya VoIP
3C:A8:2A:A6:07:0B,HP Thin Client"""

clibatch_add_macs = f"""[italic cyan]cencli batch add macs IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [red]mac[/], [cyan]name[/] [italic red](red=required)[/]

{Example(data, type="macs", action="add", by_text_field="mac")}

[italic]:information:  Also supports {utils.color(['Mac Address', 'Client Name'], color_str='cyan')} as alternative headers.[/]
    [dim italic] These are the headers Central Cloud-Auth Expects, headers are converted to what is required regardless.[/]
{example.ignore_text.replace('Devices', 'MACs')}
"""

# -- // ADD MPSK (cloud-auth) \\ --  REMOVED MPSK Column does not appear to be supported
data="""name,role,status
wade@example.com,admin_users,enabled
jerry@example.com,dia,enabled
stephanie@example.com,general_users,enabled"""
example = Example(data, type="mpsk", action="add")

clibatch_add_mpsk = f"""[italic cyan]cencli batch add mpsk IMPORT_FILE --ssid <SSID>[/]:

Requires the following keys (include as header row for csv import):
    [cyan]name[/], [cyan]role[/], [cyan]status[/]
    [dim italic]:information:  All other fields are ignored[/]

:information:  MPSK will be randomly generated.
:information:  Roles should exist in Central.
:information:  [cyan]--ssid[/] Option is required when uploading Named MPSKs.


{example}

[italic]:information:  Also supports {utils.color(['Name', 'Client Role', 'Status'], color_str='cyan')} as alternative headers.[/]
    [dim italic] These are the headers Central Cloud-Auth Expects, headers are converted to what is required regardless.[/]
{example.ignore_text.replace("Mpsk", "MPSKs")}
"""


class ImportExamples:
    def __init__(self):
        self.add_devices = Example(device_add_data, type="devices", action="add").full_text
        self.verify = Example(device_verify_data, type="devices", action="verify").full_text
        self.add_sites = self.add_site = clibatch_add_sites
        self.add_groups = clibatch_add_groups
        self.add_labels = clibatch_add_labels
        self.add_macs = clibatch_add_macs
        self.add_mpsk = clibatch_add_mpsk
        self.delete_devices = clibatch_archive.replace("archive", "delete devices")
        self.delete_sites = clibatch_delete_sites
        self.delete_groups = clibatch_delete_groups
        self.delete_labels = clibatch_delete_labels
        self.deploy = clibatch_deploy
        self.subscribe = clibatch_subscribe
        self.unsubscribe = clibatch_unsubscribe
        self.archive = clibatch_archive
        self.unarchive = clibatch_archive.replace("archive", "unarchive")
        self.move_devices = Example(device_move_data, type="devices", action="move").full_text
        self.rename_aps = clibatch_rename_aps
        self.update_aps = clibatch_update_aps
        self.update_variables = clibatch_update_variables
        self.add_variables = clibatch_update_variables.replace("update variables", "add variables")
        self.update_devices = clibatch_update_aps.replace("update aps", "update devices")
        # self.assign_subscriptions = clibatch_assign_subscriptions
        self.migrate_devs_by_site = clibatch_migrate_devs_by_site
        self.migrate_devices = clibatch_add_devices.replace("batch add devices", "migrate")

    def __getattr__(self, key: str):
        if key != "__iter__" and key not in self.__dict__.keys():  # pragma: no cover
            log.error(f"An attempt was made to get {key} attr from ImportExamples which is not defined.")
            return f":warning: [bright_red]Error[/] no str defined for [cyan]ImportExamples.{key}[/]"

cron_weekly = """#!/usr/bin/env bash

/bin/su -c "{{py_path}} {{exec_path}} refresh token -d {{accounts}}" {{user}} &&
    logger -t centralcli "Token Refreshed via cron" ||
    logger -t centralcli "Token Refresh returned error"
"""

cencli_config_example = """CFG_VERSION: 2

workspaces:
  default:
    cluster: internal
    ssl_verify: true                                                  # Optional, Can be set globally or within a workspace.  Defaults to True if not provided anywhere.
    glp:                                                              # --- GreenLake ---
      client_id: 7268afzt-4d84-2b14-ac3c-4c3gcvra11a9                 # Refer to: https://developer.arubanetworks.com/new-central/docs/generating-and-managing-access-tokens
      client_secret: 1349d637688a330a81d3423df566e7b0
      base_url: https://global.api.greenlake.hpe.com                  # Optional The glp base url is the same for all public clusters, this is potentially required for VPC/On Prem deployments.
    central:                                                          # --- New Central ---
      base_url: https://internal.api.central.arubanetworks.com        # Optional, Can provide the 'cluster' at the parent level.  cencli can then determine the base_url
    classic:                                                          # --- Classic Central ---
      base_url: https://internal-apigw.central.arubanetworks.com      # Optional, Can provide the 'cluster' at the parent level.  cencli can then determine the base_url
      client_id: CZ3r5b7ctiaHr6PaL3R00155dc048Fe                      # Refer to: https://developer.arubanetworks.com/central/docs/api-gateway
      client_secret: jqXrs7lsf28557f2wADeIssOc001O3s
      username: wade@example.com                                      # Optional, but allow cencli to create a new set of token if the current refresh token expires
      password: somepassword                                          # Use 'cencli show cron' to see how to setup cron to automatically refresh the tokens once a week.
      tokens:
        access: M4wADeIsS0c00148KGipv1v09k4uB3cM                      # FYI: the tokens in the config become stale as soon as they are refreshed by cencli.  The refreshed tokens
        refresh: s4lhIvwADeIsS0c00Lxlo7Llr0OURQMT                     #   are stored elsewhere in the cache.  This allows for an easy place to update them if needed.
        webhook: 7RSaW8hZQkO1qVAqzPsE                                 # Port this system would listen on for webhooks from Aruba Central.  Only applies if optional extra 'hook-proxy' is installed.  See README
        wss_key: ezkGbGd_really_long_key_blah_blah                    # Optional, but required to use -f option with 'cencli show logs -f' and 'cencli show audit logs -f'.  Streaming should be subscribed for Audit and Monitoring.
      webhook:                                                        # This section only applies if optional extra 'hook-proxy' is installed.  See README
        port: 9443                                                    # Optional, Port this system would listen on for webhooks from Aruba Central.  Only applies if optional extra 'hook-proxy' is installed.  See README
        token: 7RSaW8hZQkO1qVAqzPsE                                   # Optional, you can put the token here, or under the tokens key.
    other-workspace:                                                  # webhook proxy will listen on 9443 by default
      cluster: us5
      # ... Same format as above.  Repeat for any other workspaces you want to interact with

# -- The following items are optional --
ssl_verify: true      # Can be set globally or in a workspace config.  Workspace config takes precedence if set.  Defaults to True.
debug: false          # Enable debug, for more logs/messages.  Default is False
debugv: false         # Verbose debug.  Default is False
cache_client_days: 90 # The local cache will store clients that have connected within the last 90 days.
forget_ws_after: 90   # when using an alternate workspace via --ws myotherws.  If this is set, cencli will continue to use
                      # myotherws workspace until no command has been issued for n minutes (90 in this case),
                      # or until -d (use default) or --account some_other_ws is used

                      # By default it will remember the last account used forever and only switch back to the default account when -d is used
                      # Set to 0 to disable sticky account functionality.  (Would use default account unless --account <account-name> is provided.)

                      # You can also set env var ARUBA_ACCOUNT to the workspace name configured in this file.

dev_options:          # --- Developer Options ---
  limit: 10           # Overrides the default pagination limit requested for each API call.  To test pagination/rate-limiting
  sanitize: false     # Sanitize output (for video demo, animated GIF creation).
  capture_raw: false  # Captures the raw response of all get commands in a common file.  So they can be used for automated testing.
  # There are also hidden command line flags supported globally for these options
  # --debug-limit --sanitize --capture-raw
"""