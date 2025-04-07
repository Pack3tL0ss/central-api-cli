from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Action(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    ADD: _ClassVar[Action]
    DELETE: _ClassVar[Action]
    UPDATE: _ClassVar[Action]

class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UP: _ClassVar[Status]
    DOWN: _ClassVar[Status]

class TunnelIndex(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    PRIMARY: _ClassVar[TunnelIndex]
    BACKUP: _ClassVar[TunnelIndex]

class CryptoType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CA_CERT: _ClassVar[CryptoType]
    PSK: _ClassVar[CryptoType]

class DataElement(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    STATE_CONTROLLER: _ClassVar[DataElement]
    STATE_SWITCH: _ClassVar[DataElement]
    STATE_SWARM: _ClassVar[DataElement]
    STATE_AP: _ClassVar[DataElement]
    STATE_VAP: _ClassVar[DataElement]
    STATE_RADIO: _ClassVar[DataElement]
    STATE_INTERFACE: _ClassVar[DataElement]
    STATE_NETWORK: _ClassVar[DataElement]
    STATE_TUNNEL: _ClassVar[DataElement]
    STATE_WIRELESSCLIENT: _ClassVar[DataElement]
    STATE_WIREDCLIENT: _ClassVar[DataElement]
    STATE_UPLINK: _ClassVar[DataElement]
    STAT_DEVICE: _ClassVar[DataElement]
    STAT_RADIO: _ClassVar[DataElement]
    STAT_VAP: _ClassVar[DataElement]
    STAT_INTERFACE: _ClassVar[DataElement]
    STAT_CLIENT: _ClassVar[DataElement]
    STAT_TUNNEL: _ClassVar[DataElement]
    STAT_MODEM: _ClassVar[DataElement]
    STAT_ROLE: _ClassVar[DataElement]
    STAT_VLAN: _ClassVar[DataElement]
    STAT_SSID: _ClassVar[DataElement]
    STAT_IPPROBE: _ClassVar[DataElement]
    STAT_UPLINK: _ClassVar[DataElement]
    STAT_UPLINKWAN: _ClassVar[DataElement]
    STAT_UPLINKIPPROBE: _ClassVar[DataElement]
    EVENTS_WIDS: _ClassVar[DataElement]
    EVENTS_ROGUE: _ClassVar[DataElement]
    STATS_UPLINK_SPEEDTEST: _ClassVar[DataElement]
    DEVICE_NEIGHBOURS: _ClassVar[DataElement]
    NOTIFICATIONS: _ClassVar[DataElement]
    SWITCH_STACK: _ClassVar[DataElement]
    STATE_IKE_TUNNEL: _ClassVar[DataElement]
    SWITCH_VLAN: _ClassVar[DataElement]
    STATE_VLAN: _ClassVar[DataElement]
    STATE_VSX: _ClassVar[DataElement]

class AuthType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NONE: _ClassVar[AuthType]
    MAC_AUTH: _ClassVar[AuthType]
    DOT1X_AUTH: _ClassVar[AuthType]
    L3_AUTH: _ClassVar[AuthType]
    CONSOLE_AUTH: _ClassVar[AuthType]
    TELNET_AUTH: _ClassVar[AuthType]
    WEBUI_AUTH: _ClassVar[AuthType]
    SSH_AUTH: _ClassVar[AuthType]
    WEB_AUTH: _ClassVar[AuthType]
    SNMP_AUTH: _ClassVar[AuthType]
    SSH_NONE_AUTH: _ClassVar[AuthType]
    LMA_AUTH: _ClassVar[AuthType]
    ANY_AUTH: _ClassVar[AuthType]
    CAPTIVE_PORTAL: _ClassVar[AuthType]
    VPN_AUTH: _ClassVar[AuthType]
    STATEFUL_KERBEROS: _ClassVar[AuthType]
    RADIUS_ACCOUNTING: _ClassVar[AuthType]
    SECURE_ID: _ClassVar[AuthType]
    STATEFUL_RADIUS: _ClassVar[AuthType]
    SWITCH_MANAGEMENT: _ClassVar[AuthType]
    DOT1X_MACHINE: _ClassVar[AuthType]
    DOT1X_USER: _ClassVar[AuthType]
    DOT1X_WIRED: _ClassVar[AuthType]
    DOT1X_WIRED_MACHINE: _ClassVar[AuthType]
    DOT1X_WIRED_USER: _ClassVar[AuthType]
    PUB_COOKIE: _ClassVar[AuthType]
    TACACAS_PLUS: _ClassVar[AuthType]
    WIRELESS_XSEC: _ClassVar[AuthType]
    WIRELESS_XSEC_MACHINE: _ClassVar[AuthType]
    WIRELESS_XSEC_USER: _ClassVar[AuthType]
    WIRELESS_XSEC_WIRED: _ClassVar[AuthType]
    WIRELESS_XSEC_WIRED_MACHINE: _ClassVar[AuthType]
    WIRELESS_XSEC_WIRED_USER: _ClassVar[AuthType]
    STATEFUL_NTLM: _ClassVar[AuthType]
    RAP_AP: _ClassVar[AuthType]
    VIA_WEB: _ClassVar[AuthType]
    GENERIC_INTERFACE_SPEC: _ClassVar[AuthType]
    TRANSPORT_VPN: _ClassVar[AuthType]
    VIA_VPN: _ClassVar[AuthType]
    PUTN_DOT1X: _ClassVar[AuthType]
    PUTN_MAC: _ClassVar[AuthType]
    PUTN_CP: _ClassVar[AuthType]
    PUTN_LMA: _ClassVar[AuthType]
    NUM_AUTH_CLIENT: _ClassVar[AuthType]
ADD: Action
DELETE: Action
UPDATE: Action
UP: Status
DOWN: Status
PRIMARY: TunnelIndex
BACKUP: TunnelIndex
CA_CERT: CryptoType
PSK: CryptoType
STATE_CONTROLLER: DataElement
STATE_SWITCH: DataElement
STATE_SWARM: DataElement
STATE_AP: DataElement
STATE_VAP: DataElement
STATE_RADIO: DataElement
STATE_INTERFACE: DataElement
STATE_NETWORK: DataElement
STATE_TUNNEL: DataElement
STATE_WIRELESSCLIENT: DataElement
STATE_WIREDCLIENT: DataElement
STATE_UPLINK: DataElement
STAT_DEVICE: DataElement
STAT_RADIO: DataElement
STAT_VAP: DataElement
STAT_INTERFACE: DataElement
STAT_CLIENT: DataElement
STAT_TUNNEL: DataElement
STAT_MODEM: DataElement
STAT_ROLE: DataElement
STAT_VLAN: DataElement
STAT_SSID: DataElement
STAT_IPPROBE: DataElement
STAT_UPLINK: DataElement
STAT_UPLINKWAN: DataElement
STAT_UPLINKIPPROBE: DataElement
EVENTS_WIDS: DataElement
EVENTS_ROGUE: DataElement
STATS_UPLINK_SPEEDTEST: DataElement
DEVICE_NEIGHBOURS: DataElement
NOTIFICATIONS: DataElement
SWITCH_STACK: DataElement
STATE_IKE_TUNNEL: DataElement
SWITCH_VLAN: DataElement
STATE_VLAN: DataElement
STATE_VSX: DataElement
NONE: AuthType
MAC_AUTH: AuthType
DOT1X_AUTH: AuthType
L3_AUTH: AuthType
CONSOLE_AUTH: AuthType
TELNET_AUTH: AuthType
WEBUI_AUTH: AuthType
SSH_AUTH: AuthType
WEB_AUTH: AuthType
SNMP_AUTH: AuthType
SSH_NONE_AUTH: AuthType
LMA_AUTH: AuthType
ANY_AUTH: AuthType
CAPTIVE_PORTAL: AuthType
VPN_AUTH: AuthType
STATEFUL_KERBEROS: AuthType
RADIUS_ACCOUNTING: AuthType
SECURE_ID: AuthType
STATEFUL_RADIUS: AuthType
SWITCH_MANAGEMENT: AuthType
DOT1X_MACHINE: AuthType
DOT1X_USER: AuthType
DOT1X_WIRED: AuthType
DOT1X_WIRED_MACHINE: AuthType
DOT1X_WIRED_USER: AuthType
PUB_COOKIE: AuthType
TACACAS_PLUS: AuthType
WIRELESS_XSEC: AuthType
WIRELESS_XSEC_MACHINE: AuthType
WIRELESS_XSEC_USER: AuthType
WIRELESS_XSEC_WIRED: AuthType
WIRELESS_XSEC_WIRED_MACHINE: AuthType
WIRELESS_XSEC_WIRED_USER: AuthType
STATEFUL_NTLM: AuthType
RAP_AP: AuthType
VIA_WEB: AuthType
GENERIC_INTERFACE_SPEC: AuthType
TRANSPORT_VPN: AuthType
VIA_VPN: AuthType
PUTN_DOT1X: AuthType
PUTN_MAC: AuthType
PUTN_CP: AuthType
PUTN_LMA: AuthType
NUM_AUTH_CLIENT: AuthType

class IpAddress(_message.Message):
    __slots__ = ("af", "addr")
    class addr_family(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ADDR_FAMILY_INET: _ClassVar[IpAddress.addr_family]
        ADDR_FAMILY_INET6: _ClassVar[IpAddress.addr_family]
    ADDR_FAMILY_INET: IpAddress.addr_family
    ADDR_FAMILY_INET6: IpAddress.addr_family
    AF_FIELD_NUMBER: _ClassVar[int]
    ADDR_FIELD_NUMBER: _ClassVar[int]
    af: IpAddress.addr_family
    addr: bytes
    def __init__(self, af: _Optional[_Union[IpAddress.addr_family, str]] = ..., addr: _Optional[bytes] = ...) -> None: ...

class MacAddress(_message.Message):
    __slots__ = ("addr",)
    ADDR_FIELD_NUMBER: _ClassVar[int]
    addr: bytes
    def __init__(self, addr: _Optional[bytes] = ...) -> None: ...

class Swarm(_message.Message):
    __slots__ = ("action", "swarm_id", "name", "status", "public_ip_address", "ip_address", "firmware_version")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SWARM_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PUBLIC_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    action: Action
    swarm_id: str
    name: str
    status: Status
    public_ip_address: IpAddress
    ip_address: IpAddress
    firmware_version: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., swarm_id: _Optional[str] = ..., name: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., public_ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., firmware_version: _Optional[str] = ...) -> None: ...

class Tunnel(_message.Message):
    __slots__ = ("action", "swarm_id", "index", "crypto_type", "peer_name", "peer_tun_ip", "tunnel_ip", "status", "active", "uptime", "tunnel_id")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SWARM_ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    CRYPTO_TYPE_FIELD_NUMBER: _ClassVar[int]
    PEER_NAME_FIELD_NUMBER: _ClassVar[int]
    PEER_TUN_IP_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_IP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_ID_FIELD_NUMBER: _ClassVar[int]
    action: Action
    swarm_id: str
    index: TunnelIndex
    crypto_type: CryptoType
    peer_name: str
    peer_tun_ip: IpAddress
    tunnel_ip: IpAddress
    status: Status
    active: bool
    uptime: int
    tunnel_id: int
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., swarm_id: _Optional[str] = ..., index: _Optional[_Union[TunnelIndex, str]] = ..., crypto_type: _Optional[_Union[CryptoType, str]] = ..., peer_name: _Optional[str] = ..., peer_tun_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., tunnel_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., status: _Optional[_Union[Status, str]] = ..., active: bool = ..., uptime: _Optional[int] = ..., tunnel_id: _Optional[int] = ...) -> None: ...

class Interface(_message.Message):
    __slots__ = ("action", "device_id", "macaddr", "status", "ipaddr", "duplex_mode", "name", "port_number", "type", "mode", "vlan", "has_poe", "poe_state", "oper_state", "admin_state", "speed", "mux", "trusted", "slot", "phy_type", "sub_type", "allowed_vlan", "native_vlan", "vsx_enabled", "state_down_reason", "vlan_mode")
    class Duplex(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        HALF: _ClassVar[Interface.Duplex]
        FULL: _ClassVar[Interface.Duplex]
        AUTO: _ClassVar[Interface.Duplex]
    HALF: Interface.Duplex
    FULL: Interface.Duplex
    AUTO: Interface.Duplex
    class IntfType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ETHERNET: _ClassVar[Interface.IntfType]
        LOOPBACK: _ClassVar[Interface.IntfType]
        VLAN: _ClassVar[Interface.IntfType]
        TUNNEL: _ClassVar[Interface.IntfType]
        PORT_CHANNEL: _ClassVar[Interface.IntfType]
        STANDBY: _ClassVar[Interface.IntfType]
        BRIDGE: _ClassVar[Interface.IntfType]
        SPLIT: _ClassVar[Interface.IntfType]
        STACK: _ClassVar[Interface.IntfType]
        MGMT: _ClassVar[Interface.IntfType]
        NONE: _ClassVar[Interface.IntfType]
    ETHERNET: Interface.IntfType
    LOOPBACK: Interface.IntfType
    VLAN: Interface.IntfType
    TUNNEL: Interface.IntfType
    PORT_CHANNEL: Interface.IntfType
    STANDBY: Interface.IntfType
    BRIDGE: Interface.IntfType
    SPLIT: Interface.IntfType
    STACK: Interface.IntfType
    MGMT: Interface.IntfType
    NONE: Interface.IntfType
    class SpeedType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        SPEED_INVALID: _ClassVar[Interface.SpeedType]
        SPEED_AUTO: _ClassVar[Interface.SpeedType]
        SPEED_10: _ClassVar[Interface.SpeedType]
        SPEED_100: _ClassVar[Interface.SpeedType]
        SPEED_1000: _ClassVar[Interface.SpeedType]
        SPEED_10000: _ClassVar[Interface.SpeedType]
    SPEED_INVALID: Interface.SpeedType
    SPEED_AUTO: Interface.SpeedType
    SPEED_10: Interface.SpeedType
    SPEED_100: Interface.SpeedType
    SPEED_1000: Interface.SpeedType
    SPEED_10000: Interface.SpeedType
    class PortType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PT_RJ45: _ClassVar[Interface.PortType]
        PT_GBIC: _ClassVar[Interface.PortType]
        PT_SERIAL: _ClassVar[Interface.PortType]
        PT_USB: _ClassVar[Interface.PortType]
        PT_X2: _ClassVar[Interface.PortType]
    PT_RJ45: Interface.PortType
    PT_GBIC: Interface.PortType
    PT_SERIAL: Interface.PortType
    PT_USB: Interface.PortType
    PT_X2: Interface.PortType
    class PoeSupport(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        NA: _ClassVar[Interface.PoeSupport]
        SUPPORTED: _ClassVar[Interface.PoeSupport]
        NOT_SUPPORTED: _ClassVar[Interface.PoeSupport]
    NA: Interface.PoeSupport
    SUPPORTED: Interface.PoeSupport
    NOT_SUPPORTED: Interface.PoeSupport
    class StateDownReason(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNINITIALIZED: _ClassVar[Interface.StateDownReason]
        WAITING_FOR_LINK: _ClassVar[Interface.StateDownReason]
        ADMIN_INTERFACE_DOWN: _ClassVar[Interface.StateDownReason]
        MODULE_MISSING: _ClassVar[Interface.StateDownReason]
        MODULE_UNRECOGNIZED: _ClassVar[Interface.StateDownReason]
        MODULE_UNSUPPORTED: _ClassVar[Interface.StateDownReason]
        MODULE_INCOMPATIBLE: _ClassVar[Interface.StateDownReason]
        MODULE_FAULT: _ClassVar[Interface.StateDownReason]
        GROUP_SPEED_MISMATCH: _ClassVar[Interface.StateDownReason]
        LANES_SPLIT: _ClassVar[Interface.StateDownReason]
        LANES_NOT_SPLIT: _ClassVar[Interface.StateDownReason]
        INVALID_MTU: _ClassVar[Interface.StateDownReason]
        INVALID_SPEEDS: _ClassVar[Interface.StateDownReason]
        AUTONEG_NOT_SUPPORTED: _ClassVar[Interface.StateDownReason]
        AUTONEG_REQUIRED: _ClassVar[Interface.StateDownReason]
        INTERFACE_ABSENT: _ClassVar[Interface.StateDownReason]
        PHYSICAL_INTERFACE_FAILED: _ClassVar[Interface.StateDownReason]
        PSPO_ENABLEMENT_LAYER_DOWN: _ClassVar[Interface.StateDownReason]
        CARD_INTERFACE_ERRORS: _ClassVar[Interface.StateDownReason]
        INTERFACE_OK: _ClassVar[Interface.StateDownReason]
    UNINITIALIZED: Interface.StateDownReason
    WAITING_FOR_LINK: Interface.StateDownReason
    ADMIN_INTERFACE_DOWN: Interface.StateDownReason
    MODULE_MISSING: Interface.StateDownReason
    MODULE_UNRECOGNIZED: Interface.StateDownReason
    MODULE_UNSUPPORTED: Interface.StateDownReason
    MODULE_INCOMPATIBLE: Interface.StateDownReason
    MODULE_FAULT: Interface.StateDownReason
    GROUP_SPEED_MISMATCH: Interface.StateDownReason
    LANES_SPLIT: Interface.StateDownReason
    LANES_NOT_SPLIT: Interface.StateDownReason
    INVALID_MTU: Interface.StateDownReason
    INVALID_SPEEDS: Interface.StateDownReason
    AUTONEG_NOT_SUPPORTED: Interface.StateDownReason
    AUTONEG_REQUIRED: Interface.StateDownReason
    INTERFACE_ABSENT: Interface.StateDownReason
    PHYSICAL_INTERFACE_FAILED: Interface.StateDownReason
    PSPO_ENABLEMENT_LAYER_DOWN: Interface.StateDownReason
    CARD_INTERFACE_ERRORS: Interface.StateDownReason
    INTERFACE_OK: Interface.StateDownReason
    class VlanModes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ACCESS: _ClassVar[Interface.VlanModes]
        NATIVE_TAGGED: _ClassVar[Interface.VlanModes]
        NATIVE_UNTAGGED: _ClassVar[Interface.VlanModes]
    ACCESS: Interface.VlanModes
    NATIVE_TAGGED: Interface.VlanModes
    NATIVE_UNTAGGED: Interface.VlanModes
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    IPADDR_FIELD_NUMBER: _ClassVar[int]
    DUPLEX_MODE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PORT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    HAS_POE_FIELD_NUMBER: _ClassVar[int]
    POE_STATE_FIELD_NUMBER: _ClassVar[int]
    OPER_STATE_FIELD_NUMBER: _ClassVar[int]
    ADMIN_STATE_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    MUX_FIELD_NUMBER: _ClassVar[int]
    TRUSTED_FIELD_NUMBER: _ClassVar[int]
    SLOT_FIELD_NUMBER: _ClassVar[int]
    PHY_TYPE_FIELD_NUMBER: _ClassVar[int]
    SUB_TYPE_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_VLAN_FIELD_NUMBER: _ClassVar[int]
    NATIVE_VLAN_FIELD_NUMBER: _ClassVar[int]
    VSX_ENABLED_FIELD_NUMBER: _ClassVar[int]
    STATE_DOWN_REASON_FIELD_NUMBER: _ClassVar[int]
    VLAN_MODE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    macaddr: MacAddress
    status: Status
    ipaddr: IpAddress
    duplex_mode: Interface.Duplex
    name: str
    port_number: str
    type: Interface.IntfType
    mode: str
    vlan: int
    has_poe: Interface.PoeSupport
    poe_state: Status
    oper_state: Status
    admin_state: Status
    speed: Interface.SpeedType
    mux: int
    trusted: int
    slot: str
    phy_type: Interface.PortType
    sub_type: str
    allowed_vlan: _containers.RepeatedScalarFieldContainer[int]
    native_vlan: int
    vsx_enabled: bool
    state_down_reason: Interface.StateDownReason
    vlan_mode: Interface.VlanModes
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., status: _Optional[_Union[Status, str]] = ..., ipaddr: _Optional[_Union[IpAddress, _Mapping]] = ..., duplex_mode: _Optional[_Union[Interface.Duplex, str]] = ..., name: _Optional[str] = ..., port_number: _Optional[str] = ..., type: _Optional[_Union[Interface.IntfType, str]] = ..., mode: _Optional[str] = ..., vlan: _Optional[int] = ..., has_poe: _Optional[_Union[Interface.PoeSupport, str]] = ..., poe_state: _Optional[_Union[Status, str]] = ..., oper_state: _Optional[_Union[Status, str]] = ..., admin_state: _Optional[_Union[Status, str]] = ..., speed: _Optional[_Union[Interface.SpeedType, str]] = ..., mux: _Optional[int] = ..., trusted: _Optional[int] = ..., slot: _Optional[str] = ..., phy_type: _Optional[_Union[Interface.PortType, str]] = ..., sub_type: _Optional[str] = ..., allowed_vlan: _Optional[_Iterable[int]] = ..., native_vlan: _Optional[int] = ..., vsx_enabled: bool = ..., state_down_reason: _Optional[_Union[Interface.StateDownReason, str]] = ..., vlan_mode: _Optional[_Union[Interface.VlanModes, str]] = ...) -> None: ...

class VapInfo(_message.Message):
    __slots__ = ("action", "device_id", "radio_mac", "essid", "ap_mac", "bssid")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    RADIO_MAC_FIELD_NUMBER: _ClassVar[int]
    ESSID_FIELD_NUMBER: _ClassVar[int]
    AP_MAC_FIELD_NUMBER: _ClassVar[int]
    BSSID_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    radio_mac: MacAddress
    essid: bytes
    ap_mac: MacAddress
    bssid: MacAddress
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., radio_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., essid: _Optional[bytes] = ..., ap_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., bssid: _Optional[_Union[MacAddress, _Mapping]] = ...) -> None: ...

class Radio(_message.Message):
    __slots__ = ("action", "device_id", "index", "macaddr", "status", "channel", "band", "channel_width", "ap_mac")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    BAND_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_WIDTH_FIELD_NUMBER: _ClassVar[int]
    AP_MAC_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    index: int
    macaddr: MacAddress
    status: Status
    channel: str
    band: int
    channel_width: int
    ap_mac: MacAddress
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., index: _Optional[int] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., status: _Optional[_Union[Status, str]] = ..., channel: _Optional[str] = ..., band: _Optional[int] = ..., channel_width: _Optional[int] = ..., ap_mac: _Optional[_Union[MacAddress, _Mapping]] = ...) -> None: ...

class Ap(_message.Message):
    __slots__ = ("action", "serial", "name", "macaddr", "cluster_id", "status", "ip_address", "model", "mesh_role", "mode", "swarm_master", "modem_connected", "uplink_type", "firmware_version")
    class UplinkType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ETHERNET: _ClassVar[Ap.UplinkType]
        MESH: _ClassVar[Ap.UplinkType]
        STATION: _ClassVar[Ap.UplinkType]
        MODEM: _ClassVar[Ap.UplinkType]
    ETHERNET: Ap.UplinkType
    MESH: Ap.UplinkType
    STATION: Ap.UplinkType
    MODEM: Ap.UplinkType
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    CLUSTER_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    MESH_ROLE_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    SWARM_MASTER_FIELD_NUMBER: _ClassVar[int]
    MODEM_CONNECTED_FIELD_NUMBER: _ClassVar[int]
    UPLINK_TYPE_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    action: Action
    serial: str
    name: str
    macaddr: MacAddress
    cluster_id: str
    status: Status
    ip_address: IpAddress
    model: str
    mesh_role: str
    mode: str
    swarm_master: bool
    modem_connected: bool
    uplink_type: Ap.UplinkType
    firmware_version: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., serial: _Optional[str] = ..., name: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., cluster_id: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., model: _Optional[str] = ..., mesh_role: _Optional[str] = ..., mode: _Optional[str] = ..., swarm_master: bool = ..., modem_connected: bool = ..., uplink_type: _Optional[_Union[Ap.UplinkType, str]] = ..., firmware_version: _Optional[str] = ...) -> None: ...

class Network(_message.Message):
    __slots__ = ("action", "swarm_id", "essid", "security", "type")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SWARM_ID_FIELD_NUMBER: _ClassVar[int]
    ESSID_FIELD_NUMBER: _ClassVar[int]
    SECURITY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    swarm_id: str
    essid: bytes
    security: str
    type: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., swarm_id: _Optional[str] = ..., essid: _Optional[bytes] = ..., security: _Optional[str] = ..., type: _Optional[str] = ...) -> None: ...

