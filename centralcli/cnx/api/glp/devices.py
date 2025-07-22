from __future__ import annotations

from centralcli import log, config, constants
from centralcli.response import Session
import time
from ...client import NewCentralBase
from ...exceptions import InvalidConfigException
from .... import utils

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from centralcli import Response
    from centralcli.logger import MyLogger

START = time.monotonic()


def get_conn_from_file(workspace, logger: MyLogger = log) -> NewCentralBase:
    """Creates an instance of NewCentralBase based on config file.

    Refer to documentation for correct format of config file.

    Args:
        account_name (str): Account name defined in the config file.
        logger (MyLogger, optional): log method. Defaults to log.

    Returns:
        [NewCentralBase]: An instance of class NewCentralBase
            Used to manage Auth and Tokens.

    Raises:
        InvalidConfigException: If config is not valid.
    """
    if not config.glp.ok:
        raise InvalidConfigException(f"{config.file}... Invalid or missing config items for New Central functionality.")

    conn = NewCentralBase(config.glp.token_info)

    return conn

class GlpDevicesApi(Session):
    def __init__(self, workspace: str = "default"):
        self.silent = False  # toggled in _batch_request to squelch Auto logging in Response
        if config.valid and constants.do_load_pycentral():  # TODO constants is a strange place for this to live
            self.auth = get_conn_from_file(workspace)
            super().__init__(auth=self.auth, base_url=config.glp.base_url)

    # TODO move references to this strip_none from get post etc methods use the one in utils.  Then remove from central.py
    @staticmethod
    def strip_none(_dict: dict | None) -> dict | None:
        """strip all keys from a dict where value is NoneType"""
        if not isinstance(_dict, dict):
            return _dict

        return {k: v for k, v in _dict.items() if v is not None}

    async def get_glp_devices(self) -> Response:
        url = "/devices/v1/devices"

        return await self.get(url)

    async def assign_subscription_to_device(self, device_ids: list[str] | str, subscription_ids: list[str] | str) -> Response:
        url = "/devices/v2beta1/devices"
        header = {"Content-Type": "application/merge-patch+json"}
        device_ids = utils.listify(device_ids)
        subscription_ids = utils.listify(subscription_ids)
        # TODO MAX 25 DEVICES

        query_str = "&".join([f"id={serial}" for serial in device_ids])
        url = f"{url}?{query_str}"

        payload = {
            "subscription": [
                {
                "id": sub
                } for sub in subscription_ids
            ]
        }

        return await self.patch(url, json_data=payload, headers=header)


