import asyncio

import pytest
from typer.testing import CliRunner

from centralcli.cli import app

from . import cache, capture_logs, config, test_data
from ._test_data import test_cert_file, test_cert_file_der, test_cert_file_p12, test_invalid_var_file, test_switch_var_file_csv, test_switch_var_file_flat, test_switch_var_file_json

runner = CliRunner()


@pytest.fixture(scope="module", autouse=True)
def ensure_not_cache_b4_adds():
    if config.dev.mock_tests:
        dbs = [cache.GroupDB, cache.SiteDB, cache.LabelDB, cache.CertDB]
        doc_ids = [[g.doc_id for g in db.all() if g["name"].startswith("cencli_test")] for db in dbs]
        assert [asyncio.run(cache.update_db(db, doc_ids=ids)) for db, ids in zip(dbs, doc_ids)]
    else:  # pragma: no cover
        ...

    yield


@pytest.mark.parametrize(
    "args",
    [
        (str(test_cert_file), "--pem", "--svr"),
        (str(test_cert_file), "--svr"),
        (str(test_cert_file_p12), "--svr"),
        (str(test_cert_file_der), "--svr"),
    ]
)
def test_add_cert(args: tuple[str]):
    result = runner.invoke(app, ["add", "cert",  "cencli_test", *args, "-Y"])
    capture_logs(result, "test_add_cert")
    assert result.exit_code == 0
    assert "201" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        (str(test_cert_file), "--pem"),  # Missing type i.e --svr
        ("--svr",),  # Missing cert format i.e. --pem (and no cert_file to determine format from)
    ]
)
def test_add_cert_fail(args: tuple[str]):
    result = runner.invoke(app, ["add", "cert",  "cencli_test", *args])
    capture_logs(result, "test_add_cert_fail", expect_failure=True)
    assert result.exit_code == 1
    assert "must be provided" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ("cencli_test_group1",),
        ("cencli_test_group2", "--sw", "--ap", "--wired-tg", "--wlan-tg"),
        ("cencli_test_group3", "--ap"),
        ("cencli_test_group4", "--ap", "--gw", "--aos10", "--gw-role", "wlan", "--cnx"),
        ("cencli_test_group5", "--cx", "--sw", "--ap", "--aos10", "--mb", "--mon-only-sw", "--mon-only-cx"),
    ]
)
def test_add_groups(args: tuple[str]):
    result = runner.invoke(app, ["add", "group",  *args, "-Y"])
    capture_logs(result, "test_add_group1")
    assert any(
        [
            result.exit_code == 0 and "Created" in result.stdout,
            result.exit_code == 1 and "already exists" in result.stdout
        ]
    )


@pytest.mark.parametrize(
    "args",
    [
        ("--cx", "--sdwan", "--gw-role", "branch"),  # invalid combination of dev types
        ("--sw", "--mon-only-cx"),  # invalid combination w mon_only_cx
        ("--cx", "--mon-only-cx", "--wired-tg"),  # invalid combination w mon_only_tg
        ("--gw", "--gw-role", "wlan"),  # invalid gw role
        ("--ap", "--mb"),  # invalid mb options (also requires --aos10)
    ]
)
def test_add_groups_invalid(args: tuple[str]):
    result = runner.invoke(app, ["add", "group",  "cencli_test_group_fail", *args, "-Y"])
    capture_logs(result, "test_add_group_invalid_combination_of_dev_types", expect_failure=True)
    result.exit_code == 1


def test_add_site_by_address():
    result = runner.invoke(app, ["add", "site",  "cencli_test_site3", "123 Main St.", "Gallatin", "TN", "37066", "US", "-Y"])
    capture_logs(result, "test_add_site_by_address")
    assert any(
        [
            result.exit_code == 0 and "37066" in result.stdout,
            result.exit_code == 1 and "already exists" in result.stdout
        ]
    )


def test_add_site_by_geo():
    result = runner.invoke(app, ["add", "site",  "cencli_test_site4", "--lat", "36.378545", "--lon", "-86.360740", "-Y"])
    capture_logs(result, "test_add_site_by_geo")
    assert any(
        [
            result.exit_code == 0 and "36.37" in result.stdout,
            result.exit_code == 1 and "already exists" in result.stdout
        ]
    )


def test_add_template(ensure_cache_group2):
    result = runner.invoke(app, ["add", "template",  "cencli_test_template", "cencli_test_group2", test_data["template"]["template_file"], "--dev-type", "sw", "-Y"])
    capture_logs(result, "test_add_template")
    assert result.exit_code == 0
    assert "201" in result.stdout


