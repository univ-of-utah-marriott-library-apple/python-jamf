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
__version__ = "0.5.1"

import html.parser
import json
import logging
import logging.handlers
from datetime import datetime
from sys import stderr

import keyring
import requests

from . import config, convert

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
#         if response.status_code == 401:
#             print(
#                 f'{response.url} returned: "401 Unauthorized". Wrong username/password.'
#             )
#         elif response.status_code == 404:
#             print(
#                 f'{response.url} is "404 Not Found". Are you sure this is a Jamf Pro server?'
#             )
#         elif response.status_code == 503:
#             print(
#                 f'{response.url} returned: "503 Service Unavailable". Maybe the Jamf server is still starting.'
#             )
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
            raise SystemExit("No jamf hostname or credentials could be found.")
        while hostname[-1] == "/":
            hostname = hostname[:-1]
        self.hostname = hostname
        self.session = requests.Session()

    def get_token(self, old_token=None):
        session = requests.Session()
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
        if self.save_token_in_keyring:
            keyring.set_password(self.hostname, "api-token", json_data["token"])
            keyring.set_password(self.hostname, "api-expires", json_data["expires"])
        return json_data["token"]

    def revoke_token(self):
        try:
            keyring.delete_password(self.hostname, "api-token")
        except:
            stderr.write("Warning: couldn't delete token\n")
            pass
        try:
            keyring.delete_password(self.hostname, "api-expires")
        except:
            stderr.write("Warning: couldn't delete token expire date\n")
            pass

    def set_session_auth(self):
        """set the session Jamf Pro API token or basic auth"""
        token = None
        # Check for old token and renew it if found
        if self.save_token_in_keyring:
            saved_token = keyring.get_password(self.hostname, "api-token")
            expires = keyring.get_password(self.hostname, "api-expires")
            if saved_token and expires:
                try:
                    expires = expires[
                        :-1
                    ]  # remove the Z because in case there's no "."
                    deadline = datetime.strptime(
                        expires.split(".")[0], "%Y-%m-%dT%H:%M:%S"
                    )
                    if deadline > datetime.utcnow():
                        token = self.get_token(old_token=saved_token)
                except ValueError as e:
                    stderr.write(
                        f"Error getting saved token: {e}\n"
                        f"expire string 1: {expires}\n"
                        f"expire string 2: {expires.split('.')[0]}\n"
                        f"Will try to continue.\n"
                    )
        # Get a new token
        if not token:
            token = self.get_token()
        # Only use token if jamf version is >= 10.35.0
        use_token = False
        if token:
            session = requests.Session()
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
            self.log.debug("xml data: %s", data)
        session_method = getattr(session, method)
        try:
            response = session_method(url, data=data)
        except requests.exceptions.ConnectionError as error:
            raise SystemExit(f"Could not connect to {self.hostname}\n{error}")
        if raw:
            return response
        if not response.ok:
            raise APIError(response)
        self.log.debug("response.text: %s", response.text)
        # return successful response data (usually: {'id': jssid})
        return response

    def get(self, endpoint, raw=False):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        self.set_session_auth()
        self.session.headers.update({"Accept": "application/xml"})
        url = f"{self.hostname}/JSSResource/{endpoint}"
        response = self._submit_request(self.session, "get", url, None, raw)
        return convert.xml_to_dict(response.text)

    def post(self, endpoint, data, raw=False):
        """
        Create new entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        self.set_session_auth()
        self.session.headers.update({"Accept": "application/xml"})
        url = f"{self.hostname}/JSSResource/{endpoint}"
        response = self._submit_request(self.session, "post", url, data, raw)
        return convert.xml_to_dict(response.text)

    def put(self, endpoint, data, raw=False):
        """
        Update existing entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        self.set_session_auth()
        self.session.headers.update({"Accept": "application/xml"})
        url = f"{self.hostname}/JSSResource/{endpoint}"
        response = self._submit_request(self.session, "put", url, data, raw)
        return convert.xml_to_dict(response.text)

    def delete(self, endpoint, raw=False):
        """
        Delete entry on JSS

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw  <bool>:     return requests.Response obj (skip errors)

        :returns <dict|requests.Response>:
        """
        self.set_session_auth()
        self.session.headers.update({"Accept": "application/xml"})
        url = f"{self.hostname}/JSSResource/{endpoint}"
        response = self._submit_request(self.session, "delete", url, None, raw)
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
