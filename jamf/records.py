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
from pprint import pprint
import json
from os import path

import sys

__all__ = (
    'AdvancedComputerSearches',
    'AdvancedMobileDeviceSearches',
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
    'DirectoryBindings',
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
    'OSXConfigurationProfiles',
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
    'AdvancedUserSearches',
    'VPPAccounts',
    'VPPAssignments',
    'VPPInvitations',
    'WebHooks',
    'JamfError')

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
    _debug = False
    _swagger = json.load(open(path.dirname(__file__)+'/records.json', 'r'))
    def __new__(cls):
        """
        See the class docstring for an explanation of the parameters
        """
        rec = super().__new__(cls)

        # The endpoint url, e.g. "Policies" class becomes "policies" endpoint
        if (hasattr(cls, '_p_endpoint2')):
            rec._p_endpoint = cls._p_endpoint2
        else:
            rec._p_endpoint = cls.__name__.lower()

        if (hasattr(cls, '_p_def_name2')):
            rec._p_def_name = cls._p_def_name2
        else:
            # Get the schema, which almost always is the plural name
            # exceptions: LicensedSoftware
            _p_swagger = cls._swagger['paths']['/'+rec._p_endpoint]['get']
            rec._p_def_name = _p_swagger['responses']['200']['schema']['$ref']
            if ( rec._p_def_name[:14] == "#/definitions/" ):
                rec._p_def_name = rec._p_def_name[14:]

        # If there's an xml entry, use it
        _p_def_swagger = cls._swagger['definitions'][rec._p_def_name]
        if ('xml' in _p_def_swagger and 'name' in _p_def_swagger['xml']):
            rec._p_def_name = _p_def_swagger['xml']['name']

        if (hasattr(cls, '_id')):
            rec._s_endpoint = rec._p_endpoint+'/'+cls._id
        else:
            rec._s_endpoint = rec._p_endpoint+'/id'
        if (hasattr(cls, '_id2')):
            rec._s_endpoint2 = rec._s_endpoint+"/{"+cls._id2+"}"
        else:
            rec._s_endpoint2 = rec._s_endpoint+'/{id}'


        rec._n_endpoint = rec._p_endpoint+'/name'

        if (hasattr(cls, '_ps_def_name2')):
            rec._ps_def_name = cls._ps_def_name2
        else:
            # Get the schema, which almost always is the singular name
            # exceptions: ComputerReports
            _s_swagger = cls._swagger['paths']['/'+rec._s_endpoint2]['get']
            rec._ps_def_name = _s_swagger['responses']['200']['schema']['$ref']
            if ( rec._ps_def_name[:14] == "#/definitions/" ):
                rec._ps_def_name = rec._ps_def_name[14:]

        if (hasattr(cls, '_ss_def_name2')):
            rec._ss_def_name = cls._ss_def_name2
        else:
            rec._ss_def_name = rec._ps_def_name

        rec.session = API()
        return rec

    def list_to_dict(self, lst):
        """
        convert list returned by get() into a dict. In most cases it will
        be keyed on the ID and only have the name but some record types
        call them something different and some record types have more than
        name and id. For those it is keyed on ID still but that contains
        a further dict with the remaining keys
        """
        if (hasattr(self, '_id')):
            idn = self._id
        else:
            idn = 'id'
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
            return self.getPlural()
        else:
            return self.getSingle(record)

    def getPlural(self):
        if self.__class__._debug:
            pprint("getPlural")
        lst = self.session.get(self._p_endpoint)
        if self._p_def_name in lst:
            lst2 = lst[self._p_def_name]
            if not lst2 or 'size' in lst2 and lst2['size'] == '0':
                return {}
            elif self._ps_def_name in lst2:

                if 'size' in lst2 and lst2['size'] == '1':
                    return self.list_to_dict([lst2[self._ps_def_name]])
                else:
                    return self.list_to_dict(lst2[self._ps_def_name])
            else:
                if self.__class__._debug:
                    pprint(lst2)
                raise JamfError(f"Endpoint {self._p_endpoint} - "
                                f"{self._p_def_name} has no member named "
                                f"{self._ps_def_name} (_ps_def_name).")
        else:
            if self.__class__._debug:
                pprint(lst)
            raise JamfError(f"Endpoint {self._p_endpoint} has no member "
                            f"named {self._p_def_name} (_p_def_name).")

    def getSingle(self, record):
        if self.__class__._debug:
            pprint(f"getSingle: {record}")
        try:
            # This wont work if the name is actually a number...
            end = f'{self._s_endpoint}/{int(record)}'
        except ValueError:
            end = f'{self._n_endpoint}/{record}'

        results = self.session.get(end)
        if self._ss_def_name in results:
            if results[self._ss_def_name]:
                return results[self._ss_def_name]
            else:
                return {}
        else:
            print("-------------------------------------"
                  "-------------------------------------\n"
                  "Data dump\n")
            pprint(results)
            raise JamfError(f"Endpoint {end} has no member named "
                            f"{self._ss_def_name} (_ss_def_name).")

    def put(self, record, data, raw=False):
        out = {self._ss_def_name: data}
        out = convert.dict_to_xml(out)
        try:
            val = int(record)
        except ValueError:
            if hasattr(self,'_put_by_name') and self._put_by_name:
                end = f'{self._p_endpoint}/name/{record}'
                return self.session.post(end, out, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
            return self.session.post(end, out, raw)
        end = f'{self._p_endpoint}/id/{val}'
        return self.session.post(end, out, raw)

    def post(self, record, data, raw=False):
        out = {self._ss_def_name: data}
        out = convert.dict_to_xml(out)
        try:
            val = int(record)
        except ValueError:
            if hasattr(self,'_post_by_name') and self._post_by_name:
                end = f'{self._p_endpoint}/name/{record}'
                return self.session.post(end, out, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
            return self.session.post(end, out, raw)
        end = f'{self._p_endpoint}/id/{val}'
        return self.session.post(end, out, raw)

    def delete(self, record, raw=False):
        try:
            val = int(record)
        except ValueError:
            if hasattr(self,'_delete_by_name') and self._delete_by_name:
                end = f'{self._p_endpoint}/name/{record}'
                return self.session.delete(end, raw)
            else:
                raise JamfError("Endpoint does not support put by name.")
        end = f'{self._p_endpoint}/id/{val}'
        return self.session.delete(end, raw)

    def print(self):
        pprint(self)

class AdvancedComputerSearches(Record):
    _put_by_name = True,
    _post_by_name = True,
    _delete_by_name = True
    def __new__(cls):
        return super().__new__(cls)

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class AdvancedMobileDeviceSearches(Record):
    def __new__(cls):
        return super().__new__(cls)


class AdvancedUserSearches(Record):
    def __new__(cls):
        return super().__new__(cls)


class Buildings(Record):
    def __new__(cls):
        return super().__new__(cls)


class BYOProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class Categories(Record):
    def __new__(cls):
        return super().__new__(cls)


class Classes(Record):
    def __new__(cls):
        return super().__new__(cls)


class ComputerConfigurations(Record):
    def __new__(cls):
        return super().__new__(cls)


class ComputerExtensionAttributes(Record):
    def __new__(cls):
        return super().__new__(cls)


class ComputerGroups(Record):
    def __new__(cls):
        return super().__new__(cls)

    def members(self, record):
        """
        returns a list of the group members when passed a record
        """
        return self.list_to_dict(
            record['computers']['computer']
        )


class ComputerReports(Record):
#     _ps_def_name2 = 'computer_report'
    _ss_def_name2 = 'computer_reports'
    def __new__(cls):
        return super().__new__(cls)


class Computers(Record):
    def __new__(cls):
        return super().__new__(cls)


class Departments(Record):
    def __new__(cls):
        return super().__new__(cls)


class DirectoryBindings(Record):
    def __new__(cls):
        return super().__new__(cls)


class DiskEncryptionConfigurations(Record):
    def __new__(cls):
        return super().__new__(cls)


class DistributionPoints(Record):
    def __new__(cls):
        return super().__new__(cls)


class DockItems(Record):
    def __new__(cls):
        return super().__new__(cls)


class Ebooks(Record):
    def __new__(cls):
        return super().__new__(cls)


class Ibeacons(Record):
    def __new__(cls):
        return super().__new__(cls)


class JSONWebTokenConfigurations(Record):
    def __new__(cls):
        return super().__new__(cls)


class LDAPServers(Record):
    def __new__(cls):
        return super().__new__(cls)


class LicensedSoftware(Record):
    def __new__(cls):
        return super().__new__(cls)


class MacApplications(Record):
    def __new__(cls):
        return super().__new__(cls)


class ManagedPreferenceProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceApplications(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceCommands(Record):
    _id = "uuid"
    _id2 = "uuid"
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceConfigurationProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceEnrollmentProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceExtensionAttributes(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceInvitations(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDeviceProvisioningProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class MobileDevices(Record):
    def __new__(cls):
        return super().__new__(cls)


class NetbootServers(Record):
    def __new__(cls):
        return super().__new__(cls)


class NetworkSegments(Record):
    def __new__(cls):
        return super().__new__(cls)


class OSXConfigurationProfiles(Record):
    def __new__(cls):
        return super().__new__(cls)


class Packages(Record):
    def __new__(cls):
        return super().__new__(cls)


class PatchExternalSources(Record):
    def __new__(cls):
        return super().__new__(cls)


class PatchInternalSources(Record):
    def __new__(cls):
        return super().__new__(cls)


class PatchPolicies(Record):
    def __new__(cls):
        return super().__new__(cls)

    def get_softwaretitleconfig(self, record=''):
        """ 7 is a good example """
        end = f'{self._p_endpoint}softwaretitleconfig/id/{record}'
        lst = self.session.get(end)[self._p_def_name][self._ss_def_name]
        return self.list_to_dict(lst)

    def post_softwaretitleconfig(self, record, data, raw=False):
        if isinstance(data, dict):
            out = []
            out[self._p_def_name][self._ss_def_name] = data
        end = f'{self._p_endpoint}softwaretitleconfig/id/{record}'
        return self.session.post(end, data, raw)

class PatchSoftwareTitles(Record):
    def __new__(cls):
        return super().__new__(cls)


class Peripherals(Record):
    def __new__(cls):
        return super().__new__(cls)


class PeripheralTypes(Record):
    def __new__(cls):
        return super().__new__(cls)


class Policies(Record):
    def __new__(cls):
        return super().__new__(cls)

    def scope(self, record):
        """
        returns a dict of the scope categories to the policy when passed a record
        """
        from pprint import pprint
        return record['scope']


class Printers(Record):
    def __new__(cls):
        return super().__new__(cls)


class RemovableMACAddresses(Record):
    def __new__(cls):
        return super().__new__(cls)


class RestrictedSoftware(Record):
    _ps_def_name2 = 'restricted_software_title'
    _ss_def_name2 = 'restricted_software'
    def __new__(cls):
        return super().__new__(cls)


class Scripts(Record):
    def __new__(cls):
        return super().__new__(cls)


class Sites(Record):
    def __new__(cls):
        return super().__new__(cls)


class SoftwareUpdateServers(Record):
    def __new__(cls):
        return super().__new__(cls)


class UserExtensionAttributes(Record):
    def __new__(cls):
        return super().__new__(cls)


class UserGroups(Record):
    def __new__(cls):
        return super().__new__(cls)


class Users(Record):
    def __new__(cls):
        return super().__new__(cls)


class VPPAccounts(Record):
    def __new__(cls):
        return super().__new__(cls)


class VPPAssignments(Record):
    def __new__(cls):
        return super().__new__(cls)


class VPPInvitations(Record):
    def __new__(cls):
        return super().__new__(cls)


class WebHooks(Record):
    def __new__(cls):
        return super().__new__(cls)
