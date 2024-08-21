#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Literal, List, Dict, Any
from rich.console import Console
from rich.json import JSON
from centralcli import log, utils
import tablib
import yaml
import json
console = Console(emoji=False)

# [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]  # TODO implement this device del
# TODO document examples and uncomment below.  provide examples for all format/types
# print("See https://central-api-cli.readthedocs.io for full examples.


# TODO build examples for json yaml a master import for all make example the same for add and delete
# (noting that delete only requires 1 field)
# provide estimate on number of API calls.

# TODO pass examples through lexer

# TODO build csv examples for all the below, send through tablib and use .json .yaml .csv methods of tablib to generate examples for each
# TODO These Examples run on import need to make properties of class or something to avoid running on import


TabLibFormats = Literal['json', 'yaml', 'csv', 'tsv', 'dbf', 'html', 'jira', 'latex', 'df', 'rst', 'cli']
ExampleType = Literal["devices", "sites", "groups", "labels", "macs", "mpsk"]
Action = Literal["add", "delete", "move", "rename", "other"]

ADD_FIELDS = {
     "devices": {
          "required": ["serial", "mac"],
          "optional": {
              "group": "(pre-provision device to group)",
              "license": "(apply license to device)"
          }
    }
}
MOVE_FIELDS = {
     "devices": {
          "required": ["serial", "mac"],
          "optional": {
              "group": "(move device to group)",
              "site": "(move device to site)",
              "label": "(assign label to device)",
              "retain_config": "Retain devices current configuration during group move. [grey42](Applies to CX switches Only)[/]"
          }
    }
}
COMMAND_TEXT = {
    "devices": {
        "add": "[italic cyan]cencli batch add devices IMPORT_FILE[/]",
        "delete": "[italic cyan]cencli batch delete devices IMPORT_FILE[/]",
        "move": "[italic cyan]cencli batch move devices IMPORT_FILE[/]"
    }
}


class Example:
    """
    convert csv data as string into csv, json, and yaml
    """
    def __init__(self, data: str, type: ExampleType = None, action: Action = None, data_format: TabLibFormats = "csv") -> None:
        self.data = data.strip()
        self.type = type or "devices"
        self.action = action or "add"
        self.ds = tablib.Dataset().load(self.data, format=data_format)
        self.json = self.get_json()
        self.yaml = self.get_yaml()
        self.csv = self.get_csv()
        self.mac_text = "[italic]:information:  MAC Address can be nearly any format imaginable.[/]"
        self.ignore_text = f"[italic]:information:  {self.type.capitalize()} with the either [cyan]ignore[/], or [cyan]retired[/] keys set to true are ignored.[/]"

    def __str__(self):
        ret = [
                f'{"-":{"-"}<21}[bright_green] .csv example[reset]: {"-":{"-"}<21}',
                self.csv,
                "-" * 57,
                "",
                f'{"-":{"-"}<21}[bright_green] .json example[reset]: {"-":{"-"}<20}',
                self.json,
                "-" * 57,
                "",
                f'{"-":{"-"}<21}[bright_green] .yaml example[reset]: {"-":{"-"}<20}',
                self.yaml,
                "-" * 57
        ]
        if self.type == "devices" and self.action not in ["delete", "other"]:
            ret += [self.by_serial]

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
            str(self),
            "",
            self.parent_key_text,
            common_add_delete_end
        ]
        return "\n".join(ret)

    def _handle_bools(self, data: tablib.Dataset) -> List[Dict[str, Any]]:
        bool_strings = ["true", "false", "yes", "no"]
        def _convert_bool(value: str) -> str | bool | int:
            if value in bool_strings:
                return bool(value)
            elif value.isdigit():
                return int(value)
            elif value == "":
                return None
            else:
                return value

        return [{k: _convert_bool(v) for k, v in inner_dict.items()} for inner_dict in data.dict]

    def get_json(self):
        data = json.dumps(self._handle_bools(self.ds))
        return JSON(data).text.markup

    def get_yaml(self):
        return yaml.safe_dump(self._handle_bools(self.ds)).rstrip()

    def get_csv(self):
        return self.ds.csv.rstrip()

    @property
    def header(self):
        header =  ["Accepts the following keys (include as header row for csv import):"]
        field_dict = ADD_FIELDS if self.action == "add" else MOVE_FIELDS
        # all_fields = [*field_dict[self.type]["required"], *field_dict[self.type].get("optional", {}).keys()]  # Only setup for add devices
        required_strings =  utils.color(field_dict[self.type]["required"], "red")
        # header += [f'    {utils.color(all_fields, color_str="cyan")}']
        header += [f'    {required_strings}']
        if field_dict[self.type].get("optional"):
            header[-1] = f'{header[-1]}, {utils.color(list(field_dict[self.type]["optional"].keys()), "cyan")} [italic red](red=required)[/]'
            # cnt = len(field_dict[self.type]["optional"])
            # {' and' if idx == 1 and idx != cnt else ''}{' are optional.' if idx == cnt else ''}
            header += [""]
            for idx, (field, description) in enumerate(field_dict[self.type]["optional"].items(), start=1):
                header += [f"{'Where ' if idx == 1 else '      '}[cyan]{field}[/] [italic dark_olive_green2]{description}[/]"]

        return "\n".join(header)

    @property
    def parent_key_text(self) -> str:
        return (
            f"[italic]:information:  The examples above can also be under a parent [cyan]{self.type}[/] key ([dark_olive_green2]json[/] and [dark_olive_green2]yaml[/]).\n"
            "   This allows one import file with [cyan]devices[/], [cyan]groups[/], [cyan]labels[/], and [cyan]sites[/] to be used for multiple batch operations.[/italic]"
        )

    @property
    def command_text(self) -> str:
        return COMMAND_TEXT[self.type][self.action]

    @property  # TODO just check if self.ds has "serial" and use first item as example
    def by_serial(self) -> str:
        by_serial = [
            '\n[italic]:information:  Devices keyed by [cyan]serial[/] is also acceptable ([dark_olive_green2]json[/] and [dark_olive_green2]yaml[/]).[/italic]',
            f'{"-":{"-"}<16}[bright_green] .yaml by serial example[reset]: {"-":{"-"}<15}',
            'USABC1234:',
        ]
        if self.action != "rename":
            by_serial += [
                '  mac: aabb.ccdd.eeff',
                '  group: SNANTX',
                '  licence: advanced_ap',
            ]
        else:
            by_serial += [
                '  hostname: barn.615.ab12'
            ]
        by_serial += [f'{"-" * 57}']
        return "\n".join(by_serial)


