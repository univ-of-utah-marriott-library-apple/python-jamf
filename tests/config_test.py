# -*- coding: utf-8 -*-

"""
tests for jamf.config
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

from jamf.config import Config
from jamf.exceptions import JamfConfigError


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
        cls.pref = Config(
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
        self.assertEqual(self.pref.config_path, self.config_path)
        self.assertEqual(self.pref.hostname, self.hostname)
        self.assertEqual(self.pref.username, self.username)
        self.assertEqual(self.pref.password, self.password)

    def test_save(self):
        """
        test save pref
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.pref.save()
        self.assertTrue(path.exists(self.config_path))
        remove(self.config_path)

    def test_load(self):
        """
        test load pref
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.pref.save()
        self.pref.load()
        self.assertEqual(self.pref.hostname, self.hostname)
        self.assertEqual(self.pref.username, self.username)
        self.assertEqual(self.pref.password, self.password)
        remove(self.config_path)

    def test_config_missing_load(self):
        """
        test config missing load
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.assertRaises(JamfConfigError, self.pref.load)

    def test_reset(self):
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
        self.pref.save()
        self.assertTrue(path.exists(self.config_path))
        self.assertEqual(
            keyring.get_password(self.hostname, self.username), self.password
        )
        self.pref.reset()
        self.assertIsNone(keyring.get_password(self.hostname, self.username))
        self.assertTrue(not path.exists(self.config_path))

    def test_config_missing_no_prompt(self):
        """
        test config missing no prompt
        """
        if path.exists(self.config_path):
            remove(self.config_path)
            self.assertTrue(not path.exists(self.config_path))
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


if __name__ == "__main__":
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.FATAL, format=fmt)
    unittest.main(verbosity=1)
