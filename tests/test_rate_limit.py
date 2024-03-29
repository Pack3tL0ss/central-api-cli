import logging
from pathlib import Path
# from typer.testing import CliRunner

# from cli import app  # type: ignore # NoQA
# import json
# from pathlib import Path

# from . import TEST_DEVICES

# runner = CliRunner()

# test_dev_file = Path(__file__).parent / 'test_devices.json'
# if test_dev_file.is_file():
#     TEST_DEVICES = json.loads(test_dev_file.read_text())
import sys
from pendulum import time
try:
    from centralcli import (
        central, log
    )
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent.parent / "centralcli"
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import (
            central, log
        )
    else:
        print(pkg_dir.parts)
        raise e

log.setLevel(logging.DEBUG)
from rich import print
import time

def test_rate_limit():
    log._DEBUG = True
    b_reqs = [central.BatchRequest(central.get_switch_poe_details, "TW0BKNF063", port=f"1/1/{p}") for p in range(1, 49)]
    start = time.perf_counter()
    b_resp = central.batch_request(b_reqs)
    end = time.perf_counter() - start
    _ = [print(log) for log in central.rl_log]
    _ = [print(f"{r.ts} tr:{r.remain_day} psr: {r.remain_sec} ({r.reason}): [{r.method}] {r.url}") for r in central.requests]
    print(f"Time Elapsed for all calls: {end:.2f}")
    print(b_resp[-1].rl.text)
    failed = [r for r in central.requests if not r.ok]
    successful_retries = [r for f in failed for r in central.requests if r.ok and r.url == f.url]
    rate_limit_failures = [r for r in failed if r.status == 429]
    print(f'Number of requests: {len(b_reqs)}, Number of Failures: {len(failed)}, Number failures successful on retry: {len(successful_retries)}')
    if rate_limit_failures:
        print(f"[bright_red]!![/] Rate Limit Failures {len(rate_limit_failures)}")
    assert len(failed) == len(successful_retries)
    assert len(b_reqs) == len([r for r in central.requests if r.ok])
    assert len (rate_limit_failures) == 0
    assert len(failed) < 2

if __name__ == '__main__':
    test_rate_limit()
