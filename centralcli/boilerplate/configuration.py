#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generated from Aruba Central 2.5.4 Schemas

Code programatically generated.  May need tweaks
"""
import sys
from pathlib import Path
from typing import Union, List


# Detect if called from pypi installed package or via cloned github repo (development)
try:
    from centralcli import Response
except (ImportError, ModuleNotFoundError):
    pkg_dir = Path(__file__).absolute().parent
    if pkg_dir.name == "centralcli":
        sys.path.insert(0, str(pkg_dir.parent))
        from centralcli import Response
    else:
        print(pkg_dir.parts)
        raise

from centralcli.central import CentralApi


class AllCalls(CentralApi):
    def __init__(self):
        super().__init__()

    async def configuration_get_groups_v2(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all groups.

        Args:
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_create_group_v2(
        self,
        group: str,
        Wired: bool = True,
        Wireless: bool = None,
    ) -> Response:
        """Create new group.

        Args:
            group (str): Group Name
            Wired (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            Wireless (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups"

        json_data = {
            'group': group,
            'Wired': Wired,
            'Wireless': Wireless
        }

        return await self.post(url, json_data=json_data)

    async def configuration_create_group_v3(
        self,
        group: str,
        Wired: bool = True,
        Wireless: bool = None,
    ) -> Response:
        """Create new group with specified properties.

        Args:
            group (str): Group Name
            Wired (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            Wireless (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v3/groups"

        json_data = {
            'group': group,
            'Wired': Wired,
            'Wireless': Wireless
        }

        return await self.post(url, json_data=json_data)

    async def configuration_clone_group(
        self,
        group: str,
        clone_group: str,
        upgrade_architecture: bool = False,
    ) -> Response:
        """Clone and create new group.

        Args:
            group (str): Name of group to be created.
            clone_group (str): Group to be cloned.
            upgrade_architecture (bool, optional): Upgrade group architecture during clone.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups/clone"

        json_data = {
            'group': group,
            'clone_group': clone_group,
            'upgrade_architecture': upgrade_architecture
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_groups_template_data(
        self,
        groups: List[str],
    ) -> Response:
        """Get configuration mode set per device type for groups.

        Args:
            groups (List[str]): Group list to fetch template information.
                Maximum 20 comma separated group names allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups/template_info"

        params = {
            'groups': groups
        }

        return await self.get(url, params=params)

    async def configuration_get_groups_properties(
        self,
        groups: List[str],
    ) -> Response:
        """Get properties set for groups.

        Args:
            groups (List[str]): Group list to fetch properties.
                Maximum 20 comma separated group names allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/properties"

        params = {
            'groups': groups
        }

        return await self.get(url, params=params)

    async def configuration_update_group_properties_v2(
        self,
        group: str,
        AllowedDevTypes: List[str] = None,
        Architecture: str = None,
        ApNetworkRole: str = None,
        GwNetworkRole: str = None,
        AllowedSwitchTypes: List[str] = None,
        MonitorOnly: List[str] = None,
        Wired: bool = True,
        Wireless: bool = None,
    ) -> Response:
        """Update properties for the given group.

        Args:
            group (str): Group for which properties need to be updated.
            AllowedDevTypes (List[str], optional): Devices types which are allowed to be parked in
                the group.
            Architecture (str, optional): - Architecture for access points and gateways in the
                group.                                           - Applicable only when access
                points and gateways are allowed in the group.
                Valid Values: Instant, AOS10
            ApNetworkRole (str, optional): - Network role of the access points in the group.
                - Applicable only when access points are allowed in the group.
                - Standard network role is applicable for both AOS10 and Instant architecture.
                - Microbranch network role for access points is applicable only for AOS10
                architecture.                                              Valid Values: Standard,
                Microbranch
            GwNetworkRole (str, optional): - Network role of the gateways in the group.
                - Applicable only when gateways are allowed in the group.
                - BranchGateway and VPNConcentrator network role are applicable for both AOS10 and
                Instant architecture.                                            - WLANGateway
                network role is applicable only for AOS10 architecture.
                Valid Values: BranchGateway, VPNConcentrator, WLANGateway
            AllowedSwitchTypes (List[str], optional): -  Switch types which are allowed to be parked
                in the group.                                                       - This is
                applicable only when switches are allowed to be parked in the group.
            MonitorOnly (List[str], optional): - Device types for which monitor only mode is to be
                enabled                                                - Currently, this is
                available only for AOS-S switches in groups where switches are
                managed using UI mode of configuration.
            Wired (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            Wireless (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/groups/{group}/properties"

        json_data = {
            'AllowedDevTypes': AllowedDevTypes,
            'Architecture': Architecture,
            'ApNetworkRole': ApNetworkRole,
            'GwNetworkRole': GwNetworkRole,
            'AllowedSwitchTypes': AllowedSwitchTypes,
            'MonitorOnly': MonitorOnly,
            'Wired': Wired,
            'Wireless': Wireless
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_update_group_name(
        self,
        group: str,
        new_group: str,
    ) -> Response:
        """Update group name for the given group.

        Args:
            group (str): Group for which name need to be updated.
            new_group (str): group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/name"

        json_data = {
            'new_group': new_group
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_get_cust_default_group(
        self,
    ) -> Response:
        """Get default group.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/default_group"

        return await self.get(url)

    async def configuration_set_cust_default_group(
        self,
        group: str,
    ) -> Response:
        """Set default group.

        Args:
            group (str): group

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/default_group"

        json_data = {
            'group': group
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_delete_group(
        self,
        group: str,
    ) -> Response:
        """Delete existing group.

        Args:
            group (str): Name of the group that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}"

        return await self.delete(url)

    async def configuration_get_templates(
        self,
        group: str,
        template: str = None,
        device_type: str = None,
        version: str = None,
        model: str = None,
        q: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all templates in group.

        Args:
            group (str): Name of the group for which the templates are being queried.
            template (str, optional): Filter on provided name as template.
            device_type (str, optional): Filter on device_type.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: ALL, 2920, J9727A etc.
            q (str, optional): Search for template OR version OR model, q will be ignored if any of
                filter parameters are provided.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of template records to be returned. Defaults to
                100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"

        params = {
            'template': template,
            'device_type': device_type,
            'version': version,
            'model': model,
            'q': q,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_create_template(
        self,
        group: str,
        name: str,
        device_type: str,
        version: str,
        model: str,
        template: Union[Path, str],
    ) -> Response:
        """Create new template.

        Args:
            group (str): Name of the group for which the template is to be created.
            name (str): Name of template.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.
            template (Union[Path, str]): Template text.
                For 'ArubaSwitch' device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.                                          2. aruba-central
                url https://<URL | IP>/ws.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        template = template if isinstance(template, Path) else Path(str(template))

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        return await self.post(url, params=params)

    async def configuration_update_template(
        self,
        group: str,
        name: str,
        device_type: str = None,
        version: str = None,
        model: str = None,
        template: Union[Path, str] = None,
    ) -> Response:
        """Update existing template.

        Args:
            group (str): Name of the group for which the template is to be updated.
            name (str): Name of template.
            device_type (str, optional): Device type of the template.  Valid Values: IAP,
                ArubaSwitch, CX, MobilityController
            version (str, optional): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: 2920, J9727A etc.
            template (Union[Path, str], optional): Template text.
                For 'ArubaSwitch' device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.                                                    2.
                aruba-central url https://<URL | IP>/ws.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        template = template if isinstance(template, Path) else Path(str(template))

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        return await self.patch(url, params=params)

    async def configuration_get_template(
        self,
        group: str,
        template: str,
    ) -> Response:
        """Get template text for a template in group.

        Args:
            group (str): Name of the group for which the templates are being queried.
            template (str): Name of template.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates/{template}"

        return await self.get(url)

    async def configuration_delete_template(
        self,
        group: str,
        template: str,
    ) -> Response:
        """Delete existing template.

        Args:
            group (str): Name of the group for which the template is to be deleted.
            template (str): Name of the template to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates/{template}"

        return await self.delete(url)

    async def configuration_create_snapshot_for_group(
        self,
        group: str,
        name: str,
        do_not_delete: bool,
    ) -> Response:
        """Create new configuration backup for group.

        Args:
            group (str): Name of the group for which the configuration backup is being created.
            name (str): name
            do_not_delete (bool): Flag to represent if the snapshot can be deleted automatically by
                system when creating new snapshot or not.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/snapshot/{group}"

        json_data = {
            'name': name,
            'do_not_delete': do_not_delete
        }

        return await self.post(url, json_data=json_data)

    async def configuration_create_snapshots_for_multiple_groups(
        self,
        backup_name: str,
        do_not_delete: bool,
        include_groups: List[str],
        exclude_groups: List[str],
    ) -> Response:
        """Create new configuration backup for multiple groups.

        Args:
            backup_name (str): backup_name
            do_not_delete (bool): Flag to represent if the snapshot can be deleted automatically by
                system when creating new snapshot or not.
            include_groups (List[str]): List of group names to be included,
                Example: ["Group1", "Group2"].
                If include_groups list is specified then exclude_groups list must be empty or must
                not be specified.
            exclude_groups (List[str]): List of group names to be excluded,
                Example: ["Group1", "Group2"].
                If exclude_groups list is specified then include_groups list must be empty or must
                not be specified.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/snapshot/backups"

        json_data = {
            'backup_name': backup_name,
            'do_not_delete': do_not_delete,
            'include_groups': include_groups,
            'exclude_groups': exclude_groups
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_snapshots_for_group(
        self,
        group: str,
    ) -> Response:
        """Get all configuration backups for the given group.

        Args:
            group (str): Name of the group to list configuration backups.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots"

        return await self.get(url)

    async def configuration_update_do_not_delete(
        self,
        group: str,
        data: list,
    ) -> Response:
        """Update do-not-delete flag for list of configuration backups for the given group.

        Args:
            group (str): Name of the group.
            data (list): data

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots"

        json_data = {
            'data': data
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_get_last_restore_logs_for_group(
        self,
        group: str,
    ) -> Response:
        """Get last restore logs for the given group.

        Args:
            group (str): Name of the group.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/last_restore_log"

        return await self.get(url)

    async def configuration_get_backup_log_for_snapshot(
        self,
        group: str,
        snapshot: str,
    ) -> Response:
        """Get backup-log for the given configuration backup for the given group.

        Args:
            group (str): Name of the group.
            snapshot (str): Name of the configuration backup.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots/{snapshot}/backup_log"

        return await self.get(url)

    async def configuration_get_backup_status_for_snapshot(
        self,
        group: str,
        snapshot: str,
    ) -> Response:
        """Get status of configuration backup for the given group.

        Args:
            group (str): Name of the group.
            snapshot (str): Name of the configuration backup.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots/{snapshot}/backup_status"

        return await self.get(url)

    async def configuration_get_restore_status_for_snapshot(
        self,
        group: str,
        snapshot: str,
    ) -> Response:
        """Get status of configuration restore for the given group.

        Args:
            group (str): Name of the group.
            snapshot (str): Name of the configuration backup.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots/{snapshot}/restore_status"

        return await self.get(url)

    async def configuration_restore_snapshot_for_group(
        self,
        group: str,
        snapshot: str,
        device_type: str,
    ) -> Response:
        """Restore configuration backup of a group.

        Args:
            group (str): Name of the group.
            snapshot (str): Name of the configuration backup to be restored.
            device_type (str): Device type to restore from given backup.  Valid Values: IAP, CX,
                ArubaSwitch, MobilityController, ALL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/snapshots/{snapshot}/restore"

        params = {
            'device_type': device_type
        }

        return await self.post(url, params=params)

    async def configuration_move_devices(
        self,
        group: str,
        serials: List[str],
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): group
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/move"

        json_data = {
            'group': group,
            'serials': serials
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_device_template_variables(
        self,
        device_serial: str,
    ) -> Response:
        """Get template variables for a device.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"

        return await self.get(url)

    async def configuration_create_device_template_variables(
        self,
        device_serial: str,
        total: int,
        _sys_serial: str,
        _sys_lan_mac: str,
    ) -> Response:
        """Create template variables for a device.

        Args:
            device_serial (str): Serial number of the device.
            total (int): total
            _sys_serial (str): _sys_serial
            _sys_lan_mac (str): _sys_lan_mac

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"

        json_data = {
            'total': total,
            '_sys_serial': _sys_serial,
            '_sys_lan_mac': _sys_lan_mac
        }

        return await self.post(url, json_data=json_data)

    async def configuration_update_device_template_variables(
        self,
        device_serial: str,
        total: int,
        _sys_serial: str,
        _sys_lan_mac: str,
    ) -> Response:
        """Update template variables for a device.

        Args:
            device_serial (str): Serial number of the device.
            total (int): total
            _sys_serial (str): _sys_serial
            _sys_lan_mac (str): _sys_lan_mac

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"

        json_data = {
            'total': total,
            '_sys_serial': _sys_serial,
            '_sys_lan_mac': _sys_lan_mac
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_replace_device_template_variables(
        self,
        device_serial: str,
        total: int,
        _sys_serial: str,
        _sys_lan_mac: str,
    ) -> Response:
        """Replace all or delete some of the template variables for a device.

        Args:
            device_serial (str): Serial number of the device.
            total (int): total
            _sys_serial (str): _sys_serial
            _sys_lan_mac (str): _sys_lan_mac

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"

        json_data = {
            'total': total,
            '_sys_serial': _sys_serial,
            '_sys_lan_mac': _sys_lan_mac
        }

        return await self.put(url, json_data=json_data)

    async def configuration_delete_device_template_variables(
        self,
        device_serial: str,
    ) -> Response:
        """Delete all of the template variables for a device.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/template_variables"

        return await self.delete(url)

    async def configuration_get_device_group(
        self,
        device_serial: str,
    ) -> Response:
        """Get group for a device.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/group"

        return await self.get(url)

    async def configuration_get_device_configuration(
        self,
        device_serial: str,
    ) -> Response:
        """Get last known running configuration for a device.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/configuration"

        return await self.get(url)

    async def configuration_get_device_details(
        self,
        device_serial: str,
        details: bool = True,
    ) -> Response:
        """Get configuration details for a device (only for template groups).

        Args:
            device_serial (str): Serial number of the device.
            details (bool, optional): Usually pass false to get only the summary of a device's
                configuration status.
                Pass true only if detailed response of a device's configuration status is required.
                Passing true might result in slower API response and performance effect
                comparatively.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/config_details"

        params = {
            'details': details
        }

        return await self.get(url, params=params)

    async def configuration_get_devices_template_details(
        self,
        device_serials: List[str],
    ) -> Response:
        """Get templates for a list of devices.

        Args:
            device_serials (List[str]): Serial numbers of the devices.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/template"

        params = {
            'device_serials': device_serials
        }

        return await self.get(url, params=params)

    async def configuration_get_groups_template_details(
        self,
        device_type: str,
        include_groups: List[str] = None,
        exclude_groups: List[str] = None,
        all_groups: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get templates of devices present in the given list of groups.

        Args:
            device_type (str): Fetch device templates of the given device_type.  Valid Values: IAP,
                ArubaSwitch, CX, MobilityController
            include_groups (List[str], optional): Fetch devices templates for list of groups.
            exclude_groups (List[str], optional): Fetch devices templates not in list of groups
                (Only allowed for user having all_groups access or admin).
            all_groups (bool, optional): Fetch devices templates details for all the groups (Only
                allowed for user having all_groups access or admin)
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/groups/template"

        params = {
            'device_type': device_type,
            'include_groups': include_groups,
            'exclude_groups': exclude_groups,
            'all_groups': all_groups,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_hash_template_details(
        self,
        template_hash: str,
        exclude_hash: bool,
        device_type: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get templates of devices for given template hash (Only allowed for user having all_groups
        access or admin).

        Args:
            template_hash (str): Template_hash of the template for which list of devices needs to be
                populated.
            exclude_hash (bool): Fetch devices template details not matching with provided hash.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{template_hash}/template"

        params = {
            'exclude_hash': exclude_hash,
            'device_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_all_devices_template_variables(
        self,
        format: str = 'JSON',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get template variables for all devices, Response is sorted by device serial.

        Args:
            format (str, optional): Format in which output is desired.  Valid Values: JSON
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/template_variables"

        params = {
            'format': format,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_create_all_devices_template_variables(
        self,
        variables: Union[Path, str],
        format: str = 'JSON',
    ) -> Response:
        """Create template variables for all devices.

        Args:
            variables (Union[Path, str]):  File with variables to be applied for device.
                - {"AB0011111": {"_sys_serial": "AB0011111", "_sys_lan_mac": "11:12:AA:13:14:BB",
                "SSID_A": "Z-Employee"}, "AB0022222": {"_sys_serial": "AB0022222", "_sys_lan_mac":
                "21:22:AA:23:24:BB", "vc_name": "Instant-23:24:BB"}}
            format (str, optional): Format in which input is provided.  Valid Values: JSON

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/template_variables"
        variables = variables if isinstance(variables, Path) else Path(str(variables))

        params = {
            'format': format
        }

        return await self.post(url, params=params)

    async def configuration_replace_all_devices_template_variables(
        self,
        variables: Union[Path, str],
        format: str = 'JSON',
    ) -> Response:
        """Replace all or delete some of the template variables for all devices.

        Args:
            variables (Union[Path, str]):  File with variables to be applied for device.
                - {"AB0011111": {"_sys_serial": "AB0011111", "_sys_lan_mac": "11:12:AA:13:14:BB",
                "SSID_A": "Z-Employee"}, "AB0022222": {"_sys_serial": "AB0022222", "_sys_lan_mac":
                "21:22:AA:23:24:BB", "vc_name": "Instant-23:24:BB"}}
            format (str, optional): Format in which input is provided.  Valid Values: JSON

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/template_variables"
        variables = variables if isinstance(variables, Path) else Path(str(variables))

        params = {
            'format': format
        }

        return await self.put(url, params=params)

    async def configuration_update_all_devices_template_variables(
        self,
        variables: Union[Path, str],
    ) -> Response:
        """Update template variables for all devices (Only JSON Payload).

        Args:
            variables (Union[Path, str]):  File with variables to be applied for device.
                - {"AB0011111": {"_sys_serial": "AB0011111", "_sys_lan_mac": "11:12:AA:13:14:BB",
                "SSID_A": "Z-Employee"}, "AB0022222": {"_sys_serial": "AB0022222", "_sys_lan_mac":
                "21:22:AA:23:24:BB", "vc_name": "Instant-23:24:BB"}}

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/template_variables"
        variables = variables if isinstance(variables, Path) else Path(str(variables))

        return await self.patch(url)

    async def configuration_get_device_variabilised_template(
        self,
        device_serial: str,
    ) -> Response:
        """Get variablised template for an Aruba Switch.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/variablised_template"

        return await self.get(url)

    async def configuration_recover_md_device(
        self,
        device_serial: str,
    ) -> Response:
        """Trigger Mobility Device recovery by resetting (delete and add) Device configuration.

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/recover_device"

        return await self.post(url)

    async def configuration_get_certificates(
        self,
        q: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get Certificates details uploaded.

        Args:
            q (str, optional): Search for a particular certificate by its name, md5 hash or
                sha1_hash
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/certificates"

        params = {
            'q': q,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_upload_certificate(
        self,
        cert_name: str,
        cert_type: str,
        cert_format: str,
        passphrase: str,
        cert_data: str,
    ) -> Response:
        """Upload a certificate.

        Args:
            cert_name (str): cert_name
            cert_type (str): cert_type  Valid Values: SERVER_CERT, CA_CERT, CRL, INTERMEDIATE_CA,
                OCSP_RESPONDER_CERT, OCSP_SIGNER_CERT, PUBLIC_CERT
            cert_format (str): cert_format  Valid Values: PEM, DER, PKCS12
            passphrase (str): passphrase
            cert_data (str): Certificate content encoded in base64 for all format certificates.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/certificates"

        json_data = {
            'cert_name': cert_name,
            'cert_type': cert_type,
            'cert_format': cert_format,
            'passphrase': passphrase,
            'cert_data': cert_data
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_certificate(
        self,
        certificate: str,
    ) -> Response:
        """Delete existing certificate.

        Args:
            certificate (str): Name of the certificate that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/certificates/{certificate}"

        return await self.delete(url)

    async def configuration_msp_update_certificate(
        self,
        cert_name: str,
        cert_type: str,
        cert_format: str,
        passphrase: str,
        cert_data: str,
    ) -> Response:
        """Update a certificate.

        Args:
            cert_name (str): cert_name
            cert_type (str): cert_type  Valid Values: SERVER_CERT, CA_CERT, CRL, INTERMEDIATE_CA,
                OCSP_RESPONDER_CERT, OCSP_SIGNER_CERT, PUBLIC_CERT
            cert_format (str): cert_format  Valid Values: PEM, DER, PKCS12
            passphrase (str): passphrase
            cert_data (str): Certificate content encoded in base64 for all format certificates.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/msp/certificate"

        json_data = {
            'cert_name': cert_name,
            'cert_type': cert_type,
            'cert_format': cert_format,
            'passphrase': passphrase,
            'cert_data': cert_data
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_cp_logos(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get Captive Portal Logos uploaded.

        Args:
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/cplogo"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_upload_cp_logo(
        self,
        cp_logo_filename: str,
        cp_logo_data: str,
    ) -> Response:
        """Upload a captive portal logo.

        Args:
            cp_logo_filename (str): Filename of logo with extension.
            cp_logo_data (str): Captive Portal Logo encoded in base64.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/cplogo"

        json_data = {
            'cp_logo_filename': cp_logo_filename,
            'cp_logo_data': cp_logo_data
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_cp_logo(
        self,
        checksum: str,
    ) -> Response:
        """Delete existing captive portal logo.

        Args:
            checksum (str): MD5 checksum of the logo that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/cplogo/{checksum}"

        return await self.delete(url)

    async def configuration_update_ssh_connection_info(
        self,
        device_serial: str,
        username: str,
        password: str,
    ) -> Response:
        """Set Username, password required for establishing SSH connection to switch.

        Args:
            device_serial (str): Serial number of the device.
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{device_serial}/ssh_connection"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_msp_customer_templates(
        self,
        device_type: str = None,
        version: str = None,
        model: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get MSP customer level template details.

        Args:
            device_type (str, optional): Filter on device_type.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: 2920, J9727A etc.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of template records to be returned. Defaults to
                100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/msp/templates"

        params = {
            'device_type': device_type,
            'version': version,
            'model': model,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_msp_customer_template_text(
        self,
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Get MSP customer level template text.

        Args:
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/{device_type}/{version}/{model}"

        return await self.get(url)

    async def configuration_delete_msp_customer_template(
        self,
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Delete MSP customer template.

        Args:
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/{device_type}/{version}/{model}"

        return await self.delete(url)

    async def configuration_set_msp_customer_template(
        self,
        device_type: str,
        version: str,
        model: str,
        template: Union[Path, str],
    ) -> Response:
        """Update MSP customer level template.

        Args:
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.
            template (Union[Path, str]): Template text
                For HP Switches, the template text should include the following commands to enable
                RCS connection with central.
                1. Provide include-credential command in template text.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/msp/templates"
        template = template if isinstance(template, Path) else Path(str(template))

        params = {
            'device_type': device_type,
            'version': version,
            'model': model
        }

        return await self.put(url, params=params)

    async def configuration_get_end_customer_templates(
        self,
        cid: str,
        device_type: str = None,
        version: str = None,
        model: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get end customer level template details.

        Args:
            cid (str): Customer id where template has to be provided.
            device_type (str, optional): Filter on device_type.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: 2920, J9727A etc.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of template records to be returned. Defaults to
                100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/customer/{cid}"

        params = {
            'device_type': device_type,
            'version': version,
            'model': model,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_end_customer_template_text(
        self,
        cid: str,
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Get end customer level template text.

        Args:
            cid (str): Customer id where template has to be provided.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/customer/{cid}/{device_type}/{version}/{model}"

        return await self.get(url)

    async def configuration_delete_end_customer_template(
        self,
        cid: str,
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Delete end customer template.

        Args:
            cid (str): Customer id where template has to be provided.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/customer/{cid}/{device_type}/{version}/{model}"

        return await self.delete(url)

    async def configuration_set_end_customer_template(
        self,
        cid: str,
        device_type: str,
        version: str,
        model: str,
        template: Union[Path, str],
    ) -> Response:
        """Update end customer level template.

        Args:
            cid (str): Customer id where template has to be provided.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.
            template (Union[Path, str]): Template text.
                For HP Switches, the template text should include the
                following commands to enable RCS connection with central.
                1) Provide include-credential command in template text.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/msp/templates/customer/{cid}"
        template = template if isinstance(template, Path) else Path(str(template))

        params = {
            'device_type': device_type,
            'version': version,
            'model': model
        }

        return await self.put(url, params=params)

    async def configuration_get_msp_tmpl_differ_custs_groups(
        self,
        device_type: str,
        version: str,
        model: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get customers and groups where given MSP level template is not applied.

        Args:
            device_type (str): Template device_type.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Template version.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.
            offset (int, optional): Number of customers to be skipped before returning the data,
                useful for pagination. Defaults to 0.
            limit (int, optional): Maximum number of customer records to be returned.
                If limit is 50, records for 50 customers will be returned.
                If limit is not provided, records for a maximum of 100 customers will be returned.
                Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/differences/{device_type}/{version}/{model}"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_msp_tmpl_end_cust_differ_groups(
        self,
        cid: str,
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Get groups for given end customer where MSP Level template is not applied.

        Args:
            cid (str): End customer id.
            device_type (str): Template device_type.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Template version.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/msp/templates/differences/customer/{cid}/{device_type}/{version}/{model}"

        return await self.get(url)

    async def configuration_apply_msp_customer_template(
        self,
        include_customers: List[str],
        exclude_customers: List[str],
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Apply MSP customer level template to end customers.  This would not apply template to
        template groups at end customer. .

        Args:
            include_customers (List[str]): List of customers  IDs to be included while applying
                template,
                Example: ["111111", "111112"].
                If include_customers list is specified then exclude_customers must not be specified.
            exclude_customers (List[str]): List of customers IDs to be excluded while applying
                template,
                Example: ["111111", "111112"].
                If exclude_customers list is specified then include_customers must not be specified.
                If exclude_customers is [] then template would be applied to all end customers.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/msp/templates/end_customers/{device_type}/{version}/{model}"

        json_data = {
            'include_customers': include_customers,
            'exclude_customers': exclude_customers
        }

        return await self.post(url, json_data=json_data)

    async def configuration_apply_end_customer_template(
        self,
        cid: str,
        include_groups: List[str],
        exclude_groups: List[str],
        device_type: str,
        version: str,
        model: str,
    ) -> Response:
        """Apply end customer template to template groups at end customer.

        Args:
            cid (str): End customer id.
            include_groups (List[str]): List of group names to be included while applying template,
                Example: ["G1", "G2"].
                If include_groups list is specified then exclude_groups must not be specified.
                Special value ["ALL_GROUPS"] can be specified in include_groups list so that given
                template can be copied to ALL template groups under given tenant.
            exclude_groups (List[str]): List of group names to be excluded while applying template,
                Example: ["G1", "G2"].
                If exclude_groups list is specified then include_groups must not be specified.
            device_type (str): Device type of the template.  Valid Values: IAP, ArubaSwitch, CX,
                MobilityController
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.                                                    Example: 2920, J9727A
                etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/msp/templates/end_customers/{cid}/{device_type}/{version}/{model}/groups"

        json_data = {
            'include_groups': include_groups,
            'exclude_groups': exclude_groups
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_cust_config_mode(
        self,
    ) -> Response:
        """Get configuration mode as either Monitor or Managed mode at customer level.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode"

        return await self.get(url)

    async def configuration_set_cust_config_mode(
        self,
        config_mode: str,
    ) -> Response:
        """Set configuration mode as either Monitor or Manage at customer level.

        Args:
            config_mode (str): config_mode  Valid Values: Monitor, Manage

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode"

        json_data = {
            'config_mode': config_mode
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_group_config_mode(
        self,
        q: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get configuration mode for devices as either Monitor or Managed mode at group level.

        Args:
            q (str, optional): Search for group.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group config_mode records to be returned.
                Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode/group"

        params = {
            'q': q,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_set_group_config_mode(
        self,
        groups: List[str],
        config_mode: str,
    ) -> Response:
        """Set configuration mode as either Monitor or Manage at group level.

        Args:
            groups (List[str]): groups
            config_mode (str): config_mode  Valid Values: Monitor, Manage

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode/group"

        json_data = {
            'groups': groups,
            'config_mode': config_mode
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_device_config_mode(
        self,
        group: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get configuration mode as either Monitor or Managed mode at device level.

        Args:
            group (str): Configuration mode of devices for group.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of devices config_mode records to be returned.
                Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode/device"

        params = {
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_set_device_config_mode(
        self,
        serials: List[str],
        config_mode: str,
    ) -> Response:
        """Set configuration mode as either Monitor or Manage for given devices.

        Args:
            serials (List[str]): serials
            config_mode (str): config_mode  Valid Values: Monitor, Manage

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode/device"

        json_data = {
            'serials': serials,
            'config_mode': config_mode
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_device_serials_config_mode(
        self,
        device_serials: List[str],
    ) -> Response:
        """Get configuration mode as either Monitor or Managed mode for device serials.

        Args:
            device_serials (List[str]): List of device serials to fetch configuration mode:
                Maximum 50 comma separated serials allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/mode/devices"

        params = {
            'device_serials': device_serials
        }

        return await self.get(url, params=params)

    async def configuration_get_vfw_groups(
        self,
    ) -> Response:
        """Get whitelisted groups in Variables Firewall.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/variables_firewall/groups"

        return await self.get(url)

    async def configuration_update_vfw_groups(
        self,
        groups: List[str],
    ) -> Response:
        """Add groups to Variables Firewall whitelist.

        Args:
            groups (List[str]): groups

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/variables_firewall/groups"

        json_data = {
            'groups': groups
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_vfw_group(
        self,
        group: str,
    ) -> Response:
        """Delete group from Variables Firewall whitelist.

        Args:
            group (str): Name of the group that needs to be deleted from Variables Firewall.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/variables_firewall/groups/{group}"

        return await self.delete(url)

    async def configuration_get_vfw_variables(
        self,
    ) -> Response:
        """Get whitelisted variables in Variables Firewall.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/variables_firewall/variables"

        return await self.get(url)

    async def configuration_update_vfw_variables(
        self,
        variables: List[str],
    ) -> Response:
        """Add variables to Variables Firewall whitelist.

        Args:
            variables (List[str]): variables

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/variables_firewall/variables"

        json_data = {
            'variables': variables
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_vfw_variable(
        self,
        variable: str,
    ) -> Response:
        """Delete variable from Variables Firewall whitelist.

        Args:
            variable (str): Name of the variable that needs to be deleted from Variables Firewall.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/variables_firewall/variables/{variable}"

        return await self.delete(url)

    async def configuration_set_group_config_country_code(
        self,
        groups: List[str],
        country: str,
    ) -> Response:
        """Set country code at group level (For UI groups only, not supported for template groups).
        Note: IAP's need to be rebooted for changes to take effect. .

        Args:
            groups (List[str]): groups
            country (str): country

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/country"

        json_data = {
            'groups': groups,
            'country': country
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_group_country(
        self,
        group: str,
    ) -> Response:
        """Get country code set for group (For UI groups only, not supported for template groups).

        Args:
            group (str): Name of the group for which the country code is being queried.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/{group}/country"

        return await self.get(url)

    async def configuration_get_groups_auto_commit_state(
        self,
        q: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get auto commit state as either On or Off at group level.

        Args:
            q (str, optional): Search for group.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group records to be returned. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/auto_commit_state/groups"

        params = {
            'q': q,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_set_groups_auto_commit_state(
        self,
        groups: List[str],
        auto_commit_state: str,
    ) -> Response:
        """Set auto commit state as either On or Off at group level.

        Args:
            groups (List[str]): groups
            auto_commit_state (str): auto_commit_state  Valid Values: On, Off

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/auto_commit_state/groups"

        json_data = {
            'groups': groups,
            'auto_commit_state': auto_commit_state
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_device_serials_auto_commit_state(
        self,
        device_serials: List[str],
    ) -> Response:
        """Get auto commit state as either On or Off for device serials.

        Args:
            device_serials (List[str]): List of device serials to fetch auto commit state:
                Maximum 50 comma separated serials allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/auto_commit_state/devices"

        params = {
            'device_serials': device_serials
        }

        return await self.get(url, params=params)

    async def configuration_set_device_serials_auto_commit_state(
        self,
        serials: List[str],
        auto_commit_state: str,
    ) -> Response:
        """Set auto commit state as either On or Off for given devices.

        Args:
            serials (List[str]): serials
            auto_commit_state (str): auto_commit_state  Valid Values: On, Off

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/auto_commit_state/devices"

        json_data = {
            'serials': serials,
            'auto_commit_state': auto_commit_state
        }

        return await self.post(url, json_data=json_data)

    async def configuration_commit_group_config(
        self,
        groups: List[str],
    ) -> Response:
        """Commit configurations for given groups.

        Args:
            groups (List[str]): groups

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/commit/groups"

        json_data = {
            'groups': groups
        }

        return await self.post(url, json_data=json_data)

    async def configuration_commit_device_config(
        self,
        serials: List[str],
    ) -> Response:
        """Commit configurations for given devices.

        Args:
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/commit/devices"

        json_data = {
            'serials': serials
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_blacklist_clients(
        self,
        device_id: str,
    ) -> Response:
        """Get all denylist client mac address in device.

        Args:
            device_id (str): Device id of virtual controller or C2C ap.
                Example:14b3743c01f8080bfa07ca053ef1e895df9c0680fe5a17bfd5.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/swarm/{device_id}/blacklisting"

        return await self.get(url)

    async def configuration_add_blacklist_clients(
        self,
        device_id: str,
        blacklist: List[str],
    ) -> Response:
        """Add denylist clients.

        Args:
            device_id (str): Device id of virtual controller or C2C ap.
                Example:14b3743c01f8080bfa07ca053ef1e895df9c0680fe5a17bfd5.
            blacklist (List[str]): blacklist

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/swarm/{device_id}/blacklisting"

        json_data = {
            'blacklist': blacklist
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_blacklist_clients(
        self,
        device_id: str,
        blacklist: List[str],
    ) -> Response:
        """Delete denylist clients.

        Args:
            device_id (str): Device id of virtual controller or C2C ap.
                Example:14b3743c01f8080bfa07ca053ef1e895df9c0680fe5a17bfd5.
            blacklist (List[str]): blacklist

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/swarm/{device_id}/blacklisting"

        json_data = {
            'blacklist': blacklist
        }

        return await self.delete(url, json_data=json_data)

    async def configuration_get_wlan_list(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN list of an UI group.

        Args:
            group_name_or_guid (str): Name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_get_wlan_template(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN default configuration.

        Args:
            group_name_or_guid (str): Name of the group or guid of the swarm. Example:Group_1 or
                6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid}/template"

        return await self.get(url)

    async def configuration_get_protocol_map(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN access rule protocol map.

        Args:
            group_name_or_guid (str): Name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid}/protocol_map"

        return await self.get(url)

    async def configuration_get_access_rule_services(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN access rule services.

        Args:
            group_name_or_guid (str): Name of the group guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid}/access_rule_services"

        return await self.get(url)

    async def configuration_delete_wlan(
        self,
        group_name_or_guid: str,
        wlan_name: str,
    ) -> Response:
        """Delete an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid}/{wlan_name}"

        return await self.delete(url)

    async def configuration_get_wlan_v2(
        self,
        group_name_or_guid: str,
        wlan_name: str,
    ) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group_name_or_guid}/{wlan_name}"

        return await self.get(url)

    async def configuration_create_wlan_v2(
        self,
        group_name_or_guid: str,
        wlan_name: str,
        essid: str,
        type: str,
        hide_ssid: bool,
        vlan: str,
        zone: str,
        wpa_passphrase: str,
        wpa_passphrase_changed: bool,
        is_locked: bool,
        captive_profile_name: str,
        bandwidth_limit_up: str,
        bandwidth_limit_down: str,
        bandwidth_limit_peruser_up: str,
        bandwidth_limit_peruser_down: str,
        access_rules: list,
    ) -> Response:
        """Create a new WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to create.                              Example:wlan_1.
            essid (str): essid
            type (str): type  Valid Values: employee, guest
            hide_ssid (bool): hide_ssid
            vlan (str): vlan
            zone (str): zone
            wpa_passphrase (str): wpa_passphrase
            wpa_passphrase_changed (bool): wpa_passphrase_changed
            is_locked (bool): is_locked
            captive_profile_name (str): captive_profile_name
            bandwidth_limit_up (str): bandwidth_limit_up
            bandwidth_limit_down (str): bandwidth_limit_down
            bandwidth_limit_peruser_up (str): bandwidth_limit_peruser_up
            bandwidth_limit_peruser_down (str): bandwidth_limit_peruser_down
            access_rules (list): access_rules

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase_changed,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }

        return await self.post(url, json_data=json_data)

    async def configuration_clean_up_and_update_wlan_v2(
        self,
        group_name_or_guid: str,
        wlan_name: str,
        essid: str,
        type: str,
        hide_ssid: bool,
        vlan: str,
        zone: str,
        wpa_passphrase: str,
        wpa_passphrase_changed: bool,
        is_locked: bool,
        captive_profile_name: str,
        bandwidth_limit_up: str,
        bandwidth_limit_down: str,
        bandwidth_limit_peruser_up: str,
        bandwidth_limit_peruser_down: str,
        access_rules: list,
    ) -> Response:
        """Update an existing WLAN and clean up unsupported fields.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.
            essid (str): essid
            type (str): type  Valid Values: employee, guest
            hide_ssid (bool): hide_ssid
            vlan (str): vlan
            zone (str): zone
            wpa_passphrase (str): wpa_passphrase
            wpa_passphrase_changed (bool): wpa_passphrase_changed
            is_locked (bool): is_locked
            captive_profile_name (str): captive_profile_name
            bandwidth_limit_up (str): bandwidth_limit_up
            bandwidth_limit_down (str): bandwidth_limit_down
            bandwidth_limit_peruser_up (str): bandwidth_limit_peruser_up
            bandwidth_limit_peruser_down (str): bandwidth_limit_peruser_down
            access_rules (list): access_rules

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase_changed,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }

        return await self.patch(url, json_data=json_data)

    async def configuration_update_wlan_v2(
        self,
        group_name_or_guid: str,
        wlan_name: str,
        essid: str,
        type: str,
        hide_ssid: bool,
        vlan: str,
        zone: str,
        wpa_passphrase: str,
        wpa_passphrase_changed: bool,
        is_locked: bool,
        captive_profile_name: str,
        bandwidth_limit_up: str,
        bandwidth_limit_down: str,
        bandwidth_limit_peruser_up: str,
        bandwidth_limit_peruser_down: str,
        access_rules: list,
    ) -> Response:
        """Update an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.
            essid (str): essid
            type (str): type  Valid Values: employee, guest
            hide_ssid (bool): hide_ssid
            vlan (str): vlan
            zone (str): zone
            wpa_passphrase (str): wpa_passphrase
            wpa_passphrase_changed (bool): wpa_passphrase_changed
            is_locked (bool): is_locked
            captive_profile_name (str): captive_profile_name
            bandwidth_limit_up (str): bandwidth_limit_up
            bandwidth_limit_down (str): bandwidth_limit_down
            bandwidth_limit_peruser_up (str): bandwidth_limit_peruser_up
            bandwidth_limit_peruser_down (str): bandwidth_limit_peruser_down
            access_rules (list): access_rules

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase_changed,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_full_wlan_list(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN list of an UI group.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_get_full_wlan_template(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN default configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/template"

        return await self.get(url)

    async def configuration_get_full_wlan_protocol_map(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN access rule protocol map.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/protocol_map"

        return await self.get(url)

    async def configuration_get_full_wlan_access_rule_services(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get WLAN access rule services.

        Args:
            group_name_or_guid (str): Name of the group guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/access_rule_services"

        return await self.get(url)

    async def configuration_get_wlan(
        self,
        group_name_or_guid: str,
        wlan_name: str,
    ) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/{wlan_name}"

        return await self.get(url)

    async def configuration_create_wlan(
        self,
        group_name_or_guid: str,
        wlan_name: str,
        value: str,
    ) -> Response:
        """Create a new WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to create.                              Example:wlan_1.
            value (str): "wlan": {                            "a_max_tx_rate": "54",
                "a_min_tx_rate": "6",                            "access_type": "unrestricted",
                "accounting_server1": "",                            "accounting_server2": "",
                "air_time_limit": "",                            "air_time_limit_cb": false,
                "auth_cache_timeout": 24,                            "auth_req_threshold": 0,
                "auth_server1": "as1",                            "auth_server2": "",
                "auth_survivability": false,                            "bandwidth_limit": "",
                "bandwidth_limit_cb": false,                            "blacklist": true,
                "broadcast_filter": "arp",                            "called_station_id_deli": 0,
                "called_station_id_incl_ssid": false,
                "called_station_id_type": "macaddr",                            "captive_exclude":
                [],                            "captive_portal": "disable",
                "captive_portal_proxy_ip": "",
                "captive_portal_proxy_port": "",                            "captive_profile_name":
                "",                            "cloud_guest": false,
                "cluster_name": "",                            "content_filtering": false,
                "deny_intra_vlan_traffic": false,                            "disable_ssid": false,
                "dmo_channel_util_threshold": 90,                            "dot11k": false,
                "dot11r": false,                            "dot11v": false,
                "download_role": false,                            "dtim_period": 1,
                "dynamic_multicast_optimization": false,                            "dynamic_vlans":
                [],                            "enforce_dhcp": false,
                "essid": "wlan1",                            "explicit_ageout_client": false,
                "g_max_tx_rate": "54",                            "g_min_tx_rate": "1",
                "gw_profile_name": "",                            "hide_ssid": false,
                "high_efficiency_disable": true,
                "high_throughput_disable": true,                            "inactivity_timeout":
                1000,                            "index": 1,
                "l2_auth_failthrough": false,                            "l2switch_mode": false,
                "leap_use_session_key": false,
                "local_probe_req_threshold": 0,                            "mac_authentication":
                false,                            "mac_authentication_delimiter": "",
                "mac_authentication_upper_case": false,
                "management_frame_protection": false,
                "max_auth_failures": 0,                            "max_clients_threshold": 64,
                "mdid": "",                            "multicast_rate_optimization": false,
                "name": "wlan1",                            "okc_disable": false,
                "oos_def": "vpn-down",                            "oos_name": "none",
                "oos_time": 30,                            "opmode": "wpa3-aes-ccm-128",
                "opmode_transition_disable": true,                            "per_user_limit": "",
                "per_user_limit_cb": false,                            "radius_accounting": false,
                "radius_accounting_mode": "user-authentication",
                "radius_interim_accounting_interval": 0,
                "reauth_interval": 0,                            "rf_band": "all",
                "roles": [],                            "server_load_balancing": false,
                "set_role_mac_auth": "",
                "set_role_machine_auth_machine_only": "",
                "set_role_machine_auth_user_only": "",
                "set_role_pre_auth": "",                            "ssid_encoding": "utf8",
                "strict_svp": false,                            "termination": false,
                "time_range_profiles_status": [],                            "tspec": false,
                "tspec_bandwidth": 2000,                            "type": "employee",
                "use_ip_for_calling_station": false,                            "user_bridging":
                false,                            "very_high_throughput_disable": true,
                "vlan": "",                            "wep_index": 0,
                "wep_key": "",                            "wispr": false,
                "wmm_background_dscp": "",                            "wmm_background_share": 0,
                "wmm_best_effort_dscp": "",                            "wmm_best_effort_share": 0,
                "wmm_uapsd": true,                            "wmm_video_dscp": "",
                "wmm_video_share": 0,                            "wmm_voice_dscp": "",
                "wmm_voice_share": 0,                            "work_without_uplink": false,
                "wpa_passphrase": "",                            "zone": "",
                "hotspot_profile": ""                          },
                "access_rule": {                            "action": "allow",
                "app_rf_mv_info": "",                            "blacklist": false,
                "classify_media": false,                            "disable_scanning": false,
                "dot1p_priority": "",                            "eport": "any",
                "ipaddr": "any",                            "log": false,
                "match": "match",                            "nat_ip": "",
                "nat_port": 0,                            "netmask": "any",
                "protocol": "any",                            "protocol_id": "",
                "service_name": "",                            "service_type": "network",
                "source": "default",                            "sport": "any",
                "throttle_downstream": "",                            "throttle_upstream": "",
                "time_range": "",                            "tos": "",
                "vlan": 0                          }

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'value': value
        }

        return await self.post(url, json_data=json_data)

    async def configuration_update_wlan(
        self,
        group_name_or_guid: str,
        wlan_name: str,
        value: str,
    ) -> Response:
        """Update an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.
            value (str): "wlan": {
                "a_max_tx_rate": "54",
                "a_min_tx_rate": "6",
                "access_type": "unrestricted",
                "accounting_server1": "",
                "accounting_server2": "",
                "air_time_limit": "",
                "air_time_limit_cb": false,
                "auth_cache_timeout": 24,
                "auth_req_threshold": 0,
                "auth_server1": "as1",
                "auth_server2": "",
                "auth_survivability": false,
                "bandwidth_limit": "",
                "bandwidth_limit_cb": false,
                "blacklist": true,
                "broadcast_filter": "arp",
                "called_station_id_deli": 0,
                "called_station_id_incl_ssid": false,
                "called_station_id_type": "macaddr",
                "captive_exclude": [],
                "captive_portal": "disable",
                "captive_portal_proxy_ip": "",
                "captive_portal_proxy_port": "",
                "captive_profile_name": "",
                "cloud_guest": false,
                "cluster_name": "",
                "content_filtering": false,
                "deny_intra_vlan_traffic": false,
                "disable_ssid": false,
                "dmo_channel_util_threshold": 90,
                "dot11k": false,                                                     "dot11r":
                false,                                                     "dot11v": false,
                "download_role": false,
                "dtim_period": 1,
                "dynamic_multicast_optimization": false,
                "dynamic_vlans": [],
                "enforce_dhcp": false,                                                     "essid":
                "wlan1",
                "explicit_ageout_client": false,
                "g_max_tx_rate": "54",
                "g_min_tx_rate": "1",
                "gw_profile_name": "",
                "hide_ssid": false,
                "high_efficiency_disable": true,
                "high_throughput_disable": true,
                "inactivity_timeout": 1000,
                "index": 1,
                "l2_auth_failthrough": false,
                "l2switch_mode": false,
                "leap_use_session_key": false,
                "local_probe_req_threshold": 0,
                "mac_authentication": false,
                "mac_authentication_delimiter": "",
                "mac_authentication_upper_case": false,
                "management_frame_protection": false,
                "max_auth_failures": 0,
                "max_clients_threshold": 64,
                "mdid": "",
                "multicast_rate_optimization": false,
                "name": "wlan1",                                                     "okc_disable":
                false,                                                     "oos_def": "vpn-down",
                "oos_name": "none",                                                     "oos_time":
                30,                                                     "opmode": "wpa3-aes-
                ccm-128",
                "opmode_transition_disable": true,
                "per_user_limit": "",
                "per_user_limit_cb": false,
                "radius_accounting": false,
                "radius_accounting_mode": "user-authentication",
                "radius_interim_accounting_interval": 0,
                "reauth_interval": 0,                                                     "rf_band":
                "all",                                                     "roles": [],
                "server_load_balancing": false,
                "set_role_mac_auth": "",
                "set_role_machine_auth_machine_only": "",
                "set_role_machine_auth_user_only": "",
                "set_role_pre_auth": "",
                "ssid_encoding": "utf8",
                "strict_svp": false,
                "termination": false,
                "time_range_profiles_status": [],
                "tspec": false,
                "tspec_bandwidth": 2000,                                                     "type":
                "employee",
                "use_ip_for_calling_station": false,
                "user_bridging": false,
                "very_high_throughput_disable": true,
                "vlan": "",                                                     "wep_index": 0,
                "wep_key": "",                                                     "wispr": false,
                "wmm_background_dscp": "",
                "wmm_background_share": 0,
                "wmm_best_effort_dscp": "",
                "wmm_best_effort_share": 0,
                "wmm_uapsd": true,
                "wmm_video_dscp": "",
                "wmm_video_share": 0,
                "wmm_voice_dscp": "",
                "wmm_voice_share": 0,
                "work_without_uplink": false,
                "wpa_passphrase": "",                                                     "zone":
                "",                                                     "hotspot_profile": ""
                },                                                   "access_rule": {
                "action": "allow",
                "app_rf_mv_info": "",
                "blacklist": false,
                "classify_media": false,
                "disable_scanning": false,
                "dot1p_priority": "",                                                     "eport":
                "any",                                                     "ipaddr": "any",
                "log": false,                                                     "match": "match",
                "nat_ip": "",                                                     "nat_port": 0,
                "netmask": "any",                                                     "protocol":
                "any",                                                     "protocol_id": "",
                "service_name": "",
                "service_type": "network",
                "source": "default",                                                     "sport":
                "any",                                                     "throttle_downstream":
                "",                                                     "throttle_upstream": "",
                "time_range": "",                                                     "tos": "",
                "vlan": 0                                                   }

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/{wlan_name}"

        json_data = {
            'value': value
        }

        return await self.put(url, json_data=json_data)

    async def configuration_delete_full_wlan(
        self,
        group_name_or_guid: str,
        wlan_name: str,
    ) -> Response:
        """Delete an existing WLAN.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid}/{wlan_name}"

        return await self.delete(url)

    async def configuration_get_hotspot_list(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get hotspot list of an UI group or swarm.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_get_hotspot_list_by_mode_name(
        self,
        group_name_or_guid: str,
        mode_name: str,
    ) -> Response:
        """Get hotspot list of an UI group or swarm with mode name.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/{mode_name}"

        return await self.get(url)

    async def configuration_get_hotspot_templates(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get hotspot default configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/template"

        return await self.get(url)

    async def configuration_get_hotspot(
        self,
        group_name_or_guid: str,
        hotspot_name: str,
        mode_name: str,
    ) -> Response:
        """Get the information of an existing hotspot.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            hotspot_name (str): Name of Hotspot selected.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/{hotspot_name}/{mode_name}"

        return await self.get(url)

    async def configuration_create_hotspot(
        self,
        group_name_or_guid: str,
        hotspot_name: str,
        mode_name: str,
        value: str,
    ) -> Response:
        """Create a new hotspot.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            hotspot_name (str): Name of Hotspot to create.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.
            value (str): "hotspot": {                            "name": "aruba-passpoint",
                "mode": "HS2",                            "enable": false,
                "comeback_mode": false,                            "gas_comeback_delay": 0,
                "release_number": 0,                            "asra": false,
                "internet": false,                            "osen": false,
                "query_response_length_limit": 127,
                "access_network_type": "private",                            "roam_cons_len_1": 0,
                "roam_cons_oi_1": "",                            "roam_cons_len_2": "",
                "roam_cons_oi_2": "",                            "roam_cons_len_3": 0,
                "roam_cons_oi_3": "",                            "addtl_roam_cons_ois": 0,
                "venue_group": "business",                            "venue_type": "research-and-
                dev-facility",                            "pame_bi": false,
                "group_frame_block": false,                            "p2p_dev_mgmt": false,
                "p2p_cross_connect": false,                            "osu_nai": "",
                "osu_ssid": "",                            "qos_map_range": "",
                "qos_map_excp": "",                            "anqp_nai_realm": "",
                "anqp_venue_name": "",                            "anqp_nwk_auth": "",
                "anqp_roam_cons": "",                            "anqp_3gpp": "",
                "anqp_ip_addr_avail": "",                            "anqp_domain_name": "",
                "h2qp_oper_name": "",                            "h2qp_wan_metrics": "",
                "h2qp_conn_cap": "",                            "h2qp_oper_class": "",
                "h2qp_osu_provider": ""                          }

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/{hotspot_name}/{mode_name}"

        json_data = {
            'value': value
        }

        return await self.post(url, json_data=json_data)

    async def configuration_update_hotspot(
        self,
        group_name_or_guid: str,
        hotspot_name: str,
        mode_name: str,
        value: str,
    ) -> Response:
        """Update an existing hotspot.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            hotspot_name (str): Name of Hotspot selected.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.
            value (str): "hotspot": {                                                     "name":
                "aruba-passpoint",                                                     "mode":
                "HS2",                                                     "enable": false,
                "comeback_mode": false,
                "gas_comeback_delay": 0,
                "release_number": 0,                                                     "asra":
                false,                                                     "internet": false,
                "osen": false,
                "query_response_length_limit": 127,
                "access_network_type": "private",
                "roam_cons_len_1": 0,
                "roam_cons_oi_1": "",
                "roam_cons_len_2": "",
                "roam_cons_oi_2": "",
                "roam_cons_len_3": 0,
                "roam_cons_oi_3": "",
                "addtl_roam_cons_ois": 0,
                "venue_group": "business",
                "venue_type": "research-and-dev-facility",
                "pame_bi": false,
                "group_frame_block": false,
                "p2p_dev_mgmt": false,
                "p2p_cross_connect": false,
                "osu_nai": "",                                                     "osu_ssid": "",
                "qos_map_range": "",
                "qos_map_excp": "",
                "anqp_nai_realm": "",
                "anqp_venue_name": "",
                "anqp_nwk_auth": "",
                "anqp_roam_cons": "",
                "anqp_3gpp": "",
                "anqp_ip_addr_avail": "",
                "anqp_domain_name": "",
                "h2qp_oper_name": "",
                "h2qp_wan_metrics": "",
                "h2qp_conn_cap": "",
                "h2qp_oper_class": "",
                "h2qp_osu_provider": ""                                                   }

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/{hotspot_name}/{mode_name}"

        json_data = {
            'value': value
        }

        return await self.put(url, json_data=json_data)

    async def configuration_delete_hotspot(
        self,
        group_name_or_guid: str,
        hotspot_name: str,
        mode_name: str,
    ) -> Response:
        """Delete an existing hotspot.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            hotspot_name (str): Name of Hotspot to be deleted.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid}/{hotspot_name}/{mode_name}"

        return await self.delete(url)

    async def configuration_get_clis(
        self,
        group_name_or_guid: str,
        version: str = None,
    ) -> Response:
        """Get AP configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            version (str, optional): Version of AP.                                      Defalut is
                AP max version.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_name_or_guid}"

        params = {
            'version': version
        }

        return await self.get(url, params=params)

    async def configuration_update_clis(
        self,
        group_name_or_guid: str,
        clis: List[str],
    ) -> Response:
        """Replace AP configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            clis (List[str]): Whole configuration List in CLI format.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_name_or_guid}"

        json_data = {
            'clis': clis
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_ap_settings_clis(
        self,
        serial_number: str,
    ) -> Response:
        """Get per AP setting.

        Args:
            serial_number (str): Hotspot mode name.                                  Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial_number}"

        return await self.get(url)

    async def configuration_update_ap_settings_clis(
        self,
        serial_number: str,
        clis: List[str],
    ) -> Response:
        """Replace per AP setting.

        Args:
            serial_number (str): Hotspot mode name.                                  Example:HS2.
            clis (List[str]): Whole per AP setting List in CLI format

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial_number}"

        json_data = {
            'clis': clis
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_swarm_variables(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get variables config.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/iap_variables/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_update_swarm_variables(
        self,
        group_name_or_guid: str,
        variables: list,
    ) -> Response:
        """Replace AP variables.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            variables (list): Variable List

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/iap_variables/{group_name_or_guid}"

        json_data = {
            'variables': variables
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_dirty_diff(
        self,
        group_name_or_guid: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get dirty diff.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group config_mode records to be returned.
                Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dirty_diff/{group_name_or_guid}"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def configuration_get_ap_settings_v2(
        self,
        serial_number: str,
    ) -> Response:
        """Get an existing ap settings.

        Args:
            serial_number (str): Hotspot mode name.                                  Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial_number}"

        return await self.get(url)

    async def configuration_update_ap_settings_v2(
        self,
        serial_number: str,
        hostname: str,
        ip_address: str,
        zonename: str,
        achannel: str,
        atxpower: str,
        gchannel: str,
        gtxpower: str,
        dot11a_radio_disable: bool,
        dot11g_radio_disable: bool,
        usb_port_disable: bool,
    ) -> Response:
        """Update an existing ap settings.

        Args:
            serial_number (str): Hotspot mode name.                                  Example:HS2.
            hostname (str): hostname
            ip_address (str): ip_address
            zonename (str): zonename
            achannel (str): achannel
            atxpower (str): atxpower
            gchannel (str): gchannel
            gtxpower (str): gtxpower
            dot11a_radio_disable (bool): dot11a_radio_disable
            dot11g_radio_disable (bool): dot11g_radio_disable
            usb_port_disable (bool): usb_port_disable

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial_number}"

        json_data = {
            'hostname': hostname,
            'ip_address': ip_address,
            'zonename': zonename,
            'achannel': achannel,
            'atxpower': atxpower,
            'gchannel': gchannel,
            'gtxpower': gtxpower,
            'dot11a_radio_disable': dot11a_radio_disable,
            'dot11g_radio_disable': dot11g_radio_disable,
            'usb_port_disable': usb_port_disable
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_swarm_config_v2(
        self,
        guid: str,
    ) -> Response:
        """Get an existing swarm config.

        Args:
            guid (str): GUID of SWARM selected.
                Example:6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/swarm_config/{guid}"

        return await self.get(url)

    async def configuration_update_swarm_config_v2(
        self,
        guid: str,
        name: str,
        ip_address: str,
        timezone_name: str,
        timezone_hr: int,
        timezone_min: int,
    ) -> Response:
        """Update an existing swarm config.

        Args:
            guid (str): guid of Swarm selected.
                Example:6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): name
            ip_address (str): ip_address
            timezone_name (str): List of timezone names,                                  ["none",
                "International-Date-Line-West", "Coordinated-Universal-Time-11", "Hawaii", "Alaska",
                "Baja-California", "Pacific-Time", "Arizona", "Chihuahua", "La-Paz", "Mazatlan",
                "Mountain-Time",                                   "Central-America", "Central-
                Time", "Guadalajara", "Mexico-City", "Monterrey", "Saskatchewan",
                "Bogota", "Lima", "Quito", "Eastern-Time", "Indiana(East)", "Caracas", "Asuncion",
                "Atlantic-Time(Canada)",                                   "Cuiaba", "Georgetown",
                "Manaus", "San-Juan", "Santiago", "Newfoundland", "Brasilia", "Buenos-Aires",
                "Cayenne", "Fortaleza", "Greenland", "Montevideo", "Salvador", "Coordinated-
                Universal-Time-02",                                   "Mid-Atlantic", "Azores",
                "Cape-Verde-Is", "Casablanca", "Coordinated-Universal-Time", "Dublin",
                "Edinburgh", "Lisbon", "London", "Monrovia", "Reykjavik", "Amsterdam", "Berlin",
                "Bern", "Rome",                                   "Stockholm", "Vienna", "Belgrade",
                "Bratislava", "Budapest", "Ljubljana", "Prague", "Brussels",
                "Copenhagen", "Madrid", "Paris", "Sarajevo", "Skopje", "Warsaw", "Zagreb", "West-
                Central-Africa",                                   "Windhoek", "Amman", "Athens",
                "Bucharest", "Beirut", "Cairo", "Damascus", "East-Europe", "Harare",
                "Pretoria", "Helsinki", "Istanbul", "Kyiv", "Riga", "Sofia", "Tallinn", "Vilnius",
                "Jerusalem",                                   "Baghdad", "Minsk", "Kuwait",
                "Riyadh", "Nairobi", "Tehran", "Abu-Dhabi", "Muscat", "Baku", "Moscow",
                "St.Petersburg", "Volgograd", "Port-Louis", "Tbilisi", "Yerevan", "Kabul",
                "Islamabad", "Karachi",                                   "Tashkent", "Chennai",
                "Kolkata", "Mumbai", "New-Delhi", "Sri-Jayawardenepura", "Kathmandu", "Astana",
                "Dhaka", "Ekaterinburg", "Yangon", "Bangkok", "Hanoi", "Jakarta", "Novosibirsk",
                "Beijing", "Chongqing",                                   "HongKong", "Krasnoyarsk",
                "Kuala-Lumpur", "Perth", "Singapore", "Taipei", "Urumqi", "Ulaanbaatar",
                "Irkutsk", "Osaka", "Sapporo", "Tokyo", "Seoul", "Adelaide", "Darwin", "Brisbane",
                "Canberra", "Melbourne",                                   "Sydney", "Guam", "Port-
                Moresby", "Hobart", "Yakutsk", "Solomon-Is.", "New-Caledonia","Vladivostok",
                "Auckland", "Wellington", "Coordinated-Universal-Time+12", "Fiji", "Magadan",
                "Nukualofa", "Samoa"].
            timezone_hr (int): Range value is -12 to 14.
            timezone_min (int): Range value is 0 to 60.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/swarm_config/{guid}"

        json_data = {
            'name': name,
            'ip_address': ip_address,
            'timezone_name': timezone_name,
            'timezone_hr': timezone_hr,
            'timezone_min': timezone_min
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_interfaces(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get Interfaces.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/interfaces"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_update_interfaces(
        self,
        device_serial: str = None,
        group_name: str = None,
        name: str = None,
        description: str = None,
        admin_status: bool = None,
        speed_duplex: str = None,
        routing: bool = None,
        lag_name: str = None,
        vlan_mode: str = None,
        native_vlan_id: int = None,
        access_vlan_id: int = None,
        allowed_vlan_list: List[str] = None,
        ip_address_assignment: str = None,
        ip_address: List[str] = None,
    ) -> Response:
        """Update Interfaces.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            name (str, optional): Pattern: "^1/1/([1-9]|[1-4][0-9]|5[0-6])$|^OOBM$"
            description (str, optional): Pattern: "^([\x20-\x21\x23-\x3E\x40-\x7F])*$"
            admin_status (bool, optional): admin_status
            speed_duplex (str, optional): Please refer device specific documentation for valid
                speed_duplex values for each interface.<br>  Valid Values: 10-Full, 10-Half,
                100-Full, 100-Half, 1000-Full, Auto, Auto 10M, Auto 100M, Auto 1G, Auto 2.5G, Auto
                5G, Auto 10G, Auto 25G, Auto 40G, Auto 50G, Auto 100G
            routing (bool, optional): routing
            lag_name (str, optional): Pattern: "^(lag[
                ]?([1-9]|[1-9][0-9]|[1-4][0-9][0-9]|5[0-1][0-9]|520))*$"
            vlan_mode (str, optional): vlan_mode  Valid Values: access, trunk
            native_vlan_id (int, optional): native_vlan_id
            access_vlan_id (int, optional): access_vlan_id
            allowed_vlan_list (List[str], optional): Configure VLAN to trunk-allowed mode in
                interfaces.<br>Pattern for VLAN: "(^([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[
                0-4])(-([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4]))?$)|(^all$)"
            ip_address_assignment (str, optional): Only configurable at device-
                level.<br>ip_address_assignment field is associated with ip_address. Configure
                interface with static or dhcp mode ipv4/v6 address  Valid Values: DHCP, Static, None
            ip_address (List[str], optional): Only configurable at device-level.<br>ipv4/ipv6
                address with subnet are valid entries<br>Please refer to device specific
                documentation for more information.<br>An example for ipv6 allowed pattern is
                provided.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/interfaces"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'name': name,
            'description': description,
            'admin_status': admin_status,
            'speed_duplex': speed_duplex,
            'routing': routing,
            'lag_name': lag_name,
            'vlan_mode': vlan_mode,
            'native_vlan_id': native_vlan_id,
            'access_vlan_id': access_vlan_id,
            'allowed_vlan_list': allowed_vlan_list,
            'ip_address_assignment': ip_address_assignment,
            'ip_address': ip_address
        }

        return await self.post(url, params=params, json_data=json_data)

    async def configuration_get_lag(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get LAGs.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/lags"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_crud_lag(
        self,
        delete: List[str],
        device_serial: str = None,
        group_name: str = None,
        name: str = None,
        description: str = None,
        admin_status: bool = False,
        port_members: List[str] = None,
        speed_duplex: str = None,
        aggregation_mode: str = 'None',
        routing: bool = False,
        ip_address: List[str] = None,
        loop_protect_enabled: bool = False,
        vlan_mode: str = 'access',
        native_vlan_id: int = None,
        access_vlan_id: int = None,
        allowed_vlan_list: List[str] = None,
        dhcpv4_snooping: str = None,
    ) -> Response:
        """Create/Update/Delete LAGs.

        Args:
            delete (List[str]): LAG list to be deleted
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            name (str, optional): Pattern:
                "^(LAG|Lag|lag)(([1-9]|[1-9][0-9]|[1-4][0-9][0-9]|5[0-1][0-9]|520))$"
            description (str, optional): Pattern: "^([\x20-\x21\x23-\x3E\x40-\x7F])*$"
            admin_status (bool, optional): admin_status
            port_members (List[str], optional): For group-level configuration, port_members pattern
                to refer:<br>"^1\/1\/([1-9]|[1-4][0-9]|5[0-6])$"
            speed_duplex (str, optional): Please refer device specific documentation for valid
                speed_duplex values.<br>  Valid Values: 10-Full, 10-Half, 100-Full, 100-Half,
                1000-Full, Auto, Auto 10M, Auto 100M, Auto 1G, Auto 2.5G, Auto 5G, Auto 10G, Auto
                25G, Auto 50G
            aggregation_mode (str, optional): aggregation_mode  Valid Values: None, LACP active,
                LACP passive
            routing (bool, optional): routing
            ip_address (List[str], optional): Only configurable at device-level.<br>ipv4/ipv6
                address with subnet are valid entries.<br>Please refer to device specific
                documentation for more information.<br>An example for ipv6 allowed pattern is
                provided.<br>
            loop_protect_enabled (bool, optional): loop_protect_enabled
            vlan_mode (str, optional): vlan_mode  Valid Values: access, trunk
            native_vlan_id (int, optional): native_vlan_id
            access_vlan_id (int, optional): access_vlan_id
            allowed_vlan_list (List[str], optional): Configure VLAN to trunk-allowed mode in
                LAGs.<br>Pattern: "(^([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4])(-([1-9][0
                -9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4]))?$)|(^all$)"
            dhcpv4_snooping (str, optional): dhcpv4_snooping

        Returns:
            Response: CentralAPI Response object
        """  # noqa
        url = "/configuration/v1/switch/cx/lags"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'delete': delete,
            'name': name,
            'description': description,
            'admin_status': admin_status,
            'port_members': port_members,
            'speed_duplex': speed_duplex,
            'aggregation_mode': aggregation_mode,
            'routing': routing,
            'ip_address': ip_address,
            'loop_protect_enabled': loop_protect_enabled,
            'vlan_mode': vlan_mode,
            'native_vlan_id': native_vlan_id,
            'access_vlan_id': access_vlan_id,
            'allowed_vlan_list': allowed_vlan_list,
            'dhcpv4_snooping': dhcpv4_snooping
        }

        return await self.post(url, json_data=json_data, params=params)

    async def configuration_get_loop_prevention(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get Loop Prevention.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/loop-prevention"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_update_loop_prevention(
        self,
        device_serial: str = None,
        group_name: str = None,
        name: str = None,
        lag_members: List[str] = None,
        port_priority: int = 128,
        admin_edge_enabled: bool = False,
        bpdu_guard_enabled: bool = False,
        bpdu_filter_enabled: bool = False,
        root_guard_enabled: bool = False,
        loop_protect_enabled: bool = False,
        description: str = None,
    ) -> Response:
        """Update Loop Prevention.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            name (str, optional): Pattern: "(^1/1/([1-9]|[1-4][0-9]|5[0-6])$|^(lag[
                ]?([1-9]|[1-9][0-9]|[1-4][0-9][0-9]|5[0-1][0-9]|520))*$)"
            lag_members (List[str], optional): lag_members
            port_priority (int, optional): Configure spanning-tree port priority in Interface/LAG.
                Valid Values: 0, 16, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208, 224, 240
            admin_edge_enabled (bool, optional): admin_edge_enabled
            bpdu_guard_enabled (bool, optional): Configure spanning-tree bpdu-guard in
                Interface/LAG.
            bpdu_filter_enabled (bool, optional): Configure spanning-tree bpdu-filter in
                Interface/LAG.
            root_guard_enabled (bool, optional): Configure spanning-tree root-filter in
                Interface/LAG.
            loop_protect_enabled (bool, optional): Configure loop-protect in Interface/LAG.
            description (str, optional): description

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/loop-prevention"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'name': name,
            'lag_members': lag_members,
            'port_priority': port_priority,
            'admin_edge_enabled': admin_edge_enabled,
            'bpdu_guard_enabled': bpdu_guard_enabled,
            'bpdu_filter_enabled': bpdu_filter_enabled,
            'root_guard_enabled': root_guard_enabled,
            'loop_protect_enabled': loop_protect_enabled,
            'description': description
        }

        return await self.post(url, params=params, json_data=json_data)

    async def configuration_get_properties(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get Properties.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/properties"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_update_properties(
        self,
        name: str,
        contact: str,
        location: str,
        timezone: str,
        vrf: str,
        dns_servers: List[str],
        ntp_servers: List[str],
        admin_username: str,
        admin_password: str,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Update Properties.

        Args:
            name (str): Only configurable at device-level.<br>Pattern:
                "^((([A-Za-z0-9])+|([A-Za-z0-9]-+)*[A-Za-z0-9]+)*)$"
            contact (str): Pattern: "^[^"?]*$"
            location (str): Pattern: "^[^"?]*$"
            timezone (str): timezone  Valid Values: Africa/Abidjan, Africa/Accra,
                Africa/Addis_Ababa, Africa/Algiers, Africa/Asmara, Africa/Asmera, Africa/Bamako,
                Africa/Bangui, Africa/Banjul, Africa/Bissau, Africa/Blantyre, Africa/Brazzaville,
                Africa/Bujumbura, Africa/Cairo, Africa/Casablanca, Africa/Ceuta, Africa/Conakry,
                Africa/Dakar, Africa/Dar_es_Salaam, Africa/Djibouti, Africa/Douala, Africa/El_Aaiun,
                Africa/Freetown, Africa/Gaborone, Africa/Harare, Africa/Johannesburg, Africa/Juba,
                Africa/Kampala, Africa/Khartoum, Africa/Kigali, Africa/Kinshasa, Africa/Lagos,
                Africa/Libreville, Africa/Lome, Africa/Luanda, Africa/Lubumbashi, Africa/Lusaka,
                Africa/Malabo, Africa/Maputo, Africa/Maseru, Africa/Mbabane, Africa/Mogadishu,
                Africa/Monrovia, Africa/Nairobi, Africa/Ndjamena, Africa/Niamey, Africa/Nouakchott,
                Africa/Ouagadougou, Africa/Porto-Novo, Africa/Sao_Tome, Africa/Timbuktu,
                Africa/Tripoli, Africa/Tunis, Africa/Windhoek, America/Adak, America/Anchorage,
                America/Anguilla, America/Antigua, America/Araguaina,
                America/Argentina/Buenos_Aires, America/Argentina/Catamarca,
                America/Argentina/ComodRivadavia, America/Argentina/Cordoba,
                America/Argentina/Jujuy, America/Argentina/La_Rioja, America/Argentina/Mendoza,
                America/Argentina/Rio_Gallegos, America/Argentina/Salta, America/Argentina/San_Juan,
                America/Argentina/San_Luis, America/Argentina/Tucuman, America/Argentina/Ushuaia,
                America/Aruba, America/Asuncion, America/Atikokan, America/Atka, America/Bahia,
                America/Bahia_Banderas, America/Barbados, America/Belem, America/Belize,
                America/Blanc-Sablon, America/Boa_Vista, America/Bogota, America/Boise,
                America/Buenos_Aires, America/Cambridge_Bay, America/Campo_Grande, America/Cancun,
                America/Caracas, America/Catamarca, America/Cayenne, America/Cayman,
                America/Chicago, America/Chihuahua, America/Coral_Harbour, America/Cordoba,
                America/Costa_Rica, America/Creston, America/Cuiaba, America/Curacao,
                America/Danmarkshavn, America/Dawson, America/Dawson_Creek, America/Denver,
                America/Detroit, America/Dominica, America/Edmonton, America/Eirunepe,
                America/El_Salvador, America/Ensenada, America/Fort_Nelson, America/Fort_Wayne,
                America/Fortaleza, America/Glace_Bay, America/Godthab, America/Goose_Bay,
                America/Grand_Turk, America/Grenada, America/Guadeloupe, America/Guatemala,
                America/Guayaquil, America/Guyana, America/Halifax, America/Havana,
                America/Hermosillo, America/Indiana/Indianapolis, America/Indiana/Knox,
                America/Indiana/Marengo, America/Indiana/Petersburg, America/Indiana/Tell_City,
                America/Indiana/Vevay, America/Indiana/Vincennes, America/Indiana/Winamac,
                America/Indianapolis, America/Inuvik, America/Iqaluit, America/Jamaica,
                America/Jujuy, America/Juneau, America/Kentucky/Louisville,
                America/Kentucky/Monticello, America/Knox_IN, America/Kralendijk, America/La_Paz,
                America/Lima, America/Los_Angeles, America/Louisville, America/Lower_Princes,
                America/Maceio, America/Managua, America/Manaus, America/Marigot,
                America/Martinique, America/Matamoros, America/Mazatlan, America/Mendoza,
                America/Menominee, America/Merida, America/Metlakatla, America/Mexico_City,
                America/Miquelon, America/Moncton, America/Monterrey, America/Montevideo,
                America/Montreal, America/Montserrat, America/Nassau, America/New_York,
                America/Nipigon, America/Nome, America/Noronha, America/North_Dakota/Beulah,
                America/North_Dakota/Center, America/North_Dakota/New_Salem, America/Ojinaga,
                America/Panama, America/Pangnirtung, America/Paramaribo, America/Phoenix,
                America/Port-au-Prince, America/Port_of_Spain, America/Porto_Acre,
                America/Porto_Velho, America/Puerto_Rico, America/Punta_Arenas, America/Rainy_River,
                America/Rankin_Inlet, America/Recife, America/Regina, America/Resolute,
                America/Rio_Branco, America/Rosario, America/Santa_Isabel, America/Santarem,
                America/Santiago, America/Santo_Domingo, America/Sao_Paulo, America/Scoresbysund,
                America/Shiprock, America/Sitka, America/St_Barthelemy, America/St_Johns,
                America/St_Kitts, America/St_Lucia, America/St_Thomas, America/St_Vincent,
                America/Swift_Current, America/Tegucigalpa, America/Thule, America/Thunder_Bay,
                America/Tijuana, America/Toronto, America/Tortola, America/Vancouver,
                America/Virgin, America/Whitehorse, America/Winnipeg, America/Yakutat,
                America/Yellowknife, Antarctica/Casey, Antarctica/Davis, Antarctica/DumontDUrville,
                Antarctica/Macquarie, Antarctica/Mawson, Antarctica/McMurdo, Antarctica/Palmer,
                Antarctica/Rothera, Antarctica/South_Pole, Antarctica/Syowa, Antarctica/Troll,
                Antarctica/Vostok, Arctic/Longyearbyen, Asia/Aden, Asia/Almaty, Asia/Amman,
                Asia/Anadyr, Asia/Aqtau, Asia/Aqtobe, Asia/Ashgabat, Asia/Ashkhabad, Asia/Atyrau,
                Asia/Baghdad, Asia/Bahrain, Asia/Baku, Asia/Bangkok, Asia/Barnaul, Asia/Beirut,
                Asia/Bishkek, Asia/Brunei, Asia/Calcutta, Asia/Chita, Asia/Choibalsan,
                Asia/Chongqing, Asia/Chungking, Asia/Colombo, Asia/Dacca, Asia/Damascus, Asia/Dhaka,
                Asia/Dili, Asia/Dubai, Asia/Dushanbe, Asia/Famagusta, Asia/Gaza, Asia/Harbin,
                Asia/Hebron, Asia/Ho_Chi_Minh, Asia/Hong_Kong, Asia/Hovd, Asia/Irkutsk,
                Asia/Istanbul, Asia/Jakarta, Asia/Jayapura, Asia/Jerusalem, Asia/Kabul,
                Asia/Kamchatka, Asia/Karachi, Asia/Kashgar, Asia/Kathmandu, Asia/Katmandu,
                Asia/Khandyga, Asia/Kolkata, Asia/Krasnoyarsk, Asia/Kuala_Lumpur, Asia/Kuching,
                Asia/Kuwait, Asia/Macao, Asia/Macau, Asia/Magadan, Asia/Makassar, Asia/Manila,
                Asia/Muscat, Asia/Nicosia, Asia/Novokuznetsk, Asia/Novosibirsk, Asia/Omsk,
                Asia/Oral, Asia/Phnom_Penh, Asia/Pontianak, Asia/Pyongyang, Asia/Qatar,
                Asia/Qostanay, Asia/Qyzylorda, Asia/Rangoon, Asia/Riyadh, Asia/Saigon,
                Asia/Sakhalin, Asia/Samarkand, Asia/Seoul, Asia/Shanghai, Asia/Singapore,
                Asia/Srednekolymsk, Asia/Taipei, Asia/Tashkent, Asia/Tbilisi, Asia/Tehran,
                Asia/Tel_Aviv, Asia/Thimbu, Asia/Thimphu, Asia/Tokyo, Asia/Tomsk,
                Asia/Ujung_Pandang, Asia/Ulaanbaatar, Asia/Ulan_Bator, Asia/Urumqi, Asia/Ust-Nera,
                Asia/Vientiane, Asia/Vladivostok, Asia/Yakutsk, Asia/Yangon, Asia/Yekaterinburg,
                Asia/Yerevan, Atlantic/Azores, Atlantic/Bermuda, Atlantic/Canary,
                Atlantic/Cape_Verde, Atlantic/Faeroe, Atlantic/Faroe, Atlantic/Jan_Mayen,
                Atlantic/Madeira, Atlantic/Reykjavik, Atlantic/South_Georgia, Atlantic/St_Helena,
                Atlantic/Stanley, Australia/ACT, Australia/Adelaide, Australia/Brisbane,
                Australia/Broken_Hill, Australia/Canberra, Australia/Currie, Australia/Darwin,
                Australia/Eucla, Australia/Hobart, Australia/LHI, Australia/Lindeman,
                Australia/Lord_Howe, Australia/Melbourne, Australia/North, Australia/NSW,
                Australia/Perth, Australia/Queensland, Australia/South, Australia/Sydney,
                Australia/Tasmania, Australia/Victoria, Australia/West, Australia/Yancowinna,
                Brazil/Acre, Brazil/DeNoronha, Brazil/East, Brazil/West, Canada/Atlantic,
                Canada/Central, Canada/Eastern, Canada/Mountain, Canada/Newfoundland,
                Canada/Pacific, Canada/Saskatchewan, Canada/Yukon, CET, Chile/Continental,
                Chile/EasterIsland, CST6CDT, Cuba, EET, Egypt, Eire, EST, EST5EDT, Etc/GMT,
                Etc/GMT+0, Etc/GMT+1, Etc/GMT+10, Etc/GMT+11, Etc/GMT+12, Etc/GMT+2, Etc/GMT+3,
                Etc/GMT+4, Etc/GMT+5, Etc/GMT+6, Etc/GMT+7, Etc/GMT+8, Etc/GMT+9, Etc/GMT-0,
                Etc/GMT-1, Etc/GMT-10, Etc/GMT-11, Etc/GMT-12, Etc/GMT-13, Etc/GMT-14, Etc/GMT-2,
                Etc/GMT-3, Etc/GMT-4, Etc/GMT-5, Etc/GMT-6, Etc/GMT-7, Etc/GMT-8, Etc/GMT-9,
                Etc/GMT0, Etc/Greenwich, Etc/UCT, Etc/Universal, Etc/UTC, Etc/Zulu,
                Europe/Amsterdam, Europe/Andorra, Europe/Astrakhan, Europe/Athens, Europe/Belfast,
                Europe/Belgrade, Europe/Berlin, Europe/Bratislava, Europe/Brussels,
                Europe/Bucharest, Europe/Budapest, Europe/Busingen, Europe/Chisinau,
                Europe/Copenhagen, Europe/Dublin, Europe/Gibraltar, Europe/Guernsey,
                Europe/Helsinki, Europe/Isle_of_Man, Europe/Istanbul, Europe/Jersey,
                Europe/Kaliningrad, Europe/Kiev, Europe/Kirov, Europe/Lisbon, Europe/Ljubljana,
                Europe/London, Europe/Luxembourg, Europe/Madrid, Europe/Malta, Europe/Mariehamn,
                Europe/Minsk, Europe/Monaco, Europe/Moscow, Europe/Nicosia, Europe/Oslo,
                Europe/Paris, Europe/Podgorica, Europe/Prague, Europe/Riga, Europe/Rome,
                Europe/Samara, Europe/San_Marino, Europe/Sarajevo, Europe/Saratov,
                Europe/Simferopol, Europe/Skopje, Europe/Sofia, Europe/Stockholm, Europe/Tallinn,
                Europe/Tirane, Europe/Tiraspol, Europe/Ulyanovsk, Europe/Uzhgorod, Europe/Vaduz,
                Europe/Vatican, Europe/Vienna, Europe/Vilnius, Europe/Volgograd, Europe/Warsaw,
                Europe/Zagreb, Europe/Zaporozhye, Europe/Zurich, Factory, GB, GB-Eire, GMT, GMT+0,
                GMT-0, GMT0, Greenwich, Hongkong, HST, Iceland, Indian/Antananarivo, Indian/Chagos,
                Indian/Christmas, Indian/Cocos, Indian/Comoro, Indian/Kerguelen, Indian/Mahe,
                Indian/Maldives, Indian/Mauritius, Indian/Mayotte, Indian/Reunion, Iran, Israel,
                Jamaica, Japan, Kwajalein, Libya, MET, Mexico/BajaNorte, Mexico/BajaSur,
                Mexico/General, MST, MST7MDT, Navajo, NZ, NZ-CHAT, Pacific/Apia, Pacific/Auckland,
                Pacific/Bougainville, Pacific/Chatham, Pacific/Chuuk, Pacific/Easter, Pacific/Efate,
                Pacific/Enderbury, Pacific/Fakaofo, Pacific/Fiji, Pacific/Funafuti,
                Pacific/Galapagos, Pacific/Gambier, Pacific/Guadalcanal, Pacific/Guam,
                Pacific/Honolulu, Pacific/Johnston, Pacific/Kiritimati, Pacific/Kosrae,
                Pacific/Kwajalein, Pacific/Majuro, Pacific/Marquesas, Pacific/Midway, Pacific/Nauru,
                Pacific/Niue, Pacific/Norfolk, Pacific/Noumea, Pacific/Pago_Pago, Pacific/Palau,
                Pacific/Pitcairn, Pacific/Pohnpei, Pacific/Ponape, Pacific/Port_Moresby,
                Pacific/Rarotonga, Pacific/Saipan, Pacific/Samoa, Pacific/Tahiti, Pacific/Tarawa,
                Pacific/Tongatapu, Pacific/Truk, Pacific/Wake, Pacific/Wallis, Pacific/Yap, Poland,
                Portugal, PRC, PST8PDT, ROC, ROK, Singapore, Turkey, UCT, Universal, US/Alaska,
                US/Aleutian, US/Arizona, US/Central, US/East-Indiana, US/Eastern, US/Hawaii,
                US/Indiana-Starke, US/Michigan, US/Mountain, US/Pacific, US/Samoa, UTC, W-SU, WET,
                Zulu
            vrf (str): vrf  Valid Values: default, mgmt
            dns_servers (List[str]): vrf is required to configure dns_servers<br>ipv4/ipv6 address
                without subnet are valid dns_server patterns.<br>Please refer to device specific
                documentation for more information.<br>An example for ipv4 allowed pattern is
                provided.
            ntp_servers (List[str]): vrf is required to configure ntp_servers<br>ipv4/ipv6 address
                without subnet are valid ntp_servers patterns.<br>Please refer to device specific
                documentation for more information.<br>An example for ipv6 allowed pattern is
                provided.
            admin_username (str): Pattern: "^(admin)$"
            admin_password (str): admin_username should be provided with this field.
                Pattern: "^[^"? ]*$"
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/properties"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'name': name,
            'contact': contact,
            'location': location,
            'timezone': timezone,
            'vrf': vrf,
            'dns_servers': dns_servers,
            'ntp_servers': ntp_servers,
            'admin_username': admin_username,
            'admin_password': admin_password
        }

        return await self.post(url, json_data=json_data, params=params)

    async def configuration_get_syslog(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get Syslog.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/syslog"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def post_configuration_v1_switch_cx_syslog(
        self,
        delete: List[str],
        global_severity: str,
        device_serial: str = None,
        group_name: str = None,
        severity: str = 'info',
        vrf: str = 'default',
    ) -> Response:
        """Create/Update/Delete Syslog.

        Args:
            delete (List[str]): Logging servers list to be deleted
            global_severity (str): Configure syslog server severity level.  Valid Values: alert,
                crit, debug, emer, err, info, notice, warning
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            severity (str, optional): severity  Valid Values: alert, crit, debug, emerg, err, info,
                notice, warning
            vrf (str, optional): vrf  Valid Values: default, mgmt

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/syslog"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'delete': delete,
            'global_severity': global_severity,
            'severity': severity,
            'vrf': vrf
        }

        return await self.post(url, json_data=json_data, params=params)

    async def configuration_get_vlans(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get VLANs.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/vlans"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_crud_vlans(
        self,
        delete: List[str],
        device_serial: str = None,
        group_name: str = None,
        vlan_id: int = None,
        name: str = None,
        admin_status: bool = True,
        description: str = None,
        ip_address_assignment: str = 'DHCP',
        ip_address: List[str] = None,
        dhcp_relay: List[str] = None,
        voice: bool = False,
    ) -> Response:
        """Create/Update/Delete VLANs.

        Args:
            delete (List[str]): VLAN list to be deleted
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            vlan_id (int, optional): vlan_id
            name (str, optional): Pattern: "^$|^[^"?]*[A-Za-z0-9]$"
            admin_status (bool, optional): admin_status
            description (str, optional): Pattern: "^([\x20-\x21\x23-\x3E\x40-\x7F])*$"
            ip_address_assignment (str, optional): For VLANs (excluding vlan1) and platforms
                8320/8325/8360, the default value is "None", and "DHCP" is not valid
                entry.<br>ip_address_assignment field is associated with ip_address.  Configure
                interface-VLAN with static or dhcp mode ipv4/v6 address.  Valid Values: DHCP, Static
            ip_address (List[str], optional): ipv4/ipv6 address with subnet are valid
                entries.<br>Please refer to device specific documentation for more
                information.<br>An example for ipv4 allowed pattern is provided.
            dhcp_relay (List[str], optional): Only configurable at device-level.<br>
            voice (bool, optional): voice

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/vlans"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'delete': delete,
            'vlan_id': vlan_id,
            'name': name,
            'admin_status': admin_status,
            'description': description,
            'ip_address_assignment': ip_address_assignment,
            'ip_address': ip_address,
            'dhcp_relay': dhcp_relay,
            'voice': voice
        }

        return await self.post(url, json_data=json_data, params=params)

    # API-NOTE grabs group level sys info password is masked
    async def configuration_get_system_config(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get System Config.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        # [
        #     {
        #         "dns_server": "",
        #         "ntp_server": [
        #             "10.0.30.101",
        #             "10.0.30.52"
        #         ],
        #         "password": "********",
        #         "username": "admin"
        #     }
        # ]
        """
        url = f"/configuration/v1/system_config/{group_name_or_guid}"

        return await self.get(url)

    # API-NOTE Update group level pass for APs??
    async def configuration_update_system_config(
        self,
        group_name_or_guid: str,
        dns_server: str,
        ntp_server: List[str],
        username: str,
        password: str,
    ) -> Response:
        """Update system config.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            dns_server (str): DNS server IPs or domain name
            ntp_server (List[str]): List of ntp server,
                Example: ["192.168.1.1", "127.0.0.0", "xxx.com"].
                IPs or domain name.
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{group_name_or_guid}"

        json_data = {
            'dns_server': dns_server,
            'ntp_server': ntp_server,
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_arm_config(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get ARM configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/arm/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_update_arm_config(
        self,
        group_name_or_guid: str,
        eighty_mhz_support: bool,
        a_channels: str,
        air_time_fairness_mode: str,
        backoff_time: int,
        band_steering_mode: str,
        client_aware: bool,
        client_match: bool,
        cm_calc_interval: int,
        cm_calc_threshold: int,
        cm_holdtime: int,
        cm_key: str,
        cm_match_debug: int,
        cm_max_adaption: int,
        cm_max_request: int,
        cm_nb_matching: int,
        cm_slb_mode: int,
        error_rate_threshold: int,
        error_rate_wait_time: int,
        g_channels: str,
        max_tx_power: str,
        min_tx_power: str,
        rf_channel_quality_aware_arm_disable: bool,
        rf_channel_quality_threshold: int,
        rf_channel_quality_wait_time: int,
        rf_free_channel_index: int,
        rf_ideal_coverage_index: int,
        scanning: bool,
        spectrum_lb: bool,
        wide_bands: str,
    ) -> Response:
        """Update ARM configuration.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            eighty_mhz_support (bool): eighty_mhz_support
            a_channels (str): a_channels
            air_time_fairness_mode (str): air_time_fairness_mode
            backoff_time (int): backoff_time
            band_steering_mode (str): band_steering_mode
            client_aware (bool): client_aware
            client_match (bool): client_match
            cm_calc_interval (int): cm_calc_interval
            cm_calc_threshold (int): cm_calc_threshold
            cm_holdtime (int): cm_holdtime
            cm_key (str): cm_key
            cm_match_debug (int): cm_match_debug
            cm_max_adaption (int): cm_max_adaption
            cm_max_request (int): cm_max_request
            cm_nb_matching (int): cm_nb_matching
            cm_slb_mode (int): cm_slb_mode
            error_rate_threshold (int): error_rate_threshold
            error_rate_wait_time (int): error_rate_wait_time
            g_channels (str): g_channels
            max_tx_power (str): max_tx_power
            min_tx_power (str): min_tx_power
            rf_channel_quality_aware_arm_disable (bool): rf_channel_quality_aware_arm_disable
            rf_channel_quality_threshold (int): rf_channel_quality_threshold
            rf_channel_quality_wait_time (int): rf_channel_quality_wait_time
            rf_free_channel_index (int): rf_free_channel_index
            rf_ideal_coverage_index (int): rf_ideal_coverage_index
            scanning (bool): scanning
            spectrum_lb (bool): spectrum_lb
            wide_bands (str): wide_bands

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/arm/{group_name_or_guid}"

        json_data = {
            '80mhz_support': eighty_mhz_support,
            'a_channels': a_channels,
            'air_time_fairness_mode': air_time_fairness_mode,
            'backoff_time': backoff_time,
            'band_steering_mode': band_steering_mode,
            'client_aware': client_aware,
            'client_match': client_match,
            'cm_calc_interval': cm_calc_interval,
            'cm_calc_threshold': cm_calc_threshold,
            'cm_holdtime': cm_holdtime,
            'cm_key': cm_key,
            'cm_match_debug': cm_match_debug,
            'cm_max_adaption': cm_max_adaption,
            'cm_max_request': cm_max_request,
            'cm_nb_matching': cm_nb_matching,
            'cm_slb_mode': cm_slb_mode,
            'error_rate_threshold': error_rate_threshold,
            'error_rate_wait_time': error_rate_wait_time,
            'g_channels': g_channels,
            'max_tx_power': max_tx_power,
            'min_tx_power': min_tx_power,
            'rf_channel_quality_aware_arm_disable': rf_channel_quality_aware_arm_disable,
            'rf_channel_quality_threshold': rf_channel_quality_threshold,
            'rf_channel_quality_wait_time': rf_channel_quality_wait_time,
            'rf_free_channel_index': rf_free_channel_index,
            'rf_ideal_coverage_index': rf_ideal_coverage_index,
            'scanning': scanning,
            'spectrum_lb': spectrum_lb,
            'wide_bands': wide_bands
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_all_dot11g_radio_profile(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get all Dot11g Radio Profiles.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profiles/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_get_dot11g_radio_config_by_name(
        self,
        group_name_or_guid: str,
        name: str,
    ) -> Response:
        """Get Dot11g radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Name of the dot11g radio profile that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid}/{name}"

        return await self.get(url)

    async def configuration_update_dot11g_radio_profile(
        self,
        group_name_or_guid: str,
        name: str,
        allowed_channels: str,
        beacon_interval: int,
        ch_bw_range: List[str],
        csa_count: int,
        disable_arm_wids_functions: str,
        dot11h: bool,
        high_noise_backoff_time: int,
        interference_immunity: int,
        legacy_mode: bool,
        max_tx_power: int,
        max_tx_power_ai: str,
        min_tx_power: int,
        min_tx_power_ai: str,
        new_name: str,
        scanning_disable: bool,
        smart_antenna: bool,
        spectrum_monitor: bool,
        zone: str,
    ) -> Response:
        """Update/Create Dot11g radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Name of the dot11g radio profile that needs to be deleted.
            allowed_channels (str): allowed_channels
            beacon_interval (int): beacon_interval
            ch_bw_range (List[str]): ch_bw_range
            csa_count (int): csa_count
            disable_arm_wids_functions (str): disable_arm_wids_functions
            dot11h (bool): dot11h
            high_noise_backoff_time (int): high_noise_backoff_time
            interference_immunity (int): interference_immunity
            legacy_mode (bool): legacy_mode
            max_tx_power (int): max_tx_power
            max_tx_power_ai (str): max_tx_power_ai
            min_tx_power (int): min_tx_power
            min_tx_power_ai (str): min_tx_power_ai
            new_name (str): name
            scanning_disable (bool): scanning_disable
            smart_antenna (bool): smart_antenna
            spectrum_monitor (bool): spectrum_monitor
            zone (str): zone

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid}/{name}"

        json_data = {
            'allowed_channels': allowed_channels,
            'beacon_interval': beacon_interval,
            'ch_bw_range': ch_bw_range,
            'csa_count': csa_count,
            'disable_arm_wids_functions': disable_arm_wids_functions,
            'dot11h': dot11h,
            'high_noise_backoff_time': high_noise_backoff_time,
            'interference_immunity': interference_immunity,
            'legacy_mode': legacy_mode,
            'max_tx_power': max_tx_power,
            'max_tx_power_ai': max_tx_power_ai,
            'min_tx_power': min_tx_power,
            'min_tx_power_ai': min_tx_power_ai,
            'new_name': new_name,
            'scanning_disable': scanning_disable,
            'smart_antenna': smart_antenna,
            'spectrum_monitor': spectrum_monitor,
            'zone': zone
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_dot11g_radio_profile(
        self,
        group_name_or_guid: str,
        name: str,
    ) -> Response:
        """Delete Dot11g radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Name of the dot11g radio profile that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid}/{name}"

        return await self.delete(url)

    async def configuration_get_all_dot11a_radio_profile(
        self,
        group_name_or_guid: str,
    ) -> Response:
        """Get all Dot11a Radio Profiles.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profiles/{group_name_or_guid}"

        return await self.get(url)

    async def configuration_get_dot11a_radio_config_by_name(
        self,
        group_name_or_guid: str,
        name: str,
    ) -> Response:
        """Get Dot11a radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Dot11a radio profile name.                         Example: default.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid}/{name}"

        return await self.get(url)

    async def configuration_update_dot11a_radio_profile(
        self,
        group_name_or_guid: str,
        name: str,
        allowed_channels: str,
        beacon_interval: int,
        ch_bw_range: List[str],
        csa_count: int,
        disable_arm_wids_functions: str,
        dot11h: bool,
        high_noise_backoff_time: int,
        interference_immunity: int,
        legacy_mode: bool,
        max_tx_power: int,
        max_tx_power_ai: str,
        min_tx_power: int,
        min_tx_power_ai: str,
        new_name: str,
        scanning_disable: bool,
        smart_antenna: bool,
        spectrum_monitor: bool,
        zone: str,
    ) -> Response:
        """Update/Create Dot11a radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Dot11a radio profile name.                         Example: default.
            allowed_channels (str): allowed_channels
            beacon_interval (int): beacon_interval
            ch_bw_range (List[str]): ch_bw_range
            csa_count (int): csa_count
            disable_arm_wids_functions (str): disable_arm_wids_functions
            dot11h (bool): dot11h
            high_noise_backoff_time (int): high_noise_backoff_time
            interference_immunity (int): interference_immunity
            legacy_mode (bool): legacy_mode
            max_tx_power (int): max_tx_power
            max_tx_power_ai (str): max_tx_power_ai
            min_tx_power (int): min_tx_power
            min_tx_power_ai (str): min_tx_power_ai
            new_name (str): name
            scanning_disable (bool): scanning_disable
            smart_antenna (bool): smart_antenna
            spectrum_monitor (bool): spectrum_monitor
            zone (str): zone

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid}/{name}"

        json_data = {
            'allowed_channels': allowed_channels,
            'beacon_interval': beacon_interval,
            'ch_bw_range': ch_bw_range,
            'csa_count': csa_count,
            'disable_arm_wids_functions': disable_arm_wids_functions,
            'dot11h': dot11h,
            'high_noise_backoff_time': high_noise_backoff_time,
            'interference_immunity': interference_immunity,
            'legacy_mode': legacy_mode,
            'max_tx_power': max_tx_power,
            'max_tx_power_ai': max_tx_power_ai,
            'min_tx_power': min_tx_power,
            'min_tx_power_ai': min_tx_power_ai,
            'new_name': new_name,
            'scanning_disable': scanning_disable,
            'smart_antenna': smart_antenna,
            'spectrum_monitor': spectrum_monitor,
            'zone': zone
        }

        return await self.post(url, json_data=json_data)

    async def configuration_delete_dot11a_radio_profile(
        self,
        group_name_or_guid: str,
        name: str,
    ) -> Response:
        """Delete an existing Dot11a radio profile.

        Args:
            group_name_or_guid (str): Group name of the group or guid of the swarm. Example:Group_1
                or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): Dot11a radio profile name.                         Example: default.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid}/{name}"

        return await self.delete(url)