@pytest.mark.parametrize(
    "test_file",
    [
        test_switch_var_file_json,
        test_switch_var_file_csv,
        test_switch_var_file_flat
    ]
)
def test_add_variables(ensure_cache_group2, test_file: str):
    result = runner.invoke(app, ["add", "variables",  str(test_file), "-Y"])
    capture_logs(result, "test_add_variables")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_add_variables_invalid(ensure_cache_group2):
    result = runner.invoke(app, ["add", "variables",  str(test_invalid_var_file), "-Y"])
    capture_logs(result, "test_add_variables_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "Missing" in result.stdout


@pytest.mark.parametrize(
    "labels",
    [
        ("cencli_test_label1",),
        ("cencli_test_label2", "cencli_test_label3"),
    ]
)
def test_add_label(labels: tuple[str]):
    result = runner.invoke(app, ["add", "label", *labels, "-Y"])
    capture_logs(result, "test_add_label")
    assert result.exit_code == 0
    assert "test_label" in result.stdout
    if config.dev.mock_tests:
        assert result.exit_code == 0
        assert "test_label" in result.stdout
    else:  # pragma: no cover
        assert any(
            [
                result.exit_code == 0 and "test_label" in result.stdout,
                result.exit_code == 1 and "already exist" in result.stdout
            ]
        )


def test_add_label_duplicate_name(ensure_cache_label1):
    result = runner.invoke(app, ["add", "label",  "cencli_test_label1", "-Y"])
    capture_logs(result, "test_add_label_duplicate_name", expect_failure=True)
    assert result.exit_code == 1
    assert "already exist" in result.stdout


@pytest.mark.parametrize(
    "args",
    [
        ("test@cencli.wtf", "--role", "authenticated", "--psk", "psk option does nothing", "-D"),
        ("test@cencli.wtf", "--role", "authenticated", "--psk", "psk option does nothing")
    ]
)
def test_add_named_mpsk(args: tuple[str]):
    result = runner.invoke(app, ["add", "mpsk",  test_data["mpsk_ssid"], *args, "-Y"])
    capture_logs(result, "test_add_named_mpsk")
    assert result.exit_code == 0
    assert "201" in result.stdout


def test_add_guest():
    result = runner.invoke(
        app,
        [
            "add",
            "guest",
            test_data["portal"]["name"],
            test_data["portal"]["guest"]["name"],
            "--email",
            test_data["portal"]["guest"]["email"],
            "--company",
            "central-api-cli test company",
            "--password",
            "cencli so awesome",
            "--notify-to",
            "email",
            "--phone",
            "615.555.1212",
            "--yes"
        ]
    )
    capture_logs(result, "test_add_guest")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout


def test_add_guest_invalid_notify():
    result = runner.invoke(app, ["add", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--email", test_data["portal"]["guest"]["email"], "--company", "central-api-cli test company", "--notify-to", "email", "--yes"])
    capture_logs(result, "test_add_guest_invalid_notify", expect_failure=True)
    assert result.exit_code == 1
    assert "--password" in result.stdout


def test_add_guest_invalid_phone():
    result = runner.invoke(app, ["add", "guest",  test_data["portal"]["name"],  test_data["portal"]["guest"]["name"], "--phone", "615555121", "--yes"])
    capture_logs(result, "test_add_guest_invalid_notify", expect_failure=True)
    assert result.exit_code == 1
    assert "invalid" in result.stdout


def test_add_device(ensure_cache_group2):
    result = runner.invoke(app, ["add", "device",  "serial", test_data["test_devices"]["ap"]["serial"], "mac", test_data["test_devices"]["ap"]["mac"], "group", test_data["test_devices"]["ap"]["group"], "-s", "foundation-ap", "--yes"])
    capture_logs(result, "test_add_device")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout


def test_add_wlan(ensure_cache_group1):
    result = runner.invoke(app, ["add", "wlan",  "cencli_test_group1", "delme", "vlan", "110", "psk", "C3ncliR0cks!", "--hidden", "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_add_wlan_no_psk(ensure_cache_group1):
    result = runner.invoke(app, ["add", "wlan",  "cencli_test_group1", "delme", "vlan", "110", "--hidden"])
    capture_logs(result, "test_add_wlan_no_psk", expect_failure=True)
    assert result.exit_code == 1


if config.dev.mock_tests:
    def test_add_webhook():
        result = runner.invoke(app, ["add", "webhook",  "cencli_test_webhook", "http://wh.consolepi.com:8123/webhook", "-y"])
        capture_logs(result, "test_add_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout

else:  # pragma: no cover
    ...
