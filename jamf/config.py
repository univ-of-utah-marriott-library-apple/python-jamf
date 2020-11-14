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
import pathlib
import plistlib
import itertools
from os import path
from sys import stderr
from xml.parsers.expat import ExpatError

LINUX_PREFS = pathlib.Path.home()/'.edu.utah.mlib.jamfutil.plist'
MACOS_PREFS = pathlib.Path.home()/'Library'/'Preferences'/'edu.utah.mlib.jamfutil.plist'
AUTOPKG_PREFS = pathlib.Path.home()/'Library'/'Preferences'/'com.github.autopkg.plist'
JAMF_PREFS = '/Library/Preferences/com.jamfsoftware.jamf.plist'
MAGIC =  (125, 137, 82, 35, 210, 188, 221, 234, 163, 185, 31)
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Error(Exception):
    pass


class CorruptedConfigError(Error):
    pass


class ValidationError(Error):
    pass


class Config:
    def __init__(self, config_path=None, prompt=0):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.prompt = prompt
        self.hostname = None
        self.auth = None
        if not config_path:
            if path.exists(MACOS_PREFS):
                self.config_path = MACOS_PREFS
            elif path.exists(LINUX_PREFS):
                self.config_path = LINUX_PREFS
            elif path.exists(AUTOPKG_PREFS):
                self.config_path = AUTOPKG_PREFS
            elif path.exists(JAMF_PREFS):
                self.config_path = JAMF_PREFS
            else:
                self.config_path = None
        else:
            if config_path[0] == '~':
                self.config_path = path.expanduser(config_path)
            else:
                self.config_path = config_path
        # Load the prefs
        if self.prompt==2 or (not self.config_path and self.prompt==1):
            # Prompt 2 takes precedence over file
            hostname = prompt_user('JSS Hostname https://')
            self.hostname = f"https://{hostname}"
            self.auth = credentials_prompt()
        elif self.config_path and path.exists(self.config_path):
            fptr = open(self.config_path, 'rb')
            prefs = plistlib.load(fptr)
            # TODO remove this when it's no longer used anywhere else.
            self.data = prefs
            fptr.close()
            if 'JSSHostname' in prefs:
                hostname = prefs['JSSHostname']
                self.hostname = f"https://{hostname}:8443"
                c = prefs.get('Credentials', {})
                self._credentials = Credentials(c, callback=transposition(MAGIC))
                self.auth = self.credentials('jamf.biology.utah.edu', None)
            elif 'JSS_URL' in prefs:
                self.hostname = prefs["JSS_URL"]
                self.auth = (prefs["API_USERNAME"], prefs["API_PASSWORD"])
            elif 'jss_url' in prefs:
                self.hostname = prefs["jss_url"]
                # No auth in that file
            # Prompt 1 for any missing prefs
            if not self.hostname and self.prompt==1:
                hostname = prompt_user('JSS Hostname https://')
                self.hostname = f"https://{hostname}"
            if not self.auth and self.prompt==1:
                self.auth = credentials_prompt()
        elif not self.config_path:
            print("No jamf config file could be found and prompt is off.")
            exit(1)
        else:
            raise FileNotFoundError(self.config_path)



    def save(self):
        self.data.update({'Credentials': bytes(self._credentials)})
        _prev = None
        try:
            _prev = self.load()
        except FileNotFoundError:
            self.log.debug(f"missing: {self.config_path}")
        except ExpatError:
            self.log.error(f"corrupted: {self.config_path}")
        self.log.info(f"saving: {self.config_path}")
        try:
            # save the data
            with open(self.config_path, 'wb') as f:
                plistlib.dump(self.data, f)
        except TypeError as e:
            # file is partially overwritten when error occurs
            self.log.error(f"invalid plist value: {e}")
            if _prev is not None:
                # restore the file to the previous state (if any)
                self.log.info(f"restoring: {self.config_path}")
                with open(self.config_path, 'wb') as f:
                    plistlib.dump(_prev, f)
            else:
                # remove the empty/corrupted file (no previous data)
                self.log.debug("removing empty file")
                self.config_path.unlink()
            raise e

#     def get(self, key, prompt='', **kwargs):
#         value = self.data.get(key)
#         if value is None:
#             if prompt:
#                 value = prompt_user(prompt, **kwargs)
#                 self.set(key, value)
#             if not value:
#                 raise KeyError(key)
#             self.set(key, value)
#         return value

    def set(self, key, value):
        if value is None:
            raise ValueError("unsupported value: None")
        self.data[key] = value

    def remove(self, key):
        try:
            del(self.data[key])
        except KeyError:
            pass

    def exists(self):
        return self.config_path.exists()

    def credentials(self, hostname, auth=None):
        print(hostname)
        hostname="jamf.biology.utah.edu"
        if auth:
            self._credentials.register(hostname, auth)
            self.data['Credentials'] = bytes(self._credentials)
        else:
            try:
                # return saved credentials
                return tuple(self._credentials.retrieve(hostname))
            except KeyError:
                pass
            # prompt user for credentials and register them for future use
            auth = credentials_prompt()
            self._credentials.register(hostname, auth)
            return auth

    def reset(self):
        self.data = {}
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
        return bytes(x^y for x, y in zip(data, itertools.cycle(key)))
    return _wrapped


def credentials_prompt(user=None):
    if not user:
        user = input("username: ")
    passwd = getpass.getpass()
    return user, passwd


def prompt_user(prompt, callback=None, attempts=3):
    if not callback:
        value = input(f"{prompt}")
    else:
        count = 0
        value = None
        while not value and count <= attempts:
            _input = input(f"{prompt}: ")
            try:
                callback(_input)
            except Exception as e:
                print(f"invalid {prompt}", file=stderr)
            else:
                value = _input
            count += 1
        if not value:
            raise ValidationError(f"failed after {count} attempt(s)")
    return value
