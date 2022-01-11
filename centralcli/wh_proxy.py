#!/usr/bin/env python3

from typing import Any, Dict
from fastapi import FastAPI  # NoQA
from pydantic import BaseModel  # NoQA
from starlette.requests import Request  # NoQA
import uvicorn
from pathlib import Path
import base64
import hashlib
import hmac
from fastapi import FastAPI, Header, Request, Response
from pydantic import BaseModel
# from rich import print_json
import json
# from centralcli import config, log, cache


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import config, log, cache
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        import sys
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import config, log, cache  # type: ignore
    else:
        print(pkg_dir.parts)
        raise e


class WebhookResponse(BaseModel):
    result: str


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


app = FastAPI(
    title='Central CLI Webhook Proxy',
    docs_url='/api/docs',
    redoc_url="/api/redoc",
    openapi_url='/api/openapi/openapi.json',
    version="1.0",
)

def verify_header_auth(data: dict, svc: str, sig: str, ts: str, del_id: str):
    """
    This method ensures integrity and authenticity of the data
    received from Aruba Central via Webhooks
    """
    # Token obtained from Aruba Central Webhooks page as provided in the input
    token = config.tokens["webhook_token"]
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
    log.info('[NEW API RQST IN] {} Requesting -- {} -- Data via API'.format(request.client.host, route))


@app.get('/api/v1.0/alerts/{serial}')
async def alerts(request: Request, serial: str = None):
    log_request(request, f'fetching alerts details for {serial}')
    # TODO get wh from cache and send
    return await cache.get_hooks_by_serial(serial)


@app.post("/webhook", status_code=200)
async def webhook(
    data: WebhookData,
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
        log.error(f"Content too long ({content_length})")
        response.status_code = 400
        return {"result": "Content too long"}

    raw_input = await request.json()
    if x_central_signature:
        if verify_header_auth(
            raw_input,
            svc=x_central_service,
            sig=x_central_signature,
            ts=x_central_delivery_timestamp,
            del_id=x_central_delivery_id,
        ):
            # print_json(data=raw_input)
            await cache.update_hook_data_db(data.dict())
            return {"result": "ok"}
        else:
            log.error("Invalid signature", show=True)
    else:  # curl test
        log.error("No Signature", show=True)
        # print_json(data=raw_input)
        await cache.update_hook_data_db(data.dict())
        # print_json(data=cache.hook_data)
        return {"result": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.wh_port, log_level="info")