common_add_delete_end = """
[italic]:information:  Batch add and batch delete operations are designed so the same import file can be used.[/]
[italic]   The delete operation does not require as many fields, the cli will ignore the fields it does not need.[/]"""


device_add_data = """
serial,mac,group,license
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

[italic]Note: Most imports use a common format, so the same import file can be leveraged for multiple batch operations.
      i.e. The same file can be used to batch add the APs, then to batch rename the APs (once they've checked in).
      Fields not required for a specific batch operation are ignored.[/]
"""

data = """
serial,license
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap
"""
example = Example(data, type="devices", action="delete")
clibatch_delete_devices = f"""[italic cyan]cencli batch delete devices IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [bright_green]-[/] [cyan]serial[/] [italic](any other keys will be ignored)[/]

{example.ignore_text}

[italic]Examples show extra [cyan]license[/] field which is ignored:
{example}
{example.parent_key_text}
{common_add_delete_end}
"""

data = """
name,address,city,state,zipcode,country
site1,123 Privacy Dr,Anytown,TN,37066,US
site2,,Noblesville,IN,46060,US
"""
example = Example(data, type="sites", action="add")

clibatch_add_sites = f"""[italic cyan]cencli batch add sites IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    {utils.color(['name', 'address', 'city', 'state', 'zipcode', 'country', 'longitude', 'latitude'], "cyan")}

[italic]:information:  [red]name[/] is required.
[italic]   Provide address fields, or geo-location ({utils.color(['longitude' ,'latitude'])}) [red]not both[/].
[italic]   Central will calc long/lat if address is provided,[/]
[italic]   but does not determine address from long/lat

{example.ignore_text}

{example}

{example.parent_key_text}
{common_add_delete_end}
"""
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

clibatch_add_labels = """[italic cyan]cencli batch add labels IMPORT_FILE[/]:

For all formats, labels should be under a 'labels' key/header.

-------------- [cyan]yaml[/] --------------------
labels:
  - example1
  - example2
  - example3

[bright_green]- OR -[/]

labels: \[example1, example2, example3]
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

# TODO verify aos10 default. make functional only tested with deploy yaml file need to make work for csv
clibatch_add_groups = f"""

THIS COMMAND IS CURRENTLY DISABLED AS MORE WORK/TESTING NEEDS TO BE DONE.

[italic cyan]cencli batch add groups IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
If importing yaml or json the following fields can optionally be under a 'groups' key
[cyan]name[/],[cyan]types[/],[cyan]wired-tg[/],[cyan]wlan-tg[/],[cyan]gw-role[/],[cyan]aos10[/],[cyan]gw-config[/],[cyan]ap-config[/],[cyan]gw-vars[/],[cyan]ap-vars[/]
Where '[cyan]name[/](str)' is the only required field.
      '[cyan]types[/](str or list)' defines what type of devices are allowed in the group.
            All types are allowed if not provided.
            Valid values: ["ap", "gw", "cx", "sw"]
            For csv leave the field blank of populate with "cx" or "[cx,ap,sw]"
      '[cyan]wired-tg[/](bool)' Set to true to make the group a template group for switches false be default.
      '[cyan]wlan-tg[/](bool)' Set to true to make the group a template group for APs false be default.
      '[cyan]gw-role[/](str)' "branch" or "vpnc" only valid if gw type is allowed. Defaults to "branch" if not provided.
      '[cyan]aos10[/](bool)' set to true to enable group as aos10 group, defaults to aos8 IAP
      '[cyan]gw-config[/](Path)' Path to file containing gw group level config or jinja2 template.
      '[cyan]ap-config[/](Path)' Path to file containing ap group level config or jinja2 template.
      '[cyan]gw-vars[/](Path)' Path to variables used if gw-config is a j2 template.
      '[cyan]ap-vars[/](Path)' Path to variables used if ap-config is a j2 template.
            [italic]Use ap-config and gw-config with caution
            If gw-config or ap-config is a j2 file and the associated **-vars key is not provided
            the cli will look for a yaml/json/csv with the same name as the j2 file.

