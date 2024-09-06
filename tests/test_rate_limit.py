import logging
import time
from rich import print
from . import common, log, test_data

central = common.central

log.setLevel(logging.DEBUG)

def skip_test_rate_limit():
    log._DEBUG = True
    b_reqs = [central.BatchRequest(central.get_switch_poe_details, test_data["rate_limit_switch"]["serial"], port=f"1/1/{p}") for p in range(1, 49)]
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
    assert len(b_reqs) == len([r for r in central.requests if r.ok and "poe_detail" in r.url])
    assert len (rate_limit_failures) == 0
    assert len(failed) < 2

if __name__ == '__main__':
    skip_test_rate_limit()
