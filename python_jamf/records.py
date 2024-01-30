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

__author__ = "James Reynolds, Sam Forester, Tony Williams"
__email__ = "reynolds@biology.utah.edu, sam.forester@utah.edu, tonyw@honestpuck.com"
__copyright__ = "Copyright (c) 2021 University of Utah, School of Biological Sciences and Copyright (c) 2020 Tony Williams"
__license__ = "MIT"
__date__ = "2020-09-21"
__version__ = "0.4.7"


import logging
import random
import re
import string
import warnings
from pprint import pprint
from sys import stderr

from . import convert
from .exceptions import (
    JamfAPISurprise,
    JamfRecordInvalidPath,
    JamfRecordNotFound,
    JamfUnknownClass,
)

__all__ = (
    "AdvancedComputerSearches",
    "AdvancedMobileDeviceSearches",
    "AdvancedUserSearches",
    "Buildings",
    "BYOProfiles",
    "Categories",
    "Classes",
    "ComputerExtensionAttributes",
    "ComputerGroups",
    "ComputerReports",
    "Computers",
    "Departments",
    "DirectoryBindings",
    "DiskEncryptionConfigurations",
    "DistributionPoints",
    "DockItems",
    "Ebooks",
    "Ibeacons",
    "JSONWebTokenConfigurations",
    "LDAPServers",
    "MacApplications",
    "ManagedPreferenceProfiles",
    "MobileDeviceApplications",
    "MobileDeviceConfigurationProfiles",
    "MobileDeviceEnrollmentProfiles",
    "MobileDeviceExtensionAttributes",
    "MobileDeviceInvitations",
    "MobileDeviceProvisioningProfiles",
    "MobileDevices",
    "NetworkSegments",
    "OSXConfigurationProfiles",
    "Packages",
    "PatchExternalSources",
    "PatchInternalSources",
    "PatchPolicies",
    "PatchSoftwareTitles",
    "Peripherals",
    "PeripheralTypes",
    "Policies",
    "Printers",
    "RemovableMACAddresses",
    "Scripts",
    "Sites",
    "SoftwareUpdateServers",
    "UserExtensionAttributes",
    "UserGroups",
    "Users",
    "VPPAccounts",
    "VPPAssignments",
    "VPPInvitations",
    "WebHooks",
    # Add all non-Jamf Record classes to the exclude list in valid_records below
)


def valid_records():
    valid = tuple(
        x
        for x in __all__
        if x
        not in [
            # Exclude list, add all non-Jamf Record classes here
            "JamfError"
        ]
    )
    return valid


# pylint: disable=eval-used
def class_name(name, case_sensitive=True):
    if case_sensitive and name in valid_records():
        return eval(name)
    if not case_sensitive:
        for temp in valid_records():
            if name.lower() == temp.lower():
                return eval(temp)
    raise JamfUnknownClass(f"{name} is not a valid record.")


class Singleton(type):
    """allows us to share a single object"""

    _instances = {}

    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class Record:
    plurals = None
    name_path = "name"

    def __new__(cls, jamf_id, jamf_name):
        """
        returns existing record if one has been instantiated
        """
        if not hasattr(cls, "_instances"):
            cls._instances = {}
        jamf_id = int(jamf_id)
        if jamf_id not in cls._instances:
            rec = super(Record, cls).__new__(cls)
            rec.id = jamf_id
            rec.name = jamf_name
            rec._data = {}
            rec.plural = eval(cls.plural_class)
            rec.cls = cls
            if jamf_id != 0:
                cls._instances[jamf_id] = rec
        else:
            rec = cls._instances[jamf_id]
        return rec

    def __eq__(self, x):
        if isinstance(x, Record):
            return self is x
            # return self.name == x.name and self.id == x.id
        elif isinstance(x, int):
            return self.id == x
        elif isinstance(x, str):
            if x.isdigit() or x == "-1":
                return self.id == int(x)
            else:
                return self.name == x
        elif isinstance(x, dict):
            jamf_id = int(x.get("id", -1))
            return self.name == x.get("name") and self.id == jamf_id
        else:
            raise TypeError(f"can't test equality of {x!r}")

    def __lt__(self, x):
        if self.name and x.name and self.name < x.name:
            return True
        return False

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return ""

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name!r})"

    @property
    def data(self):
        if not self._data:
            self.refresh_data()
        return self._data

    def delete(self, refresh=True):
        if hasattr(self, "delete_method"):
            getattr(self.classic, self.delete_method)(self.id)
            if refresh:
                self.plural().refresh_records()

    def save(self):
        if hasattr(self, "update_method"):
            if isinstance(self._data, dict):
                if hasattr(self, "changed_data"):
                    data_copy = self.save_override(self.changed_data)
                    del self.changed_data
                else:
                    data_copy = self.save_override(self._data)
                newdata = {self.singular_string: data_copy}
                newdata = convert.dict_to_xml(newdata)
                newdata = newdata.encode("utf-8")
            getattr(self.classic, self.update_method)(newdata, id=self.id)
            self.refresh_data()
            self.name = self.get_data_name()

    def save_override(self, newdata):
        # Override this for records that get errors with empty values when updating
        return newdata

    def set_data_name(self, name):
        self.set_path(self.name_path, name)

    def get_data_name(self):
        return self.get_path(self.name_path)

    def refresh_data(self):
        results = getattr(self.classic, self.refresh_method)(self.id, data_type="xml")
        results = convert.xml_to_dict(results, self.plurals)
        if len(results) > 0:
            self._data = results[self.singular_string]
        else:
            self._data = None

    def refresh(self, *args, **kwargs):
        # For compatibility, deprecated
        self.refresh_data(*args, **kwargs)

    def get_path_worker(self, path, placeholder, idx=0):
        path_part = path[idx]
        search_parts = None
        if path_part[0] == "[" and path_part[-1] == "]":
            # Look ahead: Find the next record with a member that equals something
            search_parts = path_part[1:-1].split("==")
            path_part = search_parts[0]
        if type(placeholder) is dict:
            if path_part in placeholder:
                if idx + 1 >= len(path):
                    return placeholder[path_part]
                else:
                    placeholder = self.get_path_worker(
                        path, placeholder[path_part], idx + 1
                    )
            else:
                raise JamfRecordInvalidPath(
                    f"Path not found {path} ('{path_part}' missing)"
                )
        elif type(placeholder) is list:
            # I'm not sure this is the best way to handle arrays...
            result = []
            for item in placeholder:
                next_place = None
                if search_parts is not None:
                    if (
                        search_parts[0] in item
                        and item[search_parts[0]] == search_parts[1]
                    ):
                        next_place = item
                elif path_part in item:
                    next_place = item[path_part]
                if next_place is not None:
                    if idx + 1 < len(path):
                        more_next = self.get_path_worker(path, next_place, idx + 1)
                    else:
                        more_next = next_place
                    if search_parts is not None:
                        result = more_next
                    else:
                        result.append(more_next)
            placeholder = result
        return placeholder

    def get_path(self, path):
        result = self.get_path_worker(path.rstrip("/").split("/"), self.data)
        return result

    def force_array(self, parent, child_name):
        _data = parent[child_name]
        if "size" in parent:
            if int(parent["size"]) > 0:
                return _data
        else:
            if type(_data) is list:
                return _data
        return [_data]

    def set_path(self, path, value):
        path_parts = path.split("/")
        path_parts_bw = path_parts.copy()
        # First change the data
        endpoint = path_parts.pop()
        temp2 = "/".join(path_parts)
        success = True
        if len(temp2) > 0:
            placeholder = self.get_path(temp2)
        else:
            placeholder = self.data
        if placeholder:
            if endpoint in placeholder:
                placeholder[endpoint] = value
            else:
                # This is here because there are unanswered questions
                stderr.write(f"Error: '{endpoint}' missing from:")
                pprint(placeholder)
                success = False
        else:
            # This is here because there are unanswered questions
            stderr.write("Error: empty data:")
            pprint(placeholder)
            success = False
        # Track the changed data
        if success:
            # Note, this does not respect arrays!
            # This should only be used to .save()
            if "id" in placeholder:
                sibling = {"id": placeholder["id"]}
            elif endpoint in placeholder:
                sibling = {endpoint: placeholder[endpoint]}
            placeholder = value
            path_parts_bw.reverse()
            for path_part in path_parts_bw:
                if sibling is not None:
                    newdict = sibling
                    sibling = None
                else:
                    newdict = {}
                if path_part[0] == "[" and path_part[-1] == "]":
                    placeholder = [placeholder]
                else:
                    newdict.setdefault(path_part, placeholder)
                    placeholder = newdict
            if hasattr(self, "changed_data"):
                new_changed = {**newdict, **self.changed_data}
                self.changed_data = new_changed
            else:
                self.changed_data = newdict
        return success


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


