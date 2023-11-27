# -*- coding: utf-8 -*-

"""
Tests for jamf.api
"""

__author__ = "James Reynolds"
__email__ = "reynolds@biology.utah.edu"
__copyright__ = "Copyright (c) 2022 University of Utah"
__license__ = "MIT"
__version__ = "0.1.0"

import logging
import os
import random
import string
import unittest

from python_jamf import api, exceptions

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


class TestHost(unittest.TestCase):
    def test_successful_connection(self):
        """
        Test successful connection
        """
        api.API._instances = {}
        hostname, username, password = get_creds()
        server = api.API(hostname=hostname, username=username, password=password)
        server.revoke_token()
        accounts = server.get("accounts")
        self.assertTrue("accounts" in accounts)

    def test_bad_prefs(self):
        """
        Test bad prefs
        """
        api.API._instances = {}
        self.assertRaises(
            exceptions.JamfConfigError,
            lambda: api.API(
                config_path="/var/false",
                hostname="",
                username="",
                password="",
                prompt=False,
            ),
        )

    def test_bad_hostname(self):
        """
        Test bad hostname
        """
        api.API._instances = {}
        hostname, username, password = get_creds()
        server = api.API(hostname=BAD_HOSTNAME, username=username, password=password)
        server.revoke_token()
        self.assertRaises(
            exceptions.JamfNoConnectionError, lambda: server.get("accounts")
        )

    def test_bad_port(self):
        """
        Test bad port
        """
        api.API._instances = {}
        hostname, username, password = get_creds()
        server = api.API(
            hostname=BAD_HOSTNAME_PORT, username=username, password=password
        )
        server.revoke_token()
        self.assertRaises(
            exceptions.JamfNoConnectionError, lambda: server.get("accounts")
        )

    def test_bad_username_password(self):
        """
        Test bad username password
        """
        api.API._instances = {}
        hostname, username, password = get_creds()
        server = api.API(hostname=hostname, username=BAD_USERNAME, password=password)
        server.revoke_token()
        self.assertRaises(
            exceptions.JamfAuthenticationError, lambda: server.get("accounts")
        )


class TestAPI(unittest.TestCase):
    def setUp(self):
        api.API._instances = {}
        hostname, username, password = get_creds()
        self.server = api.API(hostname=hostname, username=username, password=password)

    def test_get_token(self):
        """
        Test get_token
        """

        token = self.server.get_token()
        self.assertTrue(len(token) == 331)

    def test_revoke_token(self):
        """
        Test revoke_token
        """
        token1 = self.server.get_token()
        self.server.revoke_token()
        token2 = self.server.get_token()
        self.assertTrue(token1 != token2)

    def test_get_accounts(self):
        """
        Test get accounts
        """
        accounts = self.server.get("accounts")
        self.assertTrue("accounts" in accounts)

    def test_get_account_1(self):
        """
        Test get accounts
        """
        account = self.server.get("accounts/userid/1")
        self.assertTrue("account" in account)
        self.assertTrue("password_sha256" in account["account"])

    def test_crud(self):
        """
        Test CRUD: post new record, get, assert email, change email, put, get, assert email, delete, assert not found
        """
        name = "python-jamf-" + "".join(random.choices(string.ascii_letters, k=16))
        data = {
            "account": {
                "access_level": "Full Access",
                "directory_user": "false",
                "email": "python@jamf.jamf",
                "email_address": "python@jamf.jamf",
                "enabled": "Disabled",
                "force_password_change": "false",
                "full_name": "Python-Jamf",
                "name": name,
                "password": "probably-not-a-good-test",
                "privilege_set": "Custom",
                "privileges": {
                    "casper_admin": None,
                    "casper_remote": None,
                    "jss_actions": None,
                    "jss_objects": None,
                    "jss_settings": None,
                    "recon": None,
                },
            }
        }
        self.server.post("accounts/userid/0", data)
        account = self.server.get(f"accounts/username/{name}")
        self.assertTrue(account["account"]["email"] == "python@jamf.jamf")
        account["account"]["email"] = "test@test.test"
        self.server.put(f"accounts/userid/{account['account']['id']}", account)
        account = self.server.get(f"accounts/username/{name}")
        self.assertTrue(account["account"]["email"] == "test@test.test")
        self.server.delete(f"accounts/username/{name}")
        self.assertRaises(
            exceptions.JamfRecordNotFound,
            lambda: self.server.get(f"accounts/username/{name}"),
        )


if __name__ == "__main__":
    FMT = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=FMT)
    unittest.main(verbosity=1)
