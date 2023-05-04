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

    async def platform_get_metadata(
        self,
        domain: str,
    ) -> Response:
        """Get saml metadata.

        Args:
            domain (str): domain name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/aaa_config/v2/authentication/profiles/metadata/{domain}"

        return await self.get(url)

    async def platform_get_domain_list(
        self,
    ) -> Response:
        """Get domain list.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v2/authentication/idp/source"

        return await self.get(url)

    async def platform_add_authentication_source(
        self,
        domain: str = None,
        entity_id: str = None,
        login_url: str = None,
        logout_url: str = None,
        signing_certificate: str = None,
        email: str = None,
        first_name: str = 'fn_not_configured',
        last_name: str = 'ln_not_configured',
        idle_session_timeout: int = 15,
        hpe_ccs_attribute: str = None,
        username: str = None,
        password: str = None,
        recovery_email: str = None,
    ) -> Response:
        """Add IDP config.

        Args:
            domain (str, optional): Name of the domain
            entity_id (str, optional): Entity ID of the SAML configuration
            login_url (str, optional): Login URL of the IDP
            logout_url (str, optional): Logout url of the IDP
            signing_certificate (str, optional): X.509 signing certificate
            email (str, optional): Email field attribute
            first_name (str, optional): First name field attribute
            last_name (str, optional): Last name field attribute
            idle_session_timeout (int, optional): Idle session timeout for the federated users
            hpe_ccs_attribute (str, optional): IDP attribute that maps to HPE's custom attribute
            username (str, optional): username of Recovery/fallback user
            password (str, optional): password of Recovery/fallback user
            recovery_email (str, optional): An email to reset password of recovery user

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v2/authentication/idp/source"

        json_data = {
            'domain': domain,
            'entity_id': entity_id,
            'login_url': login_url,
            'logout_url': logout_url,
            'signing_certificate': signing_certificate,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'idle_session_timeout': idle_session_timeout,
            'hpe_ccs_attribute': hpe_ccs_attribute,
            'username': username,
            'password': password,
            'recovery_email': recovery_email
        }

        return await self.post(url, json_data=json_data)

    async def platform_update_idp_config(
        self,
        domain: str = None,
        entity_id: str = None,
        login_url: str = None,
        logout_url: str = None,
        signing_certificate: str = None,
        email: str = None,
        first_name: str = 'fn_not_configured',
        last_name: str = 'ln_not_configured',
        idle_session_timeout: int = 15,
        hpe_ccs_attribute: str = None,
        username: str = None,
        password: str = None,
        recovery_email: str = None,
    ) -> Response:
        """Update IDP configuration.

        Args:
            domain (str, optional): Name of the domain
            entity_id (str, optional): Entity ID of the SAML configuration
            login_url (str, optional): Login URL of the IDP
            logout_url (str, optional): Logout url of the IDP
            signing_certificate (str, optional): X.509 signing certificate
            email (str, optional): Email field attribute
            first_name (str, optional): First name field attribute
            last_name (str, optional): Last name field attribute
            idle_session_timeout (int, optional): Idle session timeout for the federated users
            hpe_ccs_attribute (str, optional): IDP attribute that maps to HPE's custom attribute
            username (str, optional): username of Recovery/fallback user
            password (str, optional): password of Recovery/fallback user
            recovery_email (str, optional): An email to reset password of recovery user

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v2/authentication/idp/source"

        json_data = {
            'domain': domain,
            'entity_id': entity_id,
            'login_url': login_url,
            'logout_url': logout_url,
            'signing_certificate': signing_certificate,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'idle_session_timeout': idle_session_timeout,
            'hpe_ccs_attribute': hpe_ccs_attribute,
            'username': username,
            'password': password,
            'recovery_email': recovery_email
        }

        return await self.put(url, json_data=json_data)

    async def platform_delete_domain(
        self,
        domain: str,
    ) -> Response:
        """Un-claim domain.

        Args:
            domain (str): domain name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/platform/aaa_config/v2/authentication/idp/source/{domain}"

        return await self.delete(url)

    async def platform_extract_metadata(
        self,
        saml_meta_data: Union[Path, str],
    ) -> Response:
        """Extract Saml metadata from file.

        Args:
            saml_meta_data (Union[Path, str]): file object

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/aaa_config/v2/authentication/idp/source/extract/metadata"
        saml_meta_data = saml_meta_data if isinstance(saml_meta_data, Path) else Path(str(saml_meta_data))

        return await self.post(url)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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
            'from_ms': from_ms,
            'to': to
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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

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

        params = {
            'from_ms': from_ms,
            'to': to
        }

        return await self.get(url, params=params)

    async def airgroup_get_traffic_summary(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
        """Get AirGroup Traffic Summary in terms of Packets.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): Label to filter the output. Default is 'all'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/traffic"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def airgroup_get_trends(
        self,
        start_time: int,
        end_time: int,
        trend_type: str,
        label: str = None,
    ) -> Response:
        """Get temporal data about AirGroup based on the parameter passed.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            trend_type (str): suppressed_serviced_traffic or service_traffic
            label (str, optional): Label to filter the output. Default is 'all'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/trend"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'trend_type': trend_type,
            'label': label
        }

        return await self.get(url, params=params)

    async def airgroup_get_device_summary(
        self,
    ) -> Response:
        """Retrieves device summary.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/devices"

        return await self.get(url)

    async def airgroup_get_label_list_by_cid(
        self,
    ) -> Response:
        """Retrieves list of labels.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/labels"

        return await self.get(url)

    async def airgroup_get_service_query_summary(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
        """Retrieves a summary of all the services queried for.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): Label ID to filter the output. Default is 'all'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/distribution/services"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def airgroup_get_server_distribution(
        self,
        start_time: int,
        end_time: int,
        label: str = None,
    ) -> Response:
        """Retrieves a summary of the servers connected to AirGroup.

        Args:
            start_time (int): start time in epoch
            end_time (int): stop time in epoch
            label (str, optional): Label to filter the output. Default is 'all'

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/distribution/servers"

        params = {
            'start_time': start_time,
            'end_time': end_time,
            'label': label
        }

        return await self.get(url, params=params)

    async def airgroup_get_uncached_serviceid(
        self,
    ) -> Response:
        """Get all the uncached services encountered by AirGroup.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/uncached_services"

        return await self.get(url)

    async def airgroup_get_hostname(
        self,
    ) -> Response:
        """Retrieves a list of all hostnames.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/hostnames"

        return await self.get(url)

    async def airgroup_get_suppression_factor(
        self,
    ) -> Response:
        """Retrieves the suppression factor.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/stats/suppression"

        return await self.get(url)

    async def airmatch_get_rep_radio_by_radio_mac(
        self,
        radio_mac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get reporting_radio of a specific Radio MAC.

        Args:
            radio_mac (str): Radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/reporting_radio/{radio_mac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_rep_radio(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get All reporting_radio for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/reporting_radio_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_ap_info_by_eth_mac(
        self,
        ap_eth_mac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get ap_info of a specific AP Ethernet MAC.

        Args:
            ap_eth_mac (str): AP Ethernet MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/ap_info/{ap_eth_mac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_ap_info(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get ap_info for all APs.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/ap_info_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_nbr_pathloss_by_nbr_band(
        self,
        radio_mac: str,
        nbr_mac: str,
        band: str,
        tenant_id: str = None,
    ) -> Response:
        """Get nbr_pathloss of a Neighbor Mac heard by a specific Radio Mac.

        Args:
            radio_mac (str): Heard Radio MAC address
            nbr_mac (str): Neighbor's MAC address
            band (str): Band of the Heard's Radio Mac
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/nbr_pathloss/{radio_mac}/{nbr_mac}/{band}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_nbr_pathloss(
        self,
        band: str,
        tenant_id: str = None,
    ) -> Response:
        """Get All nbr_pathloss for a Customer and Band.

        Args:
            band (str): Heard on a specific Band
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/nbr_pathloss_all/{band}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_rf_events_by_radio_mac(
        self,
        radio_mac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get rf_events of a specific Radio MAC.

        Args:
            radio_mac (str): Radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/rf_events/{radio_mac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_priority_rf_events_by_radio_mac(
        self,
        radio_mac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get radar and noise RF events of a specific Radio MAC.

        Args:
            radio_mac (str): Radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/priority_rf_events/{radio_mac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_history_by_radio_mac(
        self,
        radio_mac: str,
        band: str,
        tenant_id: str = None,
    ) -> Response:
        """Get history of a specific Radio MAC.

        Args:
            radio_mac (str): Radio MAC address
            band (str): Heard on a specific Band
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/history/{radio_mac}/{band}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_radio_all_nbr_pathloss(
        self,
        radio_mac: str,
        band: str,
        tenant_id: str = None,
    ) -> Response:
        """Get All nbr_pathloss for a Customer and Radio-Mac.

        Args:
            radio_mac (str): Radio MAC address
            band (str): Heard on a specific Band
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/telemetry/v1/nbr_pathloss_radio/{radio_mac}/{band}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_static_radios(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get All Static Radios for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/static_radio_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_advanced_stat_ap(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get Number of APs and AP Models.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/adv_ap_stats"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_advanced_stat_eirp(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get EIRP Distribution.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/adv_eirp_distrubution"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_advanced_stat_eirp_reason(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get EIRP Reasons.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/adv_eirp_reason"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_advanced_stat_radio(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get Information about Radio.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/adv_stat_radio"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_adv_stat_nbr(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get Neighbor stats information.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/adv_stat_nbr"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_rf_events(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get all rf_events of a tenant-id.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/rf_events_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_priority_rf_events(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get all radar and noise RF events of a tenant.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/priority_rf_events_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_bootstrap(
        self,
        bootstrap_type: str,
        tenant_id: str = None,
    ) -> Response:
        """Bootstrap.

        Args:
            bootstrap_type (str): Bootstrap type
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/bootstrap"

        params = {
            'bootstrap_type': bootstrap_type,
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_purge(
        self,
        purge_type: str,
        tenant_id: str = None,
    ) -> Response:
        """Purge.

        Args:
            purge_type (str): Purge type
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/telemetry/v1/purge"

        params = {
            'purge_type': purge_type,
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_optimization_get_req(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get optimizations for tenant.

        Args:
            tenant_id (str, optional): tenant to get the solution

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/solver/v1/optimization"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_optimization_post_req(
        self,
        tenant_id: str = None,
    ) -> Response:
        """run the algorithm for the solution.

        Args:
            tenant_id (str, optional): tenant to run the solution

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/solver/v1/optimization"

        params = {
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_get_radio_plan_by_radio_mac(
        self,
        radio_mac: str,
        tenant_id: str = None,
        debug: bool = None,
    ) -> Response:
        """Get solution of a specific Radio MAC.

        Args:
            radio_mac (str): Radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID
            debug (bool, optional): Trigger to switch between debug level and Nondebug level
                information

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/solver/v1/radio_plan/{radio_mac}"

        params = {
            'tenant_id': tenant_id,
            'debug': debug
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_radio_plan(
        self,
        tenant_id: str = None,
        band: str = None,
        debug: bool = None,
    ) -> Response:
        """Get All solutions for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID
            band (str, optional): Radio Frequency Band Filter  Valid Values: 2.4ghz, 5ghz
            debug (bool, optional): Trigger to switch between debug level and Nondebug level
                information

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/solver/v1/radio_plan"

        params = {
            'tenant_id': tenant_id,
            'band': band,
            'debug': debug
        }

        return await self.get(url, params=params)

    async def airmatch_get_optimization_per_partition(
        self,
        rf_id: str,
        partition_id: str,
        tenant_id: str = None,
    ) -> Response:
        """Get optimizations for tenant's requested partition.

        Args:
            rf_id (str): RF Domain Id
            partition_id (str): Partition number
            tenant_id (str, optional): tenant to get the solution

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/solver/v1/optimization_partition/{rf_id}/{partition_id}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_adv_state_deployment(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Gets Radios Deployment Status.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/solver/v1/advanced_deployment_stats"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_tenant_svc_config_update(
        self,
        tenant_id: str = None,
    ) -> Response:
        """RMQ message triggers a recompute of the schedule due to change in tenant timezone/deploy
        hour details.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/svc-config-update"

        params = {
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_trigger_runnow(
        self,
        runnow_type: str,
        tenant_id: str = None,
    ) -> Response:
        """RMQ message triggers a runnow job for a certain tenant.

        Args:
            runnow_type (str): Runnow type
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/runnow"

        params = {
            'runnow_type': runnow_type,
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_get_schedule(
        self,
        tenant_id: str = None,
    ) -> Response:
        """get the schedule of all jobs computed by the scheduler.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/schedule"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_get_deploy_jobs(
        self,
        tenant_id: str = None,
    ) -> Response:
        """get the jobs to be sent to deployer for airmatch solution deployment.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/deploy-jobs"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_get_job_list(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get the list of jobs generated by Scheduler.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/job-list"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_get_tenant_tz_deploy_hr_info(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get the list of unique timezone and deploy hours per tenant.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/tenant-tz-deploy-hr-info"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_trigger_solver_job(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Trigger - RMQ message with on-demand compute for a provided tenant-id.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/scheduler/v1/trigger-solver-job"

        params = {
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_update_feasibility(
        self,
        radio_mac: str,
        tenant_id: str = None,
    ) -> Response:
        """Trigger update of radio feasibility.

        Args:
            radio_mac (str): Update a single radio feasibility
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/receiver/v1/radio_feasibility_update/{radio_mac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.put(url, params=params)

    async def airmatch_get_radio_feas_by_radio_mac(
        self,
        radioMac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get radio_feasibility of a specific radio MAC.

        Args:
            radioMac (str): radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/receiver/v1/radio_feasibility/{radioMac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_radio_feas(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get All radio_feasibility for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/radio_feasibility_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_device_config(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Returns all Device (AP) Running Configuration for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/devices_config_all"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_device_config(
        self,
        ap_serial: str,
        tenant_id: str = None,
    ) -> Response:
        """Returns Device (AP) Running Configuration.

        Args:
            ap_serial (str): AP Serial Num
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/receiver/v1/device_config/{ap_serial}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_set_device_config(
        self,
        ap_serial: str,
        device_mac: str,
        static_chan: int,
        static_pwr: int,
        opmodes: List[str],
        tenant_id: str = None,
        CBW20: List[int] = None,
        CBW40: List[int] = None,
    ) -> Response:
        """Change a device Running Config.

        Args:
            ap_serial (str): AP Serial Num
            device_mac (str): Device MAC Address
            static_chan (int): Static Channel
            static_pwr (int): Static Power
            opmodes (List[str]): opmodes
            tenant_id (str, optional): Customer(Tenant) ID
            CBW20 (List[int], optional): CBW20
            CBW40 (List[int], optional): CBW40

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/receiver/v1/device_config_set/{ap_serial}"

        params = {
            'tenant_id': tenant_id
        }

        json_data = {
            'device_mac': device_mac,
            'static_chan': static_chan,
            'static_pwr': static_pwr,
            'opmodes': opmodes,
            'CBW20': CBW20,
            'CBW40': CBW40
        }

        return await self.put(url, json_data=json_data, params=params)

    async def airmatch_get_all_service_config(
        self,
    ) -> Response:
        """Returns All Device (AP) Running Configuration for all customers.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/service_config_all"

        return await self.get(url)

    async def airmatch_get_service_config(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Returns Device (AP) Running Configuration.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/service_config"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_advanced_stat_eirp_feasible_range(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get EIRP Reasons.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/adv_eirp_range"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_radio_feas_by_radio_mac(
        self,
        radioMac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get radio_feasibility of a specific radio MAC.

        Args:
            radioMac (str): radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/radio_feasibility/{radioMac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_all_radio_feas(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Get All radio_feasibility for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/feasibility/v1/radio_feasibility"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_device_config(
        self,
        ap_serial: str,
        tenant_id: str = None,
    ) -> Response:
        """Returns Device (AP) Running Configuration.

        Args:
            ap_serial (str): AP Serial Num
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/device_config/{ap_serial}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_set_device_config(
        self,
        ap_serial: str,
        device_mac: str,
        static_chan: int,
        static_pwr: int,
        opmodes: List[str],
        tenant_id: str = None,
        CBW20: List[int] = None,
        CBW40: List[int] = None,
    ) -> Response:
        """Change a device Running Config.

        Args:
            ap_serial (str): AP Serial Num
            device_mac (str): Device MAC Address
            static_chan (int): Static Channel
            static_pwr (int): Static Power
            opmodes (List[str]): opmodes
            tenant_id (str, optional): Customer(Tenant) ID
            CBW20 (List[int], optional): CBW20
            CBW40 (List[int], optional): CBW40

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/device_config/{ap_serial}"

        params = {
            'tenant_id': tenant_id
        }

        json_data = {
            'device_mac': device_mac,
            'static_chan': static_chan,
            'static_pwr': static_pwr,
            'opmodes': opmodes,
            'CBW20': CBW20,
            'CBW40': CBW40
        }

        return await self.put(url, json_data=json_data, params=params)

    async def airmatch_get_all_device_config(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Returns all Device (AP) Running Configuration for a Customer.

        Args:
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/feasibility/v1/device_config"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_ap_info_by_serial(
        self,
        ap_serial: str,
        tenant_id: str = None,
    ) -> Response:
        """Get feasibility ap_info of a specific AP Ethernet MAC.

        Args:
            ap_serial (str): AP Serial
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/ap_info/{ap_serial}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_feas_radio_info(
        self,
        radioMac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get Feasibility Radio info of a specific radio MAC.

        Args:
            radioMac (str): radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/radio_info/{radioMac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_get_radio_board_limit(
        self,
        radioMac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get board limits of a specific radio MAC.

        Args:
            radioMac (str): radio MAC address
            tenant_id (str, optional): Customer(Tenant) ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/feasibility/v1/board_limit/{radioMac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_get_pending_deployments(
        self,
        tenant_id: str = None,
        deploy_hour: int = None,
    ) -> Response:
        """get a list of pending deployments for a tenant-id.

        Args:
            tenant_id (str, optional): tenant id
            deploy_hour (int, optional): deploy Hour

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/deployer/v1/pending_deployments"

        params = {
            'tenant_id': tenant_id,
            'deploy_hour': deploy_hour
        }

        return await self.get(url, params=params)

    async def airmatch_process_triger_computation_complete(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Trigger Computation complete message.

        Args:
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/deployer/v1/trigger_computation_complete"

        params = {
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_test_action_msg(
        self,
        mac: str,
        opmode: str,
        cbw: str,
        chan: int,
        eirp: int,
        tenant_id: str = None,
    ) -> Response:
        """RMQ message generates southbound test action-msg.

        Args:
            mac (str): Radio MAC ID
            opmode (str): AP operational Mode
            cbw (str): Radio Channel Bandwidth
            chan (int): Radio Channel
            eirp (int): Radio EIRP (power)
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/deployer/v1/trigger_test_action_msg"

        params = {
            'mac': mac,
            'opmode': opmode,
            'cbw': cbw,
            'chan': chan,
            'eirp': eirp,
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_test_config(
        self,
        disallow_action_msg: bool,
        tenant_id: str = None,
    ) -> Response:
        """Trigger test-config update.

        Args:
            disallow_action_msg (bool): Disallow sending southbound action msg
            tenant_id (str, optional): tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/deployer/v1/test_config_update"

        params = {
            'disallow_action_msg': disallow_action_msg,
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def airmatch_process_ap_neighbors_get_req(
        self,
        apserialnum: str,
        tenant_id: str = None,
        count: int = None,
        max_pathloss: int = None,
        ap_mac: bool = None,
    ) -> Response:
        """Get AP neighbor list.

        Args:
            apserialnum (str): AP Serial Number to get Neighbors for
            tenant_id (str, optional): ID to look up AP list
            count (int, optional): Number of AP serial numbers to get
            max_pathloss (int, optional): Neighbors up to this max pathloss
            ap_mac (bool, optional): Return ap mac along with ap serial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/ap_nbr_graph/v1/Ap/NeighborList/{apserialnum}"

        params = {
            'tenant_id': tenant_id,
            'count': count,
            'max_pathloss': max_pathloss,
            'ap_mac': ap_mac
        }

        return await self.get(url, params=params)

    async def airmatch_process_radio_neighbors_get_req(
        self,
        radiomac: str,
        tenant_id: str = None,
    ) -> Response:
        """Get Radio neighbor list.

        Args:
            radiomac (str): Radio Mac to look up list of Neighbors
            tenant_id (str, optional): ID to look up Radio list

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch/ap_nbr_graph/v1/Radio/NeighborList/{radiomac}"

        params = {
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_ap_upgrade_sampling_get_req(
        self,
        aplist: List[str],
        tenant_id: str = None,
    ) -> Response:
        """Get AP neighbor list.

        Args:
            aplist (List[str]): List of Aps to be partitioned
            tenant_id (str, optional): ID to look up AP list

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/ap_nbr_graph/v1/Ap/LiveUpgrade/Sampling"

        params = {
            'aplist': aplist,
            'tenant_id': tenant_id
        }

        return await self.get(url, params=params)

    async def airmatch_process_partition_get_req(
        self,
        tenant_id: str = None,
        band: str = None,
        ptype: str = None,
    ) -> Response:
        """Get partition information.

        Args:
            tenant_id (str, optional): customer ID
            band (str, optional): Radio Frequency Band Filter  Valid Values: 2.4ghz, 5ghz
            ptype (str, optional): partition type  Valid Values: normal, eirp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/ap_nbr_graph/v1/partition"

        params = {
            'tenant_id': tenant_id,
            'band': band,
            'ptype': ptype
        }

        return await self.get(url, params=params)

    async def airmatch_process_partition_post_req(
        self,
        tenant_id: str = None,
    ) -> Response:
        """Start partition process.

        Args:
            tenant_id (str, optional): customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/ap_nbr_graph/v1/partition"

        params = {
            'tenant_id': tenant_id
        }

        return await self.post(url, params=params)

    async def apprf_top_n_stats_iap_get(
        self,
        count: int = None,
        group: str = None,
        site: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ssids: List[str] = None,
        user_role: List[str] = None,
        details: bool = None,
    ) -> Response:
        """Gets Top N Apprf Statistics.

        Args:
            count (int, optional): Required top N count. Default is 5 and maximum is 500
            group (str, optional): Filter by group name
            site (str, optional): Filter by site name
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            ssids (List[str], optional): ssids to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            user_role (List[str], optional): user to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            details (bool, optional): Flag deciding if apprf data details shall be shown

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/topstats"

        params = {
            'count': count,
            'group': group,
            'site': site,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ssids': ssids,
            'user_role': user_role,
            'details': details
        }

        return await self.get(url, params=params)

    async def apprf_get_top_n_stats_v2(
        self,
        count: int = None,
        group: str = None,
        group_id: str = None,
        cluster_id: str = None,
        label_id: str = None,
        site: str = None,
        metrics: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        metric_id: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
    ) -> Response:
        """Gets Top N Apprf Statistics (V2 Version).

        Args:
            count (int, optional): Required top N count. Default is 5 and maximum is 500
            group (str, optional): Filter by group name
            group_id (str, optional): Filter by group id
            cluster_id (str, optional): Filter by gateway serial number
            label_id (str, optional): Filter by label id
            site (str, optional): Filter by site name
            metrics (str, optional): Group by one or multiple params[app_id, web_id, web_rep,
                app_cat, uplink_id, policy_id]
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            metric_id (str, optional): If metrics filter is uplink_id or policy_id, this will
                provide value for id.
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/datapoints/v2/topn_stats"

        params = {
            'count': count,
            'group': group,
            'group_id': group_id,
            'cluster_id': cluster_id,
            'label_id': label_id,
            'site': site,
            'metrics': metrics,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'metric_id': metric_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.get(url, params=params)

    async def apprf_applications_get(
        self,
        count: int = None,
        group: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ssids: List[str] = None,
        user_role: List[str] = None,
        details: bool = None,
    ) -> Response:
        """Gets Top N Applications.

        Args:
            count (int, optional): Required top N count. Default is 5 and maximum is 500
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            ssids (List[str], optional): ssids to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            user_role (List[str], optional): user to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            details (bool, optional): Flag deciding if apprf data details shall be shown

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/applications"

        params = {
            'count': count,
            'group': group,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ssids': ssids,
            'user_role': user_role,
            'details': details
        }

        return await self.get(url, params=params)

    async def apprf_webcategories_get(
        self,
        count: int = None,
        group: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ssids: List[str] = None,
        user_role: List[str] = None,
        details: bool = None,
    ) -> Response:
        """Gets Top N Web categories.

        Args:
            count (int, optional): Required top N count. Default is 5 and maximum is 500
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            ssids (List[str], optional): ssids to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            user_role (List[str], optional): user to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            details (bool, optional): Flag deciding if apprf data details shall be shown

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/webcategories"

        params = {
            'count': count,
            'group': group,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ssids': ssids,
            'user_role': user_role,
            'details': details
        }

        return await self.get(url, params=params)

    async def apprf_appcategories_get(
        self,
        count: int = None,
        group: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ssids: List[str] = None,
        user_role: List[str] = None,
        details: bool = None,
    ) -> Response:
        """Gets Top N App categories.

        Args:
            count (int, optional): Required top N count. Default is 5 and maximum is 500
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            ssids (List[str], optional): ssids to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            user_role (List[str], optional): user to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            details (bool, optional): Flag deciding if apprf data details shall be shown

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/appcategories"

        params = {
            'count': count,
            'group': group,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ssids': ssids,
            'user_role': user_role,
            'details': details
        }

        return await self.get(url, params=params)

    async def apprf_webreputations_get(
        self,
        group: str = None,
        swarm_id: str = None,
        serial: str = None,
        macaddr: str = None,
        from_timestamp: int = None,
        to_timestamp: int = None,
        ssids: List[str] = None,
        user_role: List[str] = None,
        details: bool = None,
    ) -> Response:
        """Gets Top Web Reputations.

        Args:
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID
            serial (str, optional): Filter by AP serial number
            macaddr (str, optional): Filter by Client MAC address e.g. 01:23:45:67:89:ab
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp
            ssids (List[str], optional): ssids to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            user_role (List[str], optional): user to be filtered, comma seperated values (can be
                applied at customer/group/swarm levels)
            details (bool, optional): Flag deciding if apprf data details shall be shown

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/webreputations"

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'ssids': ssids,
            'user_role': user_role,
            'details': details
        }

        return await self.get(url, params=params)

    async def apprf_webreputation_mapping_get(
        self,
    ) -> Response:
        """Gets Web Reputation id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/webreputation/id_to_name"

        return await self.get(url)

    async def apprf_application_mapping_get(
        self,
    ) -> Response:
        """Gets Application id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/application/id_to_name"

        return await self.get(url)

    async def apprf_appcategory_mapping_get(
        self,
    ) -> Response:
        """Gets Application Category id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/appcategory/id_to_name"

        return await self.get(url)

    async def apprf_webcategory_mapping_get(
        self,
    ) -> Response:
        """Gets Web Category id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/webcategory/id_to_name"

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

    async def bbs_retrieve_desire_beacon(
        self,
        profile_id: str,
        ap_mac: str = None,
        iot_radio_mac: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve ble configured beacons.

        Args:
            profile_id (str): Id of profile for which to retrieve device beacon
            ap_mac (str, optional): ap mac address for which to retrieve device beacon
            iot_radio_mac (str, optional): ble radio mac address for which to retrieve device beacon
            offset (int, optional): Offset of first item in response. Defaults to 0.
            limit (int, optional): Maximum number of items in response. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/bbs/v1/ble_cfg_beacons/{profile_id}"

        params = {
            'ap_mac': ap_mac,
            'iot_radio_mac': iot_radio_mac,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def bbs_retrieve_actual_beacon(
        self,
        profile_id: str,
        ap_mac: str = None,
        iot_radio_mac: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve ble running beacons.

        Args:
            profile_id (str): Id of profile for which to retrieve device beacon
            ap_mac (str, optional): ap mac address for which to retrieve device beacon
            iot_radio_mac (str, optional): ble radio mac address for which to retrieve device beacon
            offset (int, optional): Offset of first item in response. Defaults to 0.
            limit (int, optional): Maximum number of items in response. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/bbs/v1/ble_run_beacons/{profile_id}"

        params = {
            'ap_mac': ap_mac,
            'iot_radio_mac': iot_radio_mac,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def bbs_retrieve_beacon_profile(
        self,
        profile_id: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve ble beacon profiles.

        Args:
            profile_id (str, optional): Id of profile for which to retrieve device beacon
            offset (int, optional): Offset of first item in response. Defaults to 0.
            limit (int, optional): Maximum number of items in response. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/bbs/v1/ble_beacon_profiles"

        params = {
            'profile_id': profile_id,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def bbs_update_device_beacon(
        self,
        iot_radio_mac: str,
        profile_id: str,
        adv_format: str,
        major: str,
        minor: str,
        uuid: str,
        payload: str,
        interval: str,
    ) -> Response:
        """Update one device beacon config.

        Args:
            iot_radio_mac (str): ap mac address used to identify which device change beacon
            profile_id (str): Id of profile for which to retrieve device beacon
            adv_format (str): this field is advertisement beacon type  Valid Values: ibeacon, custom
            major (str): major value for ibeacon, range is 0-65535
            minor (str): minor value for ibeacon, range is 0-65535
            uuid (str): uuid value for ibeacon included 36 charachters,
                eg:4152554E-F99B-4A3B-86D0-947070693A78
            payload (str): payload value for custom beacon, length is 3-31 bytes and each bytes
                include 2 ASCII characters
            interval (str): interval value for beacon advertised , length is 100-30000 ms and
                increment in multiples of 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/bbs/v1/ble_beacon/{iot_radio_mac}/{profile_id}"

        json_data = {
            'adv_format': adv_format,
            'major': major,
            'minor': minor,
            'uuid': uuid,
            'payload': payload,
            'interval': interval
        }

        return await self.post(url, json_data=json_data)

    async def bbs_delete_device_beacon(
        self,
        iot_radio_mac: str,
        profile_id: str,
    ) -> Response:
        """Delete one device beacon config.

        Args:
            iot_radio_mac (str): The field used to identify which device change beacon
            profile_id (str): the ble beacon profile name that ap used

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/bbs/v1/ble_beacon/{iot_radio_mac}/{profile_id}"

        return await self.delete(url)

    async def get_cm_cm_enabled_v1(
        self,
        tenant_id: str,
    ) -> Response:
        """Get the status of Client Match for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/cm-enabled/v1/{tenant_id}"

        return await self.get(url)

    async def post_cm_cm_enabled_v1(
        self,
        tenant_id: str,
        enable: bool,
    ) -> Response:
        """Enable or disable Client Match for a particular tenant.

        Args:
            tenant_id (str): Tenant ID
            enable (bool): State of Client Match.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/cm-enabled/v1/{tenant_id}"

        json_data = {
            'enable': enable
        }

        return await self.post(url, json_data=json_data)

    async def get_cm_loadbal_enable_v1(
        self,
        tenant_id: str,
    ) -> Response:
        """Get the status of Client Match Load Balancer for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/loadbal-enable/v1/{tenant_id}"

        return await self.get(url)

    async def post_cm_loadbal_enable_v1(
        self,
        tenant_id: str,
        enable: bool,
    ) -> Response:
        """Enable or disable Client Match Load Balancer for a particular tenant.

        Args:
            tenant_id (str): Tenant ID
            enable (bool): State of Client Match Load Balancer.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/loadbal-enable/v1/{tenant_id}"

        json_data = {
            'enable': enable
        }

        return await self.post(url, json_data=json_data)

    async def get_cm_bandsteer_6ghz_enable_v1(
        self,
        tenant_id: str,
    ) -> Response:
        """Get the status of Client Match Band Steer to 6GHz for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/bandsteer-6ghz-enable/v1/{tenant_id}"

        return await self.get(url)

    async def post_cm_bandsteer_6ghz_enable_v1(
        self,
        tenant_id: str,
        enable: bool,
    ) -> Response:
        """Enable or disable Client Match Band Steer to 6GHz for a particular tenant.

        Args:
            tenant_id (str): Tenant ID
            enable (bool): State of Client Match Band Steer to 6GHz.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/bandsteer-6ghz-enable/v1/{tenant_id}"

        json_data = {
            'enable': enable
        }

        return await self.post(url, json_data=json_data)

    async def get_cm_unsteerable_v1(
        self,
        tenant_id: str,
    ) -> Response:
        """Get all unsteerable entries for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}"

        return await self.get(url)

    async def get_cm_unsteerable_v1(
        self,
        tenant_id: str,
        client_mac: str,
    ) -> Response:
        """Get the unsteerable state of a client.

        Args:
            tenant_id (str): Tenant ID
            client_mac (str): MAC address of client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}/{client_mac}"

        return await self.get(url)

    async def post_cm_unsteerable_v1(
        self,
        tenant_id: str,
        client_mac: str,
        type: str = None,
        duration: int = None,
    ) -> Response:
        """Set the unsteerable state of a client.

        Args:
            tenant_id (str): Tenant ID
            client_mac (str): MAC address of client
            type (str, optional): Type of the steer.
            duration (int, optional): Duration (in minutes) for which client is unsteerable.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}/{client_mac}"

        json_data = {
            'type': type,
            'duration': duration
        }

        return await self.post(url, json_data=json_data)

    async def delete_cm_unsteerable_v1(
        self,
        tenant_id: str,
        client_mac: str,
    ) -> Response:
        """Delete the unsteerable state of a client.

        Args:
            tenant_id (str): Tenant ID
            client_mac (str): MAC address of client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}/{client_mac}"

        return await self.delete(url)

    async def cloudauth_read_auth_air_pass_list(
        self,
        cursor: str = None,
        from_time: str = None,
        time_window: str = None,
        limit: int = 100,
    ) -> Response:
        """Fetch list of authentications using Aruba Air Pass.

        Args:
            cursor (str, optional): Cursor to iterate over the next set of authentication records.
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.
            time_window (str, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: 3-hour, 1-day, 1-week, 1-month, 3-month
            limit (int, optional): Maximum number of authentication records to be returned. Allowed
                range is 1 to 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/auth/air_pass/list"

        params = {
            'cursor': cursor,
            'from_time': from_time,
            'time_window': time_window,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def cloudauth_read_auth_cloud_identity_list(
        self,
        cursor: str = None,
        from_time: str = None,
        time_window: str = None,
        limit: int = 100,
    ) -> Response:
        """Fetch list of authentications using Cloud Identity.

        Args:
            cursor (str, optional): Cursor to iterate over the next set of authentication records.
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.
            time_window (str, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: 3-hour, 1-day, 1-week, 1-month, 3-month
            limit (int, optional): Maximum number of authentication records to be returned. Allowed
                range is 1 to 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/auth/cloud_identity/list"

        params = {
            'cursor': cursor,
            'from_time': from_time,
            'time_window': time_window,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def cloudauth_read_auth_details_record(
        self,
        request_id: str,
    ) -> Response:
        """Fetch details of a specific authentication using either Cloud Identity or Aruba Air Pass.

        Args:
            request_id (str): The authentication request ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/auth/{request_id}"

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
        default_role: str,
        dpp_wlan_network: str,
        rules: list,
    ) -> Response:
        """Configure or update network access policy for registered clients.

        Args:
            default_role (str): Client Role for clients with tags that are not specified in the
                Rules. Must be a valid role, cannot be empty.
            dpp_wlan_network (str): WLAN network for clients that use dpp provisoning.
            rules (list): Mapping rules of Client Profile Tags to Client Roles.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/client_policy"

        json_data = {
            'default_role': default_role,
            'dpp_wlan_network': dpp_wlan_network,
            'rules': rules
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

    async def cloudauth_dppclientregistrationread(
        self,
        cursor: str = None,
        id: str = None,
        limit: int = 100,
    ) -> Response:
        """Fetch list of registered clients.

        Args:
            cursor (str, optional): Number of dpp clients to be skipped before returning the data,
                useful for pagination.
            id (str, optional): Search for entries with specific dpp client id
            limit (int, optional): Maximum number of registered dpp clients to be returned. Allowed
                range is 1 to 20. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/dpp_registration"

        params = {
            'cursor': cursor,
            'id': id,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def cloudauth_dppclientregistrationadd(
        self,
        id: str,
        uri: str,
    ) -> Response:
        """Register a client.

        Args:
            id (str): DPP client Id.
            uri (str): DPP URI

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/dpp_registration"

        json_data = {
            'id': id,
            'uri': uri
        }

        return await self.post(url, json_data=json_data)

    async def cloudauth_dppclientregistrationupdate(
        self,
        id: str,
        new_id: str,
        uri: str,
    ) -> Response:
        """Update registered client with bootstrapping key.

        Args:
            id (str): The unique identifier of the client.
            new_id (str): DPP client Id.
            uri (str): DPP URI

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/dpp_registration/{id}"

        json_data = {
            'new_id': new_id,
            'uri': uri
        }

        return await self.put(url, json_data=json_data)

    async def cloudauth_dppclientregistrationdelete(
        self,
        id: str,
    ) -> Response:
        """Delete registered client.

        Args:
            id (str): The unique identifier of the client.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cloudAuth/api/v1/dpp_registration/{id}"

        return await self.delete(url)

    async def cloudauth_read_session_air_pass_list(
        self,
        cursor: str = None,
        from_time: str = None,
        time_window: str = None,
        limit: int = 100,
    ) -> Response:
        """Fetch list of sessions using Aruba Air Pass.

        Args:
            cursor (str, optional): Cursor to iterate over the next set of session records.
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.
            time_window (str, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: 3-hour, 1-day, 1-week, 1-month, 3-month
            limit (int, optional): Maximum number of session records to be returned. Allowed range
                is 1 to 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/session/air_pass/list"

        params = {
            'cursor': cursor,
            'from_time': from_time,
            'time_window': time_window,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def cloudauth_read_cloud_identity_session_list(
        self,
        cursor: str = None,
        from_time: str = None,
        time_window: str = None,
        limit: int = 100,
    ) -> Response:
        """Fetch list of sessions using Cloud Identity.

        Args:
            cursor (str, optional): Cursor to iterate over the next set of session records.
            from_time (str, optional): Integer value (1-90) followed by unit - one of d , h , m for
                day , hour , minute respectively; like 3h. This is ignored if Time Window is
                specified.
            time_window (str, optional): Set Time Window to include requests started in a specific
                time window.  Valid Values: 3-hour, 1-day, 1-week, 1-month, 3-month
            limit (int, optional): Maximum number of session records to be returned. Allowed range
                is 1 to 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/session/cloud_identity/list"

        params = {
            'cursor': cursor,
            'from_time': from_time,
            'time_window': time_window,
            'limit': limit
        }

        return await self.get(url, params=params)

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
        default_role: str,
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
        mpsk: list,
        organization_name: str,
        rules: list,
        wlan_network: str,
    ) -> Response:
        """Configure policy to allow wireless network access for users.

        Args:
            default_role (str): Client roles for any user groups that are not specified in the
                Rules. If left empty all unspecified user group will be denied access.
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
            mpsk (list): SSID names for the MPSK ssids that need to be configured.
            organization_name (str): Organization name
            rules (list): Mapping rules of User Groups to Client Roles.
            wlan_network (str): WLAN network for clients that do not support Passpoint profiles.
                Empty or missing WLAN network would mean wired-only provisioning.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/cloudAuth/api/v1/user_policy"

        json_data = {
            'default_role': default_role,
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
            'mpsk': mpsk,
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
        NewCentral: bool = None,
        Wired: bool = True,
        Wireless: bool = None,
    ) -> Response:
        """Update properties for the given group.

        Args:
            group (str): Group for which properties need to be updated.
            AllowedDevTypes (List[str], optional): - Devices types which are allowed to be parked in
                the group.                                                    - The allowed device
                types are 'AccessPoints', 'Gateways' and 'Switches'
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
            AllowedSwitchTypes (List[str], optional): - Switch types which are allowed to be parked
                in the group.                                                       - This is
                applicable only when switches are allowed to be parked in the group.
                - The allowed switch types are 'AOS_S' and 'AOS_CX'
            MonitorOnly (List[str], optional): - Device types for which monitor only mode is to be
                enabled                                                - Currently, this is
                available only for AOS_S and AOS_CX switches in groups where switches are
                managed using UI mode of configuration.
            NewCentral (bool, optional): - Flag to specify that the group is compatible with New
                Central workflows.
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
            'NewCentral': NewCentral,
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

    async def configuration_pre_provision_group(
        self,
        device_id: List[str],
        group_name: str,
        tenant_id: str = None,
    ) -> Response:
        """Pre Provision a group to the device.

        Args:
            device_id (List[str]): device_id
            group_name (str): Group name
            tenant_id (str): Tenant id

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/preassign"

        json_data = {
            'device_id': device_id,
            'group_name': group_name,
        }

        if tenant_id is not None:
            json_data["tenant_id"] = str(tenant_id)

        return await self.post(url, json_data=json_data)

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
        preserve_config_overrides: List[str],
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): group
            serials (List[str]): serials
            preserve_config_overrides (List[str]): The configuration of devices of type mentioned in
                this list will be preserved when the device is moved to a UI group.
                The device configuration will not be reset completely with the group level
                configuration.
                This is supported only for AOS_CX devices.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/devices/move"

        json_data = {
            'group': group,
            'serials': serials,
            'preserve_config_overrides': preserve_config_overrides
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
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN list of an UI group.

        Args:
            group_name_or_guid_or_serial_number (str): Name of the group or guid of the swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_get_wlan_template(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN default configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Name of the group or guid of the swarm or
                serial number of 10x AP. Example:Group_1 or
                6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid_or_serial_number}/template"

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
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN access rule services.

        Args:
            group_name_or_guid_or_serial_number (str): Name of the group or guid of the swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid_or_serial_number}/access_rule_services"

        return await self.get(url)

    async def configuration_delete_wlan(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
    ) -> Response:
        """Delete an existing WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        return await self.delete(url)

    async def configuration_get_wlan_v2(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
    ) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        return await self.get(url)

    async def configuration_create_wlan_v2(
        self,
        group_name_or_guid_or_serial_number: str,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/v2/wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

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
        group_name_or_guid_or_serial_number: str,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/v2/wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

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
        group_name_or_guid_or_serial_number: str,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/v2/wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

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

    async def configuration_get_wlan_list(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN list of an UI group.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_get_wlan_template(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN default configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/template"

        return await self.get(url)

    async def configuration_get_protocol_map(
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

    async def configuration_get_access_rule_services(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get WLAN access rule services.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/access_rule_services"

        return await self.get(url)

    async def configuration_get_wlan(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
    ) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        return await self.get(url)

    async def configuration_create_wlan(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
        value: str,
    ) -> Response:
        """Create a new WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        json_data = {
            'value': value
        }

        return await self.post(url, json_data=json_data)

    async def configuration_update_wlan(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
        value: str,
    ) -> Response:
        """Update an existing WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN selected.                              Example:wlan_1.
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
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        json_data = {
            'value': value
        }

        return await self.put(url, json_data=json_data)

    async def configuration_delete_wlan(
        self,
        group_name_or_guid_or_serial_number: str,
        wlan_name: str,
    ) -> Response:
        """Delete an existing WLAN.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{group_name_or_guid_or_serial_number}/{wlan_name}"

        return await self.delete(url)

    async def configuration_get_hotspot_list(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get hotspot list of an UI group or swarm or device.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_get_hotspot_list_by_mode_name(
        self,
        group_name_or_guid_or_serial_number: str,
        mode_name: str,
    ) -> Response:
        """Get hotspot list of an UI group or swarm or device with mode name.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/{mode_name}"

        return await self.get(url)

    async def configuration_get_hotspot_templates(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get hotspot default configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/template"

        return await self.get(url)

    async def configuration_get_hotspot(
        self,
        group_name_or_guid_or_serial_number: str,
        hotspot_name: str,
        mode_name: str,
    ) -> Response:
        """Get the information of an existing hotspot.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            hotspot_name (str): Name of Hotspot selected.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/{hotspot_name}/{mode_name}"

        return await self.get(url)

    async def configuration_create_hotspot(
        self,
        group_name_or_guid_or_serial_number: str,
        hotspot_name: str,
        mode_name: str,
        value: str,
    ) -> Response:
        """Create a new hotspot.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/{hotspot_name}/{mode_name}"

        json_data = {
            'value': value
        }

        return await self.post(url, json_data=json_data)

    async def configuration_update_hotspot(
        self,
        group_name_or_guid_or_serial_number: str,
        hotspot_name: str,
        mode_name: str,
        value: str,
    ) -> Response:
        """Update an existing hotspot.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            hotspot_name (str): Name of Hotspot selected.
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
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/{hotspot_name}/{mode_name}"

        json_data = {
            'value': value
        }

        return await self.put(url, json_data=json_data)

    async def configuration_delete_hotspot(
        self,
        group_name_or_guid_or_serial_number: str,
        hotspot_name: str,
        mode_name: str,
    ) -> Response:
        """Delete an existing hotspot.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            hotspot_name (str): Name of Hotspot to be deleted.
                Example:hotspot_1.
            mode_name (str): Hotspot mode name.                              Example:HS2.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_hotspot/{group_name_or_guid_or_serial_number}/{hotspot_name}/{mode_name}"

        return await self.delete(url)

    async def configuration_get_clis(
        self,
        group_name_or_guid_or_serial_number: str,
        version: str = None,
    ) -> Response:
        """Get AP configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            version (str, optional): Version of AP.                                      Defalut is
                AP max version.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_name_or_guid_or_serial_number}"

        params = {
            'version': version
        }

        return await self.get(url, params=params)

    async def configuration_update_clis(
        self,
        group_name_or_guid_or_serial_number: str,
        clis: List[str],
    ) -> Response:
        """Replace AP configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            clis (List[str]): Whole configuration List in CLI format

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{group_name_or_guid_or_serial_number}"

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
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get variables config.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/iap_variables/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_update_swarm_variables(
        self,
        group_name_or_guid_or_serial_number: str,
        variables: list,
    ) -> Response:
        """Replace AP variables.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            variables (list): Variable List

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/iap_variables/{group_name_or_guid_or_serial_number}"

        json_data = {
            'variables': variables
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_dirty_diff(
        self,
        group_name_or_guid_or_serial_number: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get dirty diff.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of swarm or
                serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group config_mode records to be returned.
                Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dirty_diff/{group_name_or_guid_or_serial_number}"

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
                interfaces.<br>Pattern for VLAN: "(^([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-
                9]|409[0-4])(-([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4]))?$)|(^all$)"
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
                LAGs.<br>Pattern: "(^([1-9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4])(-([1-
                9][0-9]{0,2}|[1-3][0-9]{3}|40[0-8][0-9]|409[0-4]))?$)|(^all$)"
            dhcpv4_snooping (str, optional): dhcpv4_snooping

        Returns:
            Response: CentralAPI Response object
        """
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
        name: str = None,
        contact: str = None,
        location: str = None,
        timezone: str = None,
        vrf: str = None,
        dns_servers: List[str] = [],
        ntp_servers: List[str] = [],
        admin_username: str = None,
        admin_password: str = None,
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
            admin_password (str): admin_username should be provided with this field.<br>Pattern:
                "^[^"? ]*$"
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

    async def configuration_crud_syslog(
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

    async def configuration_get_authentication(
        self,
        device_serial: str = None,
        group_name: str = None,
    ) -> Response:
        """Get Port Access Authentication.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/port-access-auth"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        return await self.get(url, params=params)

    async def configuration_update_authentication(
        self,
        device_serial: str = None,
        group_name: str = None,
        enable: bool = False,
        cached_reauth_period_enable: bool = False,
        cached_reauth_period: int = 30,
        reauth_period_enable: bool = False,
        reauth_period: int = 3600,
        quiet_period: int = 60,
        primary_auth: bool = False,
        auth_priority: bool = False,
    ) -> Response:
        """Update Port Access Authentication.

        Args:
            device_serial (str, optional): Device serial number.
                Mandatory for device level configuration.
            group_name (str, optional): Group name.
                Mandatory for group level configuration.
            enable (bool, optional): enable
            cached_reauth_period_enable (bool, optional): cached_reauth_period_enable
            cached_reauth_period (int, optional): cached_reauth_period
            reauth_period_enable (bool, optional): reauth_period_enable
            reauth_period (int, optional): reauth_period
            quiet_period (int, optional): quiet_period
            primary_auth (bool, optional): primary_auth
            auth_priority (bool, optional): auth_priority

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/port-access-auth"

        params = {
            'device_serial': device_serial,
            'group_name': group_name
        }

        json_data = {
            'enable': enable,
            'cached_reauth_period_enable': cached_reauth_period_enable,
            'cached_reauth_period': cached_reauth_period,
            'reauth_period_enable': reauth_period_enable,
            'reauth_period': reauth_period,
            'quiet_period': quiet_period,
            'primary_auth': primary_auth,
            'auth_priority': auth_priority
        }

        return await self.post(url, params=params, json_data=json_data)

    async def configuration_get_system_config(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get System Config.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_update_system_config(
        self,
        group_name_or_guid_or_serial_number: str,
        dns_server: str,
        ntp_server: List[str],
        username: str,
        password: str,
    ) -> Response:
        """Update system config.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            dns_server (str): DNS server IPs or domain name
            ntp_server (List[str]): List of ntp server,
                Example: ["192.168.1.1", "127.0.0.0", "xxx.com"].
                IPs or domain name.
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{group_name_or_guid_or_serial_number}"

        json_data = {
            'dns_server': dns_server,
            'ntp_server': ntp_server,
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_arm_config(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get ARM configuration.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/arm/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_update_arm_config(
        self,
        group_name_or_guid_or_serial_number: str,
        _80mhz_support: bool,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            _80mhz_support (bool): 80mhz_support
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
        url = f"/configuration/v1/arm/{group_name_or_guid_or_serial_number}"

        json_data = {
            '_80mhz_support': _80mhz_support,
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
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get all Dot11g Radio Profiles.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profiles/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_get_dot11g_radio_config_by_name(
        self,
        group_name_or_guid_or_serial_number: str,
        name: str,
    ) -> Response:
        """Get Dot11g radio profile.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            name (str): Name of the dot11g radio profile that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

        return await self.get(url)

    async def configuration_update_dot11g_radio_profile(
        self,
        group_name_or_guid_or_serial_number: str,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

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
        group_name_or_guid_or_serial_number: str,
        name: str,
    ) -> Response:
        """Delete Dot11g radio profile.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            name (str): Name of the dot11g radio profile that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11g_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

        return await self.delete(url)

    async def configuration_get_all_dot11a_radio_profile(
        self,
        group_name_or_guid_or_serial_number: str,
    ) -> Response:
        """Get all Dot11a Radio Profiles.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profiles/{group_name_or_guid_or_serial_number}"

        return await self.get(url)

    async def configuration_get_dot11a_radio_config_by_name(
        self,
        group_name_or_guid_or_serial_number: str,
        name: str,
    ) -> Response:
        """Get Dot11a radio profile.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            name (str): Dot11a radio profile name.                         Example: default.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

        return await self.get(url)

    async def configuration_update_dot11a_radio_profile(
        self,
        group_name_or_guid_or_serial_number: str,
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
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
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
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

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
        group_name_or_guid_or_serial_number: str,
        name: str,
    ) -> Response:
        """Delete an existing Dot11a radio profile.

        Args:
            group_name_or_guid_or_serial_number (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.
            name (str): Dot11a radio profile name.                         Example: default.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dot11a_radio_profile/{group_name_or_guid_or_serial_number}/{name}"

        return await self.delete(url)

    async def configuration_get_group_ports(
        self,
        group_name: str,
    ) -> Response:
        """Get ports name for a group.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/ports/groups/{group_name}"

        return await self.get(url)

    async def configuration_set_group_ports(
        self,
        group_name: str,
        ports: list,
    ) -> Response:
        """Update ports name for a group.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.
            ports (list): ports

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/ports/groups/{group_name}"

        json_data = {
            'ports': ports
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_device_ports(
        self,
        device_serial: str,
    ) -> Response:
        """Get ports name for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/ports/devices/{device_serial}"

        return await self.get(url)

    async def configuration_set_device_ports(
        self,
        device_serial: str,
        ports: list,
    ) -> Response:
        """Update ports name for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.
            ports (list): ports

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/ports/devices/{device_serial}"

        json_data = {
            'ports': ports
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_group_vlans(
        self,
        group_name: str,
    ) -> Response:
        """Get vlans with tagged, untagged and isolated ports for a group.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/vlans/groups/{group_name}"

        return await self.get(url)

    async def configuration_set_group_vlans(
        self,
        group_name: str,
        vlans: list,
    ) -> Response:
        """Update vlans with tagged, untagged and isolated ports for a group.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.
            vlans (list): vlans

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/vlans/groups/{group_name}"

        json_data = {
            'vlans': vlans
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_device_vlans(
        self,
        device_serial: str,
    ) -> Response:
        """Get vlans with tagged, untagged and isolated ports for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/vlans/devices/{device_serial}"

        return await self.get(url)

    async def configuration_set_device_vlans(
        self,
        device_serial: str,
        vlans: list,
    ) -> Response:
        """Update vlans with tagged, untagged and isolated ports for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.
            vlans (list): vlans

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/vlans/devices/{device_serial}"

        json_data = {
            'vlans': vlans
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_group_admin(
        self,
        group_name: str,
    ) -> Response:
        """Get admin SSH details of a group.

        Args:
            group_name (str): Name of the group.                               Example:Group_1

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system/groups/{group_name}"

        return await self.get(url)

    async def configuration_set_group_admin(
        self,
        group_name: str,
        username: str,
        password: str,
    ) -> Response:
        """Update admin SSH details of a group.

        Args:
            group_name (str): Name of the group.                               Example:Group_1
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system/groups/{group_name}"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_device_admin(
        self,
        device_serial: str,
    ) -> Response:
        """Get admin SSH details of a device.

        Args:
            device_serial (str): Serial of a Device.
                Example:AB0011111

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system/devices/{device_serial}"

        return await self.get(url)

    async def configuration_set_device_admin(
        self,
        device_serial: str,
        username: str,
        password: str,
    ) -> Response:
        """Update admin SSH details of a device.

        Args:
            device_serial (str): Serial of a Device.
                Example:AB0011111
            username (str): username
            password (str): password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system/devices/{device_serial}"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_group_system_time(
        self,
        group_name: str,
    ) -> Response:
        """Get system time details for a group.

        Args:
            group_name (str): Name of the group.                               Example:Group_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system_time/groups/{group_name}"

        return await self.get(url)

    async def configuration_set_group_system_time(
        self,
        group_name: str,
        time_zone: str,
        day_of_month: int,
        month: int,
    ) -> Response:
        """Update system time details for a group.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.
            time_zone (str): time_zone
            day_of_month (int): day_of_month
            month (int): month

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system_time/groups/{group_name}"

        json_data = {
            'time_zone': time_zone,
            'day_of_month': day_of_month,
            'month': month
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_device_system_time(
        self,
        device_serial: str,
    ) -> Response:
        """Get system time details for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system_time/devices/{device_serial}"

        return await self.get(url)

    async def configuration_set_device_system_time(
        self,
        device_serial: str,
        time_zone: str,
        day_of_month: int,
        month: int,
    ) -> Response:
        """Update system time details for a device.

        Args:
            device_serial (str): Device serial of the device.
                Example:AB0011111.
            time_zone (str): time_zone
            day_of_month (int): day_of_month
            month (int): month

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/aos_switch/system_time/devices/{device_serial}"

        json_data = {
            'time_zone': time_zone,
            'day_of_month': day_of_month,
            'month': month
        }

        return await self.put(url, json_data=json_data)

    async def configuration_get_group_ssh_credential(
        self,
        group_name: str,
    ) -> Response:
        """Get ssh credential in group level.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/group/ssh_credential/{group_name}"

        return await self.get(url)

    async def configuration_update_group_ssh_credential(
        self,
        group_name: str,
        username: str,
        password: str,
    ) -> Response:
        """Update ssh credential in group level.

        Args:
            group_name (str): Group name of the group.
                Example:Group_1.
            username (str): user name
            password (str): plaintext password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/group/ssh_credential/{group_name}"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

    async def configuration_get_device_ssh_credential(
        self,
        serial_number_or_guid: str,
    ) -> Response:
        """Get ssh credential in device level.

        Args:
            serial_number_or_guid (str): Serial number of AP or guid of the swarm.
                Example:CNBRHMV3HG or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/device/ssh_credential/{serial_number_or_guid}"

        return await self.get(url)

    async def configuration_update_device_ssh_credential(
        self,
        serial_number_or_guid: str,
        username: str,
        password: str,
    ) -> Response:
        """Update ssh credential in device level.

        Args:
            serial_number_or_guid (str): Serial number of AP or guid of the swarm.
                Example:CNBRHMV3HG or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f
            username (str): user name
            password (str): plaintext password

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/device/ssh_credential/{serial_number_or_guid}"

        json_data = {
            'username': username,
            'password': password
        }

        return await self.post(url, json_data=json_data)

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

        params = {
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.get(url, params=params)

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

        params = {
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
        }

        return await self.get(url, params=params)

    async def firmware_get_swarms_details(
        self,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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

    async def firmware_get_swarm_details(
        self,
        swarm_id: str,
    ) -> Response:
        """Firmware Details of Swarm.

        Args:
            swarm_id (str): Swarm ID for which the firmware detail to be queried

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/firmware/v1/swarms/{swarm_id}"

        return await self.get(url)

    async def firmware_get_devices_details(
        self,
        device_type: str,
        group: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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
            'device_type': device_type,
            'group': group,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def firmware_get_device_details(
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

        return await self.get(url)

    async def firmware_get_version_list(
        self,
        device_type: str = None,
        swarm_id: str = None,
        serial: str = None,
    ) -> Response:
        """List Firmware Version.

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

    async def firmware_is_image_available(
        self,
        device_type: str,
        firmware_version: str,
    ) -> Response:
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

    async def firmware_get_status(
        self,
        swarm_id: str = None,
        serial: str = None,
    ) -> Response:
        """Firmware Status.

        Args:
            swarm_id (str, optional): Swarm ID
            serial (str, optional): Serial of device

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/status"

        params = {
            'swarm_id': swarm_id,
            'serial': serial
        }

        return await self.get(url, params=params)

    async def firmware_upgrade_firmware(
        self,
        firmware_scheduled_at: int,
        swarm_id: str,
        serial: str,
        group: str,
        device_type: str,
        firmware_version: str,
        reboot: bool,
        model: str,
    ) -> Response:
        """Firmware Upgrade.

        Args:
            firmware_scheduled_at (int): Firmware upgrade will be scheduled at,
                firmware_scheduled_at - current time. firmware_scheduled_at is epoch in seconds and
                default value is current time
            swarm_id (str): Swarm ID
            serial (str): Serial of device
            group (str): Specify Group Name to initiate upgrade  for whole group.
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            firmware_version (str): Specify firmware version to which you want device to upgrade. If
                you do not specify this field then firmware upgrade initiated with recommended
                firmware version
            reboot (bool): Use True for auto reboot after successful firmware download. Default
                value is False. Applicable only on MAS, aruba switches and controller since IAP
                reboots automatically after firmware download.
            model (str): To initiate upgrade at group level for specific model family. Applicable
                only for Aruba switches.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade"

        json_data = {
            'firmware_scheduled_at': firmware_scheduled_at,
            'swarm_id': swarm_id,
            'serial': serial,
            'group': group,
            'device_type': device_type,
            'firmware_version': firmware_version,
            'reboot': reboot,
            'model': model
        }

        return await self.post(url, json_data=json_data)

    async def firmware_cancel_upgrade(
        self,
        swarm_id: str,
        serial: str,
        device_type: str,
        group: str,
    ) -> Response:
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

    async def firmware_set_compliance_customer(
        self,
        device_type: str,
        group: str,
        firmware_compliance_version: str,
        reboot: bool,
        allow_unsupported_version: bool,
        compliance_scheduled_at: int,
    ) -> Response:
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

    async def firmware_set_compliance(
        self,
        device_type: str,
        group: str,
        firmware_compliance_version: str,
        reboot: bool,
        allow_unsupported_version: bool,
    ) -> Response:
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

    async def firmware_get_compliance(
        self,
        device_type: str,
        group: str = None,
    ) -> Response:
        """Get Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.get(url, params=params)

    async def firmware_delete_compliance(
        self,
        device_type: str,
        group: str = None,
    ) -> Response:
        """Clear Firmware Compliance Version.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"
            group (str, optional): Group name

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/upgrade/compliance_version"

        params = {
            'device_type': device_type,
            'group': group
        }

        return await self.delete(url, params=params)

    async def firmware_upgrade_msp(
        self,
        firmware_scheduled_at: int,
        device_type: str,
        firmware_version: str,
        reboot: bool,
        exclude_groups: str,
        exclude_customers: str,
    ) -> Response:
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

    async def firmware_upgrade_customer(
        self,
        customer_id: str,
        firmware_scheduled_at: int,
        device_type: str,
        firmware_version: str,
        reboot: bool,
        exclude_groups: str,
    ) -> Response:
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

    async def firmware_cancel_upgrade_msp_v2(
        self,
        device_type: str,
        exclude_customers: str,
    ) -> Response:
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

    async def firmware_cancel_upgrade_customer_v2(
        self,
        customer_id: str,
        device_type: str,
    ) -> Response:
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

    async def firmware_get_model_families_list(
        self,
        serial: str = None,
        device_type: str = None,
    ) -> Response:
        """List Model Family.

        Args:
            serial (str, optional): Serial of device
            device_type (str, optional): Specify one of "IAP/MAS/HP/CONTROLLER"

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/models"

        params = {
            'serial': serial,
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def firmware_set_compliance_msp(
        self,
        device_type: str,
        firmware_compliance_version: str,
        reboot: bool,
        allow_unsupported_version: bool,
        compliance_scheduled_at: int,
        tenants: str,
    ) -> Response:
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

    async def firmware_get_compliance_msp(
        self,
        device_type: str,
    ) -> Response:
        """Get Firmware Compliance Version for MSP Customer.

        Args:
            device_type (str): Specify one of "IAP/MAS/HP/CONTROLLER"

        Returns:
            Response: CentralAPI Response object
        """
        url = "/firmware/v1/msp/upgrade/compliance_version"

        params = {
            'device_type': device_type
        }

        return await self.get(url, params=params)

    async def firmware_delete_compliance_msp(
        self,
        device_type: str,
        tenants: str,
    ) -> Response:
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

    async def firmware_set_compliance_msp_tenant(
        self,
        customer_id: str,
        device_type: str,
        group: str,
        firmware_compliance_version: str,
        reboot: bool,
        allow_unsupported_version: bool,
        compliance_scheduled_at: int,
    ) -> Response:
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

    async def firmware_get_compliance_msp_tenant(
        self,
        customer_id: str,
        device_type: str,
        group: str = None,
    ) -> Response:
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
            'device_type': device_type,
            'group': group
        }

        return await self.get(url, params=params)

    async def firmware_delete_compliance_msp_tenant(
        self,
        customer_id: str,
        device_type: str,
        group: str = None,
    ) -> Response:
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
            'device_type': device_type,
            'group': group
        }

        return await self.delete(url, params=params)

    async def firmware_get_tenants_details(
        self,
        device_type: str,
        tenant_id: str,
    ) -> Response:
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

    async def guest_get_portals(
        self,
        sort: str = '+name',
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all portals with limited data.

        Args:
            sort (str, optional): + is for ascending  and - for descending order , sorts by name for
                now  Valid Values: +name, -name
            offset (int, optional): Starting index of element for a paginated query Defaults to 0.
            limit (int, optional): Number of items required per query Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/portals"

        params = {
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def guest_create_portal(
        self,
        name: str,
        auth_type: str,
        username_password_enabled: bool,
        registration_enabled: bool,
        verify_registration: bool,
        bypass_cna_policy: bool,
        cna_policy: str,
        register_accept_email: bool,
        register_accept_phone: bool,
        free_wifi_duration: int,
        self_reg_account_unlimited: bool,
        self_reg_account_expire_days: int,
        self_reg_account_expire_hours: int,
        self_reg_account_expire_minutes: int,
        login_button_title: str,
        whitelist_urls: List[str],
        custom_username_label: str,
        custom_password_label: str,
        custom_sender_message: str,
        custom_verification_message: str,
        custom_registration_message: str,
        custom_pwd_reset_message: str,
        auth_sources: list,
        facebook_wifi_configure_url: str,
        facebook_wifi_gateway_id: str,
        redirect_url: str,
        auth_failure_message: str,
        days: int,
        hours: int,
        minutes: int,
        mac_caching_enabled: bool,
        is_shared: bool,
        simultaneous_login_limit: int,
        daily_usage_limit: str,
        by_hours: int,
        by_minutes: int,
        data_type: str,
        data: int,
        background_color: str,
        button_color: str,
        header_fill_color: str,
        page_font_color: str,
        logo_name: str,
        logo: str,
        background_image_name: str,
        background_image: str,
        max_columns: int,
        page_title: str,
        welcome_text: str,
        terms_condition: str,
        display_terms_checkbox: bool,
        display_term_options: str,
        ad_url: str,
        login_image_name: str,
        ad_image: str,
        is_config_associated: bool,
        capture_url: str,
        override_common_name: str,
        override_common_name_enabled: bool,
    ) -> Response:
        """Create a new guest portal profile.

        Args:
            name (str): Name of the portal (max length 22 characters)
            auth_type (str): Authentication type of portal  Valid Values: unauthenticated,
                authenticated, facebookwifi
            username_password_enabled (bool): Username/Password authentication type
            registration_enabled (bool): Identify if guest user can register on the portal
            verify_registration (bool): Identify if verification is required for guest registration
            bypass_cna_policy (bool): Identify if CNA policy is to be bypassed
            cna_policy (str): cna_policy  Valid Values: allow_always, automatic
            register_accept_email (bool): Identify if guest registration is performed via e-mail
            register_accept_phone (bool): Identify if guest registration is performed via phone
            free_wifi_duration (int): Free wifi allowed durations (0 to 59 minutes)
            self_reg_account_unlimited (bool): Indicates if default registration account expiry is
                unlimited or not
            self_reg_account_expire_days (int): Specify the default registration account expiry in
                days, min 0 to max 180.
            self_reg_account_expire_hours (int): Specify default registration account expiry in
                hours, min 0 to max 23
            self_reg_account_expire_minutes (int): Specify default registration account expiry in
                minutes, min 0 to max 59
            login_button_title (str): Customizable login button label (optional field, max 32
                characters).
            whitelist_urls (List[str]): List of urls to  white list or allow  access before portal
                login
            custom_username_label (str): Custom username lable to be used in registration and
                password reset messages (max 30 characters)
            custom_password_label (str): Custom password label to be used in registration and
                password reset messages (max 10 characters)
            custom_sender_message (str): Custom sender text that will be in the footer of the sms
                message. This will help guest users identify who is sending them sms message. (max
                20 characters)
            custom_verification_message (str): Custom verfication message that guest will receieve
                for when verification is performed (max 90 characters)
            custom_registration_message (str): Custom registration message that guest will receieve
                for when registration is performed (max 90 characters)
            custom_pwd_reset_message (str): Custom passowrd reset message that guest will receieve
                for when password resert is performed (max 90 characters)
            auth_sources (list): List of social auth app values. This could be empty array.
            facebook_wifi_configure_url (str): Use URL to create or customize the facebook wifi page
                which has to have facebook_wifi_gateway_id as a query param. Admin has to configure
                the page inorder to get facebook wifi working
            facebook_wifi_gateway_id (str): Gateway should be used with facebook_wifi_configure_url
                to configure facebook wifi portal. This is auto generated.
            redirect_url (str): Redirect url on succesful login
            auth_failure_message (str): Display message on authentication failure (max 4096
                characters)
            days (int): Session expiry in unit of days. Min 0, Max 180
            hours (int): Session expiry in unit of hours. Min 0, Max 23
            minutes (int): Session expiry in unit of minutes. Min 0, Max 59
            mac_caching_enabled (bool): Flag to indicate whether mac chacing enabled
            is_shared (bool): Flag to indicate whether portal is shared
            simultaneous_login_limit (int): Simultaneous portal logins limit. Value of 0 indicates
                there is no limit  Valid Values: 0 - 5
            daily_usage_limit (str): IO data allowed to be used in a day. Either by time or data
                usage  Valid Values: bytime, bydata, nolimit
            by_hours (int): Time limit in hours to access network (Max 23 hours)
            by_minutes (int): Time limit in minutes to access network (Max 59 minutes)
            data_type (str): Data usage per session or per visitor  Valid Values: session, visitor
            data (int): Data usage limit in MB (Min 1 MB, Max 102400 MB)
            background_color (str): Background color of the portal. (Format  '#XXXXXX', 6 hex
                characters)
            button_color (str): Button color. (Format  '#XXXXXX' , 6 hex characters)
            header_fill_color (str): Header color of the portal. This field can could be null.
                (Format '#XXXXXX' , 6 hex characters)
            page_font_color (str): Portal page font color. (Format  '#XXXXXX ', 6 hex characters)
            logo_name (str): Name of logo file
            logo (str): Logo image. This is in base64 data format
            background_image_name (str): Name of image file used as background
            background_image (str): Background image. This is in base64 data format
            max_columns (int): Layout  Valid Values: 1, 2
            page_title (str): Page title of the portal
            welcome_text (str): Welcome text to be displayed in the portal
            terms_condition (str): Terms and condition text to be displayed in the portal
            display_terms_checkbox (bool): Show/hide terms condition check box
            display_term_options (str): Inline or overlay display option. Internal indicates inline
                Valid Values: internal, external
            ad_url (str): Advertisement url. This requires add image input
            login_image_name (str): Name of logo file
            ad_image (str): Advertisement image. This is in base64 data format
            is_config_associated (bool): Indicates whether any configuration is associated to the
                portal
            capture_url (str): URL to be used in wlan configuration
            override_common_name (str): Parameter to override the common name
            override_common_name_enabled (bool): Flag indicating whether the common name should be
                overridden

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/portals"

        json_data = {
            'name': name,
            'auth_type': auth_type,
            'username_password_enabled': username_password_enabled,
            'registration_enabled': registration_enabled,
            'verify_registration': verify_registration,
            'bypass_cna_policy': bypass_cna_policy,
            'cna_policy': cna_policy,
            'register_accept_email': register_accept_email,
            'register_accept_phone': register_accept_phone,
            'free_wifi_duration': free_wifi_duration,
            'self_reg_account_unlimited': self_reg_account_unlimited,
            'self_reg_account_expire_days': self_reg_account_expire_days,
            'self_reg_account_expire_hours': self_reg_account_expire_hours,
            'self_reg_account_expire_minutes': self_reg_account_expire_minutes,
            'login_button_title': login_button_title,
            'whitelist_urls': whitelist_urls,
            'custom_username_label': custom_username_label,
            'custom_password_label': custom_password_label,
            'custom_sender_message': custom_sender_message,
            'custom_verification_message': custom_verification_message,
            'custom_registration_message': custom_registration_message,
            'custom_pwd_reset_message': custom_pwd_reset_message,
            'auth_sources': auth_sources,
            'facebook_wifi_configure_url': facebook_wifi_configure_url,
            'facebook_wifi_gateway_id': facebook_wifi_gateway_id,
            'redirect_url': redirect_url,
            'auth_failure_message': auth_failure_message,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'mac_caching_enabled': mac_caching_enabled,
            'is_shared': is_shared,
            'simultaneous_login_limit': simultaneous_login_limit,
            'daily_usage_limit': daily_usage_limit,
            'by_hours': by_hours,
            'by_minutes': by_minutes,
            'data_type': data_type,
            'data': data,
            'background_color': background_color,
            'button_color': button_color,
            'header_fill_color': header_fill_color,
            'page_font_color': page_font_color,
            'logo_name': logo_name,
            'logo': logo,
            'background_image_name': background_image_name,
            'background_image': background_image,
            'max_columns': max_columns,
            'page_title': page_title,
            'welcome_text': welcome_text,
            'terms_condition': terms_condition,
            'display_terms_checkbox': display_terms_checkbox,
            'display_term_options': display_term_options,
            'ad_url': ad_url,
            'login_image_name': login_image_name,
            'ad_image': ad_image,
            'is_config_associated': is_config_associated,
            'capture_url': capture_url,
            'override_common_name': override_common_name,
            'override_common_name_enabled': override_common_name_enabled
        }

        return await self.post(url, json_data=json_data)

    async def guest_preview_portal(
        self,
        portal_id: str,
    ) -> Response:
        """Get preview url of guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/preview/{portal_id}"

        return await self.get(url)

    async def guest_get_portal(
        self,
        portal_id: str,
    ) -> Response:
        """Get guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.get(url)

    async def guest_update_portal(
        self,
        portal_id: str,
        name: str,
        auth_type: str,
        username_password_enabled: bool,
        registration_enabled: bool,
        verify_registration: bool,
        bypass_cna_policy: bool,
        cna_policy: str,
        register_accept_email: bool,
        register_accept_phone: bool,
        free_wifi_duration: int,
        self_reg_account_unlimited: bool,
        self_reg_account_expire_days: int,
        self_reg_account_expire_hours: int,
        self_reg_account_expire_minutes: int,
        login_button_title: str,
        whitelist_urls: List[str],
        custom_username_label: str,
        custom_password_label: str,
        custom_sender_message: str,
        custom_verification_message: str,
        custom_registration_message: str,
        custom_pwd_reset_message: str,
        auth_sources: list,
        facebook_wifi_configure_url: str,
        facebook_wifi_gateway_id: str,
        redirect_url: str,
        auth_failure_message: str,
        days: int,
        hours: int,
        minutes: int,
        mac_caching_enabled: bool,
        is_shared: bool,
        simultaneous_login_limit: int,
        daily_usage_limit: str,
        by_hours: int,
        by_minutes: int,
        data_type: str,
        data: int,
        background_color: str,
        button_color: str,
        header_fill_color: str,
        page_font_color: str,
        logo_name: str,
        logo: str,
        background_image_name: str,
        background_image: str,
        max_columns: int,
        page_title: str,
        welcome_text: str,
        terms_condition: str,
        display_terms_checkbox: bool,
        display_term_options: str,
        ad_url: str,
        login_image_name: str,
        ad_image: str,
        is_config_associated: bool,
        capture_url: str,
        override_common_name: str,
        override_common_name_enabled: bool,
    ) -> Response:
        """Update guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page
            name (str): Name of the portal (max length 22 characters)
            auth_type (str): Authentication type of portal  Valid Values: unauthenticated,
                authenticated, facebookwifi
            username_password_enabled (bool): Username/Password authentication type
            registration_enabled (bool): Identify if guest user can register on the portal
            verify_registration (bool): Identify if verification is required for guest registration
            bypass_cna_policy (bool): Identify if CNA policy is to be bypassed
            cna_policy (str): cna_policy  Valid Values: allow_always, automatic
            register_accept_email (bool): Identify if guest registration is performed via e-mail
            register_accept_phone (bool): Identify if guest registration is performed via phone
            free_wifi_duration (int): Free wifi allowed durations (0 to 59 minutes)
            self_reg_account_unlimited (bool): Indicates if default registration account expiry is
                unlimited or not
            self_reg_account_expire_days (int): Specify the default registration account expiry in
                days, min 0 to max 180.
            self_reg_account_expire_hours (int): Specify default registration account expiry in
                hours, min 0 to max 23
            self_reg_account_expire_minutes (int): Specify default registration account expiry in
                minutes, min 0 to max 59
            login_button_title (str): Customizable login button label (optional field, max 32
                characters).
            whitelist_urls (List[str]): List of urls to  white list or allow  access before portal
                login
            custom_username_label (str): Custom username lable to be used in registration and
                password reset messages (max 30 characters)
            custom_password_label (str): Custom password label to be used in registration and
                password reset messages (max 10 characters)
            custom_sender_message (str): Custom sender text that will be in the footer of the sms
                message. This will help guest users identify who is sending them sms message. (max
                20 characters)
            custom_verification_message (str): Custom verfication message that guest will receieve
                for when verification is performed (max 90 characters)
            custom_registration_message (str): Custom registration message that guest will receieve
                for when registration is performed (max 90 characters)
            custom_pwd_reset_message (str): Custom passowrd reset message that guest will receieve
                for when password resert is performed (max 90 characters)
            auth_sources (list): List of social auth app values. This could be empty array.
            facebook_wifi_configure_url (str): Use URL to create or customize the facebook wifi page
                which has to have facebook_wifi_gateway_id as a query param. Admin has to configure
                the page inorder to get facebook wifi working
            facebook_wifi_gateway_id (str): Gateway should be used with facebook_wifi_configure_url
                to configure facebook wifi portal. This is auto generated.
            redirect_url (str): Redirect url on succesful login
            auth_failure_message (str): Display message on authentication failure (max 4096
                characters)
            days (int): Session expiry in unit of days. Min 0, Max 180
            hours (int): Session expiry in unit of hours. Min 0, Max 23
            minutes (int): Session expiry in unit of minutes. Min 0, Max 59
            mac_caching_enabled (bool): Flag to indicate whether mac chacing enabled
            is_shared (bool): Flag to indicate whether portal is shared
            simultaneous_login_limit (int): Simultaneous portal logins limit. Value of 0 indicates
                there is no limit  Valid Values: 0 - 5
            daily_usage_limit (str): IO data allowed to be used in a day. Either by time or data
                usage  Valid Values: bytime, bydata, nolimit
            by_hours (int): Time limit in hours to access network (Max 23 hours)
            by_minutes (int): Time limit in minutes to access network (Max 59 minutes)
            data_type (str): Data usage per session or per visitor  Valid Values: session, visitor
            data (int): Data usage limit in MB (Min 1 MB, Max 102400 MB)
            background_color (str): Background color of the portal. (Format  '#XXXXXX', 6 hex
                characters)
            button_color (str): Button color. (Format  '#XXXXXX' , 6 hex characters)
            header_fill_color (str): Header color of the portal. This field can could be null.
                (Format '#XXXXXX' , 6 hex characters)
            page_font_color (str): Portal page font color. (Format  '#XXXXXX ', 6 hex characters)
            logo_name (str): Name of logo file
            logo (str): Logo image. This is in base64 data format
            background_image_name (str): Name of image file used as background
            background_image (str): Background image. This is in base64 data format
            max_columns (int): Layout  Valid Values: 1, 2
            page_title (str): Page title of the portal
            welcome_text (str): Welcome text to be displayed in the portal
            terms_condition (str): Terms and condition text to be displayed in the portal
            display_terms_checkbox (bool): Show/hide terms condition check box
            display_term_options (str): Inline or overlay display option. Internal indicates inline
                Valid Values: internal, external
            ad_url (str): Advertisement url. This requires add image input
            login_image_name (str): Name of logo file
            ad_image (str): Advertisement image. This is in base64 data format
            is_config_associated (bool): Indicates whether any configuration is associated to the
                portal
            capture_url (str): URL to be used in wlan configuration
            override_common_name (str): Parameter to override the common name
            override_common_name_enabled (bool): Flag indicating whether the common name should be
                overridden

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        json_data = {
            'name': name,
            'auth_type': auth_type,
            'username_password_enabled': username_password_enabled,
            'registration_enabled': registration_enabled,
            'verify_registration': verify_registration,
            'bypass_cna_policy': bypass_cna_policy,
            'cna_policy': cna_policy,
            'register_accept_email': register_accept_email,
            'register_accept_phone': register_accept_phone,
            'free_wifi_duration': free_wifi_duration,
            'self_reg_account_unlimited': self_reg_account_unlimited,
            'self_reg_account_expire_days': self_reg_account_expire_days,
            'self_reg_account_expire_hours': self_reg_account_expire_hours,
            'self_reg_account_expire_minutes': self_reg_account_expire_minutes,
            'login_button_title': login_button_title,
            'whitelist_urls': whitelist_urls,
            'custom_username_label': custom_username_label,
            'custom_password_label': custom_password_label,
            'custom_sender_message': custom_sender_message,
            'custom_verification_message': custom_verification_message,
            'custom_registration_message': custom_registration_message,
            'custom_pwd_reset_message': custom_pwd_reset_message,
            'auth_sources': auth_sources,
            'facebook_wifi_configure_url': facebook_wifi_configure_url,
            'facebook_wifi_gateway_id': facebook_wifi_gateway_id,
            'redirect_url': redirect_url,
            'auth_failure_message': auth_failure_message,
            'days': days,
            'hours': hours,
            'minutes': minutes,
            'mac_caching_enabled': mac_caching_enabled,
            'is_shared': is_shared,
            'simultaneous_login_limit': simultaneous_login_limit,
            'daily_usage_limit': daily_usage_limit,
            'by_hours': by_hours,
            'by_minutes': by_minutes,
            'data_type': data_type,
            'data': data,
            'background_color': background_color,
            'button_color': button_color,
            'header_fill_color': header_fill_color,
            'page_font_color': page_font_color,
            'logo_name': logo_name,
            'logo': logo,
            'background_image_name': background_image_name,
            'background_image': background_image,
            'max_columns': max_columns,
            'page_title': page_title,
            'welcome_text': welcome_text,
            'terms_condition': terms_condition,
            'display_terms_checkbox': display_terms_checkbox,
            'display_term_options': display_term_options,
            'ad_url': ad_url,
            'login_image_name': login_image_name,
            'ad_image': ad_image,
            'is_config_associated': is_config_associated,
            'capture_url': capture_url,
            'override_common_name': override_common_name,
            'override_common_name_enabled': override_common_name_enabled
        }

        return await self.put(url, json_data=json_data)

    async def guest_delete_portal(
        self,
        portal_id: str,
    ) -> Response:
        """Delete guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.delete(url)

    async def guest_get_visitors(
        self,
        portal_id: str,
        sort: str = '+name',
        filter_by: str = None,
        filter_value: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all visitors created against a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            sort (str, optional): + is for ascending  and - for descending order , sorts by name for
                now  Valid Values: +name, -name
            filter_by (str, optional): filter by email or name  Valid Values: name, email
            filter_value (str, optional): filter value
            offset (int, optional): Starting index of element for a paginated query Defaults to 0.
            limit (int, optional): Number of items required per query Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors"

        params = {
            'sort': sort,
            'filter_by': filter_by,
            'filter_value': filter_value,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def guest_create_visitor(
        self,
        portal_id: str,
        name: str,
        id: str,
        company_name: str,
        phone: str,
        email: str,
        is_enabled: bool,
        valid_till_no_limit: bool,
        valid_till_days: int,
        valid_till_hours: int,
        valid_till_minutes: int,
        notify: bool,
        notify_to: str,
        password: str,
        status: bool,
        created_at: str,
        expire_at: str,
    ) -> Response:
        """Create a new guest visitor of a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            name (str): Visitor account name
            id (str): NA for visitor post/put method. ID of the visitor
            company_name (str): Company name of the visitor
            phone (str): Phone number of the visitor; Format [+CountryCode][PhoneNumber]
            email (str): Email address of the visitor
            is_enabled (bool): Enable or disable the visitor account
            valid_till_no_limit (bool): Visitor account will not expire when this is set to true
            valid_till_days (int): Account validity in days
            valid_till_hours (int): Account validity in hours
            valid_till_minutes (int): Account validity in minutes
            notify (bool): Flag to notify the password via email or number
            notify_to (str): Notify to email or phone. Defualt is phone when it is provided
                otherwise email.  Valid Values: email, phone
            password (str): Password
            status (bool): This field provides status of the account. Returns true when enabled and
                not expired. NA for visitor post/put method. This is optional fields.
            created_at (str): This field indicates the created date timestamp value. It is generated
                while creating visitor. NA for visitor post/put method. This is optional field.
            expire_at (str): This field indicates expiry time timestamp value. It is generated based
                on the valid_till value and created_at time. NA for visitor post/put method. This is
                optional field

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors"

        json_data = {
            'name': name,
            'id': id,
            'company_name': company_name,
            'phone': phone,
            'email': email,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_till_no_limit,
            'valid_till_days': valid_till_days,
            'valid_till_hours': valid_till_hours,
            'valid_till_minutes': valid_till_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password,
            'status': status,
            'created_at': created_at,
            'expire_at': expire_at
        }

        return await self.post(url, json_data=json_data)

    async def guest_get_visitor(
        self,
        portal_id: str,
        visitor_id: str,
    ) -> Response:
        """Get guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        return await self.get(url)

    async def guest_update_visitor(
        self,
        portal_id: str,
        visitor_id: str,
        name: str,
        id: str,
        company_name: str,
        phone: str,
        email: str,
        is_enabled: bool,
        valid_till_no_limit: bool,
        valid_till_days: int,
        valid_till_hours: int,
        valid_till_minutes: int,
        notify: bool,
        notify_to: str,
        password: str,
        status: bool,
        created_at: str,
        expire_at: str,
    ) -> Response:
        """Update guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal
            name (str): Visitor account name
            id (str): NA for visitor post/put method. ID of the visitor
            company_name (str): Company name of the visitor
            phone (str): Phone number of the visitor; Format [+CountryCode][PhoneNumber]
            email (str): Email address of the visitor
            is_enabled (bool): Enable or disable the visitor account
            valid_till_no_limit (bool): Visitor account will not expire when this is set to true
            valid_till_days (int): Account validity in days
            valid_till_hours (int): Account validity in hours
            valid_till_minutes (int): Account validity in minutes
            notify (bool): Flag to notify the password via email or number
            notify_to (str): Notify to email or phone. Defualt is phone when it is provided
                otherwise email.  Valid Values: email, phone
            password (str): Password
            status (bool): This field provides status of the account. Returns true when enabled and
                not expired. NA for visitor post/put method. This is optional fields.
            created_at (str): This field indicates the created date timestamp value. It is generated
                while creating visitor. NA for visitor post/put method. This is optional field.
            expire_at (str): This field indicates expiry time timestamp value. It is generated based
                on the valid_till value and created_at time. NA for visitor post/put method. This is
                optional field

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        json_data = {
            'name': name,
            'id': id,
            'company_name': company_name,
            'phone': phone,
            'email': email,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_till_no_limit,
            'valid_till_days': valid_till_days,
            'valid_till_hours': valid_till_hours,
            'valid_till_minutes': valid_till_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password,
            'status': status,
            'created_at': created_at,
            'expire_at': expire_at
        }

        return await self.put(url, json_data=json_data)

    async def guest_delete_visitor(
        self,
        portal_id: str,
        visitor_id: str,
    ) -> Response:
        """Delete guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        return await self.delete(url)

    async def guest_get_sessions(
        self,
        essid_name: str,
        portal_id: str,
        sort: str = '+account_name',
        ssid_name: str = None,
        filter_by: str = None,
        filter_value: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all sessions of a ssid.

        Args:
            essid_name (str): get session of essid name
            portal_id (str): Portal ID of the splash page
            sort (str, optional): + is for ascending  and - for descending order , sorts by
                account_name for now  Valid Values: +account_name, -account_name
            ssid_name (str, optional): get session of ssid name. Not in use. Please filter by essid
                instead. Filtering by ssid will be deprecated in the future.
            filter_by (str, optional): filter by account_name  Valid Values: account_name
            filter_value (str, optional): filter value
            offset (int, optional): Starting index of element for a paginated query Defaults to 0.
            limit (int, optional): Number of items required per query Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/sessions"

        params = {
            'essid_name': essid_name,
            'sort': sort,
            'ssid_name': ssid_name,
            'filter_by': filter_by,
            'filter_value': filter_value,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def guest_get_wlans(
        self,
    ) -> Response:
        """Get all guest wlans.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/wlans"

        return await self.get(url)

    async def guest_get_enabled(
        self,
    ) -> Response:
        """Check if guest is enabled for current user.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/enabled"

        return await self.get(url)

    async def guest_get_re_provision(
        self,
    ) -> Response:
        """Provision cloud guest for current customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/reprovision"

        return await self.post(url)

    async def guest_wifi4eu_status(
        self,
        network_id: str,
        lang_code: str,
    ) -> Response:
        """WiFi4EU Status.

        Args:
            network_id (str): Network ID for WiFi4EU
            lang_code (str): Two letter language code for WiFi4EU

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/wifi4eu/lang_code/{lang_code}"

        params = {
            'network_id': network_id
        }

        return await self.post(url, params=params)

    async def guest_get_statistics(
        self,
        days: int,
        ssid: str,
    ) -> Response:
        """Get summary statistics.

        Args:
            days (int): Num of days for which session data is required  Valid Values: 1, 7, 28
            ssid (str): A comma separated list of SSIDs for which session data is required

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/summary"

        params = {
            'days': days,
            'ssid': ssid
        }

        return await self.get(url, params=params)

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
        clientId: str,
        password: str,
        token: str,
        url: str,
        username: str,
        collectorId: str,
        description: str,
        outputFormatType: str,
        protocol: str,
        name: str,
        transportProfileId: str,
        reportInterval: int = None,
        rssiAggregation: str = None,
    ) -> Response:
        """Update a transport profile by id.

        Args:
            clientId (str): clientId
            password (str): password
            token (str): token
            url (str): url
            username (str): username
            collectorId (str): collectorId
            description (str): description
            outputFormatType (str): outputFormatType  Valid Values: JSON, PROTOBUF
            protocol (str): protocol  Valid Values: WS, WSS, MQTT, MQTT_WS, MQTT_WSS
            name (str): name
            transportProfileId (str): The Unique Transport Profile Id
            reportInterval (int, optional): reportInterval
            rssiAggregation (str, optional): rssiAggregation  Valid Values: AVERAGE, LATEST, MAX

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/iot_operations/api/v1/transport_profiles/{transportProfileId}"

        json_data = {
            'clientId': clientId,
            'password': password,
            'token': token,
            'url': url,
            'username': username,
            'collectorId': collectorId,
            'description': description,
            'outputFormatType': outputFormatType,
            'protocol': protocol,
            'name': name,
            'reportInterval': reportInterval,
            'rssiAggregation': rssiAggregation
        }

        return await self.put(url, json_data=json_data)

    async def iot_operations_deleteusingdelete(
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/monitoring/v2/networks/{network_name}"

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site
        }

        return await self.get(url, params=params)

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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'site': site
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'swarm_id': swarm_id,
            'label': label,
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'serial': serial,
            'macaddr': macaddr,
            'cluster_id': cluster_id,
            'calculate_total': calculate_total,
            'sort': sort,
            'offset': offset,
            'limit': limit
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
            band (str, optional): Filter by band (2.4, 5 or 6). Valid only when serial parameter is
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
            'radio_number': radio_number,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            serial (str, optional): Filter by AP serial
            cluster_id (str, optional): Filter by Mobility Controller serial number
            interval (str, optional): Filter by interval (5minutes or 1hour or 1day or 1week).
            band (str, optional): Filter by band (2.4, 5 or 6). Valid only when serial parameter is
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'to_timestamp': to_timestamp
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
            'group': group,
            'count': count,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'group': group,
            'count': count,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            network (str, optional): Filter by network name. Field supported for wireless clients
                only
            serial (str, optional): Filter by AP serial number
            os_type (str, optional): Filter by client os type
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band. Value can be either "2.4", "5" or "6". Field
                supported for wireless clients only.
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'network': network,
            'serial': serial,
            'os_type': os_type,
            'cluster_id': cluster_id,
            'band': band,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'last_client_mac': last_client_mac,
            'offset': offset,
            'limit': limit
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'serial': serial,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'last_client_mac': last_client_mac,
            'offset': offset,
            'limit': limit
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
        band: str = None,
        stack_id: str = None,
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
                Clients.                                  Failed to connect status not supported for
                wired clients.                                    Valid Values: CONNECTED,
                FAILED_TO_CONNECT
            group (str, optional): Filter by group name
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            site (str, optional): Filter by Site name
            network (str, optional): Filter by network name. Field supported for wireless clients
                only
            serial (str, optional): Filter by device serial number
            cluster_id (str, optional): Filter by Mobility Controller serial number
            band (str, optional): Filter by band. Value can be either "2.4", "5" or "6". Field
                supported for wireless clients only.
            stack_id (str, optional): Filter by Switch stack_id. Only for Wired Clients
            os_type (str, optional): Filter by OS Type
            fields (str, optional): Comma separated list of fields to be returned.
                Valid fields for wired clients are name, ip_address, username, associated_device,
                group_name, interface_mac, vlan.                                      Valid field
                values for wireless clients are name, ip_address, username, os_type, connection,
                associated_device, group_name, swarm_id, network, radio_mac, manufacturer, vlan,
                encryption_method, radio_number, speed, usage, health, labels, site,
                signal_strength, signal_db, snr.
            calculate_total (bool, optional): Whether to calculate total Wireless/Wired Clients
            sort (str, optional): Sort parameter may be one of +macaddr, -macaddr.  Default is
                '+macaddr'
            last_client_mac (str, optional): Input the last processed client mac that got received
                in your last response. Please note that when last_client_mac is inputted , offset
                will not make any sense and by default the results are sorted by macaddr.
            show_usage (bool, optional): Whether to show usage
            show_manufacturer (bool, optional): Whether to show manufacturer
            show_signal_db (bool, optional): Whether to show signal_db and signal_strength. Field
                supported for wireless clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'site': site,
            'network': network,
            'serial': serial,
            'cluster_id': cluster_id,
            'band': band,
            'stack_id': stack_id,
            'os_type': os_type,
            'fields': fields,
            'calculate_total': calculate_total,
            'sort': sort,
            'last_client_mac': last_client_mac,
            'show_usage': show_usage,
            'show_manufacturer': show_manufacturer,
            'show_signal_db': show_signal_db,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'serial': serial,
            'macaddr': macaddr,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            network (str, optional): Filter by network name. Field supported for wireless clients
                only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'network': network,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'count': count,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
            label (str, optional): Filter by Label name
            network (str, optional): Filter by network name. Field supported for wireless clients
                only
            cluster_id (str, optional): Filter by Mobility Controller serial number
            stack_id (str, optional): Filter by Switch stack_id
            device_type (str, optional): Filter by device type. Value can be either "AP" or "Switch"
            serial (str, optional): Filter by Ap or serial
            band (str, optional): Filter by band. Value can be either "2.4", "5" or "6". Valid only
                when serial parameter is specified.
            radio_number (int, optional): Filter by radio_number (0, 1 or 2). Valid only when serial
                parameter is specified. If band is provided and radio_number is not provided then
                radio_number is defaulted to 0, 1 and 2 for band 5, 2.4 and 6 respectively.
            from_timestamp (int, optional): Need information from this timestamp. Timestamp is epoch
                in seconds. Default is current timestamp minus 3 hours
            to_timestamp (int, optional): Need information to this timestamp. Timestamp is epoch in
                seconds. Default is current timestamp

        Returns:
            Response: CentralAPI Response object
        """
        url = "/monitoring/v1/clients/count"

        params = {
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'network': network,
            'cluster_id': cluster_id,
            'stack_id': stack_id,
            'device_type': device_type,
            'serial': serial,
            'band': band,
            'radio_number': radio_number,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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

    async def monitoring_get_mc_v2(
        self,
        serial: str,
        stats_metric: bool = False,
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
            'interval': interval,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'interval': interval,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'interval': interval,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            'interval': interval,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'timerange': timerange,
            'offset': offset,
            'limit': limit
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
            'reservation': reservation,
            'offset': offset,
            'limit': limit
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
            'sort': sort,
            'offset': offset,
            'limit': limit
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
            'sort': sort,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
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
            'sort': sort,
            'offset': offset,
            'limit': limit
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
            'sort': sort,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
            'group': group,
            'label': label,
            'serial': serial,
            'stack_id': stack_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'group': group,
            'label': label,
            'stack_id': stack_id,
            'count': count,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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

    # API-FLAW returns 200 w/ no content if there are no stacks rather than an empty list
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
            'hostname': hostname,
            'group': group,
            'offset': offset,
            'limit': limit
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
            swarm_id (str, optional): Filter by Swarm ID. Field supported for AP clients only
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
            'group': group,
            'swarm_id': swarm_id,
            'label': label,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
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
            'calculate_total': calculate_total,
            'offset': offset,
            'limit': limit
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

    async def msp_create_customer_v2(
        self,
        customer_name: str,
        country_name: str,
        street_address: str,
        city: str,
        state: str,
        zip_postal_code: str,
        name: str,
        description: str,
        lock_msp_ssids: bool,
    ) -> Response:
        """Create a new customer with V2 API.

        Args:
            customer_name (str): Customer Name (Max 70 chars)
            country_name (str): Country Name (Max 50 chars)
            street_address (str): Street Address (Max 50 chars)
            city (str): City (Max 70 chars)
            state (str): City (Max 70 chars)
            zip_postal_code (str): Zip Code (Max 20 chars)
            name (str): Group Name
            description (str): Customer Description (Max length 32 chars)
            lock_msp_ssids (bool): enable/disable lock ssid

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v2/customers"

        json_data = {
            'customer_name': customer_name,
            'country_name': country_name,
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_postal_code': zip_postal_code,
            'name': name,
            'description': description,
            'lock_msp_ssids': lock_msp_ssids
        }

        return await self.post(url, json_data=json_data)

    async def msp_edit_customer_v2(
        self,
        customer_id: str,
        customer_name: str,
        country_name: str,
        street_address: str,
        city: str,
        state: str,
        zip_postal_code: str,
        name: str,
        description: str,
        lock_msp_ssids: bool,
    ) -> Response:
        """Update a customer with V2 API.

        Args:
            customer_id (str): Filter on Customer ID
            customer_name (str): Customer Name (Max 70 chars)
            country_name (str): Country Name (Max 50 chars)
            street_address (str): Street Address (Max 50 chars)
            city (str): City (Max 70 chars)
            state (str): City (Max 70 chars)
            zip_postal_code (str): Zip Code (Max 20 chars)
            name (str): Group Name
            description (str): Customer Description (Max length 32 chars)
            lock_msp_ssids (bool): enable/disable lock ssid

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v2/customers/{customer_id}"

        json_data = {
            'customer_name': customer_name,
            'country_name': country_name,
            'street_address': street_address,
            'city': city,
            'state': state,
            'zip_postal_code': zip_postal_code,
            'name': name,
            'description': description,
            'lock_msp_ssids': lock_msp_ssids
        }

        return await self.put(url, json_data=json_data)

    async def msp_get_country_code(
        self,
    ) -> Response:
        """Get list of country code list.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v2/get_country_code"

        return await self.get(url)

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

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
        """Get list of devices and licenses under the Customer account based on limit and offset,
        offset should be a multiple of the limit value.

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
            'device_type': device_type,
            'offset': offset,
            'limit': limit
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

    async def msp_unassign_tenant_devices(
        self,
        customer_id: str,
    ) -> Response:
        """Un-assign all devices from Tenant/end-customer.

        Args:
            customer_id (str): Filter on Customer ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/msp_api/v2/{customer_id}/devices"

        return await self.put(url)

    async def msp_get_devices(
        self,
        device_allocation_status: int = 0,
        device_type: str = None,
        customer_name: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get list of devices and licenses under the MSP account based on limit and offset, offset
        should be a multiple of the limit value.

        Args:
            device_allocation_status (int, optional): Filter on device_allocation_status to get list
                of devices                                                         0-All
                1-Allocated                                                         2-Available
                Valid Values: 0 - 2
            device_type (str, optional): Filter on device_type to get list of devices
                iap                                            switch
                all_controller  Valid Values: iap, switch, all_controller
            customer_name (str, optional): Filter on Customer Name
            offset (int, optional): pagination start index Defaults to 0.
            limit (int, optional): pagination end index Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/msp_api/v1/devices"

        params = {
            'device_allocation_status': device_allocation_status,
            'device_type': device_type,
            'customer_name': customer_name,
            'offset': offset,
            'limit': limit
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

    async def branchhealth_get_sites_(
        self,
        name: str = None,
        column: int = None,
        order: int = None,
        Site_properties_used_with_thresholds: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get data for all sites.

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
        url = "/branchhealth/v1/site"

        params = {
            'name': name,
            'column': column,
            'order': order,
            'Site_properties_used_with_thresholds': Site_properties_used_with_thresholds,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def central_get_types_(
        self,
        calculate_total: bool = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
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
            'sort': sort,
            'offset': offset,
            'limit': limit
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

    async def central_update_customer_settings_(
        self,
        add_sites_to_mute: List[str],
        remove_sites_from_mute: List[str],
        update_site_emails: list,
        default_recipients_email_list: List[str],
        email_subject_line_template: str,
    ) -> Response:
        """Update customer settings.

        Args:
            add_sites_to_mute (List[str]): Sites to be muted for alert
            remove_sites_from_mute (List[str]): Sites to be unmuted for alert
            update_site_emails (list): update_site_emails
            default_recipients_email_list (List[str]): Emails to be saved as deafult recipient list
            email_subject_line_template (str): Subject line to use for email notifications

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications/customer_settings"

        json_data = {
            'add_sites_to_mute': add_sites_to_mute,
            'remove_sites_from_mute': remove_sites_from_mute,
            'update_site_emails': update_site_emails,
            'default_recipients_email_list': default_recipients_email_list,
            'email_subject_line_template': email_subject_line_template
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
            'group': group,
            'label': label,
            'serial': serial,
            'site': site,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'severity': severity,
            'type': type,
            'search': search,
            'calculate_total': calculate_total,
            'ack': ack,
            'fields': fields,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
        NoName: list = None,
    ) -> Response:
        """Delete devices using Serial number.

        Args:
            NoName (list, optional): ...

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/device_inventory/v1/devices"

        return await self.delete(url)

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
        app_only_stats: bool = None,
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

    async def platform_gw_get_customer_enabled_services(
        self,
    ) -> Response:
        """Get enabled services for customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/licensing/v1/services/enabled"

        return await self.get(url)

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

    async def get_rds_v1_manually_contained_aps(
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
        """List manually contained APs.

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
        url = "/rapids/v1/manually_contained_aps"

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
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'calculate_total': calculate_total,
            'sort': sort,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
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
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'calculate_total': calculate_total,
            'sort': sort,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
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

        params = {
            'group': group,
            'label': label,
            'site': site,
            'start': start,
            'end': end,
            'sort': sort,
            'swarm_id': swarm_id,
            'from_timestamp': from_timestamp,
            'to_timestamp': to_timestamp,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
        url = "//sdwan-mon-api/external/noc/reports/wan/policy-compliance"

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
            'device': device,
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

        params = {
            'device': device,
            'address': address
        }

        return await self.put(url, params=params)

    async def get_routing_v1_bgp_neighbor_route_learned(
        self,
        device: str,
        address: str,
        marker: str = None,
        limit: int = 100,
    ) -> Response:
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

        params = {
            'device': device,
            'address': address,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'address': address,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device
        }

        return await self.put(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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
            'device': device,
            'address': address,
            'marker': marker,
            'limit': limit
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

        params = {
            'device': device,
            'marker': marker,
            'limit': limit
        }

        return await self.get(url, params=params)

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
            'device': device
        }

        return await self.get(url, params=params)

    async def airgroup_config_get_aruba_service_ids_id1(
        self,
        name: str,
        service_id: str,
    ) -> Response:
        """Retrieve service_ids by identifier service_id.

        Args:
            name (str): Name of the Custom service. This should be unique
            service_id (str): An MDNS or SSDP service ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/service_ids/{service_id}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_service_ids_id1(
        self,
        name: str,
        service_id: str,
        new_service_id: str,
    ) -> Response:
        """Create service_ids by identifier service_id.

        Args:
            name (str): Name of the Custom service. This should be unique
            service_id (str): An MDNS or SSDP service ID
            new_service_id (str): An MDNS or SSDP service ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/service_ids/{service_id}/"

        json_data = {
            'new_service_id': new_service_id
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_service_ids_id1(
        self,
        name: str,
        service_id: str,
        new_service_id: str,
    ) -> Response:
        """Create/Update service_ids by identifier service_id.

        Args:
            name (str): Name of the Custom service. This should be unique
            service_id (str): An MDNS or SSDP service ID
            new_service_id (str): An MDNS or SSDP service ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/service_ids/{service_id}/"

        json_data = {
            'new_service_id': new_service_id
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_service_ids_id1(
        self,
        name: str,
        service_id: str,
    ) -> Response:
        """Delete service_ids by identifier service_id.

        Args:
            name (str): Name of the Custom service. This should be unique
            service_id (str): An MDNS or SSDP service ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/service_ids/{service_id}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_service_ids_id2(
        self,
        name: str,
    ) -> Response:
        """Retrieve service_ids.

        Args:
            name (str): Name of the Custom service. This should be unique

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/service_ids/"

        return await self.get(url)

    async def airgroup_config_get_aruba_custom_services_id3(
        self,
        name: str,
    ) -> Response:
        """Retrieve custom_services by identifier name.

        Args:
            name (str): Name of the Custom service. This should be unique

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_custom_services_id2(
        self,
        name: str,
        new_name: str,
        description: str,
        service_ids: list,
    ) -> Response:
        """Create custom_services by identifier name.

        Args:
            name (str): Name of the Custom service. This should be unique
            new_name (str): Name of the Custom service. This should be unique
            description (str): Few line description of the service
            service_ids (list): List of Service-IDs found in protocol packets that can be used to
                identify this service. Syntax is as follows. mDNS: _<label>. repeated ending with
                tcp or _udp SSDP:  urn:<domain-name>:service:<device-type>:<version> or urn:<domain-
                name>:device:<device-type>:<version>

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/"

        json_data = {
            'new_name': new_name,
            'description': description,
            'service_ids': service_ids
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_custom_services_id2(
        self,
        name: str,
        new_name: str,
        description: str,
        service_ids: list,
    ) -> Response:
        """Create/Update custom_services by identifier name.

        Args:
            name (str): Name of the Custom service. This should be unique
            new_name (str): Name of the Custom service. This should be unique
            description (str): Few line description of the service
            service_ids (list): List of Service-IDs found in protocol packets that can be used to
                identify this service. Syntax is as follows. mDNS: _<label>. repeated ending with
                tcp or _udp SSDP:  urn:<domain-name>:service:<device-type>:<version> or urn:<domain-
                name>:device:<device-type>:<version>

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/"

        json_data = {
            'new_name': new_name,
            'description': description,
            'service_ids': service_ids
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_custom_services_id2(
        self,
        name: str,
    ) -> Response:
        """Delete custom_services by identifier name.

        Args:
            name (str): Name of the Custom service. This should be unique

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/custom_services/{name}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_custom_services_id4(
        self,
    ) -> Response:
        """Retrieve custom_services.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup-config/v2/custom_services/"

        return await self.get(url)

    async def airgroup_config_get_aruba_disallowed_roles_id5(
        self,
        mac_address: str,
        role: str,
    ) -> Response:
        """Retrieve disallowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/disallowed_roles/{role}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_roles_id3(
        self,
        mac_address: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create disallowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/disallowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_roles_id3(
        self,
        mac_address: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create/Update disallowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/disallowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_roles_id3(
        self,
        mac_address: str,
        role: str,
    ) -> Response:
        """Delete disallowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/disallowed_roles/{role}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_roles_id6(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve disallowed_roles.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/disallowed_roles/"

        return await self.get(url)

    async def airgroup_config_get_aruba_allowed_roles_id7(
        self,
        mac_address: str,
        role: str,
    ) -> Response:
        """Retrieve allowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/allowed_roles/{role}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_allowed_roles_id4(
        self,
        mac_address: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create allowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/allowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_allowed_roles_id4(
        self,
        mac_address: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create/Update allowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/allowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_allowed_roles_id4(
        self,
        mac_address: str,
        role: str,
    ) -> Response:
        """Delete allowed_roles by identifier role.

        Args:
            mac_address (str): Mac-address of the airgroup server
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/allowed_roles/{role}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_allowed_roles_id8(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve allowed_roles.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/allowed_roles/"

        return await self.get(url)

    async def airgroup_config_get_aruba_role_restrictions_id9(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve role_restrictions.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/"

        return await self.get(url)

    async def airgroup_config_post_aruba_role_restrictions_id5(
        self,
        mac_address: str,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create role_restrictions.

        Args:
            mac_address (str): Mac-address of the airgroup server
            disallowed_roles (list): List of disallowed user Roles for this server. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this server. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/"

        json_data = {
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_role_restrictions_id5(
        self,
        mac_address: str,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create/Update role_restrictions.

        Args:
            mac_address (str): Mac-address of the airgroup server
            disallowed_roles (list): List of disallowed user Roles for this server. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this server. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/"

        json_data = {
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_role_restrictions_id5(
        self,
        mac_address: str,
    ) -> Response:
        """Delete role_restrictions.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/role_restrictions/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_ap_list_id10(
        self,
        mac_address: str,
        serial_number: str,
    ) -> Response:
        """Retrieve ap_list by identifier serial_number.

        Args:
            mac_address (str): Mac-address of the airgroup server
            serial_number (str): AP Serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/ap_list/{serial_number}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_ap_list_id6(
        self,
        mac_address: str,
        serial_number: str,
        new_serial_number: str,
        device_name: str,
    ) -> Response:
        """Create ap_list by identifier serial_number.

        Args:
            mac_address (str): Mac-address of the airgroup server
            serial_number (str): AP Serial number
            new_serial_number (str): AP Serial number
            device_name (str): Device Name. This field should be omitted for POST operation and
                instead use 'serial_number' to identify the AP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/ap_list/{serial_number}/"

        json_data = {
            'new_serial_number': new_serial_number,
            'device_name': device_name
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_ap_list_id6(
        self,
        mac_address: str,
        serial_number: str,
        new_serial_number: str,
        device_name: str,
    ) -> Response:
        """Create/Update ap_list by identifier serial_number.

        Args:
            mac_address (str): Mac-address of the airgroup server
            serial_number (str): AP Serial number
            new_serial_number (str): AP Serial number
            device_name (str): Device Name. This field should be omitted for POST operation and
                instead use 'serial_number' to identify the AP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/ap_list/{serial_number}/"

        json_data = {
            'new_serial_number': new_serial_number,
            'device_name': device_name
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_ap_list_id6(
        self,
        mac_address: str,
        serial_number: str,
    ) -> Response:
        """Delete ap_list by identifier serial_number.

        Args:
            mac_address (str): Mac-address of the airgroup server
            serial_number (str): AP Serial number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/ap_list/{serial_number}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_ap_list_id11(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve ap_list.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/ap_list/"

        return await self.get(url)

    async def airgroup_config_get_aruba_network_visibility_id12(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve network_visibility.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/"

        return await self.get(url)

    async def airgroup_config_post_aruba_network_visibility_id7(
        self,
        mac_address: str,
        ap_list: list,
    ) -> Response:
        """Create network_visibility.

        Args:
            mac_address (str): Mac-address of the airgroup server
            ap_list (list): List of APs which will process this server's advertisements. One hop
                neighbours of these APs will also be included in this list dynamically.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/"

        json_data = {
            'ap_list': ap_list
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_network_visibility_id7(
        self,
        mac_address: str,
        ap_list: list,
    ) -> Response:
        """Create/Update network_visibility.

        Args:
            mac_address (str): Mac-address of the airgroup server
            ap_list (list): List of APs which will process this server's advertisements. One hop
                neighbours of these APs will also be included in this list dynamically.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/"

        json_data = {
            'ap_list': ap_list
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_network_visibility_id7(
        self,
        mac_address: str,
    ) -> Response:
        """Delete network_visibility.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/network_visibility/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_servers_list_id13(
        self,
        mac_address: str,
    ) -> Response:
        """Retrieve servers_list by identifier mac_address.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_servers_list_id8(
        self,
        mac_address: str,
        new_mac_address: str,
        name: str,
        disallowed_roles: list,
        allowed_roles: list,
        ap_list: list,
    ) -> Response:
        """Create servers_list by identifier mac_address.

        Args:
            mac_address (str): Mac-address of the airgroup server
            new_mac_address (str): Mac-address of the airgroup server
            name (str): Name of the airgroup server
            disallowed_roles (list): List of disallowed user Roles for this server. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this server. This must be empty if
                any roles are configured in 'disallowed_roles'
            ap_list (list): List of APs which will process this server's advertisements. One hop
                neighbours of these APs will also be included in this list dynamically.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/"

        json_data = {
            'new_mac_address': new_mac_address,
            'name': name,
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles,
            'ap_list': ap_list
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_servers_list_id8(
        self,
        mac_address: str,
        new_mac_address: str,
        name: str,
        disallowed_roles: list,
        allowed_roles: list,
        ap_list: list,
    ) -> Response:
        """Create/Update servers_list by identifier mac_address.

        Args:
            mac_address (str): Mac-address of the airgroup server
            new_mac_address (str): Mac-address of the airgroup server
            name (str): Name of the airgroup server
            disallowed_roles (list): List of disallowed user Roles for this server. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this server. This must be empty if
                any roles are configured in 'disallowed_roles'
            ap_list (list): List of APs which will process this server's advertisements. One hop
                neighbours of these APs will also be included in this list dynamically.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/"

        json_data = {
            'new_mac_address': new_mac_address,
            'name': name,
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles,
            'ap_list': ap_list
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_servers_list_id8(
        self,
        mac_address: str,
    ) -> Response:
        """Delete servers_list by identifier mac_address.

        Args:
            mac_address (str): Mac-address of the airgroup server

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/servers/servers_list/{mac_address}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_servers_list_id14(
        self,
        sort_by: str = None,
        search_name: str = None,
        search_mac: str = None,
        offset: str = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve servers_list.

        Args:
            sort_by (str, optional): This can be used to sort results by either name ore mac_address
                of the servers. Only ascending order is supported.  Valid Values: mac, name
            search_name (str, optional): This can be used to search the servers by their 'name'.
            search_mac (str, optional): This can be used to search the servers by their
                'mac_address'.
            offset (str, optional): Offset value from where to start lookup in the table Defaults to
                0.
            limit (int, optional): Max no.of Entries to be returned for Page. Default value is 10
                and max value allowed is 20 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup-config/v2/servers/servers_list/"

        params = {
            'sort_by': sort_by,
            'search_name': search_name,
            'search_mac': search_mac,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def airgroup_config_get_aruba_airgroup_status_id15(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        return await self.get(url)

    async def airgroup_config_post_aruba_airgroup_status_id9(
        self,
        node_type: str,
        node_id: str,
        airgroup_status: bool,
    ) -> Response:
        """Create airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled. This over-
                rides enable/disable at individual service level

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_airgroup_status_id9(
        self,
        node_type: str,
        node_id: str,
        airgroup_status: bool,
    ) -> Response:
        """Create/Update airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled. This over-
                rides enable/disable at individual service level

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        json_data = {
            'airgroup_status': airgroup_status
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_airgroup_status_id9(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Delete airgroup_status.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/airgroup_status/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_general_settings_id16(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/"

        return await self.get(url)

    async def airgroup_config_post_aruba_general_settings_id10(
        self,
        node_type: str,
        node_id: str,
        airgroup_status: bool,
        inherited_from: str,
    ) -> Response:
        """Create general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled. This over-
                rides enable/disable at individual service level
            inherited_from (str): This field indicates whether this profile was explicitly
                configured at this node or inherited from a parent node

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/"

        json_data = {
            'airgroup_status': airgroup_status,
            'inherited_from': inherited_from
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_general_settings_id10(
        self,
        node_type: str,
        node_id: str,
        airgroup_status: bool,
        inherited_from: str,
    ) -> Response:
        """Create/Update general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            airgroup_status (bool): Specifies if AirGroup service is enabled/disabled. This over-
                rides enable/disable at individual service level
            inherited_from (str): This field indicates whether this profile was explicitly
                configured at this node or inherited from a parent node

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/"

        json_data = {
            'airgroup_status': airgroup_status,
            'inherited_from': inherited_from
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_general_settings_id10(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Delete general_settings.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/general_settings/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_vlans_id17(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
    ) -> Response:
        """Retrieve disallowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/disallowed_vlans/{vlan_or_range}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_vlans_id11(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
        new_vlan_or_range: str,
    ) -> Response:
        """Create disallowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')
            new_vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/disallowed_vlans/{vlan_or_range}/"

        json_data = {
            'new_vlan_or_range': new_vlan_or_range
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_vlans_id11(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
        new_vlan_or_range: str,
    ) -> Response:
        """Create/Update disallowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')
            new_vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/disallowed_vlans/{vlan_or_range}/"

        json_data = {
            'new_vlan_or_range': new_vlan_or_range
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_vlans_id11(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
    ) -> Response:
        """Delete disallowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/disallowed_vlans/{vlan_or_range}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_vlans_id18(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve disallowed_vlans.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/disallowed_vlans/"

        return await self.get(url)

    async def airgroup_config_get_aruba_allowed_vlans_id19(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
    ) -> Response:
        """Retrieve allowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/allowed_vlans/{vlan_or_range}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_allowed_vlans_id12(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
        new_vlan_or_range: str,
    ) -> Response:
        """Create allowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')
            new_vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/allowed_vlans/{vlan_or_range}/"

        json_data = {
            'new_vlan_or_range': new_vlan_or_range
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_allowed_vlans_id12(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
        new_vlan_or_range: str,
    ) -> Response:
        """Create/Update allowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')
            new_vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/allowed_vlans/{vlan_or_range}/"

        json_data = {
            'new_vlan_or_range': new_vlan_or_range
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_allowed_vlans_id12(
        self,
        node_type: str,
        node_id: str,
        name: str,
        vlan_or_range: str,
    ) -> Response:
        """Delete allowed_vlans by identifier vlan_or_range.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            vlan_or_range (str): String representing a vlan-id or range of vlan-ids (such as
                '200-300')

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/allowed_vlans/{vlan_or_range}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_allowed_vlans_id20(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve allowed_vlans.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/allowed_vlans/"

        return await self.get(url)

    async def airgroup_config_get_aruba_vlan_restrictions_id21(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve vlan_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/"

        return await self.get(url)

    async def airgroup_config_post_aruba_vlan_restrictions_id13(
        self,
        node_type: str,
        node_id: str,
        name: str,
        disallowed_vlans: list,
        allowed_vlans: list,
    ) -> Response:
        """Create vlan_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            disallowed_vlans (list): List of disallowed VLAN IDs or range of VLAN IDs (eg '100-200'.
                This list must be if vlans are configured as part of 'allowed_vlans'.
            allowed_vlans (list): List of allowed VLAN ids or range of VLAN ids. This list must be
                empty if 'allowed_vlans' has vlans configured

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'allowed_vlans': allowed_vlans
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_vlan_restrictions_id13(
        self,
        node_type: str,
        node_id: str,
        name: str,
        disallowed_vlans: list,
        allowed_vlans: list,
    ) -> Response:
        """Create/Update vlan_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            disallowed_vlans (list): List of disallowed VLAN IDs or range of VLAN IDs (eg '100-200'.
                This list must be if vlans are configured as part of 'allowed_vlans'.
            allowed_vlans (list): List of allowed VLAN ids or range of VLAN ids. This list must be
                empty if 'allowed_vlans' has vlans configured

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/"

        json_data = {
            'disallowed_vlans': disallowed_vlans,
            'allowed_vlans': allowed_vlans
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_vlan_restrictions_id13(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Delete vlan_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/vlan_restrictions/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_roles_id22(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
    ) -> Response:
        """Retrieve disallowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/disallowed_roles/{role}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_disallowed_roles_id14(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create disallowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/disallowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_disallowed_roles_id14(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create/Update disallowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/disallowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_disallowed_roles_id14(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
    ) -> Response:
        """Delete disallowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/disallowed_roles/{role}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_disallowed_roles_id23(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve disallowed_roles.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/disallowed_roles/"

        return await self.get(url)

    async def airgroup_config_get_aruba_allowed_roles_id24(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
    ) -> Response:
        """Retrieve allowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/allowed_roles/{role}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_allowed_roles_id15(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create allowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/allowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_allowed_roles_id15(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
        new_role: str,
    ) -> Response:
        """Create/Update allowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed
            new_role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/allowed_roles/{role}/"

        json_data = {
            'new_role': new_role
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_allowed_roles_id15(
        self,
        node_type: str,
        node_id: str,
        name: str,
        role: str,
    ) -> Response:
        """Delete allowed_roles by identifier role.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            role (str): User role that needs to be disallowed

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/allowed_roles/{role}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_allowed_roles_id25(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve allowed_roles.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/allowed_roles/"

        return await self.get(url)

    async def airgroup_config_get_aruba_role_restrictions_id26(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve role_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/"

        return await self.get(url)

    async def airgroup_config_post_aruba_role_restrictions_id16(
        self,
        node_type: str,
        node_id: str,
        name: str,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create role_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            disallowed_roles (list): List of disallowed user Roles for this service. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this service. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/"

        json_data = {
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_role_restrictions_id16(
        self,
        node_type: str,
        node_id: str,
        name: str,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create/Update role_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            disallowed_roles (list): List of disallowed user Roles for this service. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this service. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/"

        json_data = {
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_role_restrictions_id16(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Delete role_restrictions.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/role_restrictions/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_services_id27(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Retrieve services by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/"

        return await self.get(url)

    async def airgroup_config_post_aruba_services_id17(
        self,
        node_type: str,
        node_id: str,
        name: str,
        new_name: str,
        inherited_from: str,
        desc: str,
        status: bool,
        server_expiry_time: int,
        is_custom: bool,
        disallowed_vlans: list,
        allowed_vlans: list,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create services by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            new_name (str): Name of the Airgroup service. This should refer to one of the pre-
                defined services or a custom-service that has been defined by user.
            inherited_from (str): This field indicates whether this profile was explicitly
                configured at this node or inherited from a parent node
            desc (str): Description of the Airgroup service. This is a read-only field
            status (bool): Indicates whether service is enabled or disabled
            server_expiry_time (int): Duration in minutes after which the records of inactive
                servers are purged. This timer will be used for all server records belonging to this
                service. Allowed range is from 60 (1 hour) to 360 (6 hours). If this is not
                configured, the records are purged as per TTL/max-age specified in packets
            is_custom (bool): Indicates whether the service is pre-defined or custom (user-defined)
                service. This is a read-only field.
            disallowed_vlans (list): List of disallowed VLAN IDs or range of VLAN IDs (eg '100-200'.
                This list must be if vlans are configured as part of 'allowed_vlans'.
            allowed_vlans (list): List of allowed VLAN ids or range of VLAN ids. This list must be
                empty if 'allowed_vlans' has vlans configured
            disallowed_roles (list): List of disallowed user Roles for this service. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this service. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/"

        json_data = {
            'new_name': new_name,
            'inherited_from': inherited_from,
            'desc': desc,
            'status': status,
            'server_expiry_time': server_expiry_time,
            'is_custom': is_custom,
            'disallowed_vlans': disallowed_vlans,
            'allowed_vlans': allowed_vlans,
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.post(url, json_data=json_data)

    async def airgroup_config_put_aruba_services_id17(
        self,
        node_type: str,
        node_id: str,
        name: str,
        new_name: str,
        inherited_from: str,
        desc: str,
        status: bool,
        server_expiry_time: int,
        is_custom: bool,
        disallowed_vlans: list,
        allowed_vlans: list,
        disallowed_roles: list,
        allowed_roles: list,
    ) -> Response:
        """Create/Update services by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.
            new_name (str): Name of the Airgroup service. This should refer to one of the pre-
                defined services or a custom-service that has been defined by user.
            inherited_from (str): This field indicates whether this profile was explicitly
                configured at this node or inherited from a parent node
            desc (str): Description of the Airgroup service. This is a read-only field
            status (bool): Indicates whether service is enabled or disabled
            server_expiry_time (int): Duration in minutes after which the records of inactive
                servers are purged. This timer will be used for all server records belonging to this
                service. Allowed range is from 60 (1 hour) to 360 (6 hours). If this is not
                configured, the records are purged as per TTL/max-age specified in packets
            is_custom (bool): Indicates whether the service is pre-defined or custom (user-defined)
                service. This is a read-only field.
            disallowed_vlans (list): List of disallowed VLAN IDs or range of VLAN IDs (eg '100-200'.
                This list must be if vlans are configured as part of 'allowed_vlans'.
            allowed_vlans (list): List of allowed VLAN ids or range of VLAN ids. This list must be
                empty if 'allowed_vlans' has vlans configured
            disallowed_roles (list): List of disallowed user Roles for this service. This must be
                empty if any roles are configured in 'allowed_roles'
            allowed_roles (list): List of allowed user Roles for this service. This must be empty if
                any roles are configured in 'disallowed_roles'

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/"

        json_data = {
            'new_name': new_name,
            'inherited_from': inherited_from,
            'desc': desc,
            'status': status,
            'server_expiry_time': server_expiry_time,
            'is_custom': is_custom,
            'disallowed_vlans': disallowed_vlans,
            'allowed_vlans': allowed_vlans,
            'disallowed_roles': disallowed_roles,
            'allowed_roles': allowed_roles
        }

        return await self.put(url, json_data=json_data)

    async def airgroup_config_delete_aruba_services_id17(
        self,
        node_type: str,
        node_id: str,
        name: str,
    ) -> Response:
        """Delete services by identifier name.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name
            name (str): Name of the Airgroup service. This should refer to one of the pre-defined
                services or a custom-service that has been defined by user.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/{name}/"

        return await self.delete(url)

    async def airgroup_config_get_aruba_services_id28(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve services.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/services/"

        return await self.get(url)

    async def airgroup_config_get_aruba_config_id29(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def airgroup_config_get_aruba_node_list_id30(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve node_list by identifier node-type node-id.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL, GROUP
            node_id (str): The identifier of the configuration node(aka group). For node-type
                GLOBAL, node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to
                the group-name

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airgroup-config/v2/node_list/{node_type}/{node_id}/"

        return await self.get(url)

    async def airmatch_config_get_aruba_system_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def airmatch_config_post_aruba_system_id1(
        self,
        node_type: str,
        node_id: str,
        schedule: bool,
        deploy_hour: int,
        quality_threshold: int,
        quality_threshold_24ghz: int,
        quality_threshold_5ghz: int,
        quality_threshold_6ghz: int,
    ) -> Response:
        """Create system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                This configuration is deprecated and will have no effect. Please use per band fields
                such as 'quality_threshold_24ghz', 'quality_threshold_5ghz' and
                'quality_threshold_6ghz'
            quality_threshold_24ghz (int): Quality threshold value for 2.4 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_5ghz (int): Quality threshold value for 5 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_6ghz (int): Quality threshold value for 6 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        json_data = {
            'schedule': schedule,
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'quality_threshold_24ghz': quality_threshold_24ghz,
            'quality_threshold_5ghz': quality_threshold_5ghz,
            'quality_threshold_6ghz': quality_threshold_6ghz
        }

        return await self.post(url, json_data=json_data)

    async def airmatch_config_put_aruba_system_id1(
        self,
        node_type: str,
        node_id: str,
        schedule: bool,
        deploy_hour: int,
        quality_threshold: int,
        quality_threshold_24ghz: int,
        quality_threshold_5ghz: int,
        quality_threshold_6ghz: int,
    ) -> Response:
        """Create/Update system.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                This configuration is deprecated and will have no effect. Please use per band fields
                such as 'quality_threshold_24ghz', 'quality_threshold_5ghz' and
                'quality_threshold_6ghz'
            quality_threshold_24ghz (int): Quality threshold value for 2.4 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_5ghz (int): Quality threshold value for 5 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_6ghz (int): Quality threshold value for 6 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/system/"

        json_data = {
            'schedule': schedule,
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'quality_threshold_24ghz': quality_threshold_24ghz,
            'quality_threshold_5ghz': quality_threshold_5ghz,
            'quality_threshold_6ghz': quality_threshold_6ghz
        }

        return await self.put(url, json_data=json_data)

    async def airmatch_config_delete_aruba_system_id1(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
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

    async def airmatch_config_get_aruba_config_id2(
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
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.get(url)

    async def airmatch_config_post_aruba_config_id2(
        self,
        node_type: str,
        node_id: str,
        schedule: bool,
        deploy_hour: int,
        quality_threshold: int,
        quality_threshold_24ghz: int,
        quality_threshold_5ghz: int,
        quality_threshold_6ghz: int,
    ) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                This configuration is deprecated and will have no effect. Please use per band fields
                such as 'quality_threshold_24ghz', 'quality_threshold_5ghz' and
                'quality_threshold_6ghz'
            quality_threshold_24ghz (int): Quality threshold value for 2.4 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_5ghz (int): Quality threshold value for 5 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_6ghz (int): Quality threshold value for 6 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'schedule': schedule,
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'quality_threshold_24ghz': quality_threshold_24ghz,
            'quality_threshold_5ghz': quality_threshold_5ghz,
            'quality_threshold_6ghz': quality_threshold_6ghz
        }

        return await self.post(url, json_data=json_data)

    async def airmatch_config_put_aruba_config_id2(
        self,
        node_type: str,
        node_id: str,
        schedule: bool,
        deploy_hour: int,
        quality_threshold: int,
        quality_threshold_24ghz: int,
        quality_threshold_5ghz: int,
        quality_threshold_6ghz: int,
    ) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            schedule (bool): Indicates whether daily Airmatch optimizations and deployments should
                occur for APs. Default: Enabled
            deploy_hour (int): Indicates Hour of Day for RF Plan Deployment. Deploy hour in AP's
                Time Zone. Range 0-23. Default: 5
            quality_threshold (int): Quality threshold value above which solutions are deployed.
                This configuration is deprecated and will have no effect. Please use per band fields
                such as 'quality_threshold_24ghz', 'quality_threshold_5ghz' and
                'quality_threshold_6ghz'
            quality_threshold_24ghz (int): Quality threshold value for 2.4 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_5ghz (int): Quality threshold value for 5 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8
            quality_threshold_6ghz (int): Quality threshold value for 6 Ghz band above which
                solutions are deployed. Range 0-100. Default: 8

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'schedule': schedule,
            'deploy_hour': deploy_hour,
            'quality_threshold': quality_threshold,
            'quality_threshold_24ghz': quality_threshold_24ghz,
            'quality_threshold_5ghz': quality_threshold_5ghz,
            'quality_threshold_6ghz': quality_threshold_6ghz
        }

        return await self.put(url, json_data=json_data)

    async def airmatch_config_delete_aruba_config_id2(
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
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/config/"

        return await self.delete(url)

    async def airmatch_config_get_aruba_node_list_id3(
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
        url = f"/airmatch-config/v1/node_list/{node_type}/{node_id}/"

        return await self.get(url)

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
        new_siem_server_name: str,
        siem_server_url: str,
        siem_index: str,
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
            new_siem_server_name (str): SIEM server name
            siem_server_url (str): SIEM server url including the port
            siem_index (str): SIEM bucket that the events have to go into
            siem_token (str): SIEM authentication token; HEC token in case of Splunk

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        json_data = {
            'new_siem_server_name': new_siem_server_name,
            'siem_server_url': siem_server_url,
            'siem_index': siem_index,
            'siem_token': siem_token
        }

        return await self.post(url, json_data=json_data)

    async def ids_ips_config_put_aruba_ips_siem_servers_list_id2(
        self,
        node_type: str,
        node_id: str,
        siem_server_name: str,
        new_siem_server_name: str,
        siem_server_url: str,
        siem_index: str,
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
            new_siem_server_name (str): SIEM server name
            siem_server_url (str): SIEM server url including the port
            siem_index (str): SIEM bucket that the events have to go into
            siem_token (str): SIEM authentication token; HEC token in case of Splunk

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/siem_servers_list/{siem_server_name}/"

        json_data = {
            'new_siem_server_name': new_siem_server_name,
            'siem_server_url': siem_server_url,
            'siem_index': siem_index,
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
        enable: bool,
        siem_servers_list: list,
    ) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            enable (bool): Enable reporting of threats to SIEM systems
            siem_servers_list (list): SIEM Server Configuration

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'enable': enable,
            'siem_servers_list': siem_servers_list
        }

        return await self.post(url, json_data=json_data)

    async def ids_ips_config_put_aruba_ips_config_id3(
        self,
        node_type: str,
        node_id: str,
        enable: bool,
        siem_servers_list: list,
    ) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected.
            enable (bool): Enable reporting of threats to SIEM systems
            siem_servers_list (list): SIEM Server Configuration

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ids-ips-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'enable': enable,
            'siem_servers_list': siem_servers_list
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
        new_range_id: str,
        start_ip: str,
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
            new_range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            start_ip (str): Starting IPv4 Address of the range.
            end_ip (str): Last IPv4 Address of the range.
            is_conflicting (bool): This is a Read-only field that indicates whether this range is
                overlapping with any other range in the config. Adding of overlapping ranges is not
                allowed. However, we can have such ranges when legacy config is migrated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        json_data = {
            'new_range_id': new_range_id,
            'start_ip': start_ip,
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
        new_range_id: str,
        start_ip: str,
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
            new_range_id (str): Identifier for each IP range in the pool. This is just a string
                identifier in form of 2 digit number that must be unique within each pool
            start_ip (str): Starting IPv4 Address of the range.
            end_ip (str): Last IPv4 Address of the range.
            is_conflicting (bool): This is a Read-only field that indicates whether this range is
                overlapping with any other range in the config. Adding of overlapping ranges is not
                allowed. However, we can have such ranges when legacy config is migrated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/ip_range/{range_id}/"

        json_data = {
            'new_range_id': new_range_id,
            'start_ip': start_ip,
            'end_ip': end_ip,
            'is_conflicting': is_conflicting
        }

        return await self.put(url, json_data=json_data)

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
        new_pool_name: str,
        pool_type: str,
        ip_range: list,
        max_clients: int,
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
            new_pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            pool_type (str): Pool Type identifying whether IP address is used as Inner-IP or is used
                as part of DHCP pool  Valid Values: INNER_IP_POOL_TYPE, DHCP_POOL_TYPE
            ip_range (list): IP Address Range. The ranges must not overlap within or across pools
            max_clients (int): Maximum number of clients that can be allocated when subnets are
                carved out from this pool. This applies only to pool that are of type
                'DHCP_POOL_TYPE'
            oldKey (str, optional): Specify old value of 'pool_name' if it needs to be replaced

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        params = {
            'oldKey': oldKey
        }

        json_data = {
            'new_pool_name': new_pool_name,
            'pool_type': pool_type,
            'ip_range': ip_range,
            'max_clients': max_clients
        }

        return await self.post(url, json_data=json_data, params=params)

    async def ipms_config_put_aruba_address_pool_id2(
        self,
        node_type: str,
        node_id: str,
        pool_name: str,
        new_pool_name: str,
        pool_type: str,
        ip_range: list,
        max_clients: int,
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
            new_pool_name (str): Name to identify an IP pool. Maximum characters allowed is 60.
            pool_type (str): Pool Type identifying whether IP address is used as Inner-IP or is used
                as part of DHCP pool  Valid Values: INNER_IP_POOL_TYPE, DHCP_POOL_TYPE
            ip_range (list): IP Address Range. The ranges must not overlap within or across pools
            max_clients (int): Maximum number of clients that can be allocated when subnets are
                carved out from this pool. This applies only to pool that are of type
                'DHCP_POOL_TYPE'
            oldKey (str, optional): Specify old value of 'pool_name' if it needs to be replaced

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ipms-config/v1/node_list/{node_type}/{node_id}/config/address_pool/{pool_name}/"

        params = {
            'oldKey': oldKey
        }

        json_data = {
            'new_pool_name': new_pool_name,
            'pool_type': pool_type,
            'ip_range': ip_range,
            'max_clients': max_clients
        }

        return await self.put(url, json_data=json_data, params=params)

    async def ipms_config_delete_aruba_address_pool_id1(
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
        node_type: str,
        node_id: str,
        profile: str,
        profile_type: str,
        cluster_redundancy_type: str,
        cluster_group_name: str,
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
        url = f"/overlay-wlan-config/v2/node_list/{node_type}/{node_id}/config/ssid_cluster/{profile}/{profile_type}/gw_cluster_list/{cluster_redundancy_type}/{cluster_group_name}/"

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

    async def sdwan_config_get_aruba_admin_status_id21(
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

    async def sdwan_config_put_aruba_hub_clusters_id6(
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

    async def sdwan_config_post_aruba_hub_clusters_id6(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
        new_cluster_group: str,
        new_cluster_name: str,
    ) -> Response:
        """Create by hub-clusters by cluster name and cluster group.

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
        """Delete by hub-clusters by cluster name and cluster group.

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
        """Retrieve by hub-clusters by cluster name and cluster group.

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

    async def sdwan_config_put_aruba_load_balance_orchestration_id18(
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

    async def sdwan_config_post_aruba_load_balance_orchestration_id18(
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

    async def sdwan_config_delete_aruba_load_balance_orchestration_id21(
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

    async def sdwan_config_get_aruba_load_balance_orchestration_id31(
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

    async def sdwan_config_get_aruba_hub_mesh_id42(
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

    async def sdwan_config_put_aruba_tunnel_policy_id22(
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

    async def sdwan_config_post_aruba_tunnel_policy_id22(
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

    async def sdwan_config_delete_aruba_tunnel_policy_id26(
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

    async def sdwan_config_get_aruba_tunnel_policy_id38(
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

    async def sdwan_config_get_aruba_hub_clusters_id19(
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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/hub-clusters/"

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

    async def sdwan_config_put_aruba_topology_id11(
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

    async def sdwan_config_post_aruba_topology_id11(
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

    async def sdwan_config_delete_aruba_topology_id13(
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

    async def sdwan_config_get_aruba_topology_id22(
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

    async def sdwan_config_put_aruba_hub_clusters_id8(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
        new_cluster_group: str,
        new_cluster_name: str,
    ) -> Response:
        """Create/Update hub-clusters by identifier cluster-name cluster-group.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/hub-clusters/{cluster_name}/{cluster_group}/"

        json_data = {
            'new_cluster_group': new_cluster_group,
            'new_cluster_name': new_cluster_name
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_hub_clusters_id8(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
        new_cluster_group: str,
        new_cluster_name: str,
    ) -> Response:
        """Create hub-clusters by identifier cluster-name cluster-group.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/hub-clusters/{cluster_name}/{cluster_group}/"

        json_data = {
            'new_cluster_group': new_cluster_group,
            'new_cluster_name': new_cluster_name
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_delete_aruba_hub_clusters_id10(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
    ) -> Response:
        """Delete hub-clusters by identifier cluster-name cluster-group.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/hub-clusters/{cluster_name}/{cluster_group}/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_hub_clusters_id18(
        self,
        node_type: str,
        node_id: str,
        cluster_name: str,
        cluster_group: str,
    ) -> Response:
        """Retrieve hub-clusters by identifier cluster-name cluster-group.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/hub-clusters/{cluster_name}/{cluster_group}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_microbranch_dc_cluster_id9(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hub_clusters: list,
    ) -> Response:
        """Create/Update microbranch-dc-cluster.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            hubs_type (str): This indicates whether DC Preference uses induvidual VPNC devices
                ('hubs' list) or VPNC Clusters ('hub-clusters' list).  Valid Values:
                HUB_TYPE_DEVICE, HUB_TYPE_CLUSTER
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/"

        json_data = {
            'hubs_type': hubs_type,
            'hub_clusters': hub_clusters
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_microbranch_dc_cluster_id9(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hub_clusters: list,
    ) -> Response:
        """Create microbranch-dc-cluster.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied. Note: This API is supported only on GROUP  Valid Values: GLOBAL, GROUP
            node_id (str): The value of the identifer for the configuration container. This value is
                interpreted according to node-type above. Invalid combinations of node-type and
                node-id will be rejected. Note: For this API, node_id must refer to a Microbranch
                group
            hubs_type (str): This indicates whether DC Preference uses induvidual VPNC devices
                ('hubs' list) or VPNC Clusters ('hub-clusters' list).  Valid Values:
                HUB_TYPE_DEVICE, HUB_TYPE_CLUSTER
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/"

        json_data = {
            'hubs_type': hubs_type,
            'hub_clusters': hub_clusters
        }

        return await self.post(url, json_data=json_data)

    async def sdwan_config_delete_aruba_microbranch_dc_cluster_id11(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Delete microbranch-dc-cluster.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/"

        return await self.delete(url)

    async def sdwan_config_get_aruba_microbranch_dc_cluster_id20(
        self,
        node_type: str,
        node_id: str,
    ) -> Response:
        """Retrieve microbranch-dc-cluster.

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
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/microbranch-dc-cluster/"

        return await self.get(url)

    async def sdwan_config_get_aruba_route_policy_id36(
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

    async def sdwan_config_put_aruba_hub_mesh_id24(
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

    async def sdwan_config_post_aruba_hub_mesh_id24(
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

    async def sdwan_config_delete_aruba_hub_mesh_id28(
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

    async def sdwan_config_get_aruba_hub_mesh_id41(
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
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/"

        return await self.get(url)

    async def sdwan_config_get_aruba_config_id44(
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

    async def sdwan_config_put_aruba_as_number_id13(
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

    async def sdwan_config_post_aruba_as_number_id13(
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

    async def sdwan_config_delete_aruba_as_number_id16(
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

    async def sdwan_config_get_aruba_as_number_id26(
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

    async def sdwan_config_put_aruba_hub_id17(
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

    async def sdwan_config_post_aruba_hub_id17(
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

    async def sdwan_config_delete_aruba_hub_id20(
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

    async def sdwan_config_get_aruba_hub_id30(
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
        search_name: str = None,
        offset: str = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve branch-mesh.

        Args:
            last_index (str, optional): Last seen index returned part of the previous query . It can
                be used instead of offset for seeking the table faster
            search_name (str, optional): Specify partial/complete string that will be used to search
                the primary-key (labels).
            offset (str, optional): Offset value from where to start lookup in the table Defaults to
                0.
            limit (int, optional): Max no.of Entries to be returned for Page. Default value is 10
                and maximum value allowed is 10 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/sdwan-config/v1/branch-mesh/"

        params = {
            'last_index': last_index,
            'search_name': search_name,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group
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
                node-id will be rejected. Note: For this API, node_id must refer to a
                BranchGateway/Microbranch group
            identifier (str): VPNC device serial-number

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/hubs/{identifier}/"

        return await self.get(url)

    async def sdwan_config_put_aruba_rekey_interval_id21(
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

    async def sdwan_config_post_aruba_rekey_interval_id21(
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

    async def sdwan_config_delete_aruba_rekey_interval_id25(
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

    async def sdwan_config_get_aruba_rekey_interval_id37(
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

    async def sdwan_config_get_aruba_hub_groups_id40(
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

    async def sdwan_config_put_aruba_best_path_computation_id16(
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

    async def sdwan_config_post_aruba_best_path_computation_id16(
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

    async def sdwan_config_delete_aruba_best_path_computation_id19(
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

    async def sdwan_config_get_aruba_best_path_computation_id29(
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

    async def sdwan_config_delete_aruba_mesh_policy_id29(
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

    async def sdwan_config_get_aruba_mesh_policy_id43(
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

    async def sdwan_config_get_aruba_network_segment_policy_id24(
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

    async def sdwan_config_put_aruba_hub_groups_id23(
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

    async def sdwan_config_post_aruba_hub_groups_id23(
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

    async def sdwan_config_delete_aruba_hub_groups_id27(
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

    async def sdwan_config_get_aruba_hub_groups_id39(
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

    async def sdwan_config_put_aruba_graceful_restart_id15(
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

    async def sdwan_config_post_aruba_graceful_restart_id15(
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

    async def sdwan_config_delete_aruba_graceful_restart_id18(
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

    async def sdwan_config_get_aruba_graceful_restart_id28(
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

    async def sdwan_config_put_aruba_network_segment_policy_id12(
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

    async def sdwan_config_post_aruba_network_segment_policy_id12(
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

    async def sdwan_config_delete_aruba_network_segment_policy_id14(
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

    async def sdwan_config_get_aruba_network_segment_policy_id23(
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

    async def sdwan_config_get_aruba_aggregates_id33(
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

    async def sdwan_config_get_aruba_branch_aggregates_id35(
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

    async def sdwan_config_put_aruba_branch_config_id7(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hubs: list,
        hub_clusters: list,
        dc_ordering_status: str,
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
                'hubs-type' is set to 'HUB_TYPE_DEVICE' under branch-config. The VPNC devices must
                be ordered such that devices belonging to same group are contiguous
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config
            dc_ordering_status (str): Read-only field to indicate if VPNCs in 'hubs' list are in
                correct order as per their Data-Center (Group) membership. VPNCs belonging to same
                group must be consecutive entries in 'hubs' list. If not, the load-balancing will
                not work as expected. The VPNCs in 'hubs' list should be re-ordered in such cases
                Valid Values: CORRECT_ORDER, INCORRECT_ORDER

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs_type': hubs_type,
            'hubs': hubs,
            'hub_clusters': hub_clusters,
            'dc_ordering_status': dc_ordering_status
        }

        return await self.put(url, json_data=json_data)

    async def sdwan_config_post_aruba_branch_config_id7(
        self,
        node_type: str,
        node_id: str,
        hubs_type: str,
        hubs: list,
        hub_clusters: list,
        dc_ordering_status: str,
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
                'hubs-type' is set to 'HUB_TYPE_DEVICE' under branch-config. The VPNC devices must
                be ordered such that devices belonging to same group are contiguous
            hub_clusters (list): An ordered list of VPNC clusters. This can be configured only if
                'hubs-type' is set to 'HUB_TYPE_CLUSTER' under branch-config
            dc_ordering_status (str): Read-only field to indicate if VPNCs in 'hubs' list are in
                correct order as per their Data-Center (Group) membership. VPNCs belonging to same
                group must be consecutive entries in 'hubs' list. If not, the load-balancing will
                not work as expected. The VPNCs in 'hubs' list should be re-ordered in such cases
                Valid Values: CORRECT_ORDER, INCORRECT_ORDER

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/sdwan-config/v1/node_list/{node_type}/{node_id}/config/branch-config/"

        json_data = {
            'hubs_type': hubs_type,
            'hubs': hubs,
            'hub_clusters': hub_clusters,
            'dc_ordering_status': dc_ordering_status
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

    async def sdwan_config_put_aruba_timer_id14(
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

    async def sdwan_config_post_aruba_timer_id14(
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

    async def sdwan_config_delete_aruba_timer_id17(
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

    async def sdwan_config_get_aruba_timer_id27(
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

    async def sdwan_config_get_aruba_node_list_id45(
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

    async def sdwan_config_put_aruba_aggregates_id19(
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

    async def sdwan_config_post_aruba_aggregates_id19(
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

    async def sdwan_config_delete_aruba_aggregates_id22(
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

    async def sdwan_config_get_aruba_aggregates_id32(
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

    async def sdwan_config_get_aruba_sdwan_global_id25(
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

    async def sdwan_config_put_aruba_branch_aggregates_id20(
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

    async def sdwan_config_post_aruba_branch_aggregates_id20(
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

    async def sdwan_config_delete_aruba_branch_aggregates_id23(
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

    async def sdwan_config_get_aruba_branch_aggregates_id34(
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
        search_name: str = None,
        offset: str = 0,
        limit: int = 100,
    ) -> Response:
        """Retrieve branch-mesh-ui.

        Args:
            last_index (str, optional): Last seen index returned part of the previous query . It can
                be used instead of offset for seeking the table faster
            search_name (str, optional): Specify partial/complete string that will be used to search
                the primary-key (labels).
            offset (str, optional): Offset value from where to start lookup in the table Defaults to
                0.
            limit (int, optional): Max no.of Entries to be returned for Page. Default value is 10
                and maximum value allowed is 10 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/sdwan-config/v1/branch-mesh-ui/"

        params = {
            'last_index': last_index,
            'search_name': search_name,
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
        voice_priority: int,
        video_priority: int,
    ) -> Response:
        """Create skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_skype4b_id1(
        self,
        node_type: str,
        node_id: str,
        voice_priority: int,
        video_priority: int,
    ) -> Response:
        """Create/Update skype4b.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/skype4b/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority
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
        new_dns_pattern: str,
        carrier_service_provider: str,
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
            new_dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.
            carrier_service_provider (str): Enter service provider name for enhanced visibility.
                Enter NA otherwise.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        json_data = {
            'new_dns_pattern': new_dns_pattern,
            'carrier_service_provider': carrier_service_provider
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_dns_patterns_id2(
        self,
        node_type: str,
        node_id: str,
        dns_pattern: str,
        new_dns_pattern: str,
        carrier_service_provider: str,
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
            new_dns_pattern (str): Configure the DNS pattern for the carrier; A maximum of 10 DNS
                patterns can be configured; This is applicable only for Wifi Calling application.
            carrier_service_provider (str): Enter service provider name for enhanced visibility.
                Enter NA otherwise.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/wifi_calling/dns_patterns/{dns_pattern}/"

        json_data = {
            'new_dns_pattern': new_dns_pattern,
            'carrier_service_provider': carrier_service_provider
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
        voice_priority: int,
        video_priority: int,
    ) -> Response:
        """Create sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of SIP application.
            video_priority (int): DSCP priority to be applied to video calls of SIP application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_sip_id4(
        self,
        node_type: str,
        node_id: str,
        voice_priority: int,
        video_priority: int,
    ) -> Response:
        """Create/Update sip.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of SIP application.
            video_priority (int): DSCP priority to be applied to video calls of SIP application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/sip/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority
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
        voice_priority: int,
        video_priority: int,
        dns_patterns: list,
    ) -> Response:
        """Create ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority,
            'dns_patterns': dns_patterns
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_ucc_alg_id5(
        self,
        node_type: str,
        node_id: str,
        voice_priority: int,
        video_priority: int,
        dns_patterns: list,
    ) -> Response:
        """Create/Update ucc_alg.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            voice_priority (int): DSCP priority to be applied to voice calls of Skype for business
                application.
            video_priority (int): DSCP priority to be applied to video calls of Skype for business
                application.
            dns_patterns (list): Wifi calling DNS patterns.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/ucc_alg/"

        json_data = {
            'voice_priority': voice_priority,
            'video_priority': video_priority,
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
        activate: bool,
        enable_call_prioritization: bool,
        voice_priority: int = 46,
        video_priority: int = 34,
    ) -> Response:
        """Create config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.
            voice_priority (int, optional): DSCP priority to be applied to voice calls of Skype for
                business application.
            video_priority (int, optional): DSCP priority to be applied to video calls of Skype for
                business application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization,
            'voice_priority': voice_priority,
            'video_priority': video_priority
        }

        return await self.post(url, json_data=json_data)

    async def ucc_config_put_aruba_config_id8(
        self,
        node_type: str,
        node_id: str,
        activate: bool,
        enable_call_prioritization: bool,
        voice_priority: int = 46,
        video_priority: int = 34,
    ) -> Response:
        """Create/Update config.

        Args:
            node_type (str): Defines the type of configuration node to which the config is being
                applied.  Valid Values: GLOBAL
            node_id (str): The identifer of the configuration node(aka group). For node-type GLOBAL,
                node-id should be 'GLOBAL'. For node-type 'GROUP', node-id should be set to the
                group-name
            activate (bool): Specifies if UCC service is to be activated.
            enable_call_prioritization (bool): Specifies if UCC call prioritization has to be
                applied; this configuration is also consumed by Device Config.
            voice_priority (int, optional): DSCP priority to be applied to voice calls of Skype for
                business application.
            video_priority (int, optional): DSCP priority to be applied to video calls of Skype for
                business application.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/ucc-config/v1/node_list/{node_type}/{node_id}/config/"

        json_data = {
            'activate': activate,
            'enable_call_prioritization': enable_call_prioritization,
            'voice_priority': voice_priority,
            'video_priority': video_priority
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
                characters. Must start with a letter or number.                           Can
                contain the following special characters: '-', ',', '?', '!', '+', '&', '@', ':',
                ';', '(', ')', '_', '.', '*'

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
                characters. Must start with a letter or number.                           Can
                contain the following special characters: '-', ',', '?', '!', '+', '&', '@', ':',
                ';', '(', ')', '_', '.', '*'

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
            'system_user': system_user
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
            'system_user': system_user
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
            current_password (str): Current Password (Password requirements are at least 8
                characters, a lowercase letter, an uppercase letter, a number, a symbol, no parts of
                your username, does not include your first name, does not include your last name.
                Your password cannot be any of your last 6 passwords.)
            new_password (str): New Password (Password requirements are at least 8 characters, a
                lowercase letter, an uppercase letter, a number, a symbol, no parts of your
                username, does not include your first name, does not include your last name. Your
                password cannot be any of your last 6 passwords.)
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
            password (str): Password (Password requirements are at least 8 characters, a lowercase
                letter, an uppercase letter, a number, a symbol, no parts of your username, does not
                include your first name, does not include your last name. Your password cannot be
                any of your last 6 passwords.)
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
        NoName: List[str] = None,
    ) -> Response:
        """Delete multiple users account. The max no of accounts that can be deleted at once is 10.

        Args:
            NoName (List[str], optional): List of user id's to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/platform/rbac/v1/bulk_users"

        return await self.delete(url)

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
            app_name (str, optional): Filter users based on app_name  Valid Values: nms,
                account_setting
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
            app_name (str): app name  Valid Values: nms, account_setting

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
            app_name (str): app name  Valid Values: nms, account_setting

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
            app_name (str): app name  Valid Values: nms, account_setting
            new_rolename (str): name of the role
            permission (str): permission for OtherApplications [Notifications and Virtual Gateway]
                ("view"/"modify"/"denied")
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
            permission (str): permission for OtherApplications [Notifications and Virtual Gateway]
                ("view"/"modify"/"denied")
            applications (list): applications
            app_name (str): app name where role needs to be created  Valid Values: nms,
                account_setting

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_visualrf_v1_campus(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """ Get list of all campuses.

        Args:
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/campus"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def get_visualrf_v1_campus(
        self,
        campus_id: str,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """ Get a specific campus and its buildings.

        Args:
            campus_id (str):  Provide campus_id returned by /visualrf_api/v1/campus api. Example:
                /visualrf_api/v1/campus/201610193176__1b99400c-f5bd-4a17-9a1c-87da89941381
            offset (int, optional): Pagination start index. Defaults to 0.
            limit (int, optional): Pagination size. Default 100  Max 100 Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/visualrf_api/v1/campus/{campus_id}"

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

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

        params = {
            'units': units,
            'offset': offset,
            'limit': limit
        }

        return await self.get(url, params=params)

    async def post_visualrf_v1_restore_sites(
        self,
        file: Union[Path, str],
    ) -> Response:
        """create floorplans using zip file (supported files are zip and .esx).

        Args:
            file (Union[Path, str]): select zip or esx file to begin import

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/restore_sites"
        file = file if isinstance(file, Path) else Path(str(file))

        return await self.post(url)

    async def get_visualrf_v1_restore_sites_status(
        self,
    ) -> Response:
        """get last import operation information.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/restore_sites/status"

        return await self.get(url)

    async def get_visualrf_v1_anonymization(
        self,
    ) -> Response:
        """Get status of anonymization.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/anonymization"

        return await self.get(url)

    async def post_visualrf_v1_anonymization(
        self,
        schedule: str = None,
    ) -> Response:
        """Enable anonymization.

        Args:
            schedule (str, optional): Anonymization schedule. Default value is NEVER  Valid Values:
                NEVER, DAILY, WEEKLY, MONTHLY

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/anonymization"

        json_data = {
            'schedule': schedule
        }

        return await self.post(url, json_data=json_data)

    async def delete_visualrf_v1_anonymization(
        self,
    ) -> Response:
        """Disable anonymization.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/visualrf_api/v1/anonymization"

        return await self.delete(url)
