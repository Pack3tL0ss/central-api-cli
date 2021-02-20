"""
This file contains API methods for:
    - airgroup
    - airmatch
    - apprf
    - client match

Auto Generated code, not all validated look for # verified
"""
import sys
import asyncio
import json
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

    async def airgroup_get_traffic_summary(self, start_time: int, end_time: int,
                                           label: str = None) -> Response:
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

    async def airgroup_get_trends(self, start_time: int, end_time: int, trend_type: str,
                                  label: str = None) -> Response:
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

    async def airgroup_get_device_summary(self) -> Response:
        """Retrieves device summary.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/devices"

        return await self.get(url)

    async def airgroup_get_label_list_by_cid(self) -> Response:
        """Retrieves list of labels.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/labels"

        return await self.get(url)

    async def airgroup_get_service_query_summary(self, start_time: int, end_time: int,
                                                 label: str = None) -> Response:
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

    async def airgroup_get_server_distribution(self, start_time: int, end_time: int,
                                               label: str = None) -> Response:
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

    async def airgroup_get_uncached_serviceid(self) -> Response:
        """Get all the uncached services encountered by AirGroup.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/uncached_services"

        return await self.get(url)

    async def airgroup_get_hostname(self) -> Response:
        """Retrieves a list of all hostnames.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/hostnames"

        return await self.get(url)

    async def airgroup_get_suppression_factor(self) -> Response:
        """Retrieves the suppression factor.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airgroup/v1/stats/suppression"

        return await self.get(url)

    async def airmatch_get_rep_radio_by_radio_mac(self, radio_mac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_rep_radio(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_ap_info_by_eth_mac(self, ap_eth_mac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_ap_info(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_nbr_pathloss_by_nbr_band(self, radio_mac: str, nbr_mac: str, band: str,
                                                    tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_nbr_pathloss(self, band: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_rf_events_by_radio_mac(self, radio_mac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_priority_rf_events_by_radio_mac(self, radio_mac: str,
                                                           tenant_id: str = None) -> Response:
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

    async def airmatch_get_history_by_radio_mac(self, radio_mac: str, band: str,
                                                tenant_id: str = None) -> Response:
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

    async def airmatch_get_radio_all_nbr_pathloss(self, radio_mac: str, band: str,
                                                  tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_static_radios(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_advanced_stat_ap(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_advanced_stat_eirp(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_advanced_stat_eirp_reason(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_advanced_stat_radio(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_adv_stat_nbr(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_rf_events(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_priority_rf_events(self, tenant_id: str = None) -> Response:
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

    async def airmatch_bootstrap(self, bootstrap_type: str, tenant_id: str = None) -> Response:
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

    async def airmatch_purge(self, purge_type: str, tenant_id: str = None) -> Response:
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

    async def airmatch_process_optimization_get_req(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_optimization_post_req(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_radio_plan_by_radio_mac(self, radio_mac: str, tenant_id: str = None,
                                                   debug: bool = None) -> Response:
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

    async def airmatch_get_all_radio_plan(self, tenant_id: str = None, band: str = None,
                                          debug: bool = None) -> Response:
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
            'band': band
        }

        return await self.get(url, params=params)

    async def airmatch_get_optimization_per_partition(self, rf_id: str, partition_id: str,
                                                      tenant_id: str = None) -> Response:
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

    async def airmatch_get_adv_state_deployment(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_tenant_svc_config_update(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_trigger_runnow(self, runnow_type: str, tenant_id: str = None) -> Response:
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

    async def airmatch_process_get_schedule(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_get_deploy_jobs(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_get_job_list(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_get_tenant_tz_deploy_hr_info(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_trigger_solver_job(self, tenant_id: str = None) -> Response:
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

    async def airmatch_update_feasibility(self, radio_mac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_radio_feas_by_radio_mac(self, radioMac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_radio_feas(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_device_config(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_device_config(self, ap_serial: str, tenant_id: str = None) -> Response:
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

    async def airmatch_set_device_config(self, ap_serial: str, device_mac: str, static_chan: int,
                                         static_pwr: int, opmodes: List[str],
                                         tenant_id: str = None, CBW20: List[int] = None,
                                         CBW40: List[int] = None) -> Response:
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

    async def airmatch_get_all_service_config(self) -> Response:
        """Returns All Device (AP) Running Configuration for all customers.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/airmatch/receiver/v1/service_config_all"

        return await self.get(url)

    async def airmatch_get_service_config(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_advanced_stat_eirp_feasible_range(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_radio_feas_by_radio_mac(self, radioMac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_all_radio_feas(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_device_config(self, ap_serial: str, tenant_id: str = None) -> Response:
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

    async def airmatch_set_device_config(self, ap_serial: str, device_mac: str, static_chan: int,
                                         static_pwr: int, opmodes: List[str],
                                         tenant_id: str = None, CBW20: List[int] = None,
                                         CBW40: List[int] = None) -> Response:
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

    async def airmatch_get_all_device_config(self, tenant_id: str = None) -> Response:
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

    async def airmatch_get_ap_info_by_serial(self, ap_serial: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_feas_radio_info(self, radioMac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_get_radio_board_limit(self, radioMac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_process_get_pending_deployments(self, tenant_id: str = None,
                                                       deploy_hour: int = None) -> Response:
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

    async def airmatch_process_triger_computation_complete(self, tenant_id: str = None) -> Response:
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

    async def airmatch_process_test_action_msg(self, mac: str, opmode: str, cbw: str, chan: int,
                                               eirp: int, tenant_id: str = None) -> Response:
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

    async def airmatch_process_test_config(self, disallow_action_msg: bool, tenant_id: str = None) -> Response:
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

    async def airmatch_process_ap_neighbors_get_req(self, apserialnum: str, tenant_id: str = None,
                                                    count: int = None, max_pathloss: int = None,
                                                    ap_mac: bool = None) -> Response:
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

    async def airmatch_process_radio_neighbors_get_req(self, radiomac: str, tenant_id: str = None) -> Response:
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

    async def airmatch_process_ap_upgrade_sampling_get_req(self, aplist: List[str],
                                                           tenant_id: str = None) -> Response:
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

    async def airmatch_process_partition_get_req(self, tenant_id: str = None, band: str = None,
                                                 ptype: str = None) -> Response:
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
            'ptype': ptype
        }

        return await self.get(url, params=params)

    async def airmatch_process_partition_post_req(self, tenant_id: str = None) -> Response:
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

    async def apprf_top_n_stats_iap_get(self, count: int = None, group: str = None,
                                        site: str = None, swarm_id: str = None,
                                        serial: str = None, macaddr: str = None,
                                        from_timestamp: int = None, to_timestamp: int = None,
                                        ssids: List[str] = None, user_role: List[str] = None,
                                        details: bool = None) -> Response:
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

    async def apprf_get_top_n_stats_v2(self, count: int = None, group: str = None,
                                       group_id: str = None, cluster_id: str = None,
                                       label_id: str = None, site: str = None,
                                       metrics: str = None, swarm_id: str = None,
                                       serial: str = None, macaddr: str = None,
                                       metric_id: str = None, from_timestamp: int = None,
                                       to_timestamp: int = None) -> Response:
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
            'group_id': group_id,
            'cluster_id': cluster_id,
            'label_id': label_id,
            'metrics': metrics,
            'metric_id': metric_id
        }

        return await self.get(url, params=params)

    async def apprf_applications_get(self, count: int = None, group: str = None,
                                     swarm_id: str = None, serial: str = None,
                                     macaddr: str = None, from_timestamp: int = None,
                                     to_timestamp: int = None, ssids: List[str] = None,
                                     user_role: List[str] = None, details: bool = None) -> Response:
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

        return await self.get(url)

    async def apprf_webcategories_get(self, count: int = None, group: str = None,
                                      swarm_id: str = None, serial: str = None,
                                      macaddr: str = None, from_timestamp: int = None,
                                      to_timestamp: int = None, ssids: List[str] = None,
                                      user_role: List[str] = None, details: bool = None) -> Response:
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

        return await self.get(url)

    async def apprf_appcategories_get(self, count: int = None, group: str = None,
                                      swarm_id: str = None, serial: str = None,
                                      macaddr: str = None, from_timestamp: int = None,
                                      to_timestamp: int = None, ssids: List[str] = None,
                                      user_role: List[str] = None, details: bool = None) -> Response:
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

        return await self.get(url)

    async def apprf_webreputations_get(self, group: str = None, swarm_id: str = None,
                                       serial: str = None, macaddr: str = None,
                                       from_timestamp: int = None, to_timestamp: int = None,
                                       ssids: List[str] = None, user_role: List[str] = None,
                                       details: bool = None) -> Response:
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

        return await self.get(url)

    async def apprf_webreputation_mapping_get(self) -> Response:
        """Gets Web Reputation id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/webreputation/id_to_name"

        return await self.get(url)

    async def apprf_application_mapping_get(self) -> Response:
        """Gets Application id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/application/id_to_name"

        return await self.get(url)

    async def apprf_appcategory_mapping_get(self) -> Response:
        """Gets Application Category id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/appcategory/id_to_name"

        return await self.get(url)

    async def apprf_webcategory_mapping_get(self) -> Response:
        """Gets Web Category id to name mapping.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/apprf/v1/metainfo/iap/webcategory/id_to_name"

        return await self.get(url)

    async def get_cm_cm_enabled_v1(self, tenant_id: str) -> Response:
        """Get the status of Client Match for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/cm-enabled/v1/{tenant_id}"

        return await self.get(url)

    async def post_cm_cm_enabled_v1(self, tenant_id: str, enable: bool) -> Response:
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

    async def get_cm_unsteerable_v1(self, tenant_id: str) -> Response:
        """Get all unsteerable entries for a tenant.

        Args:
            tenant_id (str): Tenant ID

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}"

        return await self.get(url)

    async def get_cm_unsteerable_v1(self, tenant_id: str, client_mac: str) -> Response:
        """Get the unsteerable state of a client.

        Args:
            tenant_id (str): Tenant ID
            client_mac (str): MAC address of client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}/{client_mac}"

        return await self.get(url)

    async def post_cm_unsteerable_v1(self, tenant_id: str, client_mac: str, type: str = None,
                                     duration: int = None) -> Response:
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

    async def delete_cm_unsteerable_v1(self, tenant_id: str, client_mac: str) -> Response:
        """Delete the unsteerable state of a client.

        Args:
            tenant_id (str): Tenant ID
            client_mac (str): MAC address of client

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/cm-api/unsteerable/v1/{tenant_id}/{client_mac}"

        return await self.delete(url)
