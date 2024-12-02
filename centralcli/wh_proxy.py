#!/usr/bin/env python3

import base64
import hashlib
import hmac
import json
import sys
from datetime import datetime as dt
from pathlib import Path
from typing import List, Literal, Optional, Union

import uvicorn
from fastapi import FastAPI, Header, Request, Response, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from rich import print_json  # NoQA
from starlette.requests import Request  # NoQA
from starlette.responses import FileResponse

# TODO should have a periodic call to branch_health (every 6 hours etc) to verify cache
# TODO ensure script handles network down / unreachable state (for the script to communicate externally)
# TODO keep track of request count.
# TODO log to wh_proxy speciffic log file, keep seperate from normal cencli log file
# FIXME make sure refresh_token logic will skip token paste. given it runs in background / check for tty

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import MyLogger, cache, central, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import MyLogger, cache, central, config  # type: ignore
    else:
        print(pkg_dir.parts)
        raise e

log_file = Path(config.dir / "logs" / f"{Path(__file__).stem}.log")
log_file.parent.mkdir(exist_ok=True)
log = MyLogger(log_file, debug=config.debug, show=True, verbose=config.debugv)
print(f"Web Hook Proxy logging to {log_file}")


# LOGGING_CONFIG: dict[str, Any] = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "default": {
#             "()": "uvicorn.logging.DefaultFormatter",
#             "fmt": "%(levelprefix)s %(message)s",
#             "use_colors": None,
#         },
#         "access": {
#             "()": "uvicorn.logging.AccessFormatter",
#             "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
#         },
#     },
#     "handlers": {
#         "default": {
#             "formatter": "default",
#             "class": "logging.handlers.RotatingFileHandler",
#             "level": "INFO" if not DEBUG else "DEBUG",
#             "filename": LOG_FILE.absolute(),
#             "maxBytes": 250_000,
#             "backupCount": 5
#         },
#         "access": {
#             "formatter": "access",
#             "class": "logging.handlers.RotatingFileHandler",
#             "level": "INFO" if not DEBUG else "DEBUG",
#             "filename": LOG_FILE.absolute(),
#             "maxBytes": 250_000,
#             "backupCount": 5
#         },
#     },
#     "loggers": {
#         "uvicorn": {"handlers": ["default"], "level": "INFO" if not DEBUG else "DEBUG", "propagate": False},
#         "uvicorn.error": {"level": "INFO" if not DEBUG else "DEBUG"},
#         "uvicorn.access": {"handlers": ["access"], "level": "INFO" if not DEBUG else "DEBUG", "propagate": False},
#     },
# }
# update and pass as param to uvicorn.run to send logs to our file "log_config=LOGGING_CONFIG"

class HookResponse(BaseModel):
    result: str
    updated: bool

    class Config:
        schema_extra = {
            "example": {"result": "OK", "updated": True,}
        }


class HookResponseTooBig(HookResponse):
    class Config:
        schema_extra = {
            "example": {"result": "Content too long", "updated": False}
        }


class HookResponseTokenFail(BaseModel):
    result: str
    updated: bool

    class Config:
        schema_extra = {
            "example": {"result": "Unauthorized", "updated": False}
        }
class BranchResponse(BaseModel):
    id: str
    ok: bool
    alert_type: str
    device_id: str
    state: Literal["Open", "Close"]
    text: str
    timestamp: Optional[int]

    class Config:
        schema_extra = {
            "example": {
                    "id": "CNF1234567_init",
                    "ok": False,
                    "alert_type": "BH_POLL_UPLK_OR_TUN_DOWN",
                    "device_id": "CNF1234567",
                    "state": "Open",
                    "text": "sdbranch1:7008:uplk_g1694_v3250_inet::vpnc1:uplk_g1694_v3250_inet found to be down at hook proxy startup",
                    "timestamp": int(dt.now().timestamp())
            }
        }


