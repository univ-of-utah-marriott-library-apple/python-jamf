# -*- coding: utf-8 -*-

"""
Configuration for python-jamf

This module provides the Config class for managing Jamf Pro server configuration,
including connection details and authentication credentials. It handles loading
and saving settings to plist files and uses the system keyring for secure
storage of passwords and tokens.
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.3.0"

import getpass
import logging
import plistlib
from datetime import datetime, timezone
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
    """
    Handles Jamf Pro configuration settings.

    The Config class manages the hostname, username, password, and authentication
    type for connecting to a Jamf Pro server. It supports loading from and
    saving to plist files, and integrates with the system keyring for security.
    """

    def __init__(
        self,
        config_path=None,
        hostname=None,
        username=None,
        password=None,
        client=None,
        prompt=False,
    ):
        """
        Initialize the Config object.

        :param config_path: Path to the configuration plist file.
        :param hostname: Jamf Pro server URL.
        :param username: Username for authentication.
        :param password: Password for authentication.
        :param client: Boolean indicating if API client authentication is used.
        :param prompt: Whether to prompt the user for missing information.
        """
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.prompt = prompt
        self._hostname = hostname
        self._username = username
        self._password = password
        self.client = client
        self.config_path = resolve_config_path(config_path)
        if not self._hostname and not self._username and not self._password:
            self.load()
        # Prompt for any missing prefs
        if not self._hostname:
            if self.prompt:
                self._hostname = prompt_hostname()
        if self.client is None:
            if self.prompt:
                self.client = prompt_userauth()
            else:
                self.client = False
        if not self._username:
            if self.prompt:
                self._username = input("Username: ")
        if not self._password:
            if self.prompt:
                self._password = getpass.getpass()
        if self._hostname:
            _ = self.hostname

    @property
    def hostname(self):
        if not self._hostname:
            raise JamfConfigError("Config failed to obtain a hostname.")
        if not self._hostname.startswith("https://") and not self._hostname.startswith(
            "http://"
        ):
            raise JamfConfigError(
                f"Hostname ({self._hostname}) does not start with 'https://' or 'http://'"
            )
        return self._hostname

    @hostname.setter
    def hostname(self, value):
        self._hostname = value

    @property
    def username(self):
        if not self._username:
            raise JamfConfigError("Config failed to obtain a username.")
        return self._username

    @username.setter
    def username(self, value):
        self._username = value

    @property
    def password(self):
        if not self._password:
            raise JamfConfigError("Config failed to obtain a password.")
        return self._password

    @password.setter
    def password(self, value):
        self._password = value

    @property
    def has_password(self):
        return bool(self._password)

    def load(self):
        """
        Load configuration from the plist file.

        :raises JamfConfigError: If the file cannot be loaded or is invalid.
        """
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
the "conf-python-jamf" script.
"""
                    raise JamfConfigError(cmessage)
                self.hostname = prefs["JSSHostname"]
                self.username = prefs["Username"]
                if "APIClientAuth" in prefs:
                    self.client = prefs["APIClientAuth"]
                else:
                    self.client = False
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
        """
        Save the current configuration to the plist file and password to keyring.
        """
        keyring.set_password(self.hostname, self.username, self.password)
        data = {
            "JSSHostname": self.hostname,
            "Username": self.username,
            "APIClientAuth": self.client,
        }
        self.log.info(f"saving: {self.config_path}")
        fptr = open(self.config_path, "wb")
        plistlib.dump(data, fptr)
        fptr.close()

    def load_token(self):
        """
        Load the API token from the keyring and check if it's expired.
        """
        self.token = keyring.get_password(self.hostname, TOKEN_KEY)
        expires = keyring.get_password(self.hostname, EXPIRE_KEY)
        self.expired = False
        if self.token and expires:
            try:
                expires = expires[:-1]  # remove the Z because in case there's no "."
                deadline = datetime.strptime(
                    expires.split(".")[0],
                    "%Y-%m-%dT%H:%M:%S"
                ).replace(tzinfo=timezone.utc)
                if deadline > datetime.now(timezone.utc):
                    self.expired = True
            except ValueError as e:
                stderr.write(
                    f"Error getting saved token: {e}\n"
                    f"expire string 1: {expires}\n"
                    f"expire string 2: {expires.split('.')[0]}\n"
                    f"Will try to continue.\n"
                )

    def save_new_token(self, token, expires):
        """
        Save a new API token and its expiration date to the keyring.

        :param token: The API token string.
        :param expires: The expiration timestamp string.
        """
        self.token = token
        self.expires = expires
        keyring.set_password(self.hostname, TOKEN_KEY, self.token)
        keyring.set_password(self.hostname, EXPIRE_KEY, self.expires)

    def revoke_token(self):
        """
        Remove the API token and its expiration date from the keyring.
        """
        try:
            keyring.delete_password(self.hostname, TOKEN_KEY)
        except:
            stderr.write("Warning: couldn't delete keyring token\n")
        try:
            keyring.delete_password(self.hostname, EXPIRE_KEY)
        except:
            stderr.write("Warning: couldn't delete keyring token expire date\n")

    def reset(self):
        """
        Revoke the token, delete the password from keyring, and remove the config file.
        """
        self.revoke_token()
        try:
            keyring.delete_password(self.hostname, self.username)
        except:
            stderr.write("Warning: couldn't delete keyring password\n")
        remove(self.config_path)


def resolve_config_path(config_path=None):
    """
    Resolve the absolute path to the configuration file.

    :param config_path: Optional path provided by the user.
    :return: Resolved absolute path.
    """
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


def prompt_hostname(existing_hostname=None):
    """
    Interactively prompt the user for the Jamf Pro hostname.

    :return: Validated hostname string.
    """
    while True:
        if existing_hostname is None:
            message = "don't forget https:// and :8443"
        else:
            message = existing_hostname
        hostname = input(f"Hostname ({message}): ").strip()
        if existing_hostname and hostname == "":
            hostname = existing_hostname
        if hostname.startswith("https://") or hostname.startswith("http://"):
            break
    while hostname[-1] == "/":
        hostname = hostname[:-1]
    return hostname


def prompt_userauth(existing_client=None):
    """
    Interactively prompt the user for the authentication type.

    :return: Boolean (True for API Client Auth, False for User Auth).
    """
    while True:
        if existing_client is None:
            prompt = "User Auth [0] or API Client Auth [1]: "
        else:
            default = "1" if existing_client else "0"
            prompt = f"User Auth [0] or API Client Auth [1] (default {default}): "
        client = input(prompt).strip().lower()
        if existing_client is not None and client == "":
            return existing_client
        if client in ["0", "no", "false"]:
            return False
        if client in ["1", "yes", "true"]:
            return True


def prompt_username(existing_username=None, username_type="Username"):
    """
    Interactively prompt the user for a username or client ID.

    :return: Username string (or existing value if user enters blank).
    """
    if existing_username:
        message = existing_username
    else:
        message = None
    prompt = f"{username_type}: " if message is None else f"{username_type} ({message}): "
    username = input(prompt).strip()
    if existing_username and username == "":
        return existing_username
    return username


def prompt_password(existing_password=None, password_type="Password"):
    """
    Interactively prompt the user for a password or client secret.

    :return: Password string (or existing value if user enters blank).
    """
    if existing_password is None:
        prompt = f"{password_type}: "
    else:
        prompt = f"{password_type} (leave blank to keep existing): "
    password = getpass.getpass(prompt=prompt)
    if existing_password is not None and password == "":
        return existing_password
    return password