class WirelessClient(_message.Message):
    __slots__ = ("action", "macaddr", "name", "ip_address", "username", "associated_device", "radio_mac", "network", "user_role", "manufacturer", "os_type", "connection", "maxspeed", "vlan")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATED_DEVICE_FIELD_NUMBER: _ClassVar[int]
    RADIO_MAC_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    MANUFACTURER_FIELD_NUMBER: _ClassVar[int]
    OS_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONNECTION_FIELD_NUMBER: _ClassVar[int]
    MAXSPEED_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    action: Action
    macaddr: MacAddress
    name: str
    ip_address: IpAddress
    username: str
    associated_device: str
    radio_mac: MacAddress
    network: bytes
    user_role: str
    manufacturer: str
    os_type: str
    connection: str
    maxspeed: int
    vlan: int
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., name: _Optional[str] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., username: _Optional[str] = ..., associated_device: _Optional[str] = ..., radio_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., network: _Optional[bytes] = ..., user_role: _Optional[str] = ..., manufacturer: _Optional[str] = ..., os_type: _Optional[str] = ..., connection: _Optional[str] = ..., maxspeed: _Optional[int] = ..., vlan: _Optional[int] = ...) -> None: ...

class HardwareModule(_message.Message):
    __slots__ = ("index", "status")
    class HardwareStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        OK: _ClassVar[HardwareModule.HardwareStatus]
        ERROR: _ClassVar[HardwareModule.HardwareStatus]
        NOT_CONNECTED: _ClassVar[HardwareModule.HardwareStatus]
        ACTIVE: _ClassVar[HardwareModule.HardwareStatus]
        STANDBY: _ClassVar[HardwareModule.HardwareStatus]
        OFFLINE: _ClassVar[HardwareModule.HardwareStatus]
    OK: HardwareModule.HardwareStatus
    ERROR: HardwareModule.HardwareStatus
    NOT_CONNECTED: HardwareModule.HardwareStatus
    ACTIVE: HardwareModule.HardwareStatus
    STANDBY: HardwareModule.HardwareStatus
    OFFLINE: HardwareModule.HardwareStatus
    INDEX_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    index: int
    status: HardwareModule.HardwareStatus
    def __init__(self, index: _Optional[int] = ..., status: _Optional[_Union[HardwareModule.HardwareStatus, str]] = ...) -> None: ...