class Records:
    def __new__(cls, *a, **kw):
        rec = super().__new__(cls)
        rec.cls = cls
        return rec

    def __init__(self, classic=None):
        self.log = logging.getLogger(f"{__name__}.Records")
        self._records = {}

    def __iter__(self):
        return RecordsIterator(self)

    def __getitem__(self, item):
        return self.recordWithId(self.ids()[item])

    def __contains__(self, x):
        return True if self.find(x) else False

    def ids(self):
        if not self._records:
            self.refresh_records()
        return [x for x in self._records.keys()]

    def names(self):
        if not self._records:
            self.refresh_records()
        return [x.name for x in self._records.values()]

    def recordWithId(self, x):
        if not self._records:
            self.refresh_records()
        if type(x) is str:
            x = int(x)
        return self._records.get(x)

    def recordWithName(self, x):
        stderr.write(
            "WARNING: recordWithName deprecated, use recordsWithName (it turns "
            "out names are not unique)."
        )
        names = self.recordsWithName(x)[0]
        if len(names) > 1:
            stderr.write(
                "There is more than one record with the name you are searching "
                "for! Only the first one is being used."
            )
        return names[0]

    def recordsWithName(self, name):
        if not self._records:
            self.refresh_records()
        found = []
        for record in self._records.values():
            if name == record.name:
                found.append(record)
        return found

    def recordsWithRegex(self, x):
        if not self._records:
            self.refresh_records()
        found = []
        for record in self._records.values():
            if re.search(x, record.name):
                found.append(record)
        return found

    def refresh_records(self):
        records = getattr(self.classic, self.refresh_method)()
        records = records[self.plural_string]
        self.refresh_records2(self.singular_class, records)

    def refresh_records2(
        self, singular_class=Record, records=None, id_txt="id", name_txt="name"
    ):
        self._records = {}
        if records is not None and not ("size" in records and records["size"] == 0):
            for d in records:
                c = singular_class(d[id_txt], d[name_txt])
                c.plural_class = self.cls
                self._records.setdefault(c.id, c)

    def find(self, x):
        if not self._records:
            self.refresh_records()
        if isinstance(x, int):
            # check for record id
            result = self._records.get(x)
        elif isinstance(x, str):
            try:
                result = self._records.get(int(x))
            except ValueError:
                result = self.recordsWithName(x)
        elif isinstance(x, dict):
            keys = ("id", "jamf_id", "name")
            try:
                key = [k for k in x.keys() if k in keys][0]
            except IndexError:
                result = None
            else:
                if key in ("id", "jamf_id"):
                    result = self._records.get(int(x[key]))
                elif key == "name":
                    result = self._names.get(key)
        elif isinstance(x, Record):
            result = x
        else:
            raise TypeError(f"can't look for {type(x)}")
        return result

    def random_value(self, mode="ascii_uppercase"):
        if mode == "ascii_uppercase":
            return "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
        elif mode == "uuid":
            return "".join(
                random.choices(string.hexdigits + string.digits, k=8)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=8)
            )
        elif mode == "uuid2":
            return "".join(
                random.choices(string.hexdigits + string.digits, k=8)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=4)
                + ["-"]
                + random.choices(string.hexdigits + string.digits, k=12)
            )
        elif mode == "semver":
            return "".join(
                random.choices(string.digits, k=2)
                + ["."]
                + random.choices(string.digits, k=2)
                + ["."]
                + random.choices(string.digits, k=2)
            )
        elif mode == "sn":
            return "".join(
                random.choices(string.ascii_uppercase, k=1)
                + random.choices(string.ascii_uppercase + string.digits, k=11)
            )

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def delete(self, ids, feedback=False):
        if hasattr(self.singular_class, "delete_method"):
            for recid in ids:
                record = self.recordWithId(recid)
                if feedback:
                    print(f"Deleting record: {record}")
                record.delete(refresh=False)
            self.refresh_records()

    def create_override(self, data, data_array=None, data_dict=None):
        result = getattr(self.classic, self.create_method)(data)
        newdata = convert.xml_to_dict(result)
        return newdata[self.singular_class.singular_string]["id"]

    def create(self, data=None):
        # Do not override this method! Use create_override instead!
        data_array = None
        data_dict = None
        if data is None:
            data = self.stub_record()
        elif isinstance(data, list):
            data_array = data
            data = self.stub_record()
        if isinstance(data, dict):
            data_dict = data
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        new_id = self.create_override(data, data_array, data_dict)
        self.refresh_records()
        new_rec = self.recordWithId(new_id)
        if data_array is not None:
            new_rec.set_data_name(data_array[0])
            # add more here..
            new_rec.save()
        return new_rec


class AdvancedComputerSearch(Record):
    plural_class = "AdvancedComputerSearches"
    singular_string = "advanced_computer_search"
    refresh_method = "get_advanced_computer_search"
    delete_method = "delete_advanced_computer_search"
    update_method = "update_advanced_computer_search"


class AdvancedComputerSearches(Records, metaclass=Singleton):
    singular_class = AdvancedComputerSearch
    plural_string = "advanced_computer_searches"
    refresh_method = "get_advanced_computer_searches"
    create_method = "create_advanced_computer_search"


class AdvancedMobileDeviceSearch(Record):
    plural_class = "AdvancedMobileDeviceSearches"
    singular_string = "advanced_mobile_device_search"
    refresh_method = "get_advanced_mobile_device_search"
    delete_method = "delete_advanced_mobile_device_search"
    update_method = "update_advanced_mobile_device_search"


