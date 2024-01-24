#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python Jamf Exceptions
"""

__author__ = "James Reynolds"
__email__ = "reynolds@biology.utah.edu"
__copyright__ = "Copyright (c) 2022 University of Utah"
__license__ = "MIT"
__version__ = "0.1.2"

import html.parser


# pylint: disable=unnecessary-pass
class Error(Exception):
    """just passing through"""

    def __init__(self, message=None):
        self.message = message


class JamfConfigError(Error):
    """Error with the config or keyring"""


class JamfNoConnectionError(Error):
    """Error connecting to the server"""


class JamfRecordNotFound(Error):
    """Record not found"""


class JamfRecordInvalidPath(Error):
    """Record does not contain the path"""

    def __init__(self, message=None):
        self.message = message

    def __str__(self):
        return f"{self.message}"


class JamfConnectionError(Error):
    """Error connecting to the server"""

    def __init__(self, response, message=None):
        self.response = response
        self.message = message

    def __getattr__(self, attr):
        """
        missing attributes fallback on response
        """
        return getattr(self.response, attr)

    def __str__(self):
        rsp = self.response
        return f"{rsp}: {rsp.request.method} - {rsp.url}: {self.message}"


class JamfAuthenticationError(JamfConnectionError):
    """Error connecting to the server"""


class JamfUnknownClass(Error):
    """Error, unkwown class"""


class JamfAPISurprise(Error):
    """Error, unknown class"""


# pylint: disable=super-init-not-called
class APIError(Error):
    """Error in our call"""

    def __init__(self, response):
        self.response = response
        err = parse_html_error(response.text)
        self.message = ": ".join(err) or "failed"
        # if response.status_code == 401:
        #     print(
        #         f'{response.url} returned: "401 Unauthorized". Wrong username/password.'
        #     )
        # elif response.status_code == 404:
        #     print(
        #         f'{response.url} is "404 Not Found". Are you sure this is a Jamf Pro server?'
        #     )
        # elif response.status_code == 503:
        #     print(
        #         f'{response.url} returned: "503 Service Unavailable". Maybe the Jamf server is still starting.'
        #     )
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


## The following are used for tests only.


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