class Switch(_message.Message):
    __slots__ = ("action", "serial", "name", "macaddr", "model", "status", "public_ip_address", "ip_address", "firmware_version", "default_gateway", "device_mode", "uplink_ports", "max_slots", "used_slots", "management_modules", "power_supplies", "stack_id", "stack_member_id", "stack_member_role", "stack_macaddr")
    class StackMemberRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UNKNOWN: _ClassVar[Switch.StackMemberRole]
        COMMANDER: _ClassVar[Switch.StackMemberRole]
        STANDBY: _ClassVar[Switch.StackMemberRole]
        MEMBER: _ClassVar[Switch.StackMemberRole]
    UNKNOWN: Switch.StackMemberRole
    COMMANDER: Switch.StackMemberRole
    STANDBY: Switch.StackMemberRole
    MEMBER: Switch.StackMemberRole
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PUBLIC_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_GATEWAY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_MODE_FIELD_NUMBER: _ClassVar[int]
    UPLINK_PORTS_FIELD_NUMBER: _ClassVar[int]
    MAX_SLOTS_FIELD_NUMBER: _ClassVar[int]
    USED_SLOTS_FIELD_NUMBER: _ClassVar[int]
    MANAGEMENT_MODULES_FIELD_NUMBER: _ClassVar[int]
    POWER_SUPPLIES_FIELD_NUMBER: _ClassVar[int]
    STACK_ID_FIELD_NUMBER: _ClassVar[int]
    STACK_MEMBER_ID_FIELD_NUMBER: _ClassVar[int]
    STACK_MEMBER_ROLE_FIELD_NUMBER: _ClassVar[int]
    STACK_MACADDR_FIELD_NUMBER: _ClassVar[int]
    action: Action
    serial: str
    name: str
    macaddr: MacAddress
    model: str
    status: Status
    public_ip_address: IpAddress
    ip_address: IpAddress
    firmware_version: str
    default_gateway: IpAddress
    device_mode: int
    uplink_ports: _containers.RepeatedScalarFieldContainer[str]
    max_slots: int
    used_slots: _containers.RepeatedScalarFieldContainer[str]
    management_modules: _containers.RepeatedCompositeFieldContainer[HardwareModule]
    power_supplies: _containers.RepeatedCompositeFieldContainer[HardwareModule]
    stack_id: str
    stack_member_id: int
    stack_member_role: Switch.StackMemberRole
    stack_macaddr: MacAddress
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., serial: _Optional[str] = ..., name: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., model: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., public_ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., firmware_version: _Optional[str] = ..., default_gateway: _Optional[_Union[IpAddress, _Mapping]] = ..., device_mode: _Optional[int] = ..., uplink_ports: _Optional[_Iterable[str]] = ..., max_slots: _Optional[int] = ..., used_slots: _Optional[_Iterable[str]] = ..., management_modules: _Optional[_Iterable[_Union[HardwareModule, _Mapping]]] = ..., power_supplies: _Optional[_Iterable[_Union[HardwareModule, _Mapping]]] = ..., stack_id: _Optional[str] = ..., stack_member_id: _Optional[int] = ..., stack_member_role: _Optional[_Union[Switch.StackMemberRole, str]] = ..., stack_macaddr: _Optional[_Union[MacAddress, _Mapping]] = ...) -> None: ...

class SwitchStack(_message.Message):
    __slots__ = ("action", "stack_id", "status", "topology", "policy", "firmware_version", "vsf_domain_id")
    class StackTopology(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STANDALONE: _ClassVar[SwitchStack.StackTopology]
        CHAIN: _ClassVar[SwitchStack.StackTopology]
        RING: _ClassVar[SwitchStack.StackTopology]
        MESH: _ClassVar[SwitchStack.StackTopology]
        PARTIAL_MESH: _ClassVar[SwitchStack.StackTopology]
        UNKNOWN: _ClassVar[SwitchStack.StackTopology]
    STANDALONE: SwitchStack.StackTopology
    CHAIN: SwitchStack.StackTopology
    RING: SwitchStack.StackTopology
    MESH: SwitchStack.StackTopology
    PARTIAL_MESH: SwitchStack.StackTopology
    UNKNOWN: SwitchStack.StackTopology
    class StackPolicy(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STACK_SPLIT_UNKNOWN: _ClassVar[SwitchStack.StackPolicy]
        STACK_SPLIT_ONE_FRAGMENT_UP: _ClassVar[SwitchStack.StackPolicy]
        STACK_SPLIT_ALL_FRAGMENTS_UP: _ClassVar[SwitchStack.StackPolicy]
    STACK_SPLIT_UNKNOWN: SwitchStack.StackPolicy
    STACK_SPLIT_ONE_FRAGMENT_UP: SwitchStack.StackPolicy
    STACK_SPLIT_ALL_FRAGMENTS_UP: SwitchStack.StackPolicy
    ACTION_FIELD_NUMBER: _ClassVar[int]
    STACK_ID_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOPOLOGY_FIELD_NUMBER: _ClassVar[int]
    POLICY_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    VSF_DOMAIN_ID_FIELD_NUMBER: _ClassVar[int]
    action: Action
    stack_id: str
    status: Status
    topology: SwitchStack.StackTopology
    policy: SwitchStack.StackPolicy
    firmware_version: str
    vsf_domain_id: int
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., stack_id: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., topology: _Optional[_Union[SwitchStack.StackTopology, str]] = ..., policy: _Optional[_Union[SwitchStack.StackPolicy, str]] = ..., firmware_version: _Optional[str] = ..., vsf_domain_id: _Optional[int] = ...) -> None: ...

class WiredClient(_message.Message):
    __slots__ = ("action", "macaddr", "name", "ip_address", "username", "associated_device", "interface_mac", "user_role", "vlan", "auth_type")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    ASSOCIATED_DEVICE_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_MAC_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    AUTH_TYPE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    macaddr: MacAddress
    name: str
    ip_address: IpAddress
    username: str
    associated_device: str
    interface_mac: MacAddress
    user_role: str
    vlan: int
    auth_type: AuthType
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., name: _Optional[str] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., username: _Optional[str] = ..., associated_device: _Optional[str] = ..., interface_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., user_role: _Optional[str] = ..., vlan: _Optional[int] = ..., auth_type: _Optional[_Union[AuthType, str]] = ...) -> None: ...

class MobilityController(_message.Message):
    __slots__ = ("action", "serial", "name", "macaddr", "model", "status", "public_ip_address", "ip_address", "firmware_version", "default_gateway", "mode")
    class ControllerMode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        GATEWAY: _ClassVar[MobilityController.ControllerMode]
        VPNC: _ClassVar[MobilityController.ControllerMode]
    GATEWAY: MobilityController.ControllerMode
    VPNC: MobilityController.ControllerMode
    ACTION_FIELD_NUMBER: _ClassVar[int]
    SERIAL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    PUBLIC_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_VERSION_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_GATEWAY_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    serial: str
    name: str
    macaddr: MacAddress
    model: str
    status: Status
    public_ip_address: IpAddress
    ip_address: IpAddress
    firmware_version: str
    default_gateway: IpAddress
    mode: MobilityController.ControllerMode
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., serial: _Optional[str] = ..., name: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., model: _Optional[str] = ..., status: _Optional[_Union[Status, str]] = ..., public_ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., firmware_version: _Optional[str] = ..., default_gateway: _Optional[_Union[IpAddress, _Mapping]] = ..., mode: _Optional[_Union[MobilityController.ControllerMode, str]] = ...) -> None: ...

class Uplink(_message.Message):
    __slots__ = ("action", "device_id", "link_index", "name", "description", "priority", "status", "wan_status", "vlan", "vlan_description", "public_ip_address", "private_ip_address")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LINK_INDEX_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PRIORITY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    WAN_STATUS_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    VLAN_DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    PUBLIC_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    PRIVATE_IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    link_index: int
    name: str
    description: str
    priority: int
    status: Status
    wan_status: Status
    vlan: int
    vlan_description: str
    public_ip_address: IpAddress
    private_ip_address: IpAddress
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., link_index: _Optional[int] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., priority: _Optional[int] = ..., status: _Optional[_Union[Status, str]] = ..., wan_status: _Optional[_Union[Status, str]] = ..., vlan: _Optional[int] = ..., vlan_description: _Optional[str] = ..., public_ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., private_ip_address: _Optional[_Union[IpAddress, _Mapping]] = ...) -> None: ...

class IkeTunnel(_message.Message):
    __slots__ = ("action", "device_id", "map_id", "peer_mac", "local_mac", "src_ip", "dst_ip", "status", "map_name")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    MAP_ID_FIELD_NUMBER: _ClassVar[int]
    PEER_MAC_FIELD_NUMBER: _ClassVar[int]
    LOCAL_MAC_FIELD_NUMBER: _ClassVar[int]
    SRC_IP_FIELD_NUMBER: _ClassVar[int]
    DST_IP_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    map_id: int
    peer_mac: MacAddress
    local_mac: MacAddress
    src_ip: IpAddress
    dst_ip: IpAddress
    status: Status
    map_name: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., map_id: _Optional[int] = ..., peer_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., local_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., src_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., dst_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., status: _Optional[_Union[Status, str]] = ..., map_name: _Optional[str] = ...) -> None: ...

class DeviceStats(_message.Message):
    __slots__ = ("device_id", "timestamp", "uptime", "cpu_utilization", "mem_total", "mem_free", "power_consumption", "fan_speed", "temperature", "fan_status", "max_power", "poe_consumption", "poe_budget", "mem_utilization")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    UPTIME_FIELD_NUMBER: _ClassVar[int]
    CPU_UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    MEM_TOTAL_FIELD_NUMBER: _ClassVar[int]
    MEM_FREE_FIELD_NUMBER: _ClassVar[int]
    POWER_CONSUMPTION_FIELD_NUMBER: _ClassVar[int]
    FAN_SPEED_FIELD_NUMBER: _ClassVar[int]
    TEMPERATURE_FIELD_NUMBER: _ClassVar[int]
    FAN_STATUS_FIELD_NUMBER: _ClassVar[int]
    MAX_POWER_FIELD_NUMBER: _ClassVar[int]
    POE_CONSUMPTION_FIELD_NUMBER: _ClassVar[int]
    POE_BUDGET_FIELD_NUMBER: _ClassVar[int]
    MEM_UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: int
    uptime: int
    cpu_utilization: int
    mem_total: int
    mem_free: int
    power_consumption: int
    fan_speed: int
    temperature: int
    fan_status: Status
    max_power: int
    poe_consumption: int
    poe_budget: int
    mem_utilization: int
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., uptime: _Optional[int] = ..., cpu_utilization: _Optional[int] = ..., mem_total: _Optional[int] = ..., mem_free: _Optional[int] = ..., power_consumption: _Optional[int] = ..., fan_speed: _Optional[int] = ..., temperature: _Optional[int] = ..., fan_status: _Optional[_Union[Status, str]] = ..., max_power: _Optional[int] = ..., poe_consumption: _Optional[int] = ..., poe_budget: _Optional[int] = ..., mem_utilization: _Optional[int] = ...) -> None: ...