class AdvancedMobileDeviceSearches(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html
    singular_class = AdvancedMobileDeviceSearch
    plural_string = "advanced_mobile_device_searches"
    refresh_method = "get_advanced_mobile_device_searches"
    create_method = "create_advanced_mobile_device_search"


class AdvancedUserSearch(Record):
    plural_class = "AdvancedUserSearches"
    singular_string = "advanced_user_search"
    refresh_method = "get_advanced_user_search"
    delete_method = "delete_advanced_user_search"
    update_method = "update_advanced_user_search"


class AdvancedUserSearches(Records, metaclass=Singleton):
    # http://localhost/users.html
    singular_class = AdvancedUserSearch
    plural_string = "advanced_user_searches"
    refresh_method = "get_advanced_user_searches"
    create_method = "create_advanced_user_search"


class Building(Record):
    plural_class = "Buildings"
    singular_string = "building"
    refresh_method = "get_building"
    delete_method = "delete_building"
    update_method = "update_building"


class Buildings(Records, metaclass=Singleton):
    # http://localhost/view/settings/network/buildings
    singular_class = Building
    plural_string = "buildings"
    refresh_method = "get_buildings"
    create_method = "create_building"


class BYOProfile(Record):
    plural_class = "BYOProfiles"
    singular_string = "byo_profile"
    refresh_method = "get_byo_profile"
    update_method = "update_byo_profile"


class BYOProfiles(Records, metaclass=Singleton):
    singular_class = BYOProfile
    plural_string = "byoprofiles"
    refresh_method = "get_byo_profiles"
    create_method = "create_byo_profile"


class Category(Record):
    plural_class = "Categories"
    singular_string = "category"
    refresh_method = "get_category"
    delete_method = "delete_category"
    update_method = "update_category"


class Categories(Records, metaclass=Singleton):
    # http://localhost/categories.html
    singular_class = Category
    plural_string = "categories"
    refresh_method = "get_categories"
    create_method = "create_category"


class Class(Record):
    plural_class = "Classes"
    singular_string = "class"
    refresh_method = "get_class"
    delete_method = "delete_class"
    update_method = "update_class"


class Classes(Records, metaclass=Singleton):
    # http://localhost/classes.html
    singular_class = Class
    plural_string = "classes"
    refresh_method = "get_classes"
    create_method = "create_class"


class Computer(Record):
    plural_class = "Computers"
    singular_string = "computer"
    refresh_method = "get_computer"
    delete_method = "delete_computer"
    update_method = "update_computer"
    name_path = "general/name"

    plurals = {"computer": {"hardware": {"storage": []}, "extension_attributes": []}}

    def apps_print_during(self):
        plural_cls = eval(self.cls.plural_class)
        if not hasattr(plural_cls, "app_list"):
            plural_cls.app_list = {}
        if not hasattr(plural_cls, "computers"):
            plural_cls.computers = {}
        plural_cls.computers[self.name] = True
        try:
            apps = self.get_path("software/applications/application/path")
        except JamfRecordNotFound:
            apps = None
        try:
            versions = self.get_path("software/applications/application/version")
        except JamfRecordNotFound:
            versions = None
        if apps:
            for ii, app in enumerate(apps):
                ver = versions[ii]
                if app not in plural_cls.app_list:
                    plural_cls.app_list[app] = {}
                if ver not in plural_cls.app_list[app]:
                    plural_cls.app_list[app][ver] = {}
                plural_cls.app_list[app][ver][self.name] = True


class Computers(Records, metaclass=Singleton):
    # http://localhost/computers.html?queryType=COMPUTERS&query=
    singular_class = Computer
    plural_string = "computers"
    refresh_method = "get_computers"
    create_method = "create_computer"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }

    sub_commands = {
        "apps": {"required_args": 0, "args_description": ""},
    }

    def apps_print_after(self):
        print("application,version,", end="")
        for computer in self.computers:
            print(computer, ",", end="")
        print("")
        for app, versions in self.app_list.items():
            for version, bla in versions.items():
                text = f'"{app}","{version}",'
                print(text, end="")
                for computer in self.computers:
                    if computer in bla:
                        print("X,", end="")
                    else:
                        print(",", end="")
                print("")


class ComputerExtensionAttribute(Record):
    plural_class = "ComputerExtensionAttributes"
    singular_string = "computer_extension_attribute"
    refresh_method = "get_computer_extension_attribute"
    delete_method = "delete_computer_extension_attribute"
    update_method = "update_computer_extension_attribute"

    def save_override(self, newdata):
        if "inventory_display" in newdata and newdata["inventory_display"] == "":
            del newdata["inventory_display"]
        return newdata


class ComputerExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/computerExtensionAttributes.html
    singular_class = ComputerExtensionAttribute
    plural_string = "computer_extension_attributes"
    refresh_method = "get_computer_extension_attributes"
    create_method = "create_computer_extension_attribute"


class ComputerGroup(Record):
    plural_class = "ComputerGroups"
    singular_string = "computer_group"
    refresh_method = "get_computer_group"
    delete_method = "delete_computer_group"
    update_method = "update_computer_group"


class ComputerGroups(Records, metaclass=Singleton):
    # http://localhost/smartComputerGroups.html
    # http://localhost/staticComputerGroups.html
    singular_class = ComputerGroup
    plural_string = "computer_groups"
    refresh_method = "get_computer_groups"
    create_method = "create_computer_group"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "is_smart": True,
                "name": self.random_value(),
            }
        }


class ComputerReport(Record):
    plural_class = "ComputerReports"
    singular_string = "computer_reports"
    refresh_method = "get_computer_report"


class ComputerReports(Records, metaclass=Singleton):
    singular_class = ComputerReport
    plural_string = "computer_reports"
    refresh_method = "get_computer_reports"


class Department(Record):
    plural_class = "Departments"
    singular_string = "department"
    refresh_method = "get_department"
    delete_method = "delete_department"
    update_method = "update_department"


class Departments(Records, metaclass=Singleton):
    # http://localhost/departments.html
    singular_class = Department
    plural_string = "departments"
    refresh_method = "get_departments"
    create_method = "create_department"


class DirectoryBinding(Record):
    plural_class = "DirectoryBindings"
    singular_string = "directory_binding"
    refresh_method = "get_directory_binding"
    delete_method = "delete_directory_binding"
    update_method = "update_directory_binding"


class DirectoryBindings(Records, metaclass=Singleton):
    singular_class = DirectoryBinding
    plural_string = "directory_bindings"
    refresh_method = "get_directory_bindings"
    create_method = "create_directory_binding"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "type": "Active Directory",
            }
        }


class DiskEncryptionConfiguration(Record):
    plural_class = "DiskEncryptionConfigurations"
    singular_string = "disk_encryption_configuration"
    refresh_method = "get_disk_encryption_configuration"
    delete_method = "delete_disk_encryption_configuration"
    update_method = "update_disk_encryption_configuration"


class DiskEncryptionConfigurations(Records, metaclass=Singleton):
    # http://localhost/diskEncryptions.html
    singular_class = DiskEncryptionConfiguration
    plural_string = "disk_encryption_configurations"
    refresh_method = "get_disk_encryption_configurations"
    create_method = "create_disk_encryption_configuration"


class DistributionPoint(Record):
    plural_class = "DistributionPoints"
    singular_string = "distribution_point"
    refresh_method = "get_distribution_point"
    delete_method = "delete_distribution_point"
    update_method = "update_distribution_point"


class DistributionPoints(Records, metaclass=Singleton):
    singular_class = DistributionPoint
    plural_string = "distribution_points"
    refresh_method = "get_distribution_points"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "read_only_password_sha256": "********************",
                "read_only_username": self.random_value(),
                "read_write_password_sha256": "********************",
                "read_write_username": self.random_value(),
                "share_name": self.random_value(),
            }
        }

    def create_override(self, data, data_array=None, data_dict=None):
        result = self.classic.create_distribution_point(data)
        newdata = convert.xml_to_dict(result)
        return newdata["file_share_distribution_point"]["id"]


class DockItem(Record):
    plural_class = "DockItems"
    singular_string = "dock_item"
    refresh_method = "get_dock_item"
    delete_method = "delete_dock_item"
    update_method = "update_dock_item"


class DockItems(Records, metaclass=Singleton):
    # http://localhost/dockItems.html
    singular_class = DockItem
    plural_string = "dock_items"
    refresh_method = "get_dock_items"
    create_method = "create_dock_item"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "path": "/",
                "type": "Folder",
            }
        }


