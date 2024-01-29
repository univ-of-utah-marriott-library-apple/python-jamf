# -*- coding: utf-8 -*-

"""
Tests for python_jamf.config
"""

__author__ = "James Reynolds"
__email__ = "reynolds@biology.utah.edu"
__copyright__ = "Copyright (c) 2022 University of Utah"
__license__ = "MIT"
__version__ = "0.2.0"

import logging
import unittest
from os import path, remove

import keyring

from python_jamf.config import Config
from python_jamf.exceptions import JamfConfigError

TOKEN_KEY = "python-jamf-token"
EXPIRE_KEY = "python-jamf-expires"


class ConfigTests(unittest.TestCase):
    """
    Test the config class
    """

    @classmethod
    def setUpClass(cls):
        cls.config_path = "/tmp/jamf.config.test.alt.plist"
        cls.hostname = "https://localhost"
        cls.username = "test"
        cls.password = "test"
        cls.config = Config(
            config_path=cls.config_path,
            hostname=cls.hostname,
            username=cls.username,
            password=cls.password,
            prompt=False,
        )

    def test_parameters(self):
        """
        test parameters
        """
        self.assertEqual(self.config.config_path, self.config_path)
        self.assertEqual(self.config.hostname, self.hostname)
        self.assertEqual(self.config.username, self.username)
        self.assertEqual(self.config.password, self.password)

    def test_save(self):
        """
        test save pref
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.config.save()
        self.assertTrue(path.exists(self.config_path))
        remove(self.config_path)

    def test_load(self):
        """
        test load pref
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.config.save()
        self.config.load()
        self.assertEqual(self.config.hostname, self.hostname)
        self.assertEqual(self.config.username, self.username)
        self.assertEqual(self.config.password, self.password)
        remove(self.config_path)

    def test_config_missing_load(self):
        """
        test config missing load
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.assertRaises(JamfConfigError, self.config.load)

    def test_token(self):
        """
        test token save, load, revoke
        """
        TEMP_TOKEN = "BlaBlaBla"
        TEMP_EXPIRE = "2022-05-12T00:28:08.131Z"
        self.config.save_new_token(TEMP_TOKEN, TEMP_EXPIRE)
        self.config.load_token()
        self.assertEqual(keyring.get_password(self.hostname, TOKEN_KEY), TEMP_TOKEN)
        self.assertEqual(keyring.get_password(self.hostname, EXPIRE_KEY), TEMP_EXPIRE)
        self.config.revoke_token()
        self.assertIsNone(keyring.get_password(self.hostname, TOKEN_KEY))
        self.assertIsNone(keyring.get_password(self.hostname, EXPIRE_KEY))

    def test_config_missing_no_prompt(self):
        """
        test config missing no prompt
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.assertRaises(JamfConfigError, lambda: Config(config_path=self.config_path))

    def test_malformed_config(self):
        """
        test malformed config
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        # write bad file
        f = open(self.config_path, "w")
        f.write("This isn't plist")
        f.close()
        self.assertRaises(JamfConfigError, lambda: Config(config_path=self.config_path))

    def test_bad_hostname(self):
        """
        test bad hostname
        """
        self.assertRaises(
            JamfConfigError,
            lambda: Config(
                config_path=self.config_path,
                hostname="fail",
                username="test",
                password="test",
                prompt=False,
            ),
        )

    def test_http(self):
        """
        test http hostname
        """
        Config(
            config_path=self.config_path,
            hostname="http://localhost",
            username="test",
            password="test",
            prompt=False,
        )

    def test_https(self):
        """
        test https hostname
        """
        Config(
            config_path=self.config_path,
            hostname="https://localhost",
            username="test",
            password="test",
            prompt=False,
        )

    def test_reset(self):
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.config.save()
        self.config.save_new_token("BlaBlaBla", "2022-05-12T00:28:08.131Z")
        self.assertTrue(path.exists(self.config_path))
        self.assertEqual(
            keyring.get_password(self.hostname, self.username), self.password
        )
        self.config.reset()
        self.assertIsNone(keyring.get_password(self.hostname, TOKEN_KEY))
        self.assertIsNone(keyring.get_password(self.hostname, EXPIRE_KEY))
        self.assertIsNone(keyring.get_password(self.hostname, self.username))
        self.assertTrue(not path.exists(self.config_path))


if __name__ == "__main__":
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.FATAL, format=fmt)
    unittest.main(verbosity=1)
