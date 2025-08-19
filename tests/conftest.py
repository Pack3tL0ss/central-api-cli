import shutil

import pytest
from typer.testing import CliRunner

from centralcli import cache, config, log
from centralcli.cli import app

runner = CliRunner()

cache_bak_file = config.cache_file.parent / f"{config.cache_file.name}.pytest.bak"


def stash_cache_file():
    if config.cache_file.exists():
        log.info(f"Real Cache {config.cache_file}, backed up to {cache_bak_file} as mock test run is starting (which will add items that don't actually exist to the cache)")
        shutil.copy(config.cache_file, cache_bak_file)

    pytest_cache = config.cache_file.parent / f"{config.cache_file.name}.pytest"
    if pytest_cache.exists():
        log.info(f"Real cache replaced with existing pytest Cache {pytest_cache} to prepopulate items for mock run.")
        shutil.copy(pytest_cache, config.cache_file)



def restore_cache_file():
    if cache_bak_file.exists():
        log.info(f"Restoring real cache from {cache_bak_file} after mock test run")
        log.info(f"Stashing cache from mock test run for later use {cache_bak_file.name.removesuffix('.bak')}")
        _ = shutil.copy(cache_bak_file, config.cache_file)
        cache_bak_file.rename(cache_bak_file.name.removesuffix('.bak'))  # we keep the pytest cache as running individual tests on subsequent runs would not work otherwise

        return config.cache_file.exists()

def cleanup_test_groups():
    del_groups = [g for g in cache.groups_by_name if g.startswith("cencli_test_")]
    if del_groups:
        result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0

def cleanup_test_sites():
    del_sites = [s for s in cache.sites_by_name if s.startswith("cencli_test_")]
    if del_sites:
        result = runner.invoke(app, ["delete", "site", *del_sites, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0

def cleanup_test_labels():
    del_labels = [label for label in cache.labels_by_name if label.startswith("cencli_test_")]
    if del_labels:
        result = runner.invoke(app, ["delete", "label", *del_labels, "-Y"])
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