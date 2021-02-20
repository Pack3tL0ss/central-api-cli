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

    async def guest_get_portals(self, sort: str = '+name', offset: int = 0, limit: int = 100) -> Response:
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

    async def guest_create_portal(self, name: str, auth_type: str,
                                  username_password_enabled: bool, registration_enabled: bool,
                                  verify_registration: bool, bypass_cna_policy: bool,
                                  cna_policy: str, register_accept_email: bool,
                                  register_accept_phone: bool, free_wifi_duration: int,
                                  self_reg_account_unlimited: bool,
                                  self_reg_account_expire_days: int,
                                  self_reg_account_expire_hours: int,
                                  self_reg_account_expire_minutes: int, login_button_title: str,
                                  whitelist_urls: List[str], custom_username_label: str,
                                  custom_password_label: str, custom_sender_message: str,
                                  custom_verification_message: str,
                                  custom_registration_message: str, custom_pwd_reset_message: str,
                                  auth_sources: list, facebook_wifi_configure_url: str,
                                  facebook_wifi_gateway_id: str, redirect_url: str,
                                  auth_failure_message: str, days: int, hours: int, minutes: int,
                                  mac_caching_enabled: bool, is_shared: bool,
                                  simultaneous_login_limit: int, daily_usage_limit: str,
                                  by_hours: int, by_minutes: int, data_type: str, data: int,
                                  background_color: str, button_color: str,
                                  header_fill_color: str, page_font_color: str, logo_name: str,
                                  logo: str, background_image_name: str, background_image: str,
                                  max_columns: int, page_title: str, welcome_text: str,
                                  terms_condition: str, display_terms_checkbox: bool,
                                  display_term_options: str, ad_url: str, login_image_name: str,
                                  ad_image: str, is_config_associated: bool, capture_url: str,
                                  override_common_name: str, override_common_name_enabled: bool) -> Response:
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

    async def guest_preview_portal(self, portal_id: str) -> Response:
        """Get preview url of guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/preview/{portal_id}"

        return await self.get(url)

    async def guest_get_portal(self, portal_id: str) -> Response:
        """Get guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.get(url)

    async def guest_update_portal(self, portal_id: str, name: str, auth_type: str,
                                  username_password_enabled: bool, registration_enabled: bool,
                                  verify_registration: bool, bypass_cna_policy: bool,
                                  cna_policy: str, register_accept_email: bool,
                                  register_accept_phone: bool, free_wifi_duration: int,
                                  self_reg_account_unlimited: bool,
                                  self_reg_account_expire_days: int,
                                  self_reg_account_expire_hours: int,
                                  self_reg_account_expire_minutes: int, login_button_title: str,
                                  whitelist_urls: List[str], custom_username_label: str,
                                  custom_password_label: str, custom_sender_message: str,
                                  custom_verification_message: str,
                                  custom_registration_message: str, custom_pwd_reset_message: str,
                                  auth_sources: list, facebook_wifi_configure_url: str,
                                  facebook_wifi_gateway_id: str, redirect_url: str,
                                  auth_failure_message: str, days: int, hours: int, minutes: int,
                                  mac_caching_enabled: bool, is_shared: bool,
                                  simultaneous_login_limit: int, daily_usage_limit: str,
                                  by_hours: int, by_minutes: int, data_type: str, data: int,
                                  background_color: str, button_color: str,
                                  header_fill_color: str, page_font_color: str, logo_name: str,
                                  logo: str, background_image_name: str, background_image: str,
                                  max_columns: int, page_title: str, welcome_text: str,
                                  terms_condition: str, display_terms_checkbox: bool,
                                  display_term_options: str, ad_url: str, login_image_name: str,
                                  ad_image: str, is_config_associated: bool, capture_url: str,
                                  override_common_name: str, override_common_name_enabled: bool) -> Response:
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

    async def guest_delete_portal(self, portal_id: str) -> Response:
        """Delete guest portal profile.

        Args:
            portal_id (str): Portal ID of the splash page

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}"

        return await self.delete(url)

    async def guest_get_visitors(self, portal_id: str, sort: str = '+name', filter_by: str = None,
                                 filter_value: str = None, offset: int = 0, limit: int = 100) -> Response:
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
            'filter_value': filter_value
        }

        return await self.get(url, params=params)

    async def guest_create_visitor(self, portal_id: str, name: str, id: str, company_name: str,
                                   phone: str, email: str, is_enabled: bool,
                                   valid_till_no_limit: bool, valid_till_days: int,
                                   valid_till_hours: int, valid_till_minutes: int, notify: bool,
                                   notify_to: str, password: str, status: bool, created_at: str,
                                   expire_at: str) -> Response:
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

    async def guest_get_visitor(self, portal_id: str, visitor_id: str) -> Response:
        """Get guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        return await self.get(url)

    async def guest_update_visitor(self, portal_id: str, visitor_id: str, name: str, id: str,
                                   company_name: str, phone: str, email: str, is_enabled: bool,
                                   valid_till_no_limit: bool, valid_till_days: int,
                                   valid_till_hours: int, valid_till_minutes: int, notify: bool,
                                   notify_to: str, password: str, status: bool, created_at: str,
                                   expire_at: str) -> Response:
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

    async def guest_delete_visitor(self, portal_id: str, visitor_id: str) -> Response:
        """Delete guest visitor account.

        Args:
            portal_id (str): Portal ID of the splash page
            visitor_id (str): Visitor ID of the portal

        Returns:
            Response: CentralAPI Response object
        """
        url = f"/guest/v1/portals/{portal_id}/visitors/{visitor_id}"

        return await self.delete(url)

    async def guest_get_sessions(self, essid_name: str, portal_id: str,
                                 sort: str = '+account_name', ssid_name: str = None,
                                 filter_by: str = None, filter_value: str = None, offset: int = 0,
                                 limit: int = 100) -> Response:
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
            'filter_value': filter_value
        }

        return await self.get(url, params=params)

    async def guest_get_wlans(self) -> Response:
        """Get all guest wlans.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/wlans"

        return await self.get(url)

    async def guest_get_enabled(self) -> Response:
        """Check if guest is enabled for current user.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/enabled"

        return await self.get(url)

    async def guest_get_re_provision(self) -> Response:
        """Provision cloud guest for current customer.

        Returns:
            Response: CentralAPI Response object
        """
        url = "/guest/v1/reprovision"

        return await self.post(url)

    async def guest_wifi4eu_status(self, network_id: str, lang_code: str) -> Response:
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