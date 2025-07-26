from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from ... import Response, constants

if TYPE_CHECKING:
    from ... import Session

class FirmwareAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_vc_firmware(
        self,
        swarm_id: str = None,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Firmware Details of Swarms.

        Args:
            swarm_id: (str, optional): Providing swarm_id results in details for that swarm.
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 100.

            Providing swarm_id is effectively a filter, it provides no additional detail.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/swarms"
        if swarm_id:
            url = f"{url}/{swarm_id}"
            params = {}
        else:
            params = {
                'group': group,
                'offset': offset,
                'limit': limit
            }

        return await self.session.get(url, params=params)

    async def get_firmware_version_list(
        self,
        device_type: constants.DeviceTypes = None,
        swarm_id: str = None,
        serial: str = None,
    ) -> Response:
        """List Firmware Version.

        Provide one and only one of the following.

        Args:
            device_type (str, optional): Specify one of ap, gw, sw, cx
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/versions"

        if [device_type, swarm_id, serial].count(None) != 2:
            raise ValueError("You must specify one and one of device_type, swarm_id, serial parameters")

        params = {
            'device_type': None if device_type is None else constants.lib_to_api(device_type, "firmware"),
            'swarm_id': swarm_id,
            'serial': serial
        }

        return await self.session.get(url, params=params)

    # API-FLAW no API to upgrade cluster
    # https://internal-ui.central.arubanetworks.com/firmware/controller/clusters/upgrade is what the UI calls when you upgrade via UI
    # payload: {"reboot":true,"firmware_version":"10.5.0.0-beta_87046","devices":[],"clusters":[72],"when":0,"timezone":"+00:00","partition":"primary"}
    async def upgrade_firmware(
        self,
        scheduled_at: int = None,
        swarm_id: str = None,
        serial: str = None,
        group: str = None,
        device_type: constants.DeviceTypes = None,
        firmware_version: str = None,
        model: str = None,
        reboot: bool = False,
        forced: bool = False,
    ) -> Response:
        """Initiate firmware upgrade on device(s).

        You can only specify one of device_type, swarm_id or serial parameters

        // Used by upgrade [device|group|swarm] //

        Args:
            scheduled_at (int, optional): When to schedule upgrade (epoch seconds). Defaults to None (Now).
            swarm_id (str, optional): Upgrade a specific swarm by id. Defaults to None.
            serial (str, optional): Upgrade a specific device by serial. Defaults to None.
            group (str, optional): Upgrade devices belonging to group. Defaults to None.
            device_type (Literal["ap", "gw", "cx", "sw"]): Type of device to upgrade. Defaults to None.
            firmware_version (str, optional): Version to upgrade to. Defaults to None(recommended version).
            model (str, optional): To initiate upgrade at group level for specific model family. Applicable
                only for Aruba switches. Defaults to None.
            reboot (bool, optional): Automatically reboot device after firmware download. Defaults to False.
            forced (bool, optional): Use True for forcing the upgrade of a gateway which is part of a cluster. Defaults to False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade"

        json_data = {
            'firmware_scheduled_at': scheduled_at,
            'swarm_id': swarm_id,
            'serial': serial,
            'group': group,
            'device_type': None if not device_type else constants.lib_to_api(device_type, "firmware"),
            'firmware_version': firmware_version,
            'reboot': reboot,
            'model': model,
            'forced': forced
        }

        return await self.session.post(url, json_data=json_data)

    async def cancel_upgrade(
        self,
        device_type: constants.DeviceTypes = None,
        serial: str = None,
        swarm_id: str = None,
        group: str = None,
    ) -> Response:
        """Cancel scheduled firmware upgrade.

        You can only specify one of device_type, swarm_id or serial parameters

        Args:
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Specify one of "cx|sw|ap|gw  (sw = aos-sw)"
            serial (str, optional): Serial of device
            swarm_id (str): Swarm ID
            group (str): Specify Group Name to cancel upgrade for devices in that group

        Returns:
            Response: CentralAPI Response object
        """
        device_type = None if not device_type else constants.lib_to_api(device_type, 'firmware')
        url = "/firmware/v1/upgrade/cancel"

        json_data = {
            'swarm_id': swarm_id,
            'serial': serial,
            'device_type': device_type,
            'group': group
        }

        return await self.session.post(url, json_data=json_data)

    # API-FLAW only accepts swarm id for IAP, AOS10 show as IAP but no swarm id.  serial is rejected.
    # CX will return resp like it works, but nothing ever happens
    async def get_upgrade_status(self, swarm_id: str = None, serial: str = None) -> Response:
        """Get firmware upgrade status.

        // Used by show upgrade [device-iden] //

        Args:
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/status"

        params = {
            "swarm_id": swarm_id,
            "serial": serial
        }

        return await self.session.get(url, params=params)

    async def get_firmware_compliance(self, device_type: constants.DeviceTypes, group: str = None) -> Response:
        """Get Firmware Compliance Version.

        // Used by show firmware compliance [ap|gw|sw|cx] [group-name] //

        Args:
            device_type (str): Specify one of "ap|gw|sw|sx"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        # API method returns 404 if compliance is not set!
        url = "/firmware/v1/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.session.get(url, params=params)

    async def delete_firmware_compliance(self, device_type: constants.DeviceTypes, group: str = None) -> Response:
        """Clear Firmware Compliance Version.

        // Used by delete firmware compliance [ap|gw|sw|cx] [group] //

        Args:
            device_type (str): Specify one of "ap|gw|sw|cx"
            group (str, optional): Group name. Defaults to None (Global Compliance)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.session.delete(url, params=params)

    async def set_firmware_compliance(
        self,
        device_type: constants.DeviceTypes,
        group: str,
        version: str,
        compliance_scheduled_at: int,
        reboot: bool = True,  # Only applies to MAS all others reboot regardless.  cencli doesn't support MAS
        allow_unsupported_version: bool = False,
    ) -> Response:
        """Set Firmware Compliance version (for group/device-type).

        Args:
            device_type (str): Specify one of "ap|sw|cx|gw"
            group (str): Group name
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            compliance_scheduled_at (int): Firmware compliance will be schedule at,
                compliance_scheduled_at - current time. compliance_scheduled_at is epoch in seconds
                and default value is current time.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches, CX switches, and controller
                since IAP reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v2/upgrade/compliance_version"
        device_type = constants.lib_to_api(device_type, 'firmware')


        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at
        }

        return await self.session.post(url, json_data=json_data)

    async def get_device_firmware_details(
        self,
        serial: str,
    ) -> Response:
        """Firmware Details of Device.

        Args:
            serial (str): Serial of the device for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/devices/{serial}"

        return await self.session.get(url)

    async def get_device_firmware_details_by_type(
        self,
        device_type: Literal["mas", "cx", "sw", "gw", "ap"],
        group: str = None,
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """List Firmware Details by type for switches or gateways (Not valid for APs).

        Args:
            device_type (str): Specify one of "mas|sw|cx|gw|ap"
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. max 1000, Defaults to 500.

        Returns:
            Response: CentralAPI Response object

        Raises:
            ValueError: if device_type is not valid/supported by API endpoint.
        """
        url = "/firmware/v1/devices"
        device_type = constants.lib_to_api(device_type, "firmware")

        params = {
            'device_type': device_type,
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_all_swarms_firmware_details(
        self,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Firmware Details of all Swarms.

        Args:
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 20 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/swarms"

        params = {
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)


    async def get_swarm_firmware_details(
        self,
        swarm_id: str,
    ) -> Response:
        """Firmware Details of Swarm or AOS10 AP.

        Args:
            swarm_id (str): Swarm ID for which the firmware detail to be queried
                AOS10 APs provide serial as swarm_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/swarms/{swarm_id}"

        return await self.session.get(url)

    async def check_firmware_available(
        self,
        device_type: constants.DeviceTypes,
        firmware_version: str,
    ) -> Response:
        """Firmware Version.

        Args:
            device_type (str): Specify one of "cx", "sw", "ap", "gw"
            firmware_version (str): firmware version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/versions/{firmware_version}"
        device_type = constants.lib_to_api(device_type, "firmware")

        params = {
            'device_type': device_type
        }

        return await self.session.get(url, params=params)