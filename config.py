# -*- coding: utf-8 -*-

"""
Configuration for jamfutil
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.2.2"

import sys
import copy
import getpass
import logging
import pathlib
import plistlib
import itertools
from xml.parsers.expat import ExpatError

DOMAIN = 'edu.utah.mlib.jamfutil'
PREFERENCES = pathlib.Path.home()/'Library'/'Preferences'/f"{DOMAIN}.plist"
MAGIC =  (125, 137, 82, 35, 210, 188, 221, 234, 163, 185, 31)
logging.getLogger(__name__).addHandler(logging.NullHandler())


class Error(Exception):
    pass


class CorruptedConfigError(Error):
    pass


class ValidationError(Error):
    pass


class Config:

    def __init__(self, path=None, default=None):
        self.log = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.path = pathlib.Path(path) if path else PREFERENCES
        try:
            self.data = self.load(self.path)
        except FileNotFoundError:
            self.data = copy.deepcopy(default) if default else {}

    def load(self, path=None):
        path = pathlib.Path(path) if path else self.path
        try:
            with open(path, 'rb') as f:
                return plistlib.load(f)
        except ExpatError:
            pass
        raise CorruptedConfigError(self.path)

    def save(self):
        _prev = None
        try:
            _prev = self.load()
        except FileNotFoundError:
            self.log.debug(f"missing: {self.path}")
        except ExpatError:
            self.log.error(f"corrupted: {self.path}")
        self.log.info(f"saving: {self.path}")
        try:
            # save the data
            with open(self.path, 'wb') as f:
                plistlib.dump(self.data, f)
        except TypeError as e:
            # file is partially overwritten when error occurs
            self.log.error(f"invalid plist value: {e}")
            if _prev is not None:
                # restore the file to the previous state (if any)
                self.log.info(f"restoring: {self.path}")
                with open(self.path, 'wb') as f:
                    plistlib.dump(_prev, f)
            else:
                # remove the empty/corrupted file (no previous data)
                self.log.debug("removing empty file")
                self.path.unlink()
            raise e

    def get(self, key, prompt='', **kwargs):
        value = self.data.get(key)
        if value is None:
            if prompt:
                value = prompt_user(prompt, **kwargs)
                self.set(key, value)
            if not value:
                raise KeyError(key)
            self.set(key, value)
        return value

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
        return self.path.exists()

    def reset(self):
        self.data = {}
        self.save()


class SecureConfig(Config):

    def __init__(self, path=None, **kwargs):
        super().__init__(path=path, **kwargs)
        self.log = logging.getLogger(f"{__name__}.SecureConfig")
        c = self.data.get('Credentials', {})
        self._credentials = Credentials(c, callback=transposition(MAGIC))

    def save(self):
        self.data.update({'Credentials': bytes(self._credentials)})
        super().save()

    def credentials(self, hostname, auth=None):
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
        super().reset()
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
        value = input(f"{prompt}: ")
    else:
        count = 0
        value = None
        while not value and count <= attempts:
            _input = input(f"{prompt}: ")
            try:
                callback(_input)
            except Exception as e:
                print(f"invalid {prompt}", file=sys.stderr)
            else:
                value = _input
            count += 1
        if not value:
            raise ValidationError(f"failed after {count} attempt(s)")
    return value
