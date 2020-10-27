#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#pylint: disable=no-member, missing-class-docstring, signature-differs, missing-function-docstring

"""
records

A class for each type of record/object in Jamf
"""

__author__ = 'Tony Williams'
__email__ = 'tonyw@honestpuck.com'
__copyright__ = 'Copyright (c) 2020 Tony Williams'
__license__ = 'MIT'
__date__ = '2020-09-21'
__version__ = "0.2.0"

from .api import API
from . import convert

import sys

__all__ = ('Categories', 'Computers', 'ComputerGroups', 'JamfError')

#pylint: disable=unnecessary-pass
class Error(Exception):
    """ just passing through """
    pass


#pylint: disable=super-init-not-called
class JamfError(Error):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class Record():
    """
    A class for an object or list of objects on Jamf Pro

    NOTE: For reasons known only to itself Jamf uses 'wordstogether' for the
    endpoint in the URL but 'underscore_between' for the XML tags in some
    endpoints and there are cases where the endpoint and object tag are more
    different than that.
    This means we need to know 3 strings for each object type, the endpoint,
    the top of the list, and the top of the object. We pass them in to __new__
    as a dict.
    Just in case that's not confusing enough the id tag is not always 'id'.
    """

    def __new__(cls, prefs, idn='id'):
        """
        See the class docstring for an explanation of the parameters
        """
        rec = super().__new__(cls)
        rec._endpoint = prefs['end']
        rec._object = prefs['single']
        try:
            rec._objects = prefs['list']
        except KeyError:
            rec._objects = rec._endpoint
        rec.session = API()
        rec.idn = idn
        try:
            rec.put_by_name = prefs['put_by_name']
        except KeyError:
            rec.put_by_name = False
        try:
            rec.post_by_name = prefs['post_by_name']
        except KeyError:
            rec.post_by_name = False
        try:
            rec.delete_by_name = prefs['delete_by_name']
        except KeyError:
            rec.delete_by_name = False
        return rec

    def list_to_dict(self, lst):
        """
        convert list returned by get() into a dict. In most cases it will
        be keyed on the ID and only have the name but some record types
        call them something different and some record types have more than
        name and id. For those it is keyed on ID still but that contains
        a further dict with the remaining keys
        """
        idn = self.idn
        dct = {}
        keys = list(lst[0].keys())
        if len(keys) == 2:
            for elem in lst:
                dct.update({elem[idn]: elem[keys[1]]})
        else:
            for elem in lst:
                keys = elem.pop(idn)
                dct.update({keys: elem})
        return dct

    def get(self, record=''):
        if record == '':
            lst = self.session.get(self._endpoint)[self._objects][self._object]
            return self.list_to_dict(lst)
        try:
            end = f'{self._endpoint}/id/{int(record)}'
        except ValueError:
            end = f'{self._endpoint}/name/{record}'
        return self.session.get(end)[self._object]

    def put(self, record, data, raw=False):
        out = {self._object: data}
        out = convert.dict_to_xml(out)
        try:
            val = int(record)
        except ValueError:
            if self.post_by_name:
                end = f'{self._endpoint}/name/{record}'
                return self.session.post(end, out, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
            return self.session.post(end, out, raw)
        end = f'{self._endpoint}/id/{val}'
        return self.session.post(end, out, raw)

    def post(self, record, data, raw=False):
        out = {self._object: data}
        out = convert.dict_to_xml(out)
        try:
            val = int(record)
        except ValueError:
            if self.post_by_name:
                end = f'{self._endpoint}/name/{record}'
                return self.session.post(end, out, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
            return self.session.post(end, out, raw)
        end = f'{self._endpoint}/id/{val}'
        return self.session.post(end, out, raw)

    def delete(self, record, raw=False):
        try:
            val = int(record)
        except ValueError:
            if self.post_by_name:
                end = f'{self._endpoint}/name/{record}'
                return self.session.delete(end, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
        end = f'{self._endpoint}/id/{val}'
        return self.session.delete(end, raw)


class ComputerSearches(Record):
    def __new__(cls):
        prefs = {
            'end': 'advanced_computer_searches',
            'single': 'advanced_computer_search',
            'put_by_name': True,
            'post_by_name': True,
            'delete_by_name': True
        }
        return super().__new__(cls, prefs=prefs)

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class Categories(Record):
    def __new__(cls):
        prefs = {'end': 'categories', 'single': 'category'}
        return super().__new__(cls, prefs=prefs)


class ComputerExtensionAttributes(Record):
    def __new__(cls):
        prefs = {
            'end': 'computerextensionattributes',
            'single': 'computerextensionattributes'
        }
        return super().__new__(cls, prefs=prefs)


class Computers(Record):
    def __new__(cls):
        prefs = {'end': 'computers', 'single': 'computer'}
        return super().__new__(cls, prefs=prefs)


class ComputerGroups(Record):
    def __new__(cls):
        prefs = {
            'end': 'computergroups',
            'single': 'computer_group',
            'list': 'computer_groups'
        }
        return super().__new__(cls, prefs=prefs)

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class Departments(Record):
    def __new__(cls):
        prefs = {'end': 'departments', 'single': 'department'}
        return super().__new__(cls, prefs=prefs)


class ConfigProfiles(Record):
    def __new__(cls):
        prefs = {
            'end': 'osxconfigurationprofiles',
            'single': 'osxconfigurationprofile'
        }
        return super().__new__(cls, prefs=prefs)


class Packages(Record):
    def __new__(cls):
        prefs = {'end': 'packages', 'single': 'package'}
        return super().__new__(cls, prefs=prefs)


class PatchPolicies(Record):
    def __new__(cls):
        prefs = {'end': 'patch_policies', 'single': 'patch_policy'}
        return super().__new__(cls, prefs=prefs)

    def get_softwaretitleconfig(self, record=''):
        """ 7 is a good example """
        end = f'{self._endpoint}softwaretitleconfig/id/{record}'
        lst = self.session.get(end)[self._objects][self._object]
        return self.list_to_dict(lst)

    def post_softwaretitleconfig(self, record, data, raw=False):
        if isinstance(data, dict):
            out = []
            out[self._objects][self._object] = data
        end = f'{self._endpoint}softwaretitleconfig/id/{record}'
        return self.session.post(end, data, raw)

class PatchSoftwareTitles(Record):
    def __new__(cls):
        prefs = {
            'end': 'patch_software_titles',
            'single': 'patch_software_title'
        }
        return super().__new__(cls, prefs=prefs)

class Policies(Record):
    def __new__(cls):
        prefs = {'end': 'policies', 'single': 'policy'}
        return super().__new__(cls, prefs=prefs)

class Scripts(Record):
    def __new__(cls):
        prefs = {'end': 'scripts', 'single': 'script'}
        return super().__new__(cls, prefs=prefs)

class Sites(Record):
    def __new__(cls):
        prefs = {'end': 'sites', 'single': 'site'}
        return super().__new__(cls, prefs=prefs)
