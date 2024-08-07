#!/usr/bin/env python3
from __future__ import annotations
import base64
import hashlib
import hmac
import json
import sys
from datetime import datetime as dt
from pathlib import Path
from typing import List, Literal, Optional

import uvicorn
from fastapi import FastAPI, Header, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from rich import print
from starlette.requests import Request  # NoQA
import aiohttp
import asyncio

# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import MyLogger, cache, central, config, models, exceptions
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        import sys
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import MyLogger, cache, central, config, models, exceptions  # type: ignore
    else:
        print(pkg_dir.parts)
        raise e

def init_logs():
    log_file = Path(config.dir / "logs" / f"{Path(__file__).stem}.log")
    log_file.parent.mkdir(exist_ok=True)
    log = MyLogger(log_file, debug=config.debug, show=True, verbose=config.debugv)
    print(f"Web Hook Proxy logging to [cyan]{log_file}[/]")

    return log

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

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
    id: Optional[str] = Field(default_factory=str)
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
    docs_url='/api/docs',
    redoc_url="/api/redoc",
    openapi_url='/api/openapi/openapi.json',
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


class Hook2Snow:
    def __init__(self) -> None:
        self.created: List = []
        self.fail_count: int = 0
        self.total_hooks_in: int = 0

    async def get_current_alerts(self):
        """Gather current alerts from Central REST API

        This is ran on startup to collect any alerts that may have triggered
        while script was not running.

        Gathers last 30 days of alerts
        """
        # TODO need to see if there is a way to poll SNOW to see if incident already exists for any open alerts found
        resp = await central._request(central.get_alerts)
        if not resp:
            log.error(f"Unable to gather alerts from Central REST API\n{resp}")
        else:
            return [models.WebHook(**{**data, **{"text": data.get("text", data.get("description"))}}) for data in resp.output]

    async def post2snow(self, data: dict) -> aiohttp.ClientResponse | None:
        # success response = 201 for both create and update
        # need to cache incident_num = res payload["result"]["display_value"].replace("Incident: ", "")
        # include "u_servicenow_number": incident_num in subsequent post to update existing incident
        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(str(config.snow.incident_url), json=data)
                return response
        except Exception as e:
            log.error(f'Exception during post to snow {e.__class__.__name__}', show=True)
            log.exception(e)

    async def format_payload(self, data: dict) -> models.SnowCreate | models.SnowUpdate:
        snow_data = {}
        data = models.WebHook(data)
        if data.state == "Open":
            snow_data["u_assignment_group"] = config.snow.assignment_group
            snow_data["u_short_description"] = "".join(data.alert_type[0:161])
            snow_data["u_description"] = data.description
            snow_data["work_notes"] = "\n".join([f'{k}: {v}' for k, v in data.dict().items()])
            snow_data["u_raised_severity"] = data.severity
            snow_data["u_state"] = "New"
            out_data = models.SnowCreate(**snow_data)
        else:
            snow_cache = cache.get_hook_id(data.id)  # TODO create cache
            snow_data["u_servicenow_number"] = snow_cache.u_servicenow_number
            snow_data["u_state"] = "Resolved"
            out_data = models.SnowUpdate(**snow_data)
        return out_data

    async def process_hook(self, data: dict):
        word = "create" if data.get("state").lower() == "open" else "update"
        payload = await self.format_payload(data)
        for _ in range(0, 2):
            response = await self.post2snow(data=payload.dict())
            if response is not None:
                break  # None indicates Exception during POST attempt
            else:
                log.warning(f'Snow incident {word} failed... retrying.', show=True)

        if response is None:
                log.error(f'Snow incident {word} failed. Giving Up', show=True)
                self.fail_count += 1
        elif response.status != 201:
            log.error(f'SNOW incident {word} failed [{response.status}] {response.reason}', show=True)
            self.fail_count += 1
        else:
            res_payload = await response.json()
            res_model = models.SnowResponse(**res_payload)
            self.created += [res_model.u_servicenow_number]
            _ = await cache.update_hook_data_db(res_model.dict())  # TODO should we strip_none here?


    async def verify_header_auth(self, data: dict, svc: str, sig: str, ts: str, del_id: str):
        """
        This method ensures integrity and authenticity of the data
        received from Aruba Central via Webhooks
        """
        # Token obtained from Aruba Central Webhooks page as provided in the input
        token = config.webhook.token
        token = token.encode('utf-8')

        # strip id injected below to prevent validation error so hash is correct on test wh
        if data["nid"] == 1250:
            del data["id"]

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


    async def snow_token_refresh(self, refresh_token: str = None) -> bool:

        forms = []
        for tok in [config.snow.token.cache, config.snow.token.config]:
            if tok is None:
                continue
            # Create a FormData object
            _form = aiohttp.FormData()

            # Add some data to the form
            _form.add_field('grant_type', 'refresh_token')
            _form.add_field('client_id', config.snow.client_id)
            _form.add_field('client_secret', config.snow.client_secret)
            _form.add_field('refresh_token', tok.refresh)
            forms += [_form]

        tok_updated = False
        for form in forms:
            # Send the form data to the server
            async with aiohttp.ClientSession() as session:
                response = await session.post(str(config.snow.refresh_url), data=form)

            # Check the response status code
            if response.status == 200:
                # The form was submitted successfully
                log.info('SNOW token refresh success')
                new_tokens = await response.text()
                if not new_tokens:
                    raise Exception("SNOW token refresh refresh returned 200, but lacked text.")

                write_res = config.snow.tok_file.write_text(new_tokens)
                tok_updated = True

                if not write_res:
                    raise Exception(f"SNOW token refresh write to file ({config.snow.tok_file.name}) appears to have failed.")
                break
            elif response.status == 401:
                continue  # try again with tokens from config  # verify it's a 401 could be 404
            else:
                # The form was not submitted successfully
                log.error(f'SNOW token refresh failed [{response.status}] {response.reason}', show=True)
                raise exceptions.RefreshFailedException(f"SNOW Token refresh failure. [{response.status}] {response.reason}")

        return tok_updated

    @app.post("/webhook", status_code=200, response_model=HookResponse, responses=wh_resp_schema)
    async def webhook(
        self,
        data: dict,  # models.WebHook
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
            if await self.verify_header_auth(
                raw_input,
                svc=x_central_service,
                sig=x_central_signature,
                ts=x_central_delivery_timestamp,
                del_id=x_central_delivery_id,
            ):
                # TODO REMOVE temp to collect some example WebHooks to modify for test
                raw_file = config.outdir / "wh_raw.json"
                with raw_file.open("a") as f:
                    f.write(json.dumps(data))
                log.info(f'Recieved webhook: {data.get("alert_type", "err")}: {data.get("text", "err")}')
                # asyncio.create_task(self.process_data(data))
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
                "updated": True  #  if updated else False
            }

    async def startup(self) -> List[models.WebHook] | None:
        tok_updated, current_alerts = await asyncio.gather(self.snow_token_refresh(), self.get_current_alerts())
        # TODO verify any closed alerts don't have open entry in cache, verify snow has incident for any open alerts
        return current_alerts


if __name__ == "__main__":
    log = init_logs()  # FIXME logs are still sent to generic cencli log file
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif config.webhook:
        port = config.webhook.port
    else:
        port = 9143

    h2s = Hook2Snow()
    # TODO need to get status of alerts with central.get_alerts on start
    # need to determine if there is a way to pull all open incidents from snow at start
    # to rationalize snow with what is pulled from central.get_alerts
    # ... close any incidents that are open in snow but state:close from central.get_alerts
    # When grabbing from central.get_alerts use wh_model = WebHook(**{**data, **{"text": data.get("text", data.get("description"))}})
    # as the text field isn't supplied with the response from the REST endpoint.
    try:
        current_alerts = asyncio.run(h2s.startup())
        open_alerts = len([a for a in current_alerts if a.state == "Open"])
        # closed_alerts = len(current_alerts) - open_alerts
        print(f'Open Alerts from last 30 days: {open_alerts}')
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info" if not config.debug else "debug")
    except Exception as e:
        log.exception(f"{e.__class__.__name__}\n{e}", show=True)
