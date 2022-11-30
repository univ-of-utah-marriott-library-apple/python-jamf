#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSS API
Modifications by Tony Williams (tonyw@honestpuck.com) (ARW)
"""

__author__ = "James Reynolds"
__email__ = "reynolds@biology.utah.edu"
__copyright__ = "Copyright (c) 2022 University of Utah"
__license__ = "MIT"
__version__ = "0.1.1"

# pylint: disable=unnecessary-pass
class Error(Exception):
    """just passing through"""

    pass

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


class JamfConfigError(Error):
    """Error with the config"""
