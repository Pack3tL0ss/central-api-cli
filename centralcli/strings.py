#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Literal, List, Dict, Any
from rich.console import Console
from rich.syntax import Syntax
from rich.markup import escape
from pygments.lexers.data import JsonLexer, YamlLexer
from centralcli import log, utils
from centralcli.vendored.csvlexer.csv import CsvLexer
import tablib
import yaml
import json
console = Console(emoji=False)

# [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]  # TODO implement this device del

# TODO build examples for json yaml a master import for all make example the same for add and delete
# (noting that delete only requires 1 field)
# provide estimate on number of API calls.

# TODO These Examples run on import need to make properties of class or something to avoid running on import


TabLibFormats = Literal['json', 'yaml', 'csv', 'tsv', 'dbf', 'html', 'jira', 'latex', 'df', 'rst', 'cli']
ExampleType = Literal["devices", "sites", "groups", "labels", "macs", "mpsk"]
Action = Literal["add", "delete", "move", "rename", "other"]

_pad = " " * 6
ADD_FIELDS = {
    "devices": {
        "required": ["serial", "mac"],
        "optional": {
            "group": "Pre-provision device to group",
            "license": "Apply license to device"
        }
    },
    "groups": {
        "required": ["name"],
        "optional": {
            "types": f'Defines what type of devices are allowed in the group.\n{_pad}Valid values: ["ap", "gw", "cx", "sw"] [grey42]{escape("[default: All but sdwan allowed]")}[/]\n{_pad}For csv the field can be blank (all device types) or any of these formats: "cx" or "cx,ap" or {escape("[cx,ap,gw]")}',
            "wired-tg": f"Set to true to make the group a template group for switches. [grey42]{escape('[default: False]')}[/]",
            "wlan-tg": f"Set to true to make the group a template group for APs.  [grey42]{escape('[default: False]')}[/]",
            "gw-role": f"[cyan]branch[/], [cyan]vpnc[/] or [cyan]wlan[/] only applies if gw type is allowed. [grey42]{escape('[default: branch]')}[/]",
            "aos10": f"Set to true to enable group as aos10 group (APs).  [grey42]{escape('[default: AOS8 IAP]')}[/]",
            "microbranch": f"Set to true to configure APs in the group as micro-branch APs (implies aos_10). [grey42]{escape('[default: False]')}[/]",
            "monitor-only-cx": "Set to true to enable CX switches as monitor only.",
            "monitor-only-sw": "Set to true to enable AOS-SW switches as monitor only.",
            "cnx": f"Make group compatible with New Central (cnx)\n{_pad}:warning:  All configurations will be pushed from New Central configuration model. [grey42]{escape('[default: False]')}[/]",
            "gw-config": "Path to file containing gw group level config or jinja2 template.",
            "ap-config": "Path to file containing ap group level config or jinja2 template.",
            "gw-vars": "Path to variables used if gw-config is a j2 template.",
            "ap-vars": "Path to variables used if ap-config is a j2 template.",
        }
    }
}
MOVE_FIELDS = {
     "devices": {
          "required": ["serial", "mac"],
          "optional": {
              "group": "Move device to group",
              "site": "Move device to site",
              "label": "Assign label to device",
              "retain_config": "Retain devices current configuration as device level override. [grey42](Applies to CX switches Only)[/]"
          }
    }
}
COMMAND_TEXT = {
    "devices": {
        "add": "[italic cyan]cencli batch add devices IMPORT_FILE[/]",
        "delete": "[italic cyan]cencli batch delete devices IMPORT_FILE[/]",
        "move": "[italic cyan]cencli batch move devices IMPORT_FILE[/]"
    },
    "groups": {
        "add": "[italic cyan]cencli batch add groups IMPORT_FILE[/]"
    }
}


