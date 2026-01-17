from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Literal

from ... import config, constants, utils
from ...client import BatchRequest
from .configuration import ConfigAPI

if TYPE_CHECKING:
    from ...client import Session
    from ...response import Response

class PlatformAPI:
    def __init__(self, session: Session):
        self.session = session

    # API-FLAW limit doesn't appear to have an upper limit, but took forever to return 5,000 records
    async def get_device_inventory(
        self,
        device_type: Literal['ap', 'gw', 'switch', 'all'] = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:  # pragma: no cover Only testing GLP for this going forward
        """Get devices from device inventory.

        Args:
            device_type (Literal['ap', 'gw', 'switch', 'all'], optional): Device Type.
                Defaults to None = 'all' device types.
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        device_type = "all" if not device_type else constants.lib_to_api(device_type, "inventory")
        if config.is_cop and device_type == "gateway":
            device_type = "controller"

        params = {
            'sku_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    # API-FLAW max limit 100 enforced if you provide the limit parameter, otherwise no limit? returned 811 w/ no param provided
    async def get_audit_logs(
        self,
        log_id: str = None,
        username: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        description: str = None,
        target: str = None,
        classification: str = None,
        customer_name: str = None,
        ip_address: str = None,
        app_id: str = None,
        offset: int = 0,
        limit: int = 100,
        count: int = None,
    ) -> Response:
        """Get all audit logs.

        This API returns the first 10,000 results only.

        Args:
            log_id (str, optional): The id of the log to return details for. Defaults to None.
            username (str, optional): Filter audit logs by User Name
            from_time (int | float | datetime, optional): Start time of the audit logs to retrieve.
            to_time (int | float | datetime, optional): End time of the audit logs to retrieve.
            description (str, optional): Filter audit logs by Description
            target (str, optional): Filter audit logs by target (serial number).
            classification (str, optional): Filter audit logs by Classification
            customer_name (str, optional): Filter audit logs by Customer Name
            ip_address (str, optional): Filter audit logs by IP Address
            app_id (str, optional): Filter audit logs by app_id
            offset (int, optional): Number of items to be skipped before returning the data.
                Default to 0.
            limit (int, optional): Maximum number of audit events to be returned max: 100
                Defaults to 100.
            count: Only return <count> results.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/auditlogs/v1/logs"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            "username": username,
            "start_time": from_time,
            "end_time": to_time,
            "description": description,
            "target": target,
            "classification": classification,
            "customer_name": customer_name,
            "ip_address": ip_address,
            "app_id": app_id if not hasattr(app_id, "value") else app_id.value,
            "offset": offset,
            "limit": limit if not count or limit < count else count,
        }

        if log_id:  # pragma: no cover this endpoint is not useful other.get_audit_event_logs is the endpoint with the audit logs
            url = f"{url}/{log_id}"
            params = {}

        return await self.session.get(url, params=params, count=count)

    # TODO make add_device actual func sep and make this an aggregator that calls it and anything else based on params
    # TODO TypeDict for device_list
    async def add_devices(
        self,
        mac: str = None,
        serial: str = None,
        group: str = None,
        # site: int = None,
        part_num: str = None,
        license: str | List[str] = None,
        subscription: str | List[str] = None,
        device_list: List[Dict[str, str]] = None
    ) -> Response | List[Response]:
        """Add device(s) using Mac and Serial number (part_num also required for CoP)
        Will also pre-assign device to group if provided

        Either mac and serial or device_list (which should contain a dict with mac serial) are required.

        Args:
            mac (str, optional): MAC address of device to be added
            serial (str, optional): Serial number of device to be added
            group (str, optional): Add device to pre-provisioned group (additional API call is made)
            site (int, optional): -- Not implemented -- Site ID
            part_num (str, optional): Part Number is required for Central On Prem.
            license (str|List(str), optional): Deprecated use subscription.
            subscription (str|List(str), optional): The subscription/license to assign.
            device_list (List[Dict[str, str]], optional): List of dicts with mac, serial for each device
                and optionally group, part_num, license,

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        license_kwargs = []
        subscription = subscription or license
        if device_list:
            if not isinstance(device_list, list) or not (isinstance(device_list, list) and all(isinstance(d, dict) for d in device_list)):
                raise ValueError("When using device_list to batch add devices, they should be provided as a list of dicts")

        device_list = device_list or []
        if serial or mac:
            device_list += [{"serial": serial, "mac": mac, "group": group, "part_num": part_num, "subscription": subscription}]

        json_data = []  # could simplify by creating pydantic model for validation and decorating the function
        for d in device_list:
            d = {k if k not in constants.possible_sub_keys else "subscription": v for k, v in d.items()}
            mac = d.get("mac", d.get("mac_address"))
            if not mac:
                raise ValueError(f"No Mac Address found for entry {d}")
            else:
                mac = utils.Mac(mac)
                if not mac:
                    raise ValueError(f"Mac Address {mac} appears to be invalid.")
            serial = d.get("serial", d.get("serial_num"))
            if not serial:
                raise ValueError(f"No Serial Number found for entry with MAC Address {mac}")
            _this_dict = {"mac": mac.cols, "serial": serial}
            part_num = d.get("part_num", d.get("partNumber"))
            if part_num:  # pragma: no cover CoP only.  CoP is not currently tested
                _this_dict["partNumber"] = part_num

            json_data += [_this_dict]

        to_group = {d.get("group"): [] for d in device_list if "group" in d and d["group"]}
        for d in device_list:
            if "group" in d and d["group"]:
                to_group[d["group"]].append(d.get("serial", d.get("serial_num")))

        # to_site = {d.get("site"): [] for d in device_list if "site" in d and d["site"]}
        # for d in device_list:
        #     if "site" in d and d["site"]:
        #         to_site[d["site"]].append(d.get("serial", d.get("serial_num")))

        # Gather all serials for each license combination from device_list
        # TODO this needs to be tested
        _lic_kwargs = {}
        for d in device_list:
            if "subscription" not in d or not d["subscription"]:
                continue

            d["subscription"] = utils.listify(d["subscription"])
            _key = f"{d['subscription'] if len(d['subscription']) == 1 else '|'.join(sorted(d['subscription']))}"

            if _key in _lic_kwargs:
                _lic_kwargs[_key]["serials"] += [d["serial"]]
            else:
                _lic_kwargs[_key] = {
                    "services": utils.listify(d["subscription"]),
                    "serials": utils.listify(d["serial"])
                }
        license_kwargs = list(_lic_kwargs.values())

        # Perform API call(s) to Central API GW
        if to_group or license_kwargs:
            # Add devices to central.  1 API call for 1 or many devices.
            br = BatchRequest
            reqs = [
                br(self.session.post, url, json_data=json_data),
            ]
            # Assign devices to pre-provisioned group.  1 API call per group
            if to_group:
                config_api = ConfigAPI(self.session)
                group_reqs = [br(config_api.preprovision_device_to_group, g, devs) for g, devs in to_group.items()]
                reqs = [*reqs, *group_reqs]
            else:  # pragma: no cover
                ...

            # TODO You can add the device to a site after it's been pre-assigned (gateways only)
            # if to_site:
            #     site_reqs = [br(self.move_devices_to_site, s, devs, "gw") for s, devs in to_site.items()]
            #     reqs = [*reqs, *site_reqs]

            # Assign license to devices.  1 API call for all devices with same combination of licenses
            if license_kwargs:
                lic_reqs = [br(self.assign_licenses, **kwargs) for kwargs in license_kwargs]
                reqs = [*reqs, *lic_reqs]

            return await self.session._batch_request(reqs, continue_on_fail=True)
        else:
            return [await self.session.post(url, json_data=json_data)]

    async def cop_delete_device_from_inventory(
        self,
        devices: List[str] = None,
    ) -> Response:  # pragma: no cover not testing cop currently
        """Delete devices using Serial number.  Only applies to CoP deployments.

        Device can not be archived in CoP inventory.

        Args:
            devices (list, optional): List of devices to be deleted from
                GreenLake inventory.  Only applies to CoP

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        devices = [{"serial": serial} for serial in devices]

        return await self.session.delete(url, json_data=devices)

    # TODO verify type-hint for device_list is the right way to do that.
    async def verify_device_addition(
        self,
        serial: str = None,
        mac: str = None,
        device_list: List[Dict[Literal["serial", "mac"], str]] = []
    ) -> Response:  # pragma: no cover Not used by any command and will be updated to use GLP
        """Verify Device Addition

        Args:
            serial (str, optional): Serial Number of device to verify. Defaults to None.
            mac (str, optional): Mac Address of device to verify. Defaults to None.
            device_list (List[Dict[Literal[, optional): device_list list of dicts with
                "serial" and "mac" for each device to verify. Defaults to None.

        Must provide serial and mac for each device either via keyword argument or list.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/verify"
        if serial and mac:
            device_list += {
                "serial_num": serial,
                "mac_address": mac,
            }

        if not device_list:
            raise ValueError(
                "Invalid parameters expecting serial and mac for each device "
                "either via keyword argument or List[dict]."
            )

        return await self.session.post(url, json_data=device_list)

    async def get_subscriptions(
        self,
        sub_type: str = None,
        device_type: constants.GenericDeviceTypes = None,
        offset: int = 0,
        limit: int = 1000,  # Doesn't appear to have max, allowed 10k limit in swagger
    ) -> Response:  # pragma: no cover Only testing GLP for this going forward
        """Get user subscription keys.

        Args:
            suib_type (str, optional): Subscription type.  Supports Basic, Service Token and Multi Tier licensing types as well
            device_type (str, optional): Filter by device type ('ap', 'gw', or 'switch')
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of subscriptions to get Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions"
        if device_type:
            device_type = constants.lib_to_api(device_type, "licensing")
            device_type = device_type if not hasattr(device_type, "value") else device_type.value
        if sub_type:
            if hasattr(sub_type, "value"):
                sub_type = sub_type.value
            sub_type = sub_type.replace("-", " ").replace(" ", "_").upper()

        params = {
            'license_type': sub_type,
            'device_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_subscription_stats(
        self,
        license_type: str = 'all',
        service: str = None,
        app_only_stats: bool = None,
    ) -> Response:
        """Get subscription stats.

        Args:
            license_type (str, optional): Supports basic/special/all.
                special - will fetch the statistics of special central services like pa, ucc, clarity etc.
                basic - will fetch the statistics of device management service licenses.
                all - will fetch both of these license types.

                Also supports multi tier license types such foundation_ap, advanced_switch_6300,
                foundation_70XX etc.

            service (str, optional): Service type: pa/pa,clarity,foundation_ap,
                advanced_switch_6300, foundation_70XX  etc.
            app_only_stats (bool, optional): If value is True, stats only for the current
                application returned rather than global stats

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/stats"

        params = {
            'license_type': license_type,
            'service': service,
            'app_only_stats': app_only_stats
        }

        return await self.session.get(url, params=params)

    async def get_valid_subscription_names(
        self,
        service_category: str = None,
        device_type: constants.GenericDeviceTypes = None,
    ) -> Response:
        """Get Valid subscription names from Central.

        Args:
            service_category (str, optional): Service category - dm/network
            device_type (Literal['ap', 'gw', 'switch'], optional): Device Type one of ap, gw, switch

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/config"
        if device_type:
            device_type = constants.lib_to_api(device_type, "licensing")

        params = {
            'service_category': service_category,
            'device_type': device_type
        }

        return await self.session.get(url, params=params)

    async def assign_licenses(self, serials: str | List[str], services: str | List[str]) -> Response:
        """Assign subscription to a device.

        // Used indirectly by add device when --license <license> is provided and batch add devices with license //

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Raises:
            ValueError: When more the 50 serials are provided, which exceeds the max allowed by the API endpoint.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/assign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        if len(serials) > 50:  # pragma: no cover Not testing as focus is on GLP call for the same now.
            raise ValueError(f"{url} endpoint allows a max of 50 serials per call.  {len(serials)} were provided.")

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.session.post(url, json_data=json_data)

    async def unassign_licenses(
        self,
        serials: str | List[str],
        services: str | List[str]
    ) -> Response:  # pragma: no cover Only testing GLP for this going forward
        """Unassign subscription(s) from device(s).

        Args:
            serials (str | List[str]): List of serial number of device.
            services (str | List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Raises:
            ValueError: When more the 50 serials are provided, which exceeds the max allowed by the API endpoint.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/unassign"
        serials = utils.listify(serials)
        services = utils.listify(services)

        if len(serials) > 50:
            raise ValueError(f"{url} endpoint allows a max of 50 serials per call.  {len(serials)} were provided.")

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.session.post(url, json_data=json_data)

    async def get_archived_devices(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> Response:
        """Get Archived devices from device inventory.

        Args:
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 50 (which is also the max).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/archive"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def archive_devices(
        self,
        serials: List[str],
    ) -> Response:
        """Archive devices using Serial list.

        Args:
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/archive"

        json_data = {
            'serials': utils.listify(serials)
        }

        return await self.session.post(url, json_data=json_data)

    # API-NOTE cencli remove archive [devices]
    async def unarchive_devices(
        self,
        serials: List[str],
    ) -> Response:
        """Unarchive devices using Serial list.

        Args:
            serials (List[str]): serials

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/unarchive"

        json_data = {
            'serials': utils.listify(serials)
        }

        return await self.session.post(url, json_data=json_data)

    # API-FLAW none of the auto_subscribe endpoints work
    async def get_auto_subscribe(
        self,
    ) -> Response:
        """Get the services which have auto subscribe enabled.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        return await self.session.get(url)

    async def enable_auto_subscribe(
        self,
        services: List[str] | str,
    ) -> Response:
        """Standalone Customer API: Assign licenses to all devices and enable auto subscribe for
        given services.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        json_data = {
            'services': utils.listify(services)
        }

        return await self.session.post(url, json_data=json_data)

    async def disable_auto_subscribe(
        self,
        services: List[str] | str,
    ) -> Response:
        """Standalone Customer API: Disable auto licensing for given services.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        json_data = {
            'services': utils.listify(services)
        }

        return await self.session.delete(url, json_data=json_data)

    async def get_user_accounts(
        self,
        app_name: str = None,
        type: str = None,
        status: str = None,
        order_by: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List user accounts.

        Args:
            app_name (str, optional): Appname nms to filter Aruba Central users, and account_setting
                to filter HPE GreenLake Edge to Cloud Platform (CCS) application users  Valid
                Values: nms, account_setting
            type (str, optional): Filter based on system or federated user  Valid Values: system,
                federated
            status (str, optional): Filter user based on status (inprogress, failed)  Valid Values:
                inprogress, failed
            order_by (str, optional): Sort ordering (ascending or descending). +username signifies
                ascending order of username.  Valid Values: +username, -username
            offset (int, optional): Zero based offset to start from Defaults to 0.
            limit (int, optional): Maximum number of items to return Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/users"

        params = {
            'app_name': app_name,
            'type': type,
            'status': status,
            'order_by': order_by,
            'offset': offset,
            'limit': limit
        }

        # TODO this needs a fair amount of massaging to turn into a command, it's nested dicts
        # example response in private vscode dir.
        resp = await self.session.get(url, params=params)
        return resp
