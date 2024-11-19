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