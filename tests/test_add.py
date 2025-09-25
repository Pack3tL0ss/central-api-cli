import asyncio

import pytest
from typer.testing import CliRunner

from centralcli.cli import app

from . import cache, capture_logs, config, test_data
from ._test_data import test_cert_file, test_invalid_var_file

runner = CliRunner()


@pytest.fixture(scope="module", autouse=True)
def ensure_not_cache_b4_adds():
    if config.dev.mock_tests:
        dbs = [cache.GroupDB, cache.SiteDB, cache.LabelDB, cache.CertDB]
        doc_ids = [[g.doc_id for g in db.all() if g["name"].startswith("cencli_test")] for db in dbs]
        assert [asyncio.run(cache.update_db(db, doc_ids=ids)) for db, ids in zip(dbs, doc_ids)]
    yield


def test_add_cert():
    result = runner.invoke(app, ["-d", "add", "cert",  "cencli_test", str(test_cert_file), "--pem", "--svr", "-Y"])
    capture_logs(result, "test_add_cert")
    assert result.exit_code == 0
    assert "201" in result.stdout


def test_add_cert_no_type():
    result = runner.invoke(app, ["-d", "add", "cert",  "cencli_test", str(test_cert_file), "--pem",])
    capture_logs(result, "test_add_cert_no_type", expect_failure=True)
    assert result.exit_code == 1
    assert "must be provided" in result.stdout


def test_add_cert_no_format():
    result = runner.invoke(app, ["-d", "add", "cert",  "cencli_test", str(test_cert_file), "--svr",])
    capture_logs(result, "test_add_cert_no_format", expect_failure=True)
    assert result.exit_code == 1
    assert "must be provided" in result.stdout


def test_add_group1():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group1", "-Y"])
    capture_logs(result, "test_add_group1")
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group2_tg():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group2", "--sw", "--ap", "--wired-tg", "--wlan-tg", "-Y"])
    capture_logs(result, "test_add_group2_tg")
    assert any(
        [
            result.exit_code == 0 and "Created" in result.stdout,
            result.exit_code == 1 and "already exists" in result.stdout
        ]
    )