class Ebook(Record):
    plural_class = "Ebooks"
    singular_string = "ebook"
    refresh_method = "get_ebook"
    delete_method = "delete_ebook"
    update_method = "update_ebook"
    name_path = "general/name"

    def save_override(self, newdata):
        if "url" in newdata["general"] and newdata["general"]["url"] == "":
            del newdata["general"]["url"]
        return newdata


class Ebooks(Records, metaclass=Singleton):
    singular_class = Ebook
    plural_string = "ebooks"
    refresh_method = "get_ebooks"
    create_method = "create_ebook"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }


class Ibeacon(Record):
    plural_class = "Ibeacons"
    singular_string = "ibeacon"
    refresh_method = "get_ibeacon_region"
    delete_method = "delete_ibeacon_region"
    update_method = "update_ibeacon_region"


class Ibeacons(Records, metaclass=Singleton):
    singular_class = Ibeacon
    plural_string = "ibeacons"
    refresh_method = "get_ibeacon_regions"
    create_method = "create_ibeacon_region"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "uuid": self.random_value("uuid"),
            }
        }


class JSONWebTokenConfiguration(Record):
    plural_class = "JSONWebTokenConfigurations"
    singular_string = "json_web_token_configuration"
    refresh_method = "get_json_web_token_configuration"
    delete_method = "delete_json_web_token_configuration"
    update_method = "update_json_web_token_configuration"

    def save_override(self, newdata):
        if "token_expiry" in newdata and newdata["token_expiry"] == 0:
            del newdata["token_expiry"]
        return newdata


class JSONWebTokenConfigurations(Records, metaclass=Singleton):
    singular_class = JSONWebTokenConfiguration
    plural_string = "json_web_token_configurations"
    refresh_method = "get_json_web_token_configurations"
    create_method = "create_json_web_token_configuration"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "encryption_key": self.random_value(),
                "token_expiry": 1,
            }
        }


class LDAPServer(Record):
    plural_class = "LDAPServers"
    singular_string = "ldap_server"
    refresh_method = "get_ldap_server"
    delete_method = "delete_ldap_server"
    update_method = "update_ldap_server"


class LDAPServers(Records, metaclass=Singleton):
    singular_class = LDAPServer
    plural_string = "ldap_servers"
    refresh_method = "get_ldap_servers"
    create_method = "create_ldap_server"


class MacApplication(Record):
    plural_class = "MacApplications"
    singular_string = "mac_application"
    refresh_method = "get_mac_application"
    delete_method = "delete_mac_application"
    update_method = "update_mac_application"
    name_path = "general/name"


class MacApplications(Records, metaclass=Singleton):
    singular_class = MacApplication
    plural_string = "mac_applications"
    refresh_method = "get_mac_applications"
    create_method = "create_mac_application"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "version": self.random_value("semver"),
                    "bundle_id": "edu.utah",
                    "url": "https://apps.apple.com/us/app/fake-data/id123456789",
                }
            }
        }


class ManagedPreferenceProfile(Record):
    plural_class = "ManagedPreferenceProfiles"
    singular_string = "managed_preference_profile"
    refresh_method = "get_managed_preference_profile"
    delete_method = "delete_managed_preference_profile"
    update_method = "update_managed_preference_profile"


class ManagedPreferenceProfiles(Records, metaclass=Singleton):
    singular_class = ManagedPreferenceProfile
    plural_string = "managed_preference_profiles"
    refresh_method = "get_managed_preference_profiles"


class MobileDevice(Record):
    plural_class = "MobileDevices"
    singular_string = "mobile_device"
    refresh_method = "get_mobile_device"
    delete_method = "delete_mobile_device"
    update_method = "update_mobile_device"
    name_path = "general/name"


class MobileDevices(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html?queryType=MOBILE_DEVICES&query=
    singular_class = MobileDevice
    plural_string = "mobile_devices"
    refresh_method = "get_mobile_devices"
    create_method = "create_mobile_device"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "udid": self.random_value("uuid"),
                    "serial_number": self.random_value("sn"),
                }
            }
        }


class MobileDeviceApplication(Record):
    plural_class = "MobileDeviceApplications"
    singular_string = "mobile_device_application"
    refresh_method = "get_mobile_device_application"
    delete_method = "delete_mobile_device_application"
    update_method = "update_mobile_device_application"
    name_path = "general/name"

    def save_override(self, newdata):
        # For some reason creating a mobile device application wont save the
        # os_type, which is required! So if it's missing, just add it.
        if "os_type" not in newdata["general"]:
            newdata["general"]["os_type"] = "iOS"
        return newdata


class MobileDeviceApplications(Records, metaclass=Singleton):
    singular_class = MobileDeviceApplication
    plural_string = "mobile_device_applications"
    refresh_method = "get_mobile_device_applications"
    create_method = "create_mobile_device_application"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "version": self.random_value("semver"),
                    "bundle_id": "utah.edu",
                    "os_type": "iOS",
                }
            }
        }


class MobileDeviceCommand(Record):
    plural_class = "MobileDeviceCommands"
    singular_string = "mobile_device_command"
    refresh_method = "get_mobile_device_command"


class MobileDeviceCommands(Records, metaclass=Singleton):
    singular_class = MobileDeviceCommand
    plural_string = "mobile_device_commands"
    refresh_method = "get_mobile_device_commands"
    create_method = "create_mobile_device_command"


class MobileDeviceConfigurationProfile(Record):
    plural_class = "MobileDeviceConfigurationProfiles"
    singular_string = "configuration_profile"
    refresh_method = "get_mobile_device_configuration_profile"
    delete_method = "delete_mobile_device_configuration_profile"
    update_method = "update_mobile_device_configuration_profile"
    name_path = "general/name"


class MobileDeviceConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceConfigurationProfile
    plural_string = "configuration_profiles"
    refresh_method = "get_mobile_device_configuration_profiles"
    create_method = "create_mobile_device_configuration_profile"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }


class MobileDeviceEnrollmentProfile(Record):
    plural_class = "MobileDeviceEnrollmentProfiles"
    singular_string = "mobile_device_enrollment_profile"
    refresh_method = "get_mobile_device_enrollment_profile"
    delete_method = "delete_mobile_device_enrollment_profile"
    update_method = "update_mobile_device_enrollment_profile"
    name_path = "general/name"
    plurals = {
        "mobile_device_enrollment_profile": {
            "general": {
                "description": "",
                "invitation": "",
                "name": "",
                "uuid": "",
            }
        }
    }


class MobileDeviceEnrollmentProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceEnrollmentProfile
    plural_string = "mobile_device_enrollment_profiles"
    refresh_method = "get_mobile_device_enrollment_profiles"
    create_method = "create_mobile_device_enrollment_profile"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }


class MobileDeviceExtensionAttribute(Record):
    plural_class = "MobileDeviceExtensionAttributes"
    singular_string = "mobile_device_extension_attribute"
    refresh_method = "get_mobile_device_extension_attribute"
    delete_method = "delete_mobile_device_extension_attribute"
    update_method = "update_mobile_device_extension_attribute"


class MobileDeviceExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/mobileDeviceExtensionAttributes.html
    singular_class = MobileDeviceExtensionAttribute
    plural_string = "mobile_device_extension_attributes"
    refresh_method = "get_mobile_device_extension_attributes"
    create_method = "create_mobile_device_extension_attribute"


class MobileDeviceInvitation(Record):
    plural_class = "MobileDeviceInvitations"
    singular_string = "mobile_device_invitation"
    refresh_method = "get_mobile_device_invitation"
    delete_method = "delete_mobile_device_invitation"


