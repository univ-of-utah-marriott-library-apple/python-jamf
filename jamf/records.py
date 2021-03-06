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
__version__ = "0.3.6"


import json
import re
import sys
from os import path, _exit
from pprint import pprint
#pylint: disable=relative-beyond-top-level
from . import convert
from .api import API
__all__ = (
    'AdvancedComputerSearches',
    'AdvancedMobileDeviceSearches',
    'AdvancedUserSearches',
    'Buildings',
    'BYOProfiles',
    'Categories',
    'Classes',
    'ComputerConfigurations',
    'ComputerExtensionAttributes',
    'ComputerGroups',
    'ComputerReports',
    'Computers',
    'Departments',
    'DirectoryBindings', # produces an error when getting by name
    'DiskEncryptionConfigurations',
    'DistributionPoints',
    'DockItems',
    'Ebooks',
    'Ibeacons',
    'JSONWebTokenConfigurations',
    'LDAPServers',
    'LicensedSoftware',
    'MacApplications',
    'ManagedPreferenceProfiles',
    'MobileDeviceApplications',
    'MobileDeviceCommands',
    'MobileDeviceConfigurationProfiles',
    'MobileDeviceEnrollmentProfiles',
    'MobileDeviceExtensionAttributes',
    'MobileDeviceInvitations',
    'MobileDeviceProvisioningProfiles',
    'MobileDevices',
    'NetbootServers',
    'NetworkSegments',
    'OSXConfigurationProfiles', # produces an error when getting by name
    'Packages',
    'PatchExternalSources',
    'PatchInternalSources',
    'PatchPolicies',
    'PatchSoftwareTitles',
    'Peripherals',
    'PeripheralTypes',
    'Policies',
    'Printers',
    'RemovableMACAddresses',
    'RestrictedSoftware',
    'Scripts',
    'Sites',
    'SoftwareUpdateServers',
    'UserExtensionAttributes',
    'UserGroups',
    'Users',
    'VPPAccounts',
    'VPPAssignments',
    'VPPInvitations',
    'WebHooks',
    # Add all non-Jamf Record classes to valid_records below
    'JamfError')

def valid_records():
    valid = tuple(x for x in __all__ if not x in [
        # Add all non-Jamf Record classes here
        'JamfError'
    ])
    return valid

#pylint: disable=eval-used
def class_name(name, case_sensitive=True):
    if case_sensitive and name in valid_records():
        return eval(name)
    for temp in valid_records():
        if name.lower() == temp.lower():
            return eval(temp)
    raise JamfError(f"{name} is not a valid record.")


