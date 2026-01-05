from ._mock_request import test_responses
from centralcli.environment import env


def test_per_test_regex_match():
    prev_current = env.current_test
    env.current_test = "per_test_regex"

    # install a per-test regex entry
    test_responses.responses[env.current_test] = {
        'GET_/configuration/v1/ap_settings_cli/.*': {'status': 210, 'payload': {'ok': True}}
    }

    has_per_test_res, candidates = test_responses._get_candidates('GET_/configuration/v1/ap_settings_cli/foo')
    assert has_per_test_res is True
    assert candidates and candidates[0]['status'] == 210
    assert candidates[0]['method'] == 'GET'
    assert candidates[0]['url'] == '/configuration/v1/ap_settings_cli/foo'

    # cleanup
    del test_responses.responses[env.current_test]
    env.current_test = prev_current


def test_global_regex_match():
    # backup and inject into ok_responses for GET
    ok_responses = test_responses.responses.setdefault('ok_responses', {})
    prev_get = ok_responses.get('GET', {}).copy()

    ok_responses['GET'] = {**prev_get, 'configuration_v1_ap_settings_cli_.*': {'status': 221, 'payload': {'ok': True}, 'url': '/configuration/v1/ap_settings_cli/{id}'}}

    has_per_test_res, candidates = test_responses._get_candidates('GET_/configuration/v1/ap_settings_cli/12345')
    assert has_per_test_res is False
    assert candidates and candidates[0]['status'] == 221
    assert candidates[0]['method'] == 'GET'
    assert candidates[0]['url'] == '/configuration/v1/ap_settings_cli/12345'

    # restore
    ok_responses['GET'] = prev_get