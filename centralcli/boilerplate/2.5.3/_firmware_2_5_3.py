import sys
import asyncio
import json
from pathlib import Path
from typing import Literal, Union, List


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response
except (ImportError, ModuleNotFoundError) as e:
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response
    else:
        print(pkg_dir.parts)
        raise e

from centralcli.central import CentralApi


class AllCalls(CentralApi):
    def __init__(self):
        super().__init__()

    async def firmware_get_swarms_details(self, group: str = None, offset: int = 0,
                                          limit: int = 100) -> Response:
        """List Firmware Details of Swarms.

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

        return await self.get(url, params=params)

    async def firmware_get_swarm_details(self, swarm_id: str) -> Response:
        """Firmware Details of Swarm.

        Args:
            swarm_id (str): Swarm ID for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def firmware_get_devices_details(self, device_type: str, group: str = None,
                                           offset: int = 0, limit: int = 100) -> Response:
        """List Firmware Details of Devices.

        Args:
            device_type (str): Specify one of "MAS/HP/CONTROLLER"
            group (str, optional): Group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 20 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/devices"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def firmware_get_device_details(self, serial: str) -> Response:
        """Firmware Details of Device.

        Args:
            serial (str): Serial of the device for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/devices/{serial}"

        return await self.get(url)

    async def firmware_get_version_list(self, device_type: str = None, swarm_id: str = None,
                                        serial: str = None) -> Response:
        """List Firmware Version.

        One of device_type, swarm_id, or serial is required.

        Args:
            device_type (str, optional): Specify one of "IAP/MAS/HP/CONTROLLER"
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/versions"

        params = {
            'device_type': device_type,
            'swarm_id': swarm_id,
            'serial': serial
        }

        return await self.get(url, params=params)

    async def firmware_is_image_available(self, device_type: str, firmware_version: str) -> Response:
        """Firmware Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_version (str): firmware version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/versions/{firmware_version}"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def firmware_get_status(self, swarm_id: str = None, serial: str = None) -> Response:
        """Firmware Status.

        Args:
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/status"

        return await self.get(url)

    async def firmware_upgrade_firmware(
        self, scheduled_at: int = None,
        swarm_id: str = None,
        serial: str = None,
        group: str = None,
        device_type: Literal["IAP", "MAS", "HP", "CONTROLLER"] = None,
        firmware_version: str = None,
        reboot: bool = False,
        model: str = None
    ) -> Response:
        """Initiate firmware upgrade on device(s).

        Args:
            scheduled_at (int, optional): When to schedule upgrade (epoch seconds). Defaults to None (Now).
            swarm_id (str, optional): Upgrade a specific swarm by id. Defaults to None.
            serial (str, optional): Upgrade a specific device by serial. Defaults to None.
            group (str, optional): Upgrade devices belonging to group. Defaults to None.
            device_type (str["IAP"|"MAS"|"HP"|"CONTROLLER"]): Type of device to upgrade. Defaults to None.
            firmware_version (str, optional): Version to upgrade to. Defaults to None(recommended version).
            reboot (bool, optional): Automatically reboot device after firmware download. Defaults to False.
            model (str, optional): To initiate upgrade at group level for specific model family. Applicable
                only for Aruba switches. Defaults to None.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade"

        json_data = {
            'firmware_scheduled_at': scheduled_at,
            'swarm_id': swarm_id,
            'serial': serial,
            'group': group,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'reboot': reboot,
            'model': model
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade(self, swarm_id: str, serial: str, device_type: str,
                                      group: str) -> Response:
        """Cancel Scheduled Upgrade.

        Args:
            swarm_id (str): Swarm ID
            serial (str): Serial of device
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str): Specify Group Name to cancel upgrade for devices in that group

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/cancel"

        json_data = {
            'swarm_id': swarm_id,
            'serial': serial,
            'device_type': device_type,
            'group': group
        }

        return await self.post(url, json_data=json_data)

    async def firmware_set_compliance_customer(self, device_type: str, group: str,
                                               firmware_compliance_version: str, reboot: bool,
                                               allow_unsupported_version: bool,
                                               compliance_scheduled_at: int) -> Response:
        """Set Firmware Compliance Version Customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str): Group name
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.
            compliance_scheduled_at (int): Firmware compliance will be schedule at,
                compliance_scheduled_at - current time. compliance_scheduled_at is epoch in seconds
                and default value is current time.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v2/upgrade/compliance_version"

        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': firmware_compliance_version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at
        }

        return await self.post(url, json_data=json_data)

    async def firmware_set_compliance(self, device_type: str, group: str,
                                      firmware_compliance_version: str, reboot: bool,
                                      allow_unsupported_version: bool) -> Response:
        """Set Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str): Group name
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': firmware_compliance_version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version
        }

        return await self.post(url, json_data=json_data)

    async def firmware_get_compliance(self, device_type: str, group: str = None) -> Response:
        """Get Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'group': group
        }

        return await self.get(url, params=params)

    async def firmware_delete_compliance(self, device_type: str, group: str = None) -> Response:
        """Clear Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'group': group
        }

        return await self.delete(url, params=params)

    async def firmware_upgrade_msp(self, firmware_scheduled_at: int, device_type: str,
                                   firmware_version: str, reboot: bool, exclude_groups: str,
                                   exclude_customers: str) -> Response:
        """Firmware Upgrade at MSP Level.

        Args:
            firmware_scheduled_at (int): Firmware upgrade will be schedule at, firmware_scheduled_at
                - current time. firmware_scheduled_at is epoch in seconds and default value is
                current time.
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_version (str): Specify firmware version which you want device to upgrade. If
                you do not specify this field then firmware upgrade initiated with recommended
                firmware version
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            exclude_groups (str): List of groups to be excluded while upgrading firmware, e.g.
                ["TestGroup1", "TestGroup2"]
            exclude_customers (str): List of customer IDs to be excluded while upgrading firmware,
                e.g. ["111111", "111112"]

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade"

        json_data = {
            'firmware_scheduled_at': firmware_scheduled_at,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'reboot': reboot,
            'exclude_groups': exclude_groups,
            'exclude_customers': exclude_customers
        }

        return await self.post(url, json_data=json_data)

    async def firmware_upgrade_customer(self, customer_id: str, firmware_scheduled_at: int,
                                        device_type: str, firmware_version: str, reboot: bool,
                                        exclude_groups: str) -> Response:
        """Firmware Upgrade at Customer Level.

        Args:
            customer_id (str): Customer id of the customer
            firmware_scheduled_at (int): Firmware upgrade will be scheduled at,
                firmware_scheduled_at - current time. firmware_scheduled_at is epoch in seconds and
                default value is current time.
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_version (str): Specify firmware version which you want device to upgrade. If
                you do not specify this field then firmware upgrade initiated with recommended
                firmware version
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            exclude_groups (str): List of groups to be excluded while upgrading firmware, e.g.
                ["TestGroup1", "TestGroup2"]

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/upgrade/customers/{customer_id}"

        json_data = {
            'firmware_scheduled_at': firmware_scheduled_at,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'reboot': reboot,
            'exclude_groups': exclude_groups
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade_msp(self, device_type: str, exclude_groups: str,
                                          exclude_customers: str) -> Response:
        """Cancel Scheduled Upgrade at MSP Level.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            exclude_groups (str): List of groups to be excluded while canceling scheduled upgrade,
                e.g. ["TestGroup1", "TestGroup2"]
            exclude_customers (str): List of customer IDs to be excluded while canceling scheduled
                upgrade, e.g. ["111111", "111112"]

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade/cancel"

        json_data = {
            'device_type': device_type,
            'exclude_groups': exclude_groups,
            'exclude_customers': exclude_customers
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade_customer(self, customer_id: str, device_type: str,
                                               exclude_groups: str) -> Response:
        """Cancel Scheduled Upgrade at Customer Level.

        Args:
            customer_id (str): Customer id of the customer
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            exclude_groups (str): List of groups to be excluded while canceling scheduled upgrade,
                e.g. ["TestGroup1", "TestGroup2"]

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/upgrade/customers/{customer_id}/cancel"

        json_data = {
            'device_type': device_type,
            'exclude_groups': exclude_groups
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade_msp_v2(self, device_type: str, exclude_customers: str) -> Response:
        """Cancel Scheduled Upgrade at MSP Level.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            exclude_customers (str): List of customer IDs to be excluded while canceling scheduled
                upgrade, e.g. ["111111", "111112"]

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v2/msp/upgrade/cancel"

        json_data = {
            'device_type': device_type,
            'exclude_customers': exclude_customers
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade_customer_v2(self, customer_id: str, device_type: str) -> Response:
        """Cancel Scheduled Upgrade at Customer Level.

        Args:
            customer_id (str): Customer id of the customer
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v2/msp/upgrade/customers/{customer_id}/cancel"

        json_data = {
            'device_type': device_type
        }

        return await self.post(url, json_data=json_data)

    async def firmware_get_model_families_list(self, serial: str = None, device_type: str = None) -> Response:
        """List Model Family. API is applicable only for Aruba Switches.

        Args:
            serial (str, optional): Serial of device
            device_type (str, optional): Specify one of "IAP/MAS/HP/CONTROLLER" # TODO only HP worked (ArubaOS-SW)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/models"

        params = {
            'serial': serial,
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def firmware_set_compliance_msp(self, device_type: str,
                                          firmware_compliance_version: str, reboot: bool,
                                          allow_unsupported_version: bool,
                                          compliance_scheduled_at: int, tenants: str) -> Response:
        """Set Firmware Compliance Version for MSP customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.
            compliance_scheduled_at (int): Firmware compliance will be schedule at,
                compliance_scheduled_at - current time. compliance_scheduled_at is epoch in seconds
                and default value is current time.
            tenants (str): List of tenant IDs to set firmware compliance , e.g. ["111111", "111112"]

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade/compliance_version"

        json_data = {
            'device_type': device_type,
            'firmware_compliance_version': firmware_compliance_version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at,
            'tenants': tenants
        }

        return await self.post(url, json_data=json_data)

    async def firmware_get_compliance_msp(self, device_type: str) -> Response:
        """Get Firmware Compliance Version for MSP Customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade/compliance_version"

        return await self.get(url)

    async def firmware_delete_compliance_msp(self, device_type: str, tenants: str) -> Response:
        """Clear Firmware Compliance Version for MSP Customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            tenants (str): List of tenant IDs to delete firmware compliance , e.g. ["111111",
                "111112"]

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade/compliance_version"

        json_data = {
            'device_type': device_type,
            'tenants': tenants
        }

        return await self.delete(url, json_data=json_data)

    async def firmware_set_compliance_msp_tenant(self, customer_id: str, device_type: str,
                                                 group: str, firmware_compliance_version: str,
                                                 reboot: bool, allow_unsupported_version: bool,
                                                 compliance_scheduled_at: int) -> Response:
        """Set Firmware Compliance Version for Tenant.

        Args:
            customer_id (str): Customer id of the customer
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str): Group name
            firmware_compliance_version (str): Firmware compliance version for specific device_type.
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            allow_unsupported_version (bool): Use True to set unsupported version as firmware
                compliance version for specific device_type. Default is False.
            compliance_scheduled_at (int): Firmware compliance will be schedule at,
                compliance_scheduled_at - current time. compliance_scheduled_at is epoch in seconds
                and default value is current time.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/upgrade/customers/{customer_id}/compliance_version"

        json_data = {
            'device_type': device_type,
            'group': group,
            'firmware_compliance_version': firmware_compliance_version,
            'reboot': reboot,
            'allow_unsupported_version': allow_unsupported_version,
            'compliance_scheduled_at': compliance_scheduled_at
        }

        return await self.post(url, json_data=json_data)

    async def firmware_get_compliance_msp_tenant(self, customer_id: str, device_type: str,
                                                 group: str = None) -> Response:
        """Get Firmware Compliance Version for Tenant.

        Args:
            customer_id (str): Customer id of the customer
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/upgrade/customers/{customer_id}/compliance_version"

        params = {
            'group': group
        }

        return await self.get(url, params=params)

    async def firmware_delete_compliance_msp_tenant(self, customer_id: str, device_type: str,
                                                    group: str = None) -> Response:
        """Clear Firmware Compliance Version for Tenant.

        Args:
            customer_id (str): Customer id of the customer
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/upgrade/customers/{customer_id}/compliance_version"

        params = {
            'group': group
        }

        return await self.delete(url, params=params)

    async def firmware_get_tenants_details(self, device_type: str, tenant_id: str) -> Response:
        """List Tenants of an MSP customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            tenant_id (str): Tenant ID for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/msp/tenants/{tenant_id}"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)


if __name__ == "__main__":
    central = AllCalls()
    # r = asyncio.run(central.firmware_get_version_list(device_type="HP"))  # works
    # r = asyncio.run(central.firmware_get_version_list(device_type="CX"))  # invalid value for device type
    # r = asyncio.run(central.firmware_get_version_list(device_type="SWITCH"))  # invalid value for device type
    # r = asyncio.run(central.firmware_get_version_list(device_type="HPCX"))  # invalid value for device type
    # r = asyncio.run(central.firmware_get_device_details(serial="SG03KW806T"))  # works and it's CX dunno what device_type
    r = asyncio.run(central.firmware_get_version_list(serial="SG03KW806T"))  # works and it's CX dunno what device_type
    print(r.status)
    try:
        print((asyncio.run(r._response.text())))
    except Exception as e:
        print(e)
        print(r.output)