[blink]:warning:[/] USE **-config variables with caution. Best to be familiar with these and the caveats before using.

[bright_green].csv example[reset]:
-------------- csv --------------
name,types,wired-tg,wlan-tg,gw-role,aos10,gw-config,ap-config,gw-vars,ap-vars
main,,,,vpnc,true,,,,
san-branch,"[gw,ap,cx]",,,,true,/home/wade/san-branch-group-gw.j2,/home/wade/san-branch-group-gw.j2,,
---------------------------------
{common_add_delete_end}
"""
data = "name\nphl-access\nsan-dc-tor\ncom-branches"
example = Example(data=data, type="groups", action="delete")

clibatch_delete_groups = f"""[italic cyan]cencli batch delete groups IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [bright_green]-[/] [cyan]name[/] [italic](any other keys will be ignored)[/]

{example}
{example.parent_key_text}
{common_add_delete_end}
"""


clibatch_deploy = """
[bright_green]Batch Deploy[/]

This is a placeholder
TODO add deploy example
"""

data="""serial,license
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap"""
example = Example(data, type="devices", action="other")
clibatch_subscribe = f"""[italic cyan]cencli batch subscribe devices IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]license[/] [italic](both are required)[/]
    [italic]Other keys/columns are allowed, but will be ignored.


{example}
{example.parent_key_text}

NOTE: Most batch operations are designed so the same file can be used for multiple automations
      the fields not required for a particular automation will be ignored.
"""
data = """
serial
CN12345678
CN12345679
CN12345680
"""
example = Example(data, type="devices", action="other")
clibatch_unsubscribe = f"""[italic cyan]cencli batch unsubscribe IMPORT_FILE[/]:

Accepts the following keys (include as header row for csv import):
    [cyan]serial[/]

[italic]Other fields can be included, but only serial, is evaluated
any subscriptions associated with the serial will be removed.

{example}
{example.parent_key_text}

NOTE: Most batch operations are designed so the same file can be used for multiple automations
      the fields not required for a particular automation will be ignored.
"""

data="""Mac Address,Client Name
00:09:B0:75:65:D1,Integra
00:1B:4F:23:8A:3E,Avaya VoIP
3C:A8:2A:A6:07:0B,HP Thin Client"""

clibatch_add_macs = f"""[italic cyan]cencli batch add macs IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]Mac Address[/]
Optional keys:
    [cyan]Client Name[/]

{Example(data, type="macs", action="add")}
"""

data="""Name,MPSK,Client Role,Status
wade@example.com,chant chemo domain lugged,admin_users,enabled
jerry@example.com,quick dumpster offset jack,dia,enabled
stephanie@example.com,random here words go,general_users,enabled"""

clibatch_add_mpsk = f"""[italic cyan]cencli batch add mpsk IMPORT_FILE --ssid <SSID>[/]:

Requires the following keys (include as header row for csv import):
    [cyan]Name[/], [cyan]Client Role[/], [cyan]Status[/]

:information:  MPSK will be randomly generated if not provided.
:information:  Roles must exist in Central.
:information:  [cyan]--ssid[/] Option is required when uploading Named MPSKs.


{Example(data, type="mpsk", action="add")}
"""


class ImportExamples:
    def __init__(self):
        self.add_devices = Example(device_add_data, type="devices", action="add").full_text
        self.add_sites = clibatch_add_sites
        self.add_groups = clibatch_add_groups
        self.add_labels = clibatch_add_labels
        self.add_macs = clibatch_add_macs
        self.add_mpsk = clibatch_add_mpsk
        self.delete_devices = clibatch_delete_devices
        self.delete_sites = clibatch_delete_sites
        self.delete_groups = clibatch_delete_groups
        self.delete_labels = clibatch_delete_labels
        self.add_site = clibatch_add_sites
        self.deploy = clibatch_deploy
        self.subscribe = clibatch_subscribe
        self.unsubscribe = clibatch_unsubscribe
        self.archive = clibatch_unsubscribe.replace("unsubscribe", "archive")
        self.unarchive = clibatch_unsubscribe.replace("unsubscribe", "unarchive").replace("any subscriptions associated with the serial will be removed.\n", "")
        self.move_devices = Example(device_move_data, type="devices", action="move").full_text
        self.rename_aps = clibatch_rename_aps

    def __getattr__(self, key: str):
        if key not in self.__dict__.keys():
            log.error(f"An attempt was made to get {key} attr from ImportExamples which is not defined.")
            return f":warning: [bright_red]Error[/] no str defined for [cyan]ImportExamples.{key}[/]"
