from __future__ import annotations

import base64
import json
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List

from ... import config, constants, log, utils
from ...client import BatchRequest
from ...exceptions import CentralCliException
from ...response import BatchResponse, Response

if TYPE_CHECKING:
    from centralcli.client import Session
    from centralcli.typedefs import CertFormat, DynamicAntenna, RadioType


DEFAULT_ACCESS_RULES = {
    "ALLOW_ALL": [
        {
            "action": "allow",
            "eport": "any",
            "ipaddr": "any",
            "match": "match",
            "netmask": "any",
            "protocol": "any",
            "service_name": "",
            "service_type": "network",
            "sport": "any",
            "throttle_downstream": "",
            "throttle_upstream": ""
        }
    ],
}

class ConfigAPI:
    def __init__(self, session: Session):
        self.session = session

    # >>>> GROUPS <<<<

    async def get_group_names(self) -> Response:
        """Get a listing of all group names defined in Aruba Central

        Returns:
            Response: CentralAPI Respose object
                output attribute will be List[str]
        """
        url = "/configuration/v2/groups"
        params = {"offset": 0, "limit": 100}  # 100 is the max
        resp = await self.session.get(url, params=params,)
        if resp.ok:
            # convert list of single item lists to a single list, remove unprovisioned group, move default group to front of list.
            resp.output = [g for _ in resp.output for g in _ if g != "unprovisioned"]
            if "default" in resp.output:  # pragma: no cover  should always be there, but still want the check given we don't control the data
                resp.output.insert(0, resp.output.pop(resp.output.index("default")))

        return resp

    async def get_all_groups(self) -> Response:
        """Get properties and template info for all groups

        This method will first call configuration/v2/groups to get a list of group names.

        It then combines the responses from /configuration/v2/groups/template_info
        and /configuration/v1/groups/properties to get the template details
        (template_group or not) and properties for each group.

        The template_info and properties endpoints both allow 20 groups per request.
        Multiple requests will be performed async if there are more than 20 groups.

        Raises:
            CentralCliException: Raised when validation of combined responses fails.

        Returns:
            Response: centralcli Response Object
        """
        resp = await self.get_group_names()
        if not resp.ok:
            return resp

        groups = resp.output
        groups_with_comma_in_name = list(filter(lambda g: "," in g, groups))
        if groups_with_comma_in_name:
            log.error(f"Ignoring group(s): {'|'.join(groups_with_comma_in_name)}.  Group APIs do not support groups with commas in name", show=True, caption=True, log=True)
            _ = [groups.pop(groups.index(g)) for g in groups_with_comma_in_name]

        batch_resp = await self.session._batch_request(
            [
                BatchRequest(self.get_groups_template_status, groups),
                BatchRequest(self.get_groups_properties, groups)
            ]
        )
        failed = [r for r in batch_resp if not r.ok]
        if failed:
            log.error(f"{len(failed)} API calls necessary to fetch group details failed.  See logs for more details.", caption=True)
            return failed[-1]

        template_resp, props_resp = batch_resp

        template_by_group = {d["group"]: d["template_details"] for d in deepcopy(template_resp.output)}
        props_by_group = {d["group"]: d["properties"] for d in deepcopy(props_resp.output)}

        combined = {tg: {"properties": pv, "template_details": tv} for (tg, tv), (pg, pv) in zip(template_by_group.items(), props_by_group.items()) if pg == tg}
        if len(set([len(combined), len(template_by_group), len(props_by_group)])) > 1:  # pragma: no cover
            raise CentralCliException("Unexpected error in get_all_groups, length of responses differs.")

        combined_resp = Response(props_resp._response, elapsed=max([r.elapsed for r in batch_resp]))
        combined_resp.output = [{"group": k, **v} for k, v in combined.items()]
        combined_resp.raw = {"properties": props_resp.raw, "template_info": template_resp.raw}

        return combined_resp

    async def get_groups_properties(self, groups: str | List[str] = None) -> Response:
        """Get properties set for groups.

        // Used by show groups when -v flag is provided //

        Args:
            groups (List[str], optional): Group list to fetch properties.
                Will fetch all if no groups provided.
                Maximum 20 comma separated group names allowed.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/properties"

        # Central API method doesn't actually take a list it takes a string with
        # group names separated by comma (NO SPACES)
        if groups is None:
            resp = await self.get_group_names()
            if not resp.ok:
                return resp
            else:
                groups = resp.output

        batch_reqs = []
        for _groups in utils.chunker(utils.listify(groups), 20):  # This call allows a max of 20
            params = {"groups": ",".join(_groups)}
            batch_reqs += [BatchRequest(self.session.get, url, params=params)]
        batch_resp = await self.session._batch_request(batch_reqs)
        failed = [r for r in batch_resp if not r.ok]
        passed = batch_resp if not failed else [r for r in batch_resp if r.ok]
        if failed:
            log.error(f"{len(failed)} of {len(batch_reqs)} API requests to {url} have failed.", show=True, caption=True)
            fail_msgs = list(set([r.output if isinstance(r.output, str) else r.output.get("description", str(r.output)) for r in failed]))
            for msg in fail_msgs:
                log.error(f"Failure description: {msg}", show=True, caption=True)

        # TODO method to combine raw and output attrs of all responses into last resp
        output = [r for res in passed for r in res.output]
        resp = batch_resp[-1] if not passed else passed[-1]
        resp.output = output
        if "data" in resp.raw:
            resp.raw["data"] = output
        elif passed:  # pragma: no cover
            log.warning("raw attr in resp from get_groups_properties lacks expected outer key 'data'", show=True)

        return resp

    async def create_group(
        self,
        group: str,
        allowed_types: constants.LibAllDevTypes | List[constants.LibAllDevTypes] = ["ap", "gw", "cx", "sw"],
        wired_tg: bool = False,
        wlan_tg: bool = False,
        aos10: bool = False,
        microbranch: bool = False,
        gw_role: constants.BranchGwRoleTypes = None,
        monitor_only_sw: bool = False,
        monitor_only_cx: bool = False,
        cnx: bool = False,
    ) -> Response:
        """Create new group with specified properties. v3

        Args:
            group (str): Group Name
            allowed_types (str, List[str]): Allowed Device Types in the group. Tabs for devices not allowed
                won't display in UI.  valid values "ap", "gw", "cx", "sw", "switch", "sdwan"
                ("switch" is generic, will enable both cx and sw)
                When sdwan (EdgeConnect SD-WAN) is allowed, it has to be the only type allowed.
            wired_tg (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            wlan_tg (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.
            aos10: (bool): if True use AOS10 architecture for the access points and gateways in the group.
                default False (Instant)
            microbranch (bool): True to enable Microbranch network role for APs is applicable only for AOS10 architecture.
            gw_role (GatewayRole): Gateway role valid values "branch", "vpnc", "wlan" ("wlan" only valid on AOS10 group)
                Defaults to None.  Results in "branch" unless "sdwan" is in allowed_types otherwise "vpnc".
            monitor_only_sw: Monitor only ArubaOS-SW switches, applies to UI group only
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only
            cnx (bool, optional): Make group compatible with cnx (New Central)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v3/groups"

        gw_role_dict = {
            "branch": "BranchGateway",
            "vpnc": "VPNConcentrator",
            "wlan": "WLANGateway",
            "sdwan": "VPNConcentrator"
        }
        dev_type_dict = {
            "ap": "AccessPoints",
            "gw": "Gateways",
            "switch": "Switches",
            "cx": "Switches",
            "sw": "Switches",
            "sdwan": "SD_WAN_Gateway",
        }

        gw_role = gw_role_dict.get(gw_role, "BranchGateway")

        allowed_types = utils.listify(allowed_types)
        allowed_switch_types = []
        if "switch" in allowed_types or ("cx" in allowed_types and "sw" in allowed_types):
            allowed_switch_types += ["AOS_CX", "AOS_S"]
        if "sw" in allowed_types and "AOS_S" not in allowed_switch_types:
            allowed_switch_types += ["AOS_S"]
        if "cx" in allowed_types and "AOS_CX" not in allowed_switch_types:
            allowed_switch_types += ["AOS_CX"]

        mon_only_switches = []
        if monitor_only_sw:
            mon_only_switches += ["AOS_S"]
        if monitor_only_cx:
            mon_only_switches += ["AOS_CX"]

        allowed_types = list(set([dev_type_dict.get(t) for t in allowed_types]))

        if mon_only_switches and "Switches" not in allowed_types:
            log.warning("ignoring monitor only switch setting as no switches were specified as being allowed in group", show=True)

        if None in allowed_types:
            raise ValueError('Invalid device type for allowed_types valid values: "ap", "gw", "sw", "cx", "switch", "sdwan')
        elif "SD_WAN_Gateway" in allowed_types and len(allowed_types) > 1:
            raise ValueError('Invalid value for allowed_types.  When sdwan device type is allowed, it must be the only type allowed for the group')
        if microbranch:
            if not aos10:
                raise ValueError("Invalid combination, Group must be configured as AOS10 group to support Microbranch")
            if "Gateways" in allowed_types:
                raise ValueError("Gateways cannot be present in a group with microbranch network role set for Access points")
        if wired_tg and (monitor_only_sw or monitor_only_cx):
            raise ValueError("Invalid combination, Monitor Only is not valid for Template Group")

        json_data = {
            "group": group,
            "group_attributes": {
                "template_info": {
                    "Wired": wired_tg,
                    "Wireless": wlan_tg
                },
                "group_properties": {
                    "AllowedDevTypes": allowed_types,
                    "NewCentral": cnx,
                }
            }
        }
        if "SD_WAN_Gateway" in allowed_types:
            # SD_WAN_Gateway requires Architecture and GwNetworkRole (VPNConcentrator)
            json_data["group_attributes"]["group_properties"]["GwNetworkRole"] = "VPNConcentrator"
            json_data["group_attributes"]["group_properties"]["Architecture"] = "SD_WAN_Gateway"
        elif "Gateways" in allowed_types:
            json_data["group_attributes"]["group_properties"]["GwNetworkRole"] = gw_role
            json_data["group_attributes"]["group_properties"]["Architecture"] = \
                "Instant" if not aos10 else "AOS10"
        if "AccessPoints" in allowed_types:
            json_data["group_attributes"]["group_properties"]["ApNetworkRole"] = \
                "Standard" if not microbranch else "Microbranch"
            json_data["group_attributes"]["group_properties"]["Architecture"] = \
                "Instant" if not aos10 else "AOS10"
        if "Switches" in allowed_types:
            json_data["group_attributes"]["group_properties"]["AllowedSwitchTypes"] = \
                allowed_switch_types
            if mon_only_switches:
                json_data["group_attributes"]["group_properties"]["MonitorOnly"] = \
                    mon_only_switches

        return await self.session.post(url, json_data=json_data)

    async def clone_group(
        self,
        clone_group: str,
        new_group: str,
        upgrade_aos10: bool = False,
    ) -> Response:
        """Clone and create new group.

        Args:
            clone_group (str): Group to be cloned.
            new_group (str): Name of group to be created based on clone.
            upgrade_aos10 (bool): Set True to Update the new cloned group to AOS10.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v2/groups/clone"

        if upgrade_aos10:
            log.warning(
                "Group may not be upgraded to AOS10, API method appears to have some caveats... Doesn't always work."
            )

        json_data = {
            'group': new_group,
            'clone_group': clone_group,
            'upgrade_architecture': upgrade_aos10,
        }

        return await self.session.post(url, json_data=json_data)

    # API-FLAW add ap and gw to group with gw-role as wlan and upgrade to aos10.  Returns 200, but no changes made
    # TODO need to add flag for SD_WAN_Gateway architecture (Silver Peak), only valid associated GwNetworkRole is VPNConcentrator
    # TODO need to add SD_WAN_Gateway to AllowedDevTypes
    async def update_group_properties(
        self,
        group: str,
        allowed_types: constants.AllDevTypes | List[constants.AllDevTypes] = None,
        wired_tg: bool = None,
        wlan_tg: bool = None,
        aos10: bool = None,
        microbranch: bool = None,
        gw_role: constants.GatewayRole = None,
        monitor_only_sw: bool = None,
        monitor_only_cx: bool = None,
    ) -> Response:
        """Update properties for the given group.

        // Used by update group //

        - The update of persona and configuration mode set for existing device types is not permitted.
        - Can update from standard AP to MicroBranch, but can't go back
        - Can update to AOS10, but can't go back
        - Can Add Allowed Device Types, but can't remove.
        - Can Add Allowed Switch Types, but can't remove.
        - Can only change mon_only_sw and wired_tg when adding switches (cx, sw) to allowed_device_types


        Args:
            group (str): Group Name
            allowed_types (str, List[str]): Allowed Device Types in the group. Tabs for devices not allowed
                won't display in UI.  valid values "ap", "gw", "cx", "sw", "switch"
                ("switch" is generic, will enable both cx and sw)
            wired_tg (bool, optional): Set to true if wired(Switch) configuration in a group is managed
                using templates.
            wlan_tg (bool, optional): Set to true if wireless(IAP, Gateways) configuration in a
                group is managed using templates.
            aos10: (bool): if True use AOS10 architecture for the access points and gateways in the group.
                default False (Instant)
            microbranch (bool): True to enable Microbranch network role for APs is applicable only for AOS10 architecture.
            gw_role (GatewayRole): Gateway role valid values "branch", "vpnc", "wlan" ("wlan" only valid on AOS10 group)
            monitor_only_sw: Monitor only ArubaOS-SW switches, applies to UI group only
            monitor_only_cx: Monitor only ArubaOS-CX switches, applies to UI group only

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/groups/{group}/properties"

        resp = await self.get_groups_properties(group)
        if not resp:
            log.error(f"Unable to perform call to update group {group} properties.  Call to get current properties failed.", caption=True)
            return resp

        cur_group_props = resp.output[-1]["properties"]

        if aos10 is False and (cur_group_props.get("AOSVersion", "") == "AOS_10X"):
            return Response(
                error=f"{group} is currently an AOS10 group.  Upgrading to AOS10 is supported, reverting back is not.",
            )
        if aos10 is True:
            if "AccessPoints" in cur_group_props["AllowedDevTypes"] or \
                "Gateways" in cur_group_props["AllowedDevTypes"]:
                resp.output = f"This call fetched current properties for group {group}"
                return [
                    resp,
                    Response(
                        error=f"{utils.color('AOS10')} can only be set when APs or GWs are initially added as allowed device types for the group"
                        f"\n{utils.color(group)} can be cloned with option to upgrade during clone.",
                    )
                ]

        if "AccessPoints" in cur_group_props["AllowedDevTypes"]:
            if microbranch is not None:
                resp.output = f"This call fetched current properties for group {group}"
                return [
                    resp,
                    Response(
                        error=f"{group} already allows APs.  Microbranch/Standard AP can only be set "
                        "when initially adding APs to allowed_types of group",
                    )
                ]
        if monitor_only_sw is not None and "AOS_S" in cur_group_props["AllowedSwitchTypes"]:
            resp.output = f"This call fetched current properties for group {group}"
            return [
                resp,
                Response(
                    error=f"{group} already allows AOS-SW.  Monitor Only can only be set "
                    "when initially adding AOS-SW to allowed_types of group",
                )
            ]
        if monitor_only_cx is not None and "AOS_CX" in cur_group_props["AllowedSwitchTypes"]:
            resp.output = f"This call fetched current properties for group {group}"
            return [
                Response(
                    error=f"{group} already allows AOS-CX.  Monitor Only can only be set "
                    "when initially adding AOS-CX to allowed_types of group",
                )
            ]
        allowed_types = allowed_types or []
        allowed_switch_types = []
        if allowed_types:
            allowed_types = utils.listify(allowed_types)
            if "switch" in allowed_types or ("cx" in allowed_types and "sw" in allowed_types):
                allowed_switch_types += ["AOS_CX", "AOS_S"]
            elif "sw" in allowed_types:
                allowed_switch_types += ["AOS_S"]
            elif "cx" in allowed_types:
                allowed_switch_types += ["AOS_CX"]

        # TODO copy paste from create group ... common func to build payload
        gw_role_dict = {
            "branch": "BranchGateway",
            "vpnc": "VPNConcentrator",
            "wlan": "WLANGateway",
        }
        dev_type_dict = {
            "ap": "AccessPoints",
            "gw": "Gateways",
            "switch": "Switches",
            "cx": "Switches",
            "sw": "Switches",
        }
        gw_role = gw_role_dict.get(gw_role)

        mon_only_switches = []
        if monitor_only_sw:
            mon_only_switches += ["AOS_S"]
        if monitor_only_cx:
            mon_only_switches += ["AOS_CX"]

        arch = None
        if "ap" in allowed_types:
            arch = "AOS10" if aos10 else "Instant"

        allowed_types = list(set([dev_type_dict.get(t) for t in allowed_types]))
        combined_allowed = [*allowed_types, *cur_group_props["AllowedDevTypes"]]

        fail_resp = None
        if None in allowed_types:
            fail_resp = Response(
                error='Invalid device type for allowed_types valid values: "ap", "gw", "sw", "cx", "switch"',
            )
        elif microbranch and not aos10:
            fail_resp = Response(
                error="Invalid combination, Group must be configured as AOS10 group to support Microbranch",
            )
        elif microbranch and "AccessPoints" not in combined_allowed:
            fail_resp = Response(
                error=f"Invalid combination, {utils.color('Microbranch')} "
                      f"can not be enabled in group {utils.color(group)}.  "
                      "APs must be added to allowed devices.\n"
                      f"[reset]Current Allowed Devices: {utils.color(combined_allowed)}",
            )
        elif wired_tg and mon_only_switches:
            fail_resp = Response(
                error="Invalid combination, Monitor Only is not valid for Template Group",
            )

        if fail_resp is not None:
            fail_resp.rl = resp.rl
            return fail_resp

        grp_props = {
            "AllowedDevTypes": combined_allowed,
            "Architecture": arch or cur_group_props.get("Architecture"),
            "AllowedSwitchTypes": allowed_switch_types or cur_group_props.get("AllowedSwitchTypes", []),
            "MonitorOnly": mon_only_switches or cur_group_props.get("MonitorOnlySwitch")
        }
        grp_props = {k: v for k, v in grp_props.items() if v}

        if gw_role and "Gateways" in allowed_types:
            grp_props["GwNetworkRole"] = gw_role
        if "AccessPoints" in allowed_types or "AccessPoints" in cur_group_props["AllowedDevTypes"]:
            grp_props["ApNetworkRole"] = "Microbranch" if microbranch else (cur_group_props.get("ApNetworkRole") or "Standard")

        tmplt_info = {
            "Wired": wired_tg,
            "Wireless": wlan_tg
        }
        tmplt_info = utils.strip_none(tmplt_info)

        grp_attrs = {}
        if tmplt_info:
            grp_attrs["template_info"] = tmplt_info
        if grp_props:
            grp_attrs["group_properties"] = {
                **{k: v for k, v in cur_group_props.items() if k not in ["AOSVersion", "MonitorOnly"]},
                **grp_props
            }
        json_data = grp_attrs

        if config.debugv:
            print(f"[DEBUG] ---- Sending the following to {url}")
            utils.json_print(json_data)
            print("[DEBUG] ----")

        return await self.session.patch(url, json_data=json_data)

    async def update_group_name(self, group: str, new_group: str) -> Response:
        """Update group name for the given group.

        Args:
            group (str): Group for which name need to be updated.
            new_group (str): The new name of the group.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/name"

        json_data = {
            'group': new_group
        }

        return await self.session.patch(url, json_data=json_data)

    # TODO accept List of str and batch delete
    async def delete_group(self, group: str) -> Response:
        """Delete existing group.

        Args:
            group (str): Name of the group that needs to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}"

        return await self.session.delete(url)

    async def move_devices_to_group(
        self,
        group: str,
        serials: str | List[str],
        *,
        cx_retain_config: bool = True,  # TODO can we send this attribute even if it's not CX, will it ignore or error
    ) -> Response:
        """Move devices to a group.

        Args:
            group (str): Group Name to move device to.
            serials (str | List[str]): Serial numbers of devices to be added to group.

        Returns:
            Response: CentralAPI Response object
        """
        # API-FLAW report flawed API method
        # Returns 500 status code when result is essentially success
        # Please Confirm: move Aruba9004_81_E8_FA & PommoreGW1 to group WLNET? [y/N]: y
        # ✖ Sending Data [configuration/v1/devices/move]
        # status code: 500 <-- 500 on success.  At least for gw would need to double check others.
        # description:
        # Controller/Gateway group move has been initiated, please check audit trail for details
        # error_code: 0001
        # service_name: Configuration
        url = "/configuration/v1/devices/move"
        serials = utils.listify(serials)

        json_data = {
            'group': group,
            'serials': serials
        }

        if cx_retain_config:
            json_data["preserve_config_overrides"] = ["AOS_CX"]

        resp = await self.session.post(url, json_data=json_data)

        # This method returns status 500 with msg that move is initiated on success.
        if not resp and resp.status == 500:
            match_str = "group move has been initiated, please check audit trail for details"
            if match_str in resp.output.get("description", ""):
                resp._ok = True

        return resp

    async def get_default_group(self,) -> Response:
        """Get default group.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/groups/default_group"

        return await self.session.get(url)

    async def preprovision_device_to_group(
        self,
        group: str,
        serials: str | List[str],
        tenant_id: str = None,
    ) -> Response:
        """Pre Provision devices to group.

        Args:
            group (str): Group name
            serials (str | List[str]): serial numbers
            tenant_id (str): Tenant id, (only applicable with MSP mode)

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/preassign"

        json_data = {
            'device_id': utils.listify(serials),
            'group_name': group,
        }

        if tenant_id is not None:  # pragma: no cover  MSP only
            json_data["tenant_id"] = str(tenant_id)

        return await self.session.post(url, json_data=json_data)

    async def get_groups_template_status(self, groups: List[str] | str = None) -> Response:
        """Get template group status for provided groups or all if none are provided.  (if it is a template group or not)

        Will return response from /configuration/v2/groups/template_info endpoint.
        If no groups are provided /configuration/v2/groups is first called to get a list of all group names.

        Args:
            groups (List[str] | str, optional): A single group or list of groups. Defaults to None (all groups).

        Returns:
            Response: centralcli Response Object
        """
        url = "/configuration/v2/groups/template_info"

        if isinstance(groups, str):
            groups = [groups]

        if not groups:
            resp = await self.get_group_names()
            if not resp.ok:
                return resp
            groups: List[str] = resp.output

        batch_reqs = []
        for chunk in utils.chunker(groups, 20):  # This call allows a max of 20
            params = {"groups": ",".join(chunk)}
            batch_reqs += [BatchRequest(self.session.get, url, params=params)]

        batch_resp = await self.session._batch_request(batch_reqs)
        failed = [r for r in batch_resp if not r.ok]
        passed = batch_resp if not failed else [r for r in batch_resp if r.ok]
        if failed:
            log.error(f"{len(failed)} of {len(batch_reqs)} API requests to {url} have failed.", show=True, caption=True)
            fail_msgs = list(set([r.output if isinstance(r.output, str) else r.output.get("description", str(r.output)) for r in failed]))
            for msg in fail_msgs:
                log.error(f"Failure description: {msg}", show=True, caption=True)

        output = [r for res in passed for r in res.output]
        resp = batch_resp[-1] if not passed else passed[-1]
        resp.output = output
        if "data" in resp.raw:
            resp.raw["data"] = output
        else:
            log.warning("raw attr in resp from get_all_groups lacks expected outer key 'data'")

        return resp

    # >>>> TEMPLATES <<<<

    async def get_all_templates(
        self,
        groups: List[dict] | List[str] = None,
        template: str = None,
        device_type: constants.DeviceTypes = None,
        version: str = None,
        model: str = None,
        query: str = None,
    ) -> Response:
        """Get data for all defined templates from Aruba Central

        Args:
            groups (List[dict] | List[str], optional): List of groups.  If provided additional API
                calls to get group names for all template groups are not performed).
                If a list of str (group names) is provided all are queried for templates
                If a list of dicts is provided:  It should look like: [{"name": "group_name", "wired_tg": True, "wlan_tg": False}]
                Defaults to None.
            template (str, optional): Filter on provided name as template.
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Filter on device_type.  Valid Values: ap|gw|cx|sw.
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: ALL, 2920, J9727A etc.
            query (str, optional): Search for template OR version OR model, query will be ignored if any of
                filter parameters are provided.

        Returns:
            Response: centralcli Response Object
        """
        if not groups:
            resp = await self.get_groups_template_status()
            if not resp:
                return resp

            template_groups = [g["group"] for g in resp.output if True in g["template_details"].values()]
        elif isinstance(groups, list) and all([isinstance(g, str) for g in groups]):
            template_groups = groups
        else:
            template_groups = [g["name"] for g in groups if True in [g["wired_tg"], g["wlan_tg"]]]

        if not template_groups:
            return Response(
                url="No call performed",
                ok=True,
                output=[],
                raw=[],
                error="None of the configured groups are Template Groups.",
            )

        params = {
            'name': template,
            'device_type': device_type,
            'version': version,
            'model': model,
            'query': query,
        }

        reqs = [BatchRequest(self.get_all_templates_in_group, group, **params) for group in template_groups]
        # TODO maybe call the aggregator from _bath_request
        responses = await self.session._batch_request(reqs)
        failed = [r for r in responses if not r]
        if failed:
            return failed[-1]

        # combine result for all calls into 1
        # TODO aggregator Response object for multi response
        # maybe add property to Response that returns dict being done with dict comp below
        all_output = [rr for r in responses for rr in r.output]
        all_raw = {
            f"[{r.error}] {r.method} {r.url.path if not int(r.url.query.get('offset', 0)) else r.url.path_qs}": r.raw
            for r in responses
        }
        responses[-1].output = all_output
        responses[-1].raw = all_raw

        return responses[-1]

    async def get_template(
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

        return await self.session.get(url)

    async def get_template_details_for_device(self, serial: str, details: bool = False) -> Response:
        """Get configuration details for a device (only for template groups).

        Args:
            serial (str): Serial number of the device.
            details (bool, optional): Usually pass false to get only the summary of a device's
                configuration status.
                Pass true only if detailed response of a device's configuration status is required.
                Passing true might result in slower API response and performance effect
                comparatively.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/config_details"
        headers = {"Accept": "multipart/form-data"}
        params = {"details": str(details)}
        return await self.session.get(url, params=params, headers=headers)

    async def get_all_templates_in_group(
        self,
        group: str,
        name: str = None,
        device_type: constants.DeviceTypes = None,
        version: str = None,
        model: str = None,
        query: str = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Response:
        """Get all templates in group.

        Args:
            group (str): Name of the group for which the templates are being queried.
            template (str, optional): Filter on provided name as template.
            device_type (Literal['ap', 'gw', 'cx', 'sw'], optional): Filter on device_type.  Valid Values: ap|gw|cx|sw.
            version (str, optional): Filter on version property of template.
                Example: ALL, 6.5.4 etc.
            model (str, optional): Filter on model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model
                parameter.
                Example: ALL, 2920, J9727A etc.
            query (str, optional): Search for template OR version OR model, query will be ignored if any of
                filter parameters are provided.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of template records to be returned. Max 20. Defaults to
                20.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        if device_type:
            device_type = constants.lib_to_api(device_type, "template")

        params = {
            'template': name,
            'device_type': device_type,
            'version': version,
            'model': model,
            'q': query,
            'offset': offset,
            'limit': limit  # max 20
        }

        return await self.session.get(url, params=params)

    # FIXME # TODO # What the Absolute F?!  not able to send template as formdata properly with aiohttp
    #       requests module works, but no luck after hours messing with form-data in aiohttp
    async def add_template(
        self,
        name: str,
        group: str,
        template: Path | str | bytes,
        device_type: constants.DeviceTypes = constants.DevTypes.ap,
        version: str = "ALL",
        model: str = "ALL",
    ) -> Response:
        """Create new template.

        Args:
            name (str): Name of template.
            group (str): Name of the group for which the template is to be created.
            template (Path | str | bytes): Template File or encoded template content.
                For sw (AOS-Switch) device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.
                2. aruba-central url https://<URL | IP>/ws.
            device_type (str): Device type of the template.  Valid Values: ap, sw, cx, gw
                Defaults to ap.
            version (str): Firmware version property of template.
                Example: ALL, 6.5.4 etc.
            model (str): Model property of template.
                For sw (AOS-Switch) device_type, part number (J number) can be used for the model
                parameter. Example: 2920, J9727A, etc.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"
        if isinstance(template, bytes):
            files = {'template': ('template.txt', template)}
        else:
            template = template if isinstance(template, Path) else Path(str(template))
            if not template.exists():
                raise FileNotFoundError(f"{str(template)} File Not Found")

            files = {'template': ('template.txt', template.read_bytes())}


        device_type = device_type if not hasattr(device_type, "value") else device_type.value
        device_type = constants.lib_to_api(device_type, "template")

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        form_data = utils.build_multipart_form_data(url, files=files, params=params, base_url=self.session.base_url)
        return await self.session.post(url, **form_data)

    async def update_existing_template(
        self,
        group: str,
        name: str,
        payload: str = None,
        template: Path | str | bytes = None,
        device_type: constants.DeviceTypes = "ap",
        version: str = "ALL",
        model: str = "ALL",
    ) -> Response:
        """Update existing template.

        Args:
            group (str): Name of the group for which the template is to be updated.
            name (str): Name of template.
            device_type (str, optional): Device type of the template.
                Valid Values: ap, sw (ArubaOS-SW), cx (ArubaOS-CX), gw (controllers/gateways)
            version (str, optional): Firmware version property of template.
                Example: ALL, 6.5.4 etc.  Defaults to "ALL".
            model (str, optional): Model property of template.
                For 'ArubaSwitch' device_type, part number (J number) can be used for the model.
                Example: 2920, J9727A etc.  Defaults to "ALL".
            template (Path | str | bytes, optional): Template text.
                For 'ArubaSwitch' device_type, the template text should include the following
                commands to maintain connection with central.
                1. aruba-central enable.
                2. aruba-central url https://<URL | IP>/ws.
            payload (str, optional): template data passed as str.
                One of template or payload is required.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/groups/{group}/templates"

        if device_type:
            device_type = constants.lib_to_api(device_type, "template")

        params = {
            'name': name,
            'device_type': device_type,
            'version': version,
            'model': model
        }

        if template:
            template = template if isinstance(template, Path) else Path(str(template))
            if not template.exists():
                raise FileNotFoundError(f"{str(template)} Not found.")
            elif not template.stat().st_size > 0:
                raise ValueError(f"{str(template)} appears to lack any content.")
            template_data: bytes = template.read_bytes()
        elif payload:
            payload = payload if isinstance(payload, bytes) else payload.encode("utf-8")
            template_data: bytes = payload
        else:
            raise ValueError("One of template or payload is required")

        files = {'template': ('template.txt', template_data)}

        form_data = utils.build_multipart_form_data(url, "PATCH", files=files, params=params, base_url=self.session.base_url)
        return await self.session.patch(url, **form_data)

    async def delete_template(
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

        return await self.session.delete(url)

    async def get_variablised_template(self, serial: str) -> Response:
        """Get variablised template for an Aruba Switch.

        Args:
            serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/variablised_template"

        return await self.session.get(url)

    # >>>> VARIABLES <<<<

    async def get_variables(
            self,
            serial: str = None,
            offset: int = 0,
            limit: int = 20,
        ) -> Response:
        """Get template variables for a device or all devices

        Args:
            serial (str): Serial number of the device, If None provided all templates for all devices
                will be fetched.  Defaults to None.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of records to be returned. Max allowed is 20. Defaults to 20.

        offset and limit are ignored if serial is provided.

        Returns:
            Response: CentralAPI Response object
        """
        if serial and serial != "all":
            url = f"/configuration/v1/devices/{serial}/template_variables"
            params = {}
        else:
            url = "/configuration/v1/devices/template_variables"
            params = {"offset": offset, "limit": limit}

        return await self.session.get(url, params=params)

    async def create_device_template_variables(
        self,
        serial: str,
        mac: str,
        var_dict: dict,
    ) -> Response:
        """Create template variables for a device.

        Args:
            serial (str): Serial number of the device.
            mac (str): MAC address of the device.
            var_dict (dict): dict with variables to be updated

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/template_variables"

        var_dict = {k: v for k, v in var_dict.items() if k not in ["_sys_serial", "_sys_lan_mac"]}
        _mac = utils.Mac(mac)

        json_data = {
            'total': len(var_dict) + 2,
            "variables": {
                **{
                    '_sys_serial': serial,
                    '_sys_lan_mac': _mac.cols,
                },
                **var_dict
            }
        }

        return await self.session.post(url, json_data=json_data)


    async def update_device_template_variables(
        self,
        serial: str,
        mac: str,
        var_dict: dict,
        *,
        replace: bool = False
    ) -> Response:
        """Update template variables for a device.

        Args:
            serial (str): Serial number of the device.
            mac (str): MAC address of the device.
            var_dict (dict): dict with variables to be updated
            replace: (bool, optional): Replace all existing variables for the device with the payload provided
                defaults to False.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/template_variables"
        var_dict = {k: v for k, v in var_dict.items() if k not in ["_sys_serial", "_sys_lan_mac"]}
        _mac = utils.Mac(mac)

        json_data = {
            'total': len(var_dict) + 2,
            "variables": {
                **{
                    '_sys_serial': serial,
                    '_sys_lan_mac': _mac.cols,
                },
                **var_dict
            }
        }

        func = self.session.patch if not replace else self.session.put
        return await func(url, json_data=json_data)


    async def delete_device_template_variables(
        self,
        serial: str,
    ) -> Response:
        """Delete all of the template variables for a device.

        Args:
            serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/template_variables"

        return await self.session.delete(url)


    # >>>> CERTIFICATES <<<<

    async def get_certificates(self, q: str = None, offset: int = 0, limit: int = 20) -> Response:
            """Get Certificates details.

            Args:
                q (str, optional): Search for a particular certificate by its name, md5 hash or sha1_hash
                offset (int, optional): Number of items to be skipped before returning the data, useful
                    for pagination. Defaults to 0.
                limit (int, optional): Maximum number of records to be returned. Defaults to 20, Max 20.

            Returns:
                Response: CentralAPI Response object
            """
            url = "/configuration/v1/certificates"
            params = {"q": q, "offset": offset, "limit": limit}  # offset and limit are both required by the API method.

            return await self.session.get(url, params=params)

    async def upload_certificate(
        self,
        passphrase: str = "",
        cert_file: str | Path = None,
        cert_name: str = None,
        cert_format: CertFormat = None,
        cert_data: str = None,
        server_cert: bool = False,
        ca_cert: bool = False,
        crl: bool = False,
        int_ca_cert: bool = False,
        ocsp_resp_cert: bool = False,
        ocsp_signer_cert: bool = False,
        ssh_pub_key: bool = False,
    ) -> Response:
        """Upload a certificate.

        Args:
            passphrase (str): passphrase
            cert_file (Path|str, optional): Cert file to upload, if file is provided cert_name
                and cert_format will be derived from file name / extension, unless those params
                are also provided.
            cert_name (str, optional): The name of the certificate.
            cert_format (Literal["PEM", "DER", "PKCS12"], optional): cert_format  Valid Values: PEM, DER, PKCS12
            cert_data (str, optional): Certificate content encoded in base64 for all format certificates.
            server_cert (bool, optional): Set to True if cert is a server certificate. Defaults to False.
            ca_cert (bool, optional): Set to True if cert is a CA Certificate. Defaults to False.
            crl (bool, optional): Set to True if data is a certificate revocation list. Defaults to False.
            int_ca_cert (bool, optional): Set to True if certificate is an intermediate CA cert. Defaults to False.
            ocsp_resp_cert (bool, optional): Set to True if certificate is an OCSP responder cert. Defaults to False.
            ocsp_signer_cert (bool, optional): Set to True if certificate is an OCSP signer cert. Defaults to False.
            ssh_pub_key (bool, optional): Set to True if certificate is an SSH Pub key. Defaults to False.
                ssh_pub_key needs to be in PEM format, ssh-rsa is not supported.

        Raises:
            ValueError: Raised if invalid combination of arguments is provided.

        Returns:
            Response: CentralAPI Response object
        """
        # API-FLAW API method, PUBLIC_CERT is not accepted
        url = "/configuration/v1/certificates"
        valid_types = [
            "SERVER_CERT",
            "CA_CERT",
            "CRL",
            "INTERMEDIATE_CA",
            "OCSP_RESPONDER_CERT",
            "OCSP_SIGNER_CERT",
            "PUBLIC_CERT"
        ]
        type_vars = [server_cert, ca_cert, crl, int_ca_cert, ocsp_resp_cert, ocsp_signer_cert, ssh_pub_key]
        if type_vars.count(True) > 1:
            raise ValueError("Provided conflicting certificate types, only 1 should be set to True.")
        elif all([not bool(var) for var in type_vars]):
            raise ValueError("No cert_type provided, one of the cert_types should be set to True")

        if cert_format and cert_format.upper() not in ["PEM", "DER", "PKCS12"]:
            raise ValueError(f"Invalid cert_format {cert_format}, valid values are 'PEM', 'DER', 'PKCS12'")
        elif not cert_format and not cert_file:
            raise ValueError("cert_format is required when not providing certificate via file.")

        if not cert_data and not cert_file:
            raise ValueError("One of cert_file or cert_data should be provided")
        elif cert_data and cert_file:
            raise ValueError("Only one of cert_file and cert_data should be provided")

        for cert_type, var in zip(valid_types, type_vars):
            if var:
                break

        cert_bytes = None
        if cert_file:
            cert_file = Path(cert_file) if not isinstance(cert_file, Path) else cert_file
            cert_name = cert_name or cert_file.stem
            if cert_format:
                cert_format = cert_format.upper()
            else:
                if cert_file.suffix.lower() in [".pfx", ".p12"]:
                    cert_format = "PKCS12"
                elif cert_file.suffix.lower() in [".pem", ".cer", "crt"]:
                    cert_format = "PEM"
                else:
                    # TODO determine format using cryptography lib
                    cert_format = "DER"

            if cert_format == "PEM":
                cert_data = cert_file.read_text()
            else:
                cert_bytes = cert_file.read_bytes()

        cert_bytes = cert_bytes or cert_data.encode("utf-8")
        cert_b64 = base64.b64encode(cert_bytes).decode("utf-8")

        json_data = {
            'cert_name': cert_name,
            'cert_type': cert_type,
            'cert_format': cert_format,
            'passphrase': passphrase,
            'cert_data': cert_b64
        }

        return await self.session.post(url, json_data=json_data)

    async def delete_certificate(self, certificate: str) -> Response:
        """Delete existing certificate.

        Args:
            certificate (str): Name of the certificate to delete.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/certificates/{certificate}"

        return await self.session.delete(url)

    # >>>> WLAN <<<<

    async def get_full_wlan_list(
        self,
        scope: str,
    ) -> Response:
        """Get WLAN list/details by (UI) group.

        Args:
            scope (str): Provide one of group name, swarm id, or serial number.
                Example: Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/full_wlan/{scope}"

        # this endpoint returns a JSON string
        resp = await self.session.get(url)
        if isinstance(resp.output, str):
            resp.output = json.loads(resp.output)
        if isinstance(resp.output, dict) and "wlans" in resp.output:
            resp.output = resp.output["wlans"]

        return resp

    async def get_wlan(self, group: str, wlan_name: str) -> Response:
        """Get the information of an existing WLAN.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN selected.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/wlan/{group}/{wlan_name}"

        return await self.session.get(url)

    async def create_wlan(
        self,
        group: str,
        wlan_name: str,
        wpa_passphrase: str,
        # wpa_passphrase_changed: bool = True,
        vlan: str = "",
        type: constants.WlanType = "employee",
        essid: str = None,
        zone: str = "",
        captive_profile_name: str = "",
        bandwidth_limit_up: str = "",
        bandwidth_limit_down: str = "",
        bandwidth_limit_peruser_up: str = "",
        bandwidth_limit_peruser_down: str = "",
        access_rules: list = DEFAULT_ACCESS_RULES["ALLOW_ALL"],
        is_locked: bool = False,
        hide_ssid: bool = False,
    ) -> Response:
        """Create a new WLAN (SSID).

        Args:
            group (str): Aruba Central Group name or swarm guid
            wlan_name (str): Name of the WLAN/Network
            wpa_passphrase (str): WPA passphrase
            vlan (str): Client VLAN name or id. Defaults to "" (Native AP VLAN).
            type (WlanType, optional): Valid: ['employee', 'guest']. Defaults to "employee".
            essid (str, optional): SSID. Defaults to None (essid = wlan_name).
            zone (str, optional): AP Zone SSID will broadcast on. Defaults to "" (Broadcast on all APs).
            captive_profile_name (str, optional): Captive Portal Profile. Defaults to "" (No CP Profile).
            bandwidth_limit_up (str, optional): [description]. Defaults to "" (No BW Limit Up).
            bandwidth_limit_down (str, optional): [description]. Defaults to "" (No BW Limit Down).
            bandwidth_limit_peruser_up (str, optional): [description]. Defaults to "" (No per user BW Limit Up).
            bandwidth_limit_peruser_down (str, optional): [description]. Defaults to "" (No per user BW Limit Down).
            access_rules (list, optional): [description]. Default: unrestricted.
            is_locked (bool, optional): [description]. Defaults to False.
            hide_ssid (bool, optional): [description]. Defaults to False.
            wpa_passphrase_changed (bool, optional): indicates passphrase has changed. Defaults to True.

        Returns:
            Response: [description]
        """
        url = f"/configuration/v2/wlan/{group}/{wlan_name}"

        json_data = {
            "wlan": {
                'essid': essid or wlan_name,
                'type': type,
                'hide_ssid': hide_ssid,
                'vlan': vlan,
                'zone': zone,
                'wpa_passphrase': wpa_passphrase,
                # 'wpa_passphrase_changed': wpa_passphrase_changed,
                'is_locked': is_locked,
                'captive_profile_name': captive_profile_name,
                'bandwidth_limit_up': bandwidth_limit_up,
                'bandwidth_limit_down': bandwidth_limit_down,
                'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
                'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
                'access_rules': access_rules
            }
        }

        return await self.session.post(url, json_data=json_data)

    async def update_wlan(
        self,
        scope: str,
        wlan_name: str,
        essid: str = None,
        type: str = None,
        hide_ssid: bool = None,
        vlan: str = None,
        zone: str = None,
        wpa_passphrase: str = None,
        is_locked: bool = None,
        captive_profile_name: str = None,
        bandwidth_limit_up: str = None,
        bandwidth_limit_down: str = None,
        bandwidth_limit_peruser_up: str = None,
        bandwidth_limit_peruser_down: str = None,
        access_rules: list = None,
    ) -> Response:
        """Update an existing WLAN and clean up unsupported fields.

        Args:
            scope (str): Group name of the group or guid of the swarm
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
        url = f"/configuration/v2/wlan/{scope}/{wlan_name}"

        json_data = {
            'essid': essid,
            'type': type,
            'hide_ssid': hide_ssid,
            'vlan': vlan,
            'zone': zone,
            'wpa_passphrase': wpa_passphrase,
            'wpa_passphrase_changed': wpa_passphrase is not None,
            'is_locked': is_locked,
            'captive_profile_name': captive_profile_name,
            'bandwidth_limit_up': bandwidth_limit_up,
            'bandwidth_limit_down': bandwidth_limit_down,
            'bandwidth_limit_peruser_up': bandwidth_limit_peruser_up,
            'bandwidth_limit_peruser_down': bandwidth_limit_peruser_down,
            'access_rules': access_rules
        }
        json_data = {'wlan': utils.strip_none(json_data)}

        return await self.session.patch(url, json_data=json_data)

    async def delete_wlan(self, group: str, wlan_name: str) -> Response:
        """Delete an existing WLAN.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            wlan_name (str): Name of WLAN to be deleted.
                Example:wlan_1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/wlan/{group}/{wlan_name}"

        return await self.session.delete(url)

    # >>>> AP SETTINGS <<<<

    async def get_ap_settings(self, serial: str) -> Response:
        """Get an existing ap settings.

        This returns a JSON and does not support all settings.
        Recommended to use ap_settings_cli

        Args:
            serial (str): AP serial number.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial}"

        return await self.session.get(url)

    # API-FLAW no option for 6G radio currently
    # disable radio via UI and ap_settings uses radio-0-disable (5G), radio-1-disable (2.4G), radio-2-disable (6G)
    # disable radio via API and ap_settings uses dot11a_radio_disable (5G), dot11g_radio_disable(2.4G), no option for (6G)
    # however UI still shows radio as UP (in config, overview shows it down) if changed via the API, it's down in reality, but not reflected in the UI because they use different attributes
    # API doesn't appear to take radio-n-disable, tried it.
    async def update_ap_settings(
        self,
        serial: str,
        hostname: str = None,
        ip_address: str = None,
        zonename: str = None,
        achannel: str = None,
        atxpower: str = None,
        gchannel: str = None,
        gtxpower: str = None,
        dot11a_radio_disable: bool = None,
        dot11g_radio_disable: bool = None,
        usb_port_disable: bool = None,
    ) -> Response:
        """Update an existing ap settings.

        Args:
            serial (str): AP Serial Number
            hostname (str, optional): hostname
            ip_address (str, optional): ip_address Default (DHCP)
            zonename (str, optional): zonename. Default "" (No Zone)
            achannel (str, optional): achannel
            atxpower (str, optional): atxpower
            gchannel (str, optional): gchannel
            gtxpower (str, optional): gtxpower
            dot11a_radio_disable (bool, optional): dot11a_radio_disable
            dot11g_radio_disable (bool, optional): dot11g_radio_disable
            usb_port_disable (bool, optional): usb_port_disable

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/ap_settings/{serial}"

        _json_data = {
            'hostname': hostname,
            'ip_address': ip_address,
            'zonename': zonename,
            'achannel': achannel,
            'atxpower': atxpower,
            'gchannel': gchannel,
            'gtxpower': gtxpower,
            'dot11a_radio_disable': dot11a_radio_disable,
            'dot11g_radio_disable': dot11g_radio_disable,
            'usb_port_disable': usb_port_disable,
        }
        if None in _json_data.values():
            resp: Response = await self.get_ap_settings(serial)
            if not resp:
                log.error(f"Unable to update AP settings for AP {serial}, API call to fetch current settings failed (all settings are required).", caption=True, log=True)
                return resp

            json_data = utils.strip_none(_json_data)
            if {k: v for k, v in resp.output.items() if k in json_data.keys()} == json_data:
                return Response(url=url, ok=True, output=f"{resp.output.get('hostname', '')}|{serial} Nothing to Update provided AP settings match current AP settings", error="OK",)

            json_data = {**resp.output, **json_data}

        return await self.session.post(url, json_data=json_data)

    async def _build_update_per_ap_settings_reqs(
        self,
        serial: str,
        current_clis: List[str],
        *,
        hostname: str = None,
        ip: str = None,
        mask: str = None,
        gateway: str = None,
        dns: str | List[str] = None,
        domain: str = None,
        swarm_mode: str = None,
        radio_24_mode: str = None,
        radio_5_mode: str = None,
        radio_6_mode: str = None,
        radio_24_disable: bool = None,
        radio_5_disable: bool = None,
        radio_6_disable: bool = None,
        uplink_vlan: int = None,
        zone: str = None,
        dynamic_ant_mode: DynamicAntenna = None,
        flex_dual_exclude: RadioType = None,
        boot_partition: int = None,
        ant_24_gain: int = None,
        ant_5_gain: int = None,
        ant_6_gain: int = None,
    ) -> BatchRequest | Response:
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        ip_address = None
        if ip:
            for param in [mask, gateway, dns]:
                if not param:
                    raise ValueError(f"Invalid configuration for {serial}: mask, gateway, and dns are required when IP is updated")

            dns = ','.join(utils.listify(dns))

            domain = domain or '""'
            ip_address = f'{ip} {mask} {gateway} {dns} {domain}'.rstrip()

        flex_dual = None
        if flex_dual_exclude:
            flex_dual_exclude = str(flex_dual_exclude)
            if flex_dual_exclude.startswith("6"):
                flex_dual = "5GHz-and-2.4GHz"
            elif flex_dual_exclude.startswith("5"):
                flex_dual = "2.4GHz-and-6GHz"
            elif flex_dual_exclude.startswith("2"):
                flex_dual = "5GHz-and-6GHz"
            else:
                raise ValueError(f"Invalid value {flex_dual_exclude} for flex_dual_exclude, valid values: '2.4', '5', '6'")

        old_disable = {
            "radio-0-disable": "dot11a-radio-disable",
            "radio-1-disable": "dot11g-radio-disable",
        }
        cli_items = {
            "hostname": hostname,
            "ip-address": ip_address,
            "swarm-mode": swarm_mode,
            "wifi0-mode": radio_5_mode,
            "wifi1-mode": radio_24_mode,
            "wifi2-mode": radio_6_mode,
            "radio-0-disable": radio_5_disable,
            "radio-1-disable": radio_24_disable,
            "radio-2-disable": radio_6_disable,
            "zonename": zone,
            "uplink-vlan": uplink_vlan,
            "dynamic-ant": dynamic_ant_mode,
            "flex-dual-band": flex_dual,
            "g-external-antenna": ant_24_gain,
            "a-external-antenna": ant_5_gain,
            # "radio-6-external-antenna": ant_6_gain,
            "os_partition": boot_partition

        }
        if all([v is None for v in cli_items.values()]):
            return Response(error="No Values provided to update")

        update_clis = deepcopy(current_clis)
        for idx, key in enumerate(cli_items, start=1):
            if cli_items[key] is not None:
                update_clis = [item for item in update_clis if not item.lstrip().startswith(key)]
                if key.endswith("-disable"):
                    old_model = True if "wifi2-mode" not in str(update_clis) else False
                    old_var = old_disable.get(key)
                    value = old_var if old_model else key
                    stripped_clis = [item.strip() for item in update_clis]
                    if cli_items[key] is True:
                        if value not in stripped_clis:
                            update_clis.insert(idx, f"  {value}")
                    elif old_var and old_var in stripped_clis:  # Ensure we remove old variable from new APs as we initially sent both.
                        _ = update_clis.pop(stripped_clis.index(old_var))
                elif key == "dynamic-ant" and cli_items[key] == "wide":
                    continue  # dynamic-ant wide is the default putting it in the config causes dirty diff as central pushes it, but when it verifies that line is not there
                else:
                    update_clis.insert(idx, f"  {key} {cli_items[key]}")

        if sorted(current_clis) == sorted(update_clis):
            try:
                iden = f"{current_clis[1].split()[1]}|{serial}"
            except Exception:
                iden = serial
            return Response(ok=True, error="NO CHANGES", output=f"{iden} skipped. The Provided per ap settings match the APs current AP settings.")

        return BatchRequest(self.session.post, url, json_data={'clis': update_clis})

    # TODO types for below
    # effectively a dup of update_ap_settings, granted the other uses ap_settings vs this which uses ap_settings_cli (more complete coverage here)
    async def update_per_ap_settings(
        self,
        serial: str = None,
        hostname: str = None,
        ip: str = None,
        mask: str = None,
        gateway: str = None,
        dns: str | List[str] = None,
        domain: str = None,
        swarm_mode: str = None,
        radio_24_mode: str = None,
        radio_5_mode: str = None,
        radio_6_mode: str = None,
        radio_24_disable: bool = None,
        radio_5_disable: bool = None,
        radio_6_disable: bool = None,
        uplink_vlan: int = None,
        zone: str = None,
        dynamic_ant_mode: DynamicAntenna = None,
        flex_dual_exclude: RadioType = None,
        ant_24_gain: int = None,
        ant_5_gain: int = None,
        ant_6_gain: int = None,
        as_dict: Dict[str, Dict[str | int | List[str] | bool | DynamicAntenna | RadioType]] = None
    ) -> List[Response]:
        """Update per AP settings (AP ENV)

        This method performs 2 API calls, the first to pull the existing config,
        the second to update the config based on the updates provided.

        model is needed if disabling 2.4 or 5Ghz radios to determine if AP uses
        old format: dot11g-radio-disable or newer: radio-1-disable
        Sending the wrong one has no impact, sending both results in Central
        showing unsynchronized

        as_list can be provided with params for multiple APs.
        """
        kwargs = {
            "hostname": hostname,
            "ip": ip,
            "mask": mask,
            "gateway": gateway,
            "dns": dns,
            "domain": domain,
            "swarm_mode": swarm_mode,
            "radio_24_mode": radio_24_mode,
            "radio_5_mode": radio_5_mode,
            "radio_6_mode": radio_6_mode,
            "radio_24_disable": radio_24_disable,
            "radio_5_disable": radio_5_disable,
            "radio_6_disable": radio_6_disable,
            "uplink_vlan": uplink_vlan,
            "zone": zone,
            "dynamic_ant_mode": dynamic_ant_mode,
            "flex_dual_exclude": flex_dual_exclude,
            "ant_5_gain": ant_5_gain,
            "ant_24_gain": ant_24_gain,
            "ant_6_gain": ant_6_gain,
        }
        as_dict = as_dict or {}
        if any(kwargs.values()) and not serial:
            raise ValueError("serial is required")
        if serial:
            as_dict[serial] = kwargs

        base_url = "/configuration/v1/ap_settings_cli"

        try:
            current_reqs = [
                BatchRequest(self.session.get, f"{base_url}/{serial}")
                for serial in as_dict
            ]
        except KeyError as e:
            raise KeyError(f"Missing required argument 'serial'\n{e}")

        current_resp = await self.session._batch_request(current_reqs)

        passed: Dict[str, Response] = {}
        failed: Dict[str, Response] = {}
        for serial, resp in zip(as_dict.keys(), current_resp):
            if resp.ok:
                passed[serial] = resp
            else:
                failed[serial] = resp

        if not passed:
            log.error(f"Unable to send updates to AP{utils.singular_plural_sfx(current_reqs)}.  Request to fetch current settings failed{utils.singular_plural_sfx(current_reqs, singular='.', plural=' for All APs.')}", caption=True)
            return current_resp

        update_reqs = [
            await self._build_update_per_ap_settings_reqs(serial, current_clis=resp.output, **{k: v for k, v in as_dict[serial].items() if k != "serial"})
            for serial, resp in passed.items()
        ]

        skipped = [resp for resp in update_reqs if isinstance(resp, Response)]
        update_reqs = [req for req in update_reqs if isinstance(req, BatchRequest)]

        update_resp = await self.session._batch_request(update_reqs)

        return [*update_resp, *skipped, *list(failed.values())]

    # not used by any commands
    async def get_ap_system_config(
        self,
        scope: str,
    ) -> Response:
        """Get System Config.

        Args:
            scope (str): Group name of the group or guid of the swarm
                or serial number of 10x AP.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f or CNF7JSS9L1.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/system_config/{scope}"

        return await self.session.get(url)

    # API-FLAW  Seems to work fine for cx, ap, but gw the return is
    # "Fetching configuration in progress for Mobility Controller SERIAL/MAC"
    # subsequent calls for the same gw return 500 internal server error.
    # FIXME
    async def get_device_configuration(self, serial: str) -> Response:
        """Get last known running configuration for a device.

        // Used by show run <DEVICE-IDEN> //

        Args:
            device_serial (str): Serial number of the device.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/devices/{serial}/configuration"

        return await self.session.get(url, headers={"Accept": "multipart/form-data"})

    async def get_ap_config(
        self,
        iden: str,
        version: str = None,
    ) -> Response:
        """Get AP Group Level configuration for UI group.

        // Used by show config <AP MAC for AOS10 AP> //

        Args:
            iden (str, optional): Group name swarm id or serial # (AOS10 AP).
                Example: Retail or 6a5d123b1b77c828a085f04f... or USF7JSS9L1.
            version (str, optional): Version of AP.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{iden}"

        params = {
            'version': version
        }

        return await self.session.get(url, params=params)

    async def replace_ap_config(
        self,
        iden: str,
        clis: List[str],
    ) -> Response:
        """Replace AP Group or device Level configuration for UI group.

        Send AP configuration in CLI format as a list of strings where each item in the list is
        a line from the config.  Requires all lines of the config, not a partial update.

        Args:
            iden (str): Group name swarm id or serial # (AOS10 AP)
                Example: Retail or 6a5d123b1b77c828a085f04f... or USF7JSS9L1.
            clis (List[str]): Whole configuration List in CLI format.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_cli/{iden}"

        json_data = {
            'clis': clis
        }

        return await self.session.post(url, json_data=json_data)

    async def get_swarm_config(
        self,
        swarm_id: str,
    ) -> Response:
        """Get an existing swarm config.

        Args:
            swarm_id (str): swarm_id (guid) of the SWARM.
                Example: 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/swarm_config/{swarm_id}"

        return await self.session.get(url)

    # API-FLAW ??  throws error if offsets are not provided, API apparently doesn't get tz offset from timezone (name) and doesn't seem to change the setting regardless
    # It will add "clock timezone America/Chicago -06 00" if you provide name=America/Chicago tz_offset_hr = -6 tz_offset_min = 0
    # but the DST config line "clock summer-time CDT recurring second sunday march 02:00 first sunday november 02:00" will not be added as it is from the dropdown in the UI
    # Also the TimeZone dropdown is not changed either way.  Maybe need to send Central-Time which is what is sent via the UI???
    # TODO update to fech current config if not all options provided the API thows an error if everything is not provided
    async def replace_swarm_config(
        self,
        swarm_id: str,
        name: str,
        ip_address: str,
        timezone: constants.IAP_TZ_NAMES,
        tz_offset_hr: int,
        tz_offset_min: int,
    ) -> Response:  # pragma: no cover the command that uses this is hidden see API-FLAW comment aboce
        """Update (replace) an existing swarm config.  All values are required.

        Args:
            swarm_id (str): swarm_id (guid) of Swarm.
                Example:6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            name (str): The name of the Virtual Controller
            ip_address (str): ip_address
            timezone (str): timezone name.
            tz_offset_hr (int): timezone offset hours from UTC. Range value is -12 to 14.
            tz_offset_min (int): timezone offset mins from UTC. Range value is 0 to 60.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v2/swarm_config/{swarm_id}"
        if tz_offset_hr and not isinstance(tz_offset_hr, int):
            tz_offset_hr = int(tz_offset_hr)
        if tz_offset_min and not isinstance(tz_offset_min, int):
            tz_offset_min = int(tz_offset_min)

        json_data = {
            'name': name,
            'ip_address': ip_address,
            'timezone_name': timezone,
            'timezone_hr': tz_offset_hr,
            'timezone_min': tz_offset_min
        }

        return await self.session.post(url, json_data=json_data)

    async def _add_altitude_to_config(self, data: List[str], altitude: int | float) -> List[str] | None:
            """Adds GPS altitude (meters from ground) to existing AP or swarm config

            Args:
                data (str): str representing the current configuration.
                altitude (int | float): The ap-altitude to add to the provided config.

            Raises:
                CentralCliException: If no commands remain after stripping empty lines.

            Returns:
                List[str] | None Original config with 2 additional lines to define ap-altitude for gps
                    Returns None if desired ap-altitude is already in current configuration
            """
            cli_cmds = [out for out in [line.rstrip() for line in data] if out]

            if not cli_cmds:
                raise CentralCliException("Error: No cli commands remain after stripping empty lines.")

            # Need to send altitude as a float, if you try to update 2.1 with 2 it results in dirty-diff, but 2.1 updated to 2.0 is OK (wtf)
            # sending value as int initially is OK, but float to int it doesn't like so just always send float
            # this may have been because group level had ap-altitude as 2, dunno
            if "gps" not in cli_cmds:
                cli_cmds += ["gps", f"  ap-altitude {float(altitude)}"]
            elif f"  ap-altitude {float(altitude)}" in cli_cmds:
                return # No change ap-altitude already in existing
            else:
                cli_cmds = [line for line in cli_cmds if not line.strip().startswith("ap-altitude")]
                cli_cmds.insert(cli_cmds.index("gps") + 1, f"  ap-altitude {float(altitude)}")

            return cli_cmds

    async def update_ap_altitude(
        self,
        iden: str = None,
        altitude: int | float = None,
        as_dict: Dict[str, int | float] = None,
    ) -> List[Response]:
        """Set or Update gps ap-altitude at group or device level for APs (UI group).

        Pulls existing config and adds or updates provided ap-altitude.
        Performs 2 API calls per AP.

        Multiple APs can be provided using as_dict.

        Args:
            iden (str, optional): Group name swarm id or serial # (AOS10 AP).
                Example: Retail or 6a5d123b1b77c828a085f04f... or USF7JSS9L1.
            altitude (int | float, optional): The AP installation height represented as meters from the ground.
                Note: Despite the CLI command being ap-altitude, it is not from sea level, it's from the ground.
            as_dict: (Dict[str, int | float], optional): A dict providing ap serial numbers and altitudes.
                i.e.: {"AP1serial": ap1_altitude, AP2serial: ap2_altitude ...}

        Returns:
            List[Response]: Returns a List of Response objects.
        """
        base_url = "/configuration/v1/ap_cli"
        as_dict = as_dict or {}
        if iden:
            if not altitude:
                raise ValueError("altitude is required when iden is provided")
            as_dict = {**as_dict, **{iden: altitude}}
        if not as_dict:
            raise ValueError("Missing required parameter: iden and altitude and/or as_dict is required")

        current_reqs = [BatchRequest(self.session.get, f"{base_url}/{iden}") for iden in as_dict]
        current_resp = await self.session._batch_request(current_reqs)

        passed: Dict[str, Response] = {}
        failed: Dict[str, Response] = {}
        for iden, resp in zip(as_dict.keys(), current_resp):
            if resp.ok:
                passed[iden] = resp
            else:
                failed[iden] = resp

        if not passed:
            return current_resp

        updated_clis_list = [await self._add_altitude_to_config(resp.output, altitude=as_dict[iden]) for iden, resp in passed.items()]

        skipped = [Response(ok=True, error="No CHANGES", output=f"AP Altitude Update skipped for {iden}. ap-altitude {as_dict[iden]} exists in current configuration.") for (iden, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis is None]
        update_reqs = [BatchRequest(self.session.post, f"{base_url}/{iden}", json_data={"clis": updated_clis}) for (iden, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis]

        update_resp = [] if not update_reqs else await self.session._batch_request(update_reqs)

        return [*update_resp, *skipped, *list(failed.values())]

    async def _add_banner_to_config(self, data: List[str], banner: str | list[str]) -> List[str] | None:
            """Adds banner motd text to existing AP or swarm config

            Args:
                data (str): str representing the current configuration.
                banner (str | list[str]): The banner text as str or list of str.

            Raises:
                CentralCliException: If no commands remain after stripping empty lines.

            Returns:
                List[str] | None: Original config with with banner text inserted.
                    Returns None if desired ap-altitude is already in current configuration
            """
            cli_cmds = [out for out in [line.rstrip() for line in data] if out]
            existing_banner = [line for line in cli_cmds if line.startswith("banner motd")]
            if isinstance(banner, str):
                banner = banner.splitlines()

            def _format_banner_line(banner_line: str) -> str:
                return banner_line if banner_line.startswith("banner motd") else f'banner motd "{banner_line}"'

            banner = [_format_banner_line(line.strip()) for line in banner]

            if not cli_cmds:
                raise CentralCliException("Error: No cli commands remain after stripping empty lines.")

            if not existing_banner:
                cli_cmds += banner
            elif banner == existing_banner:
                return # No change banner text is as desired
            else:
                cli_cmds = [line for line in cli_cmds if not line.strip().startswith("banner motd")]
                cli_cmds += banner

            return cli_cmds

    async def update_ap_banner(
        self,
        iden: str | list[str] = None,
        banner: str = None,
        as_dict: dict[str, str] = None,
    ) -> List[Response]:
        """Set or Update ap motd banner at group or device level for APs (UI group).

        Pulls existing config and adds or updates provided banner.
        Performs 2 API calls per AP.

        Multiple APs can be provided using as_dict.

        Args:
            iden (str | list[str], optional): Group name swarm id or serial # (AOS10 AP) or list of the same.
                Example: Retail or 6a5d123b1b77c828a085f04f... or USF7JSS9L1 or ['USF7JSS9L1', 'USF7JSS9L2'].
            banner (str, optional): The banner text to be added at the AP or group level.
                Note: Despite the CLI command being ap-altitude, it is not from sea level, it's from the ground.
            as_dict: (dict[str, str], optional): A dict providing ap serial numbers and altitudes.
                i.e.: {"AP1serial": "banner text", "AP2serial": "banner text" ...}

        If banner is the same, multiple APs/groups can be processed by sending a list for iden parameter.
        If banners are unique for each iden, multiple APs/Groups can be processed by sending as_dict where
        group name/serial is the key and the desired banner text is the value.  i.e.
        {
            "USF7JSS9L1": "banner text ... connected to USF7JSS9L1",
            "USF7JSS9L2": "banner text ... connected to USF7JSS9L2"
        }

        Returns:
            List[Response]: Returns a List of Response objects.
        """
        base_url = "/configuration/v1/ap_cli"
        as_dict = as_dict or {}
        if iden:
            if not banner:
                raise ValueError("banner is required when iden is provided")
            as_dict = {**as_dict, **{i: banner for i in utils.listify(iden)}}
        if not as_dict:
            raise ValueError("Missing required parameter: iden and banner and/or as_dict is required")

        current_reqs = [BatchRequest(self.session.get, f"{base_url}/{iden}") for iden in as_dict]
        current_resp = await self.session._batch_request(current_reqs)

        passed: Dict[str, Response] = {}
        failed: Dict[str, Response] = {}
        for iden, resp in zip(as_dict.keys(), current_resp):
            if resp.ok:
                passed[iden] = resp
            else:
                failed[iden] = resp

        if not passed:
            return current_resp

        updated_clis_list = [await self._add_banner_to_config(resp.output, banner=as_dict[iden]) for iden, resp in passed.items()]


        skipped = [Response(ok=True, error="No CHANGES", output=f"Banner Update skipped for {iden}. desired banner text already exists in current configuration.") for (iden, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis is None]
        update_reqs = [BatchRequest(self.session.post, f"{base_url}/{iden}", json_data={"clis": updated_clis}) for (iden, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis]

        update_resp = [] if not update_reqs else await self.session._batch_request(update_reqs)

        return [*update_resp, *skipped, *list(failed.values())]

    async def _update_cp_cert_in_config(self, data: List[str], cp_cert_md5: str,) -> List[str] | None:
            """Updates cp-cert-checksum in AP group level config

            Args:
                data (str): str representing the current configuration.
                cp_cert_md5 (str): The cp-cert-md5 checksum to reference in the config.

            Raises:
                CentralCliException: If no commands remain after stripping empty lines.
                    This really should not happen.

            Returns:
                List[str] | None Original config with cp-cert-checksum updated with provided value
                    Returns None if desired cp-cert-checksum is already in current configuration
            """
            cli_cmds = [out for out in [line.rstrip() for line in data] if out]

            if not cli_cmds:
                raise CentralCliException("Error: No cli commands remain after stripping empty lines.")

            if f"cp-cert-checksum {cp_cert_md5}" in cli_cmds:
                return # No change cp-cert-checksum already as desired
            else:
                line_index = [idx for idx, line in [(idx, line) for idx, line in enumerate(cli_cmds)] if line.strip().startswith("cp-cert-checksum")]
                if line_index:
                    line_index = line_index[0]
                    _ = cli_cmds.pop(line_index)
                    log.debug(f"Removed {_} from config")
                else:  # cp-cert-checksum does not exist in the config
                    line_index = cli_cmds.index("cluster-security")
                cli_cmds.insert(line_index, f"cp-cert-checksum {cp_cert_md5}")
                log.debug(f'Added "cp-cert-checksum {cp_cert_md5}" to line {line_index + 1} of the config')

            return cli_cmds

    async def update_group_cp_cert(
        self,
        group: str | List[str] = None,
        cp_cert_md5: str = None,
        as_dict: Dict[str, str] = None,
    ) -> List[Response]:
        """Update cp-cert-checksum at group level for APs (UI group).

        Pulls existing config andupdates with provided cp-cert-checksum.
        Performs 2 API calls per AP.

        Multiple APs can be provided using as_dict.

        Args:
            group (str | List[str], optional): Group name, must be an AP group.
            cp_cert_md5 (str | float, optional): The Captive Portal Certificate md5 checksum.
            as_dict: (Dict[str, int | float], optional): A dict providing group names and cp cert md5 checksums
                i.e.: {"ap-group1": cp-cert-md5-checksum-goes-here, ap-group2: cp-cert-md5-checksum-goes-here ...}
                if the checksums are all the same just use group and and cp_cert_md5 arguments as group can take a list.

        Returns:
            List[Response]: Returns a List of Response objects.
        """
        as_dict = as_dict or {}
        if group:
            group = utils.listify(group)
            if not cp_cert_md5:
                raise ValueError("cp_cert_md5 is required when group is provided")
            as_dict = {**as_dict, **{g: cp_cert_md5 for g in group}}
        if not as_dict:
            raise ValueError("Missing required parameter: group and cp_cert_md5 and/or as_dict is required")

        base_url = "/configuration/v1/ap_cli"
        current_reqs = [BatchRequest(self.session.get, f"{base_url}/{g}") for g in as_dict]
        current_resp = await self.session._batch_request(current_reqs)

        passed: Dict[str, Response] = {}
        failed: Dict[str, Response] = {}
        for group, resp in zip(as_dict.keys(), current_resp):
            if resp.ok:
                passed[group] = resp
            else:
                failed[group] = resp

        if not passed:
            return current_resp

        updated_clis_list = [await self._update_cp_cert_in_config(resp.output, cp_cert_md5=as_dict[group]) for group, resp in passed.items()]

        skipped = [group for (group, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis is None]
        if skipped:
            skipped_msg = f"Certificate Update skipped for groups: {', '.join(skipped)}. cp-cert-checksum already configured as desired."
            log.info(skipped_msg, caption=True, log=False)

        update_reqs = [BatchRequest(self.session.post, f"{base_url}/{group}", json_data={"clis": updated_clis}) for (group, _), updated_clis in zip(passed.items(), updated_clis_list) if updated_clis]
        if not update_reqs:
            res = Response(error="No Update", output="No updates to process after validating current configuration")
            res.rl = BatchResponse(current_resp).last_rl
            return res

        update_resp = await self.session._batch_request(update_reqs)
        return [*update_resp, *list(failed.values())]

    async def get_per_ap_config(
        self,
        serial: str,
    ) -> Response:
        """Get per AP setting.

        Args:
            serial (str): Serial Number of AP

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        return await self.session.get(url)

    async def replace_per_ap_config(
        self,
        serial: str,
        clis: List[str],
    ) -> Response:
        """Replace per AP setting.

        Args:
            serial (str): Serial Number of AP
            clis (List[str]): All per AP setting List in CLI format
                Must provide all per AP settings, not partial

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/ap_settings_cli/{serial}"

        json_data = {
            'clis': clis
        }

        return await self.session.post(url, json_data=json_data)

    async def get_dirty_diff(
        self,
        group: str,
        offset: int = 0,
        limit: int = 20
    ) -> Response:
        """Get AP dirty diff (config items not pushed) by group.

        Args:
            group (str): Group name of the group or guid of the swarm.
                Example:Group_1 or 6a5d123b01f9441806244ea6e023fab5841b77c828a085f04f.
            offset (int, optional): Number of items to be skipped before returning the data, useful
                for pagination. Defaults to 0.
            limit (int, optional): Maximum number of group config_mode records to be returned.
                Max: 20, Defaults to 20.

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/dirty_diff/{group}"

        params = {
            'offset': offset,
            'limit': limit if limit <= 20 else 20
        }

        return await self.session.get(url, params=params)

    # >>>> SNAPSHOTS <<<<

    async def do_multi_group_snapshot(
        self,
        backup_name: str,
        include_groups: List[str] = None,
        exclude_groups: List[str] = None,
        do_not_delete: bool = False,
    ) -> Response:  # pragma: no cover ... not used by any command
        """Create new configuration backup for multiple groups.

        Either include_groups or exclude_groups should be provided, but not both.

        Args:
            backup_name (str): Name of Backup
            include_groups (List[str], optional): Groups to include in Backup. Defaults to None.
            exclude_groups (List[str], optional): Groups to Exclude in Backup. Defaults to None.
            do_not_delete (bool, optional): Flag to represent if the snapshot can be deleted automatically
                by system when creating new snapshot or not. Defaults to False.


        Returns:
            Response: Response Object
        """
        url = "/configuration/v1/groups/snapshot/backups"
        include_groups = utils.listify(include_groups)
        exclude_groups = utils.listify(exclude_groups)
        payload = {
            "backup_name": backup_name,
            "do_not_delete": do_not_delete,
            "include_groups": include_groups,
            "exclude_groups": exclude_groups,
        }
        payload = utils.strip_none(payload)
        return await self.session.post(url, json_data=payload)

    async def get_snapshots_by_group(self, group: str):
        url = f"/configuration/v1/groups/{group}/snapshots"
        return await self.session.get(url)

    # TODO validate IP address format / Not used by CLI yet
    # needs testing returned 400: {"error":{"code":"BADREQ_UNSUPPORTED_REST_OP","message":"Operation not allowed"}}
    async def update_cx_properties(
        self,
        *,
        serial: str = None,
        group: str = None,
        name: str = None,
        contact: str = None,
        location: str = None,
        timezone: constants.TZDB = None,
        mgmt_vrf: bool = None,
        dns_servers: List[str] = [],
        ntp_servers: List[str] = [],
        admin_user: str = None,
        admin_pass: str = None,
    ) -> Response:  # pragma: no cover.  Not sure this endpoint works see comments above
        """Update Properties (ArubaOS-CX).

        Args:
            serial (str, optional): Device serial number.
                Mandatory for device level configuration.
                1 and only 1 of serial or group are required
            group (str, optional): Group name.
                Mandatory for group level configuration.
                1 and only 1 of serial or group are required
            name (str): Only configurable at device-level.
            contact (str): Pattern: "^[^"?]*$"
            location (str): Pattern: "^[^"?]*$"
            timezone (str): timezone  Valid Values: use tz database format like "America/Chicago"
            mgmt_vrf (bool): Use mgmt VRF, indicates VRF for dns_servers and ntp_servers, if False or not provided default VRF is used.
            dns_servers (List[str]): ipv4/ipv6 address
            ntp_servers (List[str]): ipv4/ipv6 address
            admin_user (str): local admin user
            admin_pass (str): local admin password

        Returns:
            Response: CentralAPI Response object
        """
        url = "/configuration/v1/switch/cx/properties"

        params = {
            'device_serial': serial,
            'group_name': group
        }

        json_data = {
            'name': name,
            'contact': contact,
            'location': location,
            'timezone': timezone,
            'dns_servers': dns_servers,
            'ntp_servers': ntp_servers,
            'admin_username': admin_user,
            'admin_password': admin_pass
        }
        if mgmt_vrf is not None:
            json_data["vrf"] = "mgmt" if mgmt_vrf else "default"
        elif dns_servers or ntp_servers:
            json_data["vrf"] = "default"

        if len([x for x in [admin_user, admin_pass] if x is not None]) == 1:
            raise ValueError("If either admin_user or admin_pass are bing updated, *both* should be provided.")

        if len([x for x in [serial, group] if x is not None]) > 1:
            raise ValueError("provide serial to update device level properties, or group to update at the group level.  Providing both is invalid.")

        json_data = utils.strip_none(json_data, strip_empty_obj=True)

        return await self.session.post(url, json_data=json_data, params=params)

    async def get_denylist_clients(
        self,
        serial: str,
    ) -> Response:
        """Get all denylist client mac address in device.

        Args:
            serial (str): Device id of virtual controller (AOS8 IAP) or serial of AOS10 ap.
                Example:14b3743c01f8080bfa07ca053ef1e895df9c0680fe5a17bfd5

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/configuration/v1/swarm/{serial}/blacklisting"

        return await self.session.get(url)