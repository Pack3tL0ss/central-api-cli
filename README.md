# Aruba Central API CLI

---

A CLI app for interacting with Aruba Central Clound Management Platform. With cross-platform / shell support. i.e. Bash, zsh, PowerShell, etc.

## Features
- Cross Platform Support
- Auto Completion
- Specify device, site, etc. by fuzzy match of multiple fields (i.e. name, mac, serial#, ip address)
- multiple output formats
- output to file
- multiple account support (easily switch between different central accounts)

## Installation
Requires python3 and pip

`pip3 install centralcli`

### Configuration

TODO Change pending config file location change, will look in user home .config/centralcli on all platforms and won't have the extra config subdir (currently ~/.config/centralcli/config) derived by click... just noticed on Windows the path is the config folder in site-packages, not what we want.

Refer to [config.yaml.example](config/config.yaml.example) to guide in the creation of config.yaml and place in the config directory.