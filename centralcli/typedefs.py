from yarl import URL
from typing import Union, Literal, List, Dict  # future annotations does not work here, need to use Union to support py < 3.10



StrOrURL = Union[str, URL]
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
CacheTableName = Literal["devices", "sites", "groups", "labels", "macs", "mpsk"]
DynamicAntenna = Literal["narrow", "wide"]
RadioType = Literal["2.4", "5", "6"]
MPSKStatus = Literal["enabled", "disabled"]
CertType = Literal["SERVER_CERT", "CA_CERT", "CRL", "INTERMEDIATE_CA", "OCSP_RESPONDER_CERT", "OCSP_SIGNER_CERT", "PUBLIC_CERT"]
CertFormat = Literal["PEM", "DER", "PKCS12"]

# StrEnum available python 3.11+
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum
    class StrEnum(Enum):
        ...