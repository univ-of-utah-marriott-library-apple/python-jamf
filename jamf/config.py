# -*- coding: utf-8 -*-

"""
Configuration for jamfutil
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.2.3"

import copy
import getpass
import logging
import plistlib
import itertools
from os import path
LINUX_PREFS_TILDA = '~/.edu.utah.mlib.jamfutil.plist'
MACOS_PREFS_TILDA = '~/Library/Preferences/edu.utah.mlib.jamfutil.plist'
AUTOPKG_PREFS_TILDA = '~/Library/Preferences/com.github.autopkg.plist'
JAMF_PREFS = '/Library/Preferences/com.jamfsoftware.jamf.plist'
MAGIC = (125, 137, 82, 35, 210, 188, 221, 234, 163, 185, 31)
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Error(Exception):
    pass


class CorruptedConfigError(Error):
    pass


class ValidationError(Error):
    pass


class Config:
    def __init__(self,
                 config_path=None,
                 prompt=False,
                 hostname=None,
                 username=None,
                 password=None,
                 explain=False):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.prompt = prompt
        self.hostname = hostname
        self.username = username
        self.password = password
        self._credentials = None
        macos_prefs = path.expanduser(MACOS_PREFS_TILDA)
        if not config_path:
            linux_prefs = path.expanduser(LINUX_PREFS_TILDA)
            autopkg_prefs = path.expanduser(AUTOPKG_PREFS_TILDA)
            if path.exists(macos_prefs):
                if explain:
                    print("Using "+macos_prefs)
                self.config_path = macos_prefs
            elif path.exists(linux_prefs):
                if explain:
                    print("Using "+linux_prefs)
                self.config_path = linux_prefs
            elif path.exists(autopkg_prefs):
                if explain:
                    print("Using "+autopkg_prefs)
                self.config_path = autopkg_prefs
            elif path.exists(JAMF_PREFS):
                if explain:
                    print("Using "+JAMF_PREFS)
                self.config_path = JAMF_PREFS
            else:
                if explain:
                    print("Using "+macos_prefs+" but it doesn't exist yet.")
                self.config_path = macos_prefs
        else:
            if explain:
                print("Using "+config_path+" because you said so.")
            self.config_path = config_path

        if self.config_path[0] == '~':
            self.config_path = path.expanduser(self.config_path)
            if explain:
                print("Expanding the path. Using "+self.config_path)

        if not self.hostname and not self.username and not self.password:
            if path.exists(self.config_path):
                fptr = open(self.config_path, 'rb')
                prefs = plistlib.load(fptr)
                fptr.close()
                if 'JSSHostname' in prefs:
                    self.hostname = prefs['JSSHostname']
                    c = prefs.get('Credentials', {})
                    self._credentials = Credentials(c, callback=transposition(MAGIC))
                    (self.username, self.password) = self.read_credentials(self.hostname)
                elif 'JSS_URL' in prefs:
                    self.hostname = prefs["JSS_URL"]
                    self.username = prefs["API_USERNAME"]
                    self.password = prefs["API_PASSWORD"]
                elif 'jss_url' in prefs:
                    self.hostname = prefs["jss_url"]
                    # No auth in that file
            else:
                self.log.debug(f"file not found: {self.config_path}")

        # Prompt for any missing prefs
        if self.prompt:
            if not self.hostname:
                self.hostname = prompt_hostname()
            if not self.username:
                self.username = input("username: ")
            if not self.password:
                self.password = getpass.getpass()
        elif not self.hostname and not self.username and not self.password:
#             raise FileNotFoundError(self.config_path)
            print("No jamf config file could be found and prompt is off.")
            exit(1)

    def save(self):
        if not self._credentials:
            self._credentials = Credentials({}, callback=transposition(MAGIC))
        self._credentials.register(self.hostname, (self.username, self.password))
        creds = bytes(self._credentials)
        data = {
            'JSSHostname': self.hostname,
            'Credentials': creds
        }
        self.log.info(f"saving: {self.config_path}")
        fptr = open(self.config_path, 'wb')
        plistlib.dump(data, fptr)
        fptr.close()

#     def exists(self):
#         return self.config_path.exists()

    def read_credentials(self, hostname):
        return tuple(self._credentials.retrieve(hostname))

    def reset(self):
        self.save()
        self._credentials = Credentials({}, callback=transposition(MAGIC))


class Credentials:
    def __init__(self, data, callback=None):
        self.data = data
        if isinstance(data, (list, tuple, dict)):
            self.data = copy.deepcopy(data)
        elif isinstance(data, bytes):
            self.data = plistlib.loads(data)
        self.transpose = callback if callback else lambda x: x

    def retrieve(self, key):
        value = self.data[key]
        data = self.transpose(value)
        try:
            return plistlib.loads(data)
        except plistlib.InvalidFileException:
            try:
                return data.decode('utf-8')
            except AttributeError:
                return data

    def register(self, key, value):
        if isinstance(value, Credentials):
            value = bytes(value)
        else:
            value = bytes(Credentials(value, self.transpose))
        self.data[key] = self.transpose(value)

    def reset(self):
        self.data = {}

    def __bytes__(self):
        return plistlib.dumps(self.data, fmt=plistlib.FMT_BINARY)

    def __bool__(self):
        return True if self.data else False


def transposition(key):
    if isinstance(key, str):
        key = bytes(key, encoding='utf-8')
    if not all(isinstance(x, int) for x in key):
        raise ValueError(f"invalid key: {key!r}")

    def _wrapped(data):
        if isinstance(data, str):
            data = bytes(data, encoding='utf-8')
        return bytes(x ^ y for x, y in zip(data, itertools.cycle(key)))
    return _wrapped


def prompt_hostname():
    return input('JSS Hostname (don\'t forget https:// and :8443): ')
