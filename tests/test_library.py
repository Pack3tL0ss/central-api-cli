"""
tests for method/function branches that can't be tested via the CLI either because there
is not a command associated yet, or because the branch is only reachable when used as a library.

i.e. The CLI handles validation / errors prior to sending to the library modules that perform the API call.
So to test handling of invalid arguments to the library methods we need to test them directly (or via "cencli test method")
"""
from typer.testing import CliRunner

from centralcli.cache import api
from centralcli.cli import app
from centralcli.exceptions import MissingRequiredArgumentException

from . import capture_logs, config, test_data

runner = CliRunner()

# @pytest.mark.parametrize(
#     "args",
#     [
#         ([test_data["switch"]["name"], "on", "1"]),
#         ([test_data["switch"]["name"], "on"]),
#         ([test_data["switch"]["name"], "off"]),
#     ]
# )


if config.wss.key:
    def test_validate_wss_key():
        result = runner.invoke(app, ["test", "method", "validate_wss_key", config.wss.base_url, config.wss.key])
        capture_logs(result, "test_validate_wss_key")
        assert result.exit_code == 0
        assert "200" in result.stdout


if config.dev.mock_tests:
    def test_ack_notification():  # TODO NEEDS COMMAND, and alert id to int cache (like logs/events)
        resp = api.session.request(api.central.central_acknowledge_notifications, "AZl5PdWQBnVd7wH8QpSa")
        assert resp.ok
        assert resp.status == 200


def test_get_ap_system_config():
    resp = api.session.request(api.configuration.get_ap_system_config, test_data["ap"]["group"])
    assert resp.ok
    assert resp.status == 200


def test_kick_all_missing_argument():
    try:
        api.session.request(api.device_management.kick_users, test_data["ap"]["serial"])
    except MissingRequiredArgumentException:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_kick_all_missing_argument should have raised a MissingRequiredArgumentException but did not")


def test_remove_label_from_devices_fail():
    try:
        api.session.request(api.central.remove_label_from_devices, 1106, serials="US123456789", device_type="INVALID_DEV_TYPE")
    except ValueError:
        ...  # Test Passes
    else:  # pragma: no cover
        raise AssertionError("test_remove_label_from_devices_fail should have raised a ValueError due to invalid device_type, but did not")

