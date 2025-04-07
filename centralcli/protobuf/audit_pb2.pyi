from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class classification(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONFIGURATION: _ClassVar[classification]
    FIRMWARE: _ClassVar[classification]
    DEVICE_MGMT: _ClassVar[classification]
CONFIGURATION: classification
FIRMWARE: classification
DEVICE_MGMT: classification

class mac_address(_message.Message):
    __slots__ = ("addr",)
    ADDR_FIELD_NUMBER: _ClassVar[int]
    addr: bytes
    def __init__(self, addr: _Optional[bytes] = ...) -> None: ...

class ip_address(_message.Message):
    __slots__ = ("af", "addr")
    class addr_family(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        ADDR_FAMILY_UNSPEC: _ClassVar[ip_address.addr_family]
        ADDR_FAMILY_INET: _ClassVar[ip_address.addr_family]
        ADDR_FAMILY_INET6: _ClassVar[ip_address.addr_family]
    ADDR_FAMILY_UNSPEC: ip_address.addr_family
    ADDR_FAMILY_INET: ip_address.addr_family
    ADDR_FAMILY_INET6: ip_address.addr_family
    AF_FIELD_NUMBER: _ClassVar[int]
    ADDR_FIELD_NUMBER: _ClassVar[int]
    af: ip_address.addr_family
    addr: bytes
    def __init__(self, af: _Optional[_Union[ip_address.addr_family, str]] = ..., addr: _Optional[bytes] = ...) -> None: ...

class config(_message.Message):
    __slots__ = ("data", "detailed_data")
    DATA_FIELD_NUMBER: _ClassVar[int]
    DETAILED_DATA_FIELD_NUMBER: _ClassVar[int]
    data: str
    detailed_data: str
    def __init__(self, data: _Optional[str] = ..., detailed_data: _Optional[str] = ...) -> None: ...

class firmware(_message.Message):
    __slots__ = ("data", "detailed_data")
    DATA_FIELD_NUMBER: _ClassVar[int]
    DETAILED_DATA_FIELD_NUMBER: _ClassVar[int]
    data: str
    detailed_data: str
    def __init__(self, data: _Optional[str] = ..., detailed_data: _Optional[str] = ...) -> None: ...

class device_management(_message.Message):
    __slots__ = ("data", "detailed_data")
    DATA_FIELD_NUMBER: _ClassVar[int]
    DETAILED_DATA_FIELD_NUMBER: _ClassVar[int]
    data: str
    detailed_data: str
    def __init__(self, data: _Optional[str] = ..., detailed_data: _Optional[str] = ...) -> None: ...

class audit_message(_message.Message):
    __slots__ = ("customer_id", "timestamp", "service", "group_name", "target", "client_ip", "username", "config_info", "firmware_info", "dm_info")
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    SERVICE_FIELD_NUMBER: _ClassVar[int]
    GROUP_NAME_FIELD_NUMBER: _ClassVar[int]
    TARGET_FIELD_NUMBER: _ClassVar[int]
    CLIENT_IP_FIELD_NUMBER: _ClassVar[int]
    USERNAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_INFO_FIELD_NUMBER: _ClassVar[int]
    FIRMWARE_INFO_FIELD_NUMBER: _ClassVar[int]
    DM_INFO_FIELD_NUMBER: _ClassVar[int]
    customer_id: str
    timestamp: int
    service: classification
    group_name: str
    target: str
    client_ip: ip_address
    username: str
    config_info: config
    firmware_info: firmware
    dm_info: device_management
    def __init__(self, customer_id: _Optional[str] = ..., timestamp: _Optional[int] = ..., service: _Optional[_Union[classification, str]] = ..., group_name: _Optional[str] = ..., target: _Optional[str] = ..., client_ip: _Optional[_Union[ip_address, _Mapping]] = ..., username: _Optional[str] = ..., config_info: _Optional[_Union[config, _Mapping]] = ..., firmware_info: _Optional[_Union[firmware, _Mapping]] = ..., dm_info: _Optional[_Union[device_management, _Mapping]] = ...) -> None: ...
