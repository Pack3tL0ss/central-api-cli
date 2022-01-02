# `cencli`

Aruba Central API CLI
  > This is the CLI reference in an alternate format.  Note it may not be as up to date as the primary [CLI Reference Guide](https://central-api-cli.readthedocs.io/en/latest/#cli-reference).

**Usage**:

```console
$ cencli [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--install-completion`: Install completion for the current shell.
* `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
* `--help`: Show this message and exit.

**Commands**:

* `add`: Add devices / objects.
* `batch`: Perform batch operations.
* `blink`: Blink LED
* `bounce`: Bounce Interface or PoE on Interface
* `caas`: Interact with Aruba Central CAAS API
* `clone`: Clone Aruba Central Groups
* `delete`: Delete Aruba Central Objects.
* `kick`: Disconnect a client
* `method-test`: dev testing commands to run CentralApi...
* `move`: Move device(s) to a defined group and/or site
* `nuke`: Factory Default A Device
* `reboot`: Reboot a device
* `refresh`: refresh <'token'|'cache'>
* `remove`: Remove a device from a site.
* `rename`: Rename an Access Point.
* `save`: Save Device Running Config to Startup
* `show`: Show Details about Aruba Central Objects
* `sync`: Sync/Refresh device config with Aruba Central
* `update`: Update existing Aruba Central objects.
* `upgrade`: Upgrade Firmware

## `cencli add`

Add devices / objects.

**Usage**:

```console
$ cencli add [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `device`: Add a Device to Aruba Central.
* `group`: Add a group
* `wlan`: Add WLAN (SSID)

### `cencli add device`

**Usage**:

```console
$ cencli add device [OPTIONS]  serial [SERIAL NUM]  mac [MAC ADDRESS] [KW3] group [GROUP]
```

**Arguments**:

* `serial [SERIAL NUM]`: [required]
* `mac [MAC ADDRESS]`: [required]
* `group [GROUP]`: pre-assign device to group

**Options**:

* `--license [advance-70xx|advance-72xx|advance-90xx-sec|advance-base-7005|advanced-ap|advanced-switch-6100|advanced-switch-6200|advanced-switch-6300|advanced-switch-6400|dm|foundation-70xx|foundation-72xx|foundation-90xx-sec|foundation-ap|foundation-base-7005|foundation-base-90xx-sec|foundation-switch-6100|foundation-switch-6200|foundation-switch-6300|foundation-switch-6400|foundation-wlan-gw|vgw2g|vgw4g|vgw500m]`: Assign license subscription(s) to device
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli add group`

Add a group

**Usage**:

```console
$ cencli add group [OPTIONS] [GROUP NAME]
```

**Arguments**:

* `[GROUP NAME]`: [required]

**Options**:

* `--wired-tg`: Manage switch configurations via templates  [default: False]
* `--wlan-tg`: Manage AP configurations via templates  [default: False]
* `--gw-role [branch|vpnc|wlan]`
* `--aos10`: Create AOS10 Group (default Instant)
* `--mb`: Configure Group for MicroBranch APs (AOS10 only)
* `--ap`: Allow APs in group
* `--sw`: Allow ArubaOS-SW switches in group.
* `--cx`: Allow ArubaOS-CX switches in group.
* `--gw`: Allow gateways in group.
* `--mon-only-sw`: Monitor Only for ArubaOS-SW  [default: False]
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli add wlan`

**Usage**:

```console
$ cencli add wlan [OPTIONS] [GROUP NAME|SWARM ID] NAME psk [WPA PASSPHRASE] type ['employee'|'guest'] vlan [VLAN] zone [ZONE] ssid [SSID] bw-limit-up [LIMIT] bw-limit-down [LIMIT] bw-limit-user-up [LIMIT] bw-limit-user-down [LIMIT] portal-profile [PORTAL PROFILE]
```

**Arguments**:

* `[GROUP NAME|SWARM ID]`: [required]
* `NAME`: [required]
* `psk [WPA PASSPHRASE]`: [default: psk, None]
* `type ['employee'|'guest']`: [default: type, employee]
* `vlan [VLAN]`: [default: vlan, ]
* `zone [ZONE]`: [default: zone, ]
* `ssid [SSID]`: [default: ssid, None]
* `bw-limit-up [LIMIT]`: [default: bw_limit_up, ]
* `bw-limit-down [LIMIT]`: [default: bw_limit_down, ]
* `bw-limit-user-up [LIMIT]`: [default: bw_limit_user_up, ]
* `bw-limit-user-down [LIMIT]`: [default: bw_limit_user_down, ]
* `portal-profile [PORTAL PROFILE]`: [default: portal_profile, ]

**Options**:

* `--hidden`: Make WLAN hidden  [default: False]
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account  [default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli batch`

Perform batch operations.

**Usage**:

```console
$ cencli batch [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `add`: Perform batch Add operations using import...
* `delete`: Perform batch Delete operations using import...
* `rename`: Perform AP rename in batch from import file...

### `cencli batch add`

Perform batch Add operations using import data from file.

**Usage**:

```console
$ cencli batch add [OPTIONS] WHAT:[sites|aps] IMPORT_FILE
```

**Arguments**:

* `WHAT:[sites|aps]`: [required]
* `IMPORT_FILE`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli batch delete`

Perform batch Delete operations using import data from file.

**Usage**:

```console
$ cencli batch delete [OPTIONS] WHAT:[sites] IMPORT_FILE
```

**Arguments**:

* `WHAT:[sites]`: [required]
* `IMPORT_FILE`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli batch rename`

Perform AP rename in batch from import file or automatically based on LLDP

**Usage**:

```console
$ cencli batch rename [OPTIONS] WHAT:[sites|aps] ['lldp'|IMPORT FILE PATH]
```

**Arguments**:

* `WHAT:[sites|aps]`: [required]
* `['lldp'|IMPORT FILE PATH]`

**Options**:

* `--lldp / --no-lldp`: Automatic AP rename based on lldp info from upstream switch.
* `--ap [name|ip|mac|serial]`: [LLDP rename] Perform on specified AP
* `--label TEXT`: [LLDP rename] Perform on APs with specified label
* `--group TEXT`: [LLDP rename] Perform on APs in specified group
* `--site [name|site_id|address|city|state|zip]`: [LLDP rename] Perform on APs in specified site
* `--model TEXT`: [LLDP rename] Perform on APs of specified model
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli blink`

**Usage**:

```console
$ cencli blink [OPTIONS] [name|ip|mac|serial] ACTION:[on|off] SECONDS
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]
* `ACTION:[on|off]`: [required]
* `SECONDS`: Blink for _ seconds.

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli bounce`

**Usage**:

```console
$ cencli bounce [OPTIONS] WHAT:[poe|interface] [name|ip|mac|serial] PORT
```

**Arguments**:

* `WHAT:[poe|interface]`: [required]
* `[name|ip|mac|serial]`: [required]
* `PORT`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli caas`

Interact with Aruba Central CAAS API

**Usage**:

```console
$ cencli caas [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `add-vlan`
* `batch`: Run Supported caas commands providing parameters via stored-tasks file
* `bulk-edit`: Import Apply settings from bulk-edit.csv
* `import-vlan`: import VLAN from Stored Tasks File

### `cencli caas add-vlan`

**Usage**:

```console
$ cencli caas add-vlan [OPTIONS] GROUP_DEV PVID [IP] [MASK]
```

**Arguments**:

* `GROUP_DEV`: [required]
* `PVID`: [required]
* `[IP]`
* `[MASK]`: [default: 255.255.255.0]

**Options**:

* `--name TEXT`
* `--description TEXT`
* `--interface TEXT`
* `--vrid TEXT`
* `--vrrp-ip TEXT`
* `--vrrp-pri INTEGER`
* `-d`: Use default central account  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli caas batch`

cencli caas batch add-vlan add-vlan-99

**Usage**:

```console
$ cencli caas batch [OPTIONS] [KEY]
```

**Arguments**:

* `[KEY]`

**Options**:

* `--file PATH`: [default: /home/wade/.config/centralcli/stored-tasks.yaml]
* `--command TEXT`
* `-d`: Use default central account  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli caas bulk-edit`

**Usage**:

```console
$ cencli caas bulk-edit [OPTIONS] [INPUT_FILE]
```

**Arguments**:

* `[INPUT_FILE]`: [default: /home/wade/.config/centralcli/bulkedit.csv]

**Options**:

* `-d`: Use default central account  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli caas import-vlan`

Add VLAN from stored_tasks file.

This is the same as `cencli batch add-vlan key`, but command: add_vlan
is implied only need to provide key

**Usage**:

```console
$ cencli caas import-vlan [OPTIONS] KEY [IMPORT_FILE]
```

**Arguments**:

* `KEY`: The Key from stored_tasks with vlan details to import  [required]
* `[IMPORT_FILE]`

**Options**:

* `--file PATH`
* `-d`: Use default central account  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli clone`

Clone Aruba Central Groups

**Usage**:

```console
$ cencli clone [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `group`: Clone a group

### `cencli clone group`

**Usage**:

```console
$ cencli clone group [OPTIONS] [NAME OF GROUP TO CLONE] [NAME OF GROUP TO CREATE]
```

**Arguments**:

* `[NAME OF GROUP TO CLONE]`: [required]
* `[NAME OF GROUP TO CREATE]`: [required]

**Options**:

* `--aos10`: Upgrade new cloned group to AOS10
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli delete`

Delete Aruba Central Objects.

**Usage**:

```console
$ cencli delete [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `certificate`: Delete a certificate
* `firmware`: Delete/Clear firmware compliance
* `group`: Delete group(s)
* `site`: Delete a site
* `wlan`: Delete a WLAN (SSID)

### `cencli delete certificate`

**Usage**:

```console
$ cencli delete certificate [OPTIONS] NAME
```

**Arguments**:

* `NAME`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli delete firmware`

**Usage**:

```console
$ cencli delete firmware [OPTIONS] WHAT:[compliance] [ap|gw|switch] [GROUP-NAME]
```

**Arguments**:

* `WHAT:[compliance]`: [required]
* `[ap|gw|switch]`: [required]
* `[GROUP-NAME]`

**Options**:

* `--group TEXT`: Filter by group
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli delete group`

**Usage**:

```console
$ cencli delete group [OPTIONS] GROUPS...
```

**Arguments**:

* `GROUPS...`: Group to delete (can provide more than one).  [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli delete site`

**Usage**:

```console
$ cencli delete site [OPTIONS] SITES...
```

**Arguments**:

* `SITES...`: Site(s) to delete (can provide more than one).  [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli delete wlan`

**Usage**:

```console
$ cencli delete wlan [OPTIONS] [GROUP NAME|SWARM ID] [WLAN NAME]
```

**Arguments**:

* `[GROUP NAME|SWARM ID]`: [required]
* `[WLAN NAME]`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli kick`

Disconnect a client.

**Usage**:

```console
$ cencli kick [OPTIONS] CONNECTED_DEVICE[name|ip|mac|serial] WHAT:[all|mac|wlan] [WHO]
```

**Arguments**:

* `CONNECTED_DEVICE[name|ip|mac|serial]`: [required]
* `WHAT:[all|mac|wlan]`: [required]
* `[WHO]`: [<mac>|<wlan/ssid>]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli method-test`

dev testing commands to run CentralApi methods from command line

Args:
    method (str, optional): CentralAPI method to test.
    kwargs (List[str], optional): list of args kwargs to pass to function.

format: arg1 arg2 keyword=value keyword2=value
    or  arg1, arg2, keyword = value, keyword2=value

Displays all attributes of Response object

**Usage**:

```console
$ cencli method-test [OPTIONS] METHOD [KWARGS]...
```

**Arguments**:

* `METHOD`: [required]
* `[KWARGS]...`

**Options**:

* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in Table
* `--outfile PATH`: Output to file (and terminal)
* `--pager`: Enable Paged Output  [default: True]
* `-d`: Use default central account
* `--debug`: Enable Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

Output is displayed in yaml by default.

## `cencli move`

Move device(s) to a defined group and/or site.

**Usage**:

```console
$ cencli move [OPTIONS] [[name|ip|mac|serial] ...]  [site <SITE>]  [group <GROUP>]
```

**Arguments**:

* `[[name|ip|mac|serial] ...]`
* `[site <SITE>]`
* `[group <GROUP>]`: [site and/or group required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli nuke`

**Usage**:

```console
$ cencli nuke [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli reboot`

**Usage**:

```console
$ cencli reboot [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli refresh`

refresh <'token'|'cache'>

**Usage**:

```console
$ cencli refresh [OPTIONS] WHAT:[cache|token|tokens]
```

**Arguments**:

* `WHAT:[cache|token|tokens]`: [required]

**Options**:

* `-d`: Use default central account
* `--debug`: Enable Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli remove`

Remove a device from a site.

**Usage**:

```console
$ cencli remove [OPTIONS] [name|ip|mac|serial] ... (multiple allowed) [site <SITE>]
```

**Arguments**:

* `[name|ip|mac|serial] ... (multiple allowed)`: [required]
* `[site <SITE>]`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli rename`

Rename an Access Point

**Usage**:

```console
$ cencli rename [OPTIONS] WHAT:[group|ap] AP[name|ip|mac|serial] NEW_NAME
```

**Arguments**:

* `WHAT:[group|ap]`: [required]
* `AP[name|ip|mac|serial]`: [required]
* `NEW_NAME`: [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli save`

**Usage**:

```console
$ cencli save [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli show`

Show Details about Aruba Central Objects

**Usage**:

```console
$ cencli show [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `all`: Show All Devices
* `aps`: Show APs/details
* `cache`: Show contents of Identifier Cache.
* `certs`: Show certificates/details
* `clients`: Show clients/details
* `config`: Show Effective Group/Device Config
* `controllers`: Show controllers/details
* `devices`: Show devices [identifier]
* `dhcp`: Show DHCP pool or lease details (gateways only)
* `events`: Show Event Logs (last 4 hours by default)
* `firmware`: Show Firmware / compliance details
* `gateways`: Show gateways/details
* `groups`: Show groups/details
* `interfaces`: Show interfaces/details
* `lldp`: Show AP lldp neighbor
* `logs`: Show Event Logs (2 days by default)
* `routes`: Show device routing table
* `run`: Show last known running config for a device
* `sites`: Show sites/details
* `switches`: Show switches/details
* `templates`: Show templates/details
* `upgrade`: Show firmware upgrade status
* `variables`: Show Variables for all or specific device
* `vlans`: Show VLANs for device or site
* `wids`: Show Firmware / compliance details
* `wlans`: Show WLAN(SSID)/details

### `cencli show all`

**Usage**:

```console
$ cencli show all [OPTIONS]
```

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--stats`: Show device statistics  [default: False]
* `--sort [name|model|ip|mac|serial|group|site|status|type|labels|version]`
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show aps`

**Usage**:

```console
$ cencli show aps [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--status [up|down]`: Filter by device status
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--stats`: Show device statistics  [default: False]
* `--clients`: Calculate client count (per device)  [default: False]
* `--sort [+name|-name|+mac|-mac|+serial|-serial]`
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show cache`

**Usage**:

```console
$ cencli show cache [OPTIONS] [ARGS]:[devices|sites|templates|groups|logs|events]...
```

**Arguments**:

* `[ARGS]:[devices|sites|templates|groups|logs|events]...`

**Options**:

* `--json`: Output in JSON
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show certs`

**Usage**:

```console
$ cencli show certs [OPTIONS] [certificate name|certificate hash]
```

**Arguments**:

* `[certificate name|certificate hash]`

**Options**:

* `-r`: Reverse output order
* `--sort [name|type|expiration|expired|md5_checksum|sha1_checksum]`
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show clients`

**Usage**:

```console
$ cencli show clients [OPTIONS] [FILTER]:[wired|wireless|all|mac|device] [name|ip|mac|serial]
```

**Arguments**:

* `[FILTER]:[wired|wireless|all|mac|device]`: [default: all]
* `[name|ip|mac|serial]`: Show clients for a specific device or multiple devices.

**Options**:

* `--group <Group>`: Filter by Group
* `--site <Site>`: Filter by Site
* `--label <Label>`: Filter by Label
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--sort [name|mac|vlan|ip|role|network|dot11|connected_device|site|group|last_connected]`
* `-r`: Reverse output order
* `-v`: additional details (vertically)
* `-vv`: Show raw response (no formatting but still honors --yaml, --csv ... if provided)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show config`

Show Effective Group/Device Config (UI Group)

**Usage**:

```console
$ cencli show config [OPTIONS] [GROUP NAME|name|ip|mac|serial] [DEVICE]
```

**Arguments**:

* `[GROUP NAME|name|ip|mac|serial]`: [required]
* `[DEVICE]`

**Options**:

* `--gw`: Show group level config for gateways.
* `--ap`: Show group level config for APs.
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show controllers`

**Usage**:

```console
$ cencli show controllers [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--stats`: Show device statistics  [default: False]
* `--clients`: Calculate client count (per device)  [default: False]
* `--sort [name|model|ip|mac|serial|group|site|status|type|labels|version]`
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show devices`

**Usage**:

```console
$ cencli show devices [OPTIONS] [name|ip|mac|serial|'all']
```

**Arguments**:

* `[name|ip|mac|serial|'all']`: Show details for a specific device [Default: show summary for all devices]

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--stats`: Show device statistics  [default: False]
* `--clients`: Calculate client count (per device)  [default: False]
* `--sort [name|model|ip|mac|serial|group|site|status|type|labels|version]`
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show dhcp`

**Usage**:

```console
$ cencli show dhcp [OPTIONS] WHAT:[clients|server] [name|ip|mac|serial] (Valid for Gateways Only)
```

**Arguments**:

* `WHAT:[clients|server]`: ['server', 'clients']  [required]
* `[name|ip|mac|serial] (Valid for Gateways Only) `: [required]

**Options**:

* `--no-res`: Filter out reservations  [default: False]
* `--sort TEXT`: Field to sort by
* `-r`: Reverse sort order
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `-vv`: Show raw response (no formatting) (vertically)
* `--help`: Show this message and exit.

### `cencli show events`

Show event logs


**Usage**:

```console
$ cencli show events [OPTIONS] [LOG_ID]
```

**Arguments**:

* `[LOG_ID]`: Show details for a specific log_id

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--site [name|site_id|address|city|state|zip]`: Filter by Site
* `--start TEXT`: Start time of range to collect events, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect events, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect events for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--device [name|ip|mac|serial]`: Filter events by device
* `--client-mac TEXT`: Filter events by client MAC address
* `--bssid TEXT`: Filter events by bssid
* `--hostname TEXT`: Filter events by hostname (fuzzy match)
* `--dev-type [ap|switch|gw|client]`: Filter events by device type
* `--description TEXT`: Filter events by description (fuzzy match)
* `--event-type TEXT`: Filter events by type (fuzzy match)
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--sort TEXT`
* `-r`: Reverse Output order Default order: newest on bottom.
* `-v`: Show logs with original field names and minimal formatting (vertically)  [default: False]
* `-vv`: Show raw unformatted response from Central API Gateway  [default: False]
* `--no-pager`: Disable Paged Output  [default: False]
* `--out PATH`: Output to file (and terminal)
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show firmware`

Show Firmware / compliance details

**Usage**:

```console
$ cencli show firmware [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `compliance`: Show firmware compliance details

#### `cencli show firmware compliance`

**Usage**:

```console
$ cencli show firmware compliance [OPTIONS] [ap|gw|switch] [GROUP-NAME]
```

**Arguments**:

* `[ap|gw|switch]`: [required]
* `[GROUP-NAME]`

**Options**:

* `--group TEXT`: Filter by group
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show gateways`

**Usage**:

```console
$ cencli show gateways [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--stats`: Show device statistics  [default: False]
* `--clients`: Calculate client count (per device)  [default: False]
* `--sort [name|model|ip|mac|serial|group|site|status|type|labels|version]`
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show groups`

**Usage**:

```console
$ cencli show groups [OPTIONS]
```

**Options**:

* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-v`: Verbose: adds AoS10 / Monitor only switch attributes
* `-vv`: Show raw response (no formatting but still honors --yaml, --csv ... if provided)
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show interfaces`

**Usage**:

```console
$ cencli show interfaces [OPTIONS] [name|ip|mac|serial] [SLOT]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]
* `[SLOT]`: Slot name of the ports to query (chassis only)

**Options**:

* `--sort TEXT`: Field to sort by
* `-r`: Sort in descending order  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show lldp`

Show AP lldp neighbor.  Command only applies to APs at this time.

**Usage**:

```console
$ cencli show lldp [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show logs`

**Usage**:

```console
$ cencli show logs [OPTIONS] [LOG_ID]
```

**Arguments**:

* `[LOG_ID]`: Show details for a specific log_id

**Options**:

* `--user TEXT`: Filter logs by user
* `--start TEXT`: Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--device [name|ip|mac|serial]`: Filter logs by device
* `--ip TEXT`: Filter logs by device IP address
* `--description TEXT`: Filter logs by description (fuzzy match)
* `--class TEXT`: Filter logs by classification (fuzzy match)
* `-n INTEGER`: Collect Last n logs
* `--cencli`: Show cencli logs  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--sort [time|app|class|type|description|target|ip|user|id|has_details]`
* `-r`: Reverse Output order Default order: newest on bottom.
* `-v`: Show logs with original field names and minimal formatting (vertically)  [default: False]
* `-vv`: Show raw unformatted response from Central API Gateway  [default: False]
* `--no-pager`: Disable Paged Output  [default: False]
* `--out PATH`: Output to file (and terminal)
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show routes`

**Usage**:

```console
$ cencli show routes [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `-r`: Reverse output order
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show run`

**Usage**:

```console
$ cencli show run [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show sites`

**Usage**:

```console
$ cencli show sites [OPTIONS] [name|site_id|address|city|state|zip]
```

**Arguments**:

* `[name|site_id|address|city|state|zip]`

**Options**:

* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--sort [+name|-name|+mac|-mac|+serial|-serial]`
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show switches`

**Usage**:

```console
$ cencli show switches [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--status [up|down]`: Filter by device status
* `--up`: Filter by devices that are Up
* `--down`: Filter by devices that are Down
* `--pub-ip <Public IP Address>`: Filter by Public IP
* `--stats`: Show device statistics  [default: False]
* `--clients`: Calculate client count (per device)  [default: False]
* `--sort [+name|-name|+mac|-mac|+serial|-serial]`
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show templates`

**Usage**:

```console
$ cencli show templates [OPTIONS] [NAME] [GROUP]...
```

**Arguments**:

* `[NAME]`: Template: [name] or Device: [name|ip|mac|serial]
* `[GROUP]...`: Get Templates for Group

**Options**:

* `--group TEXT`: Get Templates for Group
* `--dev-type [ap|sw|cx|gw]`: Filter by Device Type
* `--version <version>`: [Templates] Filter by dev version Template is assigned to
* `--model <model>`: [Templates] Filter by model
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--sort [device_type|group|model|name|template_hash|version]`
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show upgrade`

**Usage**:

```console
$ cencli show upgrade [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show variables`

**Usage**:

```console
$ cencli show variables [OPTIONS] [name|ip|mac|serial|all]
```

**Arguments**:

* `[name|ip|mac|serial|all]`: Default: 'all'

**Options**:

* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show vlans`

**Usage**:

```console
$ cencli show vlans [OPTIONS] [name|ip|mac|serial] (vlans for a device) OR [name|site_id|address|city|state|zip] (vlans for a site)
```

**Arguments**:

* `[name|ip|mac|serial] (vlans for a device) OR [name|site_id|address|city|state|zip] (vlans for a site)`: [required]

**Options**:

* `--up`: Filter: Up VLANs
* `--down`: Filter: Down VLANs
* `--json`: Output in JSON
* `--yaml`: Output in YAML
* `--csv`: Output in CSV
* `--table`: Output in table format
* `--out PATH`: Output to file (and terminal)
* `--sort [name|pvid|untagged|tagged|status|mgmt|jumbo|voice|igmp|oper_state_reason]`
* `-r`: Reverse output order
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show wids`

Show Firmware / compliance details

**Usage**:

```console
$ cencli show wids [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `interfering`: Show interfering APs
* `neighbor`: Show Neighbor APs
* `rogues`: Show Detected Rogue APs
* `suspect`: Show Suspected Rogue APs

#### `cencli show wids interfering`

**Usage**:

```console
$ cencli show wids interfering [OPTIONS] [GROUP-NAME] [LABEL] [SITE-NAME]
```

**Arguments**:

* `[GROUP-NAME]`
* `[LABEL]`
* `[SITE-NAME]`

**Options**:

* `--start TEXT`: Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--sort TEXT`
* `-r`: Reverse Output order.
* `-v`: Show raw unformatted response (vertically)  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

#### `cencli show wids neighbor`

**Usage**:

```console
$ cencli show wids neighbor [OPTIONS] [GROUP-NAME] [LABEL] [SITE-NAME]
```

**Arguments**:

* `[GROUP-NAME]`
* `[LABEL]`
* `[SITE-NAME]`

**Options**:

* `--start TEXT`: Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--sort TEXT`
* `-r`: Reverse Output order.
* `-v`: Show raw unformatted response (vertically)  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

#### `cencli show wids rogues`

**Usage**:

```console
$ cencli show wids rogues [OPTIONS] [GROUP-NAME] [LABEL] [SITE-NAME]
```

**Arguments**:

* `[GROUP-NAME]`
* `[LABEL]`
* `[SITE-NAME]`

**Options**:

* `--start TEXT`: Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--sort TEXT`
* `-r`: Reverse Output order.
* `-v`: Show raw unformatted response (vertically)  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

#### `cencli show wids suspect`

**Usage**:

```console
$ cencli show wids suspect [OPTIONS] [GROUP-NAME] [LABEL] [SITE-NAME]
```

**Arguments**:

* `[GROUP-NAME]`
* `[LABEL]`
* `[SITE-NAME]`

**Options**:

* `--start TEXT`: Start time of range to collect logs, format: yyyy-mm-ddThh:mm (24 hour notation)
* `--end TEXT`: End time of range to collect logs, formnat: yyyy-mm-ddThh:mm (24 hour notation)
* `--past TEXT`: Collect Logs for last <past>, d=days, h=hours, m=mins i.e.: 3h
* `--sort TEXT`
* `-r`: Reverse Output order.
* `-v`: Show raw unformatted response (vertically)  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli show wlans`

**Usage**:

```console
$ cencli show wlans [OPTIONS] [WLAN NAME]
```

**Arguments**:

* `[WLAN NAME]`: Get Details for a specific WLAN

**Options**:

* `--group <Device Group>`: Filter by Group
* `--label <Device Label>`: Filter by Label
* `--site [site identifier]`: Filter by device status
* `--swarm-id TEXT`
* `--clients`: Calculate client count (per SSID)  [default: False]
* `--json`: Output in JSON  [default: False]
* `--yaml`: Output in YAML  [default: False]
* `--csv`: Output in CSV  [default: False]
* `--table`: Output in table format  [default: False]
* `--out PATH`: Output to file (and terminal)
* `--no-pager`: Disable Paged Output  [default: False]
* `-d`: Use default central account
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli sync`

**Usage**:

```console
$ cencli sync [OPTIONS] [name|ip|mac|serial]
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]

**Options**:

* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli update`

Update existing Aruba Central objects.

**Usage**:

```console
$ cencli update [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `ap-config`: Replace AP configuration
* `group`: Update group properties
* `group-new`: Update group properties.
* `template`: Update an existing template
* `variables`: Update existing or add new Variables for a device/template

### `cencli update ap-config`

Update/Replace AP configuration by group or AP

**Usage**:

```console
$ cencli update ap-config [OPTIONS] GROUP_DEV CLI_FILE
```

**Arguments**:

* `GROUP_DEV`: [required]
* `CLI_FILE`: File containing desired config in CLI format.  [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli update group`

Update group properties (AOS8 vs AOS10 & Monitor Only Switch enabled/disabled)

**Usage**:

```console
$ cencli update group [OPTIONS] GROUP_NAME [10]
```

**Arguments**:

* `GROUP_NAME`: [required]
* `[10]`: Set to 10 to Upgrade group to AOS 10

**Options**:

* `--mos / --no-mos`: Enable monitor only for switches in the group
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli update group-new`

Update group properties.

**Usage**:

```console
$ cencli update group-new [OPTIONS] [GROUP NAME]
```

**Arguments**:

* `[GROUP NAME]`: [required]

**Options**:

* `--wired-tg / --no-wired-tg`: Manage switch configurations via templates
* `--wlan-tg / --no-wlan-tg`: Manage AP configurations via templates
* `--gw-role [branch|vpnc|wlan]`
* `--aos10`: Create AOS10 Group (default Instant)
* `--mb / --no-mb`: Configure Group for MicroBranch APs (AOS10 only
* `--ap / --no-ap`: Allow APs in group
* `--sw / --no-sw`: Allow ArubaOS-SW switches in group.
* `--cx / --no-cx`: Allow ArubaOS-CX switches in group.
* `--gw / --no-gw`: Allow gateways in group.
                                  If No device types specified all are allowed.
* `--mon-only-sw / --no-mon-only-sw`: Monitor Only for ArubaOS-SW
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli update template`

**Usage**:

```console
$ cencli update template [OPTIONS] NAME [TEMPLATE]
```

**Arguments**:

* `NAME`: Template: [name] or Device: [name|ip|mac|serial]  [required]
* `[TEMPLATE]`: Path to file containing new template

**Options**:

* `--group TEXT`: The template group the template belongs to
* `--dev-type [ap|sw|cx|gw]`: Filter by Device Type
* `--version <version>`: [Templates] Filter by version
* `--model <model>`: [Templates] Filter by model
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli update variables`

**Usage**:

```console
$ cencli update variables [OPTIONS] [name|ip|mac|serial] VAR_VALUE...
```

**Arguments**:

* `[name|ip|mac|serial]`: [required]
* `VAR_VALUE...`: comma seperated list 'variable = value, variable2 = value2'  [required]

**Options**:

* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

## `cencli upgrade`

Upgrade Firmware

**Usage**:

```console
$ cencli upgrade [OPTIONS] COMMAND [ARGS]...
```

**Options**:

* `--help`: Show this message and exit.

**Commands**:

* `device`: Upgrade firmware on a specific device
* `group`: Upgrade firmware by group
* `swarm`: Upgrade firmware for an IAP cluster

### `cencli upgrade device`

**Usage**:

```console
$ cencli upgrade device [OPTIONS] Device: [serial #|name|ip address|mac address] [VERSION]
```

**Arguments**:

* `Device: [serial #|name|ip address|mac address]`: [required]
* `[VERSION]`: Version to upgrade to [Default: recommended version]

**Options**:

* `--at [%m/%d/%Y_%H:%M|%d_%H:%M]`: When to schedule upgrade. format: 'mm/dd/yyyy_hh:mm' or 'dd_hh:mm' (implies current month) [Default: Now]
* `-R`: Automatically reboot device after firmware download  [default: False]
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli upgrade group`

**Usage**:

```console
$ cencli upgrade group [OPTIONS] [GROUP NAME] [VERSION]
```

**Arguments**:

* `[GROUP NAME]`: Upgrade devices by group  [required]
* `[VERSION]`: Version to upgrade to [Default: recommended version]

**Options**:

* `--at [%m/%d/%Y %H:%M|%d %H:%M]`: When to schedule upgrade. format: 'mm/dd/yyyy hh:mm' or 'dd hh:mm' (implies current month) [Default: Now]
* `--dev-type [ap|sw|cx|gw|switch]`: Upgrade a specific device type
* `--model TEXT`: [applies to switches only] Upgrade a specific switch model
* `-R`: Automatically reboot device after firmware download  [default: False]
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.

### `cencli upgrade swarm`

**Usage**:

```console
$ cencli upgrade swarm [OPTIONS] [IAP VC NAME|IAP SWARM ID|AP NAME|AP SERIAL|AP MAC] [VERSION]
```

**Arguments**:

* `[IAP VC NAME|IAP SWARM ID|AP NAME|AP SERIAL|AP MAC]`: Upgrade firmware on an IAP cluster.  For AP name,serial,mac it will upgrade the cluster that AP belongs to.
* `[VERSION]`: Version to upgrade to

**Options**:

* `--at [%m/%d/%Y %H:%M|%d %H:%M]`: When to schedule upgrade. format: 'mm/dd/yyyy hh:mm' or 'dd hh:mm' (implies current month) [Default: Now]
* `-R`: Automatically reboot device after firmware download  [default: False]
* `-Y`: Bypass confirmation prompts - Assume Yes  [default: False]
* `--debug`: Enable Additional Debug Logging  [env var: ARUBACLI_DEBUG; default: False]
* `-d`: Use default central account
* `--account TEXT`: The Aruba Central Account to use (must be defined in the config)  [env var: ARUBACLI_ACCOUNT; default: central_info]
* `--help`: Show this message and exit.
