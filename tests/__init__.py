"""cencli test setup

This file will ensure only the account specified via customer_id key in
test_devices.json is the only account tests are ran against.

Otherwise if the last command you've run was for an alternate account, and
forget_account_after is set, you could inadvertantly run tests against an
account you didn't intend to.

This would be fairly harmless, we do add a bunch of sites/groups/etc. but
we don't harm any existing devices/groups.  Any commands ran against devices
(we do bounce PoE), references devices in test_devices.json.

NOTE: Doing the imports here has the originally unintended consequence of using
the same cache object for all runs.  This means cache.updated will carry over
from one command to another, which is not the behavior under normal circumstances.

Turns out this is a good thing though.  Most cache.update_*_db methods first
check to see if the API call had already been done before running, with the
intent being to use the cache rather than make another request if it has been
ran.  Turns out this logic doesn't work for a number of functions.

i.e. update_client_db wasn't even returning a value if get_clients had already
been ran.  update_dev_db returns the cache response, but if the previous call
was at verbosity 0 and the subsequent call was verbosity > 0, the cache results
don't include the verbose details.

All this is to say we can use this to test and update that logic.  Currently
most tests impacted import config and set config.updated = [] before the run
to flush the previous results forcing a new API call, as under typically CLI
use this isn't going to be an issue.

Bottom Line.
  1. import config and set config.updated = [] inside any test method
     impacted by previous runs, and update_*_db resulting in unexpected failures.
  2. Leave config.updated unchanged to test caching behavior, which currently
     normal CLI operations don't really exercise.


"""
# from cli import cli as common
from centralcli.cli import log, cli as common, config
import json
from pathlib import Path
from typing import Dict, Any

class InvalidAccountError(Exception):
    ...

class BatchImportFileError(Exception):
    ...

class ConfigNotFoundError(Exception):
    ...

def update_log(txt: str):
    with test_log_file.open("a") as f:
        f.write(f'{txt.rstrip()}\n')

def get_test_data():
    test_file = Path(__file__).parent / 'test_devices.json'
    if not test_file.is_file():
        raise FileNotFoundError(f"Required test file {test_file} is missing.  Refer to {test_file.name}.example")
    return json.loads(test_file.read_text())

def setup_batch_import_file(test_data: dict, import_type: str = "sites") -> Path:
    test_batch_file = config.cache_dir / f"test_runner_{import_type}.json"
    res = test_batch_file.write_text(
        json.dumps(test_data["batch"][import_type])
    )
    if not res:
        raise BatchImportFileError("Batch import file creation from test_data returned 0 chars written")
    return test_batch_file

def ensure_default_account(test_data: dict):
    if common.central.auth.central_info["customer_id"] != str(test_data["customer_id"]):
        msg = f'customer_id {common.central.auth.central_info["customer_id"]} script initialized with does not match customer_id in test_data.\nRun a command with -d to revert to default account'
        raise InvalidAccountError(msg)

if __name__ == "tests":
    test_log_file: Path = log.log_file.parent / "pytest.log"
    # update_log(f"\n__init__: cache: {id(common.cache)}")
    test_data: Dict[str, Any] = get_test_data()
    ensure_default_account(test_data=test_data)
    test_group_file: Path = setup_batch_import_file(test_data=test_data, import_type="groups_by_name")
    test_site_file: Path = setup_batch_import_file(test_data=test_data)
    gw_group_config_file = config.cache_dir / "test_runner_gw_grp_config"
    test_batch_device_file: Path = test_data["batch"]["devices"]