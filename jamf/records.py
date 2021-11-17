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
__version__ = "0.4.3"


#pylint: disable=relative-beyond-top-level
from .api import API
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
        exit(1)

#pylint: disable=super-init-not-called
class NotFound(Exception):
    pass

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
        ]
        post_template2 = {'general':{'name':'%NAME%'}}
        self._post_templates = {
            'BYOProfiles': post_template2,
            'ComputerConfigurations': post_template2,
            'ComputerReports': post_template2,
            'DirectoryBindings': post_template2,
            'Ebooks': post_template2,
            'JSONWebTokenConfigurations': post_template2,
#            'LicensedSoftware': post_template2,
#            'LDAPServers': post_template2,
            'MacApplications': post_template2,
            'ManagedPreferenceProfiles': post_template2,
            'MobileDevices': post_template2,
            'MobileDeviceApplications': post_template2,
            'MobileDeviceConfigurationProfiles': post_template2,
            'MobileDeviceEnrollmentProfiles': post_template2,
            'MobileDeviceProvisioningProfiles': post_template2,
            'OSXConfigurationProfiles': post_template2,
            'PatchPolicies': post_template2,
            'Peripherals': post_template2,
            'Policies': post_template2,
            'SoftwareUpdateServers': post_template2,
            'VPPAccounts': post_template2,
            'VPPAssignments': post_template2,
            'VPPInvitations': post_template2,

            'ComputerGroups': {'name':'%NAME%','is_smart':True},
            'DistributionPoints': {
                'name':'%NAME%',
                'read_only_username':'read_only_username',
                'read_write_username':'read_write_username',
                'share_name':'files'
            },
            'DockItems': {
                'name':'%NAME%',
                'path':'file://localhost/Applications/Safari.app/', 'type':'App'
            },
            'Ibeacons': {
                'name':'%NAME%',
                'uuid': '7710B6A4-FD29-4647-B2F4-B3FA645146A8' # I don't have iBeacons, I don't know the purpose of this value, I got it with `uuidgen` (https://support.twocanoes.com/hc/en-us/articles/203081205-Managing-Printers-with-iBeacons)
            },
            'NetbootServers': {'name':'%NAME%','ip_address':'10.0.0.1'},
            'NetworkSegments': {
                'name':'%NAME%',
                'starting_address':'10.0.0.1',
                'ending_address':'10.0.0.1'
            },
            'Packages': {
                'name':'%NAME%',
                'filename': 'filename.pkg',
            },
            'PatchExternalSources': {
                'name':'%NAME%',
                'host_name':'example.com',
            },
            'PatchSoftwareTitles': {'name':'%NAME%', 'source_id':'1'},
#            'RestrictedSoftware': {'general':{'name':'%NAME%','process_name':'%NAME%'}},
            'UserGroups': {
                'general':{'name':'%NAME%'},
                'is_smart':False
            },
            'WebHooks': {
                'event': 'ComputerAdded',
                'name':'%NAME%',
                'url': 'http:/example.com',
            },
        }
        self._swagger_fixes = {
            'ComputerConfigurations':{
                's2':'configuration',
            },
            'ComputerReports': {
                's1':'computer_reports',
            },
            'MobileDeviceCommands': {
                'id_text1':'uuid',
                'id_text2':'uuid',
            },
            'RestrictedSoftware': {
                'p3':'restricted_software_title',
                's1':'restricted_software'
            },
        }

    def post_template(self, className, name):
        if className in self._post_templates:
            template = self._post_templates[className]
            if 'name' in template:
                template['name'] = template['name'].replace('%NAME%', name)
            elif 'name_id' in template:
                template['name_id'] = template['name_id'].replace('%NAME%', name)
            elif 'general' in template and 'name' in template['general']:
                t = template['general']['name']
                template['general']['name'] = t.replace('%NAME%', name)
        else:
            template = {'name':name}
        return template

    def swagger(self, cls, kk):
        fixes = {}
        if cls.__name__ in self._swagger_fixes:
            fixes = self._swagger_fixes[cls.__name__]

        # The endpoint url, e.g. "Policies" class becomes "policies" endpoint
        if 'p1' in fixes:
            p1 = fixes['p1']
        else:
            p1 = cls.__name__.lower()
        if kk == 'path_name':
            return p1

        # Get the definition name, which almost always is the plural name
        # exceptions: LicensedSoftware, RestrictedSoftware?
        if 'p2' in fixes:
            p2 = fixes['p2']
        else:
            p2 = self.get_schema(p1)
            # If there's an xml entry, use it for the definition name
            temp2 = self._swagger['definitions'][p2]
            if ('xml' in temp2 and 'name' in temp2['xml']):
                p2 = temp2['xml']['name']
        if kk == 'def_name':
            return p2

        if 'id_text1' in fixes:
            id1 = fixes['id_text1']
        else:
            id1 = 'id'
        if kk == 'id1':
            return id1

        if kk == 'p1, id1':
            return p1, id1

        end = f'{p1}/{id1}/'

        if kk == 'end':
            return end

        if 'id_text2' in fixes:
            id2 = fixes['id_text2']
        else:
            id2 = 'id'
        if kk == 'id2':
            return id2

        # Get the schema, which almost always is the singular name
        if 'p3' in fixes:
            p3 = fixes['p3']
        else:
            temp1 = f"{p1}/{id1}/{{{id2}}}"
            p3 = self.get_schema(temp1)
        if kk == 'p3':
            return p3

        if kk == 'p1, p2, id1, p3':
            return p1, p2, id1, p3

        # Singular, which almost always is the p3
        if 's1' in fixes:
            s1 = fixes['s1']
        else:
            s1 = p3
        if kk == 's1':
            return s1

        # This is the name of the endpoint when it's returned from a post
        # e.g. ComputerConfigurations: {'configuration': {'general': {'name': 'rfwlkzis'}}}
        if 's2' in fixes:
            s2 = fixes['s2']
        else:
            s2 = s1
        if kk == 's2':
            return s2

        if kk == 's1, end':
            return s1, end

        if kk == 's1, s2, end':
            return s1, s2, end

    def get_schema(self, swagger_path):
        temp1 = self._swagger['paths']['/'+swagger_path]['get']
        schema = temp1['responses']['200']['schema']['$ref']
        if schema.startswith("#/definitions/"):
            schema = schema[14:]
        return schema

    def is_action_valid(self, className, action):
        p1, id1 = self.swagger(className, 'p1, id1')
        p = f'/{p1}/{id1}/{{{id1}}}'
        if className == PatchPolicies and action == "post":
            p = '/patchpolicies/softwaretitleconfig/id/{softwaretitleconfigid}'
        if p in self._broken_api:
            return False
        return p in self._swagger['paths'] and action in self._swagger['paths'][p]


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

    def __new__(cls, *a, **kw):
        """
        returns existing record if one has been instantiated
        """
        jamf_id = int(a[0])
        name = a[1]
        if not hasattr(cls, "_instances"):
            cls._instances = {}
        swag = ClassicSwagger()
        plural = eval(cls.plural_class)
        api = API()
        _data = {}
        if jamf_id == 0:
            if not swag.is_action_valid(plural, 'post'):
                print(f"Creating a new record with an id of 0 causes a post, "
                      f"which isn't a valid action for the {cls.plural_class} "
                      f"record type.")
                return None
            s1, s2, end = swag.swagger(plural, 's1, s2, end')
            if cls.plural_class == "PatchPolicies":
                print("Use /patchpolicies/softwaretitleconfig/id/{softwaretitleconfigid}"
                      " instead")
                return None
            end = f"{end}0"
            out = {s1: swag.post_template(cls.plural_class, name)}
            _data = api.post(end, out)
            jamf_id = int(_data[s2]['id'])
        if jamf_id not in cls._instances:
            rec = super(Record, cls).__new__(cls)
            rec.cls = cls
            rec.plural = plural
            cls._instances[jamf_id] = rec
        rec.api = api
        rec = cls._instances[jamf_id]
        rec.id = int(jamf_id)
        rec._data = _data
        rec.s = swag
        rec.name = name
        return rec

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
        s1, end = self.s.swagger(self.plural, 's1, end')
        end = f"{end}{self.id}"
        if not self.s.is_action_valid(self.plural, 'get'):
            raise JamfError(f'get({end}) is an invalid action for get')
        results = self.api.get(end)
        if not s1 in results:
            print("---------------------------------------------\nData dump\n")
            pprint(results)
            raise JamfError(f"Endpoint {end} has no member named {s1} (s1).")
        if results[s1]:
            self._data = results[s1]
        else:
            self._data = {}

    def delete(self):
        end = self.s.swagger(self.plural, 'end')
        end = f"{end}{self.id}"
        if not self.s.is_action_valid(self.plural, 'delete'):
            raise JamfError(f'{end} is an invalid endpoint for delete')
        return self.api.delete(end)

    def save(self):
        s1, end = self.s.swagger(self.plural, 's1, end')
        end = f"{end}{self.id}"
        if not self.s.is_action_valid(self.plural, 'put'):
            raise JamfError(f'{end} is an invalid endpoint for put')
        out = {s1: self._data}
        return self.api.put(end, out)

    @property
    def data(self):
        if not self._data:
            self.refresh()
        return self._data

    def get_path2(self, path, placeholder, index=0):
        current = path[index]
        if type(placeholder) is dict:
            if current in placeholder:
                if index+1 >= len(path):
                    return placeholder[current]
                placeholder = self.get_path2(path, placeholder[current], index+1)
            else:
                return None
        elif type(placeholder) is list:
            # I'm not sure this is the best way to handle arrays...
            result = []
            for item in placeholder:
                if current in item:
                    if index+1 < len(path):
                        result.append(self.get_path2(path, item[current], index+1))
                    else:
                        result.append(item[current])
            placeholder = result
        elif placeholder == None:
            return None
        else:
            print("Something went wrong in get_path2")
            exit()
        return placeholder

    def get_path(self, path):
        if not self._data:
            self.refresh()
        try:
            result = self.get_path2(path.split('/'), self._data)
        except NotFound as error:
            print("Not Found")
            result = []
        if type(result) is list or type(result) is dict or result == None:
            return result
        return [result]

    def force_array(self, parent, child_name):
        _data = parent[child_name]
        if 'size' in parent:
            if int(parent['size']) > 1:
                return _data
        else:
            if type(_data) is list:
                return _data
        return [_data]

    def set_path(self, path, value):
        temp1 = path.split('/')
        endpoint = temp1.pop()
        temp2 = "/".join(temp1)
        if len(temp2) > 0:
            placeholder = self.get_path(temp2)
        else:
            if not self._data:
                self.refresh()
            placeholder = self._data
        if placeholder:
            if endpoint in placeholder:
                placeholder[endpoint] = value
                return True
            else:
                print(f"Error: '{endpoint}' missing from ")
                pprint(placeholder)
                return False
        else:
            print(f"Error: empty data:")
            pprint(placeholder)
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

    def __iter__(self):
        return RecordsIterator(self)

    def __getitem__(self, item):
        return self.recordWithId(self.ids()[item])

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
        p1, p2, id1, p3 = self.s.swagger(self.cls, 'p1, p2, id1, p3')
        lst = self.api.get(p1)           # e.g. categories
        if p2 in lst:
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

    def createNewRecord(self, args):
        return self.singular_class(0, args)

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
    def apps_print_during(self):
        plural_cls = eval(self.cls.plural_class)
        if not hasattr(plural_cls, 'app_list'):
            plural_cls.app_list = {}
        if not hasattr(plural_cls, 'computers'):
            plural_cls.computers = {}
        plural_cls.computers[self.name] = True
        apps = self.get_path("software/applications/application/path")
        versions = self.get_path("software/applications/application/version")
        if apps:
            for ii, app in enumerate(apps):
                ver = versions[ii]
                if not app in plural_cls.app_list:
                    plural_cls.app_list[app] = {}
                if not ver in plural_cls.app_list[app]:
                    plural_cls.app_list[app][ver] = {}
                plural_cls.app_list[app][ver][self.name] = True

