# pragma: exclude file  Still a WIP
import base64
from functools import lru_cache
import ipaddress
from itertools import groupby
from typing import Literal

import aiohttp
from google.protobuf.json_format import MessageToDict
from rich import inspect
from rich.console import Console

from centralcli import render
from centralcli.cache import CacheDevice, api
from centralcli.models.config import WSSConfig
from centralcli.typedefs import LogType

from . import config, log, utils, cache
from .objects import DateTime
from .protobuf import audit_pb2, monitoring_pb2, streaming_pb2

console = Console(emoji=False)
econsole = Console(stderr=True)

FieldType = Literal["mac", "ip", "essid"]
mac_fields = ["macaddr", "peer_mac", "local_mac", "radio_mac", "interface_mac"]
ip_fields = ["ip_address", "src_ip", "dst_ip"]
strip_fields = ["customer_id"]
iden_fields = ["device_id"]

IGNORED_MSG_TYPES = ["STAT_UPLINK", "STAT_CLIENT"]

pretty_value = {
    "ADD": "[bright_green]ADD[/]",
    "DELETE": "[red]DELETE[/]",
    "UPDATE": "[dark_orange3]UPDATE[/]",
    "UP": "[bright_green]UP[/]",
    "DOWN": "[red]DOWN[/]",
}


# TODO need to convert mac / ip / essid fields as described in readme of https://github.com/aruba/central-python-workflows/tree/main/streaming-api-client

def _decode(data, field_type: FieldType = "ip"):
    """
    Decode fields from protobuf payloads.

    - If `data` is a base64-encoded string (MessageToDict output), decode to bytes.
    - If already bytes/bytearray, use as-is.
    - For 'essid' return UTF-8 string (fallback to bytes on decode error).
    - For 'ip' return human-readable address (IPv4 or IPv6) via ipaddress.
    - For 'mac' return colon-separated lower-case MAC using utils.Mac.
    """
    try:
        raw = None
        # MessageToDict may return nested dicts for complex types like IpAddress
        if isinstance(data, dict):
            # Try to extract the nested 'addr' or numeric representation
            if "addr" in data:
                data = data["addr"]
            elif "ip" in data:
                data = data["ip"]
            else:
                # nothing to decode
                return data

        if isinstance(data, str):
            # MessageToDict encodes bytes as base64 strings; try to decode
            try:
                raw = base64.b64decode(data)
            except Exception:
                # not base64 — assume already human readable string
                if field_type in ["essid", "network"]:
                    return data
                if field_type == "ip":
                    if data.is_digit():  # Some ip address fields represented as str(int) i.e. probeIp
                        raw = int(data)
                    else:
                        return data
                if field_type == "mac":
                    try:
                        return utils.Mac(data).cols
                    except Exception:
                        return data
                return data
        elif isinstance(data, (bytes, bytearray)):
            raw = bytes(data)
        elif isinstance(data, int):
            raw = data
        else:
            return data

        if field_type in ["essid", "network"]:
            try:
                return raw.decode("utf-8", errors="replace")
            except Exception:
                return raw
        if field_type == "ip":
            # raw might be bytes (base64-decoded), or an integer already (MessageToDict can return ints for some proto variants)
            try:
                if isinstance(raw, int):
                    return str(ipaddress.ip_address(raw))
                # bytes -> integer big endian
                addr = ipaddress.ip_address(int.from_bytes(raw, "big"))
                return str(addr)
            except Exception:
                # fallback: dotted decimal for 4-byte IPv4
                if isinstance(raw, (bytes, bytearray)) and len(raw) == 4:
                    return '.'.join(str(b) for b in raw)
                return raw
        if field_type == "mac":
            return utils.Mac(raw).cols

        return ':'.join(f'{b:02x}' for b in raw)
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