class MobileDeviceInvitations(Records, metaclass=Singleton):
    singular_class = MobileDeviceInvitation
    plural_string = "mobile_device_invitations"

    def refresh_records(self):
        records = self.classic.get_mobile_device_invitations()
        records = records[self.plural_string]
        super().refresh_records2(self.singular_class, records, name_txt="invitation")

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "id": 0,
                "invitation_type": "USER_INITIATED_EMAIL",
            }
        }

    def create_override(self, data, data_array=None, data_dict=None):
        result = self.classic.create_mobile_device_invitation(data, 0)
        newdata = convert.xml_to_dict(result)
        return newdata[self.singular_class.singular_string]["id"]


class MobileDeviceProvisioningProfile(Record):
    plural_class = "MobileDeviceProvisioningProfiles"
    singular_string = "mobile_device_provisioning_profile"
    refresh_method = "get_mobile_device_provisioning_profile"
    delete_method = "delete_mobile_device_provisioning_profile"
    update_method = "update_mobile_device_provisioning_profile"


class MobileDeviceProvisioningProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceProvisioningProfile
    plural_string = "mobile_device_provisioning_profiles"
    refresh_method = "get_mobile_device_provisioning_profiles"

    def stub_record(self):
        import base64

        uuid = self.random_value("uuid2")
        payload = "Your profile here"
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "general": {
                    "display_name": self.random_value(),
                    "uuid": uuid,
                    "profile": {
                        "name": self.random_value(),
                        "data": base64.b64encode(payload.encode("utf-8")),
                    },
                },
            }
        }

    def create_override(self, data, data_array=None, data_dict=None):
        result = self.classic.create_mobile_device_provisioning_profile(data, 0)
        newdata = convert.xml_to_dict(result)
        return newdata[self.singular_class.singular_string]["id"]


class NetworkSegment(Record):
    plural_class = "NetworkSegments"
    singular_string = "network_segment"
    refresh_method = "get_network_segment"
    delete_method = "delete_network_segment"
    update_method = "update_network_segment"


class NetworkSegments(Records, metaclass=Singleton):
    singular_class = NetworkSegment
    plural_string = "network_segments"
    refresh_method = "get_network_segments"
    create_method = "create_network_segment"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "ending_address": "10.0.0.255",
                "starting_address": "10.0.0.1",
            }
        }


class OSXConfigurationProfile(Record):
    plural_class = "OSXConfigurationProfiles"
    singular_string = "os_x_configuration_profile"
    # singular_string = "osx_configuration_profile" error: `jctl osxconfigurationprofiles -l`
    refresh_method = "get_osx_configuration_profile"
    delete_method = "delete_osx_configuration_profile"
    update_method = "update_osx_configuration_profile"


class OSXConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = OSXConfigurationProfile
    plural_string = "os_x_configuration_profiles"
    refresh_method = "get_osx_configuration_profiles"
    create_method = "create_osx_configuration_profile"


def parse_package_name(name):
    m = re.match(r"([^-]*)-(.*)\.([^\.]*)$", name)
    if m:
        return m[1], m[2], m[3]
    else:
        m = re.match(r"([^-]*)\.([^\.]*)$", name)
        if m:
            return m[1], "", m[2]
        else:
            return name, "", ""


class Package(Record):
    plural_class = "Packages"
    singular_string = "package"
    refresh_method = "get_package"
    delete_method = "delete_package"
    update_method = "update_package"

    def save_override(self, newdata):
        if "category" in newdata and newdata["category"] == "No category assigned":
            del newdata["category"]
        return newdata

    @property
    def metadata(self):
        if not hasattr(self, "meta"):
            basename, version, filetype = parse_package_name(self.name)
            self._metadata = {
                "basename": basename,
                "version": version,
                "filetype": filetype,
            }
            if not self._metadata["basename"] in self.plural.groups:
                self.plural.groups[self._metadata["basename"]] = []
            if self not in self.plural.groups[self._metadata["basename"]]:
                self.plural.groups[self._metadata["basename"]].append(self)
        return self._metadata

    def refresh_patchsoftwaretitles(self, related, patchsoftwaretitles_definitions):
        for jamf_record in jamf_records(PatchSoftwareTitles):
            pkgs = jamf_record.get_path("versions/version")
            if pkgs:
                for ii, pkg_hash in enumerate(pkgs):
                    if pkg_hash["package"] is None:
                        continue
                    if not str(jamf_record.id) in patchsoftwaretitles_definitions:
                        patchsoftwaretitles_definitions[str(jamf_record.id)] = {}
                    patchsoftwaretitles_definitions[str(jamf_record.id)][
                        pkg_hash["software_version"]
                    ] = pkg_hash["package"]
                    temp = related.setdefault(
                        int(pkg_hash["package"]["id"]), {"PatchSoftwareTitles": []}
                    )
                    temp.setdefault("PatchSoftwareTitles", []).append(jamf_record)

    def refresh_patchpolicies(self, related, patchsoftwaretitles_definitions):
        for jamf_record in jamf_records(PatchPolicies):
            patchsoftwaretitle_id = jamf_record.get_path(
                "software_title_configuration_id"
            )
            parent_pkg_version = jamf_record.get_path("general/target_version")
            if str(patchsoftwaretitle_id) in patchsoftwaretitles_definitions:
                patch_definitions = patchsoftwaretitles_definitions[
                    str(patchsoftwaretitle_id)
                ]
                if parent_pkg_version in patch_definitions:
                    pkg = patch_definitions[parent_pkg_version]
                    temp = related.setdefault(int(pkg["id"]), {"PatchPolicies": []})
                    temp.setdefault("PatchPolicies", []).append(jamf_record)

    def refresh_policies(self, related):
        for jamf_record in jamf_records(Policies):
            try:
                pkgs = jamf_record.get_path("package_configuration/packages/package/id")
            except JamfRecordInvalidPath:
                pkgs = []
            if pkgs:
                for pkg in pkgs:
                    temp = related.setdefault(int(pkg), {"Policies": []})
                    temp.setdefault("Policies", []).append(jamf_record)

    def refresh_groups(self, related):
        for jamf_record in jamf_records(ComputerGroups):
            try:
                criterions = jamf_record.get_path("criteria/criterion")
            except (JamfRecordNotFound, JamfRecordInvalidPath):
                criterions = []
            for criteria in criterions:
                if criteria["name"] == "Packages Installed By Casper":
                    pkg = criteria["value"]
                    if pkg and re.search(".pkg|.zip|.dmg", pkg[-4:]):
                        temp1 = self.plural().recordsWithName(pkg)
                        if len(temp1) > 1:
                            raise JamfAPISurprise(
                                f"Too many packages with the name {pkg}, this isn't supposed to happen."
                            )
                        elif len(temp1) == 1:
                            temp = related.setdefault(
                                temp1[0].id, {"ComputerGroups": []}
                            )
                            temp.setdefault("ComputerGroups", []).append(jamf_record)
                        else:
                            stderr.write(
                                f"Warning {jamf_record.name} specifies non-existant package: {pkg}\n"
                            )

    def refresh_related(self):
        related = {}
        patchsoftwaretitles_definitions = {}
        self.refresh_patchsoftwaretitles(related, patchsoftwaretitles_definitions)
        self.refresh_patchpolicies(related, patchsoftwaretitles_definitions)
        self.refresh_policies(related)
        self.refresh_groups(related)
        self.__class__._related = related

    @property
    def related(self):
        if not hasattr(self.__class__, "_related"):
            self.refresh_related()
        if self.id in self.__class__._related:
            return self.__class__._related[self.id]
        else:
            return {}

    def usage_print_during(self):
        related = self.related
        if "PatchSoftwareTitles" in related:
            print(self.name)
        else:
            print(f"{self.name} [no patch defined]")
        if "Policies" in related:
            print("  Policies")
            for x in related["Policies"]:
                print("    " + x)
        if "ComputerGroups" in related:
            print("  ComputerGroups")
            for x in related["ComputerGroups"]:
                print("    " + x)
        if "PatchPolicies" in related:
            print("  PatchPolicies")
            for x in related["PatchPolicies"]:
                print("    " + x)
        print()


