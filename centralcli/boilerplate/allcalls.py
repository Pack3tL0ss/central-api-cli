import sys
from pathlib import Path
from typing import Union, List


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

    async def platform_get_idp_metadata(
        self,
        domain: str,
    ) -> Response:
        """SAML Metadata for the given domain.

        Args:
            domain (str): domain name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/aaa_config/v1/authentication/profiles/metadata/{domain}"

        return await self.get(url)

    async def platform_get_idp_source(
        self,
        domain: str = 'None',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List IDP Authentication Sources.

        Args:
            domain (str, optional): Domain name. Defaults to None
            offset (int, optional): Zero based offset to start from. Defaults to 0
            limit (int, optional): Maximum number of items to return. Defaults to 100

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

    async def platform_add_idp_source(
        self,
        domain: str,
        login_url: str,
        logout_url: str,
        public_cert: str,
        entity_id: str,
    ) -> Response:
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

    async def platform_update_idp_source(
        self,
        domain: str,
        login_url: str,
        logout_url: str,
        public_cert: str,
        entity_id: str,
    ) -> Response:
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

    async def platform_delete_idp_source(
        self,
        domain: str,
    ) -> Response:
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

    async def platform_upload_metadata(
        self,
        domain: str,
        saml_meta_data: Union[Path, str],
    ) -> Response:
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

    async def platform_upload_certificate(
        self,
        domain: str,
        saml_certificate: Union[Path, str],
    ) -> Response:
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

    async def get_aiops_v1_connectivity_global_stage_export(
        self,
        stage: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """Wi-Fi Connectivity at Global.

        Args:
            stage (str): Connectivity Stage Name  Valid Values: all, association, authentication,
                dhcp, dns
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v1/connectivity/global/stage/{stage}/export"

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

    async def get_aiops_v1_connectivity_site_stage_export(
        self,
        site_id: int,
        stage: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """Wi-Fi Connectivity at Site.

        Args:
            site_id (int): Site ID
            stage (str): Connectivity Stage Name  Valid Values: all, association, authentication,
                dhcp, dns
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v1/connectivity/site/{site_id}/stage/{stage}/export"

        return await self.get(url)

    async def get_aiops_v1_connectivity_group_stage_export(
        self,
        group: str,
        stage: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """Wi-Fi Connectivity at Group.

        Args:
            group (str): Group Name
            stage (str): Connectivity Stage Name  Valid Values: all, association, authentication,
                dhcp, dns
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v1/connectivity/group/{group}/stage/{stage}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_global_list(
        self,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for a Network.

        Args:
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = "/aiops/v2/insights/global/list"

        params = {
            "from": from_ms,
            "to": to
        }

        return await self.get(url, params=params)

    async def get_aiops_v2_insights_site_list(
        self,
        site_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for a Site.

        Args:
            site_id (int): Site ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/site/{site_id}/list"

        return await self.get(url)

    async def get_aiops_v2_insights_ap_list(
        self,
        ap_serial: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for an AP.

        Args:
            ap_serial (str): AP Serial
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/ap/{ap_serial}/list"

        return await self.get(url)

    async def get_aiops_v2_insights_client_list(
        self,
        sta_mac: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for a Client.

        Args:
            sta_mac (str): Client Mac
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/client/{sta_mac}/list"

        return await self.get(url)

    async def get_aiops_v2_insights_gateway_list(
        self,
        gw_serial: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for a Gateway.

        Args:
            gw_serial (str): Gateway Serial
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/gateway/{gw_serial}/list"

        return await self.get(url)

    async def get_aiops_v2_insights_switch_list(
        self,
        sw_serial: str,
        from_ms: int,
        to: int,
    ) -> Response:
        """List AI Insights for a Switch.

        Args:
            sw_serial (str): Switch Serial
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/switch/{sw_serial}/list"

        return await self.get(url)

    async def get_aiops_v2_insights_global_id_export(
        self,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for a Network.

        Args:
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/global/id/{insight_id}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_site_id_export(
        self,
        site_id: int,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for a Site.

        Args:
            site_id (int): Site ID
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/site/{site_id}/id/{insight_id}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_ap_id_export(
        self,
        ap_serial: str,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for an AP.

        Args:
            ap_serial (str): AP Serial
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/ap/{ap_serial}/id/{insight_id}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_client_id_export(
        self,
        sta_mac: str,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for a Client.

        Args:
            sta_mac (str): Client Mac
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/client/{sta_mac}/id/{insight_id}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_gateway_id_export(
        self,
        gw_serial: str,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for a Gateway.

        Args:
            gw_serial (str): Gateway Serial
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/gateway/{gw_serial}/id/{insight_id}/export"

        return await self.get(url)

    async def get_aiops_v2_insights_switch_id_export(
        self,
        sw_serial: str,
        insight_id: int,
        from_ms: int,
        to: int,
    ) -> Response:
        """AI Insight Details for a Switch.

        Args:
            sw_serial (str): Switch Serial
            insight_id (int): Insight ID
            from_ms (int): Start time in epoch-milliseconds
            to (int): End time in epoch-milliseconds

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/aiops/v2/insights/switch/{sw_serial}/id/{insight_id}/export"

        return await self.get(url)

    async def auditlogs_get_audits(
        self,
        group_name: str = None,
        device_id: str = None,
        classification: str = None,
        start_time: int = None,
        end_time: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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
        print(params)

        return await self.get(url, params=params)

    async def auditlogs_get_audit_details(
        self,
        id: str,
    ) -> Response:
        """Get details of an audit event/log.

        Args:
            id (str): ID of audit event

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/auditlogs/v1/event_details/{id}"

        return await self.get(url)

    async def platform_get_audit_logs(
        self,
        username: str = None,
        start_time: int = None,
        end_time: int = None,
        description: str = None,
        target: str = None,
        classification: str = None,
        customer_name: str = None,
        ip_address: str = None,
        app_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all audit logs.

        Args:
            username (str, optional): Filter audit logs by User Name
            start_time (int, optional): Filter audit logs by Time Range. Start time of the audit
                logs should be provided in epoch seconds
            end_time (int, optional): Filter audit logs by Time Range. End time of the audit logs
                should be provided in epoch seconds
            description (str, optional): Filter audit logs by Description
            target (str, optional): Filter audit logs by target
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

    async def platform_get_audit_log_details(
        self,
        id: str,
    ) -> Response:
        """Get details of an audit log.

        Args:
            id (str): ID of audit event

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/auditlogs/v1/logs/{id}"

        return await self.get(url)

    async def cloudauth_read_client_policy(
        self,
    ) -> Response:
        """Fetch network access policy for registered clients.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_policy"

        return await self.get(url)

    async def cloudauth_update_client_policy(
        self,
        rules: list,
        unprofiled_client_role: str,
    ) -> Response:
        """Configure or update network access policy for registered clients.

        Args:
            rules (list): Mapping rules of Client Profile Tags to Client Roles.
            unprofiled_client_role (str): Client Role for clients that are not profiled or do not
                have any Client Profile Tag.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_policy"

        json_data = {
            'rules': rules,
            'unprofiled_client_role': unprofiled_client_role
        }

        return await self.put(url, json_data=json_data)

    async def cloudauth_delete_client_policy(
        self,
    ) -> Response:
        """Delete existing Client Policy.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_policy"

        return await self.delete(url)

    async def cloudauth_read_client_registration(
        self,
        mac_prefix: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Fetch list of registered clients.

        Args:
            mac_prefix (str, optional): Search for entries starting with MAC Address prefix
            offset (int, optional): Number of clients to be skipped before returning the data,
                useful for pagination. Defaults to 0.
            limit (int, optional): Maximum number of registered clients to be returned. Allowed
                range is 1 to 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_registration"

        params = {
            'mac_prefix': mac_prefix,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def cloudauth_add_client_registration(
        self,
        client_name: str,
        mac_address: str,
    ) -> Response:
        """Add registered client.

        Args:
            client_name (str): Display name of the registered client
            mac_address (str): MAC Address of the registered client.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_registration"

        json_data = {
            'client_name': client_name,
            'mac_address': mac_address
        }

        return await self.post(url, json_data=json_data)

    async def cloudauth_delete_client_registration(
        self,
        mac_address: str,
    ) -> Response:
        """Delete registered client.

        Args:
            mac_address (str): The MAC Address of the Client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/client_registration/{mac_address}"

        return await self.delete(url)

    async def cloudauth_update_client_registration(
        self,
        mac_address: str,
        client_name: str,
    ) -> Response:
        """Update registered client name.

        Args:
            mac_address (str): The MAC Address of the Client
            client_name (str): Display name of the registered client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/client_registration/{mac_address}"

        json_data = {
            'client_name': client_name
        }

        return await self.patch(url, json_data=json_data)

    async def cloudauth_read_user_policy(
        self,
    ) -> Response:
        """Fetch policy that allows wireless network access for users.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/user_policy"

        return await self.get(url)

    async def cloudauth_update_user_policy(
        self,
        administrator_email: str,
        auth_provider_x509_cert_url: str,
        auth_uri: str,
        client_email: str,
        client_id: str,
        client_secret: str,
        client_x509_cert_url: str,
        customer_id: str,
        domain: str,
        open_id: str,
        private_key: str,
        private_key_id: str,
        project_id: str,
        token_uri: str,
        type: str,
        tenant_id: str,
        organization_name: str,
        rules: list,
        wlan_network: str,
    ) -> Response:
        """Configure policy to allow wireless network access for users.

        Args:
            administrator_email (str): Administrator Email
            auth_provider_x509_cert_url (str): Copy attribute with same name from JSON file
                downloaded from Google Workspace
            auth_uri (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            client_email (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            client_id (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            client_secret (str): Client Secret
            client_x509_cert_url (str): Copy attribute with same name from JSON file downloaded from
                Google Workspace
            customer_id (str): Customer ID
            domain (str): domain
            open_id (str): Open ID
            private_key (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            private_key_id (str): Copy attribute with same name from JSON file downloaded from
                Google Workspace
            project_id (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            token_uri (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            type (str): Copy attribute with same name from JSON file downloaded from Google
                Workspace
            tenant_id (str): Tenant ID
            organization_name (str): Organization name
            rules (list): Mapping rules of User Groups to Client Roles.
            wlan_network (str): WLAN network for clients that do not support Passpoint profiles.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/user_policy"

        json_data = {
            'administrator_email': administrator_email,
            'auth_provider_x509_cert_url': auth_provider_x509_cert_url,
            'auth_uri': auth_uri,
            'client_email': client_email,
            'client_id': client_id,
            'client_secret': client_secret,
            'client_x509_cert_url': client_x509_cert_url,
            'customer_id': customer_id,
            'domain': domain,
            'open_id': open_id,
            'private_key': private_key,
            'private_key_id': private_key_id,
            'project_id': project_id,
            'token_uri': token_uri,
            'type': type,
            'tenant_id': tenant_id,
            'organization_name': organization_name,
            'rules': rules,
            'wlan_network': wlan_network
        }

        return await self.put(url, json_data=json_data)

    async def cloudauth_delete_user_policy(
        self,
    ) -> Response:
        """Delete existing User Policy.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/user_policy"

        return await self.delete(url)

    async def device_management_send_command_to_device(
        self,
        serial: str,
        command: str,
    ) -> Response:
        """Generic commands for device.

        Args:
            serial (str): Serial of device
            command (str): Command mentioned in the description that is to be executed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/device/{serial}/action/{command}"

        return await self.post(url)

    async def device_management_send_multi_line_cmd(
        self,
        serial: str,
        command: str,
        port: str,
    ) -> Response:
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

    async def device_management_send_multi_line_cmd_v2(
        self,
        serial: str,
        command: str,
        port: str,
    ) -> Response:
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

    async def device_management_send_command_to_swarm(
        self,
        swarm_id: str,
        command: str,
    ) -> Response:
        """Generic commands for swarm.

        Args:
            swarm_id (str): Swarm ID of device
            command (str): Command mentioned in the description that is to be executed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/swarm/{swarm_id}/action/{command}"

        return await self.post(url)

    async def device_management_send_disconnect_user(
        self,
        serial: str,
        disconnect_user_mac: str,
        disconnect_user_all: bool,
        disconnect_user_network: str,
    ) -> Response:
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

    async def device_management_send_speed_test(
        self,
        serial: str,
        host: str,
        options: str,
    ) -> Response:
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

    async def device_management_get_command_status(
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

        return await self.get(url)

    async def device_management_assign_pre_provisioned_group(
        self,
        serials: List[str],
        group: str,
    ) -> Response:
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

    async def activate_move_devices(
        self,
        operation: str,
        devices: List[str],
        sync: bool = None,
    ) -> Response:
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

    async def device_management_activate_sync(
        self,
        mm_name: str,
    ) -> Response:
        """Trigger activate sync for given MobilityMaster.

        Args:
            mm_name (str): Mobility Master name previously set in ACP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{mm_name}/activate_sync"

        return await self.post(url)

    async def device_management_static_md_mm_assign(
        self,
        device_serial: str,
        mm_name: str,
    ) -> Response:
        """Statically assign Mobility Master to Mobility Device.

        Args:
            device_serial (str): Mobility Device serial.
            mm_name (str): Mobility Master name previously set in ACP.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}/{mm_name}"

        return await self.post(url)

    async def device_management_get_md_mm_mapping(
        self,
        device_serial: str,
    ) -> Response:
        """Get assigned Mobility Master to Mobility Device.

        Args:
            device_serial (str): Mobility Device serial.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}"

        return await self.get(url)

    async def device_management_del_md_mm_mapping(
        self,
        device_serial: str,
    ) -> Response:
        """Delete Mobility Master to Mobility Device mapping.

        Args:
            device_serial (str): Mobility Device serial.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/device_management/v1/mobility_master/{device_serial}"

        return await self.delete(url)

    async def central_get_webhooks_(
        self,
    ) -> Response:
        """List webhooks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"

        return await self.get(url)

    async def central_add_webhook_(
        self,
        name: str,
        urls: List[str],
    ) -> Response:
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

    async def central_get_webhook_item_(
        self,
        wid: str,
    ) -> Response:
        """Webhook setting for a specific item.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        return await self.get(url)

    async def central_delete_webhook_(
        self,
        wid: str,
    ) -> Response:
        """Delete Webhooks.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}"

        return await self.delete(url)

    async def central_update_webhook_(
        self,
        wid: str,
        name: str,
        urls: List[str],
    ) -> Response:
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

    async def central_get_webhook_token_(
        self,
        wid: str,
    ) -> Response:
        """Get Webhook Token.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/token"

        return await self.get(url)

    async def central_refresh_webhook_token_(
        self,
        wid: str,
    ) -> Response:
        """Refresh the webhook token.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/token"

        return await self.put(url)

    async def central_test_webhook(
        self,
        wid: str,
    ) -> Response:
        """Test for webhook notification.

        Args:
            wid (str): id of the webhook

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/webhooks/{wid}/ping"

        return await self.get(url)

    async def dps_monitoring_get_policy_stats(
        self,
        cluster_id: str,
        policy_name: str,
    ) -> Response:
        """Gets DPS Policy stats for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            policy_name (str): DPS compliance policy name.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policy/policy_stats/{policy_name}"

        return await self.get(url)

    async def dps_monitoring_getdpspolicystatshigherwindow(
        self,
        cluster_id: str,
        policy_name: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def dps_monitoring_getdpspolicieskpistats(
        self,
        cluster_id: str,
    ) -> Response:
        """DPS Key Performance Indicator for a given BOC.

        Args:
            cluster_id (str): cluster_id number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policies/kpi"

        return await self.get(url)

    async def dps_monitoring_getdpspoliciescompliancepercentage(
        self,
        cluster_id: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def dps_monitoring_getdpspoliciesstatus(
        self,
        cluster_id: str,
    ) -> Response:
        """DPS Compliance Status of all DPS Policies for a given BOC.

        Args:
            cluster_id (str): cluster_id number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policies/status"

        return await self.get(url)

    async def dps_monitoring_getdpspolicieseventlogs(
        self,
        cluster_id: str,
        policy_name: str,
    ) -> Response:
        """Gets DPS Policy Event Logs for a given BOC.

        Args:
            cluster_id (str): cluster_id number.
            policy_name (str): DPS compliance policy name.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/dps_monitoring_api/datapoints/v1/cluster/{cluster_id}/sdwan_policy/event_logs/{policy_name}"

        return await self.get(url)

    async def dps_monitoring_getdpssitepolicystats(
        self,
        site_name: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def gdpr_get_gdprs_(
        self,
    ) -> Response:
        """List gdprs opt out MAC clients for this customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/gdpr/v1/opt_out_clients"

        return await self.get(url)

    async def gdpr_add_(
        self,
        mac: str,
    ) -> Response:
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

    async def gdpr_get_mac(
        self,
        mac: str,
    ) -> Response:
        """GDPR Opt out MAC.

        Args:
            mac (str): mac address of the client to be opted out

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/gdpr/v1/opt_out_clients/{mac}"

        return await self.get(url)

    async def gdpr_delete_(
        self,
        mac: str,
    ) -> Response:
        """Delete Opt out Mac.

        Args:
            mac (str): mac address of the client to be opted out

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/gdpr/v1/opt_out_clients/{mac}"

        return await self.delete(url)

    async def install_manager_invite_installer(
        self,
        first_name: str,
        last_name: str,
        country_code: str,
        mobile_number: str,
        expire_at: int,
        allow_config: bool,
        sites: list,
    ) -> Response:
        """Invite a new installer.

        Args:
            first_name (str): First Name of Installer
            last_name (str): Last Name of Installer
            country_code (str): Country code of Installer mobile number
            mobile_number (str): Installer mobile number without spaces or special characters
            expire_at (int): Date upto which the installer should be given access. Value is in epoch
                seconds
            allow_config (bool): Allow the installer to add a device name during installation
            sites (list): The list of sites assigned to the installer

        Returns:
            Response: CentralAPI Response object
        """
        url = "/install_manager/external/v1/invite_installer"

        json_data = {
            'first_name': first_name,
            'last_name': last_name,
            'country_code': country_code,
            'mobile_number': mobile_number,
            'expire_at': expire_at,
            'allow_config': allow_config,
            'sites': sites
        }

        return await self.post(url, json_data=json_data)

    async def install_manager_assign_group_to_device_types_in_sites(
        self,
        groups_association: list,
        sites_association: list,
    ) -> Response:
        """For a given set of site names, assign Group Names for each device type.

        Args:
            groups_association (list): groups_association
            sites_association (list): sites_association

        Returns:
            Response: CentralAPI Response object
        """
        url = "/install_manager/external/v1/assign_group_to_device_types_in_sites"

        json_data = {
            'groups_association': groups_association,
            'sites_association': sites_association
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_searchappsusingget(
        self,
        collectorId: str = None,
        keywords: str = None,
        page: int = 0,
        size: int = 20,
    ) -> Response:
        """Search apps.

        Args:
            collectorId (str, optional): The unique Id of the collector to check whether App is
                installed
            keywords (str, optional): Open channel App categories like Industrial, Maintenance,
                Sensoring
            page (int, optional): Results page you want to retrieve (0…N)
            size (int, optional): Number of records per page.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/apps"

        params = {
            'collectorId': collectorId,
            'keywords': keywords,
            'page': page,
            'size': size
        }

        return await self.get(url, params=params)

    async def iot_operations_findallinstalledappsusingget(
        self,
        collectorId: str,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Find all installed apps.

        Args:
            collectorId (str): The unique Id of the collector to check whether App is installed
            page (int, optional): Results page you want to retrieve (0…N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/apps/installed"

        params = {
            'collectorId': collectorId,
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_countallinstalledappsusingget(
        self,
        collectorId: str,
    ) -> Response:
        """Count all installed apps.

        Args:
            collectorId (str): The unique Id of the collector to check whether App is installed

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/apps/installed/count"

        params = {
            'collectorId': collectorId
        }

        return await self.get(url, params=params)

    async def iot_operations_getappusingget(
        self,
        appId: str,
        collectorId: str = None,
        latestVersion: bool = False,
    ) -> Response:
        """Get App.

        Args:
            appId (str): App Id of App to be queried
            collectorId (str, optional): The unique Id of the collector to check whether App is
                installed
            latestVersion (bool, optional): Query the latest version of App

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}"

        params = {
            'collectorId': collectorId,
            'latestVersion': latestVersion
        }

        return await self.get(url, params=params)

    async def iot_operations_getappiconusingget(
        self,
        appId: str,
    ) -> Response:
        """Get App Icon.

        Args:
            appId (str): App Id of App to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}/icon"

        return await self.get(url)

    async def iot_operations_installappusingpost(
        self,
        appId: str,
        collectorId: str = None,
        subscriptions: list = None,
    ) -> Response:
        """Install app.

        Args:
            appId (str): App Id to be  Installed
            collectorId (str, optional): collectorId
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}/install"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_editinstalledappusingpost(
        self,
        appId: str,
        collectorId: str = None,
        subscriptions: list = None,
    ) -> Response:
        """Edit Installed app configuration.

        Args:
            appId (str): App Id to be  Edited
            collectorId (str, optional): collectorId
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}/install/edit"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_uninstallappusingdelete(
        self,
        appId: str,
        collectorId: str = None,
    ) -> Response:
        """Delete app.

        Args:
            appId (str): App Id to be Uninstalled
            collectorId (str, optional): collectorId

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}/uninstall"

        json_data = {
            'collectorId': collectorId
        }

        return await self.delete(url, json_data=json_data)

    async def iot_operations_upgradeappusingpost(
        self,
        appId: str,
        collectorId: str = None,
        subscriptions: list = None,
    ) -> Response:
        """Upgrade app.

        Args:
            appId (str): App Id to be Upgraded
            collectorId (str, optional): collectorId
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/apps/{appId}/upgrade"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_developerssearchappsusingget(
        self,
        collectorId: str = None,
        includeLiveVersion: bool = False,
        keywords: str = None,
    ) -> Response:
        """Developer apps.

        Args:
            collectorId (str, optional): The unique Id of the collector to check whether App is
                installed
            includeLiveVersion (bool, optional): Should the live version for apps be included?
            keywords (str, optional): Not available for use

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/developers/apps"

        params = {
            'collectorId': collectorId,
            'includeLiveVersion': includeLiveVersion,
            'keywords': keywords
        }

        return await self.get(url, params=params)

    async def iot_operations_editdeveloperinstalledappusingpost(
        self,
        appId: str,
        collectorId: str,
        subscriptions: list = None,
    ) -> Response:
        """Edit Developer installed app configuration.

        Args:
            appId (str): App Id of App to be Edited
            collectorId (str): collectorId
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/install/edit"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_getdeveloperappusingget(
        self,
        appId: str,
        version: int,
        collectorId: str = None,
    ) -> Response:
        """Get Developer App.

        Args:
            appId (str): App Id of App to be queried
            version (int): App version
            collectorId (str, optional): The unique Id of the collector to check whether App is
                installed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/versions/{version}"

        params = {
            'collectorId': collectorId
        }

        return await self.get(url, params=params)

    async def iot_operations_getdeveloperappiconusingget(
        self,
        appId: str,
        version: int,
    ) -> Response:
        """Get Developer App Icon.

        Args:
            appId (str): App Id of App to be queried
            version (int): Version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/versions/{version}/icon"

        return await self.get(url)

    async def iot_operations_installdeveloperappusingpost(
        self,
        appId: str,
        collectorId: str,
        version: int,
        subscriptions: list = None,
    ) -> Response:
        """Install Developer app.

        Args:
            appId (str): App Id of App to be Installed
            collectorId (str): collectorId
            version (int): App version
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/versions/{version}/install"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_uninstalldeveloperappusingdelete(
        self,
        appId: str,
        collectorId: str,
        version: int,
    ) -> Response:
        """Delete Developer app.

        Args:
            appId (str): App Id of App to be Uninstalled
            collectorId (str): collectorId
            version (int): App version

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/versions/{version}/uninstall"

        json_data = {
            'collectorId': collectorId
        }

        return await self.delete(url, json_data=json_data)

    async def iot_operations_upgradedeveloperappusingpost(
        self,
        appId: str,
        collectorId: str,
        version: int,
        subscriptions: list = None,
    ) -> Response:
        """Upgrade developer app.

        Args:
            appId (str): App Id of App to be Upgraded
            collectorId (str): collectorId
            version (int): App version
            subscriptions (list, optional): subscriptions

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/appstore/developers/apps/{appId}/versions/{version}/upgrade"

        json_data = {
            'collectorId': collectorId,
            'subscriptions': subscriptions
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_developerinfousingget(
        self,
    ) -> Response:
        """Developer info.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/developers/info"

        return await self.get(url)

    async def iot_operations_findallrecommendedappsusingget(
        self,
        collectorId: str = None,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
        type: str = None,
    ) -> Response:
        """Find Recommended Apps.

        Args:
            collectorId (str, optional): The unique Id of the collector to check whether App is
                installed
            page (int, optional): Results page you want to retrieve (0…N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.
            type (str, optional): Open channel App type

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/appstore/recommendations"

        params = {
            'collectorId': collectorId,
            'page': page,
            'size': size,
            'sort': sort,
            'type': type
        }

        return await self.get(url, params=params)

    async def iot_operations_getalldevicesusingget(
        self,
        collectorId: List[str] = None,
        deviceAddress: str = None,
        deviceClasses: List[str] = None,
        deviceType: str = None,
        page: int = 0,
        since: str = None,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of all devices.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            deviceAddress (str, optional): Device Address
            deviceClasses (List[str], optional): Device Classes
            deviceType (str, optional): Device Type  Valid Values: BLE, ZIGBEE, UNRECOGNIZED
            page (int, optional): Results page you want to retrieve (0…N)
            since (str, optional): Start time - End time range in ISO timestamp
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices"

        params = {
            'collectorId': collectorId,
            'deviceAddress': deviceAddress,
            'deviceClasses': deviceClasses,
            'deviceType': deviceType,
            'page': page,
            'since': since,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_getalldevicesbyattributeusingget(
        self,
        attName: str = None,
        attValue: str = '*',
        collectorId: List[str] = None,
        page: int = 0,
        since: str = None,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of all devices.

        Args:
            attName (str, optional): Device attribute name
            attValue (str, optional): Device attribute value
            collectorId (List[str], optional): The unique Id of the collector
            page (int, optional): Results page you want to retrieve (0…N)
            since (str, optional): Start time - End time range in ISO timestamp
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/attribute"

        params = {
            'attName': attName,
            'attValue': attValue,
            'collectorId': collectorId,
            'page': page,
            'since': since,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_getdeviceclassifiedcountusingget(
        self,
        collectorId: List[str] = None,
        deviceType: str = None,
        since: str = None,
    ) -> Response:
        """Return the count of devices with one or more device classes.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            deviceType (str, optional): Device Type  Valid Values: BLE, ZIGBEE, UNRECOGNIZED
            since (str, optional): Start time - End time range in ISO timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/statistics/classified/count"

        params = {
            'collectorId': collectorId,
            'deviceType': deviceType,
            'since': since
        }

        return await self.get(url, params=params)

    async def iot_operations_getdevicecountusingget(
        self,
        collectorId: List[str] = None,
        since: str = None,
    ) -> Response:
        """Return the count of devices.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            since (str, optional): Start time - End time range in ISO timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/statistics/count"

        params = {
            'collectorId': collectorId,
            'since': since
        }

        return await self.get(url, params=params)

    async def iot_operations_getdeviceclassifiedstatisticsusingget(
        self,
        collectorId: List[str] = None,
        deviceType: str = None,
        since: str = None,
    ) -> Response:
        """Return the count of devices by Device Class.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            deviceType (str, optional): Device Type  Valid Values: BLE, ZIGBEE, UNRECOGNIZED
            since (str, optional): Start time - End time range in ISO timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/statistics/device_classes/count"

        params = {
            'collectorId': collectorId,
            'deviceType': deviceType,
            'since': since
        }

        return await self.get(url, params=params)

    async def iot_operations_getreporterscountusingget(
        self,
        collectorId: List[str] = None,
        since: str = None,
    ) -> Response:
        """Return the count of devices reporters by Collector.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            since (str, optional): Start time - End time range in ISO timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/statistics/reporters/count"

        params = {
            'collectorId': collectorId,
            'since': since
        }

        return await self.get(url, params=params)

    async def iot_operations_getdevicecountbytypeusingget(
        self,
        collectorId: List[str] = None,
        since: str = None,
    ) -> Response:
        """Return the count of devices by type.

        Args:
            collectorId (List[str], optional): The unique Id of the collector
            since (str, optional): Start time - End time range in ISO timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/statistics/types/count"

        params = {
            'collectorId': collectorId,
            'since': since
        }

        return await self.get(url, params=params)

    async def iot_operations_getdevicecountbycollectoridusingget(
        self,
        endTime: str,
        startTime: str,
        aggregation: int = None,
        collectorId: List[str] = None,
        type: str = None,
    ) -> Response:
        """Return a time-series device count by collectorId.

        Args:
            endTime (str): End time
            startTime (str): Start time
            aggregation (int, optional): Aggregation time
            collectorId (List[str], optional): The unique Id of the collector
            type (str, optional): Device Type  Valid Values: BLE, ZIGBEE, UNRECOGNIZED

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/devices/timeseries/count_device"

        params = {
            'endTime': endTime,
            'startTime': startTime,
            'aggregation': aggregation,
            'collectorId': collectorId,
            'type': type
        }

        return await self.get(url, params=params)

    async def iot_operations_getdeviceusingget(
        self,
        deviceId: str,
    ) -> Response:
        """Return a device by Id.

        Args:
            deviceId (str): The unique Device Id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/devices/{deviceId}"

        return await self.get(url)

    async def iot_operations_getdeviceattributesusingget(
        self,
        deviceId: str,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of Attributes.

        Args:
            deviceId (str): The unique Device Id
            page (int, optional): Results page you want to retrieve (0…N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/devices/{deviceId}/attributes"

        params = {
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_getdevicetimeseriesmetricsusingget(
        self,
        deviceId: str,
        endTime: str,
        startTime: str,
        aggregation: int = None,
        collectorId: str = None,
        metrics: List[str] = None,
        reporter: str = None,
    ) -> Response:
        """Return the time-series from device.

        Args:
            deviceId (str): The unique Device Id
            endTime (str): End time
            startTime (str): Start time
            aggregation (int, optional): Aggregation time
            collectorId (str, optional): The unique Id of the collector
            metrics (List[str], optional): Metrics  Valid Values: RSSI, BATTERY, ADVERTISING,
                COLLECTOR, LQI, RXPACKETS, RXBYTES, TXPACKETS, TXBYTES
            reporter (str, optional): Reporter MacAddress

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/devices/{deviceId}/timeseries"

        params = {
            'endTime': endTime,
            'startTime': startTime,
            'aggregation': aggregation,
            'collectorId': collectorId,
            'metrics': metrics,
            'reporter': reporter
        }

        return await self.get(url, params=params)

    async def iot_operations_getallgatewaysusingget(
        self,
        checkStatus: bool = True,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of Gateways.

        Args:
            checkStatus (bool, optional): Check collector status
            page (int, optional): Results page you want to retrieve (0..N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways"

        params = {
            'checkStatus': checkStatus,
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_getallassociationusingget(
        self,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of Gateways.

        Args:
            page (int, optional): Results page you want to retrieve (0..N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/association"

        params = {
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_addassociationusingpost(
        self,
        collectorId: str = None,
        collectorIp: str = None,
        reporterList: List[str] = None,
    ) -> Response:
        """Add Association.

        Args:
            collectorId (str, optional): collectorId
            collectorIp (str, optional): collectorIp
            reporterList (List[str], optional): reporterList

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/association"

        json_data = {
            'collectorId': collectorId,
            'collectorIp': collectorIp,
            'reporterList': reporterList
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_deleteassociationusingdelete(
        self,
        collectorId: str = None,
        reporterList: List[str] = None,
    ) -> Response:
        """Delete Association.

        Args:
            collectorId (str, optional): collectorId
            reporterList (List[str], optional): reporterList

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/association"

        json_data = {
            'collectorId': collectorId,
            'reporterList': reporterList
        }

        return await self.delete(url, json_data=json_data)

    async def iot_operations_getassociationforcollectorusingget(
        self,
        collectorId: str,
    ) -> Response:
        """Return Pageable List of Gateways.

        Args:
            collectorId (str): The unique Id of the collector

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/iot_gateways/association/collector/{collectorId}"

        return await self.get(url)

    async def iot_operations_getassociationtokenforcollectorusingget(
        self,
        collectorId: str,
    ) -> Response:
        """Returns security token associated with a collector.

        Args:
            collectorId (str): The unique Id of the collector

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/iot_gateways/association/token/{collectorId}"

        return await self.get(url)

    async def iot_operations_getgroupforconnectorusingget(
        self,
        connectorId: str,
    ) -> Response:
        """Returns connector to group mapping.

        Args:
            connectorId (str): The unique Id of the collector

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/iot_gateways/groups/connector/{connectorId}"

        return await self.get(url)

    async def iot_operations_moveusingpost(
        self,
        connectorList: List[str] = None,
        groupId: str = None,
    ) -> Response:
        """Group move.

        Args:
            connectorList (List[str], optional): connectorList
            groupId (str, optional): groupId

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/groups/move"

        json_data = {
            'connectorList': connectorList,
            'groupId': groupId
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_deleteusingdelete(
        self,
        connectorList: List[str] = None,
    ) -> Response:
        """Group move.

        Args:
            connectorList (List[str], optional): connectorList

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/groups/move"

        json_data = {
            'connectorList': connectorList
        }

        return await self.delete(url, json_data=json_data)

    async def iot_operations_getallonlinegatewaysusingget(
        self,
        checkStatus: bool = True,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Return Pageable List of Gateways.

        Args:
            checkStatus (bool, optional): Check collector status
            page (int, optional): Results page you want to retrieve (0..N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/iot_gateways/online"

        params = {
            'checkStatus': checkStatus,
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_getgatewayusingget(
        self,
        id: str,
        checkStatus: bool = True,
    ) -> Response:
        """Return a Gateway by cluster Id.

        Args:
            id (str): Unique Cluster Id
            checkStatus (bool, optional): checkStatus

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/iot_gateways/{id}"

        params = {
            'checkStatus': checkStatus
        }

        return await self.get(url, params=params)

    async def iot_operations_findtransportprofilesusingget(
        self,
        collectorId: str = None,
        page: int = 0,
        size: int = 20,
        sort: List[str] = None,
    ) -> Response:
        """Find transport profiles.

        Args:
            collectorId (str, optional): The unique Id of the collector
            page (int, optional): Results page you want to retrieve (0…N)
            size (int, optional): Number of records per page.
            sort (List[str], optional): Sorting criteria in the format: property(,asc|desc). Default
                sort order is ascending. Multiple sort criteria are supported.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/transport_profiles"

        params = {
            'collectorId': collectorId,
            'page': page,
            'size': size,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def iot_operations_addusingpost(
        self,
        clientId: str = None,
        password: str = None,
        token: str = None,
        url: str = None,
        username: str = None,
        collectorId: str = None,
        reportInterval: int = None,
        rssiAggregation: str = None,
        description: str = None,
        outputFormatType: str = None,
        protocol: str = None,
        name: str = None,
    ) -> Response:
        """Create a transport profile.

        Args:
            clientId (str, optional): clientId
            password (str, optional): password
            token (str, optional): token
            url (str, optional): url
            username (str, optional): username
            collectorId (str, optional): collectorId
            reportInterval (int, optional): reportInterval
            rssiAggregation (str, optional): rssiAggregation  Valid Values: AVERAGE, LATEST, MAX
            description (str, optional): description
            outputFormatType (str, optional): outputFormatType  Valid Values: JSON, PROTOBUF
            protocol (str, optional): protocol  Valid Values: WS, WSS, MQTT, MQTT_WS, MQTT_WSS
            name (str, optional): name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/transport_profiles"

        json_data = {
            'clientId': clientId,
            'password': password,
            'token': token,
            'url': url,
            'username': username,
            'collectorId': collectorId,
            'reportInterval': reportInterval,
            'rssiAggregation': rssiAggregation,
            'description': description,
            'outputFormatType': outputFormatType,
            'protocol': protocol,
            'name': name
        }

        return await self.post(url, json_data=json_data)

    async def iot_operations_counttransportprofilesusingget(
        self,
        collectorIds: List[str] = None,
    ) -> Response:
        """Count transport profiles.

        Args:
            collectorIds (List[str], optional): List of collector Ids

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/transport_profiles/count"

        params = {
            'collectorIds': collectorIds
        }

        return await self.get(url, params=params)

    async def iot_operations_finddeviceclassesusingget(
        self,
    ) -> Response:
        """Get a list of all device classes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/iot_operations/api/v1/transport_profiles/device_classes"

        return await self.get(url)

    async def iot_operations_getusingget(
        self,
        transportProfileId: str,
        collectorId: str = None,
    ) -> Response:
        """Get a transport profile by id.

        Args:
            transportProfileId (str): The unique Transport Profile Id
            collectorId (str, optional): The unique Id of the collector

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/transport_profiles/{transportProfileId}"

        params = {
            'collectorId': collectorId
        }

        return await self.get(url, params=params)

    async def iot_operations_saveusingput(
        self,
        collectorId: str,
        description: str,
        name: str,
        transportProfileId: str,
        clientId: str = None,
        password: str = None,
        token: str = None,
        url: str = None,
        username: str = None,
        reportInterval: int = None,
        rssiAggregation: str = None,
        outputFormatType: str = None,
        protocol: str = None,
    ) -> Response:
        """Update a transport profile by id.

        Args:
            collectorId (str): collectorId
            description (str): description
            name (str): name
            transportProfileId (str): The Unique Transport Profile Id
            clientId (str, optional): clientId
            password (str, optional): password
            token (str, optional): token
            url (str, optional): url
            username (str, optional): username
            reportInterval (int, optional): reportInterval
            rssiAggregation (str, optional): rssiAggregation  Valid Values: AVERAGE, LATEST, MAX
            outputFormatType (str, optional): outputFormatType  Valid Values: JSON, PROTOBUF
            protocol (str, optional): protocol  Valid Values: WS, WSS, MQTT, MQTT_WS, MQTT_WSS

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/transport_profiles/{transportProfileId}"

        json_data = {
            'collectorId': collectorId,
            'description': description,
            'name': name,
            'clientId': clientId,
            'password': password,
            'token': token,
            'url': url,
            'username': username,
            'reportInterval': reportInterval,
            'rssiAggregation': rssiAggregation,
            'outputFormatType': outputFormatType,
            'protocol': protocol
        }

        return await self.put(url, json_data=json_data)

    async def iot_operations_delete_by_id(
        self,
        transportProfileId: str,
        collectorId: str = None,
    ) -> Response:
        """Delete a transport profile by id.

        Args:
            transportProfileId (str): The unique Transport Profile Id
            collectorId (str, optional): collectorId

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/transport_profiles/{transportProfileId}"

        json_data = {
            'collectorId': collectorId
        }

        return await self.delete(url, json_data=json_data)

    async def monitoring_get_networks_v2(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        calculate_client_count: bool = None,
        sort: str = None,
    ) -> Response:
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

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'calculate_client_count': calculate_client_count,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_network_v2(
        self,
        network_name: str,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
    ) -> Response:
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

        return await self.get(url)

    async def monitoring_get_networks_bandwidth_usage_v2(
        self,
        network: str,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        site: str = None,
    ) -> Response:
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

    async def monitoring_get_aps_v2(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        status: str = None,
        serial: str = None,
        macaddr: str = None,
        model: str = None,
        cluster_id: str = None,
        fields: str = None,
        calculate_total: bool = None,
        calculate_client_count: bool = None,
        calculate_ssid_count: bool = None,
        show_resource_details: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_bssids_v2(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        macaddr: str = None,
        cluster_id: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_ap(
        self,
        serial: str,
    ) -> Response:
        """AP Details.

        Args:
            serial (str): Serial Number of AP to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/aps/{serial}"

        return await self.get(url)

    async def monitoring_delete_ap(
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

        return await self.delete(url)

    async def monitoring_get_ap_rf_summary_v3(
        self,
        serial: str,
        band: str = None,
        radio_number: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_aps_bandwidth_usage_v3(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        cluster_id: str = None,
        interval: str = None,
        band: str = None,
        radio_number: int = None,
        ethernet_interface_index: int = None,
        network: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_aps_bandwidth_usage_topn_v2(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        cluster_id: str = None,
        count: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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
            'cluster_id': cluster_id,
            'count': count
        }

        return await self.get(url, params=params)

    async def monitoring_get_swarms_bandwidth_usage_topn(
        self,
        group: str = None,
        count: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_swarms_clients_count_topn(
        self,
        group: str = None,
        count: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        sort: str = None,
    ) -> Response:
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

    async def monitoring_get_wireless_clients(
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
        calculate_total: bool = None,
        sort: str = None,
        last_client_mac: str = None,
        offset: int = 0,
        limit: int = 100,
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
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            last_client_mac (str, optional): Input the last processed client mac that got received
                in your last response. Please note that when last_client_mac is inputted , offset
                will not make any sense and by default the results are sorted by macaddr.
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
            'sort': sort,
            'last_client_mac': last_client_mac
        }

        return await self.get(url, params=params)

    async def monitoring_get_wired_clients(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        serial: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        last_client_mac: str = None,
        offset: int = 0,
        limit: int = 100,
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
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            last_client_mac (str, optional): Input the last processed client mac that got received
                in your last response. Please note that when last_client_mac is inputted , offset
                will not make any sense and by default the results are sorted by macaddr.
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
            'sort': sort,
            'last_client_mac': last_client_mac
        }

        return await self.get(url, params=params)

    async def monitoring_get_v2_unified_clients(
        self,
        timerange: str,
        client_type: str,
        client_status: str,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        site: str = None,
        network: str = None,
        serial: str = None,
        cluster_id: str = None,
        os_type: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        last_client_mac: str = None,
        show_usage: bool = None,
        show_manufacturer: bool = None,
        show_signal_db: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Unified Clients (Wired/Wireless). Option to choose Connected/Failed Clients.

        Args:
            timerange (str): Time range for unified clients information.
                3H = 3 Hours, 1D = 1 Day, 1W = 1 Week, 1M = 1Month, 3M = 3Months.
                Valid Values: 3H, 1D, 1W, 1M, 3M
            client_type (str): WIRED = List Wired Clients, WIRELESS = List Wireless Clients.  Valid
                Values: WIRELESS, WIRED
            client_status (str): CONNECTED = List Connected Clients, FAILED_TO_CONNECT = List Failed
                Clients.  Valid Values: CONNECTED, FAILED_TO_CONNECT
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            network (str, optional): Filter by network name
            serial (str, optional): Filter by device serial number
            cluster_id (str, optional): Filter by Mobility Controller serial number
            os_type (str, optional): Filter by OS Type
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                name, ip_address, username, associated_device, group_name, interface_mac, vlan
            calculate_total (bool, optional): Whether to calculate total Wireless/Wired Clients
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            last_client_mac (str, optional): Input the last processed client mac that got received
                in your last response. Please note that when last_client_mac is inputted , offset
                will not make any sense and by default the results are sorted by macaddr.
            show_usage (bool, optional): Whether to show usage
            show_manufacturer (bool, optional): Whether to show manufacturer
            show_signal_db (bool, optional): Whether to show signal_db and signal_strength
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/clients"

        params = {
            'timerange': timerange,
            'client_type': client_type,
            'client_status': client_status,
            'serial': serial,
            'cluster_id': cluster_id,
            'os_type': os_type,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'last_client_mac': last_client_mac,
            'show_usage': show_usage,
            'show_manufacturer': show_manufacturer,
            'show_signal_db': show_signal_db
        }

        return await self.get(url, params=params)

    async def monitoring_get_v2_unified_client_detail(
        self,
        macaddr: str,
    ) -> Response:
        """Client Details.

        Args:
            macaddr (str): MAC address of the Wireless/Wired Client to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/clients/{macaddr}"

        return await self.get(url)

    async def monitoring_get_wireless_client(
        self,
        macaddr: str,
    ) -> Response:
        """Wireless Client Details.

        Args:
            macaddr (str): MAC address of the Wireless Client to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wireless/{macaddr}"

        return await self.get(url)

    async def monitoring_get_wireless_client_mobility(
        self,
        macaddr: str,
        calculate_total: bool = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_wired_client(
        self,
        macaddr: str,
    ) -> Response:
        """Wired Client Details.

        Args:
            macaddr (str): MAC address of the Wired Client to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/clients/wired/{macaddr}"

        return await self.get(url)

    async def monitoring_get_clients_bandwidth_usage(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_clients_bandwidth_usage_topn(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        count: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_clients_count(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        network: str = None,
        cluster_id: str = None,
        stack_id: str = None,
        device_type: str = None,
        serial: str = None,
        band: str = None,
        radio_number: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_swarms(
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

    async def monitoring_get_swarm(
        self,
        swarm_id: str,
    ) -> Response:
        """Swarm Details.

        Args:
            swarm_id (str): Swarm ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def monitoring_get_vpn_info(
        self,
        swarm_id: str,
    ) -> Response:
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

    async def monitoring_get_vpn_usage_v3(
        self,
        swarm_id: str,
        tunnel_index: int,
        tunnel_name: str,
        from_timestamp: int,
        to_timestamp: int,
    ) -> Response:
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

    async def monitoring_get_mc_ports_bandwidth_usage(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
    ) -> Response:
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

    async def monitoring_get_mc_ports(
        self,
        serial: str,
    ) -> Response:
        """Mobility Controllers Ports Details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/ports"

        return await self.get(url)

    async def monitoring_get_vlan_info(
        self,
        serial: str,
    ) -> Response:
        """Mobility Controllers VLAN details.

        Args:
            serial (str): Serial number of mobility controller to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/mobility_controllers/{serial}/vlan"

        return await self.get(url)

    async def monitoring_get_mcs_v2(
        self,
        group: str = None,
        label: str = None,
        site: str = None,
        status: str = None,
        macaddr: str = None,
        model: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Mobility Controllers.

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
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/mobility_controllers"

        params = {
            'status': status,
            'macaddr': macaddr,
            'model': model,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_mc_v2(
        self,
        serial: str,
        stats_metric: bool = None,
    ) -> Response:
        """Mobility Controller Details.

        Args:
            serial (str): Serial Number of Mobility Controller to be queried
            stats_metric (bool, optional): If set, gets the uplinks and tunnels count

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/mobility_controllers/{serial}"

        params = {
            'stats_metric': stats_metric
        }

        return await self.get(url, params=params)

    async def monitoring_delete_mc_v2(
        self,
        serial: str,
    ) -> Response:
        """Delete Mobility Controller.

        Args:
            serial (str): Serial Number of Mobility Controller to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/mobility_controllers/{serial}"

        return await self.delete(url)

    async def monitoring_get_gateways(
        self,
        group: str = None,
        label: str = None,
        site: str = None,
        status: str = None,
        macaddr: str = None,
        model: str = None,
        fields: str = None,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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
            'status': status,
            'macaddr': macaddr,
            'model': model,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway(
        self,
        serial: str,
        stats_metric: bool = False,
    ) -> Response:
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

    async def monitoring_delete_gateway(
        self,
        serial: str,
    ) -> Response:
        """Delete Gateway.

        Args:
            serial (str): Serial Number of Gateway to be deleted

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}"

        return await self.delete(url)

    async def monitoring_get_gateway_uplinks_detail(
        self,
        serial: str,
        timerange: str,
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
            'timerange': timerange
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_bandwidth_usage(
        self,
        serial: str,
        uplink_id: str = None,
        interval: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_gateway_uplinks_tunnel_stats(
        self,
        serial: str,
        uplink_id: str = None,
        map_name: str = None,
        interval: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
        """Gateway Uplink tunnel stats.

        Args:
            serial (str): Filter by Gateway serial
            uplink_id (str, optional): Filter by map ID.This field has been DEPRECATED.
            map_name (str, optional): Filter by tunnel map name.
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
            'map_name': map_name,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_uplinks_wan_compression_usage(
        self,
        serial: str,
        uplink_id: str = None,
        interval: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_gateway_uplinks_distribution(
        self,
        serial: str,
    ) -> Response:
        """Gateway Uplink distribution.

        Args:
            serial (str): Gateway serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/uplinks/distribution"

        return await self.get(url)

    async def monitoring_get_gateway_ports_bandwidth_usage(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
    ) -> Response:
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

    async def monitoring_get_gateway_ports(
        self,
        serial: str,
    ) -> Response:
        """Gateway Ports Details.

        Args:
            serial (str): Serial number of Gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports"

        return await self.get(url)

    async def monitoring_get_gateway_port_errors(
        self,
        serial: str,
        port: str,
        interval: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
        """Gateway Port Errors.

        Args:
            serial (str): Serial number of Gateway to be queried
            port (str): Filter by Port (example GE0/0/1)
            interval (str, optional): Sampling interval of Port Errors.  Valid Values: 5minutes,
                1hour, 1day, 1week
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/ports/errors"

        params = {
            'port': port,
            'interval': interval
        }

        return await self.get(url, params=params)

    async def monitoring_get_gateway_tunnels(
        self,
        serial: str,
        timerange: str = '3H',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_gateway_dhcp_clients(
        self,
        serial: str,
        reservation: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_gateway_dhcp_pools(
        self,
        serial: str,
    ) -> Response:
        """Gateway DHCP Pools details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/dhcp_pools"

        return await self.get(url)

    async def monitoring_get_gateway_vlan_info(
        self,
        serial: str,
    ) -> Response:
        """Gateway VLAN details.

        Args:
            serial (str): Serial number of gateway to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/gateways/{serial}/vlan"

        return await self.get(url)

    async def central_get_labels(
        self,
        calculate_total: bool = None,
        category_id: int = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def central_create_label(
        self,
        category_id: int,
        label_name: str,
    ) -> Response:
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

    async def central_get_default_labels(
        self,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def central_get_label(
        self,
        label_id: int,
    ) -> Response:
        """Label details.

        Args:
            label_id (int): Label name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        return await self.get(url)

    async def central_update_label(
        self,
        label_id: int,
        label_name: str,
    ) -> Response:
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

    async def central_delete_label(
        self,
        label_id: int,
    ) -> Response:
        """Delete Label.

        Args:
            label_id (int): Label ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/labels/{label_id}"

        return await self.delete(url)

    async def central_assign_label(
        self,
        device_id: str,
        device_type: str,
        label_id: int,
    ) -> Response:
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

    async def central_unassign_label(
        self,
        device_id: str,
        device_type: str,
        label_id: int,
    ) -> Response:
        """Unassociate Label from device.

        Args:
            device_id (str): Device ID. In the case IAP or SWITCH, it is device serial number
            device_type (str): Device type. It is either IAP, SWITCH or CONTROLLER
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

    async def central_assign_label_to_devices(
        self,
        label_id: int,
        device_type: str,
        device_ids: List[str],
    ) -> Response:
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

    async def central_unassign_label_from_devices(
        self,
        label_id: int,
        device_type: str,
        device_ids: List[str],
    ) -> Response:
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

    async def central_get_label_categories(
        self,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def central_get_sites(
        self,
        calculate_total: bool = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def central_create_site(
        self,
        site_name: str,
        address: str,
        city: str,
        state: str,
        country: str,
        zipcode: str,
        latitude: str,
        longitude: str,
    ) -> Response:
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

    async def central_get_site(
        self,
        site_id: int,
    ) -> Response:
        """Site details.

        Args:
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        return await self.get(url)

    async def central_update_site(
        self,
        site_id: int,
        site_name: str,
        address: str,
        city: str,
        state: str,
        country: str,
        zipcode: str,
        latitude: str,
        longitude: str,
    ) -> Response:
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

    async def central_delete_site(
        self,
        site_id: int,
    ) -> Response:
        """Delete Site.

        Args:
            site_id (int): Site ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"

        return await self.delete(url)

    async def central_assign_site(
        self,
        device_id: str,
        device_type: str,
        site_id: int,
    ) -> Response:
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

    async def central_unassign_site(
        self,
        device_id: str,
        device_type: str,
        site_id: int,
    ) -> Response:
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

    async def central_assign_site_to_devices(
        self,
        site_id: int,
        device_type: str,
        device_ids: List[str],
    ) -> Response:
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

    async def central_unassign_site_from_devices(
        self,
        site_id: int,
        device_type: str,
        device_ids: List[str],
    ) -> Response:
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

    async def monitoring_get_switches(
        self,
        group: str = None,
        label: str = None,
        stack_id: str = None,
        status: str = None,
        fields: str = None,
        calculate_total: bool = None,
        show_resource_details: bool = None,
        calculate_client_count: bool = None,
        public_ip_address: str = None,
        site: str = None,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_switch_vlan(
        self,
        serial: str,
        name: str = None,
        id: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_cx_switch_vlan(
        self,
        serial: str,
        name: str = None,
        id: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_switch_stack_vlan(
        self,
        stack_id: str,
        name: str = None,
        id: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def monitoring_get_cx_switch_stack_vlan(
        self,
        stack_id: str,
        name: str = None,
        id: int = None,
        tagged_port: str = None,
        untagged_port: str = None,
        is_jumbo_enabled: bool = None,
        is_voice_enabled: bool = None,
        is_igmp_enabled: bool = None,
        type: str = None,
        primary_vlan_id: int = None,
        status: str = None,
        sort: str = None,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    # TODO PoE details works for both sw and cx specify port for port level details
    async def monitoring_get_switch_poe_detail(
        self,
        serial: str,
        port: str = None,
    ) -> Response:
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

    # port is required output seems same as above
    async def monitoring_get_cx_switch_poe_detail(
        self,
        serial: str,
        port: str,
    ) -> Response:
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

    # TODO 1 call gets PoE details for all ports
    async def monitoring_get_switch_poe_details_for_all_ports(
        self,
        serial: str,
        port: str = None,
    ) -> Response:
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

    async def monitoring_get_cx_switch_poe_details_for_all_ports(
        self,
        serial: str,
        port: str = None,
    ) -> Response:
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

    async def monitoring_get_switch_vsx_detail(
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

        return await self.get(url)

    async def monitoring_get_bandwidth_usage(
        self,
        group: str = None,
        label: str = None,
        serial: str = None,
        stack_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_bandwidth_usage_topn(
        self,
        group: str = None,
        label: str = None,
        stack_id: str = None,
        count: int = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
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

    async def monitoring_get_switch(
        self,
        serial: str,
    ) -> Response:
        """Switch Details.

        Args:
            serial (str): Serial number of switch to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}"

        return await self.get(url)

    async def monitoring_delete_switch(
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

        return await self.delete(url)

    async def monitoring_get_switch_ports(
        self,
        serial: str,
        slot: str = None,
    ) -> Response:
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

    async def monitoring_get_cx_switch_ports(
        self,
        serial: str,
        slot: str = None,
    ) -> Response:
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

    async def monitoring_get_chassis_info(
        self,
        serial: str,
    ) -> Response:
        """Switch Chassis Details.

        Args:
            serial (str): Serial number of switch to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switches/{serial}/chassis_info"

        return await self.get(url)

    async def monitoring_get_switch_ports_bandwidth_usage(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
        show_uplink: bool = None,
    ) -> Response:
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

    async def monitoring_get_cx_switch_ports_bandwidth_usage(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
        show_uplink: bool = None,
    ) -> Response:
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

    async def monitoring_get_ports_errors(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
        error: str = None,
    ) -> Response:
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

    async def monitoring_get_cx_ports_errors(
        self,
        serial: str,
        from_timestamp: int = None,
        to_timestamp: int = None,
        port: str = None,
        error: str = None,
    ) -> Response:
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

    async def monitoring_get_stack_ports(
        self,
        stack_id: str,
    ) -> Response:
        """Switch Stack Port Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/switch_stacks/{stack_id}/ports"

        return await self.get(url)

    async def monitoring_get_cx_stack_ports(
        self,
        stack_id: str,
    ) -> Response:
        """CX Switch Stack Port Details.

        Args:
            stack_id (str): Filter by Switch stack_id

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v1/cx_switch_stacks/{stack_id}/ports"

        return await self.get(url)

    async def monitoring_get_switch_stacks(
        self,
        hostname: str = None,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Switch Stacks.

        Args:
            hostname (str, optional): Filter by stack hostname
            group (str, optional): Filter by group name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/switch_stacks"

        params = {
            'hostname': hostname
        }

        return await self.get(url, params=params)

    async def monitoring_get_switch_stack(
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

        return await self.get(url)

    async def monitoring_delete_switch_stack(
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

        return await self.delete(url)

    async def monitoring_get_events_v2(
        self,
        group: str = None,
        swarm_id: str = None,
        label: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        macaddr: str = None,
        bssid: str = None,
        device_mac: str = None,
        hostname: str = None,
        device_type: str = None,
        sort: str = '-timestamp',
        site: str = None,
        serial: str = None,
        level: str = None,
        event_description: str = None,
        event_type: str = None,
        fields: str = None,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Events.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            label (str, optional): Filter by Label name
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            macaddr (str, optional): Filter by client MAC address
            bssid (str, optional): Filter by bssid
            device_mac (str, optional): Filter by device_mac
            hostname (str, optional): Filter by hostname
            device_type (str, optional): Filter by device type. It is either ACCESS POINT, SWITCH,
                GATEWAY or CLIENT  Valid Values: ACCESS POINT, SWITCH, GATEWAY, CLIENT
            sort (str, optional): Sort by desc/asc using -timestamp/+timestamp. Default is
                '-timestamp'  Valid Values: -timestamp, +timestamp
            site (str, optional): Filter by site name
            serial (str, optional): Filter by switch serial number
            level (str, optional): Filter by event level
            event_description (str, optional): Filter by event description
            event_type (str, optional): Filter by event type
            fields (str, optional): Comma separated list of fields to be returned. Valid fields are
                number, level
            calculate_total (bool, optional): Whether to calculate total events
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v2/events"

        params = {
            'macaddr': macaddr,
            'bssid': bssid,
            'device_mac': device_mac,
            'hostname': hostname,
            'device_type': device_type,
            'sort': sort,
            'site': site,
            'serial': serial,
            'level': level,
            'event_description': event_description,
            'event_type': event_type,
            'fields': fields,
            'calculate_total': calculate_total
        }

        return await self.get(url, params=params)

    async def msp_get_customers(
        self,
        customer_name: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def msp_create_customer(
        self,
        customer_name: str,
        name: str,
        description: str,
        lock_msp_ssids: bool,
    ) -> Response:
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

    async def msp_get_customer(
        self,
        customer_id: str,
    ) -> Response:
        """Get details of customer.

        Args:
            customer_id (str): Filter on Customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}"

        return await self.get(url)

    async def msp_edit_customer(
        self,
        customer_id: str,
        customer_name: str,
        name: str,
        description: str,
        lock_msp_ssids: bool,
    ) -> Response:
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

    async def msp_delete_customer(
        self,
        customer_id: str,
    ) -> Response:
        """Delete a customer.

        Args:
            customer_id (str): Filter on Customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}"

        return await self.delete(url)

    async def msp_get_users(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get list of users under the MSP account based on limit and offset.

        Args:
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/customers/users"

        return await self.get(url)

    async def msp_get_customer_users(
        self,
        customer_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get list of users under the Customer account based on limit and offset.

        Args:
            customer_id (str): Filter on Customer ID
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/customers/{customer_id}/users"

        return await self.get(url)

    async def msp_get_resource(
        self,
    ) -> Response:
        """Get the resource under the MSP.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/resource"

        return await self.get(url)

    async def msp_edit_resource(
        self,
        contact_link: str,
        logo_image_url: str,
        mail_address: str,
        primary_color: str,
        product_name: str,
        provider_name: str,
        sender_email_address: str,
        service_link: str,
        terms_link: str,
        image_blob: str,
        skin_info: str,
    ) -> Response:
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

    async def msp_get_customer_devices(
        self,
        customer_id: str,
        device_type: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def msp_move_devices_to_customer(
        self,
        customer_id: str,
        devices: list,
        group: str,
    ) -> Response:
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

    async def msp_get_devices(
        self,
        device_allocation_status: int = 0,
        device_type: str = None,
        customer_name: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def msp_get_mapped_tenants(
        self,
        group_name: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get list of customers mapped to MSP group based on limit and offset.

        Args:
            group_name (str): MSP group name
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v1/groups/{group_name}/customers"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def branchhealth_get_labels_(
        self,
        name: str = None,
        column: int = None,
        order: int = None,
        Site_properties_used_with_thresholds: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    # TODO ADD TO CLI
    async def branchhealth_get_sites_(
        self,
        name: str = None,
        column: int = None,
        reverse: bool = False,
        filters: dict = {},
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get data for all sites.

        Args:
            name (str, optional): site / label name or part of its name
            column (int, optional): Column to sort on
            reverse (bool, optional): Sort in reverse order:
                * asc - Ascending, from A to Z.
                * desc - Descending, from Z to A.
                Valid Values: asc, desc
            filters (str, optional): Site thresholds
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

        params = {
            "name": name,
            # "column": column,
            "order": "asc" if not reverse else "desc",
            "wan_tunnels_down\__gt": "0",
            "wan_uplinks_down\__gt": "0",
            # **filters,
            "offset": offset,
            "limit": limit,
        }

        return await self.get(url, params=params)

    # API-NOTE appears to show alert types
    async def central_get_types_(
        self,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Types.

        Args:
            calculate_total (bool, optional): Whether to count total items in the response
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Default is 1000 and max is 1000.

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

    # API-NOTE returns alert/notification settings not used by any command yet
    async def central_get_settings_(
        self,
        search: str = None,
        sort: str = '-created_ts',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def central_add_setting_(
        self,
        type: str,
        rules: list,
        active: bool,
    ) -> Response:
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

    async def central_delete_setting_(
        self,
        settings_id: str,
    ) -> Response:
        """Delete Settings.

        Args:
            settings_id (str): id of the settings

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v1/notifications/settings/{settings_id}"

        return await self.delete(url)

    async def central_update_setting_(
        self,
        settings_id: str,
        type: str,
        rules: list,
        active: bool,
    ) -> Response:
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

    async def central_get_customer_settings_(
        self,
    ) -> Response:
        """Get Customer account level Settings.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/customer_settings"

        return await self.get(url)

    # API-NOTE Use This Add sites to mute
    async def central_update_customer_settings_(
        self,
        add_sites_to_mute: List[str],
        remove_sites_from_mute: List[str],
        update_site_emails: list,
        default_recipients_email_list: List[str],
    ) -> Response:
        """Update customer settings.

        Args:
            add_sites_to_mute (List[str]): Sites to be muted for alert
            remove_sites_from_mute (List[str]): Sites to be unmuted for alert
            update_site_emails (list): update_site_emails
            default_recipients_email_list (List[str]): Emails to be saved as deafult recipient list

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/customer_settings"

        json_data = {
            'add_sites_to_mute': add_sites_to_mute,
            'remove_sites_from_mute': remove_sites_from_mute,
            'update_site_emails': update_site_emails,
            'default_recipients_email_list': default_recipients_email_list
        }

        return await self.put(url, json_data=json_data)

    async def central_get_count_by_severity_(
        self,
        customer_id: str = None,
        group: str = None,
        label: str = None,
        serial: str = None,
        site: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ack: bool = None,
    ) -> Response:
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

    # TODO ADD TO CLI ... ALERTS DEVICE/Tunnel Down alerts etc.
    async def central_get_notifications_(
        self,
        customer_id: str = None,
        group: str = None,
        label: str = None,
        serial: str = None,
        site: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        severity: str = None,
        type: str = None,
        search: str = None,
        calculate_total: bool = None,
        ack: bool = None,
        fields: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    # API-NOTE ack notifications
    async def central_acknowledge_notifications(
        self,
        NoName: List[str] = None,
    ) -> Response:
        """Acknowledge Notifications by ID List / All.

        Args:
            NoName (List[str], optional): Acknowledge notifications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"

        return await self.post(url)

    # API-NOTE ack notifications
    async def central_acknowledge_notification(
        self,
        notification_id: str,
        acknowledged: bool,
    ) -> Response:
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

    async def ofc_enable_wildcard_flow(
        self,
        enable: bool,
        serial_id: str,
    ) -> Response:
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

    async def ofc_enable_wildcard_flow_list(
        self,
        enable: bool,
        serial_id_metadata: Union[Path, str],
    ) -> Response:
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

    async def ofc_check_status_list(
        self,
        serial_ids: Union[Path, str],
    ) -> Response:
        """Check Status of Syslog App for given SerialIDs.

        Args:
            serial_ids (Union[Path, str]): File with SerialIDs

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ofcapi/v1/syslog/flows/status/device_list"
        serial_ids = serial_ids if isinstance(serial_ids, Path) else Path(str(serial_ids))

        return await self.post(url)

    async def ofc_check_status(
        self,
        serial_id: str,
    ) -> Response:
        """Check Status of Enabled Flow SerialID.

        Args:
            serial_id (str): Device Serial ID on which the Status is checked

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ofcapi/v1/syslog/flow/status/{serial_id}"

        return await self.get(url)

    async def platform_get_devices(
        self,
        sku_type: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get devices from device inventory.

        Args:
            sku_type (str): iap/switch/controller/gateway/vgw/cap/boc/all_ap/all_controller/others
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        params = {
            'sku_type': sku_type,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def platform_add_device(
        self,
        NoName: list = None,
    ) -> Response:
        """Add device using Mac and Serial number.

        Args:
            NoName (list, optional): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        return await self.post(url)

    async def platform_delete_device(
        self,
        device: Union[str, List[str]],
    ) -> Response:
        """Delete devices using Serial number.
        Valid only for Central On Prem

        Args:
            devices (List[str]): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"
        devices = [devices] if not isinstance(devices, list) else devices
        params = [
            {"serial": s} for s in devices
        ]

        return await self.delete(url, params=params)

    async def platform_get_devices_stats(
        self,
        sku_type: str,
        service_type: str,
    ) -> Response:
        """Get devices stats.

        Args:
            sku_type (str): iap/switch/controller/gateway/vgw/cap/boc/all_ap/all_controller/others
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

    async def platform_verify_device_addition(
        self,
        NoName: list = None,
    ) -> Response:
        """Verify device addition.

        Args:
            NoName (list, optional): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/verify"

        return await self.post(url)

    async def platform_refresh_inventory_status(
        self,
    ) -> Response:
        """Get status of refresh job.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/refresh"

        return await self.get(url)

    async def platform_refresh_inventory(
        self,
    ) -> Response:
        """Schedule a job to refresh the device inventory.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/refresh"

        return await self.post(url)

    async def platform_get_device(
        self,
        serial: str,
    ) -> Response:
        """Get device from device inventory.

        Args:
            serial (str): Query device using serial number (API is only supported for private cloud
                Central environment)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/device_inventory/v1/device/{serial}"

        return await self.get(url)

    # API-NOTE cencli show archive
    async def platform_get_archive_devices(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get Archived devices from device inventory.

        Args:
            offset (int, optional): offset or page number Defaults to 0.
            limit (int, optional): Number of devices to get Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices/archive"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    # API-NOTE cencli archive [devices]
    async def platform_archive_devices(
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
            'serials': serials
        }

        return await self.post(url, json_data=json_data)

    # API-NOTE cencli remove archive [devices]
    async def platform_unarchive_devices(
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
            'serials': serials
        }

        return await self.post(url, json_data=json_data)

    async def platform_get_msp_customer_devices(
        self,
        customer_id: str,
        device_type: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def platform_assign_device_to_customer(
        self,
        customer_id: str,
        devices: list,
    ) -> Response:
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

    async def platform_get_msp_devices(
        self,
        device_type: str = None,
        customer_name: str = None,
        device_allocation_status: int = 0,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def platform_get_user_subscriptions(
        self,
        license_type: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def platform_get_subscription_stats(
        self,
        license_type: str = 'all',
        service: str = None,
    ) -> Response:
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
        # [
        #     {
        #         "available": 6108,
        #         "expiring": 0,
        #         "license_usage_by_services": {
        #             "advance_70xx": 0,
        #             "advance_72xx": 0,
        #             "advance_90xx_sec": 3,
        #             "advance_base_7005": 0,
        #             "advanced_ap": 11,
        #             "advanced_switch_6100": 0,
        #             "advanced_switch_6200": 0,
        #             "advanced_switch_6300": 0,
        #             "advanced_switch_6400": 0,
        #             "dm": 0,
        #             "foundation_70xx": 3,
        #             "foundation_72xx": 0,
        #             "foundation_90xx_sec": 0,
        #             "foundation_ap": 0,
        #             "foundation_base_7005": 0,
        #             "foundation_base_90xx_sec": 0,
        #             "foundation_switch_6100": 6,
        #             "foundation_switch_6200": 2,
        #             "foundation_switch_6300": 0,
        #             "foundation_switch_6400": 0,
        #             "foundation_wlan_gw": 0,
        #             "vgw2g": 0,
        #             "vgw4g": 0,
        #             "vgw500m": 0
        #         },
        #         "non_subscribed_devices": 0,
        #         "total": 6133,
        #         "total_devices": 25,
        #         "used": 25
        #     }
        # ]
        url = "/platform/licensing/v1/subscriptions/stats"

        params = {
            'license_type': license_type,
            'service': service
        }

        return await self.get(url, params=params)

    async def platform_gw_license_available(
        self,
        service: str,
    ) -> Response:
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

    async def platform_gw_get_autolicense_settings(
        self,
    ) -> Response:
        """Get the services which are auto enabled.

        Returns:
            Response: CentralAPI Response object
        """
        # [
        #     {
        #         "services": []
        #     }
        # ]
        url = "/platform/licensing/v1/customer/settings/autolicense"

        return await self.get(url)

    async def platform_gw_enable_auto_licensing_settings(
        self,
        services: List[str],
    ) -> Response:
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

    async def platform_gw_disable_auto_licensing_settings(
        self,
        services: List[str],
    ) -> Response:
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

    async def platform_gw_msp_get_autolicense_settings(
        self,
        customer_id: str,
    ) -> Response:
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

    async def platform_gw_msp_enable_auto_licensing_settings(
        self,
        include_customers: List[str],
        exclude_customers: List[str],
        services: List[str],
    ) -> Response:
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

    async def platform_gw_msp_disable_auto_licensing_settings(
        self,
        include_customers: List[str],
        exclude_customers: List[str],
        services: List[str],
    ) -> Response:
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

    async def platform_gw_assign_licenses(
        self,
        serials: List[str],
        services: List[str],
    ) -> Response:
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

    async def platform_gw_unassign_licenses(
        self,
        serials: List[str],
        services: List[str],
    ) -> Response:
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

    # Show all available licenses [{"services": {"services": [foundation_70xx, ...]}] <-- wtf
    async def platform_gw_get_customer_enabled_services(
        self,
    ) -> Response:
        """Get enabled services for customer.

        Returns:
            Response: CentralAPI Response object
        """
        # [
        #     {
        #         "services": {
        #             "services": [
        #                 "foundation_70xx",
        #                 "cloud_guest",
        #                 "dm",
        #                 "foundation_switch_6100",
        #                 "advance_90xx_sec",
        #                 "pa",
        #                 "ucc",
        #                 "airgroup",
        #                 "advanced_ap",
        #                 "clarity",
        #                 "foundation_switch_6200"
        #             ]
        #         }
        #     }
        # ]
        url = "/platform/licensing/v1/services/enabled"

        return await self.get(url)

    # TODO useful shows list of license types
    async def platform_get_services_config(
        self,
        service_category: str = None,
        device_type: str = None,
    ) -> Response:
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

    async def platform_assign_subscription_all_devices(
        self,
        services: List[str],
    ) -> Response:
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

    async def platform_unassign_subscription_all_devices(
        self,
        services: List[str],
    ) -> Response:
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

    async def platform_msp_assign_subscription_all_devices(
        self,
        include_customers: List[str],
        exclude_customers: List[str],
        services: List[str],
    ) -> Response:
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

    async def platform_msp_unassign_subscription_all_devices(
        self,
        include_customers: List[str],
        exclude_customers: List[str],
        services: List[str],
    ) -> Response:
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

    async def presence_set_v3_thresholds(
        self,
        dwelltime: int,
        rssi: int,
        passerby_rssi: int,
        site_id: int,
        select_all: bool = False,
    ) -> Response:
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

    async def presence_get_v3_thresholds(
        self,
        site_id: str = None,
    ) -> Response:
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

    async def presence_get_pa_config_data(
        self,
        sort: str = None,
        search: str = None,
        site_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def presence_get_visitors_status_info(
        self,
        start_time: int,
        end_time: int,
        tag_id: str = None,
    ) -> Response:
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

    async def presence_get_loyalty_visit_frequency(
        self,
        start_time: int,
        end_time: int,
        tag_id: str = None,
    ) -> Response:
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

    async def presence_get_dashboard_v3_percentile_datapoints(
        self,
        category: str,
        start_time: int,
        end_time: int,
        tag_id: str = None,
        sample_frequency: str = None,
    ) -> Response:
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

    async def presence_get_v3_loyalty_trends(
        self,
        start_time: int,
        end_time: int,
        tag_id: str = None,
        sample_frequency: str = None,
    ) -> Response:
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

    async def presence_enable_or_disable_pa_license(
        self,
        customer_level: bool,
        enable_device_list: List[str],
        disable_device_list: List[str],
    ) -> Response:
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

    async def presence_get_pa_license_status(
        self,
    ) -> Response:
        """Customer level device license status.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/presence/v3/license"

        return await self.get(url)

    async def presence_get_device_license_status_per_site(
        self,
        tag_id: str,
    ) -> Response:
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

    async def presence_get_site_wise_data(
        self,
        start_time: int,
        end_time: int,
        search: str = None,
        sort: str = None,
        site_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def get_rds_v1_rogue_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def get_rds_v1_interfering_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def get_rds_v1_suspect_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def get_rds_v1_neighbor_aps(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def delete_rds_v1_rogues(
        self,
        bssid: str,
    ) -> Response:
        """Delete a rogue.

        Args:
            bssid (str): The bssid of the rogue device (AA:BB:CC:DD:EE:FF)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/rapids/v1/rogues/{bssid}"

        return await self.delete(url)

    async def get_rds_v1_ssid_allow(
        self,
    ) -> Response:
        """List Allowed SSIDs.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_allow"

        return await self.get(url)

    async def post_rds_v1_ssid_allow(
        self,
        ssids: List[str],
    ) -> Response:
        """Add Allowed SSIDs.

        Args:
            ssids (List[str]): Array of SSIDs to be manually blocked

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_allow"

        json_data = {
            'ssids': ssids
        }

        return await self.post(url, json_data=json_data)

    async def delete_rds_v1_ssid_allow(
        self,
        ssids: List[str],
    ) -> Response:
        """Delete Allowed SSIDs.

        Args:
            ssids (List[str]): Array of SSIDs to be manually blocked

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_allow"

        json_data = {
            'ssids': ssids
        }

        return await self.delete(url, json_data=json_data)

    async def get_rds_v1_ssid_block(
        self,
    ) -> Response:
        """List Blocked SSIDs.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_block"

        return await self.get(url)

    async def post_rds_v1_ssid_block(
        self,
        ssids: List[str],
    ) -> Response:
        """Add Blocked SSIDs.

        Args:
            ssids (List[str]): Array of SSIDs to be manually allowed

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_block"

        json_data = {
            'ssids': ssids
        }

        return await self.post(url, json_data=json_data)

    async def delete_rds_v1_ssid_block(
        self,
        ssids: List[str],
    ) -> Response:
        """Delete Blocked SSIDs.

        Args:
            ssids (List[str]): Array of SSIDs to be manually allowed

        Returns:
            Response: CentralAPI Response object
        """
        url = "/rapids/v1/ssid_block"

        json_data = {
            'ssids': ssids
        }

        return await self.delete(url, json_data=json_data)

    async def rds_get_infrastructure_attacks(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        calculate_total: bool = None,
        sort: str = '-ts',
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def rds_get_client_attacks(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        calculate_total: bool = None,
        sort: str = '-ts',
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def rds_get_wids_events(
        self,
        group: List[str] = None,
        label: List[str] = None,
        site: List[str] = None,
        start: int = None,
        end: int = None,
        sort: str = '-ts',
        swarm_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def oauth2_xxx(
        self,
        client_id: str,
        client_secret: str,
        grant_type: str,
        refresh_token: str,
    ) -> Response:
        """Refresh API token.

        Args:
            client_id (str): Client ID
            client_secret (str): Client Secret
            grant_type (str): Value should be "refresh_token"
            refresh_token (str): Refresh Token

        Returns:
            Response: CentralAPI Response object
        """
        url = "/oauth2/token"

        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': grant_type,
            'refresh_token': refresh_token
        }

        return await self.post(url, params=params)

    async def reports_scheduled_reports(
        self,
        cid: str,
        start_time: int = None,
        end_time: int = None,
    ) -> Response:
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

    async def reports_generated_reports(
        self,
        cid: str,
        start_time: int = None,
        end_time: int = None,
    ) -> Response:
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

    async def sdwan_mon_get_wan_policy_compliance(
        self,
        period: str,
        result_order: str,
        count: int,
    ) -> Response:
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
        url = "/api/sdwan-mon-api/external/noc/reports/wan/policy-compliance"

        params = {
            'period': period,
            'result_order': result_order,
            'count': count
        }

        return await self.get(url, params=params)

    async def get_routing_v1_bgp_neighbor(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_bgp_neighbor_detail(
        self,
        device: str,
        address: str,
    ) -> Response:
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

    async def put_routing_v1_bgp_neighbor_reset(
        self,
        device: str,
        address: str,
    ) -> Response:
        """Reset/clear BGP neighbor session.

        Args:
            device (str): Device serial number
            address (str): IP address

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/bgp/neighbor/reset"

        return await self.put(url)

    async def get_routing_v1_bgp_neighbor_route_learned(
        self,
        device: str,
        address: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of routes learned from a BGP neighbor.

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

    async def get_routing_v1_bgp_neighbor_route_advertised(
        self,
        device: str,
        address: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_bgp_route(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    # TODO useful.  Verify marker param
    async def get_routing_v1_overlay_connection(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def put_routing_v1_overlay_connection_reset(
        self,
        device: str,
    ) -> Response:
        """Reset overlay control connection.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/connection/reset"

        return await self.put(url)

    # TODO Useful show OAP tunnels
    async def get_routing_v1_overlay_interface(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of overlay interfaces (tunnels).

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_overlay_route_learned(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List of learned routes from overlay.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/overlay/route/learned"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_overlay_route_learned_best(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_overlay_route_advertised(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_ospf_area(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_ospf_interface(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
        """List OSPF Interface Information.

        Args:
            device (str): Device serial number
            marker (str, optional): Opaque handle to fetch next page
            limit (int, optional): page size Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v1/ospf/interface"

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_routing_v1_ospf_neighbor(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_ospf_database(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_rip_interface(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_rip_neighbor(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_rip_neighbor_route(
        self,
        device: str,
        address: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_rip_route(
        self,
        device: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v1_route(
        self,
        device: str,
        api: str = None,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

    async def get_routing_v0_route(
        self,
        device: str,
    ) -> Response:
        """Get legacy routes.

        Args:
            device (str): Device serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = "/api/routing/v0/route"

        params = {
            'device': device,
        }

        return await self.get(url, params=params)

    async def cloud_security_config_get_aruba_security_config_id2(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def cloud_security_config_post_aruba_security_config_id2(
        self,
        node_type: str,
        node_id: str,
        base_uri: str,
        password: str,
        admin_status: str,
        api_key: str,
        user: str,
    ) -> Response:
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

    async def cloud_security_config_put_aruba_security_config_id2(
        self,
        node_type: str,
        node_id: str,
        base_uri: str,
        password: str,
        admin_status: str,
        api_key: str,
        user: str,
    ) -> Response:
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

    async def cloud_security_config_delete_aruba_security_config_id2(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def cloud_security_config_get_aruba_security_zscaler_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def cloud_security_config_post_aruba_security_zscaler_id1(
        self,
        node_type: str,
        node_id: str,
        base_uri: str,
        password: str,
        admin_status: str,
        api_key: str,
        user: str,
    ) -> Response:
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

    async def cloud_security_config_put_aruba_security_zscaler_id1(
        self,
        node_type: str,
        node_id: str,
        base_uri: str,
        password: str,
        admin_status: str,
        api_key: str,
        user: str,
    ) -> Response:
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

    async def cloud_security_config_delete_aruba_security_zscaler_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def cloud_security_config_get_aruba_security_node_list_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_get_aruba_ips_node_list_id5(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_get_aruba_ips_siem_servers_list_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_get_aruba_ips_siem_servers_list_id2(
        self,
        node_type: str,
        node_id: str,
        siem_server_name: str,
    ) -> Response:
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

    async def ids_ips_config_post_aruba_ips_siem_servers_list_id2(
        self,
        node_type: str,
        node_id: str,
        siem_server_name: str,
        siem_index: str,
        new_siem_server_name: str,
        siem_server_url: str,
        siem_token: str,
    ) -> Response:
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

    async def ids_ips_config_put_aruba_ips_siem_servers_list_id2(
        self,
        node_type: str,
        node_id: str,
        siem_server_name: str,
        siem_index: str,
        new_siem_server_name: str,
        siem_server_url: str,
        siem_token: str,
    ) -> Response:
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

    async def ids_ips_config_delete_aruba_ips_siem_servers_list_id2(
        self,
        node_type: str,
        node_id: str,
        siem_server_name: str,
    ) -> Response:
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

    async def ids_ips_config_get_aruba_ips_siem_notification_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_post_aruba_ips_siem_notification_id1(
        self,
        node_type: str,
        node_id: str,
        enable: bool,
    ) -> Response:
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

    async def ids_ips_config_put_aruba_ips_siem_notification_id1(
        self,
        node_type: str,
        node_id: str,
        enable: bool,
    ) -> Response:
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

    async def ids_ips_config_delete_aruba_ips_siem_notification_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_get_aruba_ips_config_id4(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ids_ips_config_post_aruba_ips_config_id3(
        self,
        node_type: str,
        node_id: str,
        siem_servers_list: list,
        enable: bool,
    ) -> Response:
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

    async def ids_ips_config_put_aruba_ips_config_id3(
        self,
        node_type: str,
        node_id: str,
        siem_servers_list: list,
        enable: bool,
    ) -> Response:
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

    async def ids_ips_config_delete_aruba_ips_config_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ipms_config_get_aruba_ip_range_id2(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
    ) -> Response:
        """Retrieve ip_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/"

        return await self.get(url)

    async def ipms_config_get_aruba_config_id5(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def ipms_config_delete_aruba_config_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def ipms_config_get_aruba_address_pool_id4(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve address_pool.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/"

        return await self.get(url)

    async def ipms_config_get_aruba_address_pool_id3(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
    ) -> Response:
        """Retrieve address_pool by identifier pool_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        return await self.get(url)

    async def ipms_config_post_aruba_address_pool_id2(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        pool_type: str,
        new_pool_name: str,
        max_clients: int,
        ip_range: list,
        oldKey: str = None,
    ) -> Response:
        """Create address_pool by identifier pool_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            pool_type (str): Pool Type identifying whether IP address is used as Inner-IP or is used
                as part of DHCP pool  Valid Values: INNER_IP_POOL_TYPE, DHCP_POOL_TYPE
            new_pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            max_clients (int): Maximum number of clients that can be allocated when subnets are
                carved out from this pool. This applies only to pool that are of type
                'DHCP_POOL_TYPE'
            ip_range (list): IP Address Range. The ranges must not overlap within or across pools
            oldKey (str, optional): Specify old value of 'pool_name' if it needs to be replaced

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        params = {
            'oldKey': oldKey
        }

        json_data = {
            'pool_type': pool_type,
            'new_pool_name': new_pool_name,
            'max_clients': max_clients,
            'ip_range': ip_range
        }

        return await self.post(url, json_data=json_data, params=params)

    async def ipms_config_put_aruba_address_pool_id2(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        pool_type: str,
        new_pool_name: str,
        max_clients: int,
        ip_range: list,
        oldKey: str = None,
    ) -> Response:
        """Create/Update address_pool by identifier pool_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            pool_type (str): Pool Type identifying whether IP address is used as Inner-IP or is used
                as part of DHCP pool  Valid Values: INNER_IP_POOL_TYPE, DHCP_POOL_TYPE
            new_pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            max_clients (int): Maximum number of clients that can be allocated when subnets are
                carved out from this pool. This applies only to pool that are of type
                'DHCP_POOL_TYPE'
            ip_range (list): IP Address Range. The ranges must not overlap within or across pools
            oldKey (str, optional): Specify old value of 'pool_name' if it needs to be replaced

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        params = {
            'oldKey': oldKey
        }

        json_data = {
            'pool_type': pool_type,
            'new_pool_name': new_pool_name,
            'max_clients': max_clients,
            'ip_range': ip_range
        }

        return await self.put(url, json_data=json_data, params=params)

    async def ipms_config_delete_aruba_address_pool_id2(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
    ) -> Response:
        """Delete address_pool by identifier pool_name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        return await self.delete(url)

    async def ipms_config_get_aruba_ip_range_id1(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        range_id: str,
    ) -> Response:
        """Retrieve ip_range by identifier range_id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        return await self.get(url)

    async def ipms_config_post_aruba_ip_range_id1(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        range_id: str,
        start_ip: str,
        new_range_id: str,
        end_ip: str,
        is_conflicting: bool,
    ) -> Response:
        """Create ip_range by identifier range_id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            start_ip (str): Starting IPv4 Address of the range.
            new_range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            end_ip (str): Last IPv4 Address of the range.
            is_conflicting (bool): This indicates whether this range is conflicting with any other
                range in the config. This can happen with migrated IP-ranges

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        json_data = {
            'start_ip': start_ip,
            'new_range_id': new_range_id,
            'end_ip': end_ip,
            'is_conflicting': is_conflicting
        }

        return await self.post(url, json_data=json_data)

    async def ipms_config_put_aruba_ip_range_id1(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        range_id: str,
        start_ip: str,
        new_range_id: str,
        end_ip: str,
        is_conflicting: bool,
    ) -> Response:
        """Create/Update ip_range by identifier range_id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            start_ip (str): Starting IPv4 Address of the range.
            new_range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            end_ip (str): Last IPv4 Address of the range.
            is_conflicting (bool): This indicates whether this range is conflicting with any other
                range in the config. This can happen with migrated IP-ranges

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        json_data = {
            'start_ip': start_ip,
            'new_range_id': new_range_id,
            'end_ip': end_ip,
            'is_conflicting': is_conflicting
        }

        return await self.put(url, json_data=json_data)

    async def ipms_config_delete_aruba_ip_range_id1(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        range_id: str,
    ) -> Response:
        """Delete ip_range by identifier range_id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        return await self.delete(url)

    async def ipms_config_get_aruba_node_list_id6(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def overlay_wlan_config_get_aruba_wlan_gw_cluster_list_id1(
        self,
        # node_type: str = "GROUP",
        node_id: str,
        profile: str = None,
        profile_type: str = None,
        cluster_redundancy_type: str = None,
        cluster_group_name: str = None,
    ) -> Response:
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
        node_type = "GROUP"
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/" \
            "config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

        return await self.get(url)

    async def overlay_wlan_config_post_aruba_wlan_gw_cluster_list_id1(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        cluster_redundancy_type: str,
        cluster_group_name: str,
        new_cluster_redundancy_type: str,
        cluster: str,
        new_cluster_group_name: str,
        tunnel_type: str,
        cluster_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_put_aruba_wlan_gw_cluster_list_id1(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        cluster_redundancy_type: str,
        cluster_group_name: str,
        new_cluster_redundancy_type: str,
        cluster: str,
        new_cluster_group_name: str,
        tunnel_type: str,
        cluster_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_delete_aruba_wlan_gw_cluster_list_id1(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        cluster_redundancy_type: str,
        cluster_group_name: str,
    ) -> Response:
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

    async def overlay_wlan_config_get_aruba_wlan_gw_cluster_list_id2(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_get_aruba_wlan_config_id5(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def overlay_wlan_config_post_aruba_wlan_config_id3(
        self,
        node_type: str,
        node_id: str,
        address_family: List[str],
        ssid_cluster: list,
    ) -> Response:
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

    async def overlay_wlan_config_put_aruba_wlan_config_id3(
        self,
        node_type: str,
        node_id: str,
        address_family: List[str],
        ssid_cluster: list,
    ) -> Response:
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

    async def overlay_wlan_config_delete_aruba_wlan_config_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def overlay_wlan_config_get_aruba_wlan_ssid_cluster_id3(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_post_aruba_wlan_ssid_cluster_id2(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        new_profile: str,
        gw_cluster_list: list,
        new_profile_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_put_aruba_wlan_ssid_cluster_id2(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        new_profile: str,
        gw_cluster_list: list,
        new_profile_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_delete_aruba_wlan_ssid_cluster_id2(
        self,
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
    ) -> Response:
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

    async def overlay_wlan_config_get_aruba_wlan_ssid_cluster_id4(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def overlay_wlan_config_get_aruba_wlan_node_list_id6(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_admin_status_id18(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_hub_clusters_id7(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
        new_cluster_group: str,
        new_cluster_name: str,
    ) -> Response:
        """Create/Update hub-clusters by cluster name and cluster group.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            cluster_name (str): Name of controller Cluster
            cluster_group (str): Name of controller group to which the cluster belongs
            new_cluster_group (str): Name of controller group to which the cluster belongs
            new_cluster_name (str): Name of controller Cluster

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hub-clusters/{cluster_name}/{cluster_group}/"

        json_data = {
            'new_cluster_group': new_cluster_group,
            'new_cluster_name': new_cluster_name
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_clusters_id7(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
        new_cluster_group: str,
        new_cluster_name: str,
    ) -> Response:
        """Create by hub-clusters cluster name and cluster group.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            cluster_name (str): Name of controller Cluster
            cluster_group (str): Name of controller group to which the cluster belongs
            new_cluster_group (str): Name of controller group to which the cluster belongs
            new_cluster_name (str): Name of controller Cluster

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hub-clusters/{cluster_name}/{cluster_group}/"

        json_data = {
            'new_cluster_group': new_cluster_group,
            'new_cluster_name': new_cluster_name
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_delete_aruba_hub_clusters_id8(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
    ) -> Response:
        """Delete by hub-clusters cluster name and cluster group.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            cluster_name (str): Name of controller Cluster
            cluster_group (str): Name of controller group to which the cluster belongs

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hub-clusters/{cluster_name}/{cluster_group}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hub_clusters_id15(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
    ) -> Response:
        """Retrieve by hub-clusters cluster name and cluster group.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            cluster_name (str): Name of controller Cluster
            cluster_group (str): Name of controller group to which the cluster belongs

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hub-clusters/{cluster_name}/{cluster_group}/"

        return await self.get(url)

    # This API is supported on ['Microbranch Group'].
    async def sdwan_config_get_aruba_hub_clusters_id16(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve hub-clusters.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hub-clusters/"

        return await self.get(url)

    async def sdwan_config_put_aruba_load_balance_orchestration_id17(
        self,
        node_type: str,
        node_id: str,
        hold_time: int,
        pre_emption: bool,
        randomize_time: int,
    ) -> Response:
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

    async def sdwan_config_post_aruba_load_balance_orchestration_id17(
        self,
        node_type: str,
        node_id: str,
        hold_time: int,
        pre_emption: bool,
        randomize_time: int,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_load_balance_orchestration_id19(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_load_balance_orchestration_id28(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_network_segment_policy_id21(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_tunnel_policy_id21(
        self,
        node_type: str,
        node_id: str,
        rekey_interval: int,
        type: str,
    ) -> Response:
        """Create/Update tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.
            type (str): Type of tunnel  Valid Values: IPSEC

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        json_data = {
            'rekey_interval': rekey_interval,
            'type': type
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_tunnel_policy_id21(
        self,
        node_type: str,
        node_id: str,
        rekey_interval: int,
        type: str,
    ) -> Response:
        """Create tunnel-policy.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GLOBAL  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must be GLOBAL
            rekey_interval (int): Time interval, in seconds, between rekeying. Value should be in
                the range 1 minute (60 seconds) to 14 days (1209600 seconds) and default is 24
                hours.
            type (str): Type of tunnel  Valid Values: IPSEC

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/tunnel-policy/"

        json_data = {
            'rekey_interval': rekey_interval,
            'type': type
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_delete_aruba_tunnel_policy_id24(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_tunnel_policy_id35(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_mesh_id4(
        self,
        label: str,
    ) -> Response:
        """Retrieve branch-mesh by label.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_transit_id3(
        self,
        node_type: str,
        node_id: str,
        transit: bool,
    ) -> Response:
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

    async def sdwan_config_post_aruba_transit_id3(
        self,
        node_type: str,
        node_id: str,
        transit: bool,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_transit_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_transit_id7(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_topology_id10(
        self,
        node_type: str,
        node_id: str,
        topology: str,
    ) -> Response:
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

    async def sdwan_config_post_aruba_topology_id10(
        self,
        node_type: str,
        node_id: str,
        topology: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_topology_id11(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_topology_id19(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_sdwan_global_id22(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_route_policy_id33(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_hub_mesh_id23(
        self,
        node_type: str,
        node_id: str,
        label: str,
        hub_groups: list,
        new_label: str,
    ) -> Response:
        """Create/Update hub-mesh by label.

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

    async def sdwan_config_post_aruba_hub_mesh_id23(
        self,
        node_type: str,
        node_id: str,
        label: str,
        hub_groups: list,
        new_label: str,
    ) -> Response:
        """Create hub-mesh by label.

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

    async def sdwan_config_delete_aruba_hub_mesh_id26(
        self,
        node_type: str,
        node_id: str,
        label: str,
    ) -> Response:
        """Delete hub-mesh by label.

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

    async def sdwan_config_get_aruba_hub_mesh_id38(
        self,
        node_type: str,
        node_id: str,
        label: str,
    ) -> Response:
        """Retrieve hub-mesh by label.

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

    # valid for GW group returns list of dicts {"Identifier": <vpnc-serial-num>}
    async def sdwan_config_get_aruba_hubs_id14(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve hubs.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BranchGateway
                group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/"

        return await self.get(url)

    async def sdwan_config_delete_aruba_config_id28(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_config_id41(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_aggregates_id11(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_as_number_id12(
        self,
        node_type: str,
        node_id: str,
        as_number: int,
    ) -> Response:
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

    async def sdwan_config_post_aruba_as_number_id12(
        self,
        node_type: str,
        node_id: str,
        as_number: int,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_as_number_id14(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_as_number_id23(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_hub_id16(
        self,
        node_type: str,
        node_id: str,
        distance_factor: int,
        prefer_overlay_path: bool,
        best_path_computation: bool,
    ) -> Response:
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

    async def sdwan_config_post_aruba_hub_id16(
        self,
        node_type: str,
        node_id: str,
        distance_factor: int,
        prefer_overlay_path: bool,
        best_path_computation: bool,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_hub_id18(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_id27(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_mesh_id5(
        self,
        last_index: str = '0',
        offset: str = 0,
        limit: int = 100,
    ) -> Response:
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

    async def sdwan_config_put_aruba_hubs_id6(
        self,
        node_type: str,
        node_id: str,
        identifier: str,
        new_identifier: str,
    ) -> Response:
        """Create/Update hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BranchGateway
                group
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

    async def sdwan_config_post_aruba_hubs_id6(
        self,
        node_type: str,
        node_id: str,
        identifier: str,
        new_identifier: str,
    ) -> Response:
        """Create hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BranchGateway
                group
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

    async def sdwan_config_delete_aruba_hubs_id7(
        self,
        node_type: str,
        node_id: str,
        identifier: str,
    ) -> Response:
        """Delete hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BranchGateway
                group
            identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hubs_id13(
        self,
        node_type: str,
        node_id: str,
        identifier: str,
    ) -> Response:
        """Retrieve hubs by device serial number.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a BranchGateway
                group
            identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_rekey_interval_id20(
        self,
        node_type: str,
        node_id: str,
        rekey_interval: int,
    ) -> Response:
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

    async def sdwan_config_post_aruba_rekey_interval_id20(
        self,
        node_type: str,
        node_id: str,
        rekey_interval: int,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_rekey_interval_id23(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_rekey_interval_id34(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_branch_devices_id1(
        self,
        label: str,
        identifier: str,
        new_identifier: str,
    ) -> Response:
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

    async def sdwan_config_post_aruba_branch_devices_id1(
        self,
        label: str,
        identifier: str,
        new_identifier: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_branch_devices_id1(
        self,
        label: str,
        identifier: str,
    ) -> Response:
        """Delete branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_branch_devices_id1(
        self,
        label: str,
        identifier: str,
    ) -> Response:
        """Retrieve branch-devices by device serial number.

        Args:
            label (str): branch-mesh label
            identifier (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/{identifier}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_best_path_computation_id15(
        self,
        node_type: str,
        node_id: str,
        best_path_computation: bool,
    ) -> Response:
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

    async def sdwan_config_post_aruba_best_path_computation_id15(
        self,
        node_type: str,
        node_id: str,
        best_path_computation: bool,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_best_path_computation_id17(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_best_path_computation_id26(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_aggregates_id9(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_aggregates_id4(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
        new_prefix: str,
    ) -> Response:
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

    async def sdwan_config_post_aruba_aggregates_id4(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
        new_prefix: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_aggregates_id4(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_aggregates_id8(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_mesh_policy_id27(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_mesh_policy_id40(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_mesh_id39(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_hub_groups_id22(
        self,
        node_type: str,
        node_id: str,
        label: str,
        name: str,
        new_name: str,
    ) -> Response:
        """Create/Update hub-groups by name.

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

    async def sdwan_config_post_aruba_hub_groups_id22(
        self,
        node_type: str,
        node_id: str,
        label: str,
        name: str,
        new_name: str,
    ) -> Response:
        """Create hub-groups by name.

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

    async def sdwan_config_delete_aruba_hub_groups_id25(
        self,
        node_type: str,
        node_id: str,
        label: str,
        name: str,
    ) -> Response:
        """Delete hub-groups by name.

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

    async def sdwan_config_get_aruba_hub_groups_id36(
        self,
        node_type: str,
        node_id: str,
        label: str,
        name: str,
    ) -> Response:
        """Retrieve hub-groups by name.

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

    async def sdwan_config_put_aruba_graceful_restart_id14(
        self,
        node_type: str,
        node_id: str,
        enabled: bool,
        timer: int,
    ) -> Response:
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

    async def sdwan_config_post_aruba_graceful_restart_id14(
        self,
        node_type: str,
        node_id: str,
        enabled: bool,
        timer: int,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_graceful_restart_id16(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_graceful_restart_id25(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_network_segment_policy_id11(
        self,
        node_type: str,
        node_id: str,
        name: str,
        new_name: str,
        load_balance: bool,
    ) -> Response:
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

    async def sdwan_config_post_aruba_network_segment_policy_id11(
        self,
        node_type: str,
        node_id: str,
        name: str,
        new_name: str,
        load_balance: bool,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_network_segment_policy_id12(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_network_segment_policy_id20(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_aggregates_id30(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_aggregates_id32(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_branch_config_id8(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hubs: list,
        hub_clusters: list,
    ) -> Response:
        """Create/Update branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group
            hubs_type (str): This indicates whether DC Preference uses induvidual VPNC devices
                ('hubs' list) or VPNC Clusters ('hub-clusters' list). Value 'HUB_TYPE_DEVICE' is
                used to indicate 'hubs' is configured. Value 'HUB_TYPE_CLUSTER' is used to indicate
                'hub-clusters' is configured  Valid Values: HUB_TYPE_DEVICE, HUB_TYPE_CLUSTER
            hubs (list): An ordered list of VPNC device identifiers.This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_DEVICE' under branch-config
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs_type': hubs_type,
            'hubs': hubs,
            'hub_clusters': hub_clusters
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_branch_config_id8(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hubs: list,
        hub_clusters: list,
    ) -> Response:
        """Create branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group
            hubs_type (str): This indicates whether DC Preference uses induvidual VPNC devices
                ('hubs' list) or VPNC Clusters ('hub-clusters' list). Value 'HUB_TYPE_DEVICE' is
                used to indicate 'hubs' is configured. Value 'HUB_TYPE_CLUSTER' is used to indicate
                'hub-clusters' is configured  Valid Values: HUB_TYPE_DEVICE, HUB_TYPE_CLUSTER
            hubs (list): An ordered list of VPNC device identifiers.This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_DEVICE' under branch-config
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs_type': hubs_type,
            'hubs': hubs,
            'hub_clusters': hub_clusters
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_delete_aruba_branch_config_id9(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Delete branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_branch_config_id17(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve branch-config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        return await self.get(url)

    async def sdwan_config_put_aruba_timer_id13(
        self,
        node_type: str,
        node_id: str,
        timer: int,
    ) -> Response:
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

    async def sdwan_config_post_aruba_timer_id13(
        self,
        node_type: str,
        node_id: str,
        timer: int,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_timer_id15(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_timer_id24(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_node_list_id42(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_config_id2(
        self,
        label: str,
        branch_devices: list,
    ) -> Response:
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

    async def sdwan_config_post_aruba_config_id2(
        self,
        label: str,
        branch_devices: list,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_config_id2(
        self,
        label: str,
    ) -> Response:
        """Delete branch-mesh config.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_config_id3(
        self,
        label: str,
    ) -> Response:
        """Retrieve branch-mesh config.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/"

        return await self.get(url)

    async def sdwan_config_put_aruba_hub_aggregates_id5(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        aggregates: list,
        new_segment: str,
    ) -> Response:
        """Create/Update DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            aggregates (list): List of IPv4 prefixes
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

    async def sdwan_config_post_aruba_hub_aggregates_id5(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        aggregates: list,
        new_segment: str,
    ) -> Response:
        """Create DC aggregate routes for given network segment.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a VPNC group
            segment (str): Overlay network segment name
            aggregates (list): List of IPv4 prefixes
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

    async def sdwan_config_delete_aruba_hub_aggregates_id5(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_aggregates_id10(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_aggregates_id18(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
        new_prefix: str,
    ) -> Response:
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

    async def sdwan_config_post_aruba_aggregates_id18(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
        new_prefix: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_aggregates_id20(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_aggregates_id29(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        prefix: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_groups_id37(
        self,
        node_type: str,
        node_id: str,
        label: str,
    ) -> Response:
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

    async def sdwan_config_put_aruba_branch_aggregates_id19(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        aggregates: list,
        new_segment: str,
    ) -> Response:
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

    async def sdwan_config_post_aruba_branch_aggregates_id19(
        self,
        node_type: str,
        node_id: str,
        segment: str,
        aggregates: list,
        new_segment: str,
    ) -> Response:
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

    async def sdwan_config_delete_aruba_branch_aggregates_id21(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_aggregates_id31(
        self,
        node_type: str,
        node_id: str,
        segment: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_mesh_ui_id6(
        self,
        last_index: str = '0',
        offset: str = 0,
        limit: int = 100,
    ) -> Response:
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

    async def sdwan_config_get_aruba_hub_config_id12(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def sdwan_config_get_aruba_branch_devices_id2(
        self,
        label: str,
    ) -> Response:
        """Retrieve branch-devices.

        Args:
            label (str): branch-mesh label

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/branch-mesh/{label}/config/branch-devices/"

        return await self.get(url)

    async def ucc_config_get_aruba_dns_patterns_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_sip_id5(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_sip_id4(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
    ) -> Response:
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

    async def ucc_config_put_aruba_sip_id4(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
    ) -> Response:
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

    async def ucc_config_delete_aruba_sip_id4(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_skype4b_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_skype4b_id1(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
    ) -> Response:
        """Create skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_skype4b_id1(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
    ) -> Response:
        """Create/Update skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_skype4b_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_ucc_settings_id8(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_ucc_settings_id7(
        self,
        node_type: str,
        node_id: str,
        activate: bool,
        enable_call_prioritization: bool,
    ) -> Response:
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

    async def ucc_config_put_aruba_ucc_settings_id7(
        self,
        node_type: str,
        node_id: str,
        activate: bool,
        enable_call_prioritization: bool,
    ) -> Response:
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

    async def ucc_config_delete_aruba_ucc_settings_id7(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_node_list_id10(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_dns_patterns_id2(
        self,
        node_type: str,
        node_id: str,
        dns_pattern: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_dns_patterns_id2(
        self,
        node_type: str,
        node_id: str,
        dns_pattern: str,
        carrier_service_provider: str,
        new_dns_pattern: str,
    ) -> Response:
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

    async def ucc_config_put_aruba_dns_patterns_id2(
        self,
        node_type: str,
        node_id: str,
        dns_pattern: str,
        carrier_service_provider: str,
        new_dns_pattern: str,
    ) -> Response:
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

    async def ucc_config_delete_aruba_dns_patterns_id2(
        self,
        node_type: str,
        node_id: str,
        dns_pattern: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_config_id9(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_config_id8(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
        activate: bool,
        enable_call_prioritization: bool,
    ) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_config_id8(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
        activate: bool,
        enable_call_prioritization: bool,
    ) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_config_id8(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_wifi_calling_id4(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_wifi_calling_id3(
        self,
        node_type: str,
        node_id: str,
        voice_priority: int,
        dns_patterns: list,
    ) -> Response:
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

    async def ucc_config_put_aruba_wifi_calling_id3(
        self,
        node_type: str,
        node_id: str,
        voice_priority: int,
        dns_patterns: list,
    ) -> Response:
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

    async def ucc_config_delete_aruba_wifi_calling_id3(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_ucc_alg_id6(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_ucc_alg_id5(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
        dns_patterns: list,
    ) -> Response:
        """Create ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'dns_patterns': dns_patterns
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_ucc_alg_id5(
        self,
        node_type: str,
        node_id: str,
        video_priority: int,
        voice_priority: int,
        dns_patterns: list,
    ) -> Response:
        """Create/Update ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'video_priority': video_priority,
            'voice_priority': voice_priority,
            'dns_patterns': dns_patterns
        }

        return await self.put(url, json_data=json_data)

    async def ucc_config_delete_aruba_ucc_alg_id5(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_get_aruba_activate_id7(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def ucc_config_post_aruba_activate_id6(
        self,
        node_type: str,
        node_id: str,
        activate: bool,
    ) -> Response:
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

    async def ucc_config_put_aruba_activate_id6(
        self,
        node_type: str,
        node_id: str,
        activate: bool,
    ) -> Response:
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

    async def ucc_config_delete_aruba_activate_id6(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def topology_external_display_topology(
        self,
        site_id: int,
    ) -> Response:
        """Get topology details of a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/{site_id}"

        return await self.get(url)

    async def topology_external_display_devices(
        self,
        device_serial: str,
    ) -> Response:
        """Get details of a device.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/devices/{device_serial}"

        return await self.get(url)

    async def topology_external_display_edges(
        self,
        source_serial: str,
        dest_serial: str,
    ) -> Response:
        """Get details of an edge.

        Args:
            source_serial (str): Device serial number.
            dest_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/edges/{source_serial}/{dest_serial}"

        return await self.get(url)

    async def topology_external_display_edges_v2(
        self,
        source_serial: str,
        dest_serial: str,
    ) -> Response:
        """Get details of an edge for the selected source and destination.

        Args:
            source_serial (str): Device serial number.
            dest_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/v2/edges/{source_serial}/{dest_serial}"

        return await self.get(url)

    async def topology_external_display_uplinks(
        self,
        source_serial: str,
        uplink_id: str,
    ) -> Response:
        """Get details of an uplink.

        Args:
            source_serial (str): Device serial number.
            uplink_id (str): Uplink id.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/uplinks/{source_serial}/{uplink_id}"

        return await self.get(url)

    async def topology_external_display_gettunnel(
        self,
        site_id: int,
        tunnel_map_names: List[str],
    ) -> Response:
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

    async def topology_external_display_ap_neighbors(
        self,
        device_serial: str,
    ) -> Response:
        """Get neighbor details reported by AP via LLDP.

        Args:
            device_serial (str): Device serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/apNeighbors/{device_serial}"

        return await self.get(url)

    async def topology_external_display_vlans(
        self,
        site_id: int,
        search: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def topology_external_display_expiring_devices(
        self,
        site_id: int,
    ) -> Response:
        """Get list of unreachable devices in a site.

        Args:
            site_id (int): Site ID.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/topology_external_api/unreachableDevices/{site_id}"

        return await self.get(url)

    async def troubleshooting_get_commands_list(
        self,
        device_type: str,
    ) -> Response:
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

    async def troubleshooting_start_troubleshoot(
        self,
        serial: str,
        device_type: str,
        commands: list,
    ) -> Response:
        """Start Troubleshooting Session.

        Args:
            serial (str): Serial of device
            device_type (str): Specify one of "IAP/SWITCH/CX/MAS/CONTROLLER" for  IAPs, Aruba
                switches, CX Switches, MAS switches and controllers respectively.
            commands (list): List of command ids use get_command_list to get command to id map.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}"

        json_data = {
            'device_type': device_type,
            'commands': commands
        }

        return await self.post(url, json_data=json_data)

    async def troubleshooting_get_troubleshoot_output(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
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

    async def troubleshooting_clear_session(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Clear Troubleshooting Session.

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

        return await self.delete(url, params=params)

    # API-FLAW returns 404 if there are no sessions running
    async def troubleshooting_get_session_id(
        self,
        serial: str,
    ) -> Response:
        """Get Troubleshooting Session ID.

        Args:
            serial (str): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/session"

        return await self.get(url)

    async def troubleshooting_export_output(
        self,
        serial: str,
        session_id: int,
    ) -> Response:
        """Export Troubleshooting Output.

        Args:
            serial (str): Serial of device
            session_id (int): Unique ID for each troubleshooting session

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/devices/{serial}/export"

        params = {
            'session_id': session_id
        }

        return await self.get(url, params=params)

    async def tools_send_enroll_pki_certificate_switch(
        self,
        serial: str,
        est_profile_name: str,
        cert_name: str,
    ) -> Response:
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

    async def troubleshooting_post_running_config_backup_serial(
        self,
        serial: str,
        prefix: str,
    ) -> Response:
        """Initiate Running Config Backup For A Single Device.

        Args:
            serial (str): Serial of device
            prefix (str): Name prefix for name of long term named storage. Must be 3 - 64
                characters. Must start with a letter or number.                           Can
                contain the following special characters: '-', ',', '?', '!', '+', '&', '@', ':',
                ';', '(', ')', '_', '.', '*'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/running-config-backup/serial/{serial}/prefix/{prefix}"

        return await self.post(url)

    async def troubleshooting_get_named_backups_for_serial_prefix(
        self,
        serial: str,
        prefix: str,
    ) -> Response:
        """Get list of backups associated with the device serial with the given prefix.

        Args:
            serial (str): Serial of device
            prefix (str): Name prefix for name of long term named storage. Must be 3 - 64
                characters. Must start with a letter or number.
                Can contain the following special characters: '-', ',', '?', '!', '+', '&', '@',
                ':', ';', '(', ')', '_', '.', '*'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/running-config-backup/serial/{serial}/prefix/{prefix}"

        return await self.get(url)

    async def troubleshooting_post_running_config_backup_group_name(
        self,
        group_name: str,
        prefix: str,
    ) -> Response:
        """Initiate Running Config Backup For All Devices In A Group.

        Args:
            group_name (str): Group name of the group of interest
            prefix (str): Name prefix for name of long term named storage. Must be 3 - 64
                characters. Must start with a letter or number.
                Can contain the following special characters: '-', ',', '?', '!', '+', '&', '@',
                ':', ';', '(', ')', '_', '.', '*'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/running-config-backup/group_name/{group_name}/prefix/{prefix}"

        return await self.post(url)

    async def troubleshooting_get_named_backups_for_serial(
        self,
        serial: str,
    ) -> Response:
        """Get list of backups associated with the device serial.

        Args:
            serial (str): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/running-config-backup/serial/{serial}"

        return await self.get(url)

    async def troubleshooting_get_running_config_backup_with_name(
        self,
        name: str,
    ) -> Response:
        """Fetch the backup stored against the given name.

        Args:
            name (str): Name of the backup to fetch

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/troubleshooting/v1/running-config-backup/name/{name}"

        return await self.get(url)

    async def ucc_get_uc_summary(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_clients(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_count_by_st(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_session_count_by_protocol(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_sq_by_st(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_sq_by_ssid(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_insights_count(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_insights(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def ucc_get_uc_cdrs(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def ucc_export_uc_cdrs(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
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

    async def ucc_get_uc_skype_elb(
        self,
    ) -> Response:
        """Fetch skype server central termination URL.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/ucc/v1/SkypeCentralURL"

        return await self.get(url)

    async def platform_get_user_accounts(
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

    async def platform_create_user_account(
        self,
        username: str = None,
        password: str = None,
        description: str = None,
        firstname: str = None,
        lastname: str = None,
        phone: str = None,
        street: str = None,
        city: str = None,
        state: str = None,
        country: str = None,
        zipcode: str = None,
        applications: list = None,
    ) -> Response:
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

    async def platform_update_user_account(
        self,
        user_id: str,
        username: str = None,
        description: str = None,
        firstname: str = None,
        lastname: str = None,
        phone: str = None,
        street: str = None,
        city: str = None,
        state: str = None,
        country: str = None,
        zipcode: str = None,
        applications: list = None,
    ) -> Response:
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

    async def platform_get_user_account_details(
        self,
        user_id: str,
        system_user: bool = True,
    ) -> Response:
        """Get user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': str(system_user).lower()
        }

        return await self.get(url, params=params)

    async def platform_delete_user_account(
        self,
        user_id: str,
        system_user: bool = True,
    ) -> Response:
        """delete user account details specified by user id.

        Args:
            user_id (str): User's email id is specified as the user id
            system_user (bool, optional): false if federated user. Defaults to true

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/users/{user_id}"

        params = {
            'system_user': str(system_user).lower()
        }

        return await self.delete(url, params=params)

    async def platform_change_user_password(
        self,
        current_password: str,
        new_password: str,
        user_id: str,
    ) -> Response:
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

    async def platform_reset_user_password(
        self,
        password: str,
        user_id: str,
    ) -> Response:
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

    async def platform_create_bulk_users_account(
        self,
        NoName: list = None,
    ) -> Response:
        """Create multiple users account. The max no of accounts that can be created at once is 10.

        Args:
            NoName (list, optional): List of user attributes.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.post(url)

    async def platform_update_bulk_users_account(
        self,
        NoName: list = None,
    ) -> Response:
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

    async def platform_delete_bulk_users_account(
        self,
        user_list: List[str],
    ) -> Response:
        """Delete multiple users account. The max no of accounts that can be deleted at once is 10.

        Args:
            user_list (List[str], optional): List of user id's to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        json_data = user_list

        return await self.delete(url, json_data=json_data)

    async def platform_bulk_users_get_cookie_status(
        self,
        cookie_name: str,
    ) -> Response:
        """Get task status.

        Args:
            cookie_name (str): Specify the name of the cookie received after doing bulk operation.
                This status will be available for 1 hour.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/status/{cookie_name}"

        return await self.get(url)

    async def platform_get_roles(
        self,
        app_name: str = None,
        order_by: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def platform_get_role(
        self,
        rolename: str,
        app_name: str,
    ) -> Response:
        """Get Role details.

        Args:
            rolename (str): role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.get(url)

    async def platform_delete_role(
        self,
        rolename: str,
        app_name: str,
    ) -> Response:
        """Delete a  role.

        Args:
            rolename (str): User role name
            app_name (str): app name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/rbac/v1/apps/{app_name}/roles/{rolename}"

        return await self.delete(url)

    async def platform_update_role(
        self,
        rolename: str,
        app_name: str,
        new_rolename: str,
        permission: str,
        applications: list,
    ) -> Response:
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

    async def platform_create_role(
        self,
        rolename: str,
        permission: str,
        applications: list,
        app_name: str,
    ) -> Response:
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

    async def get_visualrf_v1_client_location(
        self,
        macaddr: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get location of a specific client.

        Args:
            macaddr (str): Provide a macaddr returned by
                /visualrf_api/v1/floor/{floor_id}/*_location api. Example:
                /visualrf_api/v1/client_location/ac:37:43:a9:ec:10
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/client_location/{macaddr}"

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_visualrf_v1_floor_client_location(
        self,
        floor_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get a specific floor and location of all its clients.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/client_location"

        return await self.get(url)

    async def get_visualrf_v1_rogue_location(
        self,
        macaddr: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get location of a specific rogue access point.

        Args:
            macaddr (str): Provide a macaddr returned by
                /visualrf_api/v1/floor/{floor_id}/*_location api. Example:
                /visualrf_api/v1/client_location/ac:37:43:a9:ec:10
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/rogue_location/{macaddr}"

        return await self.get(url)

    async def get_visualrf_v1_floor_rogue_location(
        self,
        floor_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get a specific floor and location of all its rogue access points.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/rogue_location"

        return await self.get(url)

    async def get_visualrf_v1_building(
        self,
        building_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get a specific building and its floors.

        Args:
            building_id (str): Provide building_id returned by /visualrf_api/v1/campus/{campus_id}
                api. Example:
                /visualrf_api/v1/building/201610193176__f2267635-d1b5-4e33-be9b-2bf7dbd6f885
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/building/{building_id}"

        return await self.get(url)

    async def get_visualrf_v1_floor(
        self,
        floor_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get details of a specific floor.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}"

        return await self.get(url)

    async def get_visualrf_v1_floor_image(
        self,
        floor_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get background image of a specific floor.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/image"

        return await self.get(url)

    async def get_visualrf_v1_floor_access_point_location(
        self,
        floor_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get a specific floor and location of all its access points.

        Args:
            floor_id (str): Provide floor_id returned by /visualrf_api/v1/building/{building_id api.
                Example: /visualrf_api/v1/floor/201610193176__39295d71-fac8-4837-8a91-c1798b51a2ad
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/floor/{floor_id}/access_point_location"

        return await self.get(url)

    async def get_visualrf_v1_access_point_location(
        self,
        ap_id: str,
        units: str = 'FEET',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get location of a specific access point.

        Args:
            ap_id (str): Provide ap_id returned by
                /visualrf_api/v1/floor/{floor_id}/access_point_location api. Example:
                /visualrf_api/v1/access_point_location/201610193176__B4:5D:50:C5:DA:5A
            units (str, optional): METERS or FEET  Valid Values: METERS, FEET
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/access_point_location/{ap_id}"

        return await self.get(url)
