import os
from typing import Dict, List, Literal, Union  # future annotations does not work here, need to use Union to support py < 3.10

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
PortalAuthTypes = List[PortalAuthType]
CacheTableName = Literal["devices", "sites", "groups", "labels", "macs", "mpsk", "subscriptions"]
DynamicAntenna = Literal["narrow", "wide"]
RadioType = Literal["2.4", "5", "6"]
MPSKStatus = Literal["enabled", "disabled"]
CertType = Literal["SERVER_CERT", "CA_CERT", "CRL", "INTERMEDIATE_CA", "OCSP_RESPONDER_CERT", "OCSP_SIGNER_CERT", "PUBLIC_CERT"]
CertFormat = Literal["PEM", "DER", "PKCS12"]
JSON_TYPE = Union[List, Dict, str]


# These typedefs are done this way (the backup manually typed class then try to import the real type) as vscode
# fails to resolve or learn the attributes for the manual class when it's in the except block

# typing.Self added in python 3.11+
class Self:
    def __init__(self):
        self.serial: str

try:
    from typing import Self  # noqa
except ImportError:
    ...