class Packages(Records, metaclass=Singleton):
    singular_class = Package
    plural_string = "packages"
    refresh_method = "get_packages"
    create_method = "create_package"

    groups = {}
    sub_commands = {
        "usage": {"required_args": 0, "args_description": ""},
    }

    def stub_record(self):
        name = self.random_value()
        return {self.singular_class.singular_string: {"filename": name, "name": name}}


class PatchExternalSource(Record):
    plural_class = "PatchExternalSources"
    singular_string = "patch_external_source"
    refresh_method = "get_patch_external_source"
    delete_method = "delete_patch_external_source"
    update_method = "update_patch_external_source"


class PatchExternalSources(Records, metaclass=Singleton):
    singular_class = PatchExternalSource
    plural_string = "patch_external_sources"
    refresh_method = "get_patch_external_sources"

    def create_override(self, data, data_array=None, data_dict=None):
        result = self.classic.create_patch_external_source(data, 0)
        newdata = convert.xml_to_dict(result)
        return newdata[self.singular_class.singular_string]["id"]


class PatchInternalSource(Record):
    plural_class = "PatchInternalSources"
    singular_string = "patch_internal_source"

    def refresh_data(self):
        results = self.classic.get_patch_internal_source(self.id)
        self._data = results[self.singular_string]


class PatchInternalSources(Records, metaclass=Singleton):
    singular_class = PatchInternalSource
    plural_string = "patch_internal_sources"
    refresh_method = "get_patch_internal_sources"


class PatchPolicy(Record):
    delete_method = "delete_patch_policy"
    plural_class = "PatchPolicies"
    refresh_method = "get_patch_policy"
    singular_string = "patch_policy"
    update_method = "update_patch_policy"
    name_path = "general/name"

    def set_version_update_during(self, pkg_version):
        change_made = False
        cur_ver = self.data["general"]["target_version"]
        if cur_ver != pkg_version:
            print(f"Set version to {pkg_version}")
            self.data["general"]["target_version"] = pkg_version
            change_made = True
        else:
            print(f"Version is already {pkg_version}")
        return change_made

    def save_override(self, newdata):
        # If you don't delete the self_service_icon then it will error
        #   <Response [409]>: PUT - https://example.com:8443/JSSResource/patchpolicies/id/18:
        #   Conflict: Error: Problem with icon
        #   Couldn't save changed record: <Response [409]>
        # I don't think the self service icon can be modified from the cli, so just delete it
        if (
            "user_interaction" in newdata
            and "self_service_icon" in newdata["user_interaction"]
            and newdata["user_interaction"]["self_service_icon"] is None
        ):
            del newdata["user_interaction"]["self_service_icon"]
        if (
            "user_interaction" in newdata
            and "self_service_description" in newdata["user_interaction"]
            and newdata["user_interaction"]["self_service_description"] is None
        ):
            del newdata["user_interaction"]["self_service_description"]
        return newdata


class PatchPolicies(Records, metaclass=Singleton):
    singular_class = PatchPolicy
    plural_string = "patch_policies"
    refresh_method = "get_patch_policies"
    create_method = "create_patch_policy"

    sub_commands = {
        "set_version": {"required_args": 1, "args_description": ""},
    }

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                },
                "software_title_configuration_id": 1,
            }
        }

    def create_override(self, data, data_array=None, data_dict=None):
        if data_dict is not None:
            newid = data_dict["patch_policy"]["software_title_configuration_id"]
        result = getattr(self.classic, self.create_method)(data, newid)
        newdata = convert.xml_to_dict(result)
        return newdata[self.singular_class.singular_string]["id"]

    def refresh_records(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            super().refresh_records()


class PatchSoftwareTitle(Record):
    plural_class = "PatchSoftwareTitles"
    singular_string = "patch_software_title"
    refresh_method = "get_patch_software_title"
    delete_method = "delete_patch_software_title"
    update_method = "update_patch_software_title"
    plurals = {"patch_software_title": {"versions": {"version": []}}}

    def packages_print_during(self):
        print(self.name)
        versions = self.data["versions"]["version"]
        if not type(versions) is list:
            versions = [versions]
        for version in versions:
            if version["package"] is not None:
                print(f" {version['software_version']}: {version['package']['name']}")

    def patchpolicies_print_during(self):
        print(self.name)
        patchpolicies = jamf_records(PatchPolicies)
        for policy in patchpolicies:
            try:
                policy_id = policy.get_path("software_title_configuration_id")
            except JamfRecordNotFound:
                policy_id = None
            if str(policy_id) != str(self.id):
                continue
            print(f" {policy.data['general']['target_version']}: {str(policy)}")

    def set_all_packages_update_during(self):
        policy_regex = {
            "1Password 7": r"^1Password-%VERSION%\.pkg",
            "Apple GarageBand 10": r"^GarageBand-%VERSION%\.pkg",
            "Apple Keynote": r"^Keynote-%VERSION%\.pkg",
            "Apple Numbers": r"^Numbers-%VERSION%\.pkg",
            "Apple Pages": r"^Pages-%VERSION%\.pkg",
            "Apple Xcode": r"^Xcode-%VERSION%\.pkg",
            "Apple iMovie": r"^iMovie-%VERSION%\.pkg",
            "Arduino IDE": r"^Arduino-%VERSION%\.pkg",
            "Bare Bones BBEdit": r"BBEdit-%VERSION%\.pkg",
            "BusyCal 3": r"^BusyCal-%VERSION%\.pkg",
            "Microsoft Remote Desktop 10": r"^Microsoft Remote Desktop-%VERSION%\.pkg",
            "Microsoft Visual Studio Code": r"^Visual Studio Code-%VERSION%\.pkg",
            "Microsoft Teams": r"^Microsoft_Teams_%VERSION%\.pkg",
            "Mozilla Firefox": r"^Firefox-%VERSION%\.pkg",
            "R for Statistical Computing": r"^R-%VERSION%\.pkg",
            "RStudio Desktop": r"RStudio-%VERSION%\.dmg",
            "Sublime Text 3": r"Sublime Text-%VERSION%\.pkg",
            "VLC media player": r"VLC-%VERSION%\.pkg",
            "VMware Fusion 12": r"VMware Fusion-%VERSION%\.pkg",
            "VMware Horizon 8 Client": r"VMwareHorizonClient-%VERSION%.pkg",
            "Zoom Client for Meetings": r"Zoom-%VERSION%.pkg",
        }
        change_made = False
        packages = jamf_records(Packages)
        versions = self.data["versions"]["version"]
        if not type(versions) is list:
            versions = [versions]
        for pkg_version in versions:
            for package in packages:
                if not pkg_version["package"]:
                    if self.name in policy_regex:
                        regex = policy_regex[self.name]
                        regex = regex.replace(
                            "%VERSION%", pkg_version["software_version"]
                        )
                    else:
                        regex = (
                            rf".*{self.name}.*{pkg_version['software_version']}\.pkg"
                        )
                    regex = regex.replace("(", "\\(")
                    regex = regex.replace(")", "\\)")
                    if re.search(regex, package.name):
                        print(f"Matched {package.name}")
                        pkg_version["package"] = {"name": package.name}
                        change_made = True
        return change_made

    def set_package_for_version_update_during(self, package, target_version):
        change_made = False
        versions = self.data["versions"]["version"]
        if not type(versions) is list:
            versions = [versions]
        for pkg_version in versions:
            if pkg_version["software_version"] == target_version:
                print(f"{target_version}: {package}")
                pkg_version["package"] = {"name": package}
                change_made = True
        return change_made

    def versions_print_during(self):
        print(self.name)
        versions = self.data["versions"]["version"]
        if not type(versions) is list:
            versions = [versions]
        for version in versions:
            if version["package"] is not None:
                print(f" {version['software_version']}: {version['package']['name']}")
            else:
                print(f" {version['software_version']}: -")


class PatchSoftwareTitles(Records, metaclass=Singleton):
    singular_class = PatchSoftwareTitle
    plural_string = "patch_software_titles"
    refresh_method = "get_patch_software_titles"
    create_method = "create_patch_software_title"

    sub_commands = {
        "patchpolicies": {"required_args": 0, "args_description": ""},
        "packages": {"required_args": 0, "args_description": ""},
        "set_package_for_version": {
            "required_args": 2,
            "args_description": "package, version",
        },
        "set_all_packages": {"required_args": 0, "args_description": ""},
        "versions": {"required_args": 0, "args_description": ""},
    }

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name_id": "0C6",
                "source_id": "1",
            }
        }


