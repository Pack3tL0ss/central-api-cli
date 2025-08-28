import os
from typing import Dict, List, Literal, Optional, Sequence, TypedDict, Union  # future annotations does not work here, need to use Union to support py < 3.10

from yarl import URL

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
PortalAuthTypes = Sequence[PortalAuthType]
CacheTableName = Literal["devices", "sites", "groups", "labels", "macs", "mpsk", "subscriptions"]
DynamicAntenna = Literal["narrow", "wide"]
RadioType = Literal["2.4", "5", "6"]
MPSKStatus = Literal["enabled", "disabled"]
CertType = Literal["SERVER_CERT", "CA_CERT", "CRL", "INTERMEDIATE_CA", "OCSP_RESPONDER_CERT", "OCSP_SIGNER_CERT", "PUBLIC_CERT"]
CertFormat = Literal["PEM", "DER", "PKCS12"]
GLPDeviceTypes = Literal["ap", "switch", "gw", "bridge", "sdwan"]
PrimaryDeviceTypes = Literal["ap", "cx", "sw", "gw"]
SendConfigTypes = Literal["ap", "gw"]
CloudAuthUploadTypes = Literal["mpsk", "mac"]
TableFormat = Literal["json", "yaml", "csv", "rich", "tabulate", "simple", "action"]
LogType = Literal["event", "audit"]
InsightSeverityType = Literal["high", "med", "low"]
JSON_TYPE = Union[List, Dict, str]

class CacheSiteDict(TypedDict):
    name: str
    id: int
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    lon: Optional[str]
    lat: Optional[str]
    devices: int

class UnsetType:
    def __repr__(self):
        return "UNSET"  # pragma: no cover

UNSET = UnsetType()

# These typedefs are done this way (the backup manually typed class then try to import the real type) as vscode
# fails to resolve or learn the attributes for the manual class when it's in the except block

# typing.Self added in python 3.11+
class Self:
    def __init__(self):
        self.serial: str  # pragma: no cover

try:
    from typing import Self  # noqa
except ImportError:
    ...