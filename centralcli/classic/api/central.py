from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, List

from ... import BatchRequest, Response, cleaner, constants, utils

if TYPE_CHECKING:
    from ... import Session


class CentralAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_all_sites(
        self,
        calculate_total: bool = False,
        sort: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """List Sites.

        Args:
            calculate_total (bool, optional): Whether to calculate total Site Labels
            sort (str, optional): Sort parameter may be one of +site_name, -site_name. Default is
                +site_name
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000 Defaults to 1000 (max).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"

        params = {
            'calculate_total': str(calculate_total),
            'sort': sort,
            'offset': offset,
            'limit': limit
        }

        return await self.session.get(url, params=params)

    # async def get_site_details(self, site_id):
    #     return await self.session.get(f"/central/v2/sites/{site_id}", callback=cleaner.sites)

    async def get_site_details(
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

        return await self.session.get(url)

    async def get_all_webhooks(self) -> Response:
        """List all defined webhooks.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"

        return await self.session.get(url)

    async def add_webhook(
        self,
        name: str,
        urls: List[str],
    ) -> Response:
        """Add / update Webhook.

        Args:
            name (str): name of the webhook
            urls (List[str]): List of webhook urls

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/webhooks"
        urls = utils.listify(urls)

        json_data = {
            'name': name,
            'urls': urls
        }

        return await self.session.post(url, json_data=json_data)

    async def update_webhook(
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

        return await self.session.put(url, json_data=json_data)

    async def delete_webhook(
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

        return await self.session.delete(url)

    async def refresh_webhook_token(
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

        return await self.session.put(url)

    # API-FLAW Test webhook does not send an "id", it's how you determine what to Close
    async def test_webhook(
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

        return await self.session.get(url)

    async def create_site(
        self,
        site_name: str = None,
        address: str = None,
        city: str = None,
        state: str = None,
        country: str = None,
        zipcode: int | str = None,
        latitude: float = None,
        longitude: float = None,
        site_list: List[Dict[str, str | dict]] = None,  # TODO TypedDict
    ) -> Response:
        """Create Site

        Either address information or GeoLocation information is required.  For Geolocation attributes
        all attributes are required.  Or a List[dict] with multiple sites to be added containing either
        'site_address' or 'geolocation' attributes for each site.

        Args:
            site_name (str, optional): Site Name. Defaults to None.
            address (str, optional): Address. Defaults to None.
            city (str, optional): City. Defaults to None.
            state (str, optional): State. Defaults to None.
            country (str, optional): Country Name. Defaults to None.
            zipcode (int | str, optional): Zipcode. Defaults to None.
            latitude (float, optional): Latitude (in the range of -90 and 90). Defaults to None.
            longitude (float, optional): Longitude (in the range of -100 and 180). Defaults to None.
            site_list (List[Dict[str, str | dict]], optional): A list of sites to be created. Defaults to None.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/sites"
        zipcode = None if not zipcode else str(zipcode)
        latitude = None if not latitude else str(latitude)
        longitude = None if not longitude else str(longitude)

        address_dict = utils.strip_none({"address": address, "city": city, "state": state, "country": country, "zipcode": zipcode})
        geo_dict = utils.strip_none({"latitude": latitude, "longitude": longitude})
        json_data = {"site_name": site_name}
        if address_dict:
            json_data["site_address"] = address_dict
        if geo_dict:
            json_data["geolocation"] = geo_dict

        # TODO revert this to single site add and use batch_add_site method for multi-add
        if site_list:
            resp = await self.session.post(url, json_data=site_list[0])
            if not resp:
                return resp
            if len(site_list) > 1:
                ret = await self.session._batch_request(
                    [
                        BatchRequest(self.session.post, url, json_data=_json, callback=cleaner._unlist)
                        for _json in site_list[1:]
                    ]
                )
                return [resp, *ret]
        else:
            return await self.session.post(url, json_data=json_data, callback=cleaner._unlist)  # TODO remove callback

    async def update_site(
        self,
        site_id: int,
        site_name: str,
        address: str = None,
        city: str = None,
        state: str = None,
        zipcode: str = None,
        country: str = None,
        latitude: str = None,
        longitude: str = None,
    ) -> Response:
        """Update Site.

        Provide geo-loc or address details, not both.
        Can provide both in subsequent calls, but apigw does not
        allow both in same call.

        Args:
            site_id (int): Site ID
            site_name (str): Site Name
            address (str): Address
            city (str): City Name
            state (str): State Name
            zipcode (str): Zipcode
            country (str): Country Name
            latitude (str): Latitude (in the range of -90 and 90)
            longitude (str): Longitude (in the range of -180 and 180)

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/central/v2/sites/{site_id}"
        if zipcode:
            zipcode = str(zipcode)


        site_address = {"address": address, "city": city, "state": state, "country": country, "zipcode": zipcode}
        geolocation = {"latitude": latitude, "longitude": longitude}

        site_address = utils.strip_none(site_address)
        geolocation = utils.strip_none(geolocation)

        json_data = {
            "site_name": site_name,
            "site_address": site_address,
            "geolocation": geolocation
        }

        return await self.session.patch(url, json_data=json_data)

    async def delete_site(self, site_id: int | List[int]) -> Response | List[Response]:
        """Delete Site.

        Args:
            site_id (int|List[int]): Either the site_id or a list of site_ids to be deleted.

        Returns:
            Response: CentralAPI Response object
        """
        b_url = "/central/v2/sites"
        if isinstance(site_id, list):
            return await self.session._batch_request(
                [
                    BatchRequest(self.session.delete, f"{b_url}/{_id}")
                    for _id in site_id
                ]
            )
        else:
            url = f"{b_url}/{site_id}"
            return await self.session.delete(url)

    async def move_devices_to_site(
        self,
        site_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Associate list of devices to a site.

        Args:
            site_id (int): Site ID
            device_type (str): Device type. Valid Values: ap, gw switch
            serials (str | List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.

        Returns:
            Response: CentralAPI Response object
        """
        # TODO make device_types consistent throughout
        device_type = constants.lib_to_api(device_type, "site")
        if not device_type:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_str}"
            )

        url = "/central/v2/sites/associations"
        serials = utils.listify(serials)

        json_data = {
            'site_id': site_id,
            'device_ids': serials,
            'device_type': device_type
        }

        return await self.session.post(url, json_data=json_data)

    async def remove_devices_from_site(
        self,
        site_id: int,
        serials: List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Remove a list of devices from a site.

        Args:
            site_id (int): Site ID
            serials (str | List[str]): List of device serial numbers of the devices to which the site
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (Literal['ap', 'gw', 'switch']): Device type. Valid Values: ap, gw, switch.

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        url = "/central/v2/sites/associations"
        serials = utils.listify(serials)

        json_data = {
            'site_id': site_id,
            'device_ids': serials,
            'device_type': device_type
        }

        return await self.session.delete(url, json_data=json_data)  # API-FLAW: This method returns 200 when failures occur.

    async def create_label(
        self,
        label_name: str,
        category_id: int = 1,
    ) -> Response:
        """Create Label.

        Args:
            label_name (str): Label name
            category_id (int, optional): Label category ID defaults to 1
                1 = default label category, 2 = site

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/labels"

        json_data = {
            'category_id': category_id,
            'label_name': label_name
        }

        return await self.session.post(url, json_data=json_data)

    async def get_labels(
        self,
        calculate_total: bool = None,
        reverse: bool = False,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """List Labels.

        Args:
            calculate_total (bool, optional): Whether to calculate total Labels
            reverse (bool, optional): List labels in reverse alphabetical order. Defaults to False
            offset (int, optional): Pagination offset Defaults to 0.
            limit (int, optional): Pagination limit. Max is 1000. Defaults to 100.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels"

        params = {
            "calculate_total": calculate_total,
            "offset": offset,
            "limit": limit
        }
        if reverse:
            params["sort"] = "-label_name"

        return await self.session.get(url, params=params)

    async def assign_label_to_devices(
        self,
        label_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """Associate Label to a list of devices.

        Args:
            label_id (int): Label ID
            serials (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (str): Device type. Valid Values: ap, gw, switch

        Returns:
            Response: CentralAPI Response object
        """
        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        url = "/central/v2/labels/associations"
        serials = utils.listify(serials)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serials
        }

        return await self.session.post(url, json_data=json_data)

    async def remove_label_from_devices(
        self,
        label_id: int,
        serials: str | List[str],
        device_type: constants.GenericDeviceTypes,
    ) -> Response:
        """unassign a label from a list of devices.

        Args:
            label_id (int): Label ID
            serials (str | List[str]): List of device serial numbers of the devices to which the label
                has to be un/associated with. A maximum of 5000 device serials are allowed at once.
            device_type (Literal['ap', 'gw', 'switch']): Device type. Valid Values: ap, gw, switch.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v2/labels/associations"

        device_type = constants.lib_to_api(device_type, "site")
        if device_type not in ["CONTROLLER", "IAP", "SWITCH"]:
            raise ValueError(
                f"Invalid Value for device_type.  Supported Values: {constants.lib_to_api.valid_generic_str}"
            )

        serials = utils.listify(serials)

        json_data = {
            'label_id': label_id,
            'device_type': device_type,
            'device_ids': serials
        }

        return await self.session.delete(url, json_data=json_data)

    async def delete_label(
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

        return await self.session.delete(url)  # returns empty payload / response on success 200

    async def get_alerts(
        self,
        customer_id: str = None,
        group: str = None,
        label: str = None,
        serial: str = None,
        site: str = None,
        from_time: int | float | datetime = None,
        to_time: int | float | datetime = None,
        severity: str = None,
        type: str = None,
        search: str = None,
        # calculate_total: bool = False,  # Doesn't appear to impact always returns total
        ack: bool = None,
        fields: str = None,
        offset: int = 0,
        limit: int = 1000,
    ) -> Response:
        """[central] List Notifications/Alerts.  Returns 1 day by default.

        Args:
            customer_id (str, optional): MSP user can filter notifications based on customer id
            group (str, optional): Used to filter the notification types based on group name
            label (str, optional): Used to filter the notification types based on Label name
            serial (str, optional): Used to filter the result based on serial number of the device
            site (str, optional): Used to filter the notification types based on Site name
            from_time (int | float | datetime, optional): start of duration within which alerts are raised
                Default now - 1 day (max 90) (API endpoint default is 30 days)
            to_time (int | float | datetime, optional): end of duration within which alerts are raised
                Default now.
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
            limit (int, optional): Pagination limit. Default is 100 and max is 1000 Defaults to 500.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/central/v1/notifications"
        from_time, to_time = utils.parse_time_options(from_time, to_time)

        params = {
            'customer_id': customer_id,
            'group': group,
            'label': label,
            'serial': serial,
            'site': site,
            'from_timestamp': from_time,
            'to_timestamp': to_time,
            'severity': severity,
            'search': search,
            # 'calculate_total': str(calculate_total),
            'type': type,
            'ack': None if ack is None else str(ack),
            'fields': fields,
            'offset': offset,
            'limit': limit,
        }

        return await self.session.get(url, params=params)

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

        return await self.session.post(url)

    async def central_get_notification_config(
        self,
        search: str = None,
        sort: str = '-created_ts',
        offset: int = 0,
        limit: int = 500,
    ) -> Response:
        """List Configuration/Settings for alerts that result in notification.

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

        return await self.session.get(url, params=params)