def test_add_group3():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group3", "--ap", "-Y"])
    capture_logs(result, "test_add_group3")
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group4_aos10_gw_wlan_cnx():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group4", "--ap", "--gw", "--aos10", "--gw-role", "wlan", "--cnx", "-Y"])
    capture_logs(result, "test_add_group4_aos10_gw_wlan_cnx")
    assert True in [
        result.exit_code == 0 and "Created" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_group5_mb_mon_only_cx_sw():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group5", "--cx", "--sw", "--ap", "--aos10", "--mb", "--mon-only-sw", "--mon-only-cx", "-Y"])
    capture_logs(result, "test_add_group5_mb_mon_only_cx_sw")
    assert result.exit_code == 0
    assert "Created" in result.stdout


def test_add_group_invalid_combination_of_dev_types():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group_fail", "--cx", "--sdwan", "--gw-role", "branch", "-Y"])
    capture_logs(result, "test_add_group_invalid_combination_of_dev_types", expect_failure=True)
    result.exit_code == 1


def test_add_group_invalid_combination_mon_only_cx():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group_fail", "--sw", "--mon-only-cx", "-Y"])
    capture_logs(result, "test_add_group_invalid_combination_mon_only_cx", expect_failure=True)
    result.exit_code == 1


def test_add_group_invalid_combination_mon_only_tg():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group_fail", "--cx", "--mon-only-cx", "--wired-tg", "-Y"])
    capture_logs(result, "test_add_group_invalid_combination_mon_only_tg", expect_failure=True)
    result.exit_code == 1


def test_add_group_invalid_gw_role():
    result = runner.invoke(app, ["add", "group",  "cencli_test_group_fail", "--gw", "--gw-role", "wlan", "-Y"])
    capture_logs(result, "test_add_group_invalid_gw_role", expect_failure=True)
    result.exit_code == 1


def test_add_group_invalid_mb_options():
    result = runner.invoke(app, ["-d", "add", "group",  "cencli_test_group_fail", "--ap", "--mb", "-Y"])
    capture_logs(result, "test_add_group_invalid_mb_options", expect_failure=True)
    result.exit_code == 1


def test_add_site_by_address():
    result = runner.invoke(app, ["-d", "add", "site",  "cencli_test_site3", "123 Main St.", "Gallatin", "TN", "37066", "US", "-Y"])
    capture_logs(result, "test_add_site_by_address")
    assert True in [
        result.exit_code == 0 and "37066" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_site_by_geo():
    result = runner.invoke(app, ["-d", "add", "site",  "cencli_test_site4", "--lat", "36.378545", "--lon", "-86.360740", "-Y"])
    capture_logs(result, "test_add_site_by_geo")
    assert True in [
        result.exit_code == 0 and "36.37" in result.stdout,
        result.exit_code == 1 and "already exists" in result.stdout
    ]


def test_add_template(ensure_cache_group2):
    result = runner.invoke(app, ["add", "template",  "cencli_test_template", "cencli_test_group2", test_data["template"]["template_file"], "--dev-type", "sw", "-Y"])
    capture_logs(result, "test_add_template")
    assert result.exit_code == 0
    assert "201" in result.stdout


def test_add_variables(ensure_cache_group2):
    result = runner.invoke(app, ["add", "variables",  test_data["test_devices"]["switch"]["variable_file"], "-Y"])
    capture_logs(result, "test_add_variables")
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_add_variables_invalid(ensure_cache_group2):
    result = runner.invoke(app, ["add", "variables",  str(test_invalid_var_file), "-Y"])
    capture_logs(result, "test_add_variables_invalid", expect_failure=True)
    assert result.exit_code == 1
    assert "Missing" in result.stdout


def test_add_label():
    result = runner.invoke(app, ["-d", "add", "label",  "cencli_test_label1", "-Y"])
    capture_logs(result, "test_add_label")
    assert True in [
        result.exit_code == 0 and "test_label" in result.stdout,
        result.exit_code == 1 and "already exist" in result.stdout
    ]


def test_add_label_duplicate_name():
    result = runner.invoke(app, ["-d", "add", "label",  "delme", "-Y"])
    capture_logs(result, "test_add_label_duplicate_name", expect_failure=True)
    assert result.exit_code == 1 and "already exist" in result.stdout


def test_add_label_multi():
    result = runner.invoke(app, ["-d", "add", "label",  "cencli_test_label2", "cencli_test_label3", "-Y"])
    capture_logs(result, "test_add_label_multi")
    assert True in [
        result.exit_code == 0 and "test_label" in result.stdout,
        result.exit_code == 1 and "already exist" in result.stdout
    ]


def test_add_named_mpsk():
    result = runner.invoke(app, ["add", "mpsk",  test_data["mpsk_ssid"], "test@cencli.wtf", "--role", "authenticated", "--psk", "psk option does nothing", "-D", "-Y"])
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
    result = runner.invoke(app, ["-d", "add", "device",  "serial", test_data["test_devices"]["ap"]["serial"], "mac", test_data["test_devices"]["ap"]["mac"], "group", test_data["test_devices"]["ap"]["group"], "-s", "foundation-ap", "--yes"])
    capture_logs(result, "test_add_device")
    assert result.exit_code == 0
    assert "200" in result.stdout
    assert "cache update ERROR" not in result.stdout
    assert "xception" not in result.stdout


def test_add_wlan(ensure_cache_group1):
    result = runner.invoke(app, ["-d", "add", "wlan",  "cencli_test_group1", "delme", "vlan", "110", "psk", "C3ncliR0cks!", "--hidden", "--yes"])
    assert result.exit_code == 0
    assert "200" in result.stdout


def test_add_wlan_no_psk(ensure_cache_group1):
    result = runner.invoke(app, ["-d", "add", "wlan",  "cencli_test_group1", "delme", "vlan", "110", "--hidden"])
    capture_logs(result, "test_add_wlan_no_psk", expect_failure=True)
    assert result.exit_code == 1

if config.dev.mock_tests:
    def test_add_webhook():
        result = runner.invoke(app, ["add", "webhook",  "cencli_test_webhook", "http://wh.consolepi.com:8123/webhook", "-y"])
        capture_logs(result, "test_add_webhook")
        assert result.exit_code == 0
        assert "200" in result.stdout
