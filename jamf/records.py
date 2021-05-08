#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Record and Records

Combination of Sam Forester's Category class and Tony Williams' Records class
with lots of gluing, fleshing out, and other improvements by James Reynolds

James Reynolds reynolds@biology.utah.edu
Sam Forester sam.forester@utah.edu
Tony Williams tonyw@honestpuck.com

Copyright (c) 2020 University of Utah, Marriott Library
Copyright (c) 2020 Tony Williams
"""

__author__ = 'James Reynolds, Sam Forester, Tony Williams'
__email__ = 'reynolds@biology.utah.edu, sam.forester@utah.edu, tonyw@honestpuck.com'
__copyright__ = 'Copyright (c) 2021 University of Utah, School of Biological Sciences and Copyright (c) 2020 Tony Williams'
__license__ = 'MIT'
__date__ = '2020-09-21'
__version__ = "0.4.1"


#pylint: disable=relative-beyond-top-level
from .api import API
from os import _exit
from pprint import pprint
import json
import logging
import os.path
import re
import sys

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
    'DirectoryBindings',
    'DiskEncryptionConfigurations',
    'DistributionPoints',
    'DockItems',
    'Ebooks',
    'Ibeacons',
    'JSONWebTokenConfigurations',
    'LDAPServers',
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


class Singleton(type):
    """ allows us to share a single object """
    _instances = {}
    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class ClassicSwagger(metaclass=Singleton):
    def __init__(self):
        self._swagger = json.load(open(os.path.dirname(__file__)+'/records.json', 'r'))
        self._broken_api = [
            '/directorybindings/name/{name}',
            '/osxconfigurationprofiles/name/{name}',
        ]
        self._p1 = {
        }
        self._p2 = {
        }
        self._id_text2 = {
            'MobileDeviceCommands': 'uuid'
        }
        self._id_text1 = {
            'MobileDeviceCommands': 'uuid'
        }
        self._p3 = {
            'RestrictedSoftware': 'restricted_software_title'
        }
        self._s1 = {
            'ComputerReports': 'computer_reports',
            'RestrictedSoftware': 'restricted_software'
        }
        post_template2 = {'general':{'name':'%name%'}}
        self._post_templates = {
            'BYOProfile': post_template2,
            'ComputerConfiguration': post_template2,
            'ComputerReports': post_template2,
            'DirectoryBinding': post_template2,
            'Ebook': post_template2,
            'Ibeacon': post_template2,
            'JSONWebTokenConfiguration': post_template2,
#            'LicensedSoftware': post_template2,
#            'LDAPServers': post_template2,
            'MacApplication': post_template2,
            'ManagedPreferenceProfile': post_template2,
            'MobileDevice': post_template2,
            'MobileDeviceApplication': post_template2,
            'MobileDeviceConfigurationProfile': post_template2,
            'MobileDeviceEnrollmentProfile': post_template2,
            'MobileDeviceProvisioningProfile': post_template2,
            'OSXConfigurationProfile': post_template2,
            'Package': post_template2,
            'PatchPolicy': post_template2,
            'Peripheral': post_template2,
            'Policy': post_template2,
            'SoftwareUpdateServer': post_template2,
            'VPPAccount': post_template2,
            'VPPAssignment': post_template2,
            'VPPInvitation': post_template2,
            'WebHook': post_template2,
            'ComputerGroups': {'name':'%name%','is_smart':True},
            'DistributionPoint': {
                'name':'%name%',
                'read_only_username':'read_only_username',
                'read_write_username':'read_write_username',
                'share_name':'files'
            },
            'DockItem': {
                'name':'%name%',
                'path':'file://localhost/Applications/Safari.app/', 'type':'App'
            },
            'NetbootServer': {'name':'%name%','ip_address':'10.0.0.1'},
            'NetworkSegment': {
                'name':'%name%',
                'starting_address':'10.0.0.1',
                'ending_address':'10.0.0.1'
            },
            'PatchExternalSource': {
                'general':{'name':'%name%'},
                'displayName':'%name%',
                'remoteHostName':'%name%',
            },
            'PatchSoftwareTitle': {'name':'%name%', 'source_id':'1'},
#            'RestrictedSoftware': {'general':{'name':'%name%','process_name':'%name%'}},
            'UserGroup': {
                'general':{'name':'%name%'},
                'is_smart':False
            }
        }

    def s1(self, className):
        return self.swagger(className, "s1")

    def record_endpoint(self, className, recid):
        p1 = self.swagger(className, "path_name")
        id1 = self.swagger(className, "id1")
        s1 = self.swagger(className, "s1")
        return f'{p1}/{id1}/{recid}'

    def list_endpoint(self, className):
        p1 = self.swagger(className, "path_name")
        id1 = self.swagger(className, "id1")
        s1 = self.swagger(className, "s1")
        return f'{p1}/{id1}/{self.id}'

    def swagger(self, cls, value):
        # The endpoint url, e.g. "Policies" class becomes "policies" endpoint
        if cls.__name__ in self._p1:
            p1 = self._p1[cls.__name__]
        else:
            p1 = cls.__name__.lower()

        # Get the definition name, which almost always is the plural name
        # exceptions: LicensedSoftware, RestrictedSoftware?
        if cls.__name__ in self._p2:
            p2 = self._p2[cls.__name__]
        else:
            p2 = self.get_schema(p1)
            # If there's an xml entry, use it for the definition name
            temp2 = self._swagger['definitions'][p2]
            if ('xml' in temp2 and 'name' in temp2['xml']):
                p2 = temp2['xml']['name']

        if cls.__name__ in self._id_text1:
            id1 = self._id_text1[cls.__name__]
        else:
            id1 = "id"

        if cls.__name__ in self._id_text2:
            id2 = self._id_text2[cls.__name__]
        else:
            id2 = "id"

        # Get the schema, which almost always is the singular name
        if cls.__name__ in self._p3:
            p3 = self._p3[cls.__name__]
        else:
            temp1 = f"{p1}/{id1}/{{{id2}}}"
            p3 = self.get_schema(temp1)

        if cls.__name__ in self._s1:
            s1 = self._s1[cls.__name__]
        else:
            s1 = p3

#         if not hasattr(cls, '_list_to_dict_key'):
#             cls._list_to_dict_key = 'id'

        if value == "path_name":
            return p1
        if value == "def_name":
            return p2
        if value == "id1":
            return id1
        if value == "id2":
            return id2
        if value == "p3":
            return p3
        if value == "s1":
            return s1

    def get_schema(self, swagger_path):
        temp1 = self._swagger['paths']['/'+swagger_path]['get']
        schema = temp1['responses']['200']['schema']['$ref']
        if schema.startswith("#/definitions/"):
            schema = schema[14:]
        return schema

    def is_action_valid(self, className, a):
        p1 = self.swagger(className, "path_name")
        id1 = self.swagger(className, "id1")
        #id2 = self.swagger(self, className, "id2")???
        p = f'/{p1}/{id1}/{{{id1}}}'
        if p in self._broken_api:
            return False
        return p in self._swagger['paths'] and a in self._swagger['paths'][p]


class Record:
    """
    A class for an object on Jamf Pro

    NOTE: For reasons known only to itself Jamf uses 'wordstogether' for the
    endpoint in the URL but 'underscore_between' for the XML tags in some
    endpoints and there are cases where the endpoint and object tag are more
    different than that.

    This means we need to know 3 strings for each object type, the endpoint,
    the top of the list, and the top of the object.

    Just in case that's not confusing enough the id tag is not always 'id'.
    """

    def __new__(cls, jamf_id, name):
        """
        returns existing record if one has been instantiated
        """
        jamf_id = int(jamf_id)
        if not hasattr(cls, "_instances"):
            cls._instances = {}
        if jamf_id not in cls._instances:
            rec = super(Record, cls).__new__(cls)
            rec.cls = cls
            rec.plural = eval(cls.plural_class)
            cls._instances[jamf_id] = rec

        return cls._instances[jamf_id]

    def __init__(self, jamf_id, name):
        self.id = int(jamf_id)
        self._data = {}
        self.api = API()
        self.s = ClassicSwagger()
        self.name = name

    def __eq__(self, x):
        if isinstance(x, Record):
            return self is x
            # return self.name == x.name and self.id == x.id
        elif isinstance(x, int):
            return self.id == x
        elif isinstance(x, str):
            if x.isdigit() or x == '-1':
                return self.id == int(x)
            else:
                return self.name == x
        elif isinstance(x, dict):
            jamf_id = int(x.get('id', -1))
            return self.name == x.get('name') and self.id == jamf_id
        else:
            raise TypeError(f"can't test equality of {x!r}")

    def __lt__(self, x):
        if ( self.name and x.name and self.name < x.name ):
            return True
        return False

    def __str__(self):
        if self.name:
            return self.name
        else:
            return "Empty name"

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name!r})"

    def refresh(self):
        end = self.s.record_endpoint(self.plural, self.id)
        if not self.s.is_action_valid(self.plural, 'get'):
            raise JamfError(f'get({end}) is an invalid action for get')
        results = self.api.get(end)
        s1 = self.s.s1(self.plural)
        if not s1 in results:
            print("---------------------------------------------\nData dump\n")
            pprint(results)
            raise JamfError(f"Endpoint {end} has no member named {s1} (s1).")
        if results[s1]:
            self._data = results[s1]
        else:
            self._data = {}

    def delete(self, raw=False):
        end = self.s.record_endpoint(self.plural, self.id)
        if not self.s.is_action_valid(self.plural, 'delete'):
            raise JamfError(f'{end} is an invalid endpoint for delete')
        return self.api.delete(end, raw)

    def save(self):
        end = self.s.record_endpoint(self.plural, self.id)
        s1 = self.s.s1(self.plural)
        if not self.s.is_action_valid(self.plural, 'put'):
            raise JamfError(f'{end} is an invalid endpoint for put')
        out = {s1: self._data}
        return self.api.put(end, out)

    def data(self):
        if not self._data:
            self.refresh()
        return self._data

    def get_path(self, path):
        if not self._data:
            self.refresh()
        temp = path.split('/')
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
        temp1 = path.split('/')
        endpoint = temp1.pop()
        temp2 = "/".join(temp1)
        placeholder = self.get_path(temp2)
        if placeholder and endpoint in placeholder:
            placeholder[endpoint] = value
            return True
        else:
            return False


class RecordsIterator:
    def __init__(self, records):
        self._records = records
        self._ids = records.ids()
        self._index = 0

    def __next__(self):
        if self._index < (len(self._ids)):
            if self._index < len(self._ids):
                id = self._ids[self._index]
                result = self._records.recordWithId(id)
            self._index += 1
            return result
        # End of Iteration
        raise StopIteration


class Records():
    """
    A class for a list of objects on Jamf Pro

    NOTE: For reasons known only to itself Jamf uses 'wordstogether' for the
    endpoint in the URL but 'underscore_between' for the XML tags in some
    endpoints and there are cases where the endpoint and object tag are more
    different than that.

    This means we need to know 3 strings for each object type, the endpoint,
    the top of the list, and the top of the object.

    Just in case that's not confusing enough the id tag is not always 'id'.
    """

    def __new__(cls, *a, **kw):
        rec = super().__new__(cls)
        rec._records = {}
        rec.cls = cls
        rec.s = ClassicSwagger()
        return rec

    def __init__(self, api=None):
        self.log = logging.getLogger(f"{__name__}.Records")
        self.api = api or API()

        self.data = {}
        self._jamf_ids = {v.id: v for v in self._records.values()}
        self._names = {v.name: v for v in self._records.values()}

    def __contains__(self, x):
        return True if self.find(x) else False

    def names(self):
        if not self.data:
            self.refresh()
        return [x for x in self._names.keys()]

    def ids(self):
        if not self.data:
            self.refresh()
        return [x for x in self._jamf_ids.keys()]

    def recordWithId(self, x):
        if not self.data:
            self.refresh()
        return self._jamf_ids.get(x)

    def recordWithName(self, x):
        if not self.data:
            self.refresh()
        return self._names.get(x)

    def recordsWithRegex(self, x):
        if not self.data:
            self.refresh()
        found = []
        for name in self._names:
            if re.search(x, name):
                found.append(self._names[name])
        return found

    def refresh(self):
        p1 = self.s.swagger(self.cls, "path_name")
        lst = self.api.get(p1)           # e.g. categories
        p2 = self.s.swagger(self.cls, "def_name")
        if p2 in lst:
            id1 = self.s.swagger(self.cls, "id1")
            p3 = self.s.swagger(self.cls, "p3")
            self.data = lst[p2]
            if not self.data or not 'size' in self.data or self.data['size'] == '0':
                self._records = {}
                self._names = {}
                self._jamf_ids = {}
            elif p3 in self.data:         # e.g. category
                if self.data['size'] == '1':
                    records = [self.data[p3]]
                else:
                    records = self.data[p3]
                for d in records:
                    c = self.singular_class(d[id1], d['name'])# e.g. id
                    c.plural_class = self.cls
                    self._records.setdefault(int(d[id1]), c)# e.g. id
                    self._names.setdefault(c.name, c)
                    self._jamf_ids.setdefault(c.id, c)
            else:
                pprint(self.data)
                raise JamfError(f"Endpoint {p1} - "
                                f"{p2} has no member named "
                                f"{p3} (p3).")
        else:
            raise JamfError(f"Endpoint {p1} has no "
                            f"member named {p2}. Check "
                            f"the swagger definition file for the name of "
                            f"{p1} and set the property "
                            f"p2 for class ({p1}).")

    def find(self, x):
        if not self.data:
            self.refresh()
        if isinstance(x, int):
            # check for record id
            result = self._jamf_ids.get(x)
        elif isinstance(x, str):
            try:
                result = self._jamf_ids.get(int(x))
            except ValueError:
                result = self._names.get(x)
        elif isinstance(x, dict):
            keys = ('id', 'jamf_id', 'name')
            try:
                key = [k for k in x.keys() if k in keys][0]
            except IndexError:
                result = None
            else:
                if key in ('id', 'jamf_id'):
                    result = self._jamf_ids.get(int(x[key]))
                elif key == 'name':
                    result = self._names.get(key)
        elif isinstance(x, Record):
            result = x
        else:
            raise TypeError(f"can't look for {type(x)}")
        return result

    def __iter__(self):
        return RecordsIterator(self)


class AdvancedComputerSearch(Record):
    plural_class = "AdvancedComputerSearches"


class AdvancedComputerSearches(Records, metaclass=Singleton):
    # http://localhost/computers.html
    singular_class = AdvancedComputerSearch


class AdvancedMobileDeviceSearch(Record):
    plural_class = "AdvancedMobileDeviceSearches"


class AdvancedMobileDeviceSearches(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html
    singular_class = AdvancedMobileDeviceSearch


class AdvancedUserSearch(Record):
    plural_class = "AdvancedUserSearches"


class AdvancedUserSearches(Records, metaclass=Singleton):
    # http://localhost/users.html
    singular_class = AdvancedUserSearch


class Building(Record):
    plural_class = "Buildings"


class Buildings(Records, metaclass=Singleton):
    # http://localhost/view/settings/network/buildings
    singular_class = Building


class BYOProfile(Record):
    plural_class = "BYOProfiles"


class BYOProfiles(Records, metaclass=Singleton):
    singular_class = BYOProfile


class Category(Record):
    plural_class = "Categories"


class Categories(Records, metaclass=Singleton):
    # http://localhost/categories.html
    singular_class = Category


class Class(Record):
    plural_class = "Classes"


class Classes(Records, metaclass=Singleton):
    # http://localhost/classes.html
    singular_class = Class


class Computer(Record):
    plural_class = "Computers"


class Computers(Records, metaclass=Singleton):
    singular_class = Computer
    # http://localhost/computers.html?queryType=COMPUTERS&query=


class ComputerConfiguration(Record):
    plural_class = "ComputerConfigurations"


class ComputerConfigurations(Records, metaclass=Singleton):
    singular_class = ComputerConfiguration


class ComputerExtensionAttribute(Record):
    plural_class = "ComputerExtensionAttributes"


class ComputerExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/computerExtensionAttributes.html
    singular_class = ComputerExtensionAttribute


class ComputerGroup(Record):
    plural_class = "ComputerGroups"


class ComputerGroups(Records, metaclass=Singleton):
    # http://localhost/smartComputerGroups.html
    # http://localhost/staticComputerGroups.html
    singular_class = ComputerGroup


class ComputerReport(Record):
    plural_class = "ComputerReports"


class ComputerReports(Records, metaclass=Singleton):
    singular_class = ComputerReport


class Department(Record):
    plural_class = "Departments"


class Departments(Records, metaclass=Singleton):
    # http://localhost/departments.html
    singular_class = Department


class DirectoryBinding(Record):
    plural_class = "DirectoryBindings"


class DirectoryBindings(Records, metaclass=Singleton):
    singular_class = DirectoryBinding


class DiskEncryptionConfiguration(Record):
    plural_class = "DiskEncryptionConfigurations"


class DiskEncryptionConfigurations(Records, metaclass=Singleton):
    # http://localhost/diskEncryptions.html
    singular_class = DiskEncryptionConfiguration


class DistributionPoint(Record):
    plural_class = "DistributionPoints"


class DistributionPoints(Records, metaclass=Singleton):
    singular_class = DistributionPoint


class DockItem(Record):
    plural_class = "DockItems"


class DockItems(Records, metaclass=Singleton):
    # http://localhost/dockItems.html
    singular_class = DockItem


class Ebook(Record):
    plural_class = "Ebooks"


class Ebooks(Records, metaclass=Singleton):
    singular_class = Ebook


class Ibeacon(Record):
    plural_class = "Ibeacons"


class Ibeacons(Records, metaclass=Singleton):
    singular_class = Ibeacon


class JSONWebTokenConfiguration(Record):
    plural_class = "JSONWebTokenConfigurations"


class JSONWebTokenConfigurations(Records, metaclass=Singleton):
    singular_class = JSONWebTokenConfiguration


class LDAPServer(Record):
    plural_class = "LDAPServers"


class LDAPServers(Records, metaclass=Singleton):
    singular_class = LDAPServer


class MacApplication(Record):
    plural_class = "MacApplications"


class MacApplications(Records, metaclass=Singleton):
    singular_class = MacApplication


class ManagedPreferenceProfile(Record):
    plural_class = "ManagedPreferenceProfiles"


class ManagedPreferenceProfiles(Records, metaclass=Singleton):
    singular_class = ManagedPreferenceProfile


class MobileDevice(Record):
    plural_class = "MobileDevices"


class MobileDevices(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html?queryType=MOBILE_DEVICES&query=
    singular_class = MobileDevice


class MobileDeviceApplication(Record):
    plural_class = "MobileDeviceApplications"


class MobileDeviceApplications(Records, metaclass=Singleton):
    singular_class = MobileDeviceApplication


class MobileDeviceCommand(Record):
    plural_class = "MobileDeviceCommands"


class MobileDeviceCommands(Records, metaclass=Singleton):
    singular_class = MobileDeviceCommand


class MobileDeviceConfigurationProfile(Record):
    plural_class = "MobileDeviceConfigurationProfiles"


class MobileDeviceConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceConfigurationProfile


class MobileDeviceEnrollmentProfile(Record):
    plural_class = "MobileDeviceEnrollmentProfiles"


class MobileDeviceEnrollmentProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceEnrollmentProfile


class MobileDeviceExtensionAttribute(Record):
    plural_class = "MobileDeviceExtensionAttributes"


class MobileDeviceExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/mobileDeviceExtensionAttributes.html
    singular_class = MobileDeviceExtensionAttribute


class MobileDeviceInvitation(Record):
    plural_class = "MobileDeviceInvitations"


class MobileDeviceInvitations(Records, metaclass=Singleton):
    singular_class = MobileDeviceInvitation


class MobileDeviceProvisioningProfile(Record):
    plural_class = "MobileDeviceProvisioningProfiles"


class MobileDeviceProvisioningProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceProvisioningProfile


class NetbootServer(Record):
    plural_class = "NetbootServers"


class NetbootServers(Records, metaclass=Singleton):
    singular_class = NetbootServer


class NetworkSegment(Record):
    plural_class = "NetworkSegments"


class NetworkSegments(Records, metaclass=Singleton):
    singular_class = NetworkSegment


class OSXConfigurationProfile(Record):
    plural_class = "OSXConfigurationProfiles"


class OSXConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = OSXConfigurationProfile


class Package(Record):
    plural_class = "Packages"


class Packages(Records, metaclass=Singleton):
    singular_class = Package


class PatchExternalSource(Record):
    plural_class = "PatchExternalSources"



class PatchExternalSources(Records, metaclass=Singleton):
    singular_class = PatchExternalSource


class PatchInternalSource(Record):
    plural_class = "PatchInternalSources"


class PatchInternalSources(Records, metaclass=Singleton):
    singular_class = PatchInternalSource


class PatchPolicy(Record):
    plural_class = "PatchPolicies"


class PatchPolicies(Records, metaclass=Singleton):
    singular_class = PatchPolicy


class PatchSoftwareTitle(Record):
    plural_class = "PatchSoftwareTitles"


class PatchSoftwareTitles(Records, metaclass=Singleton):
    singular_class = PatchSoftwareTitle


class Peripheral(Record):
    plural_class = "Peripherals"


class Peripherals(Records, metaclass=Singleton):
    singular_class = Peripheral


class PeripheralType(Record):
    plural_class = "PeripheralTypes"


class PeripheralTypes(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = PeripheralType


class Policy(Record):
    plural_class = "Policies"


class Policies(Records, metaclass=Singleton):
    singular_class = Policy


class Printer(Record):
    plural_class = "Printers"


class Printers(Records, metaclass=Singleton):
    # http://localhost/printers.html
    singular_class = Printer


class RemovableMACAddress(Record):
    plural_class = "RemovableMACAddresses"


class RemovableMACAddresses(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = RemovableMACAddress


class Script(Record):
    plural_class = "Scripts"


class Scripts(Records, metaclass=Singleton):
    # http://localhost/view/settings/computer/scripts
    singular_class = Script


class Site(Record):
    plural_class = "Sites"


class Sites(Records, metaclass=Singleton):
    # http://localhost/sites.html
    singular_class = Site


class SoftwareUpdateServer(Record):
    plural_class = "SoftwareUpdateServers"


class SoftwareUpdateServers(Records, metaclass=Singleton):
    singular_class = SoftwareUpdateServer


class User(Record):
    plural_class = "Users"


class Users(Records, metaclass=Singleton):
    # http://localhost/users.html?query=
    singular_class = User


class UserExtensionAttribute(Record):
    plural_class = "UserExtensionAttributes"


class UserExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/userExtensionAttributes.html
    singular_class = UserExtensionAttribute


class UserGroup(Record):
    plural_class = "UserGroups"


class UserGroups(Records, metaclass=Singleton):
    singular_class = UserGroup


class VPPAccount(Record):
    plural_class = "VPPAccounts"


class VPPAccounts(Records, metaclass=Singleton):
    singular_class = VPPAccount


class VPPAssignment(Record):
    plural_class = "VPPAssignments"


class VPPAssignments(Records, metaclass=Singleton):
    singular_class = VPPAssignment


class VPPInvitation(Record):
    plural_class = "VPPInvitations"


class VPPInvitations(Records, metaclass=Singleton):
    singular_class = VPPInvitation


class WebHook(Record):
    plural_class = "WebHooks"


class WebHooks(Records, metaclass=Singleton):
    singular_class = WebHook


def jamf_records(cls, name='', exclude=()):
    """
    Get Jamf Records

    :param cls  <str>:       name of class
    :param name  <str>:      name in record['name']
    :param exclude  <iter>:  record['name'] not in exclude

    :returns:  list of dicts: [{'id': jamf_id, 'name': name}, ...]
    """
    # exclude specified records by full name
    included = [c for c in cls() if c.name not in exclude]
    # NOTE: empty string ('') always in all other strings
    return [c for c in included if name in c.name]

def categories(name='', exclude=()):
    """
    Get Jamf Categories

    :param name  <str>:      name in record['name']
    :param exclude  <iter>:  record['name'] not in exclude

    :returns:  list of dicts: [{'id': jamf_id, 'name': name}, ...]
    """
    return jamf_records(Categories, name, exclude)