class Peripheral(Record):
    plural_class = "Peripherals"
    singular_string = "peripheral"
    refresh_method = "get_peripheral"
    delete_method = "delete_peripheral"
    update_method = "update_peripheral"


class Peripherals(Records, metaclass=Singleton):
    singular_class = Peripheral
    plural_string = "peripherals"
    refresh_method = "get_peripherals"


class PeripheralType(Record):
    plural_class = "PeripheralTypes"
    singular_string = "peripheral_type"
    refresh_method = "get_peripheral_type"
    delete_method = "delete_peripheral_type"
    update_method = "update_peripheral_type"


class PeripheralTypes(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = PeripheralType
    plural_string = "peripheral_types"
    refresh_method = "get_peripheral_types"


class Policy(Record):
    plural_class = "Policies"
    singular_string = "policy"
    refresh_method = "get_policy"
    delete_method = "delete_policy"
    update_method = "update_policy"
    name_path = "general/name"

    def save_override(self, newdata):
        #   <Response [409]>: ...Retry options are only allowed when using the Once per computer frequency
        if (
            "frequency" in newdata["general"]
            and newdata["general"]["frequency"] != "Once per computer"
        ):
            if "retry_attempts" in newdata["general"]:
                newdata["general"]["retry_attempts"] = "-1"
            if "retry_event" in newdata["general"]:
                newdata["general"]["retry_event"] = "none"
            if "notify_on_each_failed_retry" in newdata["general"]:
                newdata["general"]["notify_on_each_failed_retry"] = "false"
        return newdata

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
        if self.data["general"]["trigger_other"]:
            _trigger.append(f"{self.data['general']['trigger_other']}")
        if self.data["general"]["trigger_enrollment_complete"] == "true":
            _trigger.append("Enrollment")
        if self.data["general"]["trigger_startup"] == "true":
            _trigger.append("Startup")
        if self.data["general"]["trigger_login"] == "true":
            _trigger.append("Login")
        if (
            hasattr(self.data["general"], "trigger_logout")
            and self.data["general"]["trigger_logout"] == "true"
        ):
            _trigger.append("Logout")
        if self.data["general"]["trigger_network_state_changed"] == "true":
            _trigger.append("Network")
        if self.data["general"]["trigger_checkin"] == "true":
            _trigger.append("Checkin")
        _text += ", ".join(_trigger)
        _text += "\t"

        # Scope
        _scope = []
        if self.data["scope"]["all_computers"] == "true":
            _scope.append("all_computers")
        if self.data["scope"]["buildings"]:
            for a in self.force_array(self.data["scope"]["buildings"], "building"):
                _scope.append(a["name"])
        if self.data["scope"]["computer_groups"]:
            for a in self.force_array(
                self.data["scope"]["computer_groups"], "computer_group"
            ):
                _scope.append(a["name"])
        if self.data["scope"]["computers"]:
            for a in self.force_array(self.data["scope"]["computers"], "computer"):
                _scope.append(a["name"])
        if self.data["scope"]["departments"]:
            for a in self.force_array(self.data["scope"]["departments"], "department"):
                _scope.append(a["name"])
        if self.data["scope"]["limit_to_users"]["user_groups"]:
            _scope.append("limit_to_users")
        _text += ", ".join(_scope)
        _text += "\t"

        # Packages
        if self.data["package_configuration"]["packages"]["size"] != "0":
            for a in self.force_array(
                self.data["package_configuration"]["packages"], "package"
            ):
                _text += a["name"]
        _text += "\t"

        # Printers
        if self.data["printers"]["size"] != "0":
            for a in self.force_array(self.data["printers"], "printer"):
                _text += a["name"]

            _text += self.data["printers"]["size"]
        _text += "\t"

        # Scripts
        if self.data["scripts"]["size"] != "0":
            for a in self.force_array(self.data["scripts"], "script"):
                _text += a["name"]
        _text += "\t"

        # Self Service
        _self_service = []
        if self.data["self_service"]["use_for_self_service"] != "false":
            _self_service.append("Yes")
        if len(_self_service) > 0:
            _text += ", ".join(_self_service)
        _text += "\t"

        ###############

        # Account Maintenance
        if self.data["account_maintenance"]["accounts"]["size"] != "0":
            for a in self.force_array(
                self.data["account_maintenance"]["accounts"], "account"
            ):
                _text += a["username"]
        _text += "\t"

        # Disk Encryption
        if self.data["disk_encryption"]["action"] != "none":
            _text += self.data["disk_encryption"]["action"]
        _text += "\t"

        # Dock Items
        if self.data["dock_items"]["size"] != "0":
            _text += self.data["dock_items"]["size"]
        _text += "\t"

        return _text

    def promote_update_during(self):
        if "package" not in self.data["package_configuration"]["packages"]:
            print(f"{self.name} has no package to update.")
            return True
        my_packages = self.data["package_configuration"]["packages"]["package"]

        all_packages = jamf_records(Packages)
        print(self.name)
        made_change = False
        for my_package in my_packages:
            similar_packages = []
            search_str = re.sub("-.*", "", my_package["name"])
            for package in all_packages:
                if package.name.find(search_str) == 0:
                    similar_packages.append(package.name)
            if len(similar_packages) > 1:
                index = 1
                for similar_package in reversed(similar_packages):
                    if similar_package == my_package["name"]:
                        print(f"  {index}. {similar_package} [Current]")
                    else:
                        print(f"  {index}. {similar_package}")
                    index += 1
                answer = "0"
                choices = list(map(str, range(1, index)))
                choices.append("")
                while answer not in choices:
                    answer = input("Choose a package [return skips]: ")
                if answer == "":
                    return True
                answer = len(similar_packages) - int(answer)
                my_package["name"] = similar_packages[answer]
                del my_package["id"]
                made_change = True
        if made_change:
            pprint(self.data["package_configuration"]["packages"])
            self.save()


class Policies(Records, metaclass=Singleton):
    singular_class = Policy
    plural_string = "policies"
    refresh_method = "get_policies"
    create_method = "create_policy"

    sub_commands = {
        "promote": {"required_args": 0, "args_description": ""},
        "spreadsheet": {"required_args": 0, "args_description": ""},
    }

    def spreadsheet_print_before(self):
        header = [
            "Name",
            "Category",
            "Frequency",
            "Trigger",
            "Scope",
            "Packages",
            "Printers",
            "Scripts",
            "Self Service",
            "Account Maintenance",
            "Disk Encryption",
            "Dock Items",
        ]
        print("\t".join(header))

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }


