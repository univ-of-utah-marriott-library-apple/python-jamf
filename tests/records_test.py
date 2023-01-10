# -*- coding: utf-8 -*-
# pylint: disable=relative-beyond-top-level, missing-function-docstring
# pylint: disable=missing-class-docstring, missing-module-docstring, invalid-name

"""
test_records
Test the Jamf object classes
"""

import logging
import unittest

from jamf import records, exceptions

HOSTNAME = "http://localhost"
USERNAME = "python-jamf"
PASSWORD = "secret"

BAD_HOSTNAME = "http://asdfasdf"
BAD_HOSTNAME_PORT = "http://github:80"
BAD_USERNAME = "asdf"


def get_creds():
    if "JAMF_HOSTNAME" in os.environ:
        hostname = os.environ["JAMF_HOSTNAME"]
    else:
        hostname = HOSTNAME
    if "JAMF_USERNAME" in os.environ:
        username = os.environ["JAMF_USERNAME"]
    else:
        username = USERNAME
    if "JAMF_PASSWORD" in os.environ:
        password = os.environ["JAMF_PASSWORD"]
    else:
        password = PASSWORD
    return (hostname, username, password)




if __name__ == "__main__":
    unittest.main(verbosity=1)
