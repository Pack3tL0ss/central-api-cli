
=================
Project Structure
=================

.. code-block:: bash

    ├── centralcli
    │   ├── __init__.py
    │   ├── boilerplate           # Boilerplate code generated via custom script from JSON schema files.
    │   │   ├── allcalls.py             # Any methods used by centralcli are pulled out and placed in central.py
    │   ├── caas.py               # Working caas API module, `cencli caas ...` (hidden command)
    │   ├── cache.py              # Local caching module facilitates use of device name / fuzzy match
    │   ├── central.py            # Contains methods that build the API calls
    │   ├── cleaner.py            # cleaner/parser module, cleans up output.
    │   ├── cli.py                # *The centralcli __main__ script*
    │   ├── cliadd.py             # `cencli add ...` level of the cli
    │   ├── clibatch.py           # `cencli batch ...` level of the cli
    │   ├── clicaas.py            # `cencli caas ...` level of the cli (hidden)
    │   ├── cliclone.py           # `cencli clone ...` level of the cli
    │   ├── clicommon.py          # Common class used by all cli levels (callbacks and output display)
    │   ├── clidel.py             # `cencli delete ...` level of the cli
    │   ├── clido.py              # Deprecated will be removed.
    │   ├── clishow.py            # `cencli show ...` level of the cli
    │   ├── clishowfirmware.py    # `cencli show firmware ...` level of the cli
    │   ├── clishowwids.py        # `cencli show wids ...` level of the cli
    │   ├── cliupdate.py          # `cencli update ...` level of the cli
    │   ├── cliupgrade.py         # `cencli upgrade ...` level of the cli
    │   ├── config.py             # config module reads centralcli config file / and any import files.
    │   ├── constants.py          # static variables and type deffinitions
    │   ├── exceptions.py         # Not Used Currently: Custom CentralApi exceptions
    │   ├── logger.py             # centralcli log module (logging)
    │   ├── response.py           # CentralApi response module.  Wraps aiohttp response and any other data sent to
    │   │                         #    Response() object.  Provides consistent set of attributes for eval during
    │   │                         #    display.
    │   ├── setup.py              # for pytest
    │   ├── utils.py              # Utils object with convenience methods.  A class just for the sake of namespace.
    │   └── vscodeargs.py         # dev helper.  Breaks single argument (how vscode represents args) into
    │   │                         #   multiple arguments (vscode debugger)
    ├── config
    │   ├── config.yaml           # pip installed version will use $HOME/.config/centralcli on POSIX or %HOME%\.centralcli on Win
    │   ├── config.yaml.example
    ├── poetry.lock
    ├── pyproject.toml
    ├── requirements-dev.txt
    ├── requirements.txt
    └── tests
        ├── cache_test.py
        ├── test_add.py
        ├── test_batch.py
        ├── test_del.py
        ├── test_devices.json
        ├── test_devices.json.example
        ├── test_do.py
        └── test_show.py

