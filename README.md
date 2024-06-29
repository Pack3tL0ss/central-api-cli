# Aruba Central API CLI

[![Latest Version](https://img.shields.io/pypi/v/centralcli.svg)](https://pypi.org/project/centralcli)
[![Documentation Status](https://readthedocs.org/projects/central-api-cli/badge/?version=latest)](https://central-api-cli.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://static.pepy.tech/badge/centralcli)](https://pepy.tech/project/centralcli)
[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://lbesson.mit-license.org/)

A CLI app for interacting with Aruba Central Cloud Management Platform. With cross-platform shell support. Auto Completion, easy device/site/group/template identification (fuzzy match), support for batch import, and a lot more.

  > As commands are built out the CLI hierarchy may evolve.  Refer to the [documentation](https://central-api-cli.readthedocs.org) or help text for CLI structure/syntax.

![centralcli Animated Demo](https://raw.githubusercontent.com/Pack3tL0ss/central-api-cli/master/docs/img/cencli-demo.gif)

## Features

- Cross Platform Support
- Auto/TAB Completion
- Specify device, site, etc. by fuzzy match of multiple fields (i.e. name, mac, serial#, ip address)
- Multiple output formats
- Output to file
- Numerous import formats (csv, yaml, json, xls, etc.)
- Multiple account support (easily switch between different central accounts `--account myotheraccount`)
- Batch Operation based on data from input file.  i.e. Add sites in batch based on data from a csv.
- Automatic Token refresh.  With prompt to paste in a new token if it becomes invalid.
  > If using Tokens, dedicate the token to the CLI alone, using it in swagger or on another system, will eventually lead to a refresh that invalidates the tokens on the other systems using it.
- You can also use username/Password Auth. which will facilitate automatic retrieval of new Tokens even if they do become invalid.

## Installation

Requires python 3.7+ and pip

`pip3 install centralcli`

> You can also install in a virtual environment (venv), but you'll lose auto-completion, unless you activate the venv.

### Upgrading the CLI

`pip3 install -U centralcli`

### if you don't have python

- You can get it for any platform @ [https://www.python.org](https://www.python.org)
- On Windows 10 it's also available in the Windows store.

## Configuration

Refer to [config.yaml.example](https://github.com/Pack3tL0ss/central-api-cli/blob/master/config/config.yaml.example) to guide in the creation of config.yaml and place in the config directory.

CentralCli will look in \<Users home dir\>/.config/centralcli, and \<Users home dir\>\\.centralcli.
i.e. on Windows `c:\Users\wade\.centralcli` or on Linux `/home/wade/.config/centralcli`

Once `config.yaml` is populated per [config.yaml.example](https://github.com/Pack3tL0ss/central-api-cli/blob/master/config/config.yaml.example), run some test commands to validate the config.

For Example `cencli show all`

```bash
wade@wellswa6:~ $ cencli show all
                                                                                       All Devices
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  name                  type   model                            ip                mac                 serial       group          site             labels        version       status
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  6100F-48-LAB          cx     6100 48G CL4 4SFP+ Swch          10.0.40.11        --redacted--   --redacted--    WadeLab8x                                     10.08.1010       Down
                               (JL675A)
  SDBranch1:7008        gw     A7008                            192.168.240.101   --redacted--   --redacted--    Branch1        Antigua          Branch View   10.3.0.0_82528   Up
  br1-2930F-sw          sw     Aruba2930F-8G-PoE+-2SFP+         10.101.5.4        --redacted--   --redacted--    Branch1        Antigua          Branch View   16.11.0002       Up
                               Switch(JL258A)
  br1-315.0c88-ap       ap     315                              10.101.6.200      --redacted--   --redacted--    Branch1        Antigua          Branch View   10.3.0.0_82528   Up
  MB1-505h              ap     505H                             10.10.1.101       --redacted--   --redacted--    MicroBranch1   Champions Hill                 10.3.0.0_82528   Up
  6200F-Bot             cx     6200F 48G CL4 4SFP+740W Swch     10.0.40.16        --redacted--   --redacted--    WadeLab8x      Pommore                        10.08.1010       Down
                               (JL728A)
  6200F-Top             cx     6200F 48G CL4 4SFP+740W Swch     10.0.40.6         --redacted--   --redacted--    WadeLab8x      Pommore                        10.08.1010       Down
                               (JL728A)
  APGW1                 gw     A9004-LTE                        10.0.35.10        --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82528   Up
  APGW2                 gw     A9004                            10.0.35.20        --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82528   Up
  VPNC1                 gw     A7005                            172.30.0.242      --redacted--   --redacted--    VPNC           WadeLab          Branch View   10.3.0.0_82528   Up
  VPNC2                 gw     A7005                            172.30.0.243      --redacted--   --redacted--    VPNC           WadeLab          Branch View   10.3.0.0_82528   Up
  av-555.11b8-ap        ap     555                              10.0.31.155       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
  barn-303p.2c30-ap     ap     303P                             10.1.30.151       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82528   Up
  barn-4100i            cx     4100i 12G CL4/6 POE 2SFP+ DIN    10.1.30.152       --redacted--   --redacted--    WadeLab        WadeLab                        10.08.1010       Up
                               Sw (JL817A)
  barn-518.2816-ap      ap     518                              10.1.30.101       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82528   Up
  bsmt-515.51s9-ap      ap     515                              10.0.30.233       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
  craft-2930F           sw     Aruba2930F-8G-PoE+-2SFP+         10.0.30.5         --redacted--   --redacted--    WadeLab        WadeLab                        16.11.0002       Up
                               Switch(JL258A)
  garage-345.5136-ap    ap     345                              10.0.31.148       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
  ktcn-505H.206c-ap     ap     505H                             10.0.30.212       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
  lwrptio-575.0824-ap   ap     575                              10.0.30.219       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
  zrm-535.70be-ap       ap     535                              10.0.31.101       --redacted--   --redacted--    WLNET          WadeLab                        10.3.0.0_82463   Down
 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Show all displays fields common to all device types. To see all columns for a given device type use show <DEVICE TYPE>
  API Rate Limit: 925 of 1000 remaining.

```

Use `cencli ?` to become familiar with the command options.

### Auto Completion

The CLI supports auto-completion.  To configure auto-completion run `cencli --install-completion`.  This will auto-detect the type of shell you are running in, and install the necessary completion into your profile.  You'll need to exit the shell and start a new session for it to take effect.
> Note for OSX 11: Additional step, edit .zshrc and add "autoload -Uz compinit && compinit -i" then exit and start new session.

## Usage Notes

### Caching & Friendly identifiers

- Caching: The CLI caches information on all devices, sites, groups, and templates in Central.  It's a minimal amount per device, and is done to allow human friendly identifiers.  The API typically accepts serial #, site id, etc.  This function allows you to specify a device by name, IP, mac (any format), and serial.

The lookup sequence for a device:

  1. Exact Match of any of the identifier fields (name, ip, mac, serial)
  2. case insensitive match
  3. case insensitive match disregarding all hyphens and underscores (in case you type 6200f_bot and the device name is 6200F-Bot)
  4. Case insensitive Fuzzy match with implied wild-card, otherwise match any devices that start with the identifier provided. `cencli show switches 6200F` will result in a match of `6200F-Bot`.

> If there is no match found, a cache update is triggered, and the match rules are re-tried.

- Caching works in a similar manner for groups, templates, and sites.  Sites can match on name and nearly any address field.  So if you only had one site in San Antonio you could specify that site with `show sites 'San Antonio'`  \<-- Note the use of quotes because there is a space in the name.

- **Multiple Matches**:  It's possible to specify an identifier that returns multiple matches (if drops all the way down to the Fuzzy match/implied trailing wild-card).  If that occurs you are prompted to select the intended device from a list of the matches.

### Output Formats

There are a number of output formats available.  Most commands default to what is likely the easiest to view given the number of fields.  Otherwise longer outputs are typically displayed vertically by default.  If the output can reasonably fit, it's displayed in tabular format horizontally.

You can specify the output format with command line flags `--json`, `--yaml`, `--csv`, `--table`  rich is tabular format with folding (multi line within the same row) and truncating.

> Most outputs will evolve to support an output with the most commonly desired fields by default and expanded vertical output via the `-v` option (not implemented yet.).  Currently the output is tabular horizontally if the amount of data is likely to fit most displays, and vertical otherwise.

### File Output

Just use `--out \<filename\>` (or \<path\\filename\>), and specify the desired format.

## CLI Tree

Use `?` or `--help` from the cli, which you can do at any level.  `ccenli ?`, `cencli bounce --help` etc.

You can also see the entire supported tree via the [CLI Reference Guide](https://central-api-cli.readthedocs.io/en/latest/cli.html).
*NOTE: The Reference Guide documents a few commands that are hidden in the CLI*