class Printer(Record):
    plural_class = "Printers"
    singular_string = "printer"
    refresh_method = "get_printer"
    delete_method = "delete_printer"
    update_method = "update_printer"


class Printers(Records, metaclass=Singleton):
    # http://localhost/printers.html
    singular_class = Printer
    plural_string = "printers"
    refresh_method = "get_printers"
    create_method = "create_printer"


class RemovableMACAddress(Record):
    plural_class = "RemovableMACAddresses"
    singular_string = "removable_mac_address"
    refresh_method = "get_removable_mac_address"
    delete_method = "delete_removable_mac_address"
    update_method = "update_removable_mac_address"


class RemovableMACAddresses(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = RemovableMACAddress
    plural_string = "removable_mac_addresses"
    refresh_method = "get_removable_mac_addresses"
    create_method = "create_removable_mac_address"


class Script(Record):
    plural_class = "Scripts"
    singular_string = "script"
    refresh_method = "get_script"
    delete_method = "delete_script"
    update_method = "update_script"

    def script_contents_print_during(self):
        try:
            printme = self.get_path("script_contents")
            print(printme[0])
        except JamfRecordNotFound:
            printme = None


class Scripts(Records, metaclass=Singleton):
    # http://localhost/view/settings/computer/scripts
    singular_class = Script
    plural_string = "scripts"
    refresh_method = "get_scripts"
    create_method = "create_script"

    sub_commands = {
        "script_contents": {"required_args": 0, "args_description": ""},
    }


class Site(Record):
    plural_class = "Sites"
    singular_string = "site"
    refresh_method = "get_site"
    delete_method = "delete_site"
    update_method = "update_site"


class Sites(Records, metaclass=Singleton):
    # http://localhost/sites.html
    singular_class = Site
    plural_string = "sites"
    refresh_method = "get_sites"
    create_method = "create_site"


class SoftwareUpdateServer(Record):
    plural_class = "SoftwareUpdateServers"
    singular_string = "update_software_server"
    refresh_method = "get_update_software_server"
    delete_method = "delete_update_software_server"
    update_method = "update_software_update_server"


class SoftwareUpdateServers(Records, metaclass=Singleton):
    singular_class = SoftwareUpdateServer
    plural_string = "software_update_servers"
    refresh_method = "get_software_update_servers"
    create_method = "create_software_update_server"


class User(Record):
    plural_class = "Users"
    singular_string = "user"
    refresh_method = "get_user"
    delete_method = "delete_user"
    update_method = "update_user"


class Users(Records, metaclass=Singleton):
    # http://localhost/users.html?query=
    singular_class = User
    plural_string = "users"
    refresh_method = "get_users"
    create_method = "create_user"


class UserExtensionAttribute(Record):
    plural_class = "UserExtensionAttributes"
    singular_string = "user_extension_attribute"
    refresh_method = "get_user_extension_attribute"
    delete_method = "delete_user_extension_attribute"
    update_method = "update_user_extension_attribute"


class UserExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/userExtensionAttributes.html
    singular_class = UserExtensionAttribute
    plural_string = "user_extension_attributes"
    refresh_method = "get_user_extension_attributes"
    create_method = "create_user_extension_attribute"


class UserGroup(Record):
    plural_class = "UserGroups"
    singular_string = "user_group"
    refresh_method = "get_user_group"
    delete_method = "delete_user_group"
    update_method = "update_user_group"


class UserGroups(Records, metaclass=Singleton):
    singular_class = UserGroup
    plural_string = "user_groups"
    refresh_method = "get_user_groups"
    create_method = "create_user_group"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "is_smart": "false",
            }
        }

    def create_override(self, data, data_array=None, data_dict=None):
        result = getattr(self.classic, self.create_method)(data)
        if self.debug:
            print(result)
        newdata = convert.xml_to_dict(result)
        if "smart_user_group" in newdata:
            return newdata["smart_user_group"]["id"]
        elif "static_user_group" in newdata:
            return newdata["static_user_group"]["id"]


class VPPAccount(Record):
    plural_class = "VPPAccounts"
    singular_string = "vpp_account"
    refresh_method = "get_vpp_account"
    delete_method = "delete_vpp_account"
    update_method = "update_vpp_account"


class VPPAccounts(Records, metaclass=Singleton):
    singular_class = VPPAccount
    plural_string = "vpp_accounts"
    refresh_method = "get_vpp_accounts"
    create_method = "create_vpp_account"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "service_token": "eyJvcmdOYWadveaz40d2FyZSIsImV4cERhdGUiOiIyMDE3LTA5LTEzVDA5OjQ5OjA5LTA3MDAiLCJ0b2tlbiI6Ik5yVUtPK1RXeityUXQyWFpIeENtd0xxby8ydUFmSFU1NW40V1FTZU8wR1E5eFh4UUZTckVJQjlzbGdYei95WkpaeVZ3SklJbW0rWEhJdGtKM1BEZGRRPT0ifQ==",
            }
        }


class VPPAssignment(Record):
    plural_class = "VPPAssignments"
    singular_string = "vpp_assignment"
    refresh_method = "get_vpp_assignment"
    delete_method = "delete_vpp_assignment"
    update_method = "update_vpp_assignment"


class VPPAssignments(Records, metaclass=Singleton):
    singular_class = VPPAssignment
    plural_string = "vpp_assignments"
    refresh_method = "get_vpp_assignments"
    create_method = "create_vpp_assignment"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "vpp_admin_account_id": "",
                }
            }
        }


class VPPInvitation(Record):
    plural_class = "VPPInvitations"
    singular_string = "vpp_invitation"
    refresh_method = "get_vpp_invitation"
    delete_method = "delete_vpp_invitation"
    update_method = "update_vpp_invitation"


class VPPInvitations(Records, metaclass=Singleton):
    singular_class = VPPInvitation
    plural_string = "vpp_invitations"
    refresh_method = "get_vpp_invitations"
    create_method = "create_vpp_invitation"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "vpp_account": {
                        "id": "",
                    },
                }
            }
        }


class WebHook(Record):
    plural_class = "WebHooks"
    singular_string = "webhook"
    refresh_method = "get_webhook"
    delete_method = "delete_webhook"
    update_method = "update_webhook"


class WebHooks(Records, metaclass=Singleton):
    singular_class = WebHook
    plural_string = "webhooks"
    refresh_method = "get_webhooks"
    create_method = "create_webhook"

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "event": "ComputerAdded",
                "name": self.random_value(),
                "url": "http://example.com",
            }
        }


def jamf_records(cls, name="", exclude=()):
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


def categories(name="", exclude=()):
    """
    Get Jamf Categories

    :param name  <str>:      name in record['name']
    :param exclude  <iter>:  record['name'] not in exclude

    :returns:  list of dicts: [{'id': jamf_id, 'name': name}, ...]
    """
    return jamf_records(Categories, name, exclude)


def set_classic(classic):
    Record.classic = classic
    Records.classic = classic


def set_debug(debug):
    Record.debug = debug
    Records.debug = debug
