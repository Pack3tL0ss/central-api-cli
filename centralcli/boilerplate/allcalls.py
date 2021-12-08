import sys
import asyncio
from pathlib import Path
from typing import Dict, Union, List


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

    async def platform_get_idp_metadata(self, domain: str) -> Response:
        """SAML Metadata for the given domain.

        Args:
            domain (str): domain name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/aaa_config/v1/authentication/profiles/metadata/{domain}"

        return await self.get(url)

    async def platform_get_idp_source(self, domain: str = 'None', offset: int = 0,
                                      limit: int = 100) -> Response:
        """List IDP Authentication Sources.

        Args:
            domain (str, optional): Domain name. Defaults to None
            offset (int, optional): Zero based offset to start from. Defaults to 0 Defaults to 0.
            limit (int, optional): Maximum number of items to return. Defaults to 100 Defaults to
                100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source"

        params = {
            'domain': domain,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_add_idp_source(self, domain: str, login_url: str, logout_url: str,
                                      public_cert: str, entity_id: str) -> Response:
        """Add IDP Authentication Source.

        Args:
            domain (str): Domain name to Federate
            login_url (str): URL for IDP's login page
            logout_url (str): URL for IDP's logout page
            public_cert (str): IDP's public certificate
            entity_id (str): Entity ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source"

        json_data = {
            'domain': domain,
            'login_url': login_url,
            'logout_url': logout_url,
            'public_cert': public_cert,
            'entity_id': entity_id
        }

        return await self.post(url, json_data=json_data)

    async def platform_update_idp_source(self, domain: str, login_url: str, logout_url: str,
                                         public_cert: str, entity_id: str) -> Response:
        """Update IDP Authentication Source.

        Args:
            domain (str): Update IDP Authentication source for given domain
            login_url (str): URL for IDP's login page
            logout_url (str): URL for IDP's logout page
            public_cert (str): IDP's public certificate
            entity_id (str): Entity ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source"

        params = {
            'domain': domain
        }

        json_data = {
            'login_url': login_url,
            'logout_url': logout_url,
            'public_cert': public_cert,
            'entity_id': entity_id
        }

        return await self.patch(url, params=params, json_data=json_data)

    async def platform_delete_idp_source(self, domain: str) -> Response:
        """Delete IDP Authentication Source.

        Args:
            domain (str): Delete IDP Authentication source for given domain

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source"

        params = {
            'domain': domain
        }

        return await self.delete(url, params=params)

    async def platform_upload_metadata(self, domain: str, saml_meta_data: Union[Path, str]) -> Response:
        """Upload IDP Authentication Source.

        Args:
            domain (str): Domain for which metadata configurations are being added
            saml_meta_data (Union[Path, str]): File with XML metadata

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source/upload/metadata"
        saml_meta_data = saml_meta_data if isinstance(saml_meta_data, Path) else Path(str(saml_meta_data))

        params = {
            'domain': domain
        }

        return await self.post(url, params=params)

    async def platform_upload_certificate(self, domain: str, saml_certificate: Union[Path, str]) -> Response:
        """Upload IDP Authentication Source Certificate.

        Args:
            domain (str): Domain for which certificate is being uploaded.
            saml_certificate (Union[Path, str]): File with IDP certificate

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v1/authentication/idp/source/upload/certificate"
        saml_certificate = saml_certificate if isinstance(saml_certificate, Path) else Path(str(saml_certificate))

        params = {
            'domain': domain
        }

        return await self.post(url, params=params)

    async def auditlogs_get_audits(self, group_name: str = None, device_id: str = None,
                                   classification: str = None, start_time: int = None,
                                   end_time: int = None, offset: int = 0, limit: int = 100) -> Response:
        """Get all audit events for all groups.

        Args:
            group_name (str, optional): Filter audit events by Group Name
            device_id (str, optional): Filter audit events by Target / Device ID. Device ID for AP
                is VC Name and Serial Number for Switches
            classification (str, optional): Filter audit events by classification
            start_time (int, optional): Filter audit logs by Time Range. Start time of the audit
                logs should be provided in epoch seconds
            end_time (int, optional): Filter audit logs by Time Range. End time of the audit logs
                should be provided in epoch seconds
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination Defaults to 0.
            limit (int, optional): Maximum number of audit events to be returned Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/auditlogs/v1/events"

        params = {
            'group_name': group_name,
            'device_id': device_id,
            'classification': classification,
            'start_time': start_time,
            'end_time': end_time,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def auditlogs_get_audit_details(self, id: str) -> Response:
        """Get details of an audit event/log.

        Args:
            id (str): ID of audit event

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/auditlogs/v1/event_details/{id}"

        return await self.get(url)

    async def platform_get_audit_logs(self, username: str = None, start_time: int = None,
                                      end_time: int = None, description: str = None,
                                      target: str = None, classification: str = None,
                                      customer_name: str = None, ip_address: str = None,
                                      app_id: str = None, offset: int = 0, limit: int = 100) -> Response:
        """Get all audit logs.

        Args:
            username (str, optional): Filter audit logs by User Name
            start_time (int, optional): Filter audit logs by Time Range. Start time of the audit
                logs should be provided in epoch seconds
            end_time (int, optional): Filter audit logs by Time Range. End time of the audit logs
                should be provided in epoch seconds
            description (str, optional): Filter audit logs by Description
            target (str, optional): Filter audit logs by target (serial number).
            classification (str, optional): Filter audit logs by Classification
            customer_name (str, optional): Filter audit logs by Customer Name
            ip_address (str, optional): Filter audit logs by IP Address
            app_id (str, optional): Filter audit logs by app_id
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination Defaults to 0.
            limit (int, optional): Maximum number of audit events to be returned Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/auditlogs/v1/logs"

        params = {
            'username': username,
            'start_time': start_time,
            'end_time': end_time,
            'description': description,
            'target': target,
            'classification': classification,
            'customer_name': customer_name,
            'ip_address': ip_address,
            'app_id': app_id,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_get_audit_log_details(self, id: str) -> Response:
        """Get details of an audit log.

        Args:
            id (str): ID of audit event

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/auditlogs/v1/logs/{id}"

        return await self.get(url)

    async def device_management_send_command_to_device(self, serial: str, command: str) -> Response:
        """Generic commands for device.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}"

        return await self.post(url)

    async def device_management_send_multi_line_cmd(self, serial: str, command: str, port: str) -> Response:
        """Generic Action Command for bouncing interface or POE (power-over-ethernet) port.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
            port (str): Port number for which the command to be executed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}/port/{port}"

        return await self.post(url)

    async def device_management_send_multi_line_cmd_v2(self, serial: str, command: str, port: str) -> Response:
        """Generic Action Command for bouncing interface or POE (power-over-ethernet) port.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed
            port (str): Specify interface port in the format of port number for devices of type HPPC
                Switch or slot/chassis/port for CX Switch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v2/device/{serial}/action/{command}"

        json_data = {
            'port': port
        }

        return await self.post(url, json_data=json_data)

    async def device_management_send_command_to_swarm(self, swarm_id: str, command: str) -> Response:
        """Generic commands for swarm.

        Args:
            swarm_id (str): Swarm ID of device
            command (str): Command mentioned in the description that is to be executed
                valid: 'reboot_swarm', 'erase_configuration'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/swarm/{swarm_id}/action/{command}"

        return await self.post(url)

    async def device_management_send_disconnect_user(self, serial: str, disconnect_user_mac: str,
                                                     disconnect_user_all: bool,
                                                     disconnect_user_network: str) -> Response:
        """Disconnect User.

        Args:
            serial (str): Serial of device
            disconnect_user_mac (str): Specify mac address of client to disconnect
            disconnect_user_all (bool): Use this option to disconnects all clients associated with
                an IAP.
            disconnect_user_network (str): specify network name to disconnect

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/disconnect_user"

        json_data = {
            'disconnect_user_mac': disconnect_user_mac,
            'disconnect_user_all': disconnect_user_all,
            'disconnect_user_network': disconnect_user_network
        }

        return await self.post(url, json_data=json_data)

    async def device_management_send_speed_test(self, serial: str, host: str, options: str) -> Response:
        """Speed Test.

        Args:
            serial (str): Serial of device
            host (str): Speed-Test server IP address
            options (str): Formatted string of optional arguments

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/speedtest"

        json_data = {
            'host': host,
            'options': options
        }

        return await self.post(url, json_data=json_data)

    async def device_management_get_command_status(self, task_id: str) -> Response:
        """Status.

        Args:
            task_id (str): Unique task id to get response of command

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/status/{task_id}"

        return await self.get(url)

    async def device_management_assign_pre_provisioned_group(self, serials: List[str], group: str) -> Response:
        """Assign Pre-Provisioned Group.

        Args:
            serials (List[str]): List of device serials
            group (str): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/group/assign"

        json_data = {
            'serials': serials,
            'group': group
        }

        return await self.post(url, json_data=json_data)

    async def activate_move_devices(self, operation: str, devices: List[str], sync: bool = None) -> Response:
        """Move the devices across customers.

        Args:
            operation (str): Use moveFrom to move the devices from child account to parent account.
                Use moveTo to move the devices from parent account to child account.  Valid Values:
                moveFrom, moveTo
            devices (List[str]): Array of devices MAC addresses to be moved
            sync (bool, optional): Sync the devices from activate to APC. Default is True

        Returns:
            Response: CentralAPI Response object
        """
        url = "/activate/v1/devices"

        json_data = {
            'operation': operation,
            'devices': devices,
            'sync': sync
        }

        return await self.post(url, json_data=json_data)

    async def device_management_activate_sync(self, mm_name: str) -> Response:
        """Trigger activate sync for given MobilityMaster.

        Args:
            mm_name (str): Mobility Master name previously set in ACP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{mm_name}/activate_sync"

        return await self.post(url)

    async def device_management_static_md_mm_assign(self, device_serial: str, mm_name: str) -> Response:
        """Statically assign Mobility Master to Mobility Device.

        Args:
            device_serial (str): Mobility Device serial.
            mm_name (str): Mobility Master name previously set in ACP.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}/{mm_name}"

        return await self.post(url)

    async def device_management_get_md_mm_mapping(self, device_serial: str) -> Response:
        """Get assigned Mobility Master to Mobility Device.

        Args:
            device_serial (str): Mobility Device serial.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}"

        return await self.get(url)

    async def device_management_del_md_mm_mapping(self, device_serial: str) -> Response:
        """Delete Mobility Master to Mobility Device mapping.

        Args:
            device_serial (str): Mobility Device serial.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}"

        return await self.delete(url)

    async def device_management_get_pskeys(self, offset: int = 0, limit: int = 100) -> Response:
        """Get ps keys from device inventory.

        Args:
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of ps keys to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/pskeys"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def device_management_create_psk(self, name: str, psk: str) -> Response:
        """Add PS Keys.

        Args:
            name (str): name
            psk (str): psk

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/pskeys"

        json_data = {
            'name': name,
            'psk': psk
        }

        return await self.post(url, json_data=json_data)

    async def device_management_delete_pskeys(self, name: str) -> Response:
        """Delete PS Keys using name.

        Args:
            name (str): Delete device using PS keys name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/pskeys"

        params = {
            'name': name
        }

        return await self.delete(url, params=params)

    async def device_management_get_controllers(self) -> Response:
        """Get list of controller discovery details from device inventory.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/controllers"

        return await self.get(url)

    async def device_management_add_controller(self, controller_ip: str, controller_name: str,
                                               https_profile_name: str, snmp_profile_name: str) -> Response:
        """Add Controller Profile to Device Inventory.

        Args:
            controller_ip (str): controller_ip
            controller_name (str): controller_name
            https_profile_name (str): https_profile_name
            snmp_profile_name (str): snmp_profile_name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/controllers"

        json_data = {
            'controller_ip': controller_ip,
            'controller_name': controller_name,
            'https_profile_name': https_profile_name,
            'snmp_profile_name': snmp_profile_name
        }

        return await self.post(url, json_data=json_data)

    async def device_management_update_controller(self, controller_ip: str, controller_name: str,
                                                  https_profile_name: str, snmp_profile_name: str) -> Response:
        """Update Controller Profile from Device Inventory.

        Args:
            controller_ip (str): controller_ip
            controller_name (str): controller_name
            https_profile_name (str): https_profile_name
            snmp_profile_name (str): snmp_profile_name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/controllers"

        json_data = {
            'controller_ip': controller_ip,
            'controller_name': controller_name,
            'https_profile_name': https_profile_name,
            'snmp_profile_name': snmp_profile_name
        }

        return await self.put(url, json_data=json_data)

    async def device_management_delete_controller(self, serial: str) -> Response:
        """Delete controller profile using Serial number.

        Args:
            serial (str): Delete controller profile using SN

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/controllers"

        params = {
            'serial': serial
        }

        return await self.delete(url, params=params)

    async def device_management_get_controller_detail(self, serial: str) -> Response:
        """Get controller settings using Serial.

        Args:
            serial (str): Get controller settings using SN

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/controllers/{serial}"

        return await self.get(url)

    async def device_management_create_https_connection_profile(self, name: str, username: str,
                                                                password: str) -> Response:
        """Add HTTPS Connection profile details.

        Args:
            name (str): name
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/https"

        json_data = {
            'name': name,
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def device_management_update_https_connection_profile(self, name: str, username: str,
                                                                password: str) -> Response:
        """Update HTTPS Connection profile details.

        Args:
            name (str): name
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/https"

        json_data = {
            'name': name,
            'username': username,
            'password': password
        }

        return await self.put(url, json_data=json_data)

    async def device_management_get_https_connection_profile_list(self) -> Response:
        """Get list of HTTPS Connection profile details.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/https"

        return await self.get(url)

    async def device_management_get_https_connection_profile(self, name: str) -> Response:
        """Get https connection profile details using name.

        Args:
            name (str): Get https connection profile details using name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/connection_profile/https/{name}"

        return await self.get(url)

    async def device_management_create_snmp_connection_profile(self, name: str, type: str,
                                                               community_string: str,
                                                               username: str, auth_protocol: str,
                                                               auth_password: str,
                                                               privacy_protocol: str,
                                                               privacy_password: str) -> Response:
        """Add SNMP Connection profile details.

        Args:
            name (str): name
            type (str): Snmp type version v2/v3
            community_string (str): Community string is a required value for snmp type v2.
            username (str): username
            auth_protocol (str): Auth protocol values of MD5/SHA
            auth_password (str): auth_password
            privacy_protocol (str): Privacy protocol values of AES/DES
            privacy_password (str): privacy_password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/snmp"

        json_data = {
            'name': name,
            'type': type,
            'community_string': community_string,
            'username': username,
            'auth_protocol': auth_protocol,
            'auth_password': auth_password,
            'privacy_protocol': privacy_protocol,
            'privacy_password': privacy_password
        }

        return await self.post(url, json_data=json_data)

    async def device_management_update_snmp_connection_profile(self, name: str, type: str,
                                                               community_string: str,
                                                               username: str, auth_protocol: str,
                                                               auth_password: str,
                                                               privacy_protocol: str,
                                                               privacy_password: str) -> Response:
        """Update SNMP Connection profile details.

        Args:
            name (str): name
            type (str): Snmp type version v2/v3
            community_string (str): Community string is a required value for snmp type v2.
            username (str): username
            auth_protocol (str): Auth protocol values of MD5/SHA
            auth_password (str): auth_password
            privacy_protocol (str): Privacy protocol values of AES/DES
            privacy_password (str): privacy_password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/snmp"

        json_data = {
            'name': name,
            'type': type,
            'community_string': community_string,
            'username': username,
            'auth_protocol': auth_protocol,
            'auth_password': auth_password,
            'privacy_protocol': privacy_protocol,
            'privacy_password': privacy_password
        }

        return await self.put(url, json_data=json_data)

    async def device_management_get_snmp_connection_profile_list(self) -> Response:
        """Get list of SNMP Connection profile details.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/device_management/v1/connection_profile/snmp"

        return await self.get(url)

    async def device_management_get_snmp_connection_profile(self, name: str) -> Response:
        """Get SNMP connection profile details using name.

        Args:
            name (str): Get snmp connection profile details using name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/connection_profile/snmp/{name}"

        return await self.get(url)

    async def central_get_webhooks_(self) -> Response:
        """List webhooks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"

        return await self.get(url)

    async def central_add_webhook_(self, name: str, urls: List[str]) -> Response:
        """Add Webhook.

        Args:
            name (str): name of the webhook
            urls (List[str]): List of webhook urls

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"

        json_data = {
            'name': name,
            'urls': urls
        }

        return await self.post(url, json_data=json_data)

    async def central_get_webhook_item_(self, wid: str) -> Response:
        """Webhook setting for a specific item.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        return await self.get(url)

    async def central_delete_webhook_(self, wid: str) -> Response:
        """Delete Webhooks.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        return await self.delete(url)

    async def central_update_webhook_(self, wid: str, name: str, urls: List[str]) -> Response:
        """Update webhook settings.

        Args:
            wid (str): id of the webhook
            name (str): name of the webhook
            urls (List[str]): List of webhook urls

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        json_data = {
            'name': name,
            'urls': urls
        }

        return await self.put(url, json_data=json_data)

    async def central_get_webhook_token_(self, wid: str) -> Response:
        """Get Webhook Token.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/token"

        return await self.get(url)

    async def central_refresh_webhook_token_(self, wid: str) -> Response:
        """Refresh the webhook token.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/token"

        return await self.put(url)

    async def central_test_webhook(self, wid: str) -> Response:
        """Test for webhook notification.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/ping"

        return await self.get(url)

    async def dps_monitoring_get_policy_stats(self, cluster_id: str, policy_name: str) -> Response:
        """Gets DPS Policy stats for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            policy_name (str): DPS compliance policy name.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policy/policy_stats/{policy_name}"

        return await self.get(url)

    async def dps_monitoring_getdpspolicystatshigherwindow(self, cluster_id: str,
                                                           policy_name: str,
                                                           from_timestamp: int = None,
                                                           to_timestamp: int = None) -> Response:
        """Gets DPS Policy stats for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            policy_name (str): DPS compliance policy name.
            from_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp minus 3 hours.
            to_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policy/policy_stats_higher_window/{policy_name}"

        params = {
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.get(url, params=params)

    async def dps_monitoring_getdpspolicieskpistats(self, cluster_id: str) -> Response:
        """DPS Key Performance Indicator for a given BOC.

        Args:
            cluster_id (str): cluster_id number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policies/kpi"

        return await self.get(url)

    async def dps_monitoring_getdpspoliciescompliancepercentage(self, cluster_id: str,
                                                                from_timestamp: int = None,
                                                                to_timestamp: int = None) -> Response:
        """DPS Compliance percentage of all DPS Policies for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            from_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp minus 3 hours.
            to_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policies/compliance_percentage"

        return await self.get(url)

    async def dps_monitoring_getdpspoliciesstatus(self, cluster_id: str) -> Response:
        """DPS Compliance Status of all DPS Policies for a given BOC.

        Args:
            cluster_id (str): cluster_id number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policies/status"

        return await self.get(url)

    async def dps_monitoring_getdpspolicieseventlogs(self, cluster_id: str, policy_name: str) -> Response:
        """Gets DPS Policy Event Logs for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            policy_name (str): DPS compliance policy name.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policy/event_logs/{policy_name}"

        return await self.get(url)

    async def dps_monitoring_getdpssitepolicystats(self, site_name: str,
                                                   from_timestamp: int = None,
                                                   to_timestamp: int = None) -> Response:
        """Gets DPS Compliance stats for a given Site.

        Args:
            site_name (str): Name of the site
            from_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp minus 3 hours.
            to_timestamp (int, optional): This is epoch timestamp given in seconds. Default is
                current timestamp.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/sdwan_site/site_policy_stats/{site_name}"

        return await self.get(url)

    async def gdpr_get_gdprs_(self) -> Response:
        """List gdprs opt out MAC clients for this customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/gdpr/v1/opt_out_clients"

        return await self.get(url)

    async def gdpr_add_(self, mac: str) -> Response:
        """Add Gdpr opt out client.

        Args:
            mac (str): MAC address of the Optout client

        Returns:
            Response: CentralAPI Response object
        """
        url = "/gdpr/v1/opt_out_clients"

        json_data = {
            'mac': mac
        }

        return await self.post(url, json_data=json_data)

    async def gdpr_get_mac(self, mac: str) -> Response:
        """GDPR Opt out MAC.

        Args:
            mac (str): mac address of the client to be opted out

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/gdpr/v1/opt_out_clients/{mac}"

        return await self.get(url)

    async def gdpr_delete_(self, mac: str) -> Response:
        """Delete Opt out Mac.

        Args:
            mac (str): mac address of the client to be opted out

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/gdpr/v1/opt_out_clients/{mac}"

        return await self.delete(url)

    async def monitoring_get_networks_v2(self, group: str = None, swarm_id: str = None,
                                         label: str = None, site: str = None,
                                         calculate_client_count: bool = None, sort: str = None) -> Response:
        """List all Networks.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            calculate_client_count (bool, optional): Whether to calculate client count per SSID
            sort (str, optional): Sort parameter may be one of +essid, -essid. Default is '+essid'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks"
        if calculate_client_count in [True, False]:
            calculate_client_count = str(calculate_client_count)

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'calculate_client_count': calculate_client_count,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_network_v2(self, network_name: str, group: str = None,
                                        swarm_id: str = None, label: str = None, site: str = None) -> Response:
        """Get Network details.

        Args:
            network_name (str): Name of the network to be queried
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/networks/{network_name}"

        params = {
            'network_name': network_name,
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site
        }

        return await self.get(url, params=params)

    async def monitoring_get_networks_bandwidth_usage_v2(self, network: str, group: str = None,
                                                         swarm_id: str = None, label: str = None,
                                                         from_timestamp: int = None,
                                                         to_timestamp: int = None,
                                                         site: str = None) -> Response:
        """WLAN Network Bandwidth usage.

        Args:
            network (str): Filter by network name
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            site (str, optional): Filter by Site name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/networks/bandwidth_usage"

        params = {
            'network': network,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.get(url, params=params)

    async def monitoring_get_aps_v2(self, group: str = None, swarm_id: str = None,
                                    label: str = None, site: str = None, status: str = None,
                                    serial: str = None, macaddr: str = None, model: str = None,
                                    cluster_id: str = None, fields: str = None,
                                    calculate_total: bool = None,
                                    calculate_client_count: bool = None,
                                    calculate_ssid_count: bool = None,
                                    show_resource_details: bool = None, sort: str = None,
                                    offset: int = 0, limit: int = 100) -> Response:
        """List Access Points.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            status (str, optional): Filter by AP status
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by AP MAC address
            model (str, optional): Filter by AP Model
            cluster_id (str, optional): Filter by Mobility Controller serial number
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, ip_address, model, firmware_version, swarm_master, labels, radios,
                ap_deployment_mode, public_ip_address, site, last_modified, ap_group, subnet_mask,
                mesh_role
            calculate_total (bool, optional): Whether to calculate total APs
            calculate_client_count (bool, optional): Whether to calculate client count per AP
            calculate_ssid_count (bool, optional): Whether to calculate ssid count per AP
            show_resource_details (bool, optional): Whether to show AP cpu_utilization, uptime,
                mem_total, mem_free, mesh_role, mode.
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr, -macaddr,
                +swarm_id, -swarm_id. Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/aps"

        params = {
            'group': group,
            'label': label,
            'swarm_id': swarm_id,
            'site': site,
            'status': status,
            'serial': serial,
            'macaddr': macaddr,
            'model': model,
            'cluster_id': cluster_id,
            'fields': fields,
            'calculate_total': calculate_total,
            'calculate_client_count': calculate_client_count,
            'calculate_ssid_count': calculate_ssid_count,
            'show_resource_details': show_resource_details,
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def monitoring_get_bssids_v2(self, group: str = None, swarm_id: str = None,
                                       label: str = None, site: str = None, serial: str = None,
                                       macaddr: str = None, cluster_id: str = None,
                                       calculate_total: bool = None, sort: str = None,
                                       offset: int = 0, limit: int = 100) -> Response:
        """List BSSIDs.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by AP MAC address
            cluster_id (str, optional): Filter by Mobility Controller serial number
            calculate_total (bool, optional): Whether to calculate total APs
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr,-macaddr,
                +swarm_id, -swarm_id.Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/bssids"

        params = {
            'serial': serial,
            'macaddr': macaddr,
            'cluster_id': cluster_id,
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_ap(self, serial: str) -> Response:
        """AP Details.

        Args:
            serial (str): Serial Number of AP to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/aps/{serial}"

        return await self.get(url)

    async def monitoring_delete_ap(self, serial: str) -> Response:
        """Delete AP.

        Args:
            serial (str): Serial Number of AP to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/aps/{serial}"

        return await self.delete(url)

    async def monitoring_get_ap_rf_summary_v3(self, serial: str, band: str = None,
                                              radio_number: int = None,
                                              from_timestamp: int = None,
                                              to_timestamp: int = None) -> Response:
        """AP RF Summary.

        Args:
            serial (str): Serial Number of AP to be queried
            band (str, optional): Filter by band (2.4 or 5). Valid only when serial parameter is
                specified.
            radio_number (int, optional): Filter by radio_number (0, 1 or 2). Valid only when serial
                parameter is specified.
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v3/aps/{serial}/rf_summary"

        params = {
            'band': band,
            'radio_number': radio_number
        }

        return await self.get(url, params=params)

    async def monitoring_get_aps_bandwidth_usage_v3(self, group: str = None, swarm_id: str = None,
                                                    label: str = None, site: str = None,
                                                    serial: str = None, cluster_id: str = None,
                                                    interval: str = None, band: str = None,
                                                    radio_number: int = None,
                                                    ethernet_interface_index: int = None,
                                                    network: str = None,
                                                    from_timestamp: int = None,
                                                    to_timestamp: int = None) -> Response:
        """AP Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by AP serial
            cluster_id (str, optional): Filter by Mobility Controller serial number
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            band (str, optional): Filter by band (2.4 or 5). Valid only when serial parameter is
                specified.
            radio_number (int, optional): Filter by radio_number (0, 1 or 2). Valid only when serial
                parameter is specified.
            ethernet_interface_index (int, optional): Filter by ethernet interface index. Valid only
                when serial parameter is specified. Valid range is 0-3.
            network (str, optional): Filter by network name. Valid only when serial parameter is
                specified.
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v3/aps/bandwidth_usage"

        params = {
            'serial': serial,
            'cluster_id': cluster_id,
            'interval': interval,
            'band': band,
            'radio_number': radio_number,
            'ethernet_interface_index': ethernet_interface_index,
            'network': network
        }

        return await self.get(url, params=params)

    async def monitoring_get_aps_bandwidth_usage_topn_v2(self, group: str = None,
                                                         swarm_id: str = None, label: str = None,
                                                         site: str = None, cluster_id: str = None,
                                                         count: int = None,
                                                         from_timestamp: int = None,
                                                         to_timestamp: int = None) -> Response:
        """Top N AP Details.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            count (int, optional): Required top N AP count. Default is 5 and maximum is 100
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/aps/bandwidth_usage/topn"

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'cluster_id': cluster_id,
            'count': count,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
        }

        return await self.get(url, params=params)

    async def monitoring_get_swarms_bandwidth_usage_topn(self, group: str = None,
                                                         count: int = None,
                                                         from_timestamp: int = None,
                                                         to_timestamp: int = None) -> Response:
        """Top N Swarms By Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            count (int, optional): Required top N Swarm count. Default is 5 and maximum is 100
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/swarms/bandwidth_usage/topn"

        params = {
            'count': count
        }

        return await self.get(url, params=params)

    async def monitoring_get_swarms_clients_count_topn(self, group: str = None, count: int = None,
                                                       from_timestamp: int = None,
                                                       to_timestamp: int = None, sort: str = None) -> Response:
        """Top N Swarms By Clients Count.

        Args:
            group (str, optional): Filter by group name
            count (int, optional): Required top N Swarm count. Default is 5 and maximum is 100
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            sort (str, optional): Required sort 'by_peak' or 'by_avg'. Default is 'by_avg'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/swarms/clients_count/topn"

        params = {
            'count': count,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_wireless_clients(self, group: str = None, swarm_id: str = None,
                                              label: str = None, site: str = None,
                                              network: str = None, serial: str = None,
                                              os_type: str = None, cluster_id: str = None,
                                              band: str = None, fields: str = None,
                                              calculate_total: bool = None, sort: str = None,
                                              offset: int = 0, limit: int = 100) -> Response:
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
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wireless"

        params = {
            'network': network,
            'serial': serial,
            'os_type': os_type,
            'cluster_id': cluster_id,
            'band': band,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_wired_clients(self, group: str = None, swarm_id: str = None,
                                           label: str = None, site: str = None,
                                           serial: str = None, cluster_id: str = None,
                                           stack_id: str = None, fields: str = None,
                                           calculate_total: bool = None, sort: str = None,
                                           offset: int = 0, limit: int = 100) -> Response:
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
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/wired"

        params = {
            'serial': serial,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_wireless_client(self, macaddr: str) -> Response:
        """Wireless Client Details.

        Args:
            macaddr (str): MAC address of the Wireless Client to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wireless/{macaddr}"

        return await self.get(url)

    async def monitoring_get_wireless_client_mobility(self, macaddr: str,
                                                      calculate_total: bool = None,
                                                      from_timestamp: int = None,
                                                      to_timestamp: int = None, offset: int = 0,
                                                      limit: int = 100) -> Response:
        """Wireless Client Mobility Trail.

        Args:
            macaddr (str): MAC address of the Wireless Client to be queried
            calculate_total (bool, optional): Whether to calculate total transitions
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wireless/{macaddr}/mobility_trail"

        params = {
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def monitoring_get_wired_client(self, macaddr: str) -> Response:
        """Wired Client Details.

        Args:
            macaddr (str): MAC address of the Wired Client to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wired/{macaddr}"

        return await self.get(url)

    async def monitoring_get_clients_bandwidth_usage(self, group: str = None,
                                                     swarm_id: str = None, label: str = None,
                                                     cluster_id: str = None, stack_id: str = None,
                                                     serial: str = None, macaddr: str = None,
                                                     from_timestamp: int = None,
                                                     to_timestamp: int = None) -> Response:
        """Client Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            serial (str, optional): Filter by switch serial
            macaddr (str, optional): Filter by Client macaddr
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/bandwidth_usage"

        params = {
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'serial': serial,
            'macaddr': macaddr
        }

        return await self.get(url, params=params)

    async def monitoring_get_clients_bandwidth_usage_topn(self, group: str = None,
                                                          swarm_id: str = None, label: str = None,
                                                          network: str = None,
                                                          cluster_id: str = None,
                                                          stack_id: str = None, count: int = None,
                                                          from_timestamp: int = None,
                                                          to_timestamp: int = None) -> Response:
        """Top N Clients.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            network (str, optional): Filter by network name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            count (int, optional): Required top N clients count. Default is 5 and maximum is 100
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/bandwidth_usage/topn"

        params = {
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'count': count
        }

        return await self.get(url, params=params)

    async def monitoring_get_clients_count(self, group: str = None, swarm_id: str = None,
                                           label: str = None, network: str = None,
                                           cluster_id: str = None, stack_id: str = None,
                                           device_type: str = None, serial: str = None,
                                           band: str = None, radio_number: int = None,
                                           from_timestamp: int = None, to_timestamp: int = None) -> Response:
        """Total Clients Count.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            network (str, optional): Filter by network name
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            device_type (str, optional): Filter by device type. Value can be either "AP" or "Switch"
            serial (str, optional): Filter by Ap or serial
            band (str, optional): Filter by band. Value can be either "2.4" or "5". Valid only when
                serial parameter is specified.
            radio_number (int, optional): Filter by radio_number (0 or 1). Valid only when serial
                parameter is specified. If band is provided and radio_number is not provided then
                radio_number is defaulted to 0 and 1 for band 5 and 2.4 respectively.
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/count"

        params = {
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'device_type': device_type,
            'serial': serial,
            'band': band,
            'radio_number': radio_number
        }

        return await self.get(url, params=params)

    async def monitoring_get_swarms(self, group: str = None, status: str = None,
                                    public_ip_address: str = None, fields: str = None,
                                    calculate_total: bool = None, sort: str = None,
                                    swarm_name: str = None, offset: int = 0, limit: int = 100) -> Response:
        """List Swarms.

        Args:
            group (str, optional): Filter by group name
            status (str, optional): Filter by Swarm status
            public_ip_address (str, optional): Filter by public ip address
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, ip_address, public_ip_address, firmware_version
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
            'status': status,
            'public_ip_address': public_ip_address,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'swarm_name': swarm_name
        }

        return await self.get(url, params=params)

    async def monitoring_get_swarm(self, swarm_id: str) -> Response:
        """Swarm Details.

        Args:
            swarm_id (str): Swarm ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def monitoring_get_vpn_info(self, swarm_id: str) -> Response:
        """Vpn Details.

        Args:
            swarm_id (str): Filter by Swarm ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/vpn/info"

        params = {
            'swarm_id': swarm_id
        }

        return await self.get(url, params=params)

    async def monitoring_get_vpn_usage_v3(self, swarm_id: str, tunnel_index: int,
                                          tunnel_name: str, from_timestamp: int,
                                          to_timestamp: int) -> Response:
        """Swarm VPN stats.

        Args:
            swarm_id (str): Swarm ID to which AP belongs to
            tunnel_index (int): Tunnel index
            tunnel_name (str): Tunnel name .
            from_timestamp (int): Need information from this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp minus 3 hours
            to_timestamp (int): Need information to this timestamp. Timestamp is epoch in seconds.
                Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v3/vpn/usage"

        json_data = {
            'swarm_id': swarm_id,
            'tunnel_index': tunnel_index,
            'tunnel_name': tunnel_name,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.post(url, json_data=json_data)

    async def monitoring_get_mcs(self, group: str = None, label: str = None, site: str = None,
                                 status: str = None, macaddr: str = None, model: str = None,
                                 fields: str = None, calculate_total: bool = None,
                                 sort: str = None, offset: int = 0, limit: int = 100) -> Response:
        """List Mobility Controllers.

        You can only specify one of group, label, site

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            status (str, optional): Filter by Mobility Controller status
            macaddr (str, optional): Filter by Mobility Controller MAC address
            model (str, optional): Filter by Mobility Controller Model
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, ip_address, model, firmware_version, labels, ap_count, usage
            calculate_total (bool, optional): Whether to calculate total Mobility Controllers
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr, -macaddr.
                Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/mobility_controllers"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'status': status,
            'macaddr': macaddr,
            'model': model,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def monitoring_get_mc(self, serial: str, stats_metric: bool = False) -> Response:
        """Mobility Controller Details.

        Args:
            serial (str): Serial Number of Mobility Controller to be queried
            stats_metric (bool, optional): If set, gets the uplinks and tunnels count

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}"

        params = {
            'stats_metric': stats_metric
        }

        return await self.get(url, params=params)

    async def monitoring_delete_mc(self, serial: str) -> Response:
        """Delete Mobility Controller.

        Args:
            serial (str): Serial Number of Mobility Controller to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}"

        return await self.delete(url)

    async def monitoring_get_uplinks_bandwidth_usage(self, group: str = None, label: str = None,
                                                     serial: str = None, uplink_id: str = None,
                                                     interval: str = None,
                                                     from_timestamp: int = None,
                                                     to_timestamp: int = None) -> Response:
        """Uplink Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            serial (str, optional): Filter by device serial
            uplink_id (str, optional): Filter by uplink ID. Valid only when serial parameter is
                specified
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/mobility_controllers/uplinks/bandwidth_usage"

        params = {
            'serial': serial,
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_uplinks_tunnel_stats(self, serial: str, uplink_id: str = None,
                                                  interval: str = None,
                                                  from_timestamp: int = None,
                                                  to_timestamp: int = None) -> Response:
        """Uplink tunnel stats.

        Args:
            serial (str): Filter by device serial
            uplink_id (str, optional): Filter by uplink ID. Valid only when serial parameter is
                specified
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/uplinks/tunnel_stats"

        params = {
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_uplinks_wan_compression_usage(self, group: str = None,
                                                           label: str = None, serial: str = None,
                                                           uplink_id: str = None,
                                                           interval: str = None,
                                                           from_timestamp: int = None,
                                                           to_timestamp: int = None) -> Response:
        """Uplink WAN compression stats.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            serial (str, optional): Filter by device serial
            uplink_id (str, optional): Filter by uplink ID. Valid only when serial parameter is
                specified
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/mobility_controllers/uplinks/wan_compression_stats"

        params = {
            'serial': serial,
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_uplinks_distribution(self, group: str = None, label: str = None,
                                                  serial: str = None) -> Response:
        """Uplink distribution.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            serial (str, optional): Filter by device serial

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/mobility_controllers/uplinks/distribution"

        params = {
            'serial': serial
        }

        return await self.get(url, params=params)

    async def monitoring_get_mc_ports_bandwidth_usage(self, serial: str,
                                                      from_timestamp: int = None,
                                                      to_timestamp: int = None, port: str = None) -> Response:
        """Mobility Controllers Ports Bandwidth Usage.

        Args:
            serial (str): Serial number of Mobility Controller to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port (example GE0/0/1)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/ports/bandwidth_usage"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_mc_ports(self, serial: str) -> Response:
        """Mobility Controllers Ports Details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/ports"

        return await self.get(url)

    async def monitoring_get_mc_tunnels(self, serial: str, timerange: str, offset: int = 0,
                                        limit: int = 100) -> Response:
        """Mobility Controllers Uplink Tunnel Details.

        Args:
            serial (str): Serial number of mobility controller to be queried
            timerange (str): Time range for tunnel stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.  Valid Values: 3H,
                1D, 1W, 1M, 3M
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/tunnels"

        params = {
            'timerange': timerange
        }

        return await self.get(url, params=params)

    async def monitoring_get_mc_uplinks_detail(self, serial: str, timerange: str) -> Response:
        """Mobility Controllers Uplink Details.

        Args:
            serial (str): Serial number of mobility controller to be queried
            timerange (str): Time range for Uplink stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
                Valid Values: 3H, 1D, 1W, 1M, 3M

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/uplinks"

        params = {
            'timerange': timerange
        }

        return await self.get(url, params=params)

    async def monitoring_get_dhcp_clients(self, serial: str, reservation: bool = True,
                                          offset: int = 0, limit: int = 100) -> Response:
        """Mobility Controllers DHCP Client information.

        Args:
            serial (str): Serial number of mobility controller to be queried
            reservation (bool, optional): Flag to turn on/off listing DHCP reservations(if any)
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/dhcp_clients"

        params = {
            'reservation': str(reservation)
        }

        return await self.get(url, params=params)

    async def monitoring_get_dhcp_server(self, serial: str) -> Response:
        """Mobility Controllers DHCP Server details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/dhcp_servers"

        return await self.get(url)

    async def monitoring_get_vlan_info(self, serial: str) -> Response:
        """Mobility Controllers VLAN details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/vlan"

        return await self.get(url)

    async def monitoring_get_gateways(self, group: str = None, label: str = None,
                                      site: str = None, status: str = None, macaddr: str = None,
                                      model: str = None, fields: str = None,
                                      calculate_total: bool = None, sort: str = None,
                                      offset: int = 0, limit: int = 100) -> Response:
        """Gateway List.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            status (str, optional): Filter by Gateway status
            macaddr (str, optional): Filter by Gateway MAC address
            model (str, optional): Filter by Gateway Model
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, ip_address, model, firmware_version, labels, ap_count, usage
            calculate_total (bool, optional): Whether to calculate total Gateways
            sort (str, optional): Sort parameter may be one of +serial, -serial, +macaddr, -macaddr.
                Default is '+serial'
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/gateways"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'status': status,
            'macaddr': macaddr,
            'model': model,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway(self, serial: str, stats_metric: bool = False) -> Response:
        """Gateway Details.

        Args:
            serial (str): Serial Number of gateway to be queried
            stats_metric (bool, optional): If set, gets the uplinks and tunnels count

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}"

        params = {
            'stats_metric': stats_metric
        }

        return await self.get(url, params=params)

    async def monitoring_delete_gateway(self, serial: str) -> Response:
        """Delete Gateway.

        Args:
            serial (str): Serial Number of Gateway to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}"

        return await self.delete(url)

    async def monitoring_get_gateway_uplinks_detail(self, serial: str, timerange: str) -> Response:
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
            'timerange': timerange
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_bandwidth_usage(self, serial: str,
                                                             uplink_id: str = None,
                                                             interval: str = None,
                                                             from_timestamp: int = None,
                                                             to_timestamp: int = None) -> Response:
        """Gateway Uplink Bandwidth Usage.

        Args:
            serial (str): Gateway serial
            uplink_id (str, optional): Filter by uplink ID.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/bandwidth_usage"

        params = {
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_tunnel_stats(self, serial: str,
                                                          uplink_id: str = None,
                                                          interval: str = None,
                                                          from_timestamp: int = None,
                                                          to_timestamp: int = None) -> Response:
        """Gateway Uplink tunnel stats.

        Args:
            serial (str): Filter by Gateway serial
            uplink_id (str, optional): Filter by uplink ID. Valid only when serial parameter is
                specified
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/tunnels/stats"

        params = {
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_wan_compression_usage(self, serial: str,
                                                                   uplink_id: str = None,
                                                                   interval: str = None,
                                                                   from_timestamp: int = None,
                                                                   to_timestamp: int = None) -> Response:
        """Gateway Uplink WAN compression stats.

        Args:
            serial (str): Gateway serial
            uplink_id (str, optional): Filter by uplink ID.
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/wan_compression_stats"

        params = {
            'uplink_id': uplink_id,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_distribution(self, serial: str) -> Response:
        """Gateway Uplink distribution.

        Args:
            serial (str): Gateway serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/distribution"

        return await self.get(url)

    async def monitoring_get_gateway_ports_bandwidth_usage(self, serial: str,
                                                           from_timestamp: int = None,
                                                           to_timestamp: int = None,
                                                           port: str = None) -> Response:
        """Gateway Ports Bandwidth Usage.

        Args:
            serial (str): Serial number of Gateway to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port (example GE0/0/1)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports/bandwidth_usage"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_ports(self, serial: str) -> Response:
        """Gateway Ports Details.

        Args:
            serial (str): Serial number of Gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports"

        return await self.get(url)

    async def monitoring_get_gateway_tunnels(self, serial: str, timerange: str = '3H',
                                             offset: int = 0, limit: int = 100) -> Response:
        """Gateway Tunnels Details.

        Args:
            serial (str): Serial number of gateway to be queried
            timerange (str, optional): Time range for tunnel stats information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
                Valid Values: 3H, 1D, 1W, 1M, 3M
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/tunnels"

        params = {
            'timerange': timerange
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_dhcp_clients(self, serial: str, reservation: bool = True,
                                                  offset: int = 0, limit: int = 100) -> Response:
        """Gateway DHCP Clients information.

        Args:
            serial (str): Serial number of gateway to be queried
            reservation (bool, optional): Flag to turn on/off listing DHCP reservations(if any)
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/dhcp_clients"

        params = {
            'reservation': reservation
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_dhcp_pools(self, serial: str) -> Response:
        """Gateway DHCP Pools details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/dhcp_pools"

        return await self.get(url)

    async def monitoring_get_gateway_vlan_info(self, serial: str) -> Response:
        """Gateway VLAN details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/vlan"

        return await self.get(url)

    async def central_get_labels(self, calculate_total: bool = None, category_id: int = None,
                                 sort: str = None, offset: int = 0, limit: int = 100) -> Response:
        """List Labels.

        Args:
            calculate_total (bool, optional): Whether to calculate total Labels
            category_id (int, optional): Label category ID
            sort (str, optional): Sort parameter may be one of +label_name, -label_name,
                +category_name, -category_name. Default is +label_name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels"

        params = {
            'calculate_total': calculate_total,
            'category_id': category_id,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def central_create_label(self, category_id: int, label_name: str) -> Response:
        """Create Label.

        Args:
            category_id (int): Label category ID
            label_name (str): Label name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels"

        json_data = {
            'category_id': category_id,
            'label_name': label_name
        }

        return await self.post(url, json_data=json_data)

    async def central_get_default_labels(self, calculate_total: bool = None, sort: str = None,
                                         offset: int = 0, limit: int = 100) -> Response:
        """List Default Labels.

        Args:
            calculate_total (bool, optional): Whether to calculate total Default Labels
            sort (str, optional): Sort parameter may be one of +label_name, -label_name. Default is
                +label_name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels"

        params = {
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def central_get_label(self, label_id: int) -> Response:
        """Label details.

        Args:
            label_id (int): Label name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        return await self.get(url)

    async def central_update_label(self, label_id: int, label_name: str) -> Response:
        """Update Label.

        Args:
            label_id (int): Label ID
            label_name (str): label_name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        json_data = {
            'label_name': label_name
        }

        return await self.patch(url, json_data=json_data)

    async def central_delete_label(self, label_id: int) -> Response:
        """Delete Label.

        Args:
            label_id (int): Label ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        return await self.delete(url)

    async def central_assign_label(self, device_id: str, device_type: str, label_id: int) -> Response:
        """Associate Label to device.

        Args:
            device_id (str): Device ID. In the case IAP or SWITCH, it is device serial number
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            label_id (int): Label ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels/associations"

        json_data = {
            'device_id': device_id,
            'device_type': device_type,
            'label_id': label_id
        }

        return await self.post(url, json_data=json_data)

    async def central_unassign_label(self, device_id: str, device_type: str, label_id: int) -> Response:
        """Unassociate Label from device.

        Args:
            device_id (str): Device ID. In the case IAP or SWITCH, it is device serial number
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            label_id (int): Label ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels/associations"

        json_data = {
            'device_id': device_id,
            'device_type': device_type,
            'label_id': label_id
        }

        return await self.delete(url, json_data=json_data)

    async def central_assign_label_to_devices(self, label_id: int, device_type: str,
                                              device_ids: List[str]) -> Response:
        """Associate Label to a list of devices.

        Args:
            label_id (int): Label ID
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            device_ids (List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': device_ids
        }

        return await self.post(url, json_data=json_data)

    async def central_unassign_label_from_devices(self, label_id: int, device_type: str,
                                                  device_ids: List[str]) -> Response:
        """Unassociate a label from a list of devices.

        Args:
            label_id (int): Label ID
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            device_ids (List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': device_ids
        }

        return await self.delete(url, json_data=json_data)

    async def central_get_label_categories(self, calculate_total: bool = None, offset: int = 0,
                                           limit: int = 100) -> Response:
        """List Label Categories.

        Args:
            calculate_total (bool, optional): Whether to calculate total label categories
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels/categories"

        params = {
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def central_get_sites(self, calculate_total: bool = None, sort: str = None,
                                offset: int = 0, limit: int = 100) -> Response:
        """List Sites.

        Args:
            calculate_total (bool, optional): Whether to calculate total Site Labels
            sort (str, optional): Sort parameter may be one of +site_name, -site_name. Default is
                +site_name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"

        params = {
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def central_create_site(self, site_name: str, address: str, city: str, state: str,
                                  country: str, zipcode: str, latitude: str, longitude: str) -> Response:
        """Create Site.

        Args:
            site_name (str): Site Name
            address (str): Address
            city (str): City Name
            state (str): State Name
            country (str): Country Name
            zipcode (str): Zipcode
            latitude (str): Latitude (in the range of -90 and 90)
            longitude (str): Longitude (in the range of -180 and 180)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"

        json_data = {
            'site_name': site_name,
            'address': address,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'latitude': latitude,
            'longitude': longitude
        }

        return await self.post(url, json_data=json_data)

    async def central_get_site(self, site_id: int) -> Response:
        """Site details.

        Args:
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        return await self.get(url)

    async def central_update_site(self, site_id: int, site_name: str, address: str, city: str,
                                  state: str, country: str, zipcode: str, latitude: str,
                                  longitude: str) -> Response:
        """Update Site.

        Args:
            site_id (int): Site ID
            site_name (str): Site Name
            address (str): Address
            city (str): City Name
            state (str): State Name
            country (str): Country Name
            zipcode (str): Zipcode
            latitude (str): Latitude (in the range of -90 and 90)
            longitude (str): Longitude (in the range of -180 and 180)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        json_data = {
            'site_name': site_name,
            'address': address,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'latitude': latitude,
            'longitude': longitude
        }

        return await self.patch(url, json_data=json_data)

    async def central_delete_site(self, site_id: int) -> Response:
        """Delete Site.

        Args:
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        return await self.delete(url)

    async def central_assign_site(self, device_id: str, device_type: str, site_id: int) -> Response:
        """Associate Site to device.

        Args:
            device_id (str): Device ID. In the case IAP or SWITCH, it is device serial number
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites/associate"

        json_data = {
            'device_id': device_id,
            'device_type': device_type,
            'site_id': site_id
        }

        return await self.post(url, json_data=json_data)

    async def central_unassign_site(self, device_id: str, device_type: str, site_id: int) -> Response:
        """Unassociate Site from device.

        Args:
            device_id (str): Device ID. In the case IAP or SWITCH, it is device serial number
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites/associate"

        json_data = {
            'device_id': device_id,
            'device_type': device_type,
            'site_id': site_id
        }

        return await self.delete(url, json_data=json_data)

    async def central_assign_site_to_devices(self, site_id: int, device_type: str,
                                             device_ids: List[str]) -> Response:
        """Associate Site to a list of devices.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            device_ids (List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites/associations"

        json_data = {
            'site_id': site_id,
            'device_type': device_type,
            'device_ids': device_ids
        }

        return await self.post(url, json_data=json_data)

    async def central_unassign_site_from_devices(self, site_id: int, device_type: str,
                                                 device_ids: List[str]) -> Response:
        """Unassociate a site from a list of devices.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER  Valid Values:
                IAP, SWITCH, CONTROLLER
            device_ids (List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites/associations"

        json_data = {
            'site_id': site_id,
            'device_type': device_type,
            'device_ids': device_ids
        }

        return await self.delete(url, json_data=json_data)

    async def monitoring_get_switches(self, group: str = None, label: str = None,
                                      stack_id: str = None, status: str = None,
                                      fields: str = None, calculate_total: bool = None,
                                      show_resource_details: bool = None,
                                      calculate_client_count: bool = None,
                                      public_ip_address: str = None, site: str = None,
                                      sort: str = None, offset: int = 0, limit: int = 100) -> Response:
        """List Switches.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            stack_id (str, optional): Filter by Switch stack_id
            status (str, optional): Filter by Switch status
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                status, macaddr, model, ip_address, public_ip_address, firmware_version, labels,
                uplink_ports, site
            calculate_total (bool, optional): Whether to calculate total Switches
            show_resource_details (bool, optional): Whether to show switch uptime, max_power,
                power_consumption, temperature, fan_speed, cpu_utilization, mem_free, mem_total,
                poe_consumption.
            calculate_client_count (bool, optional): Whether to calculate client count per Switch
            public_ip_address (str, optional): Filter by public ip address
            site (str, optional): Filter by site name
            sort (str, optional): Sort parameter may be one of +serial, -serial, +name, -name,
                +macaddr, -macaddr
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switches"

        params = {
            'group': group,
            'label': label,
            'stack_id': stack_id,
            'status': status,
            'fields': fields,
            'calculate_total': calculate_total,
            'show_resource_details': show_resource_details,
            'calculate_client_count': calculate_client_count,
            'public_ip_address': public_ip_address,
            'site': site,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_vlan(self, serial: str, name: str = None, id: int = None,
                                         tagged_port: str = None, untagged_port: str = None,
                                         is_jumbo_enabled: bool = None,
                                         is_voice_enabled: bool = None,
                                         is_igmp_enabled: bool = None, type: str = None,
                                         primary_vlan_id: int = None, status: str = None,
                                         sort: str = None, calculate_total: bool = None,
                                         offset: int = 0, limit: int = 100) -> Response:
        """Get vlan info of the switch.

        Args:
            serial (str): Filter by switch serial
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
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/vlan"

        params = {
            'name': name,
            'id': id,
            'tagged_port': tagged_port,
            'untagged_port': untagged_port,
            'is_jumbo_enabled': is_jumbo_enabled,
            'is_voice_enabled': is_voice_enabled,
            'is_igmp_enabled': is_igmp_enabled,
            'type': type,
            'primary_vlan_id': primary_vlan_id,
            'status': status,
            'sort': sort,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_vlan(self, serial: str, name: str = None, id: int = None,
                                            tagged_port: str = None, untagged_port: str = None,
                                            is_jumbo_enabled: bool = None,
                                            is_voice_enabled: bool = None,
                                            is_igmp_enabled: bool = None, type: str = None,
                                            primary_vlan_id: int = None, status: str = None,
                                            sort: str = None, calculate_total: bool = None,
                                            offset: int = 0, limit: int = 100) -> Response:
        """Get vlan info for CX switch.

        Args:
            serial (str): Filter by switch serial
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
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/vlan"

        params = {
            'name': name,
            'id': id,
            'tagged_port': tagged_port,
            'untagged_port': untagged_port,
            'is_jumbo_enabled': is_jumbo_enabled,
            'is_voice_enabled': is_voice_enabled,
            'is_igmp_enabled': is_igmp_enabled,
            'type': type,
            'primary_vlan_id': primary_vlan_id,
            'status': status,
            'sort': sort,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_stack_vlan(self, stack_id: str, name: str = None,
                                               id: int = None, tagged_port: str = None,
                                               untagged_port: str = None,
                                               is_jumbo_enabled: bool = None,
                                               is_voice_enabled: bool = None,
                                               is_igmp_enabled: bool = None, type: str = None,
                                               primary_vlan_id: int = None, status: str = None,
                                               sort: str = None, calculate_total: bool = None,
                                               offset: int = 0, limit: int = 100) -> Response:
        """Get vlan info of the switch stack.

        Args:
            stack_id (str): Filter by switch stack id
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
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}/vlan"

        params = {
            'name': name,
            'id': id,
            'tagged_port': tagged_port,
            'untagged_port': untagged_port,
            'is_jumbo_enabled': is_jumbo_enabled,
            'is_voice_enabled': is_voice_enabled,
            'is_igmp_enabled': is_igmp_enabled,
            'type': type,
            'primary_vlan_id': primary_vlan_id,
            'status': status,
            'sort': sort,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_stack_vlan(self, stack_id: str, name: str = None,
                                                  id: int = None, tagged_port: str = None,
                                                  untagged_port: str = None,
                                                  is_jumbo_enabled: bool = None,
                                                  is_voice_enabled: bool = None,
                                                  is_igmp_enabled: bool = None, type: str = None,
                                                  primary_vlan_id: int = None, status: str = None,
                                                  sort: str = None, calculate_total: bool = None,
                                                  offset: int = 0, limit: int = 100) -> Response:
        """Get vlan info of the CX switch stack.

        Args:
            stack_id (str): Filter by switch stack id
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
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switch_stacks/{stack_id}/vlan"

        params = {
            'name': name,
            'id': id,
            'tagged_port': tagged_port,
            'untagged_port': untagged_port,
            'is_jumbo_enabled': is_jumbo_enabled,
            'is_voice_enabled': is_voice_enabled,
            'is_igmp_enabled': is_igmp_enabled,
            'type': type,
            'primary_vlan_id': primary_vlan_id,
            'status': status,
            'sort': sort,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_poe_detail(self, serial: str, port: str = None) -> Response:
        """Get switch port poe info.

        Args:
            serial (str): Filter by switch serial
            port (str, optional): Filter by switch port

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/poe_detail"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_poe_detail(self, serial: str, port: str) -> Response:
        """Get switch port poe info for CX switch.

        Args:
            serial (str): Filter by switch serial
            port (str): Filter by switch port

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/poe_detail"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_poe_details_for_all_ports(self, serial: str, port: str = None) -> Response:
        """Get switch poe info.

        Args:
            serial (str): Filter by switch serial
            port (str, optional): Filter by switch port

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/poe_details"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_poe_details_for_all_ports(self, serial: str,
                                                                 port: str = None) -> Response:
        """Get switch poe info for CX switch.

        Args:
            serial (str): Filter by switch serial
            port (str, optional): Filter by switch port

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/poe_details"

        params = {
            'port': port
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_vsx_detail(self, serial: str) -> Response:
        """Get switch vsx info for CX switch.

        Args:
            serial (str): Filter by switch serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/vsx"

        return await self.get(url)

    async def monitoring_get_bandwidth_usage(self, group: str = None, label: str = None,
                                             serial: str = None, stack_id: str = None,
                                             from_timestamp: int = None, to_timestamp: int = None) -> Response:
        """Switch Bandwidth Usage.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            serial (str, optional): Filter by Switch serial
            stack_id (str, optional): Filter by Switch stack_id
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switches/bandwidth_usage"

        params = {
            'serial': serial,
            'stack_id': stack_id
        }

        return await self.get(url, params=params)

    async def monitoring_get_bandwidth_usage_topn(self, group: str = None, label: str = None,
                                                  stack_id: str = None, count: int = None,
                                                  from_timestamp: int = None,
                                                  to_timestamp: int = None) -> Response:
        """Top N Switches.

        Args:
            group (str, optional): Filter by group name
            label (str, optional): Filter by Label name
            stack_id (str, optional): Filter by Switch stack_id
            count (int, optional): Required top N Switch count. Default is 5 and maximum is 100
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switches/bandwidth_usage/topn"

        params = {
            'stack_id': stack_id,
            'count': count
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch(self, serial: str) -> Response:
        """Switch Details.

        Args:
            serial (str): Serial number of switch to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}"

        return await self.get(url)

    async def monitoring_delete_switch(self, serial: str) -> Response:
        """Delete Switch.

        Args:
            serial (str): Serial number of switch to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}"

        return await self.delete(url)

    async def monitoring_get_switch_ports(self, serial: str, slot: str = None) -> Response:
        """Switch Ports Details.

        Args:
            serial (str): Serial number of switch to be queried
            slot (str, optional): Slot name of the ports to be queried {For chassis type switches
                only}.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/ports"

        params = {
            'slot': slot
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_ports(self, serial: str, slot: str = None) -> Response:
        """Get ports details for CX switch.

        Args:
            serial (str): Serial number of switch to be queried
            slot (str, optional): Slot name of the ports to be queried {For chassis type switches
                only}.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/ports"

        params = {
            'slot': slot
        }

        return await self.get(url, params=params)

    async def monitoring_get_chassis_info(self, serial: str) -> Response:
        """Switch Chassis Details.

        Args:
            serial (str): Serial number of switch to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/chassis_info"

        return await self.get(url)

    async def monitoring_get_switch_ports_bandwidth_usage(self, serial: str,
                                                          from_timestamp: int = None,
                                                          to_timestamp: int = None,
                                                          port: str = None,
                                                          show_uplink: bool = None) -> Response:
        """Switch Ports Bandwidth Usage.

        Args:
            serial (str): Serial number of switch to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            show_uplink (bool, optional): Show usage for Uplink ports alone

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/ports/bandwidth_usage"

        params = {
            'port': port,
            'show_uplink': show_uplink
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_switch_ports_bandwidth_usage(self, serial: str,
                                                             from_timestamp: int = None,
                                                             to_timestamp: int = None,
                                                             port: str = None,
                                                             show_uplink: bool = None) -> Response:
        """Ports Bandwidth Usage for CX Switch.

        Args:
            serial (str): Serial number of switch to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            show_uplink (bool, optional): Show usage for Uplink ports alone

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/ports/bandwidth_usage"

        params = {
            'port': port,
            'show_uplink': show_uplink
        }

        return await self.get(url, params=params)

    async def monitoring_get_ports_errors(self, serial: str, from_timestamp: int = None,
                                          to_timestamp: int = None, port: str = None,
                                          error: str = None) -> Response:
        """Switch Ports Errors.

        Args:
            serial (str): Serial number of switch to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            error (str, optional): Filter by 'in' or 'out' error

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/ports/errors"

        params = {
            'port': port,
            'error': error
        }

        return await self.get(url, params=params)

    async def monitoring_get_cx_ports_errors(self, serial: str, from_timestamp: int = None,
                                             to_timestamp: int = None, port: str = None,
                                             error: str = None) -> Response:
        """CX Switch Ports Errors.

        Args:
            serial (str): Serial number of switch to be queried
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            port (str, optional): Filter by Port
            error (str, optional): Filter by 'in' or 'out' error

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switches/{serial}/ports/errors"

        params = {
            'port': port,
            'error': error
        }

        return await self.get(url, params=params)

    async def monitoring_get_stack_ports(self, stack_id: str) -> Response:
        """Switch Stack Port Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}/ports"

        return await self.get(url)

    async def monitoring_get_cx_stack_ports(self, stack_id: str) -> Response:
        """CX Switch Stack Port Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switch_stacks/{stack_id}/ports"

        return await self.get(url)

    async def monitoring_get_switch_stacks(self, hostname: str = None) -> Response:
        """List Switch Stacks.

        Args:
            hostname (str, optional): Filter by stack hostname

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switch_stacks"

        params = {
            'hostname': hostname
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_stack(self, stack_id: str) -> Response:
        """Switch Stack Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.get(url)

    async def monitoring_delete_switch_stack(self, stack_id: str) -> Response:
        """Delete Switch Stack.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}"

        return await self.delete(url)

    async def monitoring_get_events(self, group: str = None, swarm_id: str = None,
                                    label: str = None, from_timestamp: int = None,
                                    to_timestamp: int = None, serial: str = None,
                                    event_type: str = None, event_number: int = None,
                                    level: str = None, event_description: str = None,
                                    event_category: str = None, macaddr: str = None,
                                    fields: str = None, calculate_total: bool = None,
                                    offset: int = 0, limit: int = 100) -> Response:
        """List Events.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            serial (str, optional): Filter by switch serial number
            event_type (str, optional): Filter by event type
            event_number (int, optional): Filter by event number
            level (str, optional): Filter by event level
            event_description (str, optional): Filter by event description
            event_category (str, optional): Filter by event category
            macaddr (str, optional): Filter by client MAC address
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                number, level
            calculate_total (bool, optional): Whether to calculate total events
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/events"

        params = {
            'serial': serial,
            'event_type': event_type,
            'event_number': event_number,
            'level': level,
            'event_description': event_description,
            'event_category': event_category,
            'macaddr': macaddr,
            'fields': fields,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def msp_get_customers(self, customer_name: str = None, offset: int = 0,
                                limit: int = 100) -> Response:
        """Get list of customers under the MSP account based on limit and offset.

        Args:
            customer_name (str, optional): Filter on Customer Name
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/customers"

        params = {
            'customer_name': customer_name,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def msp_create_customer(self, customer_name: str, name: str, description: str,
                                  lock_msp_ssids: bool) -> Response:
        """Create a new customer.

        Args:
            customer_name (str): Customer Name (Max 70 chars)
            name (str): Group Name
            description (str): Customer Description (Max length 32 chars)
            lock_msp_ssids (bool): enable/disable lock ssid

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/customers"

        json_data = {
            'customer_name': customer_name,
            'name': name,
            'description': description,
            'lock_msp_ssids': lock_msp_ssids
        }

        return await self.post(url, json_data=json_data)

    async def msp_get_customer(self, customer_id: str) -> Response:
        """Get details of customer.

        Args:
            customer_id (str): Filter on Customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}"

        return await self.get(url)

    async def msp_edit_customer(self, customer_id: str, customer_name: str, name: str,
                                description: str, lock_msp_ssids: bool) -> Response:
        """Update a customer.

        Args:
            customer_id (str): Filter on Customer ID
            customer_name (str): Customer Name (Max 70 chars)
            name (str): Group Name
            description (str): Customer Description (Max length 32 chars)
            lock_msp_ssids (bool): enable/disable lock ssid

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}"

        json_data = {
            'customer_name': customer_name,
            'name': name,
            'description': description,
            'lock_msp_ssids': lock_msp_ssids
        }

        return await self.put(url, json_data=json_data)

    async def msp_delete_customer(self, customer_id: str) -> Response:
        """Delete a customer.

        Args:
            customer_id (str): Filter on Customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}"

        return await self.delete(url)

    async def msp_get_resource(self) -> Response:
        """Get the resource under the MSP.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/resource"

        return await self.get(url)

    async def msp_edit_resource(self, contact_link: str, logo_image_url: str, mail_address: str,
                                primary_color: str, product_name: str, provider_name: str,
                                sender_email_address: str, service_link: str, terms_link: str,
                                image_blob: str, skin_info: str) -> Response:
        """Edit an existing resource for the MSP.

        Args:
            contact_link (str): Contact Link
            logo_image_url (str): URL of the logo
            mail_address (str): Mailing address
            primary_color (str): Primary color
            product_name (str): Name of the product (Max 32 chars)
            provider_name (str): Name of the provider
            sender_email_address (str): Sender's Email address
            service_link (str): Service Link URL
            terms_link (str): Terms Link URL
            image_blob (str): Image details
            skin_info (str): Skin details

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/resource"

        json_data = {
            'contact_link': contact_link,
            'logo_image_url': logo_image_url,
            'mail_address': mail_address,
            'primary_color': primary_color,
            'product_name': product_name,
            'provider_name': provider_name,
            'sender_email_address': sender_email_address,
            'service_link': service_link,
            'terms_link': terms_link,
            'image_blob': image_blob,
            'skin_info': skin_info
        }

        return await self.put(url, json_data=json_data)

    async def msp_get_customer_devices(self, customer_id: str, device_type: str = None,
                                       offset: int = 0, limit: int = 100) -> Response:
        """Get list of devices and licenses under the Customer account based on limit and offset.

        Args:
            customer_id (str): Filter on Customer ID
            device_type (str, optional): Filter on device_type to get list of devices
                iap                                            switch
                all_controller  Valid Values: iap, switch, all_controller
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}/devices"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def msp_move_devices_to_customer(self, customer_id: str, devices: list, group: str) -> Response:
        """Move a device to an end-customer.

        Args:
            customer_id (str): Filter on Customer ID
            devices (list): array of device details
            group (str): group name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}/devices"

        json_data = {
            'devices': devices,
            'group': group
        }

        return await self.put(url, json_data=json_data)

    async def msp_get_devices(self, device_allocation_status: int = 0, device_type: str = None,
                              customer_name: str = None, offset: int = 0, limit: int = 100) -> Response:
        """Get list of devices and licenses under the MSP account based on limit and offset.

        Args:
            device_allocation_status (int, optional): Filter on device_allocation_status to get list
                of devices                                                         0-All
                1-Allocated                                                         2-Available
                Valid Values: 0 - 2
            device_type (str, optional): Filter on device_type to get list of devices
                iap
                switch
                all_controller  Valid Values: iap, switch, all_controller
            customer_name (str, optional): Filter on Customer Name
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/devices"

        params = {
            'device_allocation_status': device_allocation_status
        }

        return await self.get(url, params=params)

    async def branchhealth_get_labels_(self, name: str = None, column: int = None,
                                       order: int = None,
                                       Site_properties_used_with_thresholds: str = None,
                                       offset: int = 0, limit: int = 100) -> Response:
        """Get data for all labels.

        Args:
            name (str, optional): site / label name or part of its name
            column (int, optional): Column to sort on
            order (int, optional): Sort order:                                     * asc -
                Ascending, from A to Z.                                     * desc - Descending,
                from Z to A.                                      Valid Values: asc, desc
            Site_properties_used_with_thresholds (str, optional): Site thresholds
                * All properties of a site can be used as filter parameters with a threshold
                * The range filters can be combined with the column names with "\__"  # noqa
                * For eg. /site?device_down\__gt=0 - Lists all sites that have more than 1 device in  # noqa
                down state                                                                    * For
                eg. /site?wan_uplinks_down\__lt=1 - Lists all sites that have less than 1 wan in  # noqa
                down state                                                                    * For
                eg. /site?device_up__gt=1&device_up\__lt=10 - Lists all sites that have 1-10 devices  # noqa
                in up state
                Valid Values: gt  (Greater than), lt  (Less than), gte (Greater than or equal to),
                lte (Less than or equal to)
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/branchhealth/v1/label"

        params = {
            'name': name,
            'column': column,
            'order': order,
            'Site_properties_used_with_thresholds': Site_properties_used_with_thresholds,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def branchhealth_get_sites_(self, name: str = None, column: int = None,
                                      order: int = None,
                                      Site_properties_used_with_thresholds: str = None,
                                      offset: int = 0, limit: int = 100) -> Response:
        """Get data for all sites.

        Args:
            name (str, optional): site / label name or part of its name
            column (int, optional): Column to sort on
            order (int, optional): Sort order:
                * asc - Ascending, from A to Z.
                * desc - Descending, from Z to A.
                Valid Values: asc, desc
            Site_properties_used_with_thresholds (str, optional): Site thresholds
                * All properties of a site can be used as filter parameters with a threshold
                * The range filters can be combined with the column names with "\__"  # noqa
                * For eg. /site?device_down\__gt=0 - Lists all sites that have more than 1 device in  # noqa
                down state
                * For eg. /site?wan_uplinks_down\__lt=1 - Lists all sites that have less than 1 wan  # noqa
                in down state
                * For eg. /site?device_up__gt=1&device_up\__lt=10 - Lists all sites that have 1-10  # noqa
                devices in up state
                Valid Values: gt  (Greater than), lt  (Less than), gte (Greater than or equal to),
                lte (Less than or equal to)
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/branchhealth/v1/site"

        return await self.get(url)

    async def central_get_types_(self, calculate_total: bool = None, offset: int = 0,
                                 limit: int = 100) -> Response:
        """List Types.

        Args:
            calculate_total (bool, optional): Whether to count total items in the response
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/types"

        params = {
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def central_get_settings_(self, search: str = None, sort: str = '-created_ts',
                                    offset: int = 0, limit: int = 100) -> Response:
        """List Settings.

        Args:
            search (str, optional): term used to search in name, category of the alert
            sort (str, optional): Sort parameter may be one of +created_ts, -created_ts, Default is
                '-created_ts'  Valid Values: -created_ts, +created_ts
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/settings"

        params = {
            'search': search,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def central_add_setting_(self, type: str, rules: list, active: bool) -> Response:
        """Add settings.

        Args:
            type (str): Notification Type name
            rules (list): rules
            active (bool): Active

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/settings"

        json_data = {
            'type': type,
            'rules': rules,
            'active': active
        }

        return await self.post(url, json_data=json_data)

    async def central_delete_setting_(self, settings_id: str) -> Response:
        """Delete Settings.

        Args:
            settings_id (str): id of the settings

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/notifications/settings/{settings_id}"

        return await self.delete(url)

    async def central_update_setting_(self, settings_id: str, type: str, rules: list,
                                      active: bool) -> Response:
        """Update settings details.

        Args:
            settings_id (str): id of the settings
            type (str): Notification Type name
            rules (list): rules
            active (bool): Active

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/notifications/settings/{settings_id}"

        json_data = {
            'type': type,
            'rules': rules,
            'active': active
        }

        return await self.put(url, json_data=json_data)

    async def central_get_count_by_severity_(self, customer_id: str = None, group: str = None,
                                             label: str = None, serial: str = None,
                                             site: str = None, from_timestamp: int = None,
                                             to_timestamp: int = None, ack: bool = None) -> Response:
        """Get notifications count by severity.

        Args:
            customer_id (str, optional): MSP user can filter notifications based on customer id
            group (str, optional): Used to filter the notification types based on group name
            label (str, optional): Used to filter the notification types based on Label name
            serial (str, optional): Used to filter the result based on serial number of the device
            site (str, optional): Used to filter the notification types based on Site name
            from_timestamp (int, optional): 1)start of duration within which alerts are raised
                2)described using Unix Epoch time in seconds
            to_timestamp (int, optional): 1)end of duration within which alerts are raised
                2)described using Unix Epoch time in seconds
            ack (bool, optional): Filter acknowledged or unacknowledged notifications. When query
                parameter is not specified, both acknowledged and unacknowledged notifications are
                included

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/count_by_severity"

        params = {
            'customer_id': customer_id,
            'group': group,
            'label': label,
            'serial': serial,
            'site': site,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ack': ack
        }

        return await self.get(url, params=params)

    async def central_get_notifications_(self, customer_id: str = None, group: str = None,
                                         label: str = None, serial: str = None, site: str = None,
                                         from_timestamp: int = None, to_timestamp: int = None,
                                         severity: str = None, type: str = None,
                                         search: str = None, calculate_total: bool = None,
                                         ack: bool = None, fields: str = None, offset: int = 0,
                                         limit: int = 100) -> Response:
        """List Notifications.

        Args:
            customer_id (str, optional): MSP user can filter notifications based on customer id
            group (str, optional): Used to filter the notification types based on group name
            label (str, optional): Used to filter the notification types based on Label name
            serial (str, optional): Used to filter the result based on serial number of the device
            site (str, optional): Used to filter the notification types based on Site name
            from_timestamp (int, optional): 1)start of duration within which alerts are raised
                2)described using Unix Epoch time in seconds
            to_timestamp (int, optional): 1)end of duration within which alerts are raised
                2)described using Unix Epoch time in seconds
            severity (str, optional): Used to filter the notification types based on severity
            type (str, optional): Used to filter the notification types based on notification type
                name
            search (str, optional): term used to search in name, category of the alert
            calculate_total (bool, optional): Whether to count total items in the response
            ack (bool, optional): Filter acknowledged or unacknowledged notifications. When query
                parameter is not specified, both acknowledged and unacknowledged notifications are
                included
            fields (str, optional): Comma separated list of fields to be returned
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"

        params = {
            'customer_id': customer_id,
            'severity': severity,
            'type': type,
            'fields': fields
        }

        return await self.get(url, params=params)

    async def central_acknowledge_notifications(self, NoName: List[str] = None) -> Response:
        """Acknowledge Notifications by ID List / All.

        Args:
            NoName (List[str], optional): Acknowledge notifications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"

        return await self.post(url)

    async def central_acknowledge_notification(self, notification_id: str, acknowledged: bool) -> Response:
        """Acknowledge Notification.

        Args:
            notification_id (str): Notification ID
            acknowledged (bool): Notification acknowledgement status. Currently acknowledge is only
                supported and unacknowledge is not supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/notifications/{notification_id}"

        json_data = {
            'acknowledged': acknowledged
        }

        return await self.patch(url, json_data=json_data)

    async def ofc_enable_wildcard_flow(self, enable: bool, serial_id: str) -> Response:
        """Enable/Disable the Syslog App.

        Args:
            enable (bool): /True or /False
            serial_id (str): serial_id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ofcapi/v1/syslog/flow"

        json_data = {
            'enable': enable,
            'serial_id': serial_id
        }

        return await self.post(url, json_data=json_data)

    async def ofc_enable_wildcard_flow_list(self, enable: bool,
                                            serial_id_metadata: Union[Path, str]) -> Response:
        """Enable Syslog App on a list of given device SerialIDs.

        Args:
            enable (bool): True or False
            serial_id_metadata (Union[Path, str]): File with SerialID metadata

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ofcapi/v1/syslog/flows/{enable}"
        serial_id_metadata = serial_id_metadata if isinstance(serial_id_metadata, Path) else Path(str(serial_id_metadata))

        return await self.post(url)

    async def ofc_check_status_list(self, serial_ids: Union[Path, str]) -> Response:
        """Check Status of Syslog App for given SerialIDs.

        Args:
            serial_ids (Union[Path, str]): File with SerialIDs

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ofcapi/v1/syslog/flows/status/device_list"
        serial_ids = serial_ids if isinstance(serial_ids, Path) else Path(str(serial_ids))

        return await self.post(url)

    async def ofc_check_status(self, serial_id: str) -> Response:
        """Check Status of Enabled Flow SerialID.

        Args:
            serial_id (str): Device Serial ID on which the Status is checked

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ofcapi/v1/syslog/flow/status/{serial_id}"

        return await self.get(url)

    async def platform_get_devices(self, sku_type: str, offset: int = 0, limit: int = 100) -> Response:
        """Get devices from device inventory.

        Args:
            sku_type (str): IAP/MAS. Check /platform/orders/v1/skus?sku_type=all  API response to
                see the list of sku_type
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object

        Raw API Response Example:
            [
                {
                    "devices": [
                        {
                            "aruba_part_no": "6200",
                            "customer_id": "abc123",
                            "customer_name": "acme",
                            "device_type": "switch",
                            "imei": "",
                            "macaddr": "AA:BB...",
                            "model": "JL728A",
                            "serial": "SGABC1234",
                            "services": [
                                "foundation_switch_6200"
                            ],
                            "tier_type": "foundation"
                        },
                    ],
                    "total": 6
                }
            ]
        """
        url = "/platform/device_inventory/v1/devices"

        params = {
            'sku_type': sku_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_add_device(self, mac_address: str = None, serial_num: str = None, part_num: str = None, device_list: List[Dict[str, str]] = None) -> Response:
        """Add device using Mac and Serial number.

        Args:
            NoName (list, optional): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        if serial_num:
            if not mac_address:
                raise ValueError("mac_address is required")
            else:
                json_data = [
                    {
                        "mac": "<string>",
                        "serial": "<string>",
                    }
                ]
                if part_num:
                    json_data[0]["partNumber"] = part_num
        elif device_list:
            if not isinstance(device_list, list) and not all(isinstance(d, dict) for d in device_list):
                raise ValueError("When using device_list to batch add devices, they should be provided as a list of dicts")

            _keys = {
                "mac_address": "mac",
                "serial_num": "serial",
                "part_num": "partNumber"
            }

            json_data = [{_keys.get(k, k): v for k, v in d.items()} for d in device_list]

        return await self.post(url)

    async def platform_delete_device(self, serial_nums: Union[List[str], str]) -> Response:
        """Delete devices using Serial number.

        VALID FOR Central On Prem Only

        Args:
            serial_nums (List[str]|str): serial_num(s) of devices to delete.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        serial_nums = [serial_nums] if not isinstance(serial_nums, list) else serial_nums

        json_data = [
            {"serial": s} for s in serial_nums
        ]

        return await self.delete(url, json_data=json_data)

    async def platform_get_devices_stats(self, sku_type: str, service_type: str) -> Response:
        """Get devices stats.

        Args:
            sku_type (str): IAP/MAS. Check /platform/orders/v1/skus?sku_type=all  API response to
                see the list of sku_type
            service_type (str): Name of the service: dm/pa etc. .Check platform/orders/v1/services
                API response to know the lis of services

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/stats"

        params = {
            'sku_type': sku_type,
            'service_type': service_type
        }

        return await self.get(url, params=params)

    async def platform_verify_device_addition(self, NoName: list = None) -> Response:
        """Verify device addition.

        Args:
            NoName (list, optional): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/verify"

        return await self.post(url)

    async def platform_refresh_inventory_status(self) -> Response:
        """Get status of refresh job.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/refresh"

        return await self.get(url)

    async def platform_refresh_inventory(self) -> Response:
        """Schedule a job to refresh the device inventory.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/refresh"

        return await self.post(url)

    async def platform_get_device(self, serial: str) -> Response:
        """Get device from device inventory.

        Args:
            serial (str): Query device using serial number (API is only supported for private cloud
                Central environment)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/device_inventory/v1/device/{serial}"

        return await self.get(url)

    async def platform_get_msp_customer_devices(self, customer_id: str, device_type: str = None,
                                                offset: int = 0, limit: int = 100) -> Response:
        """A filterable paginated response of a list of devices and licenses under the customer
        account based on the provided limit and offset parameters.

        Args:
            customer_id (str): To get devices of specified customer
            device_type (str, optional): Filter on device_type to get list of devices
                iap                                             switch
                all_controller                                             cap
                boc
            offset (int, optional): Pagination Start Index Defaults to 0.
            limit (int, optional): Pagination End Index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/device_inventory/v1/msp/{customer_id}/devices"

        params = {
            'device_type': device_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_assign_device_to_customer(self, customer_id: str, devices: list) -> Response:
        """assign the device to the end-customer.

        Args:
            customer_id (str): To assign device to specified customer
            devices (list): List of devices with basic details of device like serial address and mac
                address

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/device_inventory/v1/msp/{customer_id}/devices"

        json_data = {
            'devices': devices
        }

        return await self.put(url, json_data=json_data)

    async def platform_get_msp_devices(self, device_type: str = None, customer_name: str = None,
                                       device_allocation_status: int = 0, offset: int = 0,
                                       limit: int = 100) -> Response:
        """A filterable paginated response of a list of devices and licenses under the MSP account
        based on the provided limit and offset parameters.

        Args:
            device_type (str, optional): Filter on device_type to get list of devices
                iap                                             switch
                all_controller                                             cap
                boc
            customer_name (str, optional): Filter on Customer Name
            device_allocation_status (int, optional): Filter on device_allocation_status to get list
                of devices                                                       ALL : 0
                ALLOCATED = 1                                                       AVAILABLE = 2
                Valid Values: 0 - 2
            offset (int, optional): Pagination Start Index Defaults to 0.
            limit (int, optional): Pagination End Index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/msp/devices"

        params = {
            'device_type': device_type,
            'customer_name': customer_name,
            'device_allocation_status': device_allocation_status,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_get_user_subscriptions(self, license_type: str = None, offset: int = 0,
                                              limit: int = 100) -> Response:
        """Get user subscription keys.

        Args:
            license_type (str, optional): Supports Basic, Service Token and Multi Tier licensing
                types as well
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of subscriptions to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions"

        params = {
            'license_type': license_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_get_subscription_stats(self, license_type: str = 'all',
                                              service: str = None) -> Response:
        """Get subscription stats.

        Args:
            license_type (str, optional): Supports basic/special/all.
                special - will fetch the statistics of special central services like presence
                analytics(pa), ucc, clarity etc                                           basic -
                will fetch the statistics of device management service licenses.
                all - will fetch both of these license types.
                Also supports multi tier license types such foundation_ap, advanced_switch_6300,
                foundation_70XX etc.
            service (str, optional): Service type: pa/pa,clarity,foundation_ap,
                advanced_switch_6300, foundation_70XX  etc

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/stats"

        params = {
            'license_type': license_type,
            'service': service
        }

        return await self.get(url, params=params)

    async def platform_gw_license_available(self, service: str) -> Response:
        """Get services and corresponding license token availability status.

        Args:
            service (str): specific service
                name(dm/pa/foundation_ap/advanced_switch6100/foundation_wlan_gw...). Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/licensing/v1/autolicensing/services/{service}/status"

        return await self.get(url)

    async def platform_gw_get_autolicense_settings(self) -> Response:
        """Get the services which are auto enabled.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/customer/settings/autolicense"

        return await self.get(url)

    async def platform_gw_enable_auto_licensing_settings(self, services: List[str]) -> Response:
        """Standalone Customer API:- Assign licenses to all devices and enable auto licensing for
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
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_gw_disable_auto_licensing_settings(self, services: List[str]) -> Response:
        """Standalone Customer API:- Disable auto licensing for given services.

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
            'services': services
        }

        return await self.delete(url, json_data=json_data)

    async def platform_gw_msp_get_autolicense_settings(self, customer_id: str) -> Response:
        """Get auto enabled services for msp or tenant customer.

        Args:
            customer_id (str): Customer id of msp or tenant.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/msp/customer/settings/autolicense"

        params = {
            'customer_id': customer_id
        }

        return await self.get(url, params=params)

    async def platform_gw_msp_enable_auto_licensing_settings(self, include_customers: List[str],
                                                             exclude_customers: List[str],
                                                             services: List[str]) -> Response:
        """MSP API:- Enable auto license settings and assign services to all devices owned by tenant
        customers.

        Args:
            include_customers (List[str]): Customer ids to be included for licensing/un-licensing.
            exclude_customers (List[str]): Customer ids to be excluded for licensing/un-licensing.
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/msp/customer/settings/autolicense"

        json_data = {
            'include_customers': include_customers,
            'exclude_customers': exclude_customers,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_gw_msp_disable_auto_licensing_settings(self, include_customers: List[str],
                                                              exclude_customers: List[str],
                                                              services: List[str]) -> Response:
        """MSP API:- Disable auto license settings at msp and its tenant level for given services.

        Args:
            include_customers (List[str]): Customer ids to be included for licensing/un-licensing.
            exclude_customers (List[str]): Customer ids to be excluded for licensing/un-licensing.
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/msp/customer/settings/autolicense"

        json_data = {
            'include_customers': include_customers,
            'exclude_customers': exclude_customers,
            'services': services
        }

        return await self.delete(url, json_data=json_data)

    async def platform_gw_assign_licenses(self, serials: List[str], services: List[str]) -> Response:
        """Assign subscription to a device.

        Args:
            serials (List[str]): List of serial number of device.
            services (List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/assign"

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_gw_unassign_licenses(self, serials: List[str], services: List[str]) -> Response:
        """Unassign subscription to a device.

        Args:
            serials (List[str]): List of serial number of device.
            services (List[str]): List of service names. Call services/config API to get the list of
                valid service names.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/unassign"

        json_data = {
            'serials': serials,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_gw_get_customer_enabled_services(self) -> Response:
        """Get enabled services for customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/enabled"

        return await self.get(url)

    async def platform_get_services_config(self, service_category: str = None,
                                           device_type: str = None) -> Response:
        """Get services licensing config.

        Args:
            service_category (str, optional): Service category - dm/network
            device_type (str, optional): Device Type - iap/cap/switch/boc/controller

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/config"

        params = {
            'service_category': service_category,
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def platform_assign_subscription_all_devices(self, services: List[str]) -> Response:
        """Standalone customer API:- Assign licenses to all devices.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/devices/all"

        json_data = {
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_unassign_subscription_all_devices(self, services: List[str]) -> Response:
        """Standalone customer API:- Un-assign licenses to all devices for given services.

        Args:
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/subscriptions/devices/all"

        json_data = {
            'services': services
        }

        return await self.delete(url, json_data=json_data)

    async def platform_msp_assign_subscription_all_devices(self, include_customers: List[str],
                                                           exclude_customers: List[str],
                                                           services: List[str]) -> Response:
        """MSP API:- Assign licenses to all the devices owned by tenant customers.

        Args:
            include_customers (List[str]): Customer ids to be included for licensing/un-licensing.
            exclude_customers (List[str]): Customer ids to be excluded for licensing/un-licensing.
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/msp/subscriptions/devices/all"

        json_data = {
            'include_customers': include_customers,
            'exclude_customers': exclude_customers,
            'services': services
        }

        return await self.post(url, json_data=json_data)

    async def platform_msp_unassign_subscription_all_devices(self, include_customers: List[str],
                                                             exclude_customers: List[str],
                                                             services: List[str]) -> Response:
        """MSP API:- Remove service licenses to all the devices owned by tenants and MSP.

        Args:
            include_customers (List[str]): Customer ids to be included for licensing/un-licensing.
            exclude_customers (List[str]): Customer ids to be excluded for licensing/un-licensing.
            services (List[str]): list of services e.g. ['pa', 'ucc', foundation_ap,
                advanced_switch_6200, foundation_70XX etc ...]. Check
                /platform/licensing/v1/services/config API response to know the list of supported
                services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/msp/subscriptions/devices/all"

        json_data = {
            'include_customers': include_customers,
            'exclude_customers': exclude_customers,
            'services': services
        }

        return await self.delete(url, json_data=json_data)

    async def presence_set_v3_thresholds(self, dwelltime: int, rssi: int, passerby_rssi: int,
                                         site_id: int, select_all: bool = False) -> Response:
        """It configures RSSI threshold, dwelltime threshold for visitor & RSSI threshold for
        passerby.

        Args:
            dwelltime (int): visitor dwelltime in minutes
            rssi (int): visitor rssi between -100 dBm to 0 dBm
            passerby_rssi (int): passerby rssi between -100 dBm to 0 dBm
            site_id (int): site id
            select_all (bool, optional): select all sites and apply custom threshold configuration.
                It's default value is false  Valid Values: False - True

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/config/thresholds"

        params = {
            'select_all': select_all
        }

        json_data = {
            'dwelltime': dwelltime,
            'rssi': rssi,
            'passerby_rssi': passerby_rssi,
            'site_id': site_id
        }

        return await self.post(url, json_data=json_data, params=params)

    async def presence_get_v3_thresholds(self, site_id: str = None) -> Response:
        """It retrieves RSSI threshold for passerby conversion, RSSI threshold for visitor
        conversion & dwelltime threshold for passerby to visitor conversion.

        Args:
            site_id (str, optional): site id of the Store/Campus/Building/floor

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/config/thresholds"

        params = {
            'site_id': site_id
        }

        return await self.get(url, params=params)

    async def presence_get_pa_config_data(self, sort: str = None, search: str = None,
                                          site_id: str = None, offset: int = 0, limit: int = 100) -> Response:
        """It retrieves visitor RSSI threshold, passerby RSSI threshold, dwell time threshold,
        access points and site name for site level configuration.

        Args:
            sort (str, optional): Sort parameter may be one of asc, desc. Default is asc  Valid
                Values: asc, desc
            search (str, optional): If provided, the labels containing 'search' string will be
                listed.
            site_id (str, optional): site id of the label/store/Campus/Building/floor
            offset (int, optional): Pagination offset, default is 0 Defaults to 0.
            limit (int, optional): Pagination limit. Default is 10 and max is 50 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/sites/config"

        params = {
            'sort': sort,
            'search': search,
            'site_id': site_id,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def presence_get_visitors_status_info(self, start_time: int, end_time: int,
                                                tag_id: str = None) -> Response:
        """Get details of connected and non connected visitors.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            tag_id (str, optional): id of label/site/Campus/Building/floor

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/visitor_status"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id
        }

        return await self.get(url, params=params)

    async def presence_get_loyalty_visit_frequency(self, start_time: int, end_time: int,
                                                   tag_id: str = None) -> Response:
        """Get loyalty visitors frequency.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            tag_id (str, optional): id of label/site/Campus/Building/floor

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/visit_frequency"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id
        }

        return await self.get(url, params=params)

    async def presence_get_dashboard_v3_percentile_datapoints(self, category: str,
                                                              start_time: int, end_time: int,
                                                              tag_id: str = None,
                                                              sample_frequency: str = None) -> Response:
        """Get presence analytics trends.

        Args:
            category (str): indicator field (passerby, visitor, dwelltime)
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            tag_id (str, optional): id of label/site/Campus/Building/floor
            sample_frequency (str, optional): frequency of the sampling  Valid Values: hourly,
                daily, weekly

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/analytics/trends/passerby_visitors"

        params = {
            'category': category,
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id,
            'sample_frequency': sample_frequency
        }

        return await self.get(url, params=params)

    async def presence_get_v3_loyalty_trends(self, start_time: int, end_time: int,
                                             tag_id: str = None, sample_frequency: str = None) -> Response:
        """Get presence analytics trends.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            tag_id (str, optional): id of label/site/Campus/Building/floor
            sample_frequency (str, optional): frequency of the sampling  Valid Values: hourly,
                daily, weekly

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/analytics/trends/loyal_visitors"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'tag_id': tag_id,
            'sample_frequency': sample_frequency
        }

        return await self.get(url, params=params)

    async def presence_enable_or_disable_pa_license(self, customer_level: bool,
                                                    enable_device_list: List[str],
                                                    disable_device_list: List[str]) -> Response:
        """Enable or disable PA license.

        Args:
            customer_level (bool): one of the values true or false (when customer level key is
                passed, other keys should not be passed)
            enable_device_list (List[str]): enable_device_list
            disable_device_list (List[str]): disable_device_list

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/license"

        json_data = {
            'customer_level': customer_level,
            'enable_device_list': enable_device_list,
            'disable_device_list': disable_device_list
        }

        return await self.post(url, json_data=json_data)

    async def presence_get_pa_license_status(self) -> Response:
        """Customer level device license status.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/license"

        return await self.get(url)

    async def presence_get_device_license_status_per_site(self, tag_id: str) -> Response:
        """List of devices per site with their pa license status.

        Args:
            tag_id (str): site id of the label/store/Campus/Building/floor.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/sites/devicelicense"

        params = {
            'tag_id': tag_id
        }

        return await self.get(url, params=params)

    async def presence_get_site_wise_data(self, start_time: int, end_time: int,
                                          search: str = None, sort: str = None,
                                          site_id: str = None, offset: int = 0, limit: int = 100) -> Response:
        """Get presence aggregate values for list of sites.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            search (str, optional): If provided, the labels containing, 'search' string will be
                listed.
            sort (str, optional): Sort parameter may be one of asc, desc. Default is asc  Valid
                Values: asc, desc
            site_id (str, optional): site id of the label/store/Campus/Building/floor
            offset (int, optional): Pagination offset, default is 0 Defaults to 0.
            limit (int, optional): Pagination limit. Default is 10 and max is 50 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/insights/sites/aggregates"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'search': search,
            'sort': sort,
            'site_id': site_id,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_rds_v1_rogue_aps(self, group: List[str] = None, label: List[str] = None,
                                   site: List[str] = None, start: int = None, end: int = None,
                                   swarm_id: str = None, from_timestamp: int = None,
                                   to_timestamp: int = None, offset: int = 0, limit: int = 100) -> Response:
        """List Rogue APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/rogue_aps"

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_rds_v1_interfering_aps(self, group: List[str] = None, label: List[str] = None,
                                         site: List[str] = None, start: int = None,
                                         end: int = None, swarm_id: str = None,
                                         from_timestamp: int = None, to_timestamp: int = None,
                                         offset: int = 0, limit: int = 100) -> Response:
        """List Interfering APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/interfering_aps"

        return await self.get(url)

    async def get_rds_v1_suspect_aps(self, group: List[str] = None, label: List[str] = None,
                                     site: List[str] = None, start: int = None, end: int = None,
                                     swarm_id: str = None, from_timestamp: int = None,
                                     to_timestamp: int = None, offset: int = 0, limit: int = 100) -> Response:
        """List suspect APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/suspect_aps"

        return await self.get(url)

    async def get_rds_v1_neighbor_aps(self, group: List[str] = None, label: List[str] = None,
                                      site: List[str] = None, start: int = None, end: int = None,
                                      swarm_id: str = None, from_timestamp: int = None,
                                      to_timestamp: int = None, offset: int = 0, limit: int = 100) -> Response:
        """List neighbor APs.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/neighbor_aps"

        return await self.get(url)

    async def rds_get_infrastructure_attacks(self, group: List[str] = None,
                                             label: List[str] = None, site: List[str] = None,
                                             start: int = None, end: int = None,
                                             calculate_total: bool = None, sort: str = '-ts',
                                             swarm_id: str = None, from_timestamp: int = None,
                                             to_timestamp: int = None, offset: int = 0,
                                             limit: int = 100) -> Response:
        """List Infrastructure Attacks.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            calculate_total (bool, optional): Whether to calculate total infrastructure attacks
            sort (str, optional): Sort parameter -ts(sort based on the timestamps in descending),
                +ts(sort based on timestamps ascending), -macaddr(sort based on station mac
                descending) and +macaddr(sort based station mac ascending)  Valid Values: -ts, +ts,
                -macaddr, +macaddr
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/wids/infrastructure_attacks"

        params = {
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def rds_get_client_attacks(self, group: List[str] = None, label: List[str] = None,
                                     site: List[str] = None, start: int = None, end: int = None,
                                     calculate_total: bool = None, sort: str = '-ts',
                                     swarm_id: str = None, from_timestamp: int = None,
                                     to_timestamp: int = None, offset: int = 0, limit: int = 100) -> Response:
        """List Client Attacks.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            calculate_total (bool, optional): Whether to calculate total client attacks
            sort (str, optional): Sort parameter -ts(sort based on the timestamps in descending),
                +ts(sort based on timestamps ascending), -macaddr(sort based on station mac
                descending) and +macaddr(sort based station mac ascending)  Valid Values: -ts, +ts,
                -macaddr, +macaddr
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/wids/client_attacks"

        params = {
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def rds_get_wids_events(self, group: List[str] = None, label: List[str] = None,
                                  site: List[str] = None, start: int = None, end: int = None,
                                  sort: str = '-ts', swarm_id: str = None,
                                  from_timestamp: int = None, to_timestamp: int = None,
                                  offset: int = 0, limit: int = 100) -> Response:
        """WIDS Events.

        Args:
            group (List[str], optional): List of group names
            label (List[str], optional): List of label names
            site (List[str], optional): List of site names
            start (int, optional): Need information from this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp minus 3 hours
            end (int, optional): Need information to this timestamp. Timestamp is epoch in
                milliseconds. Default is current timestamp
            sort (str, optional): Sort parameter -ts(sort based on the timestamps in descending),
                +ts(sort based on timestamps ascending), -macaddr(sort based on station mac
                descending) and +macaddr(sort based station mac ascending)  Valid Values: -ts, +ts,
                -macaddr, +macaddr
            swarm_id (str, optional): Filter by Swarm ID
            from_timestamp (int, optional): This parameter supercedes start parameter. Need
                information from this timestamp. Timestamp is epoch in seconds. Default is current
                UTC timestamp minus 3 hours
            to_timestamp (int, optional): This parameter supercedes end parameter. Need information
                to this timestamp. Timestamp is epoch in seconds. Default is current UTC timestamp
            offset (int, optional): Pagination offset (default = 0) Defaults to 0.
            limit (int, optional): pagination size (default = 100) Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/wids/events"

        return await self.get(url)

    async def oauth2_xxx(self, client_id: str, client_secret: str,
                         refresh_token: str) -> Response:
        """Refresh API token.

        Args:
            client_id (str): Client ID
            client_secret (str): Client Secret
            refresh_token (str): Refresh Token

        Returns:
            Response: CentralAPI Response object
        """
        url = "/oauth2/token"

        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        return await self.post(url, params=params)

    async def reports_scheduled_reports(self, cid: str, start_time: int = None,
                                        end_time: int = None) -> Response:
        """Scheduled Reports.

        Args:
            cid (str): Customer ID of the tenant
            start_time (int, optional): Start time in epoch. Default is start time of next day
                timestamp. Valid date range can vary upto next week
            end_time (int, optional): End time in epoch. Default is end time of  next day timestamp.
                Valid date range can vary upto next week

        Returns:
            Response: CentralAPI Response object
        """
        url = f"//reports/api/v1/{cid}/scheduled"

        params = {
            'start_time': start_time,
            'end_time': end_time
        }

        return await self.get(url, params=params)

    async def reports_generated_reports(self, cid: str, start_time: int = None,
                                        end_time: int = None) -> Response:
        """Generated Reports.

        Args:
            cid (str): Customer ID of the tenant
            start_time (int, optional): Start timestamp in epoch. Default is start timestamp of last
                day. Valid date range can vary upto last month
            end_time (int, optional): End timestamp in epoch. Default is end timestamp of last day.
                Valid date range can vary upto last month

        Returns:
            Response: CentralAPI Response object
        """
        url = f"//reports/api/v1/{cid}/generated"

        params = {
            'start_time': start_time,
            'end_time': end_time
        }

        return await self.get(url, params=params)

    async def sdwan_mon_get_wan_policy_compliance(self, period: str, result_order: str,
                                                  count: int) -> Response:
        """SDWAN DPS policy compliance report.

        Args:
            period (str): the period of time the report is covering. Acceptable parameters -
                (last_day or last_week or last_month)
            result_order (str): for each policy, device uplinks will be sorted by compliance level.
                Acceptable parameters - (best or worst)
            count (int): the number of uplinks per policy to show up in the report. Acceptable
                parameters - (min 1 - max 250)

        Returns:
            Response: CentralAPI Response object
        """
        url = "//sdwan-mon-api/external/noc/reports/wan/policy-compliance"

        params = {
            'period': period,
            'result_order': result_order,
            'count': count
        }

        return await self.get(url, params=params)

    async def get_routing_v1_bgp_neighbor(self, device: str, marker: str = None, limit: int = 100) -> Response:
        """List BGP neighbor Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_bgp_neighbor_detail(self, device: str, address: str) -> Response:
        """Get BGP neighbor detailed information.

        Args:
            device (str): Device serial number
            address (str): IP address

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor/detail"

        params = {
            'address': address
        }

        return await self.get(url, params=params)

    async def put_routing_v1_bgp_neighbor_reset(self, device: str, address: str) -> Response:
        """Reset/clear BGP neighbor session.

        Args:
            device (str): Device serial number
            address (str): IP address

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor/reset"

        return await self.put(url)

    async def get_routing_v1_bgp_neighbor_route_learned(self, device: str, address: str,
                                                        marker: str = None, limit: int = 100) -> Response:
        """List of routes learned form a BGP neighbor.

        Args:
            device (str): Device serial number
            address (str): IP address
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor/route/learned"

        return await self.get(url)

    async def get_routing_v1_bgp_neighbor_route_advertised(self, device: str, address: str,
                                                           marker: str = None, limit: int = 100) -> Response:
        """List of routes advertised to a BGP neighbor.

        Args:
            device (str): Device serial number
            address (str): IP address
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor/route/advertised"

        return await self.get(url)

    async def get_routing_v1_bgp_route(self, device: str, marker: str = None, limit: int = 100) -> Response:
        """List BGP routes.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/route"

        return await self.get(url)

    async def get_routing_v1_overlay_connection(self, device: str, marker: str = None,
                                                limit: int = 100) -> Response:
        """Get information about overlay control connection.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def put_routing_v1_overlay_connection_reset(self, device: str) -> Response:
        """Reset overlay control connection.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection/reset"

        return await self.put(url)

    async def get_routing_v1_overlay_interface(self, device: str, marker: str = None,
                                               limit: int = 100) -> Response:
        """List of overlay interfaces (tunnels).

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/interface"

        return await self.get(url)

    async def get_routing_v1_overlay_route_learned(self, device: str, marker: str = None,
                                                   limit: int = 100) -> Response:
        """List of learned routes from overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/learned"

        return await self.get(url)

    async def get_routing_v1_overlay_route_learned_best(self, device: str, marker: str = None,
                                                        limit: int = 100) -> Response:
        """List of best learned routes from overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/learned/best"

        return await self.get(url)

    async def get_routing_v1_overlay_route_advertised(self, device: str, marker: str = None,
                                                      limit: int = 100) -> Response:
        """List of advertised routes to overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/advertised"

        return await self.get(url)

    async def get_routing_v1_ospf_area(self, device: str, marker: str = None, limit: int = 100) -> Response:
        """List OSPF Area Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/area"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_ospf_interface(self, device: str, marker: str = None,
                                            limit: int = 100) -> Response:
        """List OSPF Interface Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/interface"

        return await self.get(url)

    async def get_routing_v1_ospf_neighbor(self, device: str, marker: str = None,
                                           limit: int = 100) -> Response:
        """List OSPF neighbor Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/neighbor"

        return await self.get(url)

    async def get_routing_v1_ospf_database(self, device: str, marker: str = None,
                                           limit: int = 100) -> Response:
        """List OSPF Link State Database Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/database"

        return await self.get(url)

    async def get_routing_v1_rip_interface(self, device: str, marker: str = None,
                                           limit: int = 100) -> Response:
        """List RIP interfaces.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/rip/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_rip_neighbor(self, device: str, marker: str = None, limit: int = 100) -> Response:
        """List RIP neighbors.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/rip/neighbor"

        return await self.get(url)

    async def get_routing_v1_rip_neighbor_route(self, device: str, address: str,
                                                marker: str = None, limit: int = 100) -> Response:
        """List of routes learned from a RIP neighbor.

        Args:
            device (str): Device serial number
            address (str): IP address
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/rip/neighbor/route"

        params = {
            'address': address
        }

        return await self.get(url, params=params)

    async def get_routing_v1_rip_route(self, device: str, marker: str = None, limit: int = 100) -> Response:
        """List RIP routes.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/rip/route"

        return await self.get(url)

    async def get_routing_v1_route(self, device: str, api: str = None, marker: str = None,
                                   limit: int = 100) -> Response:
        """Get routes.

        Args:
            device (str): Device serial number
            api (str, optional): API version (V0|V1)
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/route"

        params = {
            'device': device,
            'api': api,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v0_route(self, device: str) -> Response:
        """Get legacy routes.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v0/route"

        return await self.get(url)

    async def airgroup_config_get_aruba_dial_id16(self, node_type: str, node_id: str) -> Response:
        """Retrieve dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/"

        return await self.get(url)

    async def airgroup_config_post_aruba_dial_id16(self, node_type: str, node_id: str,
                                                   status: bool, disallowed_vlans: List[str],
                                                   disallowed_roles: List[str], desc: str) -> Response:
        """Create dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_dial_id16(self, node_type: str, node_id: str,
                                                  status: bool, disallowed_vlans: List[str],
                                                  disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_dial_id16(self, node_type: str, node_id: str) -> Response:
        """Delete dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_standard_services_id17(self, node_type: str, node_id: str) -> Response:
        """Retrieve standard_services.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/"

        return await self.get(url)

    async def airgroup_config_post_aruba_standard_services_id17(self, node_type: str,
                                                                node_id: str,
                                                                disallowed_vlans: List[str],
                                                                disallowed_roles: List[str]) -> Response:
        """Create standard_services.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_standard_services_id17(self, node_type: str, node_id: str,
                                                               disallowed_vlans: List[str],
                                                               disallowed_roles: List[str]) -> Response:
        """Create/Update standard_services.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_standard_services_id17(self, node_type: str,
                                                                  node_id: str) -> Response:
        """Delete standard_services.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id3(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id3(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create disallowed for airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id3(self, node_type: str, node_id: str,
                                                       disallowed_vlans: List[str],
                                                       disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id3(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id15(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id15(self, node_type: str, node_id: str,
                                                         disallowed_vlans: List[str],
                                                         disallowed_roles: List[str]) -> Response:
        """Create disallowed for dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id15(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id15(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for dial.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dial/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_airplay_id4(self, node_type: str, node_id: str) -> Response:
        """Retrieve airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/"

        return await self.get(url)

    async def airgroup_config_post_aruba_airplay_id4(self, node_type: str, node_id: str,
                                                     status: bool, disallowed_vlans: List[str],
                                                     disallowed_roles: List[str], desc: str) -> Response:
        """Create airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_airplay_id4(self, node_type: str, node_id: str,
                                                    status: bool, disallowed_vlans: List[str],
                                                    disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_airplay_id4(self, node_type: str, node_id: str) -> Response:
        """Delete airplay.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airplay/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_amazon_tv_id14(self, node_type: str, node_id: str) -> Response:
        """Retrieve amazon_tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/"

        return await self.get(url)

    async def airgroup_config_post_aruba_amazon_tv_id14(self, node_type: str, node_id: str,
                                                        status: bool, disallowed_vlans: List[str],
                                                        disallowed_roles: List[str], desc: str) -> Response:
        """Create amazon_tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_amazon_tv_id14(self, node_type: str, node_id: str,
                                                       status: bool, disallowed_vlans: List[str],
                                                       disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update amazon_tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_amazon_tv_id14(self, node_type: str, node_id: str) -> Response:
        """Delete amazon_tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_general_settings_id2(self, node_type: str, node_id: str) -> Response:
        """Retrieve general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/"

        return await self.get(url)

    async def airgroup_config_post_aruba_general_settings_id2(self, node_type: str, node_id: str,
                                                              airgroup_status: bool) -> Response:
        """Create general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_general_settings_id2(self, node_type: str, node_id: str,
                                                             airgroup_status: bool) -> Response:
        """Create/Update general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_general_settings_id2(self, node_type: str,
                                                                node_id: str) -> Response:
        """Delete general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_airprint_id6(self, node_type: str, node_id: str) -> Response:
        """Retrieve airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/"

        return await self.get(url)

    async def airgroup_config_post_aruba_airprint_id6(self, node_type: str, node_id: str,
                                                      status: bool, disallowed_vlans: List[str],
                                                      disallowed_roles: List[str], desc: str) -> Response:
        """Create airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_airprint_id6(self, node_type: str, node_id: str,
                                                     status: bool, disallowed_vlans: List[str],
                                                     disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_airprint_id6(self, node_type: str, node_id: str) -> Response:
        """Delete airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_config_id18(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def airgroup_config_post_aruba_config_id18(self, node_type: str, node_id: str,
                                                     airgroup_status: bool,
                                                     disallowed_vlans: List[str],
                                                     disallowed_roles: List[str]) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'airgroup_status': airgroup_status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_config_id18(self, node_type: str, node_id: str,
                                                    airgroup_status: bool,
                                                    disallowed_vlans: List[str],
                                                    disallowed_roles: List[str]) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'airgroup_status': airgroup_status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_config_id18(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_googlecast_id8(self, node_type: str, node_id: str) -> Response:
        """Retrieve googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/"

        return await self.get(url)

    async def airgroup_config_post_aruba_googlecast_id8(self, node_type: str, node_id: str,
                                                        status: bool, disallowed_vlans: List[str],
                                                        disallowed_roles: List[str], desc: str) -> Response:
        """Create googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_googlecast_id8(self, node_type: str, node_id: str,
                                                       status: bool, disallowed_vlans: List[str],
                                                       disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_googlecast_id8(self, node_type: str, node_id: str) -> Response:
        """Delete googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id13(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for amazon tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id13(self, node_type: str, node_id: str,
                                                         disallowed_vlans: List[str],
                                                         disallowed_roles: List[str]) -> Response:
        """Create disallowed for amazon tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id13(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for amazon tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id13(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for amazon tv.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/amazon_tv/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_node_list_id19(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def airgroup_config_get_aruba_airgroup_status_id1(self, node_type: str, node_id: str) -> Response:
        """Retrieve airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        return await self.get(url)

    async def airgroup_config_post_aruba_airgroup_status_id1(self, node_type: str, node_id: str,
                                                             airgroup_status: bool) -> Response:
        """Create airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_airgroup_status_id1(self, node_type: str, node_id: str,
                                                            airgroup_status: bool) -> Response:
        """Create/Update airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_airgroup_status_id1(self, node_type: str, node_id: str) -> Response:
        """Delete airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id7(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id7(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create disallowed for googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id7(self, node_type: str, node_id: str,
                                                       disallowed_vlans: List[str],
                                                       disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id7(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for googlecast.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/googlecast/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_dlnaprint_id12(self, node_type: str, node_id: str) -> Response:
        """Retrieve dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/"

        return await self.get(url)

    async def airgroup_config_post_aruba_dlnaprint_id12(self, node_type: str, node_id: str,
                                                        status: bool, disallowed_vlans: List[str],
                                                        disallowed_roles: List[str], desc: str) -> Response:
        """Create dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_dlnaprint_id12(self, node_type: str, node_id: str,
                                                       status: bool, disallowed_vlans: List[str],
                                                       disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_dlnaprint_id12(self, node_type: str, node_id: str) -> Response:
        """Delete dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id9(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id9(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create disallowed for dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id9(self, node_type: str, node_id: str,
                                                       disallowed_vlans: List[str],
                                                       disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id9(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id5(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id5(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create disallowed for airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id5(self, node_type: str, node_id: str,
                                                       disallowed_vlans: List[str],
                                                       disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id5(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for airprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/airprint/disallowed/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_dlnamedia_id10(self, node_type: str, node_id: str) -> Response:
        """Retrieve dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/"

        return await self.get(url)

    async def airgroup_config_post_aruba_dlnamedia_id10(self, node_type: str, node_id: str,
                                                        status: bool, disallowed_vlans: List[str],
                                                        disallowed_roles: List[str], desc: str) -> Response:
        """Create dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_dlnamedia_id10(self, node_type: str, node_id: str,
                                                       status: bool, disallowed_vlans: List[str],
                                                       disallowed_roles: List[str], desc: str) -> Response:
        """Create/Update dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            status (bool): Indicates whether service is enabled or disabled
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles
            desc (str): Few line description of the service

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/"

        json_data = {
            'status': status,
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles,
            'desc': desc
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_dlnamedia_id10(self, node_type: str, node_id: str) -> Response:
        """Delete dlnamedia.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnamedia/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_id11(self, node_type: str, node_id: str) -> Response:
        """Retrieve disallowed for dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/disallowed/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_id11(self, node_type: str, node_id: str,
                                                         disallowed_vlans: List[str],
                                                         disallowed_roles: List[str]) -> Response:
        """Create disallowed for dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_id11(self, node_type: str, node_id: str,
                                                        disallowed_vlans: List[str],
                                                        disallowed_roles: List[str]) -> Response:
        """Create/Update disallowed for dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            disallowed_vlans (List[str]): list of disallowed VLAN id or range of vlan ids
            disallowed_roles (List[str]): list of disallowed user/server Roles

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/disallowed/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'disallowed_roles': disallowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_id11(self, node_type: str, node_id: str) -> Response:
        """Delete disallowed for dlnaprint.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v1/node_list/{node_type}/{node_id}/config/standard_services/dlnaprint/disallowed/"

        return await self.delete(url)

    async def airmatch_config_get_aruba_config_id2(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def airmatch_config_post_aruba_config_id2(self, node_type: str, node_id: str,
                                                    deploy_hour: int, quality_threshold: int,
                                                    schedule: bool) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                Range 0-100. Default: 8
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'schedule': schedule
        }

        return await self.post(url, json_data=json_data)

    async def airmatch_config_put_aruba_config_id2(self, node_type: str, node_id: str,
                                                   deploy_hour: int, quality_threshold: int,
                                                   schedule: bool) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                Range 0-100. Default: 8
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'schedule': schedule
        }

        return await self.put(url, json_data=json_data)

    async def airmatch_config_delete_aruba_config_id2(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def airmatch_config_get_aruba_system_id1(self, node_type: str, node_id: str) -> Response:
        """Retrieve system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        return await self.get(url)

    async def airmatch_config_post_aruba_system_id1(self, node_type: str, node_id: str,
                                                    deploy_hour: int, quality_threshold: int,
                                                    schedule: bool) -> Response:
        """Create system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                Range 0-100. Default: 8
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        json_data = {
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'schedule': schedule
        }

        return await self.post(url, json_data=json_data)

    async def airmatch_config_put_aruba_system_id1(self, node_type: str, node_id: str,
                                                   deploy_hour: int, quality_threshold: int,
                                                   schedule: bool) -> Response:
        """Create/Update system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                Range 0-100. Default: 8
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        json_data = {
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'schedule': schedule
        }

        return await self.put(url, json_data=json_data)

    async def airmatch_config_delete_aruba_system_id1(self, node_type: str, node_id: str) -> Response:
        """Delete system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        return await self.delete(url)

    async def airmatch_config_get_aruba_node_list_id3(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def cloud_security_config_get_aruba_security_config_id2(self, node_type: str,
                                                                  node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def cloud_security_config_post_aruba_security_config_id2(self, node_type: str,
                                                                   node_id: str, base_uri: str,
                                                                   password: str,
                                                                   admin_status: str,
                                                                   api_key: str, user: str) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            base_uri (str): Base URI to access cloud security provider.
            password (str): Password to be used as login credential.
            admin_status (str): Enable auto config for Zscaler  Valid Values: UP, DOWN
            api_key (str): Organization's API key.
            user (str): User name to be used as login credential.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'base_uri': base_uri,
            'password': password,
            'admin_status': admin_status,
            'api_key': api_key,
            'user': user
        }

        return await self.post(url, json_data=json_data)

    async def cloud_security_config_put_aruba_security_config_id2(self, node_type: str,
                                                                  node_id: str, base_uri: str,
                                                                  password: str,
                                                                  admin_status: str, api_key: str,
                                                                  user: str) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            base_uri (str): Base URI to access cloud security provider.
            password (str): Password to be used as login credential.
            admin_status (str): Enable auto config for Zscaler  Valid Values: UP, DOWN
            api_key (str): Organization's API key.
            user (str): User name to be used as login credential.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'base_uri': base_uri,
            'password': password,
            'admin_status': admin_status,
            'api_key': api_key,
            'user': user
        }

        return await self.put(url, json_data=json_data)

    async def cloud_security_config_delete_aruba_security_config_id2(self, node_type: str,
                                                                     node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def cloud_security_config_get_aruba_security_zscaler_id1(self, node_type: str,
                                                                   node_id: str) -> Response:
        """Retrieve zscaler.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/zscaler/"

        return await self.get(url)

    async def cloud_security_config_post_aruba_security_zscaler_id1(self, node_type: str,
                                                                    node_id: str, base_uri: str,
                                                                    password: str,
                                                                    admin_status: str,
                                                                    api_key: str, user: str) -> Response:
        """Create zscaler.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            base_uri (str): Base URI to access cloud security provider.
            password (str): Password to be used as login credential.
            admin_status (str): Enable auto config for Zscaler  Valid Values: UP, DOWN
            api_key (str): Organization's API key.
            user (str): User name to be used as login credential.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/zscaler/"

        json_data = {
            'base_uri': base_uri,
            'password': password,
            'admin_status': admin_status,
            'api_key': api_key,
            'user': user
        }

        return await self.post(url, json_data=json_data)

    async def cloud_security_config_put_aruba_security_zscaler_id1(self, node_type: str,
                                                                   node_id: str, base_uri: str,
                                                                   password: str,
                                                                   admin_status: str,
                                                                   api_key: str, user: str) -> Response:
        """Create/Update zscaler.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            base_uri (str): Base URI to access cloud security provider.
            password (str): Password to be used as login credential.
            admin_status (str): Enable auto config for Zscaler  Valid Values: UP, DOWN
            api_key (str): Organization's API key.
            user (str): User name to be used as login credential.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/zscaler/"

        json_data = {
            'base_uri': base_uri,
            'password': password,
            'admin_status': admin_status,
            'api_key': api_key,
            'user': user
        }

        return await self.put(url, json_data=json_data)

    async def cloud_security_config_delete_aruba_security_zscaler_id1(self, node_type: str,
                                                                      node_id: str) -> Response:
        """Delete zscaler.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/config/zscaler/"

        return await self.delete(url)

    async def cloud_security_config_get_aruba_security_node_list_id3(self, node_type: str,
                                                                     node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloud-security-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def ids_ips_config_get_aruba_ips_node_list_id5(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def ids_ips_config_get_aruba_ips_siem_servers_list_id3(self, node_type: str,
                                                                 node_id: str) -> Response:
        """Retrieve siem_servers_list.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/"

        return await self.get(url)

    async def ids_ips_config_get_aruba_ips_siem_servers_list_id2(self, node_type: str,
                                                                 node_id: str,
                                                                 siem_server_name: str) -> Response:
        """Retrieve siem_servers_list by identifier siem_server_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_server_name (str): SIEM server name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        return await self.get(url)

    async def ids_ips_config_post_aruba_ips_siem_servers_list_id2(self, node_type: str,
                                                                  node_id: str,
                                                                  siem_server_name: str,
                                                                  siem_index: str,
                                                                  new_siem_server_name: str,
                                                                  siem_server_url: str,
                                                                  siem_token: str) -> Response:
        """Create siem_servers_list by identifier siem_server_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_server_name (str): SIEM server name
            siem_index (str): SIEM bucket that the events have to go into
            new_siem_server_name (str): SIEM server name
            siem_server_url (str): SIEM server url including the port
            siem_token (str): SIEM authentication token; HEC token in case of Splunk

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        json_data = {
            'siem_index': siem_index,
            'new_siem_server_name': new_siem_server_name,
            'siem_server_url': siem_server_url,
            'siem_token': siem_token
        }

        return await self.post(url, json_data=json_data)

    async def ids_ips_config_put_aruba_ips_siem_servers_list_id2(self, node_type: str,
                                                                 node_id: str,
                                                                 siem_server_name: str,
                                                                 siem_index: str,
                                                                 new_siem_server_name: str,
                                                                 siem_server_url: str,
                                                                 siem_token: str) -> Response:
        """Create/Update siem_servers_list by identifier siem_server_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_server_name (str): SIEM server name
            siem_index (str): SIEM bucket that the events have to go into
            new_siem_server_name (str): SIEM server name
            siem_server_url (str): SIEM server url including the port
            siem_token (str): SIEM authentication token; HEC token in case of Splunk

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        json_data = {
            'siem_index': siem_index,
            'new_siem_server_name': new_siem_server_name,
            'siem_server_url': siem_server_url,
            'siem_token': siem_token
        }

        return await self.put(url, json_data=json_data)

    async def ids_ips_config_delete_aruba_ips_siem_servers_list_id2(self, node_type: str,
                                                                    node_id: str,
                                                                    siem_server_name: str) -> Response:
        """Delete siem_servers_list by identifier siem_server_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_server_name (str): SIEM server name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        return await self.delete(url)

    async def ids_ips_config_get_aruba_ips_siem_notification_id1(self, node_type: str,
                                                                 node_id: str) -> Response:
        """Retrieve siem_notification.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_notification/"

        return await self.get(url)

    async def ids_ips_config_post_aruba_ips_siem_notification_id1(self, node_type: str,
                                                                  node_id: str, enable: bool) -> Response:
        """Create siem_notification.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            enable (bool): Enable reporting of threats to SIEM systems

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_notification/"

        json_data = {
            'enable': enable
        }

        return await self.post(url, json_data=json_data)

    async def ids_ips_config_put_aruba_ips_siem_notification_id1(self, node_type: str,
                                                                 node_id: str, enable: bool) -> Response:
        """Create/Update siem_notification.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            enable (bool): Enable reporting of threats to SIEM systems

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_notification/"

        json_data = {
            'enable': enable
        }

        return await self.put(url, json_data=json_data)

    async def ids_ips_config_delete_aruba_ips_siem_notification_id1(self, node_type: str,
                                                                    node_id: str) -> Response:
        """Delete siem_notification.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_notification/"

        return await self.delete(url)

    async def ids_ips_config_get_aruba_ips_config_id4(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def ids_ips_config_post_aruba_ips_config_id3(self, node_type: str, node_id: str,
                                                       siem_servers_list: list, enable: bool) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_servers_list (list): SIEM Server Configuration
            enable (bool): Enable reporting of threats to SIEM systems

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'siem_servers_list': siem_servers_list,
            'enable': enable
        }

        return await self.post(url, json_data=json_data)

    async def ids_ips_config_put_aruba_ips_config_id3(self, node_type: str, node_id: str,
                                                      siem_servers_list: list, enable: bool) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            siem_servers_list (list): SIEM Server Configuration
            enable (bool): Enable reporting of threats to SIEM systems

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'siem_servers_list': siem_servers_list,
            'enable': enable
        }

        return await self.put(url, json_data=json_data)

    async def ids_ips_config_delete_aruba_ips_config_id3(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def overlay_wlan_config_get_aruba_wlan_gw_cluster_list_id1(self, node_type: str,
                                                                     node_id: str, profile: str,
                                                                     profile_type: str,
                                                                     cluster_redundancy_type: str,
                                                                     cluster_group_name: str) -> Response:
        """Retrieve gw_cluster_list by identifier cluster_redundancy_type cluster_group_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY, BACKUP
            cluster_group_name (str): Cluster Group Name. Group name to which the cluster belongs
                to.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

        return await self.get(url)

    async def overlay_wlan_config_post_aruba_wlan_gw_cluster_list_id1(self, node_type: str,
                                                                      node_id: str, profile: str,
                                                                      profile_type: str,
                                                                      cluster_redundancy_type: str,
                                                                      cluster_group_name: str,
                                                                      new_cluster_redundancy_type: str,
                                                                      cluster: str,
                                                                      new_cluster_group_name: str,
                                                                      tunnel_type: str,
                                                                      cluster_type: str) -> Response:
        """Create gw_cluster_list by identifier cluster_redundancy_type cluster_group_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY, BACKUP
            cluster_group_name (str): Cluster Group Name. Group name to which the cluster belongs
                to.
            new_cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY,
                BACKUP
            cluster (str): Cluster name
            new_cluster_group_name (str): Cluster Group Name. Group name to which the cluster
                belongs to.
            tunnel_type (str): Type of Tunnel  Valid Values: IPSEC, GRE, MPLS, GREOIPSEC
            cluster_type (str): Type of Cluster  Valid Values: CLUSTER_ID, SITE_CLUSTER

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

        json_data = {
            'new_cluster_redundancy_type': new_cluster_redundancy_type,
            'cluster': cluster,
            'new_cluster_group_name': new_cluster_group_name,
            'tunnel_type': tunnel_type,
            'cluster_type': cluster_type
        }

        return await self.post(url, json_data=json_data)

    async def overlay_wlan_config_put_aruba_wlan_gw_cluster_list_id1(self, node_type: str,
                                                                     node_id: str, profile: str,
                                                                     profile_type: str,
                                                                     cluster_redundancy_type: str,
                                                                     cluster_group_name: str,
                                                                     new_cluster_redundancy_type: str,
                                                                     cluster: str,
                                                                     new_cluster_group_name: str,
                                                                     tunnel_type: str,
                                                                     cluster_type: str) -> Response:
        """Create/Update gw_cluster_list by identifier cluster_redundancy_type cluster_group_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY, BACKUP
            cluster_group_name (str): Cluster Group Name. Group name to which the cluster belongs
                to.
            new_cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY,
                BACKUP
            cluster (str): Cluster name
            new_cluster_group_name (str): Cluster Group Name. Group name to which the cluster
                belongs to.
            tunnel_type (str): Type of Tunnel  Valid Values: IPSEC, GRE, MPLS, GREOIPSEC
            cluster_type (str): Type of Cluster  Valid Values: CLUSTER_ID, SITE_CLUSTER

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

        json_data = {
            'new_cluster_redundancy_type': new_cluster_redundancy_type,
            'cluster': cluster,
            'new_cluster_group_name': new_cluster_group_name,
            'tunnel_type': tunnel_type,
            'cluster_type': cluster_type
        }

        return await self.put(url, json_data=json_data)

    async def overlay_wlan_config_delete_aruba_wlan_gw_cluster_list_id1(self, node_type: str,
                                                                        node_id: str,
                                                                        profile: str,
                                                                        profile_type: str,
                                                                        cluster_redundancy_type: str,
                                                                        cluster_group_name: str) -> Response:
        """Delete gw_cluster_list by identifier cluster_redundancy_type cluster_group_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            cluster_redundancy_type (str): Type of Cluster Redundancy  Valid Values: PRIMARY, BACKUP
            cluster_group_name (str): Cluster Group Name. Group name to which the cluster belongs
                to.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

        return await self.delete(url)

    async def overlay_wlan_config_get_aruba_wlan_gw_cluster_list_id2(self, node_type: str,
                                                                     node_id: str, profile: str,
                                                                     profile_type: str) -> Response:
        """Retrieve gw_cluster_list.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/"

        return await self.get(url)

    async def overlay_wlan_config_get_aruba_wlan_config_id5(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def overlay_wlan_config_post_aruba_wlan_config_id3(self, node_type: str, node_id: str,
                                                             address_family: List[str],
                                                             ssid_cluster: list) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            address_family (List[str]): Address family configuration <AFI,SAFI>.
            ssid_cluster (list): Wlan profile to Cluster mapping

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'address_family': address_family,
            'ssid_cluster': ssid_cluster
        }

        return await self.post(url, json_data=json_data)

    async def overlay_wlan_config_put_aruba_wlan_config_id3(self, node_type: str, node_id: str,
                                                            address_family: List[str],
                                                            ssid_cluster: list) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            address_family (List[str]): Address family configuration <AFI,SAFI>.
            ssid_cluster (list): Wlan profile to Cluster mapping

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'address_family': address_family,
            'ssid_cluster': ssid_cluster
        }

        return await self.put(url, json_data=json_data)

    async def overlay_wlan_config_delete_aruba_wlan_config_id3(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def overlay_wlan_config_get_aruba_wlan_ssid_cluster_id3(self, node_type: str,
                                                                  node_id: str, profile: str,
                                                                  profile_type: str) -> Response:
        """Retrieve ssid_cluster by identifier profile profile_type.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/"

        return await self.get(url)

    async def overlay_wlan_config_post_aruba_wlan_ssid_cluster_id2(self, node_type: str,
                                                                   node_id: str, profile: str,
                                                                   profile_type: str,
                                                                   new_profile: str,
                                                                   gw_cluster_list: list,
                                                                   new_profile_type: str) -> Response:
        """Create ssid_cluster by identifier profile profile_type.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            new_profile (str): Wlan ssid name or wired-port profile name
            gw_cluster_list (list): Gw Cluster
            new_profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/"

        json_data = {
            'new_profile': new_profile,
            'gw_cluster_list': gw_cluster_list,
            'new_profile_type': new_profile_type
        }

        return await self.post(url, json_data=json_data)

    async def overlay_wlan_config_put_aruba_wlan_ssid_cluster_id2(self, node_type: str,
                                                                  node_id: str, profile: str,
                                                                  profile_type: str,
                                                                  new_profile: str,
                                                                  gw_cluster_list: list,
                                                                  new_profile_type: str) -> Response:
        """Create/Update ssid_cluster by identifier profile profile_type.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE
            new_profile (str): Wlan ssid name or wired-port profile name
            gw_cluster_list (list): Gw Cluster
            new_profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/"

        json_data = {
            'new_profile': new_profile,
            'gw_cluster_list': gw_cluster_list,
            'new_profile_type': new_profile_type
        }

        return await self.put(url, json_data=json_data)

    async def overlay_wlan_config_delete_aruba_wlan_ssid_cluster_id2(self, node_type: str,
                                                                     node_id: str, profile: str,
                                                                     profile_type: str) -> Response:
        """Delete ssid_cluster by identifier profile profile_type.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            profile (str): Wlan ssid name or wired-port profile name
            profile_type (str): WIRELESS_PROFILE if profile is wlan ssid name, pass
                'WIRED_PORT_PROFILE' if profile is wired-port profile  Valid Values:
                WIRELESS_PROFILE, WIRED_PORT_PROFILE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/"

        return await self.delete(url)

    async def overlay_wlan_config_get_aruba_wlan_ssid_cluster_id4(self, node_type: str,
                                                                  node_id: str) -> Response:
        """Retrieve ssid_cluster.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/"

        return await self.get(url)

    async def overlay_wlan_config_get_aruba_wlan_node_list_id6(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GROUP
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def sdwan_config_get_aruba_admin_status_id16(self, node_type: str, node_id: str) -> Response:
        """Retrieve admin-status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/admin-status/"

        return await self.get(url)

    async def sdwan_config_put_aruba_load_balance_orchestration_id16(self, node_type: str,
                                                                     node_id: str, hold_time: int,
                                                                     pre_emption: bool,
                                                                     randomize_time: int) -> Response:
        """Create/Update load-balance-orchestration.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            hold_time (int): Hold time, in seconds, before switching over to the alternate hub after
                the connectivity to the active hub is lost. Range is 30..300 seconds
            pre_emption (bool): Enable/disable preemption. If enabled then the routing path is
                switched back to the primary as soon as primary is available.
            randomize_time (int): Random time after hold-time when failover occurs. Range is 30..300
                seconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/load-balance-orchestration/"

        json_data = {
            'hold_time': hold_time,
            'pre_emption': pre_emption,
            'randomize_time': randomize_time
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_load_balance_orchestration_id16(self, node_type: str,
                                                                      node_id: str,
                                                                      hold_time: int,
                                                                      pre_emption: bool,
                                                                      randomize_time: int) -> Response:
        """Create load-balance-orchestration.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            hold_time (int): Hold time, in seconds, before switching over to the alternate hub after
                the connectivity to the active hub is lost. Range is 30..300 seconds
            pre_emption (bool): Enable/disable preemption. If enabled then the routing path is
                switched back to the primary as soon as primary is available.
            randomize_time (int): Random time after hold-time when failover occurs. Range is 30..300
                seconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/load-balance-orchestration/"

        json_data = {
            'hold_time': hold_time,
            'pre_emption': pre_emption,
            'randomize_time': randomize_time
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_load_balance_orchestration_id26(self, node_type: str,
                                                                     node_id: str) -> Response:
        """Retrieve load-balance-orchestration.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/load-balance-orchestration/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_load_balance_orchestration_id18(self, node_type: str,
                                                                        node_id: str) -> Response:
        """Delete load-balance-orchestration.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/load-balance-orchestration/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hub_mesh_id37(self, node_type: str, node_id: str) -> Response:
        """Retrieve hub-mesh.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/"

        return await self.get(url)

    async def sdwan_config_put_aruba_tunnel_policy_id20(self, node_type: str, node_id: str,
                                                        type: str, rekey_interval: int) -> Response:
        """Create/Update tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            type (str): Type of tunnel  Valid Values: IPSEC
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        json_data = {
            'type': type,
            'rekey_interval': rekey_interval
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_tunnel_policy_id20(self, node_type: str, node_id: str,
                                                         type: str, rekey_interval: int) -> Response:
        """Create tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            type (str): Type of tunnel  Valid Values: IPSEC
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        json_data = {
            'type': type,
            'rekey_interval': rekey_interval
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_tunnel_policy_id33(self, node_type: str, node_id: str) -> Response:
        """Retrieve tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_tunnel_policy_id23(self, node_type: str, node_id: str) -> Response:
        """Delete tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_branch_mesh_id4(self, label: str) -> Response:
        """Retrieve branch-mesh by label.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_transit_id3(self, node_type: str, node_id: str,
                                                 transit: bool) -> Response:
        """Create/Update transit.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            transit (bool): Ability to provide transit (inter-branch connectivity) services.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/transit/"

        json_data = {
            'transit': transit
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_transit_id3(self, node_type: str, node_id: str,
                                                  transit: bool) -> Response:
        """Create transit.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            transit (bool): Ability to provide transit (inter-branch connectivity) services.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/transit/"

        json_data = {
            'transit': transit
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_transit_id7(self, node_type: str, node_id: str) -> Response:
        """Retrieve transit.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/transit/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_transit_id3(self, node_type: str, node_id: str) -> Response:
        """Delete transit.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/transit/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_topology_id9(self, node_type: str, node_id: str,
                                                  topology: str) -> Response:
        """Create/Update topology.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            topology (str): Overlay topology  Valid Values: HUB_AND_SPOKE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/topology/"

        json_data = {
            'topology': topology
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_topology_id9(self, node_type: str, node_id: str,
                                                   topology: str) -> Response:
        """Create topology.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            topology (str): Overlay topology  Valid Values: HUB_AND_SPOKE

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/topology/"

        json_data = {
            'topology': topology
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_topology_id17(self, node_type: str, node_id: str) -> Response:
        """Retrieve topology.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/topology/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_topology_id10(self, node_type: str, node_id: str) -> Response:
        """Delete topology.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/topology/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_sdwan_global_id20(self, node_type: str, node_id: str) -> Response:
        """Retrieve sdwan-global.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/"

        return await self.get(url)

    async def sdwan_config_get_aruba_route_policy_id31(self, node_type: str, node_id: str) -> Response:
        """Retrieve route-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/"

        return await self.get(url)

    async def sdwan_config_put_aruba_hub_mesh_id22(self, node_type: str, node_id: str, label: str,
                                                   hub_groups: list, new_label: str) -> Response:
        """Create/Update hub-mesh by identifier label.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            hub_groups (list): List of hub groups (data centers) to form a mesh.
            new_label (str): Hub-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/"

        json_data = {
            'hub_groups': hub_groups,
            'new_label': new_label
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_mesh_id22(self, node_type: str, node_id: str,
                                                    label: str, hub_groups: list, new_label: str) -> Response:
        """Create hub-mesh by identifier label.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            hub_groups (list): List of hub groups (data centers) to form a mesh.
            new_label (str): Hub-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/"

        json_data = {
            'hub_groups': hub_groups,
            'new_label': new_label
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_hub_mesh_id36(self, node_type: str, node_id: str, label: str) -> Response:
        """Retrieve hub-mesh by identifier label.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_hub_mesh_id25(self, node_type: str, node_id: str,
                                                      label: str) -> Response:
        """Delete hub-mesh by identifier label.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hubs_id14(self, node_type: str, node_id: str) -> Response:
        """Retrieve hubs.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/"

        return await self.get(url)

    async def sdwan_config_get_aruba_config_id39(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_config_id27(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hub_aggregates_id11(self, node_type: str, node_id: str) -> Response:
        """Retrieve hub-aggregates.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/"

        return await self.get(url)

    async def sdwan_config_put_aruba_as_number_id11(self, node_type: str, node_id: str,
                                                    as_number: int) -> Response:
        """Create/Update as-number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            as_number (int): Autonomous System Number for the Overlay Route Orchestrator.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/as-number/"

        json_data = {
            'as_number': as_number
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_as_number_id11(self, node_type: str, node_id: str,
                                                     as_number: int) -> Response:
        """Create as-number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            as_number (int): Autonomous System Number for the Overlay Route Orchestrator.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/as-number/"

        json_data = {
            'as_number': as_number
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_as_number_id21(self, node_type: str, node_id: str) -> Response:
        """Retrieve as-number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/as-number/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_as_number_id13(self, node_type: str, node_id: str) -> Response:
        """Delete as-number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/as-number/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_hub_id15(self, node_type: str, node_id: str,
                                              distance_factor: int, prefer_overlay_path: bool,
                                              best_path_computation: bool) -> Response:
        """Create/Update hub.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            distance_factor (int): Value used to determine the distance from branch to the
                corresponding hub devices. Range is 1..4294967295
            prefer_overlay_path (bool): Prefer overlay path when a prefix has both overlay and
                underlay paths when the corresponding overlay path is tagged with a special
                attribute.
            best_path_computation (bool): Indicates whether BGP-like best path computation is
                enabled for data center prefixes. It is disabled by default. If it is disabled then
                user provided preference (order of HUB devices) is used.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/"

        json_data = {
            'distance_factor': distance_factor,
            'prefer_overlay_path': prefer_overlay_path,
            'best_path_computation': best_path_computation
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_id15(self, node_type: str, node_id: str,
                                               distance_factor: int, prefer_overlay_path: bool,
                                               best_path_computation: bool) -> Response:
        """Create hub.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            distance_factor (int): Value used to determine the distance from branch to the
                corresponding hub devices. Range is 1..4294967295
            prefer_overlay_path (bool): Prefer overlay path when a prefix has both overlay and
                underlay paths when the corresponding overlay path is tagged with a special
                attribute.
            best_path_computation (bool): Indicates whether BGP-like best path computation is
                enabled for data center prefixes. It is disabled by default. If it is disabled then
                user provided preference (order of HUB devices) is used.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/"

        json_data = {
            'distance_factor': distance_factor,
            'prefer_overlay_path': prefer_overlay_path,
            'best_path_computation': best_path_computation
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_hub_id25(self, node_type: str, node_id: str) -> Response:
        """Retrieve hub.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_hub_id17(self, node_type: str, node_id: str) -> Response:
        """Delete hub.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_branch_mesh_id5(self, last_index: str = '0', offset: str = 0,
                                                     limit: int = 100) -> Response:
        """Retrieve branch-mesh.

        Args:
            last_index (str, optional): Last seen index returned part of the previous query . It can
                be used instead of offset for seeking the table faster
            offset (str, optional): Offset value from where to start lookup in the table Defaults to
                0.
            limit (int, optional): Max no.of Entries to be returned for Page. Default value and max
                value is set to 10 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/sdwan-config/v1/branch-mesh/"

        params = {
            'last_index': last_index,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def sdwan_config_put_aruba_hubs_id6(self, node_type: str, node_id: str, identifier: str,
                                              new_identifier: str) -> Response:
        """Create/Update hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            identifier (str): VPNC device serial-number
            new_identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        json_data = {
            'new_identifier': new_identifier
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hubs_id6(self, node_type: str, node_id: str,
                                               identifier: str, new_identifier: str) -> Response:
        """Create hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            identifier (str): VPNC device serial-number
            new_identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        json_data = {
            'new_identifier': new_identifier
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_hubs_id13(self, node_type: str, node_id: str,
                                               identifier: str) -> Response:
        """Retrieve hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_hubs_id7(self, node_type: str, node_id: str,
                                                 identifier: str) -> Response:
        """Delete hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_rekey_interval_id19(self, node_type: str, node_id: str,
                                                         rekey_interval: int) -> Response:
        """Create/Update rekey-interval.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/rekey-interval/"

        json_data = {
            'rekey_interval': rekey_interval
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_rekey_interval_id19(self, node_type: str, node_id: str,
                                                          rekey_interval: int) -> Response:
        """Create rekey-interval.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/rekey-interval/"

        json_data = {
            'rekey_interval': rekey_interval
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_rekey_interval_id32(self, node_type: str, node_id: str) -> Response:
        """Retrieve rekey-interval.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/rekey-interval/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_rekey_interval_id22(self, node_type: str, node_id: str) -> Response:
        """Delete rekey-interval.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/rekey-interval/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_branch_devices_id1(self, label: str, identifier: str,
                                                        new_identifier: str) -> Response:
        """Create/Update branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.
            new_identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        json_data = {
            'new_identifier': new_identifier
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_branch_devices_id1(self, label: str, identifier: str,
                                                         new_identifier: str) -> Response:
        """Create branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.
            new_identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        json_data = {
            'new_identifier': new_identifier
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_branch_devices_id1(self, label: str, identifier: str) -> Response:
        """Retrieve branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_branch_devices_id1(self, label: str, identifier: str) -> Response:
        """Delete branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_best_path_computation_id14(self, node_type: str,
                                                                node_id: str,
                                                                best_path_computation: bool) -> Response:
        """Create/Update best-path-computation.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            best_path_computation (bool): Indicates whether BGP-like best path computation is
                enabled for data center prefixes. It is disabled by default. If it is disabled then
                user provided preference (order of HUB devices) is used.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/best-path-computation/"

        json_data = {
            'best_path_computation': best_path_computation
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_best_path_computation_id14(self, node_type: str,
                                                                 node_id: str,
                                                                 best_path_computation: bool) -> Response:
        """Create best-path-computation.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            best_path_computation (bool): Indicates whether BGP-like best path computation is
                enabled for data center prefixes. It is disabled by default. If it is disabled then
                user provided preference (order of HUB devices) is used.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/best-path-computation/"

        json_data = {
            'best_path_computation': best_path_computation
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_best_path_computation_id24(self, node_type: str,
                                                                node_id: str) -> Response:
        """Retrieve best-path-computation.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/best-path-computation/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_best_path_computation_id16(self, node_type: str,
                                                                   node_id: str) -> Response:
        """Delete best-path-computation.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/hub/best-path-computation/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_aggregates_id9(self, node_type: str, node_id: str,
                                                    segment: str) -> Response:
        """Retrieve aggregates for hub-aggregates.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/aggregates/"

        return await self.get(url)

    async def sdwan_config_put_aruba_aggregates_id4(self, node_type: str, node_id: str,
                                                    segment: str, prefix: str, new_prefix: str) -> Response:
        """Create/Update DC aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised
            new_prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/aggregates/{prefix}/"

        json_data = {
            'new_prefix': new_prefix
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_aggregates_id4(self, node_type: str, node_id: str,
                                                     segment: str, prefix: str, new_prefix: str) -> Response:
        """Create DC aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised
            new_prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/aggregates/{prefix}/"

        json_data = {
            'new_prefix': new_prefix
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_aggregates_id8(self, node_type: str, node_id: str,
                                                    segment: str, prefix: str) -> Response:
        """Retrieve DC aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/aggregates/{prefix}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_aggregates_id4(self, node_type: str, node_id: str,
                                                       segment: str, prefix: str) -> Response:
        """Delete DC aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/aggregates/{prefix}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_mesh_policy_id38(self, node_type: str, node_id: str) -> Response:
        """Retrieve mesh-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_mesh_policy_id26(self, node_type: str, node_id: str) -> Response:
        """Delete mesh-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_network_segment_policy_id19(self, node_type: str,
                                                                 node_id: str) -> Response:
        """Retrieve network-segment-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/network-segment-policy/"

        return await self.get(url)

    async def sdwan_config_put_aruba_hub_groups_id21(self, node_type: str, node_id: str,
                                                     label: str, name: str, new_name: str) -> Response:
        """Create/Update hub-groups by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            name (str): Name of the hub group (data center). A hub group can only belong to one mesh
                label
            new_name (str): Name of the hub group (data center). A hub group can only belong to one
                mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/hub-groups/{name}/"

        json_data = {
            'new_name': new_name
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_groups_id21(self, node_type: str, node_id: str,
                                                      label: str, name: str, new_name: str) -> Response:
        """Create hub-groups by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            name (str): Name of the hub group (data center). A hub group can only belong to one mesh
                label
            new_name (str): Name of the hub group (data center). A hub group can only belong to one
                mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/hub-groups/{name}/"

        json_data = {
            'new_name': new_name
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_hub_groups_id34(self, node_type: str, node_id: str,
                                                     label: str, name: str) -> Response:
        """Retrieve hub-groups by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            name (str): Name of the hub group (data center). A hub group can only belong to one mesh
                label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/hub-groups/{name}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_hub_groups_id24(self, node_type: str, node_id: str,
                                                        label: str, name: str) -> Response:
        """Delete hub-groups by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label
            name (str): Name of the hub group (data center). A hub group can only belong to one mesh
                label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/hub-groups/{name}/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_graceful_restart_id13(self, node_type: str, node_id: str,
                                                           enabled: bool, timer: int) -> Response:
        """Create/Update Global graceful restart timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            enabled (bool): Indicates whether graceful-restart timer is enabled. Enabled by default.
            timer (int): Graceful restart timer (in seconds). This time indicates how long the the
                cached information needs to be retained when connectivity between the devices and
                overlay orchestrator is lost. The devices will flush the orchestrated information
                and the overlay orchestrator will flush the advertised information from the devices
                when the connectivity is not restored with in this interval. Value should be in the
                range 1 minute (60 seconds) to 7 days (604800) and default is 12 hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/"

        json_data = {
            'enabled': enabled,
            'timer': timer
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_graceful_restart_id13(self, node_type: str, node_id: str,
                                                            enabled: bool, timer: int) -> Response:
        """Create Global graceful restart timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            enabled (bool): Indicates whether graceful-restart timer is enabled. Enabled by default.
            timer (int): Graceful restart timer (in seconds). This time indicates how long the the
                cached information needs to be retained when connectivity between the devices and
                overlay orchestrator is lost. The devices will flush the orchestrated information
                and the overlay orchestrator will flush the advertised information from the devices
                when the connectivity is not restored with in this interval. Value should be in the
                range 1 minute (60 seconds) to 7 days (604800) and default is 12 hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/"

        json_data = {
            'enabled': enabled,
            'timer': timer
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_graceful_restart_id23(self, node_type: str, node_id: str) -> Response:
        """Retrieve Global graceful restart timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_graceful_restart_id15(self, node_type: str, node_id: str) -> Response:
        """Delete Global graceful restart timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_network_segment_policy_id10(self, node_type: str,
                                                                 node_id: str, name: str,
                                                                 new_name: str,
                                                                 load_balance: bool) -> Response:
        """Create/Update network-segment-policy by segment name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            name (str): Overlay network segment name
            new_name (str): Overlay network segment name
            load_balance (bool): Enable/Disable load balance orchestration.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/network-segment-policy/{name}/"

        json_data = {
            'new_name': new_name,
            'load_balance': load_balance
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_network_segment_policy_id10(self, node_type: str,
                                                                  node_id: str, name: str,
                                                                  new_name: str,
                                                                  load_balance: bool) -> Response:
        """Create network-segment-policy by segment name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            name (str): Overlay network segment name
            new_name (str): Overlay network segment name
            load_balance (bool): Enable/Disable load balance orchestration.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/network-segment-policy/{name}/"

        json_data = {
            'new_name': new_name,
            'load_balance': load_balance
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_network_segment_policy_id18(self, node_type: str,
                                                                 node_id: str, name: str) -> Response:
        """Retrieve network-segment-policy by segment name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            name (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/network-segment-policy/{name}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_network_segment_policy_id11(self, node_type: str,
                                                                    node_id: str, name: str) -> Response:
        """Delete network-segment-policy by segment name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            name (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/sdwan-global/network-segment-policy/{name}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_aggregates_id28(self, node_type: str, node_id: str,
                                                     segment: str) -> Response:
        """Retrieve aggregates for branch-aggregates.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/aggregates/"

        return await self.get(url)

    async def sdwan_config_get_aruba_branch_aggregates_id30(self, node_type: str, node_id: str) -> Response:
        """Retrieve branch-aggregates.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/"

        return await self.get(url)

    async def sdwan_config_put_aruba_branch_config_id7(self, node_type: str, node_id: str,
                                                       hubs: list) -> Response:
        """Create/Update branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            hubs (list): An ordered list of hub device identifiers

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs': hubs
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_branch_config_id7(self, node_type: str, node_id: str,
                                                        hubs: list) -> Response:
        """Create branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group
            hubs (list): An ordered list of hub device identifiers

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs': hubs
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_branch_config_id15(self, node_type: str, node_id: str) -> Response:
        """Retrieve branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_branch_config_id8(self, node_type: str, node_id: str) -> Response:
        """Delete branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BG group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_timer_id12(self, node_type: str, node_id: str, timer: int) -> Response:
        """Create/Update timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            timer (int): Graceful restart timer (in seconds). This time indicates how long the the
                cached information needs to be retained when connectivity between the devices and
                overlay orchestrator is lost. The devices will flush the orchestrated information
                and the overlay orchestrator will flush the advertised information from the devices
                when the connectivity is not restored with in this interval. Value should be in the
                range 1 minute (60 seconds) to 7 days (604800) and default is 12 hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/timer/"

        json_data = {
            'timer': timer
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_timer_id12(self, node_type: str, node_id: str, timer: int) -> Response:
        """Create timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            timer (int): Graceful restart timer (in seconds). This time indicates how long the the
                cached information needs to be retained when connectivity between the devices and
                overlay orchestrator is lost. The devices will flush the orchestrated information
                and the overlay orchestrator will flush the advertised information from the devices
                when the connectivity is not restored with in this interval. Value should be in the
                range 1 minute (60 seconds) to 7 days (604800) and default is 12 hours.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/timer/"

        json_data = {
            'timer': timer
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_timer_id22(self, node_type: str, node_id: str) -> Response:
        """Retrieve timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/timer/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_timer_id14(self, node_type: str, node_id: str) -> Response:
        """Delete timer.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/graceful-restart/timer/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_node_list_id40(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_config_id2(self, label: str, branch_devices: list) -> Response:
        """Create/Update branch-mesh config.

        Args:
            label (str): branch-mesh label
            branch_devices (list): List of branch devices to form a mesh.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        json_data = {
            'branch_devices': branch_devices
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_config_id2(self, label: str, branch_devices: list) -> Response:
        """Create branch-mesh config.

        Args:
            label (str): branch-mesh label
            branch_devices (list): List of branch devices to form a mesh.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        json_data = {
            'branch_devices': branch_devices
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_config_id3(self, label: str) -> Response:
        """Retrieve branch-mesh config.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_config_id2(self, label: str) -> Response:
        """Delete branch-mesh config.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_hub_aggregates_id5(self, node_type: str, node_id: str,
                                                        segment: str, aggregates: list,
                                                        new_segment: str) -> Response:
        """Create/Update DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            aggregates (list): No Description
            new_segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/"

        json_data = {
            'aggregates': aggregates,
            'new_segment': new_segment
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_aggregates_id5(self, node_type: str, node_id: str,
                                                         segment: str, aggregates: list,
                                                         new_segment: str) -> Response:
        """Create DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            aggregates (list): No Description
            new_segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/"

        json_data = {
            'aggregates': aggregates,
            'new_segment': new_segment
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_hub_aggregates_id10(self, node_type: str, node_id: str,
                                                         segment: str) -> Response:
        """Retrieve DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_hub_aggregates_id5(self, node_type: str, node_id: str,
                                                           segment: str) -> Response:
        """Delete DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/hub-aggregates/{segment}/"

        return await self.delete(url)

    async def sdwan_config_put_aruba_aggregates_id17(self, node_type: str, node_id: str,
                                                     segment: str, prefix: str, new_prefix: str) -> Response:
        """Create/Update global branch aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised
            new_prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/aggregates/{prefix}/"

        json_data = {
            'new_prefix': new_prefix
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_aggregates_id17(self, node_type: str, node_id: str,
                                                      segment: str, prefix: str, new_prefix: str) -> Response:
        """Create global branch aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised
            new_prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/aggregates/{prefix}/"

        json_data = {
            'new_prefix': new_prefix
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_aggregates_id27(self, node_type: str, node_id: str,
                                                     segment: str, prefix: str) -> Response:
        """Retrieve global branch aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/aggregates/{prefix}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_aggregates_id19(self, node_type: str, node_id: str,
                                                        segment: str, prefix: str) -> Response:
        """Delete global branch aggregate routes by prefix for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            prefix (str): Aggregate IPv4 prefix to be advertised

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/aggregates/{prefix}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hub_groups_id35(self, node_type: str, node_id: str,
                                                     label: str) -> Response:
        """Retrieve hub-groups.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            label (str): Hub-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/mesh-policy/hub-mesh/{label}/hub-groups/"

        return await self.get(url)

    async def sdwan_config_put_aruba_branch_aggregates_id18(self, node_type: str, node_id: str,
                                                            segment: str, aggregates: list,
                                                            new_segment: str) -> Response:
        """Create/Update global branch aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            aggregates (list): Aggregate prefixes
            new_segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/"

        json_data = {
            'aggregates': aggregates,
            'new_segment': new_segment
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_branch_aggregates_id18(self, node_type: str, node_id: str,
                                                             segment: str, aggregates: list,
                                                             new_segment: str) -> Response:
        """Create global branch aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name
            aggregates (list): Aggregate prefixes
            new_segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/"

        json_data = {
            'aggregates': aggregates,
            'new_segment': new_segment
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_get_aruba_branch_aggregates_id29(self, node_type: str, node_id: str,
                                                            segment: str) -> Response:
        """Retrieve global branch aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_branch_aggregates_id20(self, node_type: str, node_id: str,
                                                               segment: str) -> Response:
        """Delete global branch aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            segment (str): Overlay network segment name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/route-policy/branch-aggregates/{segment}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_branch_mesh_ui_id6(self, last_index: str = '0',
                                                        offset: str = 0, limit: int = 100) -> Response:
        """Retrieve branch-mesh-ui.

        Args:
            last_index (str, optional): Last seen index returned part of the previous query . It can
                be used instead of offset for seeking the table faster
            offset (str, optional): Offset value from where to start lookup in the table Defaults to
                0.
            limit (int, optional): Max no.of Entries to be returned for Page. Default value and max
                value is set to 10 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/sdwan-config/v1/branch-mesh-ui/"

        params = {
            'last_index': last_index,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def sdwan_config_get_aruba_hub_config_id12(self, node_type: str, node_id: str) -> Response:
        """Retrieve hub-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/hub-config/"

        return await self.get(url)

    async def sdwan_config_get_aruba_branch_devices_id2(self, label: str) -> Response:
        """Retrieve branch-devices.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/"

        return await self.get(url)

    async def ucc_config_get_aruba_dns_patterns_id4(self, node_type: str, node_id: str) -> Response:
        """Retrieve dns_patterns.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/"

        return await self.get(url)

    async def ucc_config_get_aruba_facetime_id2(self, node_type: str, node_id: str) -> Response:
        """Retrieve facetime.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/facetime/"

        return await self.get(url)

    async def ucc_config_post_aruba_facetime_id2(self, node_type: str, node_id: str,
                                                 video_priority: int) -> Response:
        """Create facetime.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/facetime/"

        json_data = {
            'video_priority': video_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_facetime_id2(self, node_type: str, node_id: str,
                                                video_priority: int) -> Response:
        """Create/Update facetime.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/facetime/"

        json_data = {
            'video_priority': video_priority
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_facetime_id2(self, node_type: str, node_id: str) -> Response:
        """Delete facetime.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/facetime/"

        return await self.delete(url)

    async def ucc_config_get_aruba_sip_id6(self, node_type: str, node_id: str) -> Response:
        """Retrieve sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        return await self.get(url)

    async def ucc_config_post_aruba_sip_id5(self, node_type: str, node_id: str,
                                            video_priority: int, voice_priority: int) -> Response:
        """Create sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of SIP application.
            voice_priority (int): DSCP priority to be applied to voice calls of SIP application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_sip_id5(self, node_type: str, node_id: str,
                                           video_priority: int, voice_priority: int) -> Response:
        """Create/Update sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of SIP application.
            voice_priority (int): DSCP priority to be applied to voice calls of SIP application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_sip_id5(self, node_type: str, node_id: str) -> Response:
        """Delete sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        return await self.delete(url)

    async def ucc_config_get_aruba_skype4b_id1(self, node_type: str, node_id: str) -> Response:
        """Retrieve skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        return await self.get(url)

    async def ucc_config_post_aruba_skype4b_id1(self, node_type: str, node_id: str,
                                                app_sharing_priority: int, video_priority: int,
                                                voice_priority: int,
                                                skype_server_certificate_domain_name: str) -> Response:
        """Create skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            app_sharing_priority (int): DSCP priority to be applied to app sharing calls of Skype
                for business application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            skype_server_certificate_domain_name (str): SDN server for Skype for business
                application; it is in FQDN format.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'app_sharing_priority': app_sharing_priority,
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'skype_server_certificate_domain_name': skype_server_certificate_domain_name
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_skype4b_id1(self, node_type: str, node_id: str,
                                               app_sharing_priority: int, video_priority: int,
                                               voice_priority: int,
                                               skype_server_certificate_domain_name: str) -> Response:
        """Create/Update skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            app_sharing_priority (int): DSCP priority to be applied to app sharing calls of Skype
                for business application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            skype_server_certificate_domain_name (str): SDN server for Skype for business
                application; it is in FQDN format.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'app_sharing_priority': app_sharing_priority,
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'skype_server_certificate_domain_name': skype_server_certificate_domain_name
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_skype4b_id1(self, node_type: str, node_id: str) -> Response:
        """Delete skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        return await self.delete(url)

    async def ucc_config_get_aruba_ucc_settings_id9(self, node_type: str, node_id: str) -> Response:
        """Retrieve ucc_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/"

        return await self.get(url)

    async def ucc_config_post_aruba_ucc_settings_id8(self, node_type: str, node_id: str,
                                                     activate: bool,
                                                     enable_call_prioritization: bool) -> Response:
        """Create ucc_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/"

        json_data = {
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_ucc_settings_id8(self, node_type: str, node_id: str,
                                                    activate: bool,
                                                    enable_call_prioritization: bool) -> Response:
        """Create/Update ucc_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/"

        json_data = {
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_ucc_settings_id8(self, node_type: str, node_id: str) -> Response:
        """Delete ucc_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/"

        return await self.delete(url)

    async def ucc_config_get_aruba_node_list_id11(self, node_type: str, node_id: str) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def ucc_config_get_aruba_dns_patterns_id3(self, node_type: str, node_id: str,
                                                    dns_pattern: str) -> Response:
        """Retrieve dns_patterns by identifier dns_pattern.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        return await self.get(url)

    async def ucc_config_post_aruba_dns_patterns_id3(self, node_type: str, node_id: str,
                                                     dns_pattern: str,
                                                     carrier_service_provider: str,
                                                     new_dns_pattern: str) -> Response:
        """Create dns_patterns by identifier dns_pattern.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.
            carrier_service_provider (str): Enter service provider name for enhanced visibility.
                Enter NA otherwise.
            new_dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        json_data = {
            'carrier_service_provider': carrier_service_provider,
            'new_dns_pattern': new_dns_pattern
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_dns_patterns_id3(self, node_type: str, node_id: str,
                                                    dns_pattern: str,
                                                    carrier_service_provider: str,
                                                    new_dns_pattern: str) -> Response:
        """Create/Update dns_patterns by identifier dns_pattern.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.
            carrier_service_provider (str): Enter service provider name for enhanced visibility.
                Enter NA otherwise.
            new_dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        json_data = {
            'carrier_service_provider': carrier_service_provider,
            'new_dns_pattern': new_dns_pattern
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_dns_patterns_id3(self, node_type: str, node_id: str,
                                                       dns_pattern: str) -> Response:
        """Delete dns_patterns by identifier dns_pattern.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        return await self.delete(url)

    async def ucc_config_get_aruba_config_id10(self, node_type: str, node_id: str) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def ucc_config_post_aruba_config_id9(self, node_type: str, node_id: str,
                                               video_priority: int, activate: bool,
                                               enable_call_prioritization: bool) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'video_priority': video_priority,
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_config_id9(self, node_type: str, node_id: str,
                                              video_priority: int, activate: bool,
                                              enable_call_prioritization: bool) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'video_priority': video_priority,
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_config_id9(self, node_type: str, node_id: str) -> Response:
        """Delete config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def ucc_config_get_aruba_wifi_calling_id5(self, node_type: str, node_id: str) -> Response:
        """Retrieve wifi_calling.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/"

        return await self.get(url)

    async def ucc_config_post_aruba_wifi_calling_id4(self, node_type: str, node_id: str,
                                                     voice_priority: int, dns_patterns: list) -> Response:
        """Create wifi_calling.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Wifi Calling
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/"

        json_data = {
            'voice_priority': voice_priority,
            'dns_patterns': dns_patterns
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_wifi_calling_id4(self, node_type: str, node_id: str,
                                                    voice_priority: int, dns_patterns: list) -> Response:
        """Create/Update wifi_calling.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Wifi Calling
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/"

        json_data = {
            'voice_priority': voice_priority,
            'dns_patterns': dns_patterns
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_wifi_calling_id4(self, node_type: str, node_id: str) -> Response:
        """Delete wifi_calling.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/"

        return await self.delete(url)

    async def ucc_config_get_aruba_ucc_alg_id7(self, node_type: str, node_id: str) -> Response:
        """Retrieve ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        return await self.get(url)

    async def ucc_config_post_aruba_ucc_alg_id6(self, node_type: str, node_id: str,
                                                video_priority: int, app_sharing_priority: int,
                                                voice_priority: int,
                                                skype_server_certificate_domain_name: str,
                                                dns_patterns: list) -> Response:
        """Create ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.
            app_sharing_priority (int): DSCP priority to be applied to app sharing calls of Skype
                for business application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            skype_server_certificate_domain_name (str): SDN server for Skype for business
                application; it is in FQDN format.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'video_priority': video_priority,
            'app_sharing_priority': app_sharing_priority,
            'voice_priority': voice_priority,
            'skype_server_certificate_domain_name': skype_server_certificate_domain_name,
            'dns_patterns': dns_patterns
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_ucc_alg_id6(self, node_type: str, node_id: str,
                                               video_priority: int, app_sharing_priority: int,
                                               voice_priority: int,
                                               skype_server_certificate_domain_name: str,
                                               dns_patterns: list) -> Response:
        """Create/Update ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to all calls of FaceTime application.
            app_sharing_priority (int): DSCP priority to be applied to app sharing calls of Skype
                for business application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            skype_server_certificate_domain_name (str): SDN server for Skype for business
                application; it is in FQDN format.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'video_priority': video_priority,
            'app_sharing_priority': app_sharing_priority,
            'voice_priority': voice_priority,
            'skype_server_certificate_domain_name': skype_server_certificate_domain_name,
            'dns_patterns': dns_patterns
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_ucc_alg_id6(self, node_type: str, node_id: str) -> Response:
        """Delete ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        return await self.delete(url)

    async def ucc_config_get_aruba_activate_id8(self, node_type: str, node_id: str) -> Response:
        """Retrieve activate.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/activate/"

        return await self.get(url)

    async def ucc_config_post_aruba_activate_id7(self, node_type: str, node_id: str,
                                                 activate: bool) -> Response:
        """Create activate.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/activate/"

        json_data = {
            'activate': activate
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_activate_id7(self, node_type: str, node_id: str,
                                                activate: bool) -> Response:
        """Create/Update activate.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/activate/"

        json_data = {
            'activate': activate
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_activate_id7(self, node_type: str, node_id: str) -> Response:
        """Delete activate.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_settings/activate/"

        return await self.delete(url)

    async def topology_external_display_topology(self, site_id: int) -> Response:
        """Get topology details of a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/{site_id}"

        return await self.get(url)

    async def topology_external_display_devices(self, device_serial: str) -> Response:
        """Get details of a device.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/devices/{device_serial}"

        return await self.get(url)

    async def topology_external_display_edges(self, source_serial: str, dest_serial: str) -> Response:
        """Get details of an edge.

        Args:
            source_serial (str): Device serial number.
            dest_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/edges/{source_serial}/{dest_serial}"

        return await self.get(url)

    async def topology_external_display_edges_v2(self, source_serial: str, dest_serial: str) -> Response:
        """Get details of an edge for the selected source and destination.

        Args:
            source_serial (str): Device serial number.
            dest_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/v2/edges/{source_serial}/{dest_serial}"

        return await self.get(url)

    async def topology_external_display_uplinks(self, source_serial: str, uplink_id: str) -> Response:
        """Get details of an uplink.

        Args:
            source_serial (str): Device serial number.
            uplink_id (str): Uplink id.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/uplinks/{source_serial}/{uplink_id}"

        return await self.get(url)

    async def topology_external_display_gettunnel(self, site_id: int, tunnel_map_names: List[str]) -> Response:
        """Get tunnel details.

        Args:
            site_id (int): Site ID.
            tunnel_map_names (List[str]): Comma separated list of tunnel map names.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/tunnels/{site_id}"

        params = {
            'tunnel_map_names': tunnel_map_names
        }

        return await self.get(url, params=params)

    async def topology_external_display_ap_neighbors(self, device_serial: str) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{device_serial}"

        return await self.get(url)

    async def topology_external_display_vlans(self, site_id: int, search: str = None,
                                              offset: int = 0, limit: int = 100) -> Response:
        """Get vlan list of a site.

        Args:
            site_id (int): Site ID.
            search (str, optional): search.
            offset (int, optional): offset. Defaults to 0.
            limit (int, optional): limit Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/vlans/{site_id}"

        params = {
            'search': search,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def topology_external_display_expiring_devices(self, site_id: int) -> Response:
        """Get list of unreachable devices in a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/unreachableDevices/{site_id}"

        return await self.get(url)

    async def troubleshooting_get_commands_list(self, device_type: str) -> Response:
        """List Troubleshooting Commands.

        Args:
            device_type (str): Specify one of "IAP" for swarm, "MAS" for MAS switches, "SWITCH" for
                aruba switches, "CONTROLLER" for controllers respectively.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/troubleshooting/v1/commands"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def troubleshooting_start_troubleshoot(self, serial: str, device_type: str,
                                                 commands: list) -> Response:
        """Start Troubleshooting Session.

        Args:
            serial (str): Serial of device
            device_type (str): Specify one of "IAP/SWITCH/MAS/CONTROLLER" for  IAPs, Aruba switches,
                MAS switches and controllers respectively.
            commands (list): List of commands

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        json_data = {
            'device_type': device_type,
            'commands': commands
        }

        return await self.post(url, json_data=json_data)

    async def troubleshooting_get_troubleshoot_output(self, serial: str, session_id: int) -> Response:
        """Get Troubleshooting Output.

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

        return await self.get(url, params=params)

    async def troubleshooting_clear_session(self, serial: str, session_id: int) -> Response:
        """Clear Troubleshooting Session.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for each troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        return await self.delete(url)

    async def troubleshooting_get_session_id(self, serial: str) -> Response:
        """Get Troubleshooting Session ID.

        Args:
            serial (str): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/session"

        return await self.get(url)

    async def troubleshooting_export_output(self, serial: str, session_id: int) -> Response:
        """Export Troubleshooting Output.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for each troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/export"

        return await self.get(url)

    async def tools_send_enroll_pki_certificate_switch(self, serial: str, est_profile_name: str,
                                                       cert_name: str) -> Response:
        """Action command for enroll est certificate.

        Args:
            serial (str): Serial of device
            est_profile_name (str): Name of the EST profile
            cert_name (str): Name of the Certificate

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/tools/action_cmd/device/{serial}/enroll_est_cert"

        json_data = {
            'est_profile_name': est_profile_name,
            'cert_name': cert_name
        }

        return await self.post(url, json_data=json_data)

    async def ucc_get_uc_summary(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch Summary.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/summary"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_clients(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch number of Clients.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/client/count"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_count_by_st(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch session counts based on session type.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/session/trend"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_session_count_by_protocol(self, start_time: int, end_time: int,
                                                label: str = None) -> Response:
        """Fetch session counts based on alg name.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/session/count/alg"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_sq_by_st(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch session quality based on session type.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/session/quality/type"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_sq_by_ssid(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch session quality based on ssid.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/session/quality/ssid"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_insights_count(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Fetch number of insights for a day.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/insights/count"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_insights(self, start_time: int, end_time: int, label: str = None,
                                  offset: int = 0, limit: int = 100) -> Response:
        """Fetch insights for a day. start time 00:00:00 and end time 23:59:59.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all
            offset (int, optional): Pagination offset, default is 0 Defaults to 0.
            limit (int, optional): Pagination limit. Default is 10 and max is 50 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/insights"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_cdrs(self, start_time: int, end_time: int, label: str = None,
                              offset: int = 0, limit: int = 100) -> Response:
        """Fetch list of CDRs.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all
            offset (int, optional): Pagination offset, default is 0 Defaults to 0.
            limit (int, optional): Pagination limit. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/cdr/list"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def ucc_export_uc_cdrs(self, start_time: int, end_time: int, label: str = None) -> Response:
        """Export list of CDRs.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): label id to include set of devices. Default value for label is
                all

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/cdr/export"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def ucc_get_uc_skype_elb(self) -> Response:
        """Fetch skype server central termination URL.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/SkypeCentralURL"

        return await self.get(url)

    async def platform_get_user_accounts(self, app_name: str = None, type: str = None,
                                         status: str = None, order_by: str = None,
                                         offset: int = 0, limit: int = 100) -> Response:
        """List user accounts.

        Args:
            app_name (str, optional): Filter users based on app_name
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

        return await self.get(url, params=params)

    async def platform_create_user_account(self, username: str = None, password: str = None,
                                           description: str = None, firstname: str = None,
                                           lastname: str = None, phone: str = None,
                                           street: str = None, city: str = None,
                                           state: str = None, country: str = None,
                                           zipcode: str = None, applications: list = None) -> Response:
        """Create a user account.

        Args:
            username (str, optional): name of user
            password (str, optional): password of user account
            description (str, optional): description of user
            firstname (str, optional): firstname
            lastname (str, optional): lastname
            phone (str, optional): Phone number. Format: +country_code-local_number
            street (str, optional): street
            city (str, optional): city
            state (str, optional): state
            country (str, optional): country
            zipcode (str, optional): zipcode
            applications (list, optional): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/users"

        json_data = {
            'username': username,
            'password': password,
            'description': description,
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'street': street,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'applications': applications
        }

        return await self.post(url, json_data=json_data)

    async def platform_update_user_account(self, user_id: str, username: str = None,
                                           description: str = None, firstname: str = None,
                                           lastname: str = None, phone: str = None,
                                           street: str = None, city: str = None,
                                           state: str = None, country: str = None,
                                           zipcode: str = None, applications: list = None) -> Response:
        """update user account details specified by user id.Providing info on account setting app is
        mandatory in this API along with other subscribed apps.Scope must be given only for NMS app.
        For non-nms apps such as account setting refer the parameters in the example json payload.

        Args:
            user_id (str): User's email id is specified as the user id
            username (str, optional): name of user
            description (str, optional): description of user
            firstname (str, optional): firstname
            lastname (str, optional): lastname
            phone (str, optional): Phone number. Format: +country_code-local_number
            street (str, optional): street
            city (str, optional): city
            state (str, optional): state
            country (str, optional): country
            zipcode (str, optional): zipcode
            applications (list, optional): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        json_data = {
            'username': username,
            'description': description,
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'street': street,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'applications': applications
        }

        return await self.patch(url, json_data=json_data)

    async def platform_get_user_account_details(self, user_id: str, system_user: bool = True) -> Response:
        """Get user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': system_user
        }

        return await self.get(url, params=params)

    async def platform_delete_user_account(self, user_id: str, system_user: bool = True) -> Response:
        """delete user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': system_user
        }

        return await self.delete(url, params=params)

    async def platform_change_user_password(self, current_password: str, new_password: str,
                                            user_id: str) -> Response:
        """Change user password.

        Args:
            current_password (str): current password
            new_password (str): new password
            user_id (str): User's email id is specified as the user id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}/password"

        json_data = {
            'current_password': current_password,
            'new_password': new_password
        }

        return await self.post(url, json_data=json_data)

    async def platform_reset_user_password(self, password: str, user_id: str) -> Response:
        """Reset user password.

        Args:
            password (str): password
            user_id (str): User's email id is specified as the user id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}/password/reset"

        json_data = {
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def platform_create_bulk_users_account(self, NoName: list = None) -> Response:
        """Create multiple users account. The max no of accounts that can be created at once is 10.

        Args:
            NoName (list, optional): List of user attributes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.post(url)

    async def platform_update_bulk_users_account(self, NoName: list = None) -> Response:
        """Update multiple users account. The max no of accounts that can be updated at once is
        10.Providing role on account setting app is mandatory in this API along with other
        subscribed apps. Scope must be given only for NMS app. For non-nms apps such as account
        setting refer the parameters in the example json payload.

        Args:
            NoName (list, optional): List of user attributes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.patch(url)

    async def platform_delete_bulk_users_account(self, NoName: List[str] = None) -> Response:
        """Delete multiple users account. The max no of accounts that can be deleted at once is 10.

        Args:
            NoName (List[str], optional): List of user id's to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.delete(url)

    async def platform_bulk_users_get_cookie_status(self, cookie_name: str) -> Response:
        """Get task status.

        Args:
            cookie_name (str): Specify the name of the cookie received after doing bulk operation.
                This status will be available for 1 hour.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/status/{cookie_name}"

        return await self.get(url)

    async def platform_get_roles(self, app_name: str = None, order_by: str = None,
                                 offset: int = 0, limit: int = 100) -> Response:
        """Get list of all roles.

        Args:
            app_name (str, optional): Filter users based on app_name
            order_by (str, optional): Sort ordering. +rolename means ascending order of rolename
                Valid Values: +rolename, -rolename
            offset (int, optional): Zero based offset to start from Defaults to 0.
            limit (int, optional): Maximum number of items to return Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/roles"

        params = {
            'app_name': app_name,
            'order_by': order_by,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_get_role(self, rolename: str, app_name: str) -> Response:
        """Get Role details.

        Args:
            rolename (str): role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.get(url)

    async def platform_delete_role(self, rolename: str, app_name: str) -> Response:
        """Delete a  role.

        Args:
            rolename (str): User role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.delete(url)

    async def platform_update_role(self, rolename: str, app_name: str, new_rolename: str,
                                   permission: str, applications: list) -> Response:
        """Update a role.

        Args:
            rolename (str): User role name
            app_name (str): app name
            new_rolename (str): name of the role
            permission (str): permission of the role
            applications (list): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        json_data = {
            'new_rolename': new_rolename,
            'permission': permission,
            'applications': applications
        }

        return await self.patch(url, json_data=json_data)

    async def platform_create_role(self, rolename: str, permission: str, applications: list,
                                   app_name: str) -> Response:
        """Create a role in an app.

        Args:
            rolename (str): name of the role
            permission (str): permission of the role
            applications (list): applications
            app_name (str): app name where role needs to be created

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles"

        json_data = {
            'rolename': rolename,
            'permission': permission,
            'applications': applications
        }

        return await self.post(url, json_data=json_data)

    async def platform_get_user_accounts(self, app_name: str = None, type: str = None,
                                         status: str = None, order_by: str = None,
                                         offset: int = 0, limit: int = 100) -> Response:
        """List user accounts.

        Args:
            app_name (str, optional): Filter users based on app_name
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

        return await self.get(url, params=params)

    async def platform_create_user_account(self, username: str = None, password: str = None,
                                           description: str = None, firstname: str = None,
                                           lastname: str = None, phone: str = None,
                                           street: str = None, city: str = None,
                                           state: str = None, country: str = None,
                                           zipcode: str = None, applications: list = None) -> Response:
        """Create a user account.

        Args:
            username (str, optional): name of user
            password (str, optional): password of user account
            description (str, optional): description of user
            firstname (str, optional): firstname
            lastname (str, optional): lastname
            phone (str, optional): Phone number. Format: +country_code-local_number
            street (str, optional): street
            city (str, optional): city
            state (str, optional): state
            country (str, optional): country
            zipcode (str, optional): zipcode
            applications (list, optional): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/users"

        json_data = {
            'username': username,
            'password': password,
            'description': description,
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'street': street,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'applications': applications
        }

        return await self.post(url, json_data=json_data)

    async def platform_update_user_account(self, user_id: str, username: str = None,
                                           description: str = None, firstname: str = None,
                                           lastname: str = None, phone: str = None,
                                           street: str = None, city: str = None,
                                           state: str = None, country: str = None,
                                           zipcode: str = None, applications: list = None) -> Response:
        """update user account details specified by user id.Providing info on account setting app is
        mandatory in this API along with other subscribed apps.Scope must be given only for NMS app.
        For non-nms apps such as account setting refer the parameters in the example json payload.

        Args:
            user_id (str): User's email id is specified as the user id
            username (str, optional): name of user
            description (str, optional): description of user
            firstname (str, optional): firstname
            lastname (str, optional): lastname
            phone (str, optional): Phone number. Format: +country_code-local_number
            street (str, optional): street
            city (str, optional): city
            state (str, optional): state
            country (str, optional): country
            zipcode (str, optional): zipcode
            applications (list, optional): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        json_data = {
            'username': username,
            'description': description,
            'firstname': firstname,
            'lastname': lastname,
            'phone': phone,
            'street': street,
            'city': city,
            'state': state,
            'country': country,
            'zipcode': zipcode,
            'applications': applications
        }

        return await self.patch(url, json_data=json_data)

    async def platform_get_user_account_details(self, user_id: str, system_user: bool = True) -> Response:
        """Get user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': system_user
        }

        return await self.get(url, params=params)

    async def platform_delete_user_account(self, user_id: str, system_user: bool = True) -> Response:
        """delete user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': system_user
        }

        return await self.delete(url, params=params)

    async def platform_change_user_password(self, current_password: str, new_password: str,
                                            user_id: str) -> Response:
        """Change user password.

        Args:
            current_password (str): current password
            new_password (str): new password
            user_id (str): User's email id is specified as the user id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}/password"

        json_data = {
            'current_password': current_password,
            'new_password': new_password
        }

        return await self.post(url, json_data=json_data)

    async def platform_reset_user_password(self, password: str, user_id: str) -> Response:
        """Reset user password.

        Args:
            password (str): password
            user_id (str): User's email id is specified as the user id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}/password/reset"

        json_data = {
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def platform_create_bulk_users_account(self, NoName: list = None) -> Response:
        """Create multiple users account. The max no of accounts that can be created at once is 10.

        Args:
            NoName (list, optional): List of user attributes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.post(url)

    async def platform_update_bulk_users_account(self, NoName: list = None) -> Response:
        """Update multiple users account. The max no of accounts that can be updated at once is
        10.Providing role on account setting app is mandatory in this API along with other
        subscribed apps. Scope must be given only for NMS app. For non-nms apps such as account
        setting refer the parameters in the example json payload.

        Args:
            NoName (list, optional): List of user attributes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.patch(url)

    async def platform_delete_bulk_users_account(self, NoName: List[str] = None) -> Response:
        """Delete multiple users account. The max no of accounts that can be deleted at once is 10.

        Args:
            NoName (List[str], optional): List of user id's to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.delete(url)

    async def platform_bulk_users_get_cookie_status(self, cookie_name: str) -> Response:
        """Get task status.

        Args:
            cookie_name (str): Specify the name of the cookie received after doing bulk operation.
                This status will be available for 1 hour.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/status/{cookie_name}"

        return await self.get(url)

    async def platform_get_roles(self, app_name: str = None, order_by: str = None,
                                 offset: int = 0, limit: int = 100) -> Response:
        """Get list of all roles.

        Args:
            app_name (str, optional): Filter users based on app_name
            order_by (str, optional): Sort ordering. +rolename means ascending order of rolename
                Valid Values: +rolename, -rolename
            offset (int, optional): Zero based offset to start from Defaults to 0.
            limit (int, optional): Maximum number of items to return Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/roles"

        params = {
            'app_name': app_name,
            'order_by': order_by,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_get_role(self, rolename: str, app_name: str) -> Response:
        """Get Role details.

        Args:
            rolename (str): role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.get(url)

    async def platform_delete_role(self, rolename: str, app_name: str) -> Response:
        """Delete a  role.

        Args:
            rolename (str): User role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.delete(url)

    async def platform_update_role(self, rolename: str, app_name: str, new_rolename: str,
                                   permission: str, applications: list) -> Response:
        """Update a role.

        Args:
            rolename (str): User role name
            app_name (str): app name
            new_rolename (str): name of the role
            permission (str): permission of the role
            applications (list): applications

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        json_data = {
            'new_rolename': new_rolename,
            'permission': permission,
            'applications': applications
        }

        return await self.patch(url, json_data=json_data)

    async def platform_create_role(self, rolename: str, permission: str, applications: list,
                                   app_name: str) -> Response:
        """Create a role in an app.

        Args:
            rolename (str): name of the role
            permission (str): permission of the role
            applications (list): applications
            app_name (str): app name where role needs to be created

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles"

        json_data = {
            'rolename': rolename,
            'permission': permission,
            'applications': applications
        }

        return await self.post(url, json_data=json_data)


if __name__ == "__main__":
    central = AllCalls()
    # r = asyncio.run(central.platform_get_idp_source())  # works
    # r = asyncio.run(central.platform_get_roles())  # works
    # r = asyncio.run(central.platform_get_user_accounts()) # works
    # r = asyncio.run(central.configuration_get_groups_v2()) # worked list of lists group names only
    # r = asyncio.run(central.central_get_webhooks_())  # works
    # r = asyncio.run(central.central_get_webhook_item_("eb23ab62-3929-44cb-8672-d83815ca65ca"))  # works
    # r = asyncio.run(central.central_test_webhook("eb23ab62-3929-44cb-8672-d83815ca65ca"))  # works
    # r = asyncio.run(central.central_refresh_webhook_token_("eb23ab62-3929-44cb-8672-d83815ca65ca"))  # works
    # r = asyncio.run(central.device_management_get_snmp_connection_profile_list())  # works cop only
    # r = asyncio.run(central.firmware_get_model_families_list("CN71HKZ1CL"))  # works
    # r = asyncio.run(central.firmware_get_model_families_list(device_type="HP"))  # works only with device_type HP ?
    # r = asyncio.run(central.monitoring_get_mcs())  # works
    # r = asyncio.run(central.monitoring_get_mcs(site="Antigua", status="up"))  # works
    # r = asyncio.run(central.monitoring_get_mcs(status="down"))  # works
    # r = asyncio.run(central.platform_get_audit_logs(target="CN71HKZ1CL"))  # works
    r = asyncio.run(central.platform_get_audit_logs())  # works
    # r = asyncio.run(central.platform_get_audit_log_details(id="audit_trail_2020_12,AXaIvVUUJ-4_gUfQaJck"))  # works
    # r = asyncio.run(central.platform_get_audit_log_details(id="audit_trail_2020_12,AXaIvVUUJ-4_gUfQaJck"))  # ? 200 body: null
    # r = asyncio.run(central.auditlogs_get_audit_details(id="audit_trail_2020_12,AXaIvVUUJ-4_gUfQaJck"))  # ? 200 body: null
    # r = asyncio.run(central.monitoring_get_networks_v2())  # works, essid, security, type(emp/guest)
    # r = asyncio.run(central.monitoring_get_network_v2(network_name="BR1_employee"))  # works, same as above with client_count
    # r = asyncio.run(central.monitoring_get_networks_v2(calculate_client_count=True))  # works, client count needs to be str not bool
    print(r.status)
    try:
        print(asyncio.run(r._response.text()))
    except Exception as e:
        print(e)
        print(r.output)
