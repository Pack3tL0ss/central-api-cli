import aiohttp
import asyncio
from . import config, log
from .objects import DateTime
from .protobuf import monitoring_pb2, streaming_pb2, audit_pb2
# from yarl import URL
from rich.console import Console
from typing import Literal
import base64
from rich import inspect


console = Console(emoji=False)
econsole = Console(stderr=True)

FieldType = Literal["mac", "ip", "essid"]
mac_fields = ["macaddr", "peer_mac", "local_mac", "radio_mac", "interface_mac"]
ip_fields = ["ip_address", "src_ip", "dst_ip"]
strip_fields = ["customer_id"]
iden_fields = ["device_id"]

# TODO BASE URL for wss is hard coded
# TODO need to convert mac / ip / essid fields as described in readme of https://github.com/aruba/central-python-workflows/tree/main/streaming-api-client

async def _decode(data, field_type: FieldType = "mac"):
    try:
        _data = base64.b64decode(data)
        if field_type == "essid":
            return _data
        if field_type == "ip":
            return '.'.join('%d' % byte for byte in _data)

        return ':'.join('%02x' % ord(byte) for byte in _data)
    except Exception as e:
        log.exception(f"Exception while attempting to decode {field_type} in wss payload.  \n{e}")
        return data

async def _clean_data(data):
    # [attr for attr in data.__dir__() if not attr.startswith("_") and not callable(getattr(data, attr)) and getattr(data, attr)]
    inspect(data)

async def follow_event_logs():
    headers = {"Authorization": config.wss_key, "Topic": "monitoring"}
    if config.username:
        headers["UserName"] = config.username

    monitoring_data = monitoring_pb2.MonitoringInformation()
    base_url = 'wss://internal-ui.central.arubanetworks.com'  #f'wss://{URL(config.base_url).host}'  # TODO makes sense for config.url to returl URL object.  All urls should be URL object
    session = aiohttp.ClientSession(base_url=base_url, headers=headers)

    try:
        async with session.ws_connect('/streaming/api') as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    stream_data = streaming_pb2.MsgProto()
                    stream_data.ParseFromString(msg.data)

                    monitoring_data = monitoring_pb2.MonitoringInformation()
                    monitoring_data.ParseFromString(stream_data.data)
                    asyncio.create_task(_clean_data(monitoring_data))
                    console.print(f"-- {DateTime(stream_data.timestamp / 1000 / 1000 / 1000)} --\n{monitoring_data}")
                    ...
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    econsole.print(msg.data)
                    break
                else:
                    econsole.print(f"Got unexpected type {msg.type}")

    except aiohttp.WSServerHandshakeError as e:
        econsole.print(f"[dark_orange3]\u26a0[/]  {e.message}  Make sure you are subscribed to monitoring logs in Central UI")


async def follow_audit_logs():
    headers = {"Authorization": config.wss_key, "Topic": "audit"}
    if config.username:
        headers["UserName"] = config.username

    audit_data = audit_pb2.audit_message()
    base_url = 'wss://internal-ui.central.arubanetworks.com'
    session = aiohttp.ClientSession(base_url=base_url, headers=headers)

    try:
        async with session.ws_connect('/streaming/api') as ws:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.BINARY:
                    stream_data = streaming_pb2.MsgProto()
                    stream_data.ParseFromString(msg.data)

                    audit_data = audit_pb2.audit_message()
                    audit_data.ParseFromString(stream_data.data)
                    console.print(f"-- {DateTime(stream_data.timestamp / 1000 / 1000 / 1000)} --\n{audit_data}")
                    ...
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    econsole.print(msg.data)
                    break
                else:
                    econsole.print(f"Got unexpected type {msg.type}")

    except aiohttp.WSServerHandshakeError as e:
        econsole.print(f"[dark_orange3]\u26a0[/]  {e.message}  Make sure you are subscribed to audit logs in Central UI")
