#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich.console import Console
from centralcli import log

# TODO typer now supports markup_mode="rich" Don't need the help below, can just put the markup in the docstr

# [italic]Also supports a simple list of serial numbers with no header 1 per line.[reset]  # TODO implement this device del
# TODO document examples and uncomment below.  provide examples for all format/types
# print("See https://central-api-cli.readthedocs.io for full examples.


# TODO build examples for json yaml a master import for all make example the same for add and delete
# (noting that delete only requires 1 field)
# provide estimate on number of API calls.

# TODO pass examples through lexer

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

clibatch_delete_devices_help = f"""
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

clibatch_deploy = f"""
[bright_green]Batch Deploy[/]

This is a placeholder
TODO add deploy example
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
        self.delete_devices = clibatch_delete_devices
        self.delete_sites = clibatch_delete_sites
        self.delete_groups = clibatch_delete_groups
        self.add_site = cliadd_site_help
        self.deploy = clibatch_deploy

    def __getattr__(self, key: str):
        if not hasattr(self, key):
            log.error(f"An attempt was made to get {key} attr from ImportExamples which is not defined.")
            return f":warning: Error no str defined  ImportExamples.{key}"

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
