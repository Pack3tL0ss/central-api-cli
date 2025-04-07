from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class MsgProto(_message.Message):
    __slots__ = ("subject", "data", "timestamp", "customer_id", "msp_id")
    SUBJECT_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    CUSTOMER_ID_FIELD_NUMBER: _ClassVar[int]
    MSP_ID_FIELD_NUMBER: _ClassVar[int]
    subject: str
    data: bytes
    timestamp: int
    customer_id: str
    msp_id: str
    def __init__(self, subject: _Optional[str] = ..., data: _Optional[bytes] = ..., timestamp: _Optional[int] = ..., customer_id: _Optional[str] = ..., msp_id: _Optional[str] = ...) -> None: ...
