# -*- coding: utf-8 -*-

"""
Configuration for python-jamf
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.3.0"

import getpass
import logging
import plistlib
from datetime import datetime
from os import path, remove
from sys import stderr

import keyring

from .exceptions import JamfConfigError

LINUX_PREFS_TILDA = "~/.edu.utah.mlib.jamfutil.plist"
MACOS_PREFS_TILDA = "~/Library/Preferences/edu.utah.mlib.jamfutil.plist"
AUTOPKG_PREFS_TILDA = "~/Library/Preferences/com.github.autopkg.plist"
JAMF_PREFS = "/Library/Preferences/com.jamfsoftware.jamf.plist"
logging.getLogger(__name__).addHandler(logging.NullHandler())

TOKEN_KEY = "python-jamf-token"
EXPIRE_KEY = "python-jamf-expires"


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
        if not self.hostname:
            if self.prompt:
                self.hostname = prompt_hostname()
            else:
                raise JamfConfigError(
                    "Config failed to obtain a hostname and prompt is off."
                )
        if not self.username:
            if self.prompt:
                self.username = input("Username: ")
            else:
                raise JamfConfigError(
                    "Config failed to obtain a username and prompt is off."
                )
        if not self.password:
            if self.prompt:
                self.password = getpass.getpass()
            else:
                raise JamfConfigError(
                    "Config failed to obtain a password and prompt is off."
                )
        if not self.hostname.startswith("https://") and not self.hostname.startswith(
            "http://"
        ):
            raise JamfConfigError(
                f"Hostname ({self.hostname}) does not start with 'https://' or 'http://'"
            )

    def load(self):
        if path.exists(self.config_path):
            fptr = open(self.config_path, "rb")
            try:
                prefs = plistlib.load(fptr)
            except plistlib.InvalidFileException:
                fptr.close()
                raise JamfConfigError(
                    f"Could not load {self.config_path}, isit plist formatted?"
                )
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

    def load_token(self):
        self.token = keyring.get_password(self.hostname, TOKEN_KEY)
        expires = keyring.get_password(self.hostname, EXPIRE_KEY)
        self.expired = False
        if self.token and expires:
            try:
                expires = expires[:-1]  # remove the Z because in case there's no "."
                deadline = datetime.strptime(expires.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                if deadline > datetime.utcnow():
                    self.expired = True
            except ValueError as e:
                stderr.write(
                    f"Error getting saved token: {e}\n"
                    f"expire string 1: {expires}\n"
                    f"expire string 2: {expires.split('.')[0]}\n"
                    f"Will try to continue.\n"
                )

    def save_new_token(self, token, expires):
        self.token = token
        self.expires = expires
        keyring.set_password(self.hostname, TOKEN_KEY, self.token)
        keyring.set_password(self.hostname, EXPIRE_KEY, self.expires)

    def revoke_token(self):
        try:
            keyring.delete_password(self.hostname, TOKEN_KEY)
        except:
            stderr.write("Warning: couldn't delete keyring token\n")
        try:
            keyring.delete_password(self.hostname, EXPIRE_KEY)
        except:
            stderr.write("Warning: couldn't delete keyring token expire date\n")

    def reset(self):
        self.revoke_token()
        try:
            keyring.delete_password(self.hostname, self.username)
        except:
            stderr.write("Warning: couldn't delete keyring password\n")
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
    while self.hostname[-1] == "/":
        self.hostname = self.hostname[:-1]
    return hostname
