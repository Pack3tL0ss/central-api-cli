#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from rich.console import Console
from rich.json import JSON
from centralcli import log
import tablib
import yaml
console = Console(emoji=False)

# TODO typer now supports markup_mode="rich" Don't need the help below, can just put the markup in the docstr

# [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]  # TODO implement this device del
# TODO document examples and uncomment below.  provide examples for all format/types
# print("See https://central-api-cli.readthedocs.io for full examples.


# TODO build examples for json yaml a master import for all make example the same for add and delete
# (noting that delete only requires 1 field)
# provide estimate on number of API calls.

# TODO pass examples through lexer

# TODO build csv examples for all the below, send through tablib and use .json .yaml .csv methods of tablib to generate examples for each
# TODO These Examples run on import need to make properties of class or something to avoid running on import

class Example:
    """
    convert csv data as string into csv, json, and yaml
    """
    def __init__(self, data: list | dict) -> None:
        self.data = data.strip()
        self.ds = tablib.Dataset().load(self.data)
        self.json = self.get_json()
        self.yaml = self.get_yaml()
        self.csv = self.get_csv()

    @staticmethod
    def _capture(text: str) -> str:
        console.begin_capture()
        console.print(text)
        return console.end_capture()


    def __str__(self):
        return "\n".join(
            [
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
        )

    def get_json(self):
        return JSON(self.ds.json).text.markup

    def get_yaml(self):
        return yaml.safe_dump(yaml.safe_load(self.ds.json)).rstrip()

    def get_csv(self):
        return self.ds.csv.rstrip()



common_add_delete_end = """
[italic]Note: Batch add and batch delete operations are designed so the same import file can be used.[/]
[italic]      The delete operation does not require as many fields, the cli will ignore the fields it does not need.[/]
"""

clibatch_add_devices = f"""
[italic cyan]cencli batch add devices IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
    If importing yaml or json the following fields can optionally be under a 'devices' key

[cyan]serial[/],[cyan]mac[/],[cyan]group[/],[cyan]license[/]
Where '[cyan]group[/]' (pre-provision device to group) and
      '[cyan]license[/]' (apply license to device) are optional.

[bright_green].csv example[reset]:
-------------------------- csv --------------------------
serial,mac,group,license
CN12345678,aabbccddeeff,phl-access,foundation_switch_6300
CN12345679,aa:bb:cc:00:11:22,phl-access,advanced_ap
CN12345680,aabb-ccdd-8899,chi-access,advanced_ap
---------------------------------------------------------
[italic]MAC Address can be nearly any format imaginable.[/]
{common_add_delete_end}
"""

data="""
serial,mac,group,site,label
CN12345678,aabbccddeeff,phl-access,snantx-1201,
CN12345679,aa:bb:cc:00:11:22,phl-access,pontmi-102,label1
CN12345680,aabb-ccdd-8899,chi-access,main,core-devs
"""

clibatch_move_devices = f"""
[italic cyan]cencli batch move devices IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
    [italic grey42]If importing yaml or json the following fields can optionally be under a 'devices' key[/italic grey42]

[cyan]serial[/],[cyan]group[/],[cyan]site[/],[cyan]label[/]
Where '[cyan]group[/]' Move device to specified group
      '[cyan]site[/]' Move device to specified site
            [italic]If device is currently in a different site it will be removed from that site[/]
      '[cyan]label[/]' Assign specified label to device

{Example(data)}

[italic]MAC Address can be nearly any format imaginable.[/]
{common_add_delete_end}
"""

clibatch_delete_devices = f"""
[italic cyan]cencli batch delete devices IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
[cyan]serial[/] ([italic]any other keys will be ignored[/])

[bright_green].csv example[reset] [italic]Example shows extra [cyan]license[/] key which is ignored:
-------------- csv --------------
serial,license
CN12345678,foundation_switch_6300
CN12345679,advanced_ap
CN12345680,advanced_ap
---------------------------------
{common_add_delete_end}
"""

clibatch_add_sites = f"""
[italic cyan]cencli batch add sites IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
If importing yaml or json the following fields can optionally be under a 'sites' key
name,address,city,state,zipcode,country

[bright_green].csv example[reset]:
-------------- csv ---------------------
name,address,city,state,zipcode,country
site1,123 Privacy Dr,Anytown,TN,37066,US
site2,,Noblesville,IN,46060,US
----------------------------------------

[italic]Note: Fields 'longitude,latitude' are also supported.
[italic]      Central will calc long/lat if address is provided.[/]
[italic]      but does not determine address from long/lat
{common_add_delete_end}
"""

clibatch_delete_sites = f"""
[italic cyan]cencli batch delete sites IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
If importing yaml or json the following fields can optionally be under a 'sites' key
[cyan]name[/] ([italic]any other keys will be ignored[/])

[bright_green].csv example[reset]:
------ csv ------
name\nsite1\nsite2\nsite3
-----------------
{common_add_delete_end}
"""

clibatch_add_labels = """
[italic cyan]cencli batch add labels IMPORT_FILE[/]:
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

clibatch_delete_groups = f"""
[italic cyan]cencli batch delete groups IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
If importing yaml or json the following fields can optionally be under a 'groups' key
[cyan]name[/] ([italic]any other keys will be ignored[/])

[bright_green].csv example[reset]:
-------------- csv --------------
name\nphl-access\nsan-dc-tor\ncom-branches
---------------------------------
{common_add_delete_end}
"""

clibatch_delete_devices_help = """
[bright_green]Perform batch Delete operations using import data from file.[/]

[cyan]cencli delete sites <IMPORT_FILE>[/] and
[cyan]cencli delte groups <IMPORT_FILE>[/]
    Do what you'd expect.

[cyan]cencli batch delete devices <IMPORT_FILE>[/]

    Delete devices will remove any subscriptions/licenses from the device and disassociate the device with the Aruba Central app in GreenLake.  It will then remove the device from the monitoring views, along with the historical data for the device.

    Note: devices can only be removed from monitoring views if they are in a down state.  This command will delay/wait for any Up devices to go Down after the subscriptions/assignment to Central is removed, but it can also be ran again.  It will pick up where it left off, skipping any steps that have already been performed.
"""

_site_common = """
[cyan]Provide geo-loc or address details, (Google Maps "Plus Codes" are supported) not both.
Can provide both in subsequent calls, but api does not allow both in same call.[reset]
"""

cliupdate_site_help = f"""
[bright_green]Update details for an existing site.[/]

{_site_common}
"""

cliadd_site_help = f"""
[bright_green]Add a site.[/]

Use '[dark_olive_green2]cencli batch add sites <IMPORT_FILE>[/]' to add multiple sites.
{_site_common}
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

clibatch_subscribe = f"""
[italic cyan]cencli batch subscribe devices IMPORT_FILE[/]:
Requires the following keys (include as header row for csv import):
    If importing yaml or json the following fields can optionally be under a 'devices' key
    [italic]Other keys/columns are allowed, but will be ignored.

[cyan]serial[/],[cyan]license[/] (both are required)

{Example(data)}

NOTE: Most batch operations are designed so the same file can be used for multiple automations
      the fields not required for a particular automation will be ignored.
"""

clibatch_unsubscribe = """
[italic cyan]cencli batch unsubscribe IMPORT_FILE[/]:
Accepts the following keys (include as header row for csv import):
    If importing yaml or json the following fields can optionally be under a 'devices' key

[cyan]serial[/]

[italic]Other fields can be included, but only serial, is evaluated
any subscriptions associated with the serial will be removed.

[bright_green].csv example[reset]:
-------------------------- csv --------------------------
serial
CN12345678
CN12345679
CN12345680
---------------------------------------------------------

NOTE: Most batch operations are designed so the same file can be used for multiple automations
      the fields not required for a particular automation will be ignored.
"""

data="""Mac Address,Client Name
00:09:B0:75:65:D1,Integra
00:1B:4F:23:8A:3E,Avaya VoIP
3C:A8:2A:A6:07:0B,HP Thin Client"""

clibatch_add_macs = f"""
[italic cyan]cencli batch add macs IMPORT_FILE[/]:

Requires the following keys (include as header row for csv import):
[cyan]Mac Address[/]
Optional keys:
[cyan]Client Name[/]

{Example(data)}
"""

data="""Name,MPSK,Client Role,Status
wade@example.com,chant chemo domain lugged,admin_users,enabled
jerry@example.com,quick dumpster offset jack,dia,enabled
stephanie@example.com,random here words go,general_users,enabled"""

clibatch_add_mpsk = f"""
[italic cyan]cencli batch add mpsk IMPORT_FILE --ssid <SSID>[/]:

Requires the following keys (include as header row for csv import):
[cyan]Name[/],[cyan]Client Role[/],[cyan]Status[/]

:information:  MPSK will be randomly generated.
:information:  Roles must exist in Central.
:information:  [cyan]--ssid[/] Option is required when uploading Named MPSKs.


{Example(data)}
"""

def do_capture(text: str) -> str:
    con = Console()
    con.begin_capture()
    con.print(text)
    ret = con.end_capture()
    return ret


class ImportExamples:
    def __init__(self):
        self.add_devices = clibatch_add_devices
        self.add_sites = clibatch_add_sites
        self.add_groups = clibatch_add_groups
        self.add_labels = clibatch_add_labels
        self.add_macs = clibatch_add_macs
        self.add_mpsk = clibatch_add_mpsk
        self.delete_devices = clibatch_delete_devices
        self.delete_sites = clibatch_delete_sites
        self.delete_groups = clibatch_delete_groups
        self.delete_labels = clibatch_delete_labels
        self.add_site = cliadd_site_help
        self.deploy = clibatch_deploy
        self.subscribe = clibatch_subscribe
        self.unsubscribe = clibatch_unsubscribe
        self.archive = clibatch_unsubscribe.replace("unsubscribe", "archive")
        self.unarchive = clibatch_unsubscribe.replace("unsubscribe", "unarchive")
        self.move_devices = clibatch_move_devices

    def __getattr__(self, key: str):
        if key not in self.__dict__.keys():
            log.error(f"An attempt was made to get {key} attr from ImportExamples which is not defined.")
            return f":warning: [bright_red]Error[/] no str defined for [cyan]ImportExamples.{key}[/]"

class LongHelp:
    def __init__(self):
        self.batch_delete_devices = do_capture(clibatch_delete_devices_help)
        self.update_site = do_capture(cliupdate_site_help)
        self.add_site = do_capture(cliadd_site_help)

    # FIXME this is a recurssion error
    def __getattr__(self, key: str):
        if not hasattr(self, key):
            log.error(f"An attempt was made to get {key} attr from ImportExamples which is not defined.")
            return f":warning: Error no str defined  ImportExamples.{key}"
        else:  # FIXME This doesn't seem to hit changed to using do_capture at init
            con = Console()
            attr = getattr(self, key)
            con.begin_capture()
            con.print(attr)
            ret = con.end_capture()
            return ret
