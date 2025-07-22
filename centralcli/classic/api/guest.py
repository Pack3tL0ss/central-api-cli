from __future__ import annotations

from ..client import Session
from ... import utils, Response, constants
from typing import Literal


class GuestAPI:
    def __init__(self, session: Session):
        self.session = session

    async def get_portals(
        self,
        sort: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all portals with limited data.

        Args:
            sort (str, optional): `+` is for ascending  and `-` for descending order, Valid Values: name prepended with `+` or `-` i.e. +name.
                Defaults to None.  Which results in use of API default +name.
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

        return await self.session.get(url, params=params)

    async def get_portal_profile(
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

        return await self.session.get(url)

    async def delete_portal_profile(
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

        return await self.session.delete(url)

    async def get_guests(
        self,
        portal_id: str,
        sort: str = '+name',
        filter_by: str = None,
        filter_value: str = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Response:
        """Get all guests created against a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            sort (str, optional): + is for ascending  and - for descending order, Valid Values: '+name', '-name'. Defaults to +name.
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
        params = utils.strip_none(params)

        return await self.session.get(url, params=params)


    async def add_guest(
        self,
        portal_id: str,
        name: str,
        # id: str,
        password: str = None,
        *,
        company_name: str = None,
        phone: str | None = None,
        email: str | None = None,
        valid_forever: bool = False,
        valid_days: int = 3,
        valid_hours: int = 0,
        valid_minutes: int = 0,
        notify: bool | None = None,
        notify_to: constants.NotifyToArgs | None = None,
        is_enabled: bool = True,
        # status: bool,
        # created_at: str,
        # expire_at: str,
    ) -> Response:
        """Create a new guest visitor of a portal.

        Args:
            portal_id (str): Portal ID of the splash page
            name (str): Visitor account name
            password (str): Password
            company_name (str): Company name of the visitor
            phone (str): Phone number of the visitor; Format [+CountryCode][PhoneNumber]
            email (str): Email address of the visitor
            valid_forever (bool): Visitor account will not expire when this is set to true
            valid_days (int): Account validity in days
            valid_hours (int): Account validity in hours
            valid_minutes (int): Account validity in minutes
            notify (bool): Flag to notify the password via email or number
            notify_to (str): Notify to email or phone. Defualt is phone when it is provided
                otherwise email.  Valid Values: email, phone
            is_enabled (bool): Enable or disable the visitor account
            # id (str): NA for visitor post/put method. ID of the visitor
            # status (bool): This field provides status of the account. Returns true when enabled and
            #     not expired. NA for visitor post/put method. This is optional fields.
            # created_at (str): This field indicates the created date timestamp value. It is generated
            #     while creating visitor. NA for visitor post/put method. This is optional field.
            # expire_at (str): This field indicates expiry time timestamp value. It is generated based
            #     on the valid_till value and created_at time. NA for visitor post/put method. This is
            #     optional field

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors"

        user_data = {
            'phone': phone,
            'email': email
        }
        # API requires *both* phone and email, when either is provided, but they can be None/null

        json_data = {
            'name': name,
            'company_name': company_name,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_forever,
            'valid_till_days': valid_days,
            'valid_till_hours': valid_hours,
            'valid_till_minutes': valid_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password
        }
        json_data = utils.strip_none(json_data)
        if phone or email:
            json_data["user"] = user_data

        return await self.session.post(url, json_data=json_data)

    async def update_guest(
        self,
        portal_id: str,
        visitor_id: str,
        name: str,
        company_name: str = None,
        phone: str = None,
        email: str = None,
        is_enabled: bool = None,
        valid_till_no_limit: bool = None,
        valid_till_days: int = None,
        valid_till_hours: int = None,
        valid_till_minutes: int = None,
        notify: bool = None,
        notify_to: Literal["email", "phone"] = None,
        password: str = None,
    ) -> Response:
        """Update guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal
            name (str): Visitor account name
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

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        json_data = {
            'name': name,
            'company_name': company_name,
            'is_enabled': is_enabled,
            'valid_till_no_limit': valid_till_no_limit,
            'valid_till_days': valid_till_days,
            'valid_till_hours': valid_till_hours,
            'valid_till_minutes': valid_till_minutes,
            'notify': notify,
            'notify_to': notify_to,
            'password': password
        }
        if any([phone, email]):
            json_data["user"] = {
                'phone': phone,
                'email': email,
            }

        return await self.session.put(url, json_data=json_data)

    async def delete_guest(
        self,
        portal_id: str,
        guest_id: str,
    ) -> Response:
        """Delete guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            guest_id (str): ID of Guest associated with the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{guest_id}"

        return await self.session.delete(url)

    # TODO build command
    async def get_guest_summary(
        self,
        ssids: list[str] | str,
        days: int = 28,
    ) -> Response:
        """Get summary statistics.

        Args:
            ssid (str): A comma separated list of SSIDs for which session data is required
            days (optional, int): Num of days for which session data is required  Valid Values: 1, 7, 28
                Default: 28

        Raises:
            ValueError: If days is not valid (1, 7, 28).

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/summary"
        ssids = utils.listify(ssids)
        ssids = ",".join(ssids)
        if days and days not in [1, 7, 28]:
            return ValueError(f"days must be one of 1, 7, or 28.  {days} is invalid")

        params = {
            'days': days,
            'ssid': ssids
        }

        return await self.session.get(url, params=params)