from __future__ import annotations

import time
from typing import TYPE_CHECKING, Literal

from rich.progress import track

from ...response import Response

if TYPE_CHECKING:
    from centralcli.client import Session

class DeviceManagementAPI:
    def __init__(self, session: Session):
        self.session = session

    async def send_bounce_command_to_device(self, serial: str, command: str, port: str) -> Response:
        """Bounce interface or POE (power-over-ethernet) on switch port.  Valid only for Aruba Switches.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
            port (str): Specify interface port in the format of port number for devices of type HPPC
                Switch or slot/chassis/port for CX Switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v2/device/{serial}/action/{command}"

        json_data = {"port": str(port)}

        return await self.session.post(url, json_data=json_data)

    async def send_command_to_device(
        self,
        serial: str,
        command: Literal[
            "reboot",
            "blink_led_on",
            "blink_led_off",
            "blink_led",
            "erase_configuration",
            "save_configuration",
            "halt",
            "config_sync",
        ],
        duration: int = None,
    ) -> Response:
        """Generic commands for device.

        Supported Commands (str):
            - reboot: supported by AP/gateways/MAS Switches/Aruba Switches
            - blink_led_on: Use this command to enable the LED display, supported by IAP/Aruba Switches
            - blink_led_off: Use this command to enable the LED display, supported by IAP/Aruba Switches
            - blink_led: Use this command to blink LED display, Supported on Aruba Switches
            - erase_configuration : Factory default the switch.  Supported on Aruba Switches
            - save_configuration: Saves the running config. supported by IAP/Aruba Switches
            - halt : This command performs a shutdown of the device, supported by Controllers alone.
            - config_sync : This commands performs full refresh of the device config, supported by Controllers alone

        Args:
            serial (str): Serial of device
            command (str): Command to be executed
            duration (int, Optional): Number of seconds to blink_led only applies to blink_led and blink_led_on

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}"

        # TODO cacth invalid actions (not supported on dev)
        responses: list[Response] = []
        responses += [await self.session.post(url)]
        if responses[0].ok and duration and "blink_led" in command and "off" not in command:
            for _ in track(range(1, duration + 1), description="[turquoise2 blink]Blinking LED[/]..."):
                time.sleep(1)
            responses += [await self.session.post(url.replace("_on", "_off"))]
        return responses

    async def kick_users(
        self,
        serial: str = None,
        *,
        kick_all: bool = False,
        mac: str = None,
        ssid: str = None,
    ) -> Response:
        url = f"/device_management/v1/device/{serial}/action/disconnect_user"
        payload = None
        if kick_all:
            payload = {"disconnect_user_all": True}
        elif mac:
            payload = {"disconnect_user_mac": f"{mac}"}
        elif ssid:
            payload = {"disconnect_user_network": f"{ssid}"}

        if payload:
            return await self.session.post(url, json_data=payload)
        else:
            return Response(error="Missing Required Parameters")

    async def get_task_status(
        self,
        task_id: str,
    ) -> Response:
        """Status.

        Args:
            task_id (str): Unique task id to get response of command

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/status/{task_id}"

        return await self.session.get(url)

    async def send_command_to_swarm(
        self,
        swarm_id: str,
        command: Literal[
            "reboot",
            "erase_configuration",
        ]
    ) -> Response:
        """Generic commands for swarm.

        Args:
            swarm_id (str): Swarm ID of device
            command (str): Command mentioned in the description that is to be executed
                valid: 'reboot', 'erase_configuration'

        Returns:
            Response: CentralAPI Response object
        """
        if command == "reboot":
            command = "reboot_swarm"

        url = f"/device_management/v1/swarm/{swarm_id}/action/{command}"

        return await self.session.post(url)

    async def run_speedtest(
        self,
        serial: str,
        host: str = "ndt-iupui-mlab1-den04.mlab-oti.measurement-lab.org",
        options: str = None
    ) -> Response:
        """Run speedtest from device (gateway only)

        Args:
            serial (str): Serial of device
            host (str, Optional): Speed-Test server IP address, Defaults to server in Central Indiana.
            options (str): Formatted string of optional arguments

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/speedtest"

        json_data = {
            'host': host,
            'options': options or ""
        }

        return await self.session.post(url, json_data=json_data)