class Computers(Records, metaclass=Singleton):
    # http://localhost/computers.html?queryType=COMPUTERS&query=
    singular_class = Computer
    sub_commands = {
        'apps': {
            'required_args': 0,
            'args_description': ''
        }
    }
    def apps_print_after(self):
        print("application,version,", end='')
        for computer in self.computers:
            print(computer, ",", end='')
        print("")
        for app, versions in self.app_list.items():
            for version, bla in versions.items():
                text = f"\"{app}\",\"{version}\","
                print(text, end='')
                for computer in self.computers:
                    if computer in bla:
                        print("X,", end='')
                    else:
                        print(",", end='')
                print("")


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

    @property
    def metadata(self):
        if not hasattr(self, 'meta'):
            self._metadata = {}
            m = re.match("([^-]*)-(.*)\.([^\.]*)$", self.name)
            if m:
                self._metadata['basename'] = m[1]
                self._metadata['version'] = m[2]
                self._metadata['filetype'] = m[3]
            else:
                m = re.match("([^-]*)\.([^\.]*)$", self.name)
                if m:
                    self._metadata['basename'] = m[1]
                    self._metadata['version'] = ""
                    self._metadata['filetype'] = m[2]
                else:
                    self._metadata['basename'] = self.name
                    self._metadata['version'] = ""
                    self._metadata['filetype'] = ""
            if not self._metadata['basename'] in self.plural.groups:
                self.plural.groups[self._metadata['basename']] = []
            self.plural.groups[self._metadata['basename']].append(self)
        return self._metadata

    def refresh_related(self):
        related = {}
        patchsoftwaretitles = jamf_records(PatchSoftwareTitles)
        patchsoftwaretitles_ids = {}
        for title in patchsoftwaretitles:
            pkgs = title.get_path("versions/version/package/name")
            versions = title.get_path("versions/version/software_version")
            if pkgs:
                for ii, pkg in enumerate(pkgs):
                    if pkg == None:
                        continue
                    if not str(title.id) in patchsoftwaretitles_ids:
                        patchsoftwaretitles_ids[str(title.id)] = {}
                    patchsoftwaretitles_ids[str(title.id)][versions[ii]] = pkg
                    if not pkg in related:
                        related[pkg] = {'patchsoftwaretitles':[]}
                    if not 'patchsoftwaretitles' in related[pkg]:
                        related[pkg]['patchsoftwaretitles'] = []
                    temp = title.name+" - "+versions[ii]
                    related[pkg]['patchsoftwaretitles'].append(temp)
        patchpolicies = jamf_records(PatchPolicies)
        for policy in patchpolicies:
            parent_id = policy.get_path("software_title_configuration_id")[0]
            parent_version = policy.get_path("general/target_version")[0]
            if str(parent_id) in patchsoftwaretitles_ids:
                ppp = patchsoftwaretitles_ids[str(parent_id)]
                if parent_version in ppp:
                    pkg = ppp[parent_version]
                    if not pkg in related:
                        related[pkg] = {'patchpolicies':[]}
                    if not 'patchpolicies' in related[pkg]:
                        related[pkg]['patchpolicies'] = []
                    related[pkg]['patchpolicies'].append(policy.name)
        policies = jamf_records(Policies)
        for policy in policies:
            pkgs = policy.get_path("package_configuration/packages/package/name")
            if pkgs:
                for pkg in pkgs:
                    if not pkg in related:
                        related[pkg] = {'policies':[]}
                    if not 'policies' in related[pkg]:
                        related[pkg]['policies'] = []
                    related[pkg]['policies'].append(policy.name)
        groups = jamf_records(ComputerGroups)
        for group in groups:
            criterions = group.get_path("criteria/criterion/value")
            if criterions:
                for pkg in criterions:
                    if pkg and re.search(".pkg|.zip|.dmg", pkg[-4:]):
                        if not pkg in related:
                            related[pkg] = {'groups':[]}
                        if not 'groups' in related[pkg]:
                            related[pkg]['groups'] = []
                        related[pkg]['groups'].append(group.name)
        self.__class__._related = related

    @property
    def related(self):
        if not hasattr(self.__class__, '_related'):
            self.refresh_related()
        if self.name in self.__class__._related:
            return self.__class__._related[self.name]
        else:
            return {}

    def usage_print_during(self):
        related = self.related
        if 'patchsoftwaretitles' in related:
            print(self.name)
        else:
            print(f"{self.name} [no patch defined]")
        if 'policies' in related:
            print("  Policies")
            for x in related['policies']:
                print("    "+x)
        if 'groups' in related:
            print("  ComputerGroups")
            for x in related['groups']:
                print("    "+x)
        if 'patchpolicies' in related:
            print("  PatchPolicies")
            for x in related['patchpolicies']:
                print("    "+x)
        print()


