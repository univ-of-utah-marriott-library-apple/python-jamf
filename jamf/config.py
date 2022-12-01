# -*- coding: utf-8 -*-

"""
Configuration for python-jamf
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.2.5"

import getpass
import logging
import plistlib
from os import path, remove

import keyring

from .exceptions import JamfConfigError

LINUX_PREFS_TILDA = "~/.edu.utah.mlib.jamfutil.plist"
MACOS_PREFS_TILDA = "~/Library/Preferences/edu.utah.mlib.jamfutil.plist"
AUTOPKG_PREFS_TILDA = "~/Library/Preferences/com.github.autopkg.plist"
JAMF_PREFS = "/Library/Preferences/com.jamfsoftware.jamf.plist"
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Config:
    def __init__(
        self,
        config_path=None,
        hostname=None,
        username=None,
        password=None,
        prompt=False,
    ):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.prompt = prompt
        self.hostname = hostname
        self.username = username
        self.password = password
        self.config_path = resolve_config_path(config_path)
        if not self.hostname and not self.username and not self.password:
            self.load()
        # Prompt for any missing prefs
        if self.prompt:
            if not self.hostname:
                self.hostname = prompt_hostname()
            if not self.username:
                self.username = input("Username: ")
            if not self.password:
                self.password = getpass.getpass()
        elif not self.hostname and not self.username and not self.password:
            raise JamfConfigError(
                "No jamf config file could be found and prompt is off."
            )
        if not self.hostname:
            raise JamfConfigError("Config failed to obtain a hostname.")
        if not self.username:
            raise JamfConfigError("Config failed to obtain a username.")
        if not self.password:
            raise JamfConfigError("Config failed to obtain a password.")
        if not self.hostname.startswith("https://") and not self.hostname.startswith(
            "http://"
        ):
            raise JamfConfigError(
                f"Hostname ({self.hostname}) does not start with 'https://' or 'http://'"
            )

    def load(self):
        if path.exists(self.config_path):
            fptr = open(self.config_path, "rb")
            prefs = plistlib.load(fptr)
            fptr.close()
            if "JSSHostname" in prefs:
                if "Credentials" in prefs:
                    cmessage = f"""
ATTENTION
To improve security with storing credentials used with the jctl tool, we have
deprecated the use of a property list file for storing configuration
information and have migrated to use the Python keyring library provides an
easy way to access the system keyring service from python. It can be used with
the macOS Keychain and Linux KWallet.

Please delete the the configuration at {self.config_path} and recreate it using
the "./jamf/setconfig.py" script.
"""
                    raise JamfConfigError(cmessage)
                self.hostname = prefs["JSSHostname"]
                self.username = prefs["Username"]
                self.password = keyring.get_password(self.hostname, self.username)
            elif "JSS_URL" in prefs:
                self.hostname = prefs["JSS_URL"]
                self.username = prefs["API_USERNAME"]
                self.password = prefs["API_PASSWORD"]
            elif "jss_url" in prefs:
                self.hostname = prefs["jss_url"]
                # No auth in that file
        else:
            raise JamfConfigError(f"Config file does not exist: {self.config_path}")

    def save(self):
        keyring.set_password(self.hostname, self.username, self.password)
        data = {"JSSHostname": self.hostname, "Username": self.username}
        self.log.info(f"saving: {self.config_path}")
        fptr = open(self.config_path, "wb")
        plistlib.dump(data, fptr)
        fptr.close()

    def reset(self):
        keyring.delete_password(self.hostname, self.username)
        remove(self.config_path)


def resolve_config_path(config_path=None):
    if not config_path:
        macos_prefs = path.expanduser(MACOS_PREFS_TILDA)
        linux_prefs = path.expanduser(LINUX_PREFS_TILDA)
        autopkg_prefs = path.expanduser(AUTOPKG_PREFS_TILDA)
        if path.exists(macos_prefs):
            config_path = macos_prefs
        elif path.exists(linux_prefs):
            config_path = linux_prefs
        elif path.exists(autopkg_prefs):
            config_path = autopkg_prefs
        elif path.exists(JAMF_PREFS):
            config_path = JAMF_PREFS
        else:
            config_path = macos_prefs
    if config_path[0] == "~":
        config_path = path.expanduser(config_path)
    return config_path


def prompt_hostname():
    valid = False
    while not valid:
        hostname = input("Hostname (don't forget https:// and :8443): ")
        if hostname.startswith("https://") or hostname.startswith("http://"):
            valid = True
    return hostname
