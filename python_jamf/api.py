#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python Jamf Classic API
Author: Sam Forester
Contributors:
James Reynolds (reynolds@biology.utah.edu)
Tony Williams (tonyw@honestpuck.com) (ARW)
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "0.5.2"

import json
import logging

import requests

from . import config, convert, exceptions

LOGLEVEL = logging.INFO


class Singleton(type):
    """allows us to share a single object"""

    _instances = {}

    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class API(metaclass=Singleton):
    """
    Class for making api calls to JSS
    """

    session = False

    def __init__(
        self, config_path=None, hostname=None, username=None, password=None, prompt=True
    ):
        """
        Create requests.Session with JSS address and authentication

        :param config_path <str>:    Path to file containing config. If it
                                     starts with '~' character we pass it
                                     to expanduser.
        :param hostname <str>:       Hostname of server
        :param username <str>:       username for server
        :param password <str>:       password for server
        :param prompt <bool>:        Allow the script to prompt if any info is missing
        """
        self.log = logging.getLogger(f"{__name__}.API")
        self.log.setLevel(LOGLEVEL)
        # Load Prefs and Init session
        self.config = config.Config(
            config_path=config_path,
            hostname=hostname,
            username=username,
            password=password,
            prompt=prompt,
        )
        hostname = hostname or self.config.hostname
        self.username = username or self.config.username
        self.password = password or self.config.password
        if self.config.password:
            self.save_token_in_keyring = True
        else:
            self.save_token_in_keyring = False

        if not hostname and not self.username and not self.password:
            raise exceptions.JamfConfigError(
                "No jamf hostname or credentials could be found."
            )
        while hostname[-1] == "/":
            hostname = hostname[:-1]
        self.hostname = hostname
        self.session = requests.Session()

    def get_token(self, old_token=None):
        with requests.Session() as session:
            if old_token:
                session.headers.update({"Authorization": f"Bearer {old_token}"})
                url = f"{self.hostname}/api/v1/auth/keep-alive"
            else:
                session.auth = (self.username, self.password)
                url = f"{self.hostname}/api/v1/auth/token"
            response = self._submit_request(session, "post", url)
            if response.status_code != 200:
                print("Server did not return a bearer token")
                return None
            try:
                json_data = json.loads(response.text)
            except Exception:
                print("Couldn't parse bearer token json")
                return None
            if self.config.password:
                self.config.save_new_token(json_data["token"], json_data["expires"])
            return json_data["token"]

    def revoke_token(self):
        self.config.revoke_token()

    def _set_session_auth(self):
        """set the session Jamf Pro API token or basic auth"""
        token = None
        # Check for old token and renew it if found
        if self.config.password:
            self.config.load_token()
            if self.config.expired:
                token = self.get_token(old_token=self.config.token)
        # Get a new token
        if not token:
            token = self.get_token()
        # Only use token if jamf version is >= 10.35.0
        use_token = False
        if token:
            with requests.Session() as session:
                url = f"{self.hostname}/api/v1/jamf-pro-version"
                session.headers.update({"Authorization": f"Bearer {token}"})
                response = self._submit_request(session, "get", url)
                if response.status_code == 200:
                    try:
                        json_data = json.loads(response.text)
                        version = json_data["version"].split("-")[0]
                        v1 = tuple(map(int, (version.split("."))))
                        v2 = tuple(map(int, (10, 35, 0)))
                        if v1 >= v2:
                            use_token = True
                    except Exception:
                        print("Couldn't parse jamf version json")
        if use_token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.auth = (self.username, self.password)

    def _submit_request(self, session, method, url, data=None, raw=False):
        """
        Generic request

        :param method <str>:   get | post | put | delete
        :param url <str>: API url (e.g. "http://server/JSSResource/policies/id/1")
        :param data <dict>:    data submitted (get and delete ignore this)
        :param raw <bool>:     return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        self.log.debug(f"{method}: {url}")
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
            self.log.debug("xml data: %s", data)
        session_method = getattr(session, method)
        try:
            response = session_method(url, data=data)
        except requests.exceptions.ConnectionError as error:
            raise exceptions.JamfNoConnectionError(
                f"Could not connect to {self.hostname}\n{error}"
            )
        if raw:
            return response
        if not response.ok:
            if response.status_code == 401:
                raise exceptions.JamfAuthenticationError(response, "Bad auth")
            elif response.status_code == 404:
                raise exceptions.JamfRecordNotFound(response, "Not Found")
            else:
                raise exceptions.JamfConnectionError(
                    response, f"Error: {response.status_code}"
                )
        self.log.debug("response.text: %s", response.text)
        # return successful response data (usually: {'id': jssid})
        return response

    def _crud(self, method, endpoint, data=None, raw=False, plurals=None):
        self._set_session_auth()
        self.session.headers.update({"Accept": "application/xml"})
        url = f"{self.hostname}/JSSResource/{endpoint}"
        response = self._submit_request(self.session, method, url, data, raw)
        convert_data = convert.xml_to_dict(response.text,plurals)
        self.log.debug("converted data: %s", convert_data)
        return convert_data

    def get(self, endpoint, raw=False, plurals=None):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        return self._crud("get", endpoint, None, raw, plurals=plurals)

    def post(self, endpoint, data, raw=False):
        """
        Create new entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        return self._crud("post", endpoint, data, raw)

    def put(self, endpoint, data, raw=False):
        """
        Update existing entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        return self._crud("put", endpoint, data, raw)

    def delete(self, endpoint, raw=False):
        """
        Delete entry on JSS

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw  <bool>:     return requests.Response obj (skip errors)

        :returns <dict|requests.Response>:
        """
        return self._crud("delete", endpoint, None, raw)

    def __del__(self):
        if self.session:
            self.log.debug("closing session")
            self.session.close()