class Packages(Records, metaclass=Singleton):
    singular_class = Package
    groups = {}
    sub_commands = {
        'usage': {
            'required_args': 0,
            'args_description': ''
        },
    }


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

    def set_version_update_during(self, pkg_version):
        change_made = False
        cur_ver = self.data['general']['target_version']

        #######################################################################
        # If you don't delete the self_service_icon then it will error
        #   <Response [409]>: PUT - https://example.com:8443/JSSResource/patchpolicies/id/18:
        #   Conflict: Error: Problem with icon
        #   Couldn't save changed record: <Response [409]>
        del(self.data['user_interaction']['self_service_icon'])
        #######################################################################

        if cur_ver != pkg_version:
            print(f"Set version to {pkg_version}")
            self.data['general']['target_version'] = pkg_version
            change_made = True
        else:
            print(f"Version is already {pkg_version}")
        return change_made


class PatchPolicies(Records, metaclass=Singleton):
    singular_class = PatchPolicy
    sub_commands = {
        'set_version': {
            'required_args': 1,
            'args_description': ''
        },
    }


class PatchSoftwareTitle(Record):
    plural_class = "PatchSoftwareTitles"

    def packages_print_during(self):
        print(self.name)
        versions = self.data['versions']['version']
        if not type(versions) is list:
            versions = [ versions ]
        for version in versions:
            if version['package'] != None:
                print(f" {version['software_version']}: {version['package']['name']}")

    def patchpolicies_print_during(self):
        print(self.name)
        patchpolicies = jamf_records(PatchPolicies)
        for policy in patchpolicies:
            parent_id = policy.get_path("software_title_configuration_id")[0]
            if str(parent_id) != str(self.id):
                continue
            print(" "+str(policy))

    def set_all_packages_update_during(self):
        policy_regex = {
            '1Password 7': '^1Password-%VERSION%\.pkg',
            'Apple GarageBand 10': '^GarageBand-%VERSION%\.pkg',
            'Apple Keynote': '^Keynote-%VERSION%\.pkg',
            'Apple Numbers': '^Numbers-%VERSION%\.pkg',
            'Apple Pages': '^Pages-%VERSION%\.pkg',
            'Apple Xcode': '^Xcode-%VERSION%\.pkg',
            'Apple iMovie': '^iMovie-%VERSION%\.pkg',
            'Arduino IDE': '^Arduino-%VERSION%\.pkg',
            'Bare Bones BBEdit':'BBEdit-%VERSION%\.pkg',
            'BusyCal 3': '^BusyCal-%VERSION%\.pkg',
            'Microsoft Remote Desktop 10': '^Microsoft Remote Desktop-%VERSION%\.pkg',
            'Microsoft Visual Studio Code': '^Visual Studio Code-%VERSION%\.pkg',
            'Microsoft Teams': '^Microsoft_Teams_%VERSION%\.pkg',
            'Mozilla Firefox': '^Firefox-%VERSION%\.pkg',
            'R for Statistical Computing': '^R-%VERSION%\.pkg',
            'RStudio Desktop': 'RStudio-%VERSION%\.dmg',
            'Sublime Text 3': 'Sublime Text-%VERSION%\.pkg',
            'VLC media player': 'VLC-%VERSION%\.pkg',
            'VMware Fusion 12': 'VMware Fusion-%VERSION%\.pkg',
            'VMware Horizon 8 Client': 'VMwareHorizonClient-%VERSION%.pkg',
            'Zoom Client for Meetings': 'Zoom-%VERSION%.pkg',
        }
        change_made = False
        packages = jamf_records(Packages)
        versions = self.data['versions']['version']
        if not type(versions) is list:
            versions = [ versions ]
        for pkg_version in versions:
            for package in packages:
                if not pkg_version['package']:
                    if self.name in policy_regex:
                        regex = policy_regex[self.name]
                        regex = regex.replace("%VERSION%",pkg_version['software_version'])
                    else:
                        regex = f".*{self.name}.*{pkg_version['software_version']}\.pkg"
                    regex = regex.replace("(", "\\(")
                    regex = regex.replace(")", "\\)")
                    if re.search(regex, package.name):
                        print(f"Matched {package.name}")
                        pkg_version['package'] = {'name':package.name}
                        change_made = True
        return change_made

    def set_package_for_version_update_during(self, package, target_version):
        change_made = False
        versions = self.data['versions']['version']
        if not type(versions) is list:
            versions = [ versions ]
        for pkg_version in versions:
            if pkg_version['software_version'] == target_version:
                print(f"{target_version}: {package}")
                pkg_version['package'] = {'name':package}
                change_made = True
        return change_made