# Not Used for now would need to ensure all possible fields
class WebhookData(BaseModel):
    id: str
    timestamp: int
    nid: int
    alert_type: str
    severity: str
    details: dict
    description: str
    setting_id: str
    state: str
    webhook: str
    cluster_hostname: str = None
    operation: str = None
    device_id: str = None
    text: str = None


wh_resp_schema = {
    401: {"model": HookResponseTokenFail},
    413: {"model": HookResponseTooBig}
}


app = FastAPI(
    title='Central CLI Webhook Proxy',
    docs_url='/api/docs',
    redoc_url="/api/redoc",
    openapi_url='/api/openapi/openapi.json',
    version="1.0",
)

app.mount("/static", StaticFiles(directory=f"{Path(__file__).parent}/static"), name="static")


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
        swagger_favicon_url="/static/favicon.ico",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
    )


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )

def _default_response(serial: str) -> dict:
    return {
            "id": f"{serial}_init",
            "ok": True,
            "alert_type": "OK",
            "device_id": serial,
            "state": "Close",
            "text": "No alerts for this gateway.",
            "timestamp": int(dt.now().timestamp())
        }

def _hook_response(data: dict) -> dict:
    return {
            "id": data.get("id"),
            "ok": False,
            "alert_type": data.get("alert_type"),
            "device_id": data.get("device_id"),
            "state": data.get("state"),
            "text": data.get("text"),
            "timestamp": data.get("timestamp")
        }


def _batch_resp_all_ok(responses: List[Response]) -> bool:
    if not all(r.ok for r in responses):
        _ = [log.error(str(r), show=True) for r in responses]
        log.critical("hook proxy exiting due to error.", show=True)
        return False

    return True


def get_current_branch_state():
    if config.account not in ["central_info", "default"]:
        log.info(f"hook_proxy is using alternate account '{config.account}'", show=True)
    _reqs = [
        central.BatchRequest(central.get_branch_health),
        central.BatchRequest(central.get_devices, "gateways"),
        central.BatchRequest(central.get_groups_properties),
    ]
    health_resp, devs_resp, gr_resp = central.batch_request(_reqs)

    if not _batch_resp_all_ok([health_resp, devs_resp, gr_resp]):
        sys.exit(1)

    log.info(f"Hook Proxy db init... {gr_resp.rl}", show=True)

    # In AOS10 a GW with WLAN persona is GWNetworkRole, Those are removed below with get_gw_tunnels check
    br_groups = [
        br["group"] for br in gr_resp.output
        if "Gateways" in br["properties"].get("AllowedDevTypes", []) and not br["properties"].get("GwNetworkRole", "ERR").startswith("VPNC")
    ]

    br_bad = [
        d["name"] for d in health_resp.output
        if d["wan_tunnels_down"] > 0 or d["wan_uplinks_down"] > 0
    ]

    devs = devs_resp.output
    # FIXME this logic would mark all gateways in the site as having issue, if more than 1
    gw_maybe_bad = {
            br: [
                gw["serial"]
                for gw in devs if gw["site"] == br and gw["group_name"] in br_groups
            ]
            for br in br_bad
    }
    _reqs = [
        central.BatchRequest(central.get_gw_tunnels, s)
        for s in [ser for _, serials in gw_maybe_bad.items() for ser in serials]
    ]
    batch_resp = central.batch_request(_reqs)
    if not _batch_resp_all_ok(batch_resp):
        sys.exit(1)

    down_tunnels = {s: [] for s in [ser for _, serials in gw_maybe_bad.items() for ser in serials]}
    for idx, serial in enumerate(down_tunnels.keys()):
        tuns = batch_resp[idx].output["tunnels"]
        if tuns:
            down_tunnels[serial] += [{"name": t["name"], "error": t["last_down_reason"]} for t in tuns if t["status"].upper() != "UP"]

    alerts_now = [
        {
            "id": f"{k}_init",
            "ok": False,
            "alert_type": v[-1]["error"],
            "device_id": k,
            "state": "Open",
            "text": f"{v[-1]['name']}, gw has {len(v)} tunnels down at hook proxy startup",
            "timestamp": int(dt.now().timestamp())
        }
        for k, v in down_tunnels.items() if v
    ]


    # TODO hook_data to it's own DB file
    cache.HookDataDB.truncate()
    cache_upd_resp = central.request(cache.update_hook_data_db, alerts_now)
    log.debug(f"Hook cache update response: {cache_upd_resp}")

    log.info(f"Initial state of HookDataDB set.  {len(alerts_now)} gateways with WAN issues.", show=True)


