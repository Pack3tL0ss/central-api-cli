from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ... import config, constants, log, utils
from ...client import BatchRequest
from ...response import CombinedResponse, Response
from ...utils import Mac

if TYPE_CHECKING:
    from centralcli.client import Session

class MonitoringAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_swarms(
        self,
        group: str = None,
        status: str = None,
        public_ip_address: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        swarm_name: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Swarms.

        Args:
            group (str, optional): Filter by group name
            status (str, optional): Filter by Swarm status
            public_ip_address (str, optional): Filter by public ip address
            fields (str, optional): Comma separated list of fields to be returned
                Valid fields are: status, ip_address, public_ip_address, firmware_version
            calculate_total (bool, optional): Whether to calculate total Swarms
            sort (str, optional): Sort parameter may be one of +swarm_id, -swarm_id
            swarm_name (str, optional): Filter by swarm name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/swarms"

        params = {
            'group': group,
            'status': status,
            'public_ip_address': public_ip_address,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'swarm_name': swarm_name,
            'offset': offset,
            'limit': limit
        }

        params = utils.strip_none(params)

        return await self.session.get(url, params=params)

    async def get_swarm_details(self, swarm_id: str) -> Response:
        """Swarm Details.

        Args:
            swarm_id (str): Swarm ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/swarms/{swarm_id}"

        return await self.session.get(url)

    async def get_clients(
        self,
        client_type: constants.ClientType = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        mac: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get Clients details.

        Args:
            client_type (Literal['wired', 'wireless', 'all'], optional): Client type to retrieve.  Defaults to None.
                if not provided all client types will be returned, unless a filter specific to a client type is
                specified.  i.e. providing band will result in WLAN clients.
            group (str, optional): Filter by Group. Defaults to None.
            swarm_id (str, optional): Filter by swarm. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            network (str, optional): Filter by WLAN SSID. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            serial (str, optional): Filter by connected device serial. Defaults to None.
            os_type (str, optional): Filter by client OS type. Defaults to None.
            stack_id (str, optional): Filter by Stack ID. Defaults to None.
            cluster_id (str, optional): Filter by Cluster ID. Defaults to None.
            band (str, optional): Filter by band. Defaults to None.
            mac (str, optional): Filter by client MAC. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for.  Format:
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): API Paging offset. Defaults to 0.
            limit (int, optional): API record limit per request. Defaults to 1000 Max 1000.

        Returns:
            Response: CentralAPI Response Object
        """
        params = {
            "group": group,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "client_status": client_status,
            "past": past,
            "offset": offset,
            "limit": limit,
        }
        wlan_only_params = {
            "network": network,
            "os_type": os_type,
            "band": band,
            "swarm_id": swarm_id,
        }
        wired_only_params = {
            "stack_id": stack_id,
        }
        all_params = {**params, **wlan_only_params, **wired_only_params}
        wired_params = {**params, **wired_only_params}
        wlan_params = {**params, **wlan_only_params}

        if True in wlan_only_params.values():
            if client_type and client_type != "wireless":
                raise ValueError(f"Invalid combination of filters.  WLAN only filter provided which conflicts with client type {client_type}")
            client_type = "wireless"
        if True in wired_only_params.values():
            if client_type and client_type != "wired":
                raise ValueError(f"Invalid combination of filters.  WIRED only filter provided which conflicts with client type {client_type}")
            client_type = "wired"

        if mac:
            _mac = utils.Mac(
                mac,
                fuzzy=True,
            )

            if _mac.ok:
                mac = _mac
            else:
                return Response(error="INVALID MAC", output=f"The Provided MAC {_mac} Appears to be invalid.")

        if mac:
            return await self.get_client_details(mac,)

        if client_type == "wireless":
            return await self.get_wireless_clients(**wlan_params,)

        if client_type == "wired":
            return await self.get_wired_clients(**wired_params,)

        return await self.get_all_clients(**all_params,)

    async def get_all_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        site: str = None,
        serial: str = None,
        os_type: str = None,
        stack_id: str = None,
        cluster_id: str = None,
        band: str = None,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """Get All clients

        Args:
            group (str, optional): Return clients connected to devices in a given group. Defaults to None.
            swarm_id (str, optional): Return clients connected to swarm by swarm_id. Defaults to None.
            label (str, optional): Return clients connected to device with provided label.
                Defaults to None.
            network (str, optional): Return clients for given network (SSID). Defaults to None.
            site (str, optional): Return clients in a particular site. Defaults to None.
            serial (str, optional): Return clients connected to the device with given serial. Defaults to None.
            os_type (str, optional): Return clients with provided os_type. Defaults to None.
            stack_id (str, optional): Return clients connected to stack with provided id. Defaults to None.
            cluster_id (str, optional): Return clients connected to cluster with provided id. Defaults to None.
            band (str, optional): Return (WLAN) clients connected to provided band. Defaults to None.
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): API offset. Defaults to 0.
            limit (int, optional): API record limit. Defaults to 1000, Max 1000.

        Returns:
            Response: CentralCli.Response object
        """
        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "client_status": client_status,
            "past": past,
            "offset": offset,
            "limit": limit,
            "calculate_total": True
        }
        wlan_only_params = {"network": network, "os_type": os_type, "band": band}
        wired_only_params = {"stack_id": stack_id}

        reqs = [
            BatchRequest(self.get_wireless_clients, **{**params, **wlan_only_params}),
            BatchRequest(self.get_wired_clients, **{**params, **wired_only_params})
        ]

        # FIXME if wireless clients call passes but wired fails there is no indication in cencli show clients output
        # TODO need Response to have an attribute that stores failed calls so cli commands can display output of passed calls and details on errors (when some calls fail)
        resp = await self.session._batch_request(reqs)
        if len(resp) == 2:
            out = []
            for r in resp:
                if r.ok:
                    out += r.output
            raw = [
                {"raw_wireless_response": resp[0].raw},
                {"raw_wired_response": resp[1].raw}
            ]
            resp = resp[1] if resp[1].ok else resp[0]
            resp.output = out
            resp.raw = raw
            return resp

        return resp[-1]

    async def get_wireless_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        network: str = None,
        serial: str = None,
        os_type: str = None,
        cluster_id: str = None,
        band: str = None,
        fields: str = None,
        calculate_total: bool = True,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Wireless Clients.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            network (str, optional): Filter by network name
            serial (str, optional): Filter by AP serial number
            os_type (str, optional): Filter by client os type
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band. Value can be either "2.4" or "5"
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                name, ip_address, username, os_type, connection, associated_device, group_name,
                swarm_id, network, radio_mac, manufacturer, vlan, encryption_method, radio_number,
                speed, usage, health, labels, site, signal_strength, signal_db, snr
            calculate_total (bool, optional): Whether to calculate total wireless Clients
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000, max 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wireless"

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "network": network,
            "serial": serial,
            "os_type": os_type,
            "cluster_id": cluster_id,
            "band": band,
            "fields": fields,
            "calculate_total": str(calculate_total).lower(),
            "client_status": client_status,
            "timerange": past,
            "offset": offset,
            "limit": limit,
        }

        return await self.session.get(url, params=params,)

    async def get_wired_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        fields: str = None,
        calculate_total: bool = True,
        client_status: constants.ClientStatus = "CONNECTED",
        past: str = "3H",
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Wired Clients.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by Switch or AP serial number
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                name, ip_address, username, associated_device, group_name, interface_mac, vlan
            calculate_total (bool, optional): Whether to calculate total wired Clients
            client_status (Literal["FAILED_TO_CONNECT", "CONNECTED"], optional): Return clients that are
                connected, or clients that have failed to connect.  Defaults to CONNECTED.
            past: (str, optional): Time-range to show client details for where
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Defaults to 3H
            FIXME sort (str, optional): Field to sort on.  Defaults to mac
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default 1000, max 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wired"

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            "serial": serial,
            "cluster_id": cluster_id,
            "stack_id": stack_id,
            "fields": fields,
            "calculate_total": str(calculate_total).lower(),
            "client_status": client_status,
            "timerange": past,
            "offset": offset,
            "limit": limit,
        }

        return await self.session.get(url, params=params,)

    async def get_client_details(
        self,
        mac: Mac,
    ) -> Response:
        """Get Client Details.

        Args:
            mac (utils.Mac): MAC address of the Wireless Client to be queried
                API will return results matching a partial Mac

        Returns:
            Response: CentralAPI Response object
        """
        mac = mac if hasattr(mac, "url") else utils.Mac(mac, fuzzy=True,)
        url = f"/monitoring/v2/clients/{mac.url}"
        return await self.session.get(url)

    async def get_client_roaming_history(
        self,
        mac: str,
        calculate_total: bool = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Wireless Client Mobility Trail.

        Args:
            mac (str): MAC address of the Wireless Client to be queried
            calculate_total (bool, optional): Whether to calculate total transitions
            from_time (int | float | datetime, optional): Collect roaming history from this starting point.
                Default is now minus 3 hours.
            to_time (int | float | datetime, optional): End of time-range to collect roaming history for.
                Default is now.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000, max is 1000.

        Returns:
            Response: CentralAPI Response object
        """
        from_time, to_time = utils.parse_time_options(from_time, to_time)
        url = f"/monitoring/v1/clients/wireless/{mac}/mobility_trail"

        params = {
            'calculate_total': calculate_total,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    # API-FLAW aos-sw always shows VLAN as 1 (allowed_vlans represents the PVID for an access port, include all VLANs on a trunk port, no indication of native)
    # API-FLAW aos-sw always shows mode as access, cx does as well, but has vlan_mode which is accurate
    # API-FLAW neither show interface name/description
    async def get_switch_ports(self, iden: str, slot: str = None, stack: bool = False, aos_sw: bool = False) -> Response:
        """Switch Ports Details.

        Args:
            iden (str): Serial number of switch to be queried or the stack_id if it's a stack
            slot (str, optional): Slot name of the ports to be queried {For chassis type switches
                only}.
            stack: (bool, optional) : Get details for stack vs individual switch (iden needs to be the stack_id)
                Defaults to False.
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False (indicating CX switch)

        Returns:
            Response: CentralAPI Response object
        """
        if stack:
            sw_path = "cx_switch_stacks" if not aos_sw else "switch_stacks"
        else:
            sw_path = "cx_switches" if not aos_sw else "switches"
        url = f"/monitoring/v1/{sw_path}/{iden}/ports"

        params = {"slot": slot}

        return await self.session.get(url, params=params)

    async def get_switch_poe_details(
        self,
        serial: str,
        port: str = None,
        aos_sw: bool = False,
    ) -> Response:
        """Get switch poe info.

        Args:
            serial (str): Switch serial
            port (str, optional): Filter by switch port
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False (CX Switch)

        Returns:
            Response: CentralAPI Response object
        """
        sw_path = "cx_switches" if not aos_sw else "switches"
        url = f"/monitoring/v1/{sw_path}/{serial}/poe_detail"

        params = {
            'port': str(port)
        }

        if not port:
            url = f"{url}s"
            params = {}

        return await self.session.get(url, params=params)

    async def get_gateway_ports(self, serial: str) -> Response:
        """Gateway Ports Details.

        Args:
            serial (str): Serial number of Gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports"

        return await self.session.get(url)

    async def get_bssids(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        mac: str = None,
        cluster_id: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List BSSIDs.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by AP serial number
            mac (str, optional): Filter by AP MAC address
            cluster_id (str, optional): Filter by Mobility Controller serial number
            calculate_total (bool, optional): Whether to calculate total APs
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr,-macaddr,
                +swarm_id, -swarm_id. Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/bssids"

        params = {
            'serial': serial,
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "site": site,
            'macaddr': mac,
            'cluster_id': cluster_id,
            'calculate_total': calculate_total,
            'sort': sort,
            "offset": offset,
            "limit": limit,
        }

        return await self.session.get(url, params=params)

    async def get_all_devices(
            self,
            dev_types: constants.GenericDeviceTypes | list[constants.GenericDeviceTypes] = None,
            *,
            group: str = None,
            site: str = None,
            label: str = None,
            serial: str = None,
            mac: str = None,
            model: str = None,
            stack_id: str = None,
            swarm_id: str = None,
            cluster_id: str = None,
            public_ip_address: str = None,
            status: constants.DeviceStatus = None,
            show_resource_details: bool = True,
            calculate_client_count: bool = True,
            calculate_ssid_count: bool = False,
            fields: list = None,
            offset: int = 0,
            limit: int = 1000,  # max allowed 1000
            cache: bool = False,
        ) -> CombinedResponse | list[Response]:
        """Get all devices from Aruba Central.

        Args:
            dev_types (Literal['ap', 'gw', 'cx', 'sw', 'sdwan', 'switch'], optional): Device Types to Update. Defaults to None.
            group (str, optional): Filter by devices in a Group. Defaults to None.
            site (str, optional): Filter by devices in a Site. Defaults to None.
            label (str, optional): Filter by devices with a label assigned. Defaults to None.
            serial (str, optional): Filter by Serial. Defaults to None.
            mac (str, optional): Filter by mac. Defaults to None.
            model (str, optional): Filter by model. Defaults to None.
            stack_id (str, optional): Filter by stack id (switches). Defaults to None.
            swarm_id (str, optional): Filter by swarm id (APs). Defaults to None.
            cluster_id (str, optional): Filter by cluster id. Defaults to None.
            public_ip_address (str, optional): Filter by public ip. Defaults to None.
            status (constants.DeviceStatus, optional): Filter by status. Defaults to None.
            show_resource_details (bool, optional): Show device resource utilization details. Defaults to True.
            calculate_client_count (bool, optional): Calculate client count. Defaults to True.
            calculate_ssid_count (bool, optional): Calculate SSID count. Defaults to False.
            fields (list, optional): fields to return. Defaults to None.
            offset (int, optional): pagination offset. Defaults to 0.
            limit (int, optional): pagination limit max 1000. Defaults to 1000.
            cache (bool, optional): Indicates if response will be used to update cache.

        Returns:
            CombinedResponse: CombinedResponse object.
        """

        dev_types = ["aps", "switches", "gateways"]  if dev_types is None else [constants.lib_to_api(dev_type, "monitoring") for dev_type in dev_types]

        # We always get resource details for switches when cache=True as we need it for the switch_role (standalone/conductor/secondary/member) to store in the cache.
        # We used the switch with an IP to determine which is the conductor in the past, but found scenarios where no IP was showing in central for an extended period of time.
        reqs = [
            BatchRequest(
                self.get_devices,
                dev_type,
                calculate_client_count=calculate_client_count,
                show_resource_details=show_resource_details if not cache or dev_type != "switches" else True,
                group=group,
                label=label,
                stack_id=stack_id,
                swarm_id=swarm_id,
                serial=serial,
                status=status,
                fields=fields,
                cluster_id=cluster_id,
                model=model,
                calculate_ssid_count=calculate_ssid_count,
                mac=mac,
                public_ip_address=public_ip_address,
                site=site,
                offset=offset,
                limit=limit,
            )
            for dev_type in dev_types
        ]
        batch_resp = await self.session._batch_request(reqs)
        if all([not r.ok for r in batch_resp]):
            return utils.unlistify(batch_resp)

        combined = CombinedResponse(batch_resp)

        if combined.ok and combined.failed:  # combined.ok indicates at least 1 call was ok, if None are ok no need for Partial failure msg
            for r in combined.failed:
                log.error(f'Partial Failure {r.url.path} | {r.status} | {r.error}', caption=True)

        return combined

    async def get_devices(
        self,
        device_type: constants.GenericDeviceTypes,
        *,
        group: str = None,
        label: str = None,
        stack_id: str = None,
        swarm_id: str = None,
        serial: str = None,
        status: constants.DeviceStatus = None,
        fields: list = None,
        show_resource_details: bool = False,
        cluster_id: str = None,
        model: str = None,
        calculate_client_count: bool = True,
        calculate_ssid_count: bool = False,
        mac: str = None,
        public_ip_address: str = None,
        site: str = None,
        limit: int = 1000,  # max allowed 1000
        offset: int = 0,
    ) -> Response:
        """Get Devices from Aruba Central API Gateway

        Args:
            device_type (Literal["ap", "gw", "switch"): Type of devices to get.
            group (str, optional): Filter on specific group. Defaults to None.
            label (str, optional): Filter by label. Defaults to None.
            stack_id (str, optional): Return switch with specific stack_id. Defaults to None.
            swarm_id (str, optional): Return APs with a specific swarm_id. Defaults to None.
            serial (str, optional): Return the device with serial number. Defaults to None.
            status (str, optional): Filter by status. Defaults to None.
            fields (list, optional): Return specific fields for device. Defaults to None.
            show_resource_details (bool, optional): Show resource utilization. Defaults to False.
            cluster_id (str, optional): Return gateways with a specific cluster_id. Defaults to None.
            model (str, optional): Filter by device model. Defaults to None.
            calculate_client_count (bool, optional): Calculate client count for each device. Defaults to False.
            calculate_ssid_count (bool, optional): Calculate SSID count for each AP. Defaults to False.
            mac (str, optional): Return device with specific MAC (fuzzy match). Defaults to None.
            public_ip_address (str, optional): Filter devices by Public IP. Defaults to None.
            site (str, optional): Filter by site. Defaults to None.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object

        Raises:
            ValueError: Raised if device_type is not valid.
        """
        if device_type not in ["switches", "aps", "gateways"]:
            device_type = constants.lib_to_api(device_type, "monitoring")
            if device_type not in ["switches", "aps", "gateways"]:
                raise ValueError(f"device_type must be one of ap, gw, switch not {device_type}")

        dev_params = {
            "aps": {
                'serial': serial,
                'macaddr': mac,
                "swarm_id": swarm_id,
                'model': model,
                'cluster_id': cluster_id,
                'fields': fields,
                'calculate_client_count': str(calculate_client_count).lower(),
                'calculate_ssid_count': str(calculate_ssid_count).lower(),
                'show_resource_details': str(show_resource_details).lower(),
            },
            "switches": {
                'stack_id': stack_id,
                'show_resource_details': str(show_resource_details).lower(),
                'calculate_client_count': str(calculate_client_count).lower(),
                'public_ip_address': public_ip_address,
            },
            "gateways": {
                'macaddr': mac,
                'model': model,
                'fields': fields,
            }
        }
        dev_params["mobility_controllers"] = dev_params["gateways"]

        common_params = {
            "group": group,
            "label": label,
            'site': site,
            'status': None if not status else status.title(),
            'offset': offset,
            'limit': limit,
            "calculate_total": "true"  # So we know if we have multile calls that can be ran async
        }

        url = f"/monitoring/v1/{device_type}"
        if device_type == "aps":
            url = url.replace("v1", "v2")
        elif device_type == "gateways" and config.is_cop:
            url = url.replace("v1/gateways", "v2/mobility_controllers")
        params = {**common_params, **dev_params[device_type]}

        return await self.session.get(url, params=params)

    async def get_switch_stacks(
        self,
        hostname: str = None,
        group: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Switch Stacks.

        Args:
            hostname (str, optional): Filter by stack hostname
            group (str, optional): Filter by group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000 and max is 1000.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switch_stacks"

        params = {
            'hostname': hostname,
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    async def get_switch_stack_details(
        self,
        stack_id: str,
    ) -> Response:
        """Switch Stack Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.session.get(url)

    async def get_dev_details(
        self,
        device_type: constants.GenericDeviceTypes,
        serial: str
    ) -> Response:
        """Return Details for a given device

        Args:
            device_type (Literal["ap", "gw", "switch"): Type of devices to get
            serial (str): Serial number of Device

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "monitoring")
        if device_type not in ["switches", "aps", "gateways"]:
            raise ValueError(f"device_type must be one of ap, gw, switch not {device_type}")

        url = f"/monitoring/v1/{device_type}/{serial}"

        return await self.session.get(url)

    async def get_wlans(
        self,
        name: str = None,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        calculate_client_count: bool = None,
        sort_by: str = None
    ) -> Response:
        """List all WLANs (SSIDs).

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            calculate_client_count (bool, optional): Whether to calculate client count per SSID
            sort_by (str, optional): Sort parameter may be one of +essid, -essid. Default is '+essid'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks"
        if name:
            url = f"{url}/{name}"

        if calculate_client_count in [True, False]:
            calculate_client_count = str(calculate_client_count)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'calculate_client_count': calculate_client_count,
            'sort': sort_by,
        }

        return await self.session.get(url, params=params)

    # API-FLAW This method returns next to nothing for reserved IPs.
    # Would be more ideal if it returned client_name pool pvid etc as it does with non resserved IPs
    async def get_dhcp_clients(
        self,
        serial: str,
        reservation: bool = True,
        offset: int = 0,
        limit: int = 100
    ) -> Response:
        """Get DHCP Client information from Gateway.

        Args:
            serial (str): Serial number of mobility controller to be queried
            reservation (bool, optional): Flag to turn on/off listing DHCP reservations(if any).
                Defaults to True
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. max 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        gw_path = "mobility_controllers" if config.is_cop else "gateways"
        url = f"/monitoring/v1/{gw_path}/{serial}/dhcp_clients"

        params = {
            'reservation': str(reservation),
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)

    async def get_dhcp_pools(self, serial: str) -> Response:
        """Gateway DHCP Pools details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/dhcp_pools"

        return await self.session.get(url)

    # API-FLAW total changes during subsequent pagination calls i.e. offset: 0 limit: 1000 = total 2420, offset: 1000 limit: 1000 = total 2408 or 2426 could go up or down.
    # This is handled in Response __add__ method.
    async def get_events(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        client_mac: str = None,
        bssid: str = None,
        device_mac: str = None,
        hostname: str = None,
        device_type: constants.EventDeviceTypes = None,
        sort: str = None,
        site: str = None,
        serial: str = None,
        level: str = None,
        event_description: str = None,
        event_type: str = None,
        fields: str = None,
        calculate_total: bool = True,
        offset: int = 0,
        limit: int = 1000,
        count: int = None,
    ) -> Response:
        """Get device events

        Endpoint allows a max of 10,000 records to be retrieved.  The sum of offset + limit can not
        exceed 10,000

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_time: (int | float | datetime, optional): Start time of the event logs to retrieve.
                Default is current timestamp minus 3 hours.
            to_time (int | float | datetime, optional): End time of the event logs to retrieve.
                seconds. Default is current timestamp.
            client_mac (str, optional): Filter by client MAC address
            bssid (str, optional): Filter by bssid
            device_mac (str, optional): Filter by device_mac
            hostname (str, optional): Filter by hostname
            device_type (str, optional): Filter by device type.
                Valid Values: ap, gw, switch, client
            sort (str, optional): Sort by desc/asc using -timestamp/+timestamp. Default is
                '-timestamp'  Valid Values: -timestamp, +timestamp
            site (str, optional): Filter by site name
            serial (str, optional): Filter by switch serial number
            level (str, optional): Filter by event level
            event_description (str, optional): Filter by event description
            event_type (str, optional): Filter by event type
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                number, level
            calculate_total (bool, optional): Whether to calculate total events. Defaults to True.
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 1000.
            count: Only return <count> results.

        Returns:
            Response: CentralAPI Response object
        """
        # sort needs to stay as default -timestamp for count to grab most recent events.
        url = "/monitoring/v2/events"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        if offset + limit > 10_000:
            if offset >= 10_000:
                log.error(f"get_events provided {offset=}, {limit=} endpoint allows max 10,000", show=True, log=True, caption=True)
                return Response()
            log.warning(f"get_events provided {offset=}, {limit=} adjusted limit to {10_000 - offset} to stay below max 10,000")
            limit = 10_000 - offset

        params = {
            "group": group,
            "swarm_id": swarm_id,
            "label": label,
            "from_timestamp": from_time,
            "to_timestamp": to_time,
            'macaddr': client_mac,
            'bssid': bssid,
            'device_mac': device_mac,
            'hostname': hostname,
            'device_type':  None if not device_type else constants.lib_to_api(device_type, "event"),
            'sort': sort,
            'site': site,
            'serial': serial,
            'level': level,
            'event_description': event_description,
            'event_type': event_type,
            'fields': fields,
            'calculate_total': str(calculate_total),
            "offset": offset,
            "limit": limit if not count or limit < count else count,
        }

        return await self.session.get(url, params=params, count=count)

    async def get_switch_vlans(
        self,
        iden: str,
        stack: bool = False,
        name: str = None,
        pvid: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = True,
        aos_sw: bool = False,
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """Get vlan info for switch (CX and SW).

        Args:
            iden (str): Serial Number or Stack ID, Identifies the dev to return VLANs from.
            stack (bool, optional): Set to True for stack. Default: False
            name (str, optional): Filter by vlan name
            id (int, optional): Filter by vlan id
            tagged_port (str, optional): Filter by tagged port name
            untagged_port (str, optional): Filter by untagged port name
            is_jumbo_enabled (bool, optional): Filter by jumbo enabled
            is_voice_enabled (bool, optional): Filter by voice enabled
            is_igmp_enabled (bool, optional): Filter by igmp enabled
            type (str, optional): Type of the vlan to be queried
            primary_vlan_id (int, optional): Primary Vlan Id of the vlan to be queried"
            status (str, optional): Filter by status of VLAN. Status can be Up/Down
            sort (str, optional): Sort parameter may be one of +name, -name
            calculate_total (bool, optional): Whether to calculate total vlans
            aos_sw (bool, optional): Device is ArubaOS-Switch. Defaults to False
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        sw_url = "switches" if not stack else "switch_stacks"
        sw_url = sw_url if aos_sw else f'cx_{sw_url}'
        url = f"/monitoring/v1/{sw_url}/{iden}/vlan"

        params = {
            "name": name,
            "id": pvid,
            "tagged_port": tagged_port,
            "untagged_port": untagged_port,
            "is_jumbo_enabled": is_jumbo_enabled,
            "is_voice_enabled": is_voice_enabled,
            "is_igmp_enabled": is_igmp_enabled,
            "type": type,
            "primary_vlan_id": primary_vlan_id,
            "status": status,
            "sort": sort,
            "calculate_total": None if not calculate_total else str(calculate_total),  # sending str of False/false will be interpreted as true.  None will strip the param
            "offset": offset,
            "limit": limit,
        }

        return await self.session.get(url, params=params)

    async def get_gateway_vlans(self, serial: str) -> Response:
        """Get gateway VLAN details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/vlan"

        return await self.session.get(url)

    async def get_cx_switch_neighbors(
        self,
        serial: str,
    ) -> Response:
        """Get lldp device neighbor info for CX switch.

        If used on AOS-SW will only return neighbors that are CX switches
        For a stack this will return neighbors for the individual member
        use get_cx_switch_stack_neighbors to get neighbors for entire stack

        Args:
            serial (str): id of the switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/neighbors"

        return await self.session.get(url)

    async def get_cx_switch_stack_neighbors(
        self,
        stack_id: str,
    ) -> Response:
        """Get lldp device neighbor info for CX switch stack.

        Args:
            stack_id (str): Filter by stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switch_stacks/{stack_id}/neighbors"

        return await self.session.get(url)

    async def get_switch_vsx_detail(
        self,
        serial: str,
    ) -> Response:
        """Get switch vsx info for CX switch.

        Args:
            serial (str): Filter by switch serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/vsx"

        return await self.session.get(url)

    async def get_gw_tunnels(
        self, serial: str,
        timerange: constants.TimeRange = "1m",
        limit: int = 250,
        offset: int = 0
    ) -> Response:
        """Get gateway Uplink tunnel details.

        Used by wh_proxy, currently not used by a command will be in show gateway tunnels

        Args:
            serial (str): Serial number of mobility controller to be queried
            timerange (str): Time range for tunnel stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
            limit (int, optional): Pagination limit. Max: 1000 Defaults to 250.
            offset (int, optional): Pagination offset Defaults to 0.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/tunnels"

        params = {
            "timerange": timerange.upper(),
            "offset": offset,
            "limit": limit
        }

        return await self.session.get(url, params=params)


    async def get_gw_uplinks_details(
        self,
        serial: str,
        timerange: constants.TimeRange = "1m",
    ) -> Response:
        """Gateway Uplink Details.

        Args:
            serial (str): Serial number of gateway to be queried
            timerange (str): Time range for Uplink stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
                Valid Values: 3H, 1D, 1W, 1M, 3M

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks"

        params = {
            'timerange': timerange.upper()
        }

        return await self.session.get(url, params=params)

    async def get_gw_uplinks_bandwidth_usage(
        self,
        serial: str,
        uplink_id: str = None,
        interval: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """Gateway Uplink Bandwidth Usage.

        Args:
            serial (str): Gateway serial
            uplink_id (str, optional): Filter by uplink ID.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)


        params = {
            'uplink_id': uplink_id,
            'interval': interval,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.session.get(url, params=params)

    async def get_switch_ports_bandwidth_usage(
        self,
        serial: str,
        switch_type: constants.SwitchTypes = "cx",
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        port: str = None,
        show_uplink: bool = None,
    ) -> Response:
        """Ports Bandwidth Usage for Switch.

        Args:
            serial (str): Serial number of switch to be queried
            switch_type: (Literal["cx", "sw"], optional) = switch type. Valid 'cx', 'sw'.  Defaults to 'cx'
            from (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            show_uplink (bool, optional): Show usage for Uplink ports alone

        Returns:
            Response: CentralAPI Response object
        """
        if show_uplink in [True, False]:
            show_uplink = str(show_uplink).lower()

        url = f"/monitoring/v1/{'cx_' if switch_type == 'cx' else ''}switches/{serial}/ports/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'port': port,
            'show_uplink': show_uplink
        }

        return await self.session.get(url, params=params)

    #  TODO add monitoring_external_controller_get_ap_rf_summary_v3 similar to bandwidth calls, "samples" key has timestamp, noise_floor, and utilization.

    async def get_aps_bandwidth_usage(
        self,
        serial: str = None,
        group: str = None,
        site: str = None,
        label: str = None,
        swarm_id: str = None,
        cluster_id: str = None,
        band: str = None,
        radio_number: int = None,
        network: str = None,
        ethernet_interface_index: int = None,
        interval: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """AP Bandwidth Usage.

        Args:
            serial (str, optional): Filter by AP serial
            group (str, optional): Filter by group name
            site (str, optional): Filter by Site name
            label (str, optional): Filter by Label name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band (2.4, 5 or 6). Valid only when serial parameter is
                specified.
            radio_number (int, optional): Filter by radio_number (0, 1 or 2). Valid only when serial
                parameter is specified.
            network (str, optional): Filter by network name. Valid only when serial parameter is
                specified.
            ethernet_interface_index (int, optional): Filter by ethernet interface index. Valid only
                when serial parameter is specified. Valid range is 0-3.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
                API endpoint defaults to 5minutes when no value is provided.
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v3/aps/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'serial': serial,
            'cluster_id': cluster_id,
            'interval': interval,
            'band': band,
            'radio_number': radio_number,
            'ethernet_interface_index': ethernet_interface_index,
            'network': network,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.session.get(url, params=params)

    async def get_networks_bandwidth_usage(
        self,
        network: str,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
    ) -> Response:
        """WLAN Network Bandwidth usage.

        Use get_wlans to fetch list of networks.

        Args:
            network (str): Network name (ssid) to return usage for
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            from_time (int | float | datetime, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_time (int | float | datetime, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'network': network,
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.session.get(url, params=params)

    async def get_clients_bandwidth_usage(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        serial: str = None,
        mac: str = None,
        from_time: int = None,
        to_time: int = None,
    ) -> Response:
        """Client Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            serial (str, optional): Filter by switch serial
            mac (str, optional): Filter by Client mac
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/bandwidth_usage"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'serial': serial,
            'macaddr': mac,
            'from_timestamp': from_time,
            'to_timestamp': to_time
        }

        return await self.session.get(url, params=params)

    # TODO maybe helper method to delete_device that calls these
    async def delete_gateway(
        self,
        serial: str,
    ) -> Response:
        """Delete Gateway.

        Args:
            serial (str): Serial Number of Gateway to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/mobility_controllers/{serial}" if config.is_cop else f"/monitoring/v1/gateways/{serial}"

        return await self.session.delete(url)

    async def delete_switch(
        self,
        serial: str,
    ) -> Response:
        """Delete Switch.

        Args:
            serial (str): Serial number of switch to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}"

        return await self.session.delete(url)

    async def delete_stack(
        self,
        stack_id: str,
    ) -> Response:
        """Delete Switch Stack.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.session.delete(url)

    async def delete_ap(
        self,
        serial: str,
    ) -> Response:
        """Delete AP.

        Args:
            serial (str): Serial Number of AP to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/aps/{serial}"

        return await self.session.delete(url)
