from __future__ import annotations

from typing import TYPE_CHECKING

from centralcli.client import Session

if TYPE_CHECKING:
    from centralcli.response import Response


class ConfigAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_system_info(
            self,
            serial: str = None,  # use serial to get scope_id
            library: bool = False,  # view-type LOCAL or LIBRARY
            object_type: str | None = None,  # object-type LOCAL or SHARED  need Enum  None results in both
            device_function: str | None = None,  # CAMPUS_AP, SWITCH... need Enum
            effective: bool = False,  # True returns hierarchical merged config, False returns config a specific scope
            detailed: bool = False,  # True returns annotations in json to indicate type of object, scope and device function.
            offset: int = 0,
            limit: int = 1000,
        ) -> Response:
        url = "/network-config/v1alpha1/system-info"
        params = {
            "scope-id": "197666073",  # "74160150531653632",
            "view-type": "LOCAL" if not library else "LIBRARY",  # TODO need common func to validate convert all bools to needed params
            # "device-function": device_function,
            "effective": str(effective),
            "detailed": str(detailed),
            # "offset": offset,
            # "limit": limit
        }

        return await self.session.get(url, params=params)
