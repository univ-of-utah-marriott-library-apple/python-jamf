#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSS API
Modifications by Tony Williams (tonyw@honestpuck.com) (ARW)
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.4.7"

import html.parser
import logging
import logging.handlers
import pathlib
from os import path, _exit
import plistlib
import subprocess
import requests
from sys import exit

from . import convert
from . import config

LOGLEVEL = logging.INFO

#pylint: disable=unnecessary-pass
class Error(Exception):
    """ just passing through """
    pass


#pylint: disable=super-init-not-called
class APIError(Error):
    """ Error in our call """
    def __init__(self, response):
        self.response = response
        err = parse_html_error(response.text)
        self.message = ": ".join(err) or 'failed'
        print(f"{response}: {response.request.method} - {response.url}: \n{self.message}")

    def __getattr__(self, attr):
        """
        missing attributes fallback on response
        """
        return getattr(self.response, attr)

    def __str__(self):
        rsp = self.response
        return f"{rsp}: {rsp.request.method} - {rsp.url}: {self.message}"


class Singleton(type):
    """ allows us to share a single object """
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

    def __init__(self,
                 config_path=None,
                 hostname=None,
                 username=None,
                 password=None,
                 prompt=True):
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
        conf = config.Config(config_path=config_path,
                             hostname=hostname,
                             username=username,
                             password=password,
                             prompt=prompt)
        hostname = hostname or conf.hostname
        username = username or conf.username
        password = password or conf.password

        if not hostname and not username and not password:
            print("No jamf hostname or credentials could be found.")
            exit(1)
        if hostname[-1] == '/':
            self.url = f"{hostname}JSSResource"
        else:
            self.url = f"{hostname}/JSSResource"
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({'Accept': 'application/xml'})

    def get(self, endpoint, raw=False):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("getting: %s", endpoint)
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

#pylint: disable=too-few-public-methods, abstract-method
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

    #pylint: disable=attribute-defined-outside-init
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
    return [t.text for t in soup.find_all('p')][0:2]
