"""We need this module to run near the end so cache is fully up to date for completion tests."""
from centralcli.cli import app  # type: ignore # NoQA
from typer.testing import CliRunner
from centralcli import cache
from click import Context, Command
from . import test_data


runner = CliRunner()
ctx = Context(Command("cencli reset"), info_name="reset", resilient_parsing=True)
ctx.params={'what': 'overlay', 'device': None, 'yes': None, 'debug': None, 'default': None, 'account': None}


# TODO most are hard-coded need to grab from test_data or dynamically from cache
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

def test_dev_site_completion(incomplete: str = "barn"):
    result = [c for c in cache.dev_site_completion(incomplete, ("show", "vlans",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_gw_switch_completion(incomplete: str = test_data["switch"]["name"].swapcase()):
    result = [c for c in cache.dev_gw_switch_completion(ctx, incomplete, ("show", "firmware", "device"))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_gw_switch_site_completion(incomplete: str = "barn"):
    result = [c for c in cache.dev_gw_switch_site_completion(incomplete, ("show", "vlans",))]
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
    result = list(cache.client_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_event_log_completion_pytest(incomplete: str = "pyte"):
    result = list(cache.event_log_completion(incomplete=incomplete))
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])