def decode_mac_field(data):
    """
    Accepts either:
      - a base64 string (as produced by MessageToDict for bytes fields), or
      - raw bytes (as produced by parsed protobuf message)
    Returns MAC as colon-separated lower-case string: '00:11:22:33:44:55'
    """
    # convert base64 string -> bytes, or accept bytes as-is
    if isinstance(data, str):
        try:
            raw = base64.b64decode(data)
        except Exception:
            # not base64 → return original
            return data
    elif isinstance(data, (bytes, bytearray)):
        raw = bytes(data)
    else:
        return data

    # Use helper to format nicely
    return utils.Mac(raw).cols


def extract_ranges(nums):
    nums = sorted(set(nums))
    try:
        groups = (list(g) for _, g in groupby(enumerate(nums), key=lambda iv: iv[1] - iv[0]))
    except Exception as e:
        log.error(f"{repr(e)} in extract_ranges, {nums = }", show=True)
        return f"{nums[0]} - {nums[-1]}"
    return ",".join([f"{g[0][1]}-{g[-1][1]}" if g[0][1] != g[-1][1] else str(g[0][1]) for g in groups])


@lru_cache
def _get_device(_key, _value):
    dev = cache.devices_by_serial.get(_value)
    if not dev:
        return _value

    return CacheDevice(dev).rich_help_text


def get_devices(as_dict, key):
    device_fields = ["deviceId", "associatedDevice"]
    return {**as_dict, key: [{k: v if k not in device_fields else _get_device(k, v) for k, v in inner.items()} for inner in as_dict[key]]}


def colorize_fields(as_dict: dict, key) -> dict:
    color_fields = ["status", "action", "operState", "adminState"]
    return {**as_dict, key: [{k: v if k not in color_fields else pretty_value.get(v, v) for k, v in inner.items()} for inner in as_dict[key]]}


def get_macs(as_dict, key) -> dict:
    as_dict = colorize_fields(as_dict, key=key)
    mac_keys = {
        "timestamp": "timestamp",
        "uptime": "uptime",
        "deviceId": "device",
        "associatedDevice": "associated_device",
        "network": "network",
        "essid": "essid",
        "ipAddress": "ip",
        "probeIpAddr": "probe_ip",
        "macaddr": "mac",
        "radioMac": "radio_mac",
        "interfaceMac": "interface_mac",
        "peerMac": "peer_mac",
        "localMac": "local_mac",
        "srcIp": "src_ip",
        "dstIp": "dst_ip"
    }
    for mkey in mac_keys.keys():
        if mkey == "timestamp":
            macs =  [DateTime(iface[mkey]) for iface in as_dict[key] if mkey in iface]
        elif mkey in ["deviceId", "associatedDevice"]:
            as_dict = get_devices(as_dict, key=key)
            continue
        elif mkey == "uptime":
            as_dict = {**as_dict, key: [{k: v if k != "uptime" else DateTime(v, "durwords-short", round_to_minute=True) for k, v in inner.items()} for inner in as_dict[key]]}
            continue
        elif mkey in ["essid", "network"]:
            macs =  [_decode(iface[mkey], field_type=mkey) for iface in as_dict[key] if mkey in iface]
        elif mkey in ["probeIpAddr"]:
            macs =  [_decode(iface[mkey], field_type=mac_keys[mkey].split("_")[-1]) for iface in as_dict[key] if mkey in iface]
        else:
            macs =  [_decode(iface[mkey]["addr"], field_type=mac_keys[mkey].split("_")[-1]) for iface in as_dict[key] if mkey in iface]

        if macs:
            as_dict[key] = [{k if k != mkey else mac_keys[mkey]: v if k != mkey else mac for k, v in iface.items()} for iface, mac in zip(as_dict[key], macs)]

    return as_dict


def get_ips(as_dict, key) -> dict:
    ip_keys = {
        "ipAddress": "ip",
    }
    for ip_key in ip_keys.keys():
        ips =  [_decode(iface[ip_key]["addr"]) for iface in as_dict[key] if ip_key in iface]
        if ips:
            as_dict[key] = [{k if k != ip_key else ip_keys[ip_key]: v if k != ip_key else ip for k, v in iface.items()} for iface, ip in zip(as_dict[key], ips)]

    return as_dict