class PatchSoftwareTitles(Records, metaclass=Singleton):
    singular_class = PatchSoftwareTitle
    sub_commands = {
        'patchpolicies': {
            'required_args': 0,
            'args_description': ''
        },
        'packages': {
            'required_args': 0,
            'args_description': ''
        },
        'set_package_for_version': {
            'required_args': 2,
            'args_description': ''
        },
        'set_all_packages': {
            'required_args': 0,
            'args_description': ''
        },
    }


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

    def spreadsheet_print_during(self):
        print(self.spreadsheet())

    def spreadsheet(self):

        # Name
        _text = f"{self.name}\t"
        # Category
        _text += f"{self.data['general']['category']['name']}\t"
        # Frequency
        _text += f"{self.data['general']['frequency']}\t"

        # Trigger
        _trigger = []
        if self.data['general']['trigger_other']:
            _trigger.append(f"{self.data['general']['trigger_other']}")
        if self.data['general']['trigger_enrollment_complete'] == "true":
            _trigger.append("Enrollment")
        if self.data['general']['trigger_startup'] == "true":
            _trigger.append("Startup")
        if self.data['general']['trigger_login'] == "true":
            _trigger.append("Login")
        if self.data['general']['trigger_logout'] == "true":
            _trigger.append("Logout")
        if self.data['general']['trigger_network_state_changed'] == "true":
            _trigger.append("Network")
        if self.data['general']['trigger_checkin'] == "true":
            _trigger.append("Checkin")
        _text += ", ".join(_trigger)
        _text += "\t"

        # Scope
        _scope = []
        if self.data['scope']['all_computers'] == 'true':
            _scope.append("all_computers")
        if self.data['scope']['buildings']:
            for a in self.force_array(self.data['scope']['buildings'], 'building'):
                _scope.append(a['name'])
        if self.data['scope']['computer_groups']:
            for a in self.force_array(self.data['scope']['computer_groups'], 'computer_group'):
                _scope.append(a['name'])
        if self.data['scope']['computers']:
            for a in self.force_array(self.data['scope']['computers'], 'computer'):
                _scope.append(a['name'])
        if self.data['scope']['departments']:
            for a in self.force_array(self.data['scope']['departments'], 'department'):
                _scope.append(a['name'])
        if self.data['scope']['limit_to_users']['user_groups']:
            _scope.append("limit_to_users")
        _text += ", ".join(_scope)
        _text += "\t"

        # Packages
        if self.data['package_configuration']['packages']['size'] != '0':
            for a in self.force_array(self.data['package_configuration']['packages'], 'package'):
                _text +=  a['name']
        _text += "\t"

        # Printers
        if self.data['printers']['size'] != '0':
            for a in self.force_array(self.data['printers'], 'printer'):
                _text +=  a['name']

            _text += self.data['printers']['size']
        _text += "\t"

        # Scripts
        if self.data['scripts']['size'] != '0':
            for a in self.force_array(self.data['scripts'], 'script'):
                _text +=  a['name']
        _text += "\t"

        # Self Service
        _self_service = []
        if self.data['self_service']['use_for_self_service'] != 'false':
            _self_service.append('Yes')
        if len(_self_service) > 0:
            _text += ", ".join(_self_service)
        _text += "\t"

        ###############

        # Account Maintenance
        if self.data['account_maintenance']['accounts']['size'] != '0':
            for a in self.force_array(self.data['account_maintenance']['accounts'], 'account'):
                _text +=  a['username']
        _text += "\t"

        # Disk Encryption
        if self.data['disk_encryption']['action'] != 'none':
            _text += self.data['disk_encryption']['action']
        _text += "\t"

        # Dock Items
        if self.data['dock_items']['size'] != '0':
            _text += self.data['dock_items']['size']
        _text += "\t"

        return _text

    def promote_update_during(self):
        if not 'package' in self.data['package_configuration']['packages']:
            print(f"{self.name} has no package to update.")
            return True
        if int(self.data['package_configuration']['packages']['size']) > 1:
            my_packages = self.data['package_configuration']['packages']['package']
        else:
            my_packages = [self.data['package_configuration']['packages']['package']]

        all_packages = jamf_records(Packages)
        print(self.name)
        made_change = False
        for my_package in my_packages:
            similar_packages = []
            search_str = re.sub('-.*', '', my_package['name'])
            for package in all_packages:
                if package.name.find(search_str) == 0:
                    similar_packages.append(package.name)
            if len(similar_packages) > 1:
                index = 1
                for similar_package in reversed(similar_packages):
                    if similar_package == my_package['name']:
                        print(f"  {index}. {similar_package} [Current]")
                    else:
                        print(f"  {index}. {similar_package}")
                    index += 1
                answer = "0"
                choices = list(map(str, range(1, index)))
                choices.append('')
                while answer not in choices:
                    answer = input("Choose a package [return skips]: ")
                if answer == '':
                    return True
                answer = len(similar_packages)-int(answer)
                my_package['name'] = similar_packages[answer]
                del my_package['id']
                made_change = True
        if made_change:
            pprint(self.data['package_configuration']['packages'])
            self.save()


class Policies(Records, metaclass=Singleton):
    singular_class = Policy
    sub_commands = {
        'promote': {
            'required_args': 0,
            'args_description': ''
        },
        'spreadsheet': {
            'required_args': 0,
            'args_description': ''
        },
    }

    def spreadsheet_print_before(self):
        header = [
            'Name',
            'Category',
            'Frequency',
            'Trigger',
            'Scope',
            'Packages',
            'Printers',
            'Scripts',
            'Self Service',
            'Account Maintenance',
            'Disk Encryption',
            'Dock Items',
        ]
        print("\t".join(header))

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

    def script_contents_print_during(self):
        printme = self.get_path("script_contents")
        print(printme[0])


class Scripts(Records, metaclass=Singleton):
    # http://localhost/view/settings/computer/scripts
    singular_class = Script
    sub_commands = {
        'script_contents': {
            'required_args': 0,
            'args_description': ''
        },
    }


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
