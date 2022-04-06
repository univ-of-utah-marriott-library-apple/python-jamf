#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSS API
Modifications by Tony Williams (tonyw@honestpuck.com) (ARW)
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "0.5.0"

import html.parser
import logging
import logging.handlers
import pathlib
from os import path, _exit
import plistlib
import subprocess
import requests
from sys import exit
import keyring
from datetime import datetime
import json
from . import convert
from . import config

LOGLEVEL = logging.INFO

# pylint: disable=unnecessary-pass
class Error(Exception):
    """just passing through"""

    pass


# pylint: disable=super-init-not-called
class APIError(Error):
    """Error in our call"""

    def __init__(self, response):
        self.response = response
        err = parse_html_error(response.text)
        self.message = ": ".join(err) or "failed"
        print(
            f"{response}: {response.request.method} - {response.url}: \n{self.message}"
        )

    def __getattr__(self, attr):
        """
        missing attributes fallback on response
        """
        return getattr(self.response, attr)

    def __str__(self):
        rsp = self.response
        return f"{rsp}: {rsp.request.method} - {rsp.url}: {self.message}"


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
        conf = config.Config(
            config_path=config_path,
            hostname=hostname,
            username=username,
            password=password,
            prompt=prompt,
        )
        hostname = hostname or conf.hostname
        self.username = username or conf.username
        self.password = password or conf.password
        if conf.password:
            self.save_token_in_keyring = True
        else:
            self.save_token_in_keyring = False

        if not hostname and not self.username and not self.password:
            print("No jamf hostname or credentials could be found.")
            exit(1)
        if hostname[-1] == "/":
            self.url = f"{hostname}JSSResource"
            self.hostname = hostname[:-1]
        else:
            self.url = f"{hostname}/JSSResource"
            self.hostname = hostname
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/xml"})

    def get_token(self, old_token=None):
        session = requests.Session()
        if old_token:
            session.headers.update({"Authorization": f"Bearer {old_token}"})
            url = f"{self.hostname}/api/v1/auth/keep-alive"
        else:
            session.auth = ( self.username, self.password )
            url = f"{self.hostname}/api/v1/auth/token"
        response = session.post(url)
        if response.status_code != 200:
            print("Server did not return a bearer token")
            return(None)
        try:
            json_data = json.loads(response.text)
        except Exception as e:
            print("Couldn't parse bearer token json")
            return(None)
        if self.save_token_in_keyring:
            keyring.set_password(self.hostname, "api-token", json_data['token'])
            keyring.set_password(self.hostname, "api-expires", json_data['expires'])
        return(json_data['token'])

    def set_session_auth(self):
        """set the session Jamf Pro API token or basic auth"""
        token = None
        # Check for old token and renew it if found
        if self.save_token_in_keyring:
            saved_token = keyring.get_password(self.hostname, "api-token")
            expires = keyring.get_password(self.hostname, "api-expires")
            if saved_token:
                deadline = datetime.strptime(expires.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                if deadline > datetime.utcnow():
                    token = self.get_token(old_token=saved_token)
        # Get a new token
        if not token:
            token = self.get_token()
        # Only use token if jamf version is >= 10.35.0
        use_token = False
        if token:
            session = requests.Session()
            url = f"{self.hostname}/api/v1/jamf-pro-version"
            session.headers.update({"Authorization": f"Bearer {token}"})
            response = session.get(url)
            if response.status_code == 200:
                try:
                    json_data = json.loads(response.text)
                    version = json_data['version'].split("-")[0]
                    v1 = tuple(map(int, (version.split("."))))
                    v2 = tuple(map(int, (10, 35, 0)))
                    if v1 >= v2:
                        use_token = True
                except Exception as e:
                    print("Couldn't parse jamf version json")
        if use_token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        else:
            self.session.auth = (self.username, self.password)

    def get(self, endpoint, raw=False):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("getting: %s", endpoint)
        self.set_session_auth()
        try:
            response = self.session.get(url)
        except requests.exceptions.ConnectionError as error:
            print(error)
            exit(1)

        if raw:
            return response
        if not response.ok:
            if response.status_code == 401:
                print("401 Unauthorized")
                exit(1)
            raise APIError(response)
        return convert.xml_to_dict(response.text)

    def post(self, endpoint, data, raw=False):
        """
        Create new entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("creating: %s", endpoint)
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
        self.set_session_auth()
        try:
            response = self.session.post(url, data=data)
        except requests.exceptions.ConnectionError as error:
            print(error)
            exit(1)

        if raw:
            return response
        if not response.ok:
            if response.status_code == 401:
                print("401 Unauthorized")
                exit(1)
            raise APIError(response)

        # return successfull response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def put(self, endpoint, data, raw=False):
        """
        Update existing entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("updating: %s", endpoint)
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
        self.set_session_auth()
        try:
            response = self.session.put(url, data=data)
        except requests.exceptions.ConnectionError as error:
            print(error)
            exit(1)

        if raw:
            return response
        if not response.ok:
            if response.status_code == 401:
                print("401 Unauthorized")
                exit(1)
            raise APIError(response)

        # return successful response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def delete(self, endpoint, raw=False):
        """
        Delete entry on JSS

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw  <bool>:     return requests.Response obj (skip errors)

        :returns <dict|requests.Response>:
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("getting: %s", endpoint)
        self.set_session_auth()
        try:
            response = self.session.delete(url)
        except requests.exceptions.ConnectionError as error:
            print(error)
            exit(1)

        if raw:
            return response
        if not response.ok:
            if response.status_code == 401:
                print("401 Unauthorized")
                exit(1)
            raise APIError(response)

        # return successful response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def __del__(self):
        if self.session:
            self.log.debug("closing session")
            self.session.close()


# pylint: disable=too-few-public-methods, abstract-method
class _DummyTag:
    """
    Minimal mock implementation of bs4.element.Tag (only has text attribute)

    >>> eg = _DummyTag('some text')
    >>> eg.text
    'some text'
    """

    def __init__(self, text):
        self.text = text


class JSSErrorParser(html.parser.HTMLParser):
    """
    Minimal mock implementation of bs4.BeautifulSoup()

    >>> [t.text for t in JSSErrorParser(html).find_all('p')]
    ['Unauthorized', 'The request requires user authentication',
     'You can get technical details here. {...}']
    """

    def __init__(self, _html):
        super().__init__()
        self._data = {}
        if _html:
            self.feed(_html)

    def find_all(self, tag):
        """
        Minimal mock implemetation of BeautifulSoup(html).find_all(tag)

        :param tag <str>:   html tag
        :returns <list>:    list of _DummyTags
        """
        return self._data.get(tag, [])

    # pylint: disable=attribute-defined-outside-init
    def handle_data(self, data):
        """
        override HTMLParser().handle_data()
            (automatically called during HTMLParser.feed())
        creates _DummyTag with text attribute from data
        """
        self._dummytag = _DummyTag(data)

    def handle_endtag(self, tag):
        """
        override HTMLParser().handle_endtag()
            (automatically called during HTMLParser.feed())
        add _DummyTag object to dictionary based on tag
        """
        # only create new list if one doesn't already exist
        self._data.setdefault(tag, [])
        self._data[tag].append(self._dummytag)


def parse_html_error(error):
    """
    Get meaningful error information from JSS Error response HTML

    :param html <str>:  JSS HTML error text
    :returns <list>:    list of meaningful error strings
    """
    if not error:
        return []
    soup = JSSErrorParser(error)
    # e.g.: ['Unauthorized', 'The request requires user authentication',
    #        'You can get technical details here. (...)']
    # NOTE: get first two <p> tags from HTML error response
    #       3rd <p> is always 'You can get technical details here...'
    return [t.text for t in soup.find_all("p")][0:2]