def format_pb_data(pb_data: monitoring_pb2.MonitoringInformation) -> dict:
    as_dict = MessageToDict(pb_data)
    if pb_data.interfaces:
        allowed_vlans = [extract_ranges(iface["allowedVlan"]) for iface in as_dict["interfaces"] if "allowedVlan" in iface]
        if allowed_vlans:
            as_dict["interfaces"] = [{**iface, "allowedVlan": v} for iface, v in zip(as_dict["interfaces"], allowed_vlans)]
        # macs = get_macs(as_dict["interfaces"])
        # as_dict["interfaces"] = [{**iface, "mac": v} for iface, v in zip(as_dict["interfaces"], macs)]
        as_dict = get_macs(as_dict, "interfaces")
    if pb_data.interface_stats:
        as_dict = get_macs(as_dict, "interfaceStats")
    if pb_data.client_stats:
        as_dict = get_macs(as_dict, "clientStats")
    if pb_data.wired_clients:
        as_dict = get_macs(as_dict, "wiredClients")
    if pb_data.wireless_clients:
        as_dict = get_macs(as_dict, "wirelessClients")
    if pb_data.vap_stats:
        as_dict = get_macs(as_dict, "vapStats")
    if pb_data.radio_stats:
        as_dict = get_macs(as_dict, "radioStats")
    if pb_data.ipprobe_stats:
        as_dict = get_macs(as_dict, "ipprobeStats")
    if pb_data.ssid_stats:
        as_dict = get_macs(as_dict, "ssidStats")
    if pb_data.ike_tunnels:
        as_dict = get_macs(as_dict, "ikeTunnels")
    if pb_data.device_stats:
        as_dict = get_macs(as_dict, "deviceStats")
    if pb_data.uplink_probe_stats:
        as_dict = get_macs(as_dict, "uplinkProbeStats")
    if pb_data.uplink_wan_stats:
        as_dict = get_macs(as_dict, "uplinkWanStats")
    if pb_data.vlan_stats:
        as_dict = get_macs(as_dict, "vlanStats")
    if pb_data.device_neighbours:
        as_dict = get_macs(as_dict, "deviceNeighbours")
    if pb_data.tunnel_stats:
        as_dict = get_macs(as_dict, "tunnelStats")
    if pb_data.uplink_stats:
        as_dict = get_macs(as_dict, "uplinkStats")
    if pb_data.switches:
        as_dict = get_macs(as_dict, "switches")
    if pb_data.aps:
        as_dict = get_macs(as_dict, "aps")
    if pb_data.mobility_controllers:
        as_dict = get_macs(as_dict, "mobilityControllers")
    if pb_data.radios:
        as_dict = get_macs(as_dict, "radios")
    if pb_data.vaps:
        as_dict = get_macs(as_dict, "vaps")
    if pb_data.networks:
        as_dict = get_macs(as_dict, "networks")
    if pb_data.tunnels:
        as_dict = get_macs(as_dict, "tunnels")


    as_dict = {"timestamp": DateTime(pb_data.timestamp), **{k: v for k, v in as_dict.items() if k != "timestamp"}}  # Move timestamp to top and format
    del as_dict["customerId"]
    return as_dict



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
                        if [t for t in MessageToDict(pb_data).get("dataElements", []) if t not in IGNORED_MSG_TYPES]:
                            pb_dict = format_pb_data(pb_data)
                            render.display_results(data=pb_dict, tablefmt="yaml")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        econsole.print(msg.data)
                        break
                    else:
                        econsole.print(f"Got unexpected type {msg.type}")

    except aiohttp.WSServerHandshakeError as e:
        econsole.print(f"[dark_orange3]\u26a0[/]  {e.message}  Make sure you are subscribed to monitoring logs in Central UI")
