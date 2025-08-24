import shutil
from pathlib import Path

import pendulum
import pytest
from typer.testing import CliRunner

from centralcli import cache, config, log
from centralcli.cli import app

from ._mock_request import test_responses
from ._test_data import test_device_file, test_group_file, test_site_file

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
        log.info(f"Stashing cache from mock test run for later use {cache_bak_file.name.removesuffix('.bak')}")
        config.cache_file.rename(cache_bak_file.parent / cache_bak_file.name.removesuffix('.bak'))  # we keep the pytest cache as running individual tests on subsequent runs would not work otherwise

        log.info(f"Restoring real cache from {cache_bak_file} after mock test run")
        cache_bak_file.rename(config.cache_file.parent / config.cache_file.name)


        return config.cache_file.exists()


def _cleanup_test_groups():
    del_groups = [g for g in cache.groups_by_name if g.startswith("cencli_test_")]
    if del_groups:
        result = runner.invoke(app, ["delete", "group", *del_groups, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


def _cleanup_test_sites():
    del_sites = [s for s in cache.sites_by_name if s.startswith("cencli_test_")]
    if del_sites:
        result = runner.invoke(app, ["delete", "site", *del_sites, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


def _cleanup_test_labels():
    del_labels = [label for label in cache.labels_by_name if label.startswith("cencli_test_")]
    if del_labels:
        result = runner.invoke(app, ["delete", "label", *del_labels, "-Y"])
        assert "Success" in result.stdout
        assert result.exit_code == 0


@pytest.hookimpl()
def pytest_sessionfinish(session: pytest.Session):
    if "--collect-only" not in session.config.invocation_params.args and config.dev.mock_tests and session.testscollected > 120:
        unused = "\n".join(test_responses.unused)
        unused_log_file = Path(config.log_dir / "pytest-unused-mocks.log")
        log.info(f"{len(test_responses.unused)} mock responses were unused.  See {unused_log_file} for details.")
        now = pendulum.now()
        ts = " ".join(now.to_day_datetime_string().split(", ")[1:])
        unused_log_file.write_text(
            f"The following {len(test_responses.unused)} mock responses were not used during this test run {ts}\n{unused}\n"
        )


def cleanup_test_items():  # prama: no cover
    try:
        _cleanup_test_groups()
        _cleanup_test_labels()
        _cleanup_test_sites()
    except AssertionError as e:
        log.exception(f"An error ({repr(e)}) may have occured during test run cleanup.  You may need to verify test objects have been deleted from central.", exc_info=True)


def do_nothing():
    ...


def cleanup_import_files():
    test_files = [test_group_file, test_site_file, test_device_file]
    for file in test_files:
        if file.exists():
            file.unlink()


def setup():
    if config.dev.mock_tests:
        yield do_nothing()
        # yield stash_cache_file()
    else:
        yield do_nothing()


def teardown():
    cleanup_import_files()
    if config.dev.mock_tests:
        return do_nothing()
        # return restore_cache_file()
    else:
        return cleanup_test_items()  # pragma: no cover


@pytest.fixture(scope='session', autouse=True)
def session_setup_teardown():
    # Will be executed before the first test
    yield from setup()

    # executed after test is run
    teardown()


@pytest.fixture(scope='function', autouse=True)
def clear_lru_caches():
    cache.get_inv_identifier.cache_clear()
    cache.get_combined_inv_dev_identifier.cache_clear()
    cache.get_name_id_identifier.cache_clear()
    for db in cache._tables:
        db.clear_cache()
    cache.responses.clear()
    yield