#pylint: disable=super-init-not-called
class JamfError(Exception):
    def __init__(self, message):
        print(f"jctl: error: {message}", file=sys.stderr)
        _exit(1)


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
    _swagger = json.load(open(path.dirname(__file__)+'/records.json', 'r'))
    _broken_api = [
        '/directorybindings/name/{name}',
        '/osxconfigurationprofiles/name/{name}',
    ]
    def __new__(cls, args, kwargs):
        """
        See the class docstring for an explanation of the parameters
        """
        rec = super().__new__(cls)

        # The treasure chest
        rec._data = None
        rec.session = API()
        rec._index = -1

        # The endpoint url, e.g. "Policies" class becomes "policies" endpoint
        if not hasattr(cls, '_swagger_path_name'):
            rec._swagger_path_name = cls.__name__.lower()

        # Get the definition name, which almost always is the plural name
        # exceptions: LicensedSoftware
        if not hasattr(cls, '_swagger_def_name'):
            rec._swagger_def_name = rec.get_schema(rec._swagger_path_name)
            # If there's an xml entry, use it for the definition name
            temp2 = cls._swagger['definitions'][rec._swagger_def_name]
            if ('xml' in temp2 and 'name' in temp2['xml']):
                rec._swagger_def_name = temp2['xml']['name']

        if not hasattr(cls, '_id_text'):
            rec._id_text = "id"

        if not hasattr(cls, '_id_text2'):
            rec._id_text2 = "id"

        if not hasattr(cls, '_swagger_plural_key'):
            # Get the schema, which almost always is the singular name
            temp1 = rec._swagger_path_name+'/'+rec._id_text+"/{"+rec._id_text2+"}"
            rec._swagger_plural_key = rec.get_schema(temp1)
            #getPlural and below

        if not hasattr(cls, '_swagger_singular_key'):
            rec._swagger_singular_key = rec._swagger_plural_key

        if not hasattr(cls, '_list_to_dict_key'):
            rec._list_to_dict_key = 'id'

        return rec

    def __init__(self, query='', python_data=None, json_file=None, json_data=None):
        if json_data:
            python_data = json.load(json_data)
            self.post(python_data)
        elif json_file is not None:
            if path.exists(json_file):
                python_data = json.load(open(json_file, 'r'))
                self.post(python_data)
            else:
                raise JamfError(f"File does not exist: {json_file}.")
        elif python_data is not None:
            self.post(python_data)
        else:
            self.get(query)

    def get(self, record=''):
        if record == '':
            self.getPlural()
        else:
            self.getSingle(record)

    def getPlural(self):
        lst = self.session.get(self._swagger_path_name)
        if self._swagger_def_name in lst:
            lst2 = lst[self._swagger_def_name]
            if not lst2 or 'size' in lst2 and lst2['size'] == '0':
                return {}
            if self._swagger_plural_key in lst2:
                if 'size' in lst2 and lst2['size'] == '1':
                    self._data = self.list_to_dict([lst2[self._swagger_plural_key]])
                else:
                    self._data = self.list_to_dict(lst2[self._swagger_plural_key])
                self.plural = True
            else:
                raise JamfError(f"Endpoint {self._swagger_path_name} - "
                                f"{self._swagger_def_name} has no member named "
                                f"{self._swagger_plural_key} (_swagger_plural_key).")
        else:
            raise JamfError(f"Endpoint {self._swagger_path_name} has no "
                            f"member named {self._swagger_def_name}. Check "
                            f"the swagger definition file for the name of "
                            f"{self._swagger_path_name} and set the property "
                            f"_swagger_def_name for class ({self._swagger_path_name}).")

    def getSingle(self, record, key_text=None):
        if key_text:
            self._key = record
            self._key_text = key_text
        else:
            try:
                # This wont work if the name is actually a number...
                self._key = int(record)
                self._key_text = self._id_text
            except ValueError:
                self._key = record
                self._key_text = 'name'
        end = f'{self._swagger_path_name}/{self._key_text}/{self._key}'
        if self.is_action_valid('get', self._key_text):
            results = self.session.get(end)
            if self._swagger_singular_key in results:
                if results[self._swagger_singular_key]:
                    self._data = results[self._swagger_singular_key]
                else:
                    self._data = {}
                self.plural = False
            else:
                print("-------------------------------------"
                      "-------------------------------------\n"
                      "Data dump\n")
                pprint(results)
                raise JamfError(f"Endpoint {end} has no member named "
                                f"{self._swagger_singular_key}"
                                f"(_swagger_singular_key).")
        else:
            if self._key_text == "name":
                # print(f'Converting {record} to id, hope for the best')
                # Warning! Infinite regression if not careful!
                self.getSingle(self.convert_name_to_id(record), self._id_text)
            else:
                raise JamfError(f'{end}[get] is an invalid action')

    def put(self, data=None, raw=False):
        if not hasattr(self, '_key'):
            raise JamfError('Record has no id or name.')
        end = f'{self._swagger_path_name}/{self._key_text}/{self._key}'
        if not self.is_action_valid('put', self._key_text):
            raise JamfError(f'{end} is an invalid endpoint')
        # Data
        if data:
            out = {self._swagger_singular_key: data}
        else:
            out = {self._swagger_singular_key: self._data}
        out = convert.dict_to_xml(out)
        return self.session.put(end, out, raw)

    def post(self, python_data, raw=False):
        if not self._data:
            end = f'{self._swagger_path_name}/{self._id_text}/0'
            if not self.is_action_valid('post', self._id_text):
                raise JamfError(f'{end} is an invalid endpoint')
            out = {self._swagger_singular_key: python_data}
            out = convert.dict_to_xml(out)
            return self.session.post(end, out, raw)
        else:
            raise JamfError("Can't post a record, use put")

    def delete(self, raw=False):
        if not self.plural:
            if not hasattr(self, '_key'):
                raise JamfError('Record has no id or name.')
            end = f'{self._swagger_path_name}/{self._key_text}/{self._key}'
            if not self.is_action_valid('delete', self._key_text):
                raise JamfError(f'{end} is an invalid endpoint')
            return self.session.delete(end, raw)
        else:
            raise JamfError("Can't delete a list of records (too dangerous)")

    def list_to_dict(self, lst):
        """
        convert list returned by get() into a dict. In most cases it will
        be keyed on the ID and only have the name but some record types
        call them something different and some record types have more than
        name and id. For those it is keyed on ID still but that contains
        a further dict with the remaining keys
        """
        dct = {}
        keys = list(lst[0].keys())
        if len(keys) == 2:
            for elem in lst:
                dct.update({elem[self._list_to_dict_key]: elem[keys[1]]})
        else:
            for elem in lst:
                keys = elem.pop(self._list_to_dict_key)
                dct.update({keys: elem})
        return dct

    def get_schema(self, swagger_path):
        temp1 = self._swagger['paths']['/'+swagger_path]['get']
        schema = temp1['responses']['200']['schema']['$ref']
        if schema.startswith("#/definitions/"):
            schema = schema[14:]
        return schema

    def is_action_valid(self, a, key_text):
        p = f'/{self._swagger_path_name}/{key_text}/{{{key_text}}}'
        if p in self._broken_api:
            return False
        return p in self._swagger['paths'] and a in self._swagger['paths'][p]

    def convert_name_to_id(self, record_name):
        self.getPlural()
        try:
            return int(self.id(record_name))
        except ValueError:
            raise JamfError(f"Couldn't convert {record_name} to id")

    def data(self):
        return self._data

    def list(self, regexes=None, exactMatches=None, ids=None, returnIds=False):
        results_ = []
        if not self._data or not self.plural:
            return results_

        for recordId, recordName in self._data.items():
            append_ = False
            if recordName:
                # some results are id:name, some are id:{name:name}
                if not isinstance(recordName, str) and 'name' in recordName:
                    recordName = recordName['name']
                if ids:
                    for id_ in ids:
                        if id_ and recordId == id_:
                            append_ = True
                if regexes:
                    for rr in regexes:
                        if not append_ and re.search(rr, recordName):
                            append_ = True
                if exactMatches:
                    for em in exactMatches:
                        if not append_ and recordName == em:
                            append_ = True
                if not regexes and not exactMatches and not ids:
                    append_ = True
                if append_:
                    if returnIds:
                        results_.append([recordName,recordId])
                    else:
                        results_.append(recordName)
        return sorted(results_, key=lambda k: (k is None, k == "", k))

    def get_path(self, path):
        if self._data:
            if self.plural:
                pass
            else:
                temp = path.split(',')
                placeholder = self._data
                for jj in temp:
                    if placeholder:
                        if jj in placeholder:
                            placeholder = placeholder[jj]
                        else:
                            return None
                    else:
                        return None
                return placeholder

    def set_path(self, path, value):
        if self._data:
            if self.plural:
                pass
            else:
                temp = path.split(',')
                key = temp.pop()
                placeholder = self._data
                for jj in temp:
                    if placeholder:
                        if jj in placeholder:
                            placeholder = placeholder[jj]
                        else:
                            return False
                    else:
                        return False
                placeholder[key] = value
                return True

    def records_by_name(self):
        objs = {}
        for ii in self._data:
            jj = self._data[ii]
            if isinstance(jj, str):
                objs[jj] = ii
            elif 'name' in self._data[ii]:
                objs[self._data[ii]['name']] = ii
            else:
                pprint(self._data)
                raise JamfError("Couldn't flip names and id's because"
                                "name is missing.")
        return objs

    def id(self, name=None):
        if self.plural and name is not None:
            objs = self.records_by_name()
            return objs[name]
        else:
            return self._data['id']

    def __iter__(self):
        if self.plural:
            return self
        else:
            return None

    def __next__(self):
        if self.plural:
            self._index+=1
            if not self._data or self._index+1 > len(self._data):
                raise StopIteration
            return list(self._data.keys())[self._index]
        else:
            return None

