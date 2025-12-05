"""We need this module to run near the end so cache is fully up to date for completion tests."""
import sys
from datetime import datetime as dt
from typing import Callable

import pytest
from click import Command, Context
from typer import Exit
from typer.testing import CliRunner

from centralcli import cache, common, log, render, utils

from . import clean_mac, test_data

runner = CliRunner()
ctx = Context(Command("cencli reset"), info_name="reset", resilient_parsing=True)
ctx.params={'what': 'overlay', 'device': None, 'yes': None, 'debug': None, 'default': None, 'account': None}


# TODO most are hard-coded need to grab from test_data or dynamically from cache
# TODO most need to be tested with a value and an empty string, parameritize decorator...
@pytest.mark.parametrize(
    "_,incomplete,args",
    [
        [1, test_data["ap"]["name"], ("dev-type", "")],
        [2, test_data["ap"]["name"], ("dev-type", "ap")],
        [3, test_data["gateway"]["name"], ("dev-type", "clients")],
        [4, test_data["switch"]["name"], ("dev-type", "switch")],
    ]
)
def test_dev_completion(_: int, incomplete: str, args: tuple[str]):
    result = [c for c in cache.dev_completion(incomplete, args)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)


@pytest.mark.parametrize("expected,args", [(test_data["ap"]["name"], ["show", "overlay", "summary"]), ("self", ["cencli", "show", "config"])])
def test_dev_ap_gw_completion(expected: str, args: list[str]):
    ctx = Context(Command("cencli show config"), info_name="cencli show config", resilient_parsing=True)
    if expected == "self":  # pragma: no cover
        ctx.params = {"group_dev": "self"}
    result = [c for c in cache.dev_ap_gw_completion(ctx=ctx, incomplete=expected[0:-2], args=args)]
    if expected == "self":
        assert len(result) == 0
    else:
        assert len(result) == 1
        assert all([m.lower().startswith(expected[0:-2].lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_group_completion(incomplete: str = ""):
    result = [c for c in cache.group_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)

def test_group_completion_case_insensitive(incomplete: str = "w"):
    result = [c for c in cache.group_completion(incomplete)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_group_ap_completion(incomplete: str = test_data["ap"]["group"]):
    result = [c for c in cache.ap_group_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)


def test_group_ap_completion_empty_string(incomplete: str = ""):
    result = [c for c in cache.ap_group_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)


def test_site_completion(incomplete: str = "barn"):
    result = [c for c in cache.site_completion(ctx, incomplete, ("show", "site",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_site_completion_empty_string(incomplete: str = ""):
    result = [c for c in cache.site_completion(ctx, incomplete, ("show", "site",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize(
    "idx,fixtures,complete_func,incomplete,args",
    [
        [1, "ensure_cache_template", cache.template_completion, "cencli", ("show", "templates")],
        [2, "ensure_cache_group2", cache.template_group_completion, "cencli", ()],
        [3, "ensure_cache_template", cache.template_completion, "", ("show", "templates")],
        [4, ["ensure_cache_group2", "ensure_cache_template"], cache.dev_template_completion, "cencl", ("show", "templates")],
        [5, ["ensure_cache_group2", "ensure_cache_template", "ensure_dev_cache_test_ap"], cache.dev_template_completion, "", ("show", "templates")],
        [6, "ensure_cache_template_by_name", cache.dev_template_completion, test_data["template"]["name"].capitalize()[0:-2], ()],
    ]
)
def test_template_completion(idx: int, fixtures: str | list[str] | None, complete_func: Callable, incomplete: str, request: pytest.FixtureRequest, args: tuple[str]):
    if fixtures:
        [request.getfixturevalue(f) for f in utils.listify(fixtures)]
    result = [c for c in complete_func(incomplete, args)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize(
    "idx,fixtures,complete_func,incomplete,args",
    [
        [1, "ensure_cache_group2", cache.smg_kw_completion, "cencli_test_group2", ("group",)],
        [2, "ensure_cache_group2", cache.smg_kw_completion, test_data["test_devices"]["ap"]["mac"], ("group", "cencli_test_group2", "mac")],
        [3, "ensure_cache_group2", cache.smg_kw_completion, "ser", ("group", "cencli_test_group2",)],
        [4, None, cache.smg_kw_completion, test_data["test_devices"]["ap"]["serial"], ("serial",)],
    ]
)
def test_smg_keyword_completion(idx: int, fixtures: str | list[str] | None, complete_func: Callable, incomplete: str, request: pytest.FixtureRequest, args: tuple[str]):
    expected = incomplete if args[-1] == "group" or args[-1] not in ["serial", "mac"] else args[-1].upper()
    if fixtures:
        [request.getfixturevalue(f) for f in utils.listify(fixtures)]
    if idx % 2 == 0:
        ctx.params = {}
        for _idx, arg in enumerate(args, start=1):
            ctx.params = {**ctx.params, f"kw{_idx}": arg} if _idx % 1 == 0 else {args[_idx - 1]: arg}
            args = ()
    result = [c for c in complete_func(ctx, incomplete, args) if c not in ["|", incomplete]]
    assert len(result) > 0
    assert all([m.lower().lstrip("<").startswith(expected.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_switch_completion(incomplete: str = test_data["switch"]["name"].swapcase()):
    result = [c for c in cache.dev_switch_completion(incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_cx_completion(incomplete: str = test_data["switch"]["name"].swapcase()):
    result = [c for c in cache.dev_cx_completion(incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_sw_completion(incomplete: str = test_data["template_switch"]["name"].swapcase()):
    result = [c for c in cache.dev_sw_completion(incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_gw_switch_completion(incomplete: str = test_data["switch"]["name"].swapcase()):
    result = [c for c in cache.dev_gw_switch_completion(ctx, incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_gw_completion(incomplete: str = test_data["gateway"]["name"].swapcase()):
    result = [c for c in cache.dev_gw_completion(incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_ap_gw_sw_completion(ensure_dev_cache_test_ap, incomplete: str = "cencli_test_ap"):  # tests underscore/hyphen logic in get_dev_identifier
    result = [c for c in cache.dev_ap_gw_sw_completion(ctx, incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().replace("_", "-").startswith(incomplete.lower().replace("_", "-")) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_gw_switch_site_completion(incomplete: str = "barn"):
    result = [c for c in cache.dev_gw_switch_site_completion(ctx, incomplete, ("show", "vlans",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_dev_ap_completion_partial_serial(incomplete: str = "CNDDK"):
    result = [c for c in cache.dev_ap_completion(incomplete, ("show", "aps",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_mpsk_completion():
    mpsk = cache.get_mpsk_network_identifier(test_data["mpsk_ssid"])
    for incomplete in {mpsk.name, mpsk.id}:
        result = [c for c in cache.mpsk_network_completion(ctx, incomplete[0:-2])]
        assert len(result) > 0
        assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize("expected,do_args", [(test_data["switch"]["name"], True), (test_data["switch"]["group"], False), ("self", True), ("self", False)])
def test_group_dev_completion(expected: str, do_args: bool):
    ctx = Context(Command("cencli show config"), info_name="cencli show config", resilient_parsing=True)
    ctx.params = {"group_dev": None}
    result = list(cache.group_dev_completion(ctx=ctx, incomplete=expected[0:-2], args=("show", "config") if do_args else ()))
    assert len(result) > 0
    assert all([m.lower().startswith(expected[0:-2].lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize("expected,do_args", [(test_data["ap"]["name"], True), (test_data["ap"]["group"], False), ("self", True), ("self", False)])
def test_group_dev_ap_gw_completion(expected: str, do_args: bool):
    ctx = Context(Command("cencli show config"), info_name="cencli show config", resilient_parsing=True)
    ctx.params = {"group_dev": None}
    result = list(cache.group_dev_ap_gw_completion(ctx=ctx, incomplete=expected[0:-2], args=("show", "config") if do_args else ()))
    assert len(result) == 1
    assert all([m.lower().startswith(expected[0:-2].lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize("expected", [test_data["switch"]["name"]])
def test_dev_switch_gw_completion(expected: str):
    result = list(cache.dev_switch_gw_completion(incomplete=expected[0:-2],))
    assert len(result) == 1
    assert all([m.lower().startswith(expected[0:-2].lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize(
        "incomplete,params,expected",
        [
            (test_data['client']['wireless']['name'][0:-1].swapcase(), {"wireless": True}, test_data["client"]["wireless"]["name"]),
            (f'"{test_data["client"]["wireless"]["name"].capitalize()[0:-2]}', {"wireless": True}, test_data["client"]["wireless"]["name"]),
            (f"'{test_data['client']['wireless']['name'][0:-2]}", {"wireless": True}, test_data["client"]["wireless"]["name"]),
            (test_data["client"]["wireless"]["mac"], {"wireless": True}, utils.Mac(test_data["client"]["wireless"]["mac"]).cols),
            (test_data["client"]["wireless"]["ip"], {"wireless": True}, test_data["client"]["wireless"]["ip"])
        ]
    )
def test_client_completion(incomplete: str, params: dict[str, str | bool], expected: str):
    ctx.params = {**ctx.params, **params}
    result = list(cache.client_completion(ctx, incomplete=incomplete))
    assert len(result) > 0
    assert clean_mac(expected).lower().startswith(clean_mac(incomplete).lower().strip('"\''))

@pytest.mark.parametrize("expected,params", [(test_data["ap"]["mac"], {"wireless": None, "wired": None}), (test_data["ap"]["name"], {"wireless": True, "wired": None}), (test_data["switch"]["serial"], {"wireless": None, "wired": True})])
def test_dev_client_completion(expected: str, params: dict[str, bool | None]):
    ctx = Context(Command("cencli blah blah"), info_name="cencli some command", resilient_parsing=True)
    ctx.params = {**ctx.params, **params}
    result = list(cache.dev_client_completion(ctx, incomplete=expected))
    assert len(result) == 1
    assert all([m.lower().startswith(expected[0:-2].lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])


def test_event_log_completion_pytest(incomplete: str = "pyte"):
    result = list(cache.event_log_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_event_log_completion_empty_string(incomplete: str = ""):
    result = list(cache.event_log_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_audit_log_completion(incomplete: str = "1"):
    result = list(cache.audit_log_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([str(m).lower().startswith(incomplete.lower()) for m in list(map(str, result))])

def test_audit_log_completion_empty_string(incomplete: str = ""):
    result = list(cache.audit_log_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([str(m).lower().startswith(incomplete.lower()) for m in list(map(str, result))])

def test_portal_completion(incomplete: str = test_data["portal"]["name"]):
    result = list(cache.portal_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_portal_completion_empty_string(incomplete: str = ""):
    result = list(cache.portal_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

@pytest.mark.parametrize(
        "incomplete,args", [
            ("sit", ("remove", test_data["ap"]["ip"])),
            (test_data["ap"]["ip"], ("remove",))
        ]
    )
def test_remove_completion_site(incomplete: str, args: tuple[str]):
    result = list(cache.remove_completion(ctx=ctx, incomplete=incomplete, args=args))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_remove_completion_dev(incomplete: str = test_data["ap"]["site"]):
    result = list(cache.remove_completion(ctx=ctx, incomplete=incomplete, args=("site",)))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

@pytest.mark.parametrize("incomplete", ["cencli-test_label1", "110"])
def test_label_completion(ensure_cache_label1, incomplete: str):
    result = list(cache.label_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize(
        "incomplete,params,expected",
        [
            (test_data["gateway"]["name"], {"kw1": "all"}, "commands"),
            (test_data["gateway"]["name"], {"kw1": "x"}, "commands"),
            (test_data["gateway"]["name"], {"kw1": "commands"}, None),
            ("cencli_test_g", {"kw1": "group"}, "cencli_test_group1"),
            ("cencli_test_s", {"kw1": "site"}, "cencli_test_site1"),
            (test_data["gateway"]["name"], {"kw1": "device"}, test_data["gateway"]["name"]),
        ]
    )
def test_send_cmds_completion(ensure_cache_group1, ensure_cache_site1, incomplete: str, params: dict[str, str | bool], expected: str | None):
    ctx.params = params
    result = list(cache.send_cmds_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert str(expected) in str(result)


def test_ws_completion(incomplete=""):
    result = list(cache.workspace_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize("expected", ["superlongemail", "superlongemail@kabrew.com", "6155551212", "7c9eb0df-b211-4225-94a6-437df0dfca59", ""])
def test_guest_completion(ensure_cache_guest1, expected: str):
    result = list(cache.guest_completion(ctx, incomplete=expected[0:-2]))
    assert len(result) >= 1
    try:
        assert all([m.lower().startswith(expected.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])
    except AssertionError:
        log.error(f"test_guest_completion: {expected = }    {result = }")


@pytest.mark.parametrize("incomplete", ["cencli-tes", "781b9320972dc571d9", ""])
def test_cert_completion(ensure_cache_cert, incomplete: str):
    result = list(cache.cert_completion(ctx, incomplete=incomplete))
    assert len(result) >= 1
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])


@pytest.mark.parametrize(
    "fixture,incomplete,pass_condition",
    [
        ("ensure_cache_subscription", "advanced-ap", lambda r: [sub[0] == "advanced-ap" for sub in r]),
        ("ensure_cache_subscription", "7658e672-2af5-5646-aa37-406af19c6d", lambda r: len(r) == 1),
        ("ensure_cache_subscription", "", lambda r: len(r) > 1),
        (None, "no_match_no_match", lambda r: len(r) == 0),
    ]
)
def test_sub_completion(fixture: str | None, incomplete: str, pass_condition: Callable, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    result = list(cache.sub_completion(ctx, incomplete=incomplete))
    assert pass_condition(result)


@pytest.mark.parametrize(
    "fixture,iden_func,query_str,kwargs,pass_condition,exception",
    [
        (None, cache.get_sub_identifier, "no_match-no_match", {}, None, Exit),
        (None, cache.get_sub_identifier, "no_match-no_match", {"retry": False}, lambda r: r is None, None),
        (None, cache.get_sub_identifier, "foundation-switch-6100", {"end_date": dt(2026, 9, 6)}, lambda r: (dt.fromtimestamp(r.end_date) - dt(2026, 9, 6)).seconds < 86400, None),
        (None, cache.get_group_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_group_identifier, "no-match_no-match", {"retry": False, "dev_type": "switch"}, lambda r: r is None, None),
        (None, cache.get_site_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_site_identifier, "no-match_no-match", {"retry": False}, lambda r: r is None, None),
        (None, cache.get_inv_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_inv_identifier, "no-match_no-match", {"retry": False, "dev_type": "switch"}, lambda r: r is None, None),
        ("ensure_inv_cache_test_ap", cache.get_inv_identifier, test_data["test_devices"]["ap"]["mac"][0:-2], {"retry": False, "dev_type": "switch"}, lambda r: r is None, None),
        (None, cache.get_dev_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_dev_identifier, "no-match_no-match", {"retry": False, "dev_type": "switch"}, lambda r: r is None, None),
        ("ensure_dev_cache_test_ap", cache.get_inv_identifier, test_data["test_devices"]["ap"]["mac"][0:-2], {"retry": False, "dev_type": "switch"}, lambda r: r is None, None),
        (None, cache.get_identifier, "no-match_no-match", {"qry_funcs": ["dev", "group"]}, None, Exit),
        (None, cache.get_identifier, "no-match_no-match", {"qry_funcs": ["site", "template"]}, None, Exit),
        (None, cache.get_cert_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_cert_identifier, "no-match_no-match", {"retry": False}, lambda r: r is None, None),
        (None, cache.get_guest_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_guest_identifier, "no-match_no-match", {"retry": False}, lambda r: r is None, None),
        ("ensure_cache_guest1", cache.get_guest_identifier, "+16155551212", {}, lambda r: "6155551212" in r.phone, None),
        ("ensure_cache_guest1", cache.get_guest_identifier, "+16155551212", {"portal_id": "6f534424-855a-4cbe-a6e7-6c561f5c1b4e"}, None, Exit),
        (None, cache.get_client_identifier, "no-match_no-match", {}, None, Exit),
        (None, cache.get_client_identifier, "no-match_no-match", {"retry": False}, lambda r: r is None, None),
        ("ensure_cache_template", cache.get_template_identifier, "cencli_test_template", {"group": test_data["template_switch"]["group"]}, None, Exit),
        (None, cache.get_template_identifier, "no-match_no-match", {"retry": False}, lambda r: r is None, None),
    ]
)
def test_get_identifier_funcs(fixture: str | None, iden_func: Callable, query_str: str, kwargs: dict[str, str | bool], pass_condition: Callable | None, exception: Exception, request: pytest.FixtureRequest):
    if fixture:
        request.getfixturevalue(fixture)
    if exception:
        try:
            result = iden_func(query_str, **kwargs)
        except exception:
            ...
        else:
            log.error(f"test_get_identifier_funcs was expected to raise {exception}, but did not.")
    else:
        result = iden_func(query_str, **kwargs)
        assert pass_condition(result)


@pytest.mark.parametrize(
    "idx,incomplete,args",
    [
        [1, "cencli_test_group1", ("group",)],
        [2, "cencli_test_site", ("site",)],
        [3, "", ("ap",)],
        [4, "sit", ("arg1", "arg2")],
        [5, "grou", ("arg1", "arg2")],
    ]
)
def test_dev_kwarg_completion(ensure_cache_group1, ensure_cache_site1, idx: int, incomplete: str, args: tuple[str]):
    ctx = Context(Command("cencli move"), info_name="move", resilient_parsing=True)
    result = list(cache.dev_kwarg_completion(ctx, incomplete=incomplete, args=args))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

@pytest.mark.parametrize(
    "workspace,args,default,pass_condition",
    [
        ("not verified", ("arg1", "dev"), False, lambda r, _: r == "not verified"),
        (None, ("group",), True, lambda r, _: r == "default"),
        ("default", ("arg1", "test", "method"), False, lambda r, _: r == "default"),
        (None, ("arg1", "test", "method"), False, lambda r, _: r == "default"),
        (None, ("arg1", "arg2"), False, lambda r, _: r == "default"),
        ("default", ("arg1", "arg2"), False, lambda r, _: r == "default")
    ]
)
def test_workspace_name_callback(workspace: str, args: tuple[str], default: bool, pass_condition: Callable):
    ctx = Context(Command("cencli show config"), info_name="cencli show config", resilient_parsing=False)
    if args:  # pragma: no cover
        sys.argv = args
    with render.econsole.capture() as cap:
        result = common.workspace_name_callback(ctx, workspace, default=default)
    output = cap.get()
    assert pass_condition(result, output)

@pytest.mark.parametrize(
    "query_str,swack,swack_only,pass_condition",
    [
        (test_data["vsf_switch"]["name"], True, False, lambda r: r.name == test_data["vsf_switch"]["name"]),
        (test_data["vsf_switch"]["name"], False, True, lambda r: r.name == test_data["vsf_switch"]["name"]),
    ]
)
def test_get_dev_identifier(ensure_cache_vsf_stack, query_str: str, swack: bool, swack_only: bool, pass_condition: Callable):
    result = cache.get_dev_identifier(query_str, swack=swack, swack_only=swack_only)
    assert pass_condition(result)