LEXERS = {
        "csv":  CsvLexer(ensurenl=False),
        "json": JsonLexer(ensurenl=False),
        "yaml": YamlLexer(ensurenl=False)
}
class ExampleSegment:
    def __init__(self, example_text: str, example_type: Literal["csv", "yaml", "json"] = "csv", example_title: str = None) -> None:
        self.original = example_text
        self.example_type = example_type
        self.example_text = self._format_example_text(example_text, example_type)
        example_title = None if not example_title else f" {example_title.strip()} "
        self.title = example_title or f" .{example_type} example "
        max_len = max([len(line.strip()) for line in example_text.splitlines()])
        self.max_len = max_len if max_len >= 57 else 57


    def __str__(self):
        return "\n".join(self.list)

    def __rich__(self):
        return str(self)

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
    def __init__(self, data: str, type: ExampleType = None, action: Action = None, data_format: TabLibFormats = "csv") -> None:
        self.data = data.strip()
        self.type = type or "devices"
        self.action = action or "add"
        self.ds = tablib.Dataset().load(self.data, format=data_format)
        self.clean = self._get_clean_data(self.ds)
        self.json = self.get_json()
        self.yaml = self.get_yaml()
        self.csv = self.get_csv()
        self.mac_text = "[italic]:information:  MAC Address can be nearly any format imaginable.[/]"
        self.ignore_text = f"[italic]:information:  {self.type.capitalize()} with either [cyan]ignore[/], or [cyan]retired[/] keys set to true are ignored.[/]"

    def __str__(self):
        ret = [*ExampleSegment(self.csv, "csv").list, *ExampleSegment(self.json, "json").list, *ExampleSegment(self.yaml, "yaml").list,]
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
        return [utils.strip_none(inner) for inner in out]

    def _handle_bools(self, data: tablib.Dataset) -> List[Dict[str, Any]]:
        bool_strings = ["true", "false", "yes", "no"]
        def _convert_bool(value: str, expecting_list: bool = False) -> str | bool | int | list:
            if expecting_list:
                if " " in value:
                    return value.split()
                elif "," in value:  # csv should only support space seperated, but leaving this in for now.
                    return value.lstrip("[").rstrip("]").split(",")
                elif value == "":
                    return None
                else:
                    return [value]
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
        return json.dumps(self.clean, indent=4)

    def get_yaml(self):
        return yaml.safe_dump(self.clean).rstrip()

    def get_csv(self):
        return self.ds.csv.rstrip()

    @property
    def header(self):
        header =  ["Accepts the following keys (include as header row for csv import):"]
        field_dict = ADD_FIELDS if self.action == "add" else MOVE_FIELDS
        required_strings =  utils.color(field_dict[self.type]["required"], "red")
        header += [f'    {required_strings}']
        if field_dict[self.type].get("optional"):
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


common_add_delete_end = """
[italic]:information:  Batch add and batch delete operations are designed so the same import file can be used.[/]
[italic]   The delete operation does not require as many fields, the cli will ignore the fields it does not need.[/]
"""

generic_end = """
[italic]:information:  Most batch operations are designed so the same file can be used for multiple automations
   the fields not required for a particular automation will be ignored.[/]
"""

# -- // ADD DEVICES \\ --  NOT USED
# This uses example.full_text property, retaining for reference
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

# -- // DELETE DEVICES \\ --
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

For all formats, labels should be under a 'labels' key/header.

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

# -- // ADD GROUPS \\ --
data = """
name,types,wired-tg,wlan-tg,gw-role,aos10,cnx,gw-config,ap-config,gw-vars,ap-vars
main,,,,vpnc,true,true,,,,
san-branch,gw ap cx,,,,true,,/home/wade/san-branch-group-gw.j2,/home/wade/san-branch-group-gw.j2,,
"""
example = Example(data=data, type="groups", action="add")

# TODO verify aos10 default. make functional only tested with deploy yaml file need to make work for csv
    # [red]name[/],[cyan]types[/],[cyan]wired-tg[/],[cyan]wlan-tg[/],[cyan]gw-role[/],[cyan]aos10[/],[cyan]gw-config[/],[cyan]ap-config[/],[cyan]gw-vars[/],[cyan]ap-vars[/] [italic red](red=required)[/]
