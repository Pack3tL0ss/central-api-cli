from yarl import URL
from typing import Union, Literal, List, Dict  # future annotations does not work here, need to use Union to support py < 3.10
import os

# We use Union as using | operator results in linter throwing "Variable not allowed in type annotation"

StrOrURL = Union[str, URL]
StrPath = Union[str, os.PathLike[str]]
Method = Literal['GET', 'POST', 'PUT', 'DELETE']
SiteData = Union[
    List[
        Dict[
            str,
            Union[
                str, int, float
            ]
        ]
    ],
    Dict[
        str,
        Union[
            str,
            int,
            float
        ]
    ]
]
PortalAuthType = Literal["user/pass", "anon", "self-reg"]
PortalAuthTypes = List[PortalAuthType]
CacheTableName = Literal["devices", "sites", "groups", "labels", "macs", "mpsk", "subscriptions"]
DynamicAntenna = Literal["narrow", "wide"]
RadioType = Literal["2.4", "5", "6"]
MPSKStatus = Literal["enabled", "disabled"]
CertType = Literal["SERVER_CERT", "CA_CERT", "CRL", "INTERMEDIATE_CA", "OCSP_RESPONDER_CERT", "OCSP_SIGNER_CERT", "PUBLIC_CERT"]
CertFormat = Literal["PEM", "DER", "PKCS12"]
JSON_TYPE = Union[List, Dict, str]

# StrEnum available python 3.11+
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(str, Enum):
        ...
