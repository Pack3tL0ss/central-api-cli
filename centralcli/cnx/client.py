# (C) Copyright 2025 Hewlett Packard Enterprise Development LP.
# MIT License
from __future__ import annotations

import oauthlib
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from pathlib import Path
from typing import Dict, Literal
from .. import config, log
import json
import pendulum



class NewCentralURLs:
    Authentication = {"OAUTH": "https://sso.common.cloud.hpe.com/as/token.oauth2"}

    GLP = {"BaseURL": "https://global.api.greenlake.hpe.com"}

    GLP_DEVICES = {
        "DEFAULT": "/devices/v1/devices",
        # full url requires {id} to be passed as param: /devices/v1/async-operations/{id}
        "GET_ASYNC": "/devices/v1/async-operations/",
    }

    GLP_SUBSCRIPTION = {
        "DEFAULT": "/subscriptions/v1/subscriptions",
        # full url requires {id} to be passed as param: /devices/v1/async-operations/{id}
        "GET_ASYNC": "/subscriptions/v1/async-operations/",
    }

    GLP_USER_MANAGEMENT = {
        "GET": "/identity/v1/users",
        # full url requires {id} to be passed as param: /identity/v1/users/{id}
        "GET_USER": "/identity/v1/users/",
        "POST": "/identity/v1/users",
        # full url requires {id} to be passed as param: /identity/v1/users/{id}
        "PUT": "/identity/v1/users/",
        # full url requires {id} to be passed as param: /identity/v1/users/{id}
        "DELETE": "/identity/v1/users/",
    }

    GLP_SERVICES = {
        "SERVICE_MANAGER": "/service-catalog/v1/service-managers",
        "SERVICE_MANAGER_PROVISIONS": "/service-catalog/v1/service-manager-provisions",
        "SERVICE_MANAGER_BY_REGION": "/service-catalog/v1/per-region-service-managers",
    }

urls = NewCentralURLs()


def _load_token_info(token_info: Path | str | Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    if isinstance(token_info, dict):
        return token_info
    if isinstance(token_info, str):
        token_info = Path(token_info)
    if not isinstance(token_info, Path):
        raise ValueError("Unexpected data type for token_info, should be a dict or the path (str or Path object) to a file containing the token_info")

    if not token_info.exists():
        raise FileNotFoundError(f"{str(token_info)} File not found.")

    return config.get_file_data(token_info)



class NewCentralBase:
    def __init__(self, token_info: Path | str | Dict[str, Dict[str, str]]):
        """Initialize NewCentralBase class.

        Args:
            token_info (Path | str | Dict[str, Dict[str, str]]): Dictionary containing token information for supported applications - new_central, glp.
                Can also be a string path to a YAML or JSON file with token information.
        """
        self.token_info = _load_token_info(token_info)
        self.token_resp = None
        self.central_info = None

        # auth is always through glp so access token is the same
        access_token = None
        for app in self.token_info:
            if "access_token" in self.token_info[app]:
                access_token = self.token_info[app]["access_token"]
                break

        if not access_token:
            _token = self.load_token_from_cache()
            if not _token:
                self.token_resp = self.get_access_token()
                access_token = self.token_resp.get("access_token")
            else:
                access_token = _token


        for app in self.token_info:
            self.token_info[app]["access_token"] = self.token_info.get("access_token") or access_token

        # Make NewCentralBase have some of the same attributes as pycentralv1
        self.central_info = {"token": {"access_token": access_token}}


    def load_token_from_cache(self) -> str | None:
        if config.cnx_tok_file and config.cnx_tok_file.exists():
            token_data = config.get_file_data(config.cnx_tok_file)
            if token_data is None:
                return

            if "expires" in token_data:
                if pendulum.now().int_timestamp - 300 > token_data["expires"]:
                    return # if cached token is within 5 mins of expiration we want to force a refresh

            return token_data.get("access_token")


    def get_access_token(self, app_name: Literal["new_central", "glp"] = "glp"):
        """
        Create a new access token for the specified application.

        This function generates a new access token using the client credentials
        for the specified application, updates the `self.token_info` dictionary
        with the new token, and optionally saves it to a file. The token is also
        returned.

        :param app_name: Name of the application. Supported applications: "new_central", "glp".
        :type app_name: str
        :return: Access token.
        :rtype: str
        :raises LoginError: If there is an error during token creation.
        :raises SystemExit: If invalid client credentials are provided.
        """
        client_id, client_secret = self._return_client_credentials(app_name)
        client = BackendApplicationClient(client_id)

        oauth = OAuth2Session(client=client)
        body = f'grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}'


        try:
            log.info(f"Attempting to create new token from {app_name}")
            token_dict = oauth.fetch_token(token_url=urls.Authentication["OAUTH"], body=body)

            if "access_token" in token_dict:
                log.info(
                    f"{app_name} Login Successful.. Obtained Access Token!"
                )
                self.central_info = {"token": {"access_token": token_dict["access_token"]}}
                if config.cnx_tok_file:
                    token_data = {
                        "access_token": token_dict["access_token"],
                        "expires": int(token_dict["expires_at"])
                    }
                    config.cnx_tok_file.write_text(json.dumps(token_data, indent=4))

                return token_dict
        except oauthlib.oauth2.rfc6749.errors.InvalidClientError:
            exit_msg = (
                "Invalid client_id or client_secret provided for "
                + app_name
                + ". Please provide valid credentials to create an access token."
            )
            exit(exit_msg)
        except Exception as e:
            error_msg = f"{e.__class__.__name__} occured fetching access token for {app_name}"
            log.exception(f"{error_msg}\n{e}")
            exit(error_msg)

    def handle_expired_token(self, app_name: Literal["new_central", "glp"] = "glp"):
        """
        Handle expired access token by creating a new one.

        :param app_name: Name of the application.
        :type app_name: str
        """
        log.info(f"{app_name} access Token has expired.", show=True)
        log.info("Handling Token Expiry...", show=True)
        client_id, client_secret = self._return_client_credentials(app_name)
        if any(credential is None for credential in [client_id, client_secret]):
            exit(
                f"Please provide client_id and client_secret in {app_name} required to generate an access token"
            )

        self.get_access_token(app_name)

    def _return_client_credentials(self, app_name):
        """
        Return client credentials for the specified application.

        :param app_name: Name of the application.
        :type app_name: str
        :return: Client ID and client secret.
        :rtype: tuple
        """
        app_token_info = self.token_info[app_name]
        if all(
            client_key in app_token_info
            for client_key in ("client_id", "client_secret")
        ):
            client_id = app_token_info["client_id"]
            client_secret = app_token_info["client_secret"]
            return client_id, client_secret
