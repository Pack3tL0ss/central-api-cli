
=================
Project Structure
=================

.. code-block:: bash

    ├── centralcli
    │   ├── boilerplate             # Boilerplate code generated via custom script from JSON schema files.
    │   │   ├── allcalls.py         # Any methods used by centralcli are pulled out and placed in central.py
    │   │   ├── configuration.py    # for now, central.py will eventually be broken out into diff modules.
    │   │   ├── firmware.py
    │   │   ├── guest.py
    │   │   └── wlan.py
    │   ├── caas.py                 # Working caas API module, `cencli caas ...` (hidden command)
    │   ├── cache.py                # Local caching module facilitates use of device name / fuzzy match in commands
    │   ├── central.py              # The module that with the async API calls for Aruba Central
    │   ├── cleaner.py              # cleaner/parser module, cleans up output.
    │   ├── cli.py                  # *The centralcli __main__ script*
    │   ├── cliadd.py               # `cencli add ...` level of the cli
    │   ├── clibatch.py             # `cencli batch ...` level of the cli
    │   ├── clicaas.py              # `cencli caas ...` level of the cli (hidden)
    │   ├── clicommon.py            # Common class used by all cli levels (callbacks and output display)
    │   ├── clidel.py               # `cencli delete ...` level of the cli
    │   ├── clido.py                # `cencli do ...` level of the cli.  These commands will move to level 1 eventually.
    │   ├── clishow.py              # `cencli show ...` level of the cli
    │   ├── cliupdate.py            # `cencli update ...` level of the cli
    │   ├── config.py               # config module reads centralcli config file / and any import files.
    │   ├── constants.py            # static variables and type deffinitions
    │   ├── exceptions.py           # Not Used Currently: Custom CentralApi exceptions
    │   ├── logger.py               # centralcli log module (logging)
    │   ├── response.py             # CentralApi response module.  Wraps aiohttp response and any other data sent to
    │   │                           #    Response() object.  Provides consistent set of attributes for eval during
    │   │                           #    display.
    │   ├── setup.py                # for pytest
    │   ├── utils.py                # Utils object with convenience methods.  A class just for the sake of namespace.
    │   └── vscodeargs.py           # dev helper.  Breaks single argument (how vscode represents args) into
    │   │                           #   multiple arguments (vscode debugger)
    ├── config                      # dev configuration directory (when running from git cloned repo)
    │   ├── config.yaml             # pip installed version will use $HOME/.config/centralcli on POSIX or %HOME%\.centralcli on Win
    │   ├── config.yaml.example
    ├── docs
    │   ├── Makefile
    │   ├── conf.py
    │   ├── img
    │   │   └── cencli-demo.gif
    │   ├── index.rst
    │   └── make.bat
    ├── poetry.lock
    ├── pyproject.toml
    ├── requirements-dev.txt
    ├── requirements.txt
    └── tests
        ├── test_devices.json
        ├── test_devices.json.example
        ├── test_do.py
        └── test_show.py

