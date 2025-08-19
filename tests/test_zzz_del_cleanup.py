import shutil

import pytest
from typer.testing import CliRunner

from centralcli import log
from centralcli.cli import app  # type: ignore # NoQA

from . import config, test_batch_device_file, test_data, test_group_file, test_site_file, update_log

runner = CliRunner()


def do_nothing():
    ...


def stash_cache_file():
    pytest_cache = config.cache_file.parent / f"{config.cache_file.name}.pytest"
    if config.cache_file.exists():
        update_log(f"{pytest_cache} stored for mock test based on contents of  {config.cache_file}.  This is stored after adds, prior to delete tests.")
        shutil.copy(config.cache_file, pytest_cache)


# We stash the cache file after all adds have occured, so subsequent mocked partial test runs will have the cache
# in an expected state (devices, sites, groups, etc) will exist in cache.
@pytest.fixture(scope="module", autouse=True)
def session_setup_teardown():
    # Will be executed before the first test
    yield stash_cache_file()

    # executed after test is run
    do_nothing()


def test_batch_del_devices():
    result = runner.invoke(app, ["batch", "delete",  "devices", f'{str(test_batch_device_file)}', "-Y"])
    assert result.exit_code == 0
    assert "subscriptions successfully removed" in result.stdout.lower()
    assert "200" in result.stdout


def test_batch_del_groups():
    result = runner.invoke(app, ["batch", "delete",  "groups", str(test_group_file), "-Y"])
    if result.exit_code != 0:
        log.error(f"Error in test_batch_del_groups:\n{result.stdout}")
    if test_group_file.is_file():
        test_group_file.unlink()
    assert result.exit_code == 0
    assert "success" in result.stdout.lower()
    assert result.stdout.lower().count("success") == len(test_data["batch"]["groups_by_name"])


def test_batch_del_sites():
    result = runner.invoke(app, ["batch", "delete",  "sites", str(test_site_file), "-Y"])
    if test_site_file.is_file():
        test_site_file.unlink()
    assert result.exit_code == 0
    assert "success" in result.stdout
    assert result.stdout.count("success") == len(test_data["batch"]["sites"])

# Groups are created in test_add
def test_del_group():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group1",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout


def test_del_group_multiple():
    result = runner.invoke(app, [
        "delete",
        "group",
        "cencli_test_group3",
        "cencli_test_group4",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "Success" in result.stdout
    assert result.stdout.count("Success") == 2


def test_del_site_by_address():
    result = runner.invoke(app, [
        "delete",
        "site",
        "123 Main St.",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "uccess" in result.stdout


def test_del_site4():
    result = runner.invoke(app, [
        "delete",
        "site",
        "cencli_test_site4",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "uccess" in result.stdout

# cencli_test_label1 is deleted in test_zdel (last), it's used in other tests prior
def test_del_label_multi():
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label2",
        "cencli_test_label3",
        "-Y"
        ])
    assert result.exit_code == 0
    assert "200" in result.stdout

def test_del_guest():
    result = runner.invoke(app, ["-d", "delete", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--yes"])
    assert True in [
        result.exit_code == 0 and "200" in result.stdout,
        result.exit_code != 0 and "Unable to gather" in result.stdout
    ]
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout

def test_del_label():
    result = runner.invoke(app, [
        "delete",
        "label",
        "cencli_test_label1",
        "-Y"
        ])
    if result.exit_code != 0:
        update_log(result.stdout)
    assert result.exit_code == 0
    assert "200" in result.stdout