_str = escape("[str]")
_str_or_list = escape("[str | list]")
_bool = escape("[bool]")
_path = escape("[Path]")
_default_false = escape("[default: False]")
clibatch_add_groups = f"""{example.command_text}

Accepts the following keys (include as header row for csv import):
    {utils.color(ADD_FIELDS['groups']["required"], color_str="red")}, {utils.color(list(ADD_FIELDS['groups']["optional"].keys()))} [italic red](red=required)[/]

Where [cyan]name[/]{_str}: The name of the group. [red italic]required[/]
      [cyan]types[/]{_str_or_list}: defines what type of devices are allowed in the group.
            Valid values: ["ap", "gw", "cx", "sw" "sdwan"] [grey42]{escape('[default: ap, gw, cx, sw]')}[/]
            :information:  For csv the field can be blank {escape('[use default: ap, gw, cx, sw]')}: or a space seperated list of device types.
            :information: "sdwan" is for EdgeConnect SD-WAN portfolio (SilverPeak), when allowed it has to be the only type allowed.
      [cyan]wired-tg[/]{_bool}: Set to true to make the group a template group for switches. [grey42]{_default_false}[/]
      [cyan]wlan-tg[/]{_bool}: Set to true to make the group a template group for APs.  [grey42]{_default_false}[/]
      [cyan]gw-role[/]{_str}: [cyan]branch[/], [cyan]vpnc[/], or [cyan]wlan[/] only valid if gw type is allowed. [grey42]{escape('[default: branch]')}[/]
      [cyan]aos10[/]{_bool}: set to true to enable group as aos10 group.  [grey42]{escape('[default: AOS8 IAP]')}[/]
      [cyan]microbranch[/]{_bool}: Set to true to configure APs in the group as micro-branch APs [grey42]{_default_false}[/]
      [cyan]monitor-only-cx[/]{_bool}: Set to true to enable CX switches as monitor only [grey42]{_default_false}[/]
      [cyan]monitor-only-sw[/]{_bool}: Set to true to enable AOS-SW switches as monitor only [grey42]{_default_false}[/]
      [cyan]cnx[/]{_bool}: Make group compatible with New Central (cnx).
            :warning:  All configurations will be pushed from New Central configuration model. [grey42]{_default_false}[/]
      [cyan]gw-config[/]{_path}: Path to file containing gw group level config or jinja2 template.
      [cyan]ap-config[/]{_path}: Path to file containing ap group level config or jinja2 template.
      [cyan]gw-vars[/]{_path}: Path to variables used if gw-config is a j2 template.
      [cyan]ap-vars[/]{_path}: Path to variables used if ap-config is a j2 template.

:warning:  USE [cyan]ap-config[/] / [cyan]gw-config[/] variables with caution. Best to be familiar with these and the caveats before using.
If [cyan]gw-config[/] or [cyan]ap-config[/] is a j2 file and the associated [cyan]gw-vars[/] / [cyan]ap-vars[/] key is not provided
the cli will look for a yaml/json/csv with the same name as the j2 file.

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

# -- // SUBSCRIBE DEVICES \\ --
data="""serial,license
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap"""
example = Example(data, type="devices", action="other")
clibatch_subscribe = f"""[italic cyan]cencli batch subscribe IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
    [cyan]serial[/], [cyan]license[/] [italic](both are required)[/]
    [italic]Other keys/columns are allowed, but will be ignored.


{example}
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

# -- // ADD MPSK (cloud-auth) \\ --
data="""Name,MPSK,Client Role,Status
wade@example.com,chant chemo domain lugged,admin_users,enabled
jerry@example.com,quick dumpster offset jack,dia,enabled
stephanie@example.com,random here words go,general_users,enabled"""
example = Example(data, type="mpsk", action="add")

clibatch_add_mpsk = f"""[italic cyan]cencli batch add mpsk IMPORT_FILE --ssid <SSID>[/]:

Requires the following keys (include as header row for csv import):
    [cyan]Name[/], [cyan]Client Role[/], [cyan]Status[/]

:information:  MPSK will be randomly generated if not provided.
:information:  Roles must exist in Central.
:information:  [cyan]--ssid[/] Option is required when uploading Named MPSKs.


{example}

{example.ignore_text.replace("Mpsk", "MPSKs")}
"""


class ImportExamples:
    def __init__(self):
        self.add_devices = Example(device_add_data, type="devices", action="add").full_text
        self.add_sites = self.add_site = clibatch_add_sites
        self.add_groups = clibatch_add_groups
        self.add_labels = clibatch_add_labels
        self.add_macs = clibatch_add_macs
        self.add_mpsk = clibatch_add_mpsk
        self.delete_devices = clibatch_delete_devices
        self.delete_sites = clibatch_delete_sites
        self.delete_groups = clibatch_delete_groups
        self.delete_labels = clibatch_delete_labels
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

cron_weekly = """#!/usr/bin/env bash

/bin/su -c "{{py_path}} {{exec_path}} refresh token -d {{accounts}}" {{user}} &&
    logger -t centralcli "Token Refreshed via cron" ||
    logger -t centralcli "Token Refresh returned error"
"""