class AdvancedComputerSearches(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class AdvancedMobileDeviceSearches(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class AdvancedUserSearches(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Buildings(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class BYOProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Categories(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Classes(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class ComputerConfigurations(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class ComputerExtensionAttributes(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class ComputerGroups(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)

    def add_computers(self, new_computers):
        """
        adds an array of computers in this format:
        [
            { 'computer': { 'id': '1' }, },
            { 'computer': { 'name': 'xserve-01' }, },
            { 'computer': { 'serial_number': 'C01234567890' }, },
        ]
        """
        self.put( { 'computer_additions': new_computers } )

    def add_computer(self, new_computer):
        """
        adds a computer in this format: { 'key': 'val' }
        key can be id, name, serial_number, and maybe even more.
        """
        self.put( { 'computer_additions': { 'computer': new_computer } } )

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class ComputerReports(Record):
    _swagger_singular_key = 'computer_reports'
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Computers(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Departments(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class DirectoryBindings(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class DiskEncryptionConfigurations(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class DistributionPoints(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class DockItems(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Ebooks(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Ibeacons(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class JSONWebTokenConfigurations(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class LDAPServers(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class LicensedSoftware(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MacApplications(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class ManagedPreferenceProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceApplications(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceCommands(Record):
    _list_to_dict_key = "uuid"
    _id_text = "uuid"
    _id_text2 = "uuid"
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceConfigurationProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceEnrollmentProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceExtensionAttributes(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceInvitations(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDeviceProvisioningProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class MobileDevices(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class NetbootServers(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class NetworkSegments(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class OSXConfigurationProfiles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Packages(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class PatchExternalSources(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class PatchInternalSources(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class PatchPolicies(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)

    def get_softwaretitleconfig(self, record=''):
        """ 7 is a good example """
        end = f'{self._swagger_path_name}softwaretitleconfig/id/{record}'
        lst = self.session.get(end)[self._swagger_def_name][self._swagger_singular_key]
        return self.list_to_dict(lst)

    def post_softwaretitleconfig(self, record, data, raw=False):
        if isinstance(data, dict):
            out = []
            out[self._swagger_def_name][self._swagger_singular_key] = data
        end = f'{self._swagger_path_name}softwaretitleconfig/id/{record}'
        return self.session.post(end, data, raw)

class PatchSoftwareTitles(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Peripherals(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class PeripheralTypes(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Policies(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)

    def scope(self, record):
        """
        returns a dict of the scope categories to the policy when passed a record
        """
        return record['scope']


class Printers(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class RemovableMACAddresses(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class RestrictedSoftware(Record):
    _swagger_plural_key = 'restricted_software_title'
    _swagger_singular_key = 'restricted_software'
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Scripts(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Sites(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class SoftwareUpdateServers(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class UserExtensionAttributes(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class UserGroups(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class Users(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class VPPAccounts(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class VPPAssignments(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class VPPInvitations(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)


class WebHooks(Record):
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, args, kwargs)
