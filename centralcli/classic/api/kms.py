from __future__ import annotations

from ..client import Session
from ... import Response


class KmsAPI:
    def __init__(self, session: Session):
        self.session = session

    # // -- Not used by commands yet.  undocumented kms api -- //
    async def kms_get_synced_aps(self, mac: str) -> Response:
        url = f"/keymgmt/v1/syncedaplist/{mac}"
        return await self.session.get(url)

    async def kms_get_client_record(self, mac: str) -> Response:
        url = f"/keymgmt/v1/keycache/{mac}"
        return await self.session.get(url)

    async def kms_get_hash(self) -> Response:
        url = "/keymgmt/v1/keyhash"
        return await self.session.get(url)

    async def kms_get_ap_state(self, serial: str) -> Response:
        url = f"/keymgmt/v1/Stats/ap/{serial}"
        return await self.session.get(url)

    # Bad endpoint URL 404
    async def kms_get_health(self) -> Response:
        url = "/keymgmt/v1/health"
        return await self.session.get(url)