class RadioStats(_message.Message):
    __slots__ = ("device_id", "macaddr", "timestamp", "tx_bytes", "rx_bytes", "tx_drops", "tx_power", "noise_floor", "utilization", "rx_bad")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TX_DROPS_FIELD_NUMBER: _ClassVar[int]
    TX_POWER_FIELD_NUMBER: _ClassVar[int]
    NOISE_FLOOR_FIELD_NUMBER: _ClassVar[int]
    UTILIZATION_FIELD_NUMBER: _ClassVar[int]
    RX_BAD_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    macaddr: MacAddress
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    tx_drops: int
    tx_power: int
    noise_floor: int
    utilization: int
    rx_bad: int
    def __init__(self, device_id: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ..., tx_drops: _Optional[int] = ..., tx_power: _Optional[int] = ..., noise_floor: _Optional[int] = ..., utilization: _Optional[int] = ..., rx_bad: _Optional[int] = ...) -> None: ...

class VapStats(_message.Message):
    __slots__ = ("device_id", "radio_mac", "network", "timestamp", "tx_bytes", "rx_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    RADIO_MAC_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    radio_mac: MacAddress
    network: bytes
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., radio_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., network: _Optional[bytes] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class TunnelStats(_message.Message):
    __slots__ = ("swarm_id", "index", "timestamp", "tx_bytes", "rx_bytes", "tunnel_id", "tunnel_name", "device_id")
    SWARM_ID_FIELD_NUMBER: _ClassVar[int]
    INDEX_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_ID_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    swarm_id: str
    index: TunnelIndex
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    tunnel_id: int
    tunnel_name: str
    device_id: str
    def __init__(self, swarm_id: _Optional[str] = ..., index: _Optional[_Union[TunnelIndex, str]] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ..., tunnel_id: _Optional[int] = ..., tunnel_name: _Optional[str] = ..., device_id: _Optional[str] = ...) -> None: ...

class ClientStats(_message.Message):
    __slots__ = ("device_id", "macaddr", "timestamp", "tx_bytes", "rx_bytes", "rx_retries", "tx_retries", "speed", "signal_in_db", "snr")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_RETRIES_FIELD_NUMBER: _ClassVar[int]
    TX_RETRIES_FIELD_NUMBER: _ClassVar[int]
    SPEED_FIELD_NUMBER: _ClassVar[int]
    SIGNAL_IN_DB_FIELD_NUMBER: _ClassVar[int]
    SNR_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    macaddr: MacAddress
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    rx_retries: int
    tx_retries: int
    speed: int
    signal_in_db: int
    snr: int
    def __init__(self, device_id: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ..., rx_retries: _Optional[int] = ..., tx_retries: _Optional[int] = ..., speed: _Optional[int] = ..., signal_in_db: _Optional[int] = ..., snr: _Optional[int] = ...) -> None: ...

class InterfaceStats(_message.Message):
    __slots__ = ("device_id", "macaddr", "timestamp", "tx_bytes", "rx_bytes", "power_consumption", "in_errors", "out_errors", "in_discards", "out_discards", "in_packets", "out_packets", "in_other_err", "in_multicast_pkt", "in_broadcast_pkt", "in_unicast_pkt", "out_multicast_pkt", "out_broadcast_pkt", "out_unicast_pkt", "in_fcs", "in_alignment", "out_excessive_collision", "in_jabbers", "in_fragmented", "in_giant", "in_runt", "out_collision", "out_late_collision", "out_deferred")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    POWER_CONSUMPTION_FIELD_NUMBER: _ClassVar[int]
    IN_ERRORS_FIELD_NUMBER: _ClassVar[int]
    OUT_ERRORS_FIELD_NUMBER: _ClassVar[int]
    IN_DISCARDS_FIELD_NUMBER: _ClassVar[int]
    OUT_DISCARDS_FIELD_NUMBER: _ClassVar[int]
    IN_PACKETS_FIELD_NUMBER: _ClassVar[int]
    OUT_PACKETS_FIELD_NUMBER: _ClassVar[int]
    IN_OTHER_ERR_FIELD_NUMBER: _ClassVar[int]
    IN_MULTICAST_PKT_FIELD_NUMBER: _ClassVar[int]
    IN_BROADCAST_PKT_FIELD_NUMBER: _ClassVar[int]
    IN_UNICAST_PKT_FIELD_NUMBER: _ClassVar[int]
    OUT_MULTICAST_PKT_FIELD_NUMBER: _ClassVar[int]
    OUT_BROADCAST_PKT_FIELD_NUMBER: _ClassVar[int]
    OUT_UNICAST_PKT_FIELD_NUMBER: _ClassVar[int]
    IN_FCS_FIELD_NUMBER: _ClassVar[int]
    IN_ALIGNMENT_FIELD_NUMBER: _ClassVar[int]
    OUT_EXCESSIVE_COLLISION_FIELD_NUMBER: _ClassVar[int]
    IN_JABBERS_FIELD_NUMBER: _ClassVar[int]
    IN_FRAGMENTED_FIELD_NUMBER: _ClassVar[int]
    IN_GIANT_FIELD_NUMBER: _ClassVar[int]
    IN_RUNT_FIELD_NUMBER: _ClassVar[int]
    OUT_COLLISION_FIELD_NUMBER: _ClassVar[int]
    OUT_LATE_COLLISION_FIELD_NUMBER: _ClassVar[int]
    OUT_DEFERRED_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    macaddr: MacAddress
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    power_consumption: int
    in_errors: int
    out_errors: int
    in_discards: int
    out_discards: int
    in_packets: int
    out_packets: int
    in_other_err: int
    in_multicast_pkt: int
    in_broadcast_pkt: int
    in_unicast_pkt: int
    out_multicast_pkt: int
    out_broadcast_pkt: int
    out_unicast_pkt: int
    in_fcs: int
    in_alignment: int
    out_excessive_collision: int
    in_jabbers: int
    in_fragmented: int
    in_giant: int
    in_runt: int
    out_collision: int
    out_late_collision: int
    out_deferred: int
    def __init__(self, device_id: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ..., power_consumption: _Optional[int] = ..., in_errors: _Optional[int] = ..., out_errors: _Optional[int] = ..., in_discards: _Optional[int] = ..., out_discards: _Optional[int] = ..., in_packets: _Optional[int] = ..., out_packets: _Optional[int] = ..., in_other_err: _Optional[int] = ..., in_multicast_pkt: _Optional[int] = ..., in_broadcast_pkt: _Optional[int] = ..., in_unicast_pkt: _Optional[int] = ..., out_multicast_pkt: _Optional[int] = ..., out_broadcast_pkt: _Optional[int] = ..., out_unicast_pkt: _Optional[int] = ..., in_fcs: _Optional[int] = ..., in_alignment: _Optional[int] = ..., out_excessive_collision: _Optional[int] = ..., in_jabbers: _Optional[int] = ..., in_fragmented: _Optional[int] = ..., in_giant: _Optional[int] = ..., in_runt: _Optional[int] = ..., out_collision: _Optional[int] = ..., out_late_collision: _Optional[int] = ..., out_deferred: _Optional[int] = ...) -> None: ...

class UplinkStats(_message.Message):
    __slots__ = ("device_id", "link_id", "timestamp", "tx_bytes", "rx_bytes", "tunnel_tx_bytes", "tunnel_rx_bytes", "map_id", "map_name")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LINK_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    MAP_ID_FIELD_NUMBER: _ClassVar[int]
    MAP_NAME_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    link_id: int
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    tunnel_tx_bytes: int
    tunnel_rx_bytes: int
    map_id: int
    map_name: str
    def __init__(self, device_id: _Optional[str] = ..., link_id: _Optional[int] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ..., tunnel_tx_bytes: _Optional[int] = ..., tunnel_rx_bytes: _Optional[int] = ..., map_id: _Optional[int] = ..., map_name: _Optional[str] = ...) -> None: ...

class UplinkWanStats(_message.Message):
    __slots__ = ("device_id", "link_id", "timestamp", "compressed_bytes", "uncompressed_bytes", "savings_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LINK_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    COMPRESSED_BYTES_FIELD_NUMBER: _ClassVar[int]
    UNCOMPRESSED_BYTES_FIELD_NUMBER: _ClassVar[int]
    SAVINGS_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    link_id: int
    timestamp: int
    compressed_bytes: int
    uncompressed_bytes: int
    savings_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., link_id: _Optional[int] = ..., timestamp: _Optional[int] = ..., compressed_bytes: _Optional[int] = ..., uncompressed_bytes: _Optional[int] = ..., savings_bytes: _Optional[int] = ...) -> None: ...

class ModemStats(_message.Message):
    __slots__ = ("device_id", "timestamp", "tx_bytes", "rx_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class RoleStats(_message.Message):
    __slots__ = ("device_id", "user_role", "timestamp", "tx_bytes", "rx_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    user_role: str
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., user_role: _Optional[str] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class VlanStats(_message.Message):
    __slots__ = ("device_id", "vlan", "timestamp", "tx_bytes", "rx_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    vlan: int
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., vlan: _Optional[int] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class SsidStats(_message.Message):
    __slots__ = ("device_id", "essid", "timestamp", "tx_bytes", "rx_bytes")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    ESSID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    TX_BYTES_FIELD_NUMBER: _ClassVar[int]
    RX_BYTES_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    essid: bytes
    timestamp: int
    tx_bytes: int
    rx_bytes: int
    def __init__(self, device_id: _Optional[str] = ..., essid: _Optional[bytes] = ..., timestamp: _Optional[int] = ..., tx_bytes: _Optional[int] = ..., rx_bytes: _Optional[int] = ...) -> None: ...

class TunnelIpProbeStats(_message.Message):
    __slots__ = ("device_id", "tunnel_index", "probe_ip_addr", "probe_status", "ip_probe_pkt_loss_pct", "tunnel_name", "tunnel_id")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_INDEX_FIELD_NUMBER: _ClassVar[int]
    PROBE_IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    PROBE_STATUS_FIELD_NUMBER: _ClassVar[int]
    IP_PROBE_PKT_LOSS_PCT_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_NAME_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_ID_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    tunnel_index: TunnelIndex
    probe_ip_addr: IpAddress
    probe_status: int
    ip_probe_pkt_loss_pct: int
    tunnel_name: str
    tunnel_id: int
    def __init__(self, device_id: _Optional[str] = ..., tunnel_index: _Optional[_Union[TunnelIndex, str]] = ..., probe_ip_addr: _Optional[_Union[IpAddress, _Mapping]] = ..., probe_status: _Optional[int] = ..., ip_probe_pkt_loss_pct: _Optional[int] = ..., tunnel_name: _Optional[str] = ..., tunnel_id: _Optional[int] = ...) -> None: ...

class UplinkIpProbeStats(_message.Message):
    __slots__ = ("device_id", "link_id", "timestamp", "ip_address", "vlan", "avg_rtt", "max_rtt", "min_rtt", "avg_jitter", "max_jitter", "min_jitter", "mos_quality", "sd_avg_latency", "ds_avg_latency", "sd_avg_jitter", "ds_avg_jitter", "probe_status", "loss_pct", "vpnc_ip_addr", "probe_ip_addr", "avg_rtt_float", "max_rtt_float", "min_rtt_float", "avg_jitter_float", "max_jitter_float", "min_jitter_float", "mos_quality_float", "sd_avg_latency_float", "ds_avg_latency_float", "sd_avg_jitter_float", "ds_avg_jitter_float")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    LINK_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    IP_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    AVG_RTT_FIELD_NUMBER: _ClassVar[int]
    MAX_RTT_FIELD_NUMBER: _ClassVar[int]
    MIN_RTT_FIELD_NUMBER: _ClassVar[int]
    AVG_JITTER_FIELD_NUMBER: _ClassVar[int]
    MAX_JITTER_FIELD_NUMBER: _ClassVar[int]
    MIN_JITTER_FIELD_NUMBER: _ClassVar[int]
    MOS_QUALITY_FIELD_NUMBER: _ClassVar[int]
    SD_AVG_LATENCY_FIELD_NUMBER: _ClassVar[int]
    DS_AVG_LATENCY_FIELD_NUMBER: _ClassVar[int]
    SD_AVG_JITTER_FIELD_NUMBER: _ClassVar[int]
    DS_AVG_JITTER_FIELD_NUMBER: _ClassVar[int]
    PROBE_STATUS_FIELD_NUMBER: _ClassVar[int]
    LOSS_PCT_FIELD_NUMBER: _ClassVar[int]
    VPNC_IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    PROBE_IP_ADDR_FIELD_NUMBER: _ClassVar[int]
    AVG_RTT_FLOAT_FIELD_NUMBER: _ClassVar[int]
    MAX_RTT_FLOAT_FIELD_NUMBER: _ClassVar[int]
    MIN_RTT_FLOAT_FIELD_NUMBER: _ClassVar[int]
    AVG_JITTER_FLOAT_FIELD_NUMBER: _ClassVar[int]
    MAX_JITTER_FLOAT_FIELD_NUMBER: _ClassVar[int]
    MIN_JITTER_FLOAT_FIELD_NUMBER: _ClassVar[int]
    MOS_QUALITY_FLOAT_FIELD_NUMBER: _ClassVar[int]
    SD_AVG_LATENCY_FLOAT_FIELD_NUMBER: _ClassVar[int]
    DS_AVG_LATENCY_FLOAT_FIELD_NUMBER: _ClassVar[int]
    SD_AVG_JITTER_FLOAT_FIELD_NUMBER: _ClassVar[int]
    DS_AVG_JITTER_FLOAT_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    link_id: int
    timestamp: int
    ip_address: IpAddress
    vlan: int
    avg_rtt: int
    max_rtt: int
    min_rtt: int
    avg_jitter: int
    max_jitter: int
    min_jitter: int
    mos_quality: int
    sd_avg_latency: int
    ds_avg_latency: int
    sd_avg_jitter: int
    ds_avg_jitter: int
    probe_status: int
    loss_pct: int
    vpnc_ip_addr: int
    probe_ip_addr: int
    avg_rtt_float: float
    max_rtt_float: float
    min_rtt_float: float
    avg_jitter_float: float
    max_jitter_float: float
    min_jitter_float: float
    mos_quality_float: float
    sd_avg_latency_float: float
    ds_avg_latency_float: float
    sd_avg_jitter_float: float
    ds_avg_jitter_float: float
    def __init__(self, device_id: _Optional[str] = ..., link_id: _Optional[int] = ..., timestamp: _Optional[int] = ..., ip_address: _Optional[_Union[IpAddress, _Mapping]] = ..., vlan: _Optional[int] = ..., avg_rtt: _Optional[int] = ..., max_rtt: _Optional[int] = ..., min_rtt: _Optional[int] = ..., avg_jitter: _Optional[int] = ..., max_jitter: _Optional[int] = ..., min_jitter: _Optional[int] = ..., mos_quality: _Optional[int] = ..., sd_avg_latency: _Optional[int] = ..., ds_avg_latency: _Optional[int] = ..., sd_avg_jitter: _Optional[int] = ..., ds_avg_jitter: _Optional[int] = ..., probe_status: _Optional[int] = ..., loss_pct: _Optional[int] = ..., vpnc_ip_addr: _Optional[int] = ..., probe_ip_addr: _Optional[int] = ..., avg_rtt_float: _Optional[float] = ..., max_rtt_float: _Optional[float] = ..., min_rtt_float: _Optional[float] = ..., avg_jitter_float: _Optional[float] = ..., max_jitter_float: _Optional[float] = ..., min_jitter_float: _Optional[float] = ..., mos_quality_float: _Optional[float] = ..., sd_avg_latency_float: _Optional[float] = ..., ds_avg_latency_float: _Optional[float] = ..., sd_avg_jitter_float: _Optional[float] = ..., ds_avg_jitter_float: _Optional[float] = ...) -> None: ...

class UplinkSpeedtest(_message.Message):
    __slots__ = ("device_id", "server_ip", "vlan", "protocol", "upstream_bps", "downstream_bps", "time_secs", "upstream_jitter", "downstream_jitter")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    SERVER_IP_FIELD_NUMBER: _ClassVar[int]
    VLAN_FIELD_NUMBER: _ClassVar[int]
    PROTOCOL_FIELD_NUMBER: _ClassVar[int]
    UPSTREAM_BPS_FIELD_NUMBER: _ClassVar[int]
    DOWNSTREAM_BPS_FIELD_NUMBER: _ClassVar[int]
    TIME_SECS_FIELD_NUMBER: _ClassVar[int]
    UPSTREAM_JITTER_FIELD_NUMBER: _ClassVar[int]
    DOWNSTREAM_JITTER_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    server_ip: IpAddress
    vlan: int
    protocol: str
    upstream_bps: int
    downstream_bps: int
    time_secs: int
    upstream_jitter: float
    downstream_jitter: float
    def __init__(self, device_id: _Optional[str] = ..., server_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., vlan: _Optional[int] = ..., protocol: _Optional[str] = ..., upstream_bps: _Optional[int] = ..., downstream_bps: _Optional[int] = ..., time_secs: _Optional[int] = ..., upstream_jitter: _Optional[float] = ..., downstream_jitter: _Optional[float] = ...) -> None: ...

class WIDSEvent(_message.Message):
    __slots__ = ("action", "event_type", "macaddr", "detected_ap", "attack_type", "channel", "network")
    class EventType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ROGUE: _ClassVar[WIDSEvent.EventType]
        INTERFERING: _ClassVar[WIDSEvent.EventType]
        INFRASTRUCTURE_ATTACK: _ClassVar[WIDSEvent.EventType]
        CLIENT_ATTACK: _ClassVar[WIDSEvent.EventType]
    ROGUE: WIDSEvent.EventType
    INTERFERING: WIDSEvent.EventType
    INFRASTRUCTURE_ATTACK: WIDSEvent.EventType
    CLIENT_ATTACK: WIDSEvent.EventType
    class AttackType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        DETECT_VALID_SSID_MISUSE: _ClassVar[WIDSEvent.AttackType]
        DETECT_ADHOC_NETWORK: _ClassVar[WIDSEvent.AttackType]
        DETECT_AP_FLOOD: _ClassVar[WIDSEvent.AttackType]
        DETECT_WIRELESS_BRIDGE: _ClassVar[WIDSEvent.AttackType]
        DETECT_INVALID_MAC_OUI_AP: _ClassVar[WIDSEvent.AttackType]
        DETECT_INVALID_MAC_OUI_STA: _ClassVar[WIDSEvent.AttackType]
        DETECT_BAD_WEP: _ClassVar[WIDSEvent.AttackType]
        DETECT_AP_IMPERSONATION: _ClassVar[WIDSEvent.AttackType]
        DETECT_WINDOWS_BRIDGE: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_DEAUTH_BROADCAST_AP: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_DEAUTH_BROADCAST_STA: _ClassVar[WIDSEvent.AttackType]
        DETECT_HT_GREENFIELD: _ClassVar[WIDSEvent.AttackType]
        DETECT_HT_40MHZ_INTOLERANCE_AP: _ClassVar[WIDSEvent.AttackType]
        DETECT_HT_40MHZ_INTOLERANCE_STA: _ClassVar[WIDSEvent.AttackType]
        DETECT_CLIENT_FLOOD: _ClassVar[WIDSEvent.AttackType]
        DETECT_ADHOC_USING_VALID_SSID: _ClassVar[WIDSEvent.AttackType]
        DETECT_AP_SPOOFING: _ClassVar[WIDSEvent.AttackType]
        DETECT_INVALID_ADDRESSCOMBINATION: _ClassVar[WIDSEvent.AttackType]
        DETECT_MALFORMED_HTIE: _ClassVar[WIDSEvent.AttackType]
        DETECT_MALFORMED_ASSOC_REQ: _ClassVar[WIDSEvent.AttackType]
        DETECT_OVERFLOW_IE: _ClassVar[WIDSEvent.AttackType]
        DETECT_OVERFLOW_EAPOL_KEY: _ClassVar[WIDSEvent.AttackType]
        DETECT_MALFORMED_LARGE_DURATION: _ClassVar[WIDSEvent.AttackType]
        DETECT_MALFORMED_FRAME_WRONG_CHANNEL: _ClassVar[WIDSEvent.AttackType]
        DETECT_MALFORMED_FRAME_AUTH: _ClassVar[WIDSEvent.AttackType]
        DETECT_CTS_RATE_ANOMALY: _ClassVar[WIDSEvent.AttackType]
        DETECT_RTS_RATE_ANOMALY: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_DEAUTH_BROADCAST: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_DEASSOCIATION_BROADCAST: _ClassVar[WIDSEvent.AttackType]
        DETECT_RATE_ANOMALIES_BY_AP: _ClassVar[WIDSEvent.AttackType]
        DETECT_RATE_ANOMALIES_BY_STA: _ClassVar[WIDSEvent.AttackType]
        DETECT_EAP_RATE_ANOMALY: _ClassVar[WIDSEvent.AttackType]
        DETECT_DISCONNECT_STA: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_ASLEAP_FROM_AP: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_ASLEAP_FROM_STA: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_AIRJACK_FROM_AP: _ClassVar[WIDSEvent.AttackType]
        SIGNATURE_AIRJACK_FROM_STA: _ClassVar[WIDSEvent.AttackType]
        DETECT_STATION_DISCONNECT_ATTACK_AP: _ClassVar[WIDSEvent.AttackType]
        DETECT_UNENCRYPTED_VALID: _ClassVar[WIDSEvent.AttackType]
        DETECT_OMERTA_ATTACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_TKIP_REPLAY_ATTACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_CHOPCHOP_ATTACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_FATAJACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_VALID_CLIENT_MISASSOCIATION: _ClassVar[WIDSEvent.AttackType]
        DETECT_BLOCK_ACK_ATTACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_HOTSPOTTER_ATTACK: _ClassVar[WIDSEvent.AttackType]
        DETECT_POWER_SAVE_DOS_ATTACK: _ClassVar[WIDSEvent.AttackType]
    DETECT_VALID_SSID_MISUSE: WIDSEvent.AttackType
    DETECT_ADHOC_NETWORK: WIDSEvent.AttackType
    DETECT_AP_FLOOD: WIDSEvent.AttackType
    DETECT_WIRELESS_BRIDGE: WIDSEvent.AttackType
    DETECT_INVALID_MAC_OUI_AP: WIDSEvent.AttackType
    DETECT_INVALID_MAC_OUI_STA: WIDSEvent.AttackType
    DETECT_BAD_WEP: WIDSEvent.AttackType
    DETECT_AP_IMPERSONATION: WIDSEvent.AttackType
    DETECT_WINDOWS_BRIDGE: WIDSEvent.AttackType
    SIGNATURE_DEAUTH_BROADCAST_AP: WIDSEvent.AttackType
    SIGNATURE_DEAUTH_BROADCAST_STA: WIDSEvent.AttackType
    DETECT_HT_GREENFIELD: WIDSEvent.AttackType
    DETECT_HT_40MHZ_INTOLERANCE_AP: WIDSEvent.AttackType
    DETECT_HT_40MHZ_INTOLERANCE_STA: WIDSEvent.AttackType
    DETECT_CLIENT_FLOOD: WIDSEvent.AttackType
    DETECT_ADHOC_USING_VALID_SSID: WIDSEvent.AttackType
    DETECT_AP_SPOOFING: WIDSEvent.AttackType
    DETECT_INVALID_ADDRESSCOMBINATION: WIDSEvent.AttackType
    DETECT_MALFORMED_HTIE: WIDSEvent.AttackType
    DETECT_MALFORMED_ASSOC_REQ: WIDSEvent.AttackType
    DETECT_OVERFLOW_IE: WIDSEvent.AttackType
    DETECT_OVERFLOW_EAPOL_KEY: WIDSEvent.AttackType
    DETECT_MALFORMED_LARGE_DURATION: WIDSEvent.AttackType
    DETECT_MALFORMED_FRAME_WRONG_CHANNEL: WIDSEvent.AttackType
    DETECT_MALFORMED_FRAME_AUTH: WIDSEvent.AttackType
    DETECT_CTS_RATE_ANOMALY: WIDSEvent.AttackType
    DETECT_RTS_RATE_ANOMALY: WIDSEvent.AttackType
    SIGNATURE_DEAUTH_BROADCAST: WIDSEvent.AttackType
    SIGNATURE_DEASSOCIATION_BROADCAST: WIDSEvent.AttackType
    DETECT_RATE_ANOMALIES_BY_AP: WIDSEvent.AttackType
    DETECT_RATE_ANOMALIES_BY_STA: WIDSEvent.AttackType
    DETECT_EAP_RATE_ANOMALY: WIDSEvent.AttackType
    DETECT_DISCONNECT_STA: WIDSEvent.AttackType
    SIGNATURE_ASLEAP_FROM_AP: WIDSEvent.AttackType
    SIGNATURE_ASLEAP_FROM_STA: WIDSEvent.AttackType
    SIGNATURE_AIRJACK_FROM_AP: WIDSEvent.AttackType
    SIGNATURE_AIRJACK_FROM_STA: WIDSEvent.AttackType
    DETECT_STATION_DISCONNECT_ATTACK_AP: WIDSEvent.AttackType
    DETECT_UNENCRYPTED_VALID: WIDSEvent.AttackType
    DETECT_OMERTA_ATTACK: WIDSEvent.AttackType
    DETECT_TKIP_REPLAY_ATTACK: WIDSEvent.AttackType
    DETECT_CHOPCHOP_ATTACK: WIDSEvent.AttackType
    DETECT_FATAJACK: WIDSEvent.AttackType
    DETECT_VALID_CLIENT_MISASSOCIATION: WIDSEvent.AttackType
    DETECT_BLOCK_ACK_ATTACK: WIDSEvent.AttackType
    DETECT_HOTSPOTTER_ATTACK: WIDSEvent.AttackType
    DETECT_POWER_SAVE_DOS_ATTACK: WIDSEvent.AttackType
    ACTION_FIELD_NUMBER: _ClassVar[int]
    EVENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AP_FIELD_NUMBER: _ClassVar[int]
    ATTACK_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    action: Action
    event_type: WIDSEvent.EventType
    macaddr: MacAddress
    detected_ap: str
    attack_type: WIDSEvent.AttackType
    channel: str
    network: bytes
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., event_type: _Optional[_Union[WIDSEvent.EventType, str]] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., detected_ap: _Optional[str] = ..., attack_type: _Optional[_Union[WIDSEvent.AttackType, str]] = ..., channel: _Optional[str] = ..., network: _Optional[bytes] = ...) -> None: ...

class AirMonitorRogueInfo(_message.Message):
    __slots__ = ("match_type", "match_mac", "match_ip", "monitor_name", "nat_match_type")
    class wms_rap_match_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        RAP_MT_NONE: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_CFG_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_ETH_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_AP_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_EXT_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_MANUAL: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_BASE_BSSID: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_EMS: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_ETH_GW_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_CLASS_OFF: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_AP_BSSID: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_PROP_ETH_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_AP_RULE: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_SYSTEM_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
        RAP_MT_SYSTEM_GW_WM: _ClassVar[AirMonitorRogueInfo.wms_rap_match_type]
    RAP_MT_NONE: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_CFG_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_ETH_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_AP_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_EXT_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_MANUAL: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_BASE_BSSID: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_EMS: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_ETH_GW_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_CLASS_OFF: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_AP_BSSID: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_PROP_ETH_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_AP_RULE: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_SYSTEM_WM: AirMonitorRogueInfo.wms_rap_match_type
    RAP_MT_SYSTEM_GW_WM: AirMonitorRogueInfo.wms_rap_match_type
    class wms_rap_nat_match_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        RAP_NMT_NONE: _ClassVar[AirMonitorRogueInfo.wms_rap_nat_match_type]
        RAP_NMT_EQUAL: _ClassVar[AirMonitorRogueInfo.wms_rap_nat_match_type]
        RAP_NMT_PLUS_ONE: _ClassVar[AirMonitorRogueInfo.wms_rap_nat_match_type]
        RAP_NMT_MINUS_ONE: _ClassVar[AirMonitorRogueInfo.wms_rap_nat_match_type]
        RAP_NMT_OUI: _ClassVar[AirMonitorRogueInfo.wms_rap_nat_match_type]
    RAP_NMT_NONE: AirMonitorRogueInfo.wms_rap_nat_match_type
    RAP_NMT_EQUAL: AirMonitorRogueInfo.wms_rap_nat_match_type
    RAP_NMT_PLUS_ONE: AirMonitorRogueInfo.wms_rap_nat_match_type
    RAP_NMT_MINUS_ONE: AirMonitorRogueInfo.wms_rap_nat_match_type
    RAP_NMT_OUI: AirMonitorRogueInfo.wms_rap_nat_match_type
    MATCH_TYPE_FIELD_NUMBER: _ClassVar[int]
    MATCH_MAC_FIELD_NUMBER: _ClassVar[int]
    MATCH_IP_FIELD_NUMBER: _ClassVar[int]
    MONITOR_NAME_FIELD_NUMBER: _ClassVar[int]
    NAT_MATCH_TYPE_FIELD_NUMBER: _ClassVar[int]
    match_type: AirMonitorRogueInfo.wms_rap_match_type
    match_mac: MacAddress
    match_ip: IpAddress
    monitor_name: str
    nat_match_type: AirMonitorRogueInfo.wms_rap_nat_match_type
    def __init__(self, match_type: _Optional[_Union[AirMonitorRogueInfo.wms_rap_match_type, str]] = ..., match_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., match_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., monitor_name: _Optional[str] = ..., nat_match_type: _Optional[_Union[AirMonitorRogueInfo.wms_rap_nat_match_type, str]] = ...) -> None: ...

class RogueEvent(_message.Message):
    __slots__ = ("action", "detected_ap", "macaddr", "channel", "network", "encr_type", "am_rogue")
    class wms_snmp_encr_protocol(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        WMS_SNMP_WPA_ENCR_OPEN: _ClassVar[RogueEvent.wms_snmp_encr_protocol]
        WMS_SNMP_WPA_ENCR_WEP: _ClassVar[RogueEvent.wms_snmp_encr_protocol]
        WMS_SNMP_WPA_ENCR_WPA: _ClassVar[RogueEvent.wms_snmp_encr_protocol]
        WMS_SNMP_WPA_ENCR_WPA2: _ClassVar[RogueEvent.wms_snmp_encr_protocol]
    WMS_SNMP_WPA_ENCR_OPEN: RogueEvent.wms_snmp_encr_protocol
    WMS_SNMP_WPA_ENCR_WEP: RogueEvent.wms_snmp_encr_protocol
    WMS_SNMP_WPA_ENCR_WPA: RogueEvent.wms_snmp_encr_protocol
    WMS_SNMP_WPA_ENCR_WPA2: RogueEvent.wms_snmp_encr_protocol
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DETECTED_AP_FIELD_NUMBER: _ClassVar[int]
    MACADDR_FIELD_NUMBER: _ClassVar[int]
    CHANNEL_FIELD_NUMBER: _ClassVar[int]
    NETWORK_FIELD_NUMBER: _ClassVar[int]
    ENCR_TYPE_FIELD_NUMBER: _ClassVar[int]
    AM_ROGUE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    detected_ap: str
    macaddr: MacAddress
    channel: int
    network: bytes
    encr_type: RogueEvent.wms_snmp_encr_protocol
    am_rogue: AirMonitorRogueInfo
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., detected_ap: _Optional[str] = ..., macaddr: _Optional[_Union[MacAddress, _Mapping]] = ..., channel: _Optional[int] = ..., network: _Optional[bytes] = ..., encr_type: _Optional[_Union[RogueEvent.wms_snmp_encr_protocol, str]] = ..., am_rogue: _Optional[_Union[AirMonitorRogueInfo, _Mapping]] = ...) -> None: ...

class DeviceNeighbours(_message.Message):
    __slots__ = ("action", "device_id", "port", "remote_device_id", "remote_port", "remote_port_number", "vlan_id")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    PORT_FIELD_NUMBER: _ClassVar[int]
    REMOTE_DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    REMOTE_PORT_FIELD_NUMBER: _ClassVar[int]
    REMOTE_PORT_NUMBER_FIELD_NUMBER: _ClassVar[int]
    VLAN_ID_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    port: str
    remote_device_id: str
    remote_port: str
    remote_port_number: str
    vlan_id: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., port: _Optional[str] = ..., remote_device_id: _Optional[str] = ..., remote_port: _Optional[str] = ..., remote_port_number: _Optional[str] = ..., vlan_id: _Optional[str] = ...) -> None: ...

class MonitoringInformation(_message.Message):
    __slots__ = ("customer_id", "data_elements", "swarms", "aps", "networks", "radios", "vaps", "interfaces", "tunnels", "wireless_clients", "switches", "wired_clients", "device_stats", "radio_stats", "interface_stats", "vap_stats", "client_stats", "tunnel_stats", "wids_events", "modem_stats", "role_stats", "vlan_stats", "ssid_stats", "ipprobe_stats", "rogue_events", "mobility_controllers", "uplinks", "uplink_stats", "uplink_wan_stats", "uplink_probe_stats", "uplink_speedtest", "device_neighbours", "notification", "switch_stacks", "ike_tunnels", "switch_vlan_info", "vlans", "vsx", "timestamp")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    DATA_ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    SWARMS_FIELD_NUMBER: _ClassVar[int]
    APS_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    RADIOS_FIELD_NUMBER: _ClassVar[int]
    VAPS_FIELD_NUMBER: _ClassVar[int]
    INTERFACES_FIELD_NUMBER: _ClassVar[int]
    TUNNELS_FIELD_NUMBER: _ClassVar[int]
    WIRELESS_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    SWITCHES_FIELD_NUMBER: _ClassVar[int]
    WIRED_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    DEVICE_STATS_FIELD_NUMBER: _ClassVar[int]
    RADIO_STATS_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_STATS_FIELD_NUMBER: _ClassVar[int]
    VAP_STATS_FIELD_NUMBER: _ClassVar[int]
    CLIENT_STATS_FIELD_NUMBER: _ClassVar[int]
    TUNNEL_STATS_FIELD_NUMBER: _ClassVar[int]
    WIDS_EVENTS_FIELD_NUMBER: _ClassVar[int]
    MODEM_STATS_FIELD_NUMBER: _ClassVar[int]
    ROLE_STATS_FIELD_NUMBER: _ClassVar[int]
    VLAN_STATS_FIELD_NUMBER: _ClassVar[int]
    SSID_STATS_FIELD_NUMBER: _ClassVar[int]
    IPPROBE_STATS_FIELD_NUMBER: _ClassVar[int]
    ROGUE_EVENTS_FIELD_NUMBER: _ClassVar[int]
    MOBILITY_CONTROLLERS_FIELD_NUMBER: _ClassVar[int]
    UPLINKS_FIELD_NUMBER: _ClassVar[int]
    UPLINK_STATS_FIELD_NUMBER: _ClassVar[int]
    UPLINK_WAN_STATS_FIELD_NUMBER: _ClassVar[int]
    UPLINK_PROBE_STATS_FIELD_NUMBER: _ClassVar[int]
    UPLINK_SPEEDTEST_FIELD_NUMBER: _ClassVar[int]
    DEVICE_NEIGHBOURS_FIELD_NUMBER: _ClassVar[int]
    NOTIFICATION_FIELD_NUMBER: _ClassVar[int]
    SWITCH_STACKS_FIELD_NUMBER: _ClassVar[int]
    IKE_TUNNELS_FIELD_NUMBER: _ClassVar[int]
    SWITCH_VLAN_INFO_FIELD_NUMBER: _ClassVar[int]
    VLANS_FIELD_NUMBER: _ClassVar[int]
    VSX_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    data_elements: _containers.RepeatedScalarFieldContainer[DataElement]
    swarms: _containers.RepeatedCompositeFieldContainer[Swarm]
    aps: _containers.RepeatedCompositeFieldContainer[Ap]
    networks: _containers.RepeatedCompositeFieldContainer[Network]
    radios: _containers.RepeatedCompositeFieldContainer[Radio]
    vaps: _containers.RepeatedCompositeFieldContainer[VapInfo]
    interfaces: _containers.RepeatedCompositeFieldContainer[Interface]
    tunnels: _containers.RepeatedCompositeFieldContainer[Tunnel]
    wireless_clients: _containers.RepeatedCompositeFieldContainer[WirelessClient]
    switches: _containers.RepeatedCompositeFieldContainer[Switch]
    wired_clients: _containers.RepeatedCompositeFieldContainer[WiredClient]
    device_stats: _containers.RepeatedCompositeFieldContainer[DeviceStats]
    radio_stats: _containers.RepeatedCompositeFieldContainer[RadioStats]
    interface_stats: _containers.RepeatedCompositeFieldContainer[InterfaceStats]
    vap_stats: _containers.RepeatedCompositeFieldContainer[VapStats]
    client_stats: _containers.RepeatedCompositeFieldContainer[ClientStats]
    tunnel_stats: _containers.RepeatedCompositeFieldContainer[TunnelStats]
    wids_events: _containers.RepeatedCompositeFieldContainer[WIDSEvent]
    modem_stats: _containers.RepeatedCompositeFieldContainer[ModemStats]
    role_stats: _containers.RepeatedCompositeFieldContainer[RoleStats]
    vlan_stats: _containers.RepeatedCompositeFieldContainer[VlanStats]
    ssid_stats: _containers.RepeatedCompositeFieldContainer[SsidStats]
    ipprobe_stats: _containers.RepeatedCompositeFieldContainer[TunnelIpProbeStats]
    rogue_events: _containers.RepeatedCompositeFieldContainer[RogueEvent]
    mobility_controllers: _containers.RepeatedCompositeFieldContainer[MobilityController]
    uplinks: _containers.RepeatedCompositeFieldContainer[Uplink]
    uplink_stats: _containers.RepeatedCompositeFieldContainer[UplinkStats]
    uplink_wan_stats: _containers.RepeatedCompositeFieldContainer[UplinkWanStats]
    uplink_probe_stats: _containers.RepeatedCompositeFieldContainer[UplinkIpProbeStats]
    uplink_speedtest: _containers.RepeatedCompositeFieldContainer[UplinkSpeedtest]
    device_neighbours: _containers.RepeatedCompositeFieldContainer[DeviceNeighbours]
    notification: _containers.RepeatedCompositeFieldContainer[Notification]
    switch_stacks: _containers.RepeatedCompositeFieldContainer[SwitchStack]
    ike_tunnels: _containers.RepeatedCompositeFieldContainer[IkeTunnel]
    switch_vlan_info: SwitchVlanInfo
    vlans: _containers.RepeatedCompositeFieldContainer[Vlan]
    vsx: VSXState
    timestamp: int
    def __init__(self, customer_id: _Optional[str] = ..., data_elements: _Optional[_Iterable[_Union[DataElement, str]]] = ..., swarms: _Optional[_Iterable[_Union[Swarm, _Mapping]]] = ..., aps: _Optional[_Iterable[_Union[Ap, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[Network, _Mapping]]] = ..., radios: _Optional[_Iterable[_Union[Radio, _Mapping]]] = ..., vaps: _Optional[_Iterable[_Union[VapInfo, _Mapping]]] = ..., interfaces: _Optional[_Iterable[_Union[Interface, _Mapping]]] = ..., tunnels: _Optional[_Iterable[_Union[Tunnel, _Mapping]]] = ..., wireless_clients: _Optional[_Iterable[_Union[WirelessClient, _Mapping]]] = ..., switches: _Optional[_Iterable[_Union[Switch, _Mapping]]] = ..., wired_clients: _Optional[_Iterable[_Union[WiredClient, _Mapping]]] = ..., device_stats: _Optional[_Iterable[_Union[DeviceStats, _Mapping]]] = ..., radio_stats: _Optional[_Iterable[_Union[RadioStats, _Mapping]]] = ..., interface_stats: _Optional[_Iterable[_Union[InterfaceStats, _Mapping]]] = ..., vap_stats: _Optional[_Iterable[_Union[VapStats, _Mapping]]] = ..., client_stats: _Optional[_Iterable[_Union[ClientStats, _Mapping]]] = ..., tunnel_stats: _Optional[_Iterable[_Union[TunnelStats, _Mapping]]] = ..., wids_events: _Optional[_Iterable[_Union[WIDSEvent, _Mapping]]] = ..., modem_stats: _Optional[_Iterable[_Union[ModemStats, _Mapping]]] = ..., role_stats: _Optional[_Iterable[_Union[RoleStats, _Mapping]]] = ..., vlan_stats: _Optional[_Iterable[_Union[VlanStats, _Mapping]]] = ..., ssid_stats: _Optional[_Iterable[_Union[SsidStats, _Mapping]]] = ..., ipprobe_stats: _Optional[_Iterable[_Union[TunnelIpProbeStats, _Mapping]]] = ..., rogue_events: _Optional[_Iterable[_Union[RogueEvent, _Mapping]]] = ..., mobility_controllers: _Optional[_Iterable[_Union[MobilityController, _Mapping]]] = ..., uplinks: _Optional[_Iterable[_Union[Uplink, _Mapping]]] = ..., uplink_stats: _Optional[_Iterable[_Union[UplinkStats, _Mapping]]] = ..., uplink_wan_stats: _Optional[_Iterable[_Union[UplinkWanStats, _Mapping]]] = ..., uplink_probe_stats: _Optional[_Iterable[_Union[UplinkIpProbeStats, _Mapping]]] = ..., uplink_speedtest: _Optional[_Iterable[_Union[UplinkSpeedtest, _Mapping]]] = ..., device_neighbours: _Optional[_Iterable[_Union[DeviceNeighbours, _Mapping]]] = ..., notification: _Optional[_Iterable[_Union[Notification, _Mapping]]] = ..., switch_stacks: _Optional[_Iterable[_Union[SwitchStack, _Mapping]]] = ..., ike_tunnels: _Optional[_Iterable[_Union[IkeTunnel, _Mapping]]] = ..., switch_vlan_info: _Optional[_Union[SwitchVlanInfo, _Mapping]] = ..., vlans: _Optional[_Iterable[_Union[Vlan, _Mapping]]] = ..., vsx: _Optional[_Union[VSXState, _Mapping]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class MonitoringStateInformation(_message.Message):
    __slots__ = ("customer_id", "mobility_controllers", "switches", "swarms", "aps", "vaps", "radios", "interfaces", "networks", "tunnels", "wireless_clients", "wired_clients", "uplinks", "switch_stacks", "ike_tunnels", "data_elements", "timestamp")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    MOBILITY_CONTROLLERS_FIELD_NUMBER: _ClassVar[int]
    SWITCHES_FIELD_NUMBER: _ClassVar[int]
    SWARMS_FIELD_NUMBER: _ClassVar[int]
    APS_FIELD_NUMBER: _ClassVar[int]
    VAPS_FIELD_NUMBER: _ClassVar[int]
    RADIOS_FIELD_NUMBER: _ClassVar[int]
    INTERFACES_FIELD_NUMBER: _ClassVar[int]
    NETWORKS_FIELD_NUMBER: _ClassVar[int]
    TUNNELS_FIELD_NUMBER: _ClassVar[int]
    WIRELESS_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    WIRED_CLIENTS_FIELD_NUMBER: _ClassVar[int]
    UPLINKS_FIELD_NUMBER: _ClassVar[int]
    SWITCH_STACKS_FIELD_NUMBER: _ClassVar[int]
    IKE_TUNNELS_FIELD_NUMBER: _ClassVar[int]
    DATA_ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    mobility_controllers: _containers.RepeatedCompositeFieldContainer[MobilityController]
    switches: _containers.RepeatedCompositeFieldContainer[Switch]
    swarms: _containers.RepeatedCompositeFieldContainer[Swarm]
    aps: _containers.RepeatedCompositeFieldContainer[Ap]
    vaps: _containers.RepeatedCompositeFieldContainer[VapInfo]
    radios: _containers.RepeatedCompositeFieldContainer[Radio]
    interfaces: _containers.RepeatedCompositeFieldContainer[Interface]
    networks: _containers.RepeatedCompositeFieldContainer[Network]
    tunnels: _containers.RepeatedCompositeFieldContainer[Tunnel]
    wireless_clients: _containers.RepeatedCompositeFieldContainer[WirelessClient]
    wired_clients: _containers.RepeatedCompositeFieldContainer[WiredClient]
    uplinks: _containers.RepeatedCompositeFieldContainer[Uplink]
    switch_stacks: _containers.RepeatedCompositeFieldContainer[SwitchStack]
    ike_tunnels: _containers.RepeatedCompositeFieldContainer[IkeTunnel]
    data_elements: _containers.RepeatedScalarFieldContainer[DataElement]
    timestamp: int
    def __init__(self, customer_id: _Optional[str] = ..., mobility_controllers: _Optional[_Iterable[_Union[MobilityController, _Mapping]]] = ..., switches: _Optional[_Iterable[_Union[Switch, _Mapping]]] = ..., swarms: _Optional[_Iterable[_Union[Swarm, _Mapping]]] = ..., aps: _Optional[_Iterable[_Union[Ap, _Mapping]]] = ..., vaps: _Optional[_Iterable[_Union[VapInfo, _Mapping]]] = ..., radios: _Optional[_Iterable[_Union[Radio, _Mapping]]] = ..., interfaces: _Optional[_Iterable[_Union[Interface, _Mapping]]] = ..., networks: _Optional[_Iterable[_Union[Network, _Mapping]]] = ..., tunnels: _Optional[_Iterable[_Union[Tunnel, _Mapping]]] = ..., wireless_clients: _Optional[_Iterable[_Union[WirelessClient, _Mapping]]] = ..., wired_clients: _Optional[_Iterable[_Union[WiredClient, _Mapping]]] = ..., uplinks: _Optional[_Iterable[_Union[Uplink, _Mapping]]] = ..., switch_stacks: _Optional[_Iterable[_Union[SwitchStack, _Mapping]]] = ..., ike_tunnels: _Optional[_Iterable[_Union[IkeTunnel, _Mapping]]] = ..., data_elements: _Optional[_Iterable[_Union[DataElement, str]]] = ..., timestamp: _Optional[int] = ...) -> None: ...

class KeyValueData(_message.Message):
    __slots__ = ("key", "value")
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class Notification(_message.Message):
    __slots__ = ("id", "type", "setting_id", "device_id", "severity", "timestamp", "state", "description", "extra")
    class Severity(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Normal: _ClassVar[Notification.Severity]
        Warning: _ClassVar[Notification.Severity]
        Minor: _ClassVar[Notification.Severity]
        Major: _ClassVar[Notification.Severity]
        Critical: _ClassVar[Notification.Severity]
    Normal: Notification.Severity
    Warning: Notification.Severity
    Minor: Notification.Severity
    Major: Notification.Severity
    Critical: Notification.Severity
    class NotificationState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        Open: _ClassVar[Notification.NotificationState]
        Close: _ClassVar[Notification.NotificationState]
    Open: Notification.NotificationState
    Close: Notification.NotificationState
    ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SETTING_ID_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    SEVERITY_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    EXTRA_FIELD_NUMBER: _ClassVar[int]
    id: str
    type: str
    setting_id: str
    device_id: str
    severity: Notification.Severity
    timestamp: int
    state: Notification.NotificationState
    description: str
    extra: _containers.RepeatedCompositeFieldContainer[KeyValueData]
    def __init__(self, id: _Optional[str] = ..., type: _Optional[str] = ..., setting_id: _Optional[str] = ..., device_id: _Optional[str] = ..., severity: _Optional[_Union[Notification.Severity, str]] = ..., timestamp: _Optional[int] = ..., state: _Optional[_Union[Notification.NotificationState, str]] = ..., description: _Optional[str] = ..., extra: _Optional[_Iterable[_Union[KeyValueData, _Mapping]]] = ...) -> None: ...

class SwitchVlanInfo(_message.Message):
    __slots__ = ("device_id", "vlans")
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    VLANS_FIELD_NUMBER: _ClassVar[int]
    device_id: str
    vlans: _containers.RepeatedCompositeFieldContainer[SwitchVlan]
    def __init__(self, device_id: _Optional[str] = ..., vlans: _Optional[_Iterable[_Union[SwitchVlan, _Mapping]]] = ...) -> None: ...

class SwitchVlan(_message.Message):
    __slots__ = ("id", "name", "tagged_ports", "untagged_ports", "primary_vlan_id", "primary_vlan_type", "promiscuous_ports", "isl_ports", "is_management_vlan", "is_voice_enabled", "is_jumbo_enabled", "is_igmp_enabled", "ipaddress", "status", "oper_state_reason", "type", "access_ports")
    class VlanStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        UP: _ClassVar[SwitchVlan.VlanStatus]
        DOWN: _ClassVar[SwitchVlan.VlanStatus]
    UP: SwitchVlan.VlanStatus
    DOWN: SwitchVlan.VlanStatus
    class VlanType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        STATIC: _ClassVar[SwitchVlan.VlanType]
        DYNAMIC: _ClassVar[SwitchVlan.VlanType]
        INTERNAL: _ClassVar[SwitchVlan.VlanType]
        DEFAULT: _ClassVar[SwitchVlan.VlanType]
    STATIC: SwitchVlan.VlanType
    DYNAMIC: SwitchVlan.VlanType
    INTERNAL: SwitchVlan.VlanType
    DEFAULT: SwitchVlan.VlanType
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TAGGED_PORTS_FIELD_NUMBER: _ClassVar[int]
    UNTAGGED_PORTS_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_VLAN_ID_FIELD_NUMBER: _ClassVar[int]
    PRIMARY_VLAN_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROMISCUOUS_PORTS_FIELD_NUMBER: _ClassVar[int]
    ISL_PORTS_FIELD_NUMBER: _ClassVar[int]
    IS_MANAGEMENT_VLAN_FIELD_NUMBER: _ClassVar[int]
    IS_VOICE_ENABLED_FIELD_NUMBER: _ClassVar[int]
    IS_JUMBO_ENABLED_FIELD_NUMBER: _ClassVar[int]
    IS_IGMP_ENABLED_FIELD_NUMBER: _ClassVar[int]
    IPADDRESS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    OPER_STATE_REASON_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ACCESS_PORTS_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: str
    tagged_ports: _containers.RepeatedScalarFieldContainer[str]
    untagged_ports: _containers.RepeatedScalarFieldContainer[str]
    primary_vlan_id: int
    primary_vlan_type: str
    promiscuous_ports: _containers.RepeatedScalarFieldContainer[str]
    isl_ports: _containers.RepeatedScalarFieldContainer[str]
    is_management_vlan: bool
    is_voice_enabled: bool
    is_jumbo_enabled: bool
    is_igmp_enabled: bool
    ipaddress: IpAddress
    status: SwitchVlan.VlanStatus
    oper_state_reason: str
    type: SwitchVlan.VlanType
    access_ports: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., tagged_ports: _Optional[_Iterable[str]] = ..., untagged_ports: _Optional[_Iterable[str]] = ..., primary_vlan_id: _Optional[int] = ..., primary_vlan_type: _Optional[str] = ..., promiscuous_ports: _Optional[_Iterable[str]] = ..., isl_ports: _Optional[_Iterable[str]] = ..., is_management_vlan: bool = ..., is_voice_enabled: bool = ..., is_jumbo_enabled: bool = ..., is_igmp_enabled: bool = ..., ipaddress: _Optional[_Union[IpAddress, _Mapping]] = ..., status: _Optional[_Union[SwitchVlan.VlanStatus, str]] = ..., oper_state_reason: _Optional[str] = ..., type: _Optional[_Union[SwitchVlan.VlanType, str]] = ..., access_ports: _Optional[_Iterable[str]] = ...) -> None: ...

class Vlan(_message.Message):
    __slots__ = ("action", "vlan_id", "ipv4", "ipv6_ll", "ipv6_1", "ipv6_2", "ipv6_3", "oper_state", "description", "admin_state", "addr_mode", "timestamp", "device_id")
    ACTION_FIELD_NUMBER: _ClassVar[int]
    VLAN_ID_FIELD_NUMBER: _ClassVar[int]
    IPV4_FIELD_NUMBER: _ClassVar[int]
    IPV6_LL_FIELD_NUMBER: _ClassVar[int]
    IPV6_1_FIELD_NUMBER: _ClassVar[int]
    IPV6_2_FIELD_NUMBER: _ClassVar[int]
    IPV6_3_FIELD_NUMBER: _ClassVar[int]
    OPER_STATE_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    ADMIN_STATE_FIELD_NUMBER: _ClassVar[int]
    ADDR_MODE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    action: Action
    vlan_id: int
    ipv4: IpAddress
    ipv6_ll: IpAddress
    ipv6_1: IpAddress
    ipv6_2: IpAddress
    ipv6_3: IpAddress
    oper_state: Status
    description: str
    admin_state: Status
    addr_mode: str
    timestamp: int
    device_id: str
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., vlan_id: _Optional[int] = ..., ipv4: _Optional[_Union[IpAddress, _Mapping]] = ..., ipv6_ll: _Optional[_Union[IpAddress, _Mapping]] = ..., ipv6_1: _Optional[_Union[IpAddress, _Mapping]] = ..., ipv6_2: _Optional[_Union[IpAddress, _Mapping]] = ..., ipv6_3: _Optional[_Union[IpAddress, _Mapping]] = ..., oper_state: _Optional[_Union[Status, str]] = ..., description: _Optional[str] = ..., admin_state: _Optional[_Union[Status, str]] = ..., addr_mode: _Optional[str] = ..., timestamp: _Optional[int] = ..., device_id: _Optional[str] = ...) -> None: ...

class VSXState(_message.Message):
    __slots__ = ("action", "device_id", "role", "peer_role", "isl_port", "peer_isl_port", "keepalive_peer_ip", "keepalive_src_ip", "last_sync_timestamp", "mac", "peer_mac", "config_sync_disable", "islp_device_state_value", "config_sync_state_value", "isl_mgmt_state_value", "nae_state_value", "https_server_state_value")
    class DeviceRole(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        PRIMARY: _ClassVar[VSXState.DeviceRole]
        SECONDARY: _ClassVar[VSXState.DeviceRole]
    PRIMARY: VSXState.DeviceRole
    SECONDARY: VSXState.DeviceRole
    class ISLPDeviceState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        WAITING_FOR_PEER: _ClassVar[VSXState.ISLPDeviceState]
        PEER_ESTABLISHED: _ClassVar[VSXState.ISLPDeviceState]
        SPLIT_SYSTEM_PRIMARY: _ClassVar[VSXState.ISLPDeviceState]
        SPLIT_SYSTEM_SECONDARY: _ClassVar[VSXState.ISLPDeviceState]
        SYNC_PRIMARY: _ClassVar[VSXState.ISLPDeviceState]
        SYNC_SECONDARY: _ClassVar[VSXState.ISLPDeviceState]
        SYNC_SECONDARY_LINKUP_DELAY: _ClassVar[VSXState.ISLPDeviceState]
    WAITING_FOR_PEER: VSXState.ISLPDeviceState
    PEER_ESTABLISHED: VSXState.ISLPDeviceState
    SPLIT_SYSTEM_PRIMARY: VSXState.ISLPDeviceState
    SPLIT_SYSTEM_SECONDARY: VSXState.ISLPDeviceState
    SYNC_PRIMARY: VSXState.ISLPDeviceState
    SYNC_SECONDARY: VSXState.ISLPDeviceState
    SYNC_SECONDARY_LINKUP_DELAY: VSXState.ISLPDeviceState
    class ISLState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        IN_SYNC: _ClassVar[VSXState.ISLState]
        DISABLED: _ClassVar[VSXState.ISLState]
        SW_IMAGE_VERSION_MISMATCH_ERROR: _ClassVar[VSXState.ISLState]
        CONFLICTING_OR_MISSING_DEV_ROLES: _ClassVar[VSXState.ISLState]
        PEER_DB_CONNECTION_ERROR: _ClassVar[VSXState.ISLState]
        CONFIGURATION_SYNC_CONFLICT: _ClassVar[VSXState.ISLState]
        CONFIGURATION_SYNC_MISSING_REFERENCE: _ClassVar[VSXState.ISLState]
        PEER_REACHABLE: _ClassVar[VSXState.ISLState]
        PEER_UNREACHABLE: _ClassVar[VSXState.ISLState]
        OPERATIONAL: _ClassVar[VSXState.ISLState]
        INTER_SWITCH_LINK_MGMT_INIT: _ClassVar[VSXState.ISLState]
        CONFLICTING_OR_MISSING_DEVICE_ROLES: _ClassVar[VSXState.ISLState]
        INTER_SWITCH_LINK_DOWN: _ClassVar[VSXState.ISLState]
        INTERNAL_ERROR: _ClassVar[VSXState.ISLState]
    IN_SYNC: VSXState.ISLState
    DISABLED: VSXState.ISLState
    SW_IMAGE_VERSION_MISMATCH_ERROR: VSXState.ISLState
    CONFLICTING_OR_MISSING_DEV_ROLES: VSXState.ISLState
    PEER_DB_CONNECTION_ERROR: VSXState.ISLState
    CONFIGURATION_SYNC_CONFLICT: VSXState.ISLState
    CONFIGURATION_SYNC_MISSING_REFERENCE: VSXState.ISLState
    PEER_REACHABLE: VSXState.ISLState
    PEER_UNREACHABLE: VSXState.ISLState
    OPERATIONAL: VSXState.ISLState
    INTER_SWITCH_LINK_MGMT_INIT: VSXState.ISLState
    CONFLICTING_OR_MISSING_DEVICE_ROLES: VSXState.ISLState
    INTER_SWITCH_LINK_DOWN: VSXState.ISLState
    INTERNAL_ERROR: VSXState.ISLState
    ACTION_FIELD_NUMBER: _ClassVar[int]
    DEVICE_ID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    PEER_ROLE_FIELD_NUMBER: _ClassVar[int]
    ISL_PORT_FIELD_NUMBER: _ClassVar[int]
    PEER_ISL_PORT_FIELD_NUMBER: _ClassVar[int]
    KEEPALIVE_PEER_IP_FIELD_NUMBER: _ClassVar[int]
    KEEPALIVE_SRC_IP_FIELD_NUMBER: _ClassVar[int]
    LAST_SYNC_TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    MAC_FIELD_NUMBER: _ClassVar[int]
    PEER_MAC_FIELD_NUMBER: _ClassVar[int]
    CONFIG_SYNC_DISABLE_FIELD_NUMBER: _ClassVar[int]
    ISLP_DEVICE_STATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    CONFIG_SYNC_STATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    ISL_MGMT_STATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    NAE_STATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    HTTPS_SERVER_STATE_VALUE_FIELD_NUMBER: _ClassVar[int]
    action: Action
    device_id: str
    role: VSXState.DeviceRole
    peer_role: VSXState.DeviceRole
    isl_port: str
    peer_isl_port: str
    keepalive_peer_ip: IpAddress
    keepalive_src_ip: IpAddress
    last_sync_timestamp: int
    mac: MacAddress
    peer_mac: MacAddress
    config_sync_disable: bool
    islp_device_state_value: VSXState.ISLPDeviceState
    config_sync_state_value: VSXState.ISLState
    isl_mgmt_state_value: VSXState.ISLState
    nae_state_value: VSXState.ISLState
    https_server_state_value: VSXState.ISLState
    def __init__(self, action: _Optional[_Union[Action, str]] = ..., device_id: _Optional[str] = ..., role: _Optional[_Union[VSXState.DeviceRole, str]] = ..., peer_role: _Optional[_Union[VSXState.DeviceRole, str]] = ..., isl_port: _Optional[str] = ..., peer_isl_port: _Optional[str] = ..., keepalive_peer_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., keepalive_src_ip: _Optional[_Union[IpAddress, _Mapping]] = ..., last_sync_timestamp: _Optional[int] = ..., mac: _Optional[_Union[MacAddress, _Mapping]] = ..., peer_mac: _Optional[_Union[MacAddress, _Mapping]] = ..., config_sync_disable: bool = ..., islp_device_state_value: _Optional[_Union[VSXState.ISLPDeviceState, str]] = ..., config_sync_state_value: _Optional[_Union[VSXState.ISLState, str]] = ..., isl_mgmt_state_value: _Optional[_Union[VSXState.ISLState, str]] = ..., nae_state_value: _Optional[_Union[VSXState.ISLState, str]] = ..., https_server_state_value: _Optional[_Union[VSXState.ISLState, str]] = ...) -> None: ...
