import shutil

import pytest
from typer.testing import CliRunner

from centralcli import cache, config
from centralcli.cli import app

runner = CliRunner()

cache_bak_file = config.cache_file.parent / f"{config.cache_file.name}.pytest.bak"

def stash_cache_file():
    if config.cache_file:
        return shutil.copy(config.cache_file, cache_bak_file)

def restore_cache_file():
    if cache_bak_file:
        _ = shutil.copy(cache_bak_file, config.cache_file)
        cache_bak_file.unlink()

        return _

def cleanup_test_groups():
    del_groups = [g for g in cache.groups_by_name if g.startswith("cencli_test_")]
    if del_groups:
        result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0

def do_nothing():
    ...

def setup():
    if config.dev.mock_tests:
        yield stash_cache_file()
    else:
        yield do_nothing()

def teardown():
    if config.dev.mock_tests:
        return restore_cache_file()
    else:
        return cleanup_test_groups()


@pytest.fixture(scope='session', autouse=True)
def session_setup_teardown():
    # Will be executed before the first test
    yield from setup()

    # executed after test is run
    teardown()