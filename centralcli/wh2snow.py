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
from rich import print
from starlette.requests import Request  # NoQA
from starlette.responses import FileResponse

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import MyLogger, cache, central, config
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        import sys
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import MyLogger, cache, central, config  # type: ignore
    else:
        print(pkg_dir.parts)
        raise e

def init_logs():
    log_file = Path(config.dir / "logs" / f"{Path(__file__).stem}.log")
    log_file.parent.mkdir(exist_ok=True)
    log = MyLogger(log_file, debug=config.debug, show=True, verbose=config.debugv)
    print(f"Web Hook Proxy logging to [cyan]{log_file}[/]")

    return log


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
    title='Central CLI Webhook-2-SNOW Proxy',
    # docs_url='/api/docs',
    # redoc_url="/api/redoc",
    # docs_url=None,
    # redoc_url=None,
    # openapi_url='/api/openapi/openapi.json',
    version="1.0",
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


def verify_header_auth(data: dict, svc: str, sig: str, ts: str, del_id: str):
    """
    This method ensures integrity and authenticity of the data
    received from Aruba Central via Webhooks
    """
    # Token obtained from Aruba Central Webhooks page as provided in the input
    token = config.tokens["webhook_token"]
    log.info(f'verifying token: {token}')
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
            # TODO REMOVE temp to collect some example WebHooks to modify for test
            raw_file = config.outdir / "wh_raw.json"
            raw_file.write_text(json.dumps(data))
            # updated = await check_cache_entry(data)
        else:
            log.error("POST from Central has invalid signature (check webhook token in config), ignoring", show=True)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"result": "Unauthorized", "updated": False}
            )
            # raise HTTPException(status_code=401, detail={"result": "Unauthorized", "updated": False})
    else:  # TODO this is to facilitate testing with curl and the like, should be removed before prod
        log.error("Message received with no signature, assuming test", show=True)
        # updated = await check_cache_entry(data)

    return {
            "result": "ok",
            # "updated": True if updated else False
        }


if __name__ == "__main__":
    log = init_logs()
    port = config.wh_port if len(sys.argv) == 1 or not sys.argv[1].isdigit() else int(sys.argv[1])
    # _ = get_current_branch_state()
    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info" if not config.debug else "debug")
    except Exception as e:
        log.exception(f"{e.__class__.__name__}\n{e}", show=True)
