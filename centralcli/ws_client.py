# import asyncio
import base64
from typing import Literal

import aiohttp
from google.protobuf import json_format
from rich import inspect
from rich.console import Console

from centralcli import render
from centralcli.cache import api
from centralcli.models.config import WSSConfig
from centralcli.typedefs import LogType

from . import config, log, utils
from .objects import DateTime
from .protobuf import audit_pb2, monitoring_pb2, streaming_pb2

console = Console(emoji=False)
econsole = Console(stderr=True)

FieldType = Literal["mac", "ip", "essid"]
mac_fields = ["macaddr", "peer_mac", "local_mac", "radio_mac", "interface_mac"]
ip_fields = ["ip_address", "src_ip", "dst_ip"]
strip_fields = ["customer_id"]
iden_fields = ["device_id"]

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

async def _clean_mon_data(data: monitoring_pb2.MonitoringInformation):
    # [attr for attr in data.__dir__() if not attr.startswith("_") and not callable(getattr(data, attr)) and getattr(data, attr)]
    inspect(data)
    # if data.client_stats:
    #     client_stats = [{k: v if k != "macaddr" else {"addr": utils.Mac(v["addr"]).cols}} for inner in list(data.client_stats) for k, v in inner.items()]


async def _render_mon_data(data: monitoring_pb2.MonitoringInformation):
    console.print(DateTime(data.timestamp / 1000 / 1000 / 1000))
    for ap in data.aps:
        ...
    for neighbor in data.device_neighbours:
        ...
    for tunnel in data.ike_tunnels:
        ...
    for iface in data.interfaces:
        ...
    for gw in data.mobility_controllers:
        ...
    for network in data.networks:
        ...
    for n in data.notification:
        ...
    for r in data.radios:
        ...
    for event in data.rogue_events:
        ...
    for s in data.swarms:
        ...
    for stack in data.switch_stacks:
        ...
    for vlan in data.switch_vlan_info:
        ...
    for s in data.switches:
        ...
    for t in data.tunnels:
        ...
    for uplink in data.uplinks:
        ...
    for vap in data.vaps:
        ...
    for vlan in data.vlans:
        ...
    for v in data.vsx:
        ...
    for event in data.wids_events:
        ...
    for client in data.wired_clients:
        ...
    for client in data.wireless_clients:
        ...


# TODO base_url will be required once not hardcoded, need to determine if base-url can be determined reliably from central base and provide config option for it.
async def follow_logs(wss_config: WSSConfig, log_type: LogType = "event"):
    base_url = wss_config.base_url  # TODO makes sense for config.url to returl URL object.  All urls should be URL object

    if log_type == "event":
        pb_data = monitoring_pb2.MonitoringInformation()
        parser = monitoring_pb2.MonitoringInformation
        topic = "monitoring"
    else:  # audit
        pb_data = audit_pb2.audit_message()
        parser = audit_pb2.audit_message
        topic = "audit"

    resp = await api.other.validate_wss_key(base_url.replace(r"wss://", r"https://"), wss_config.key)  # TODO need to cache wss key
    if not resp.ok:
        log.error("Unable to validate wss key.", caption=True)
        render.display_results(resp, exit_on_fail=True)
        # TODO wss key needs to be stored for future use

    wss_key = resp.raw["token"]

    headers = {"Authorization": wss_key, "Topic": topic}
    if config.username:
        headers["UserName"] = config.username
    session = aiohttp.ClientSession(base_url=base_url, headers=headers)

    try:
        async with session as s:
            async with s.ws_connect('/streaming/api') as ws:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.BINARY:
                        stream_data = streaming_pb2.MsgProto()
                        stream_data.ParseFromString(msg.data)

                        pb_data = parser()
                        pb_data.ParseFromString(stream_data.data)
                        # asyncio.create_task(_clean_data(monitoring_data))
                        console.print(f"-- {DateTime(stream_data.timestamp / 1000 / 1000 / 1000)} --\n{pb_data}")
                        ...
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        econsole.print(msg.data)
                        break
                    else:
                        econsole.print(f"Got unexpected type {msg.type}")

    except aiohttp.WSServerHandshakeError as e:
        econsole.print(f"[dark_orange3]\u26a0[/]  {e.message}  Make sure you are subscribed to monitoring logs in Central UI")