def verify_header_auth(data: dict, svc: str, sig: str, ts: str, del_id: str):
    """
    This method ensures integrity and authenticity of the data
    received from Aruba Central via Webhooks
    """
    # Token obtained from Aruba Central Webhooks page as provided in the input
    token = config.tokens.get("webhook_token")
    if token:
        log.warning(
            "Deprication Warning: webhook_token is depricated and will be removed in a future release. webhook now has it's own key under the account, refer to documentation to adjust config.yaml",
            show=True
        )
    else:
        token = config.webhook.token
    token = token.encode('utf-8')

    # Construct HMAC digest message
    data = json.dumps(data)
    sign_data = f"{data}{svc}{del_id}{ts}"
    sign_data = sign_data.encode('utf-8')

    # Find Message signature using HMAC algorithm and SHA256 digest mod
    dig = hmac.new(token, msg=sign_data, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(dig).decode()

    # Verify if the signature received in header is same as the one found using HMAC
    if sig == signature:
        return True
    return False


def log_request(request: Request, route: str):
    log.info('[NEW API RQST IN] {} {} via API'.format(request.client.host, route))

async def check_cache_entry(data: dict) -> Union[list, None]:
    """Querries hook db when webhook arrives, determine if entry exists

    If the entry exists, but is based on startup poll the device is querried to verify
    state before sending cache update.  If gw no longer has issues, the id is changed
    to match the id assigned at startup so the update_cache_db will result in a removal.

    Args:
        data (dict): The webhook post content.

    Returns:
        Union[list, None]: returns list of cache doc_ids returned from cache update method
            if an update was necessary, None if no update performed (i.e. new hook for branch)
            already in cache.
    """
    # -- // match based on wh id \\ --
    match = cache.HookDataDB.get(
        (cache.Q.id == data["id"])
    )
    if match is not None:
        # wh id matched Remove entry if it's close.  If it's open ignore we already have a cache entry with that id
        if data["state"] != "Open":
            log.info(f"[WH CLEAR] {data['text']} - Removed from cache, tunnel restored.")
            return await cache.update_hook_data_db(_hook_response(data))
        else:  # shouldn't really happen webhook with matching id and Open state
            log.error(f"[WH INGORE ADD] {data['text']} - gw already in cache.", show=True)
            return

    # -- // match id assigned on startup based on get_branch_health \\ --
    match = cache.HookDataDB.get(
        (cache.Q.id == f"{data['device_id']}_init")
    )
    if match is None:
        # No init entry, Update cache with new entry based on wh, ignore if it's a close msg as no entry exists
        if data["state"] == "Open":
            log.info(f"[WH ADD] Adding {data['device_id']} based on alert: {data['text']}")
            return await cache.update_hook_data_db(_hook_response(data))
        else:
            log.error(f"[WH INGORE CLEAR] {data['text']} - gw was not in cache.", show=True)
            return
    else:
        # New alert wh alert for gw already in cache from init, do not send an update
        # prevents adding duplicate entry for same gw
        # TODO update existing entry with alert_type text timestamp from wh
        if data["state"] == "Open":
            log.info(f"[WH INGORE ADD] {data['text']} gw already in cache.")
            return


        res = await central._request(central.get_gw_tunnels, data["device_id"])
        if not res:
            log.error(f"[WH IGNORE CLEAR] Error attempting to verify tunnels for {data['device_id']}")  # [{res.status}]{res.url}: {res.error}.")
            log.error("DB may drift from reality :(")
            return

        tuns = res.output["tunnels"]
        down_tunnels = [{"name": t["name"], "error": t["last_down_reason"]} for t in tuns if t["status"].upper() != "UP"]
        if down_tunnels:
            log.info(f"[WH INGORE CLEAR] {data['text']} - gw still has {len(down_tunnels)} tunnels down.")
            return
        else:
            data["id"] = f"{data['device_id']}_init"
            if data["state"] != "Close":
                log.error(f"DEV NOTE: Expected to only see state: Close in check_cache_entry.\n{data}")

            log.info(f"[WH CLEAR] {data['text']} - Removed from cache, all tunnels restored.")
            return await cache.update_hook_data_db(_hook_response(data))

@app.get('/favicon.ico', include_in_schema=False)
async def _favicon():
    return FileResponse(Path(__file__).parent / "static/favicon.ico")


@app.get('/api/v1.0/alerts', response_model=List[BranchResponse], )
async def alerts(request: Request,):
    log_request(request, 'fetching All Active Alerts')
    try:
        return cache.hook_active
    except Exception as e:
        log.exception(e)


@app.get('/api/v1.0/alerts/{serial}', response_model=BranchResponse, )
async def alerts_by_serial(request: Request, serial: str = None):
    log_request(request, f'fetching alerts details for {serial}')
    try:
        cache_entry = await cache.get_hooks_by_serial(serial)
        return cache_entry or _default_response(serial)
    except Exception as e:
        log.exception(e)


@app.post("/webhook", status_code=200, response_model=HookResponse, responses=wh_resp_schema)
async def webhook(
    data: dict,
    request: Request,
    response: Response,
    content_length: int = Header(...),
    x_central_service: str = Header(None),
    x_central_signature: str = Header(None),
    x_central_delivery_timestamp: str = Header(None),
    x_central_delivery_id: str = Header(None),
):
    updated = False
    if content_length > 1_000_000:
        # To prevent memory allocation attacks
        log.error(f"Incoming wh ignored, Content too long:  content_length: ({content_length})")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"result": "Content too long", "updated": False}
        )

    # test webhook from central lacks an id... add it to avoid validation error
    if data["nid"] == 1250:
        data["id"] = data.get("id", "TEST-HOOK-IGNORE")

    raw_input = await request.json()
    if x_central_signature:
        if verify_header_auth(
            raw_input,
            svc=x_central_service,
            sig=x_central_signature,
            ts=x_central_delivery_timestamp,
            del_id=x_central_delivery_id,
        ):
            if COLLECT:
                raw_file = config.outdir / "wh_raw.json"
                with raw_file.open("a") as rf:
                    rf.write(json.dumps(data))
                updated = await check_cache_entry(data)
        else:
            log.error("POST from Central has invalid signature (check webhook token in config), ignoring", show=True)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"result": "Unauthorized", "updated": False}
            )
            # raise HTTPException(status_code=401, detail={"result": "Unauthorized", "updated": False})
    else:  # TODO this is to facilitate testing with curl and the like, should be removed before prod
        log.error("Message received with no signature, assuming test", show=True)
        updated = await check_cache_entry(data)

    return {
            "result": "ok",
            "updated": True if updated else False
        }


if __name__ == "__main__":
    if "--collect" in sys.argv or "-c" in sys.argv:
        COLLECT = True
        flag = "--collect" if "--collect" in sys.argv else "-c"
        _ = sys.argv.pop(sys.argv.index(flag))
        log.info("Collection mode enabled.")
    else:
        COLLECT = False

    port = config.wh_port if len(sys.argv) == 1 or not sys.argv[1].isdigit() else int(sys.argv[1])
    _ = get_current_branch_state()
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except Exception as e:
        log.exception(f"{e.__class__.__name__}\n{e}", show=True)
