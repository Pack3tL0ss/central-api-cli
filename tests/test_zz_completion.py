"""We need this module to run near the end so cache is fully up to date for completion tests."""
from click import Command, Context
from typer.testing import CliRunner

from centralcli import cache
from centralcli.cli import app  # type: ignore # NoQA

from . import test_data

runner = CliRunner()
ctx = Context(Command("cencli reset"), info_name="reset", resilient_parsing=True)
ctx.params={'what': 'overlay', 'device': None, 'yes': None, 'debug': None, 'default': None, 'account': None}


# TODO most are hard-coded need to grab from test_data or dynamically from cache
# TODO most need to be tested with a value and an empty string, parameritize decorator...
def test_dev_completion(incomplete: str = "bsmt"):
    result = [c for c in cache.dev_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)

def test_dev_completion_case_insensitive(incomplete: str = "BSmT"):
    result = [c for c in cache.dev_completion(incomplete)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_ap_gw_completion(incomplete: str = "ant"):
    result = [c for c in cache.dev_ap_gw_completion(ctx=ctx, incomplete=incomplete, args=["show", "overlay", "summary"])]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

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

def test_template_group_completion(ensure_cache_group2, incomplete: str = "cencli"):
    result = [c for c in cache.template_group_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)

def test_template_completion(ensure_cache_template, incomplete: str = "cencli"):
    result = [c for c in cache.template_completion(incomplete, ("show", "templates",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_template_completion_empty_string(ensure_cache_template, incomplete: str = ""):
    result = [c for c in cache.template_completion(incomplete, ("show", "templates",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_template_completion(ensure_cache_group2, ensure_cache_template, incomplete: str = "cencl"):
    result = [c for c in cache.dev_template_completion(incomplete, ("show", "templates",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_template_completion_empty_string(ensure_cache_group2, ensure_cache_template, ensure_dev_cache_test_ap, incomplete: str = ""):
    result = [c for c in cache.dev_template_completion(incomplete, ("show", "templates",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

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

def test_mpsk_completion_partial_name(ctx=ctx, incomplete: str = test_data["mpsk_ssid"].capitalize()[0:-3]):
    _ = cache.get_mpsk_network_identifier(incomplete)
    result = [c for c in cache.mpsk_network_completion(ctx, incomplete)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_template_completion_partial_name(ensure_cache_template_by_name, incomplete: str = test_data["template"]["name"].capitalize()[0:-2]):
    result = list(cache.dev_template_completion(incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_group_dev_completion_partial_name(incomplete: str = test_data["switch"]["name"].capitalize()[0:-2]):
    result = list(cache.group_dev_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_group_dev_ap_gw_completion_partial_name(incomplete: str = test_data["ap"]["name"].capitalize()[0:-2]):
    result = list(cache.group_dev_ap_gw_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_client_completion_partial_name(incomplete: str = test_data["client"]["wireless"]["name"].capitalize()[0:-2]):
    _ = cache.get_client_identifier(incomplete)
    result = list(cache.client_completion(ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_client_completion(incomplete: str = test_data["ap"]["mac"]):
    result = list(cache.dev_client_completion(ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_client_completion_wireless(incomplete: str = test_data["ap"]["mac"]):
    ctx.params = {**ctx.params, "wireless": True, "wired": None}
    result = list(cache.dev_client_completion(ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])
    del ctx.params["wired"]
    del ctx.params["wireless"]

def test_dev_client_completion_wired(incomplete: str = test_data["switch"]["serial"]):
    ctx.params = {**ctx.params, "wireless": None, "wired": True}
    result = list(cache.dev_client_completion(ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])
    del ctx.params["wired"]
    del ctx.params["wireless"]

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

def test_remove_completion_site(incomplete: str = test_data["ap"]["ip"]):
    result = list(cache.remove_completion(ctx=ctx, incomplete=incomplete, args=("remove",)))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_remove_completion_dev(incomplete: str = test_data["ap"]["site"]):
    result = list(cache.remove_completion(ctx=ctx, incomplete=incomplete, args=("site",)))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_label_completion(ensure_cache_label1, incomplete: str = "cencli-test_label1"):
    result = list(cache.label_completion(ctx=ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_ws_completion(incomplete=""):
    result = list(cache.workspace_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_guest_completion(ensure_cache_guest1, incomplete="superlongemail@kabrew"):
    result = list(cache.guest_completion(ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_cert_completion(ensure_cache_cert, incomplete="cencli-tes"):
    result = list(cache.cert_completion(ctx, incomplete=incomplete))
    assert len(result) == 1
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_sub_completion(ensure_cache_subscription, incomplete="advanced-ap"):
    result = list(cache.sub_completion(ctx, incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_kwarg_completion_group(ensure_cache_group1, incomplete="cencli_test_group1"):
    result = list(cache.dev_kwarg_completion(ctx, incomplete=incomplete, args=("group",)))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_kwarg_completion_site(ensure_cache_site1, incomplete="cencli_test_site"):
    result = list(cache.dev_kwarg_completion(ctx, incomplete=incomplete, args=("site",)))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_kwarg_completion_ap(incomplete=""):
    result = list(cache.dev_kwarg_completion(ctx, incomplete=incomplete, args=("ap",)))
    assert len(result) > 0
    assert all([m.lower().replace("-", "_").startswith(incomplete.lower().replace("-", "_")) for m in [c if isinstance(c, str) else c[0] for c in result]])
