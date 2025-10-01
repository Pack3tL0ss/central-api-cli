from __future__ import annotations

from typing import TYPE_CHECKING

from ... import constants, utils

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response

class TroubleShootingAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_ts_commands(
        self,
        device_type: constants.DeviceTypes,
    ) -> Response:
        """List Troubleshooting Commands.

        Args:
            device_type (Literal['ap', 'cx', 'sw', 'gw']): Device Type.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/troubleshooting/v1/commands"

        params = {
            'device_type': constants.lib_to_api(device_type, "tshoot")
        }

        return await self.session.get(url, params=params)


    async def start_ts_session(
        self,
        serial: str,
        device_type: constants.DeviceTypes,
        commands: int | list[int, dict] | dict,
    ) -> Response:
        """Start Troubleshooting Session.

        Args:
            serial (str): Serial of device
            device_type (Literal['ap', 'cx', 'sw', 'gw']): Device Type.
            commands (int | List[int, dict] | dict): a single command_id, or a List of command_ids (For commands with no arguments)
                OR a dict {command_id: {argument1_name: argument1_value, argument2_name: argument2_value}}

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"
        commands = utils.listify(commands)
        cmds = []
        for cmd in commands:
            if isinstance(cmd, int):
                cmds += [{"command_id": cmd}]
            elif isinstance(cmd, dict):
                cmds += [
                    {
                        "command_id": cid,
                        "arguments": [{"name": k, "value": v} for k, v in cmd[cid].items()]
                    }
                    for cid in cmd
                ]

        json_data = {
            'device_type': constants.lib_to_api(device_type, "tshoot"),
            'commands': cmds
        }

        return await self.session.post(url, json_data=json_data)

    async def get_ts_output(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Get Troubleshooting Output.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        params = {
            'session_id': session_id
        }

        return await self.session.get(url, params=params)

    async def clear_ts_session(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Clear Troubleshooting Session and output for device.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for each troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        params = {
            'session_id': session_id
        }

        return await self.session.delete(url, params=params)

    # API-FLAW returns 404 if there are no sessions running
    async def get_ts_session_id(
        self,
        serial: str,
    ) -> Response:
        """Get Troubleshooting Session ID for a device.

        Args:
            serial (str): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/session"

        return await self.session.get(url)