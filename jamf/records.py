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
__version__ = "0.4.6"


from pprint import pprint
from sys import stderr
import copy
import json
import logging
import os.path
import random
import re
import string

from jps_api_wrapper.request_builder import RequestConflict

from . import convert

from jps_api_wrapper.classic import Classic
from jps_api_wrapper.pro import Pro

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
    "MobileDeviceCommands",
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
    "JamfError",
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


class Singleton(type):
    """allows us to share a single object"""

    _instances = {}

    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class Record:
    def __new__(cls, jamf_id, jamf_name):
        """
        returns existing record if one has been instantiated
        """
        if not hasattr(cls, "_instances"):
            cls._instances = {}
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

    def delete(self):
        pass

    def save(self):
        pass

    @property
    def data(self):
        if not self._data:
            self.refresh_data()
        return self._data

    def get_path_worker(self, path, placeholder, index=0):
        current = path[index]
        if type(placeholder) is dict:
            if current in placeholder:
                if index + 1 >= len(path):
                    return placeholder[current]
                placeholder = self.get_path_worker(
                    path, placeholder[current], index + 1
                )
            else:
                raise NotFound
        elif type(placeholder) is list:
            # I'm not sure this is the best way to handle arrays...
            result = []
            for item in placeholder:
                if current in item:
                    if index + 1 < len(path):
                        result.append(
                            self.get_path_worker(path, item[current], index + 1)
                        )
                    else:
                        result.append(item[current])
            placeholder = result
        return placeholder

    def get_path(self, path):
        if not self._data:
            self.refresh_data()
        result = self.get_path_worker(path.split("/"), self._data)
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
        temp1 = path.split("/")
        endpoint = temp1.pop()
        temp2 = "/".join(temp1)
        if len(temp2) > 0:
            placeholder = self.get_path(temp2)
        else:
            if not self._data:
                self.refresh_data()
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
            print("Error: empty data:")
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
        stderr(
            "WARNING: recordWithName deprecated, use recordsWithName (it turns "
            "out names are not unique)."
        )
        names = self.recordsWithName(self, x)[0]
        if len(names) > 1:
            stderr(
                "There is more than one record with the name you are searching "
                "for! Only the first one is being used."
            )
        return names[0]

    def recordsWithName(self, x):
        if not self._records:
            self.refresh_records()
        found = []
        for record in self._records.values():
            if x == record.name:
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

    def refresh_records(
        self, singular_class=Record, records=None, id_txt="id", name_txt="name"
    ):
        self._records = {}
        if records is not None and not ("size" in records and records["size"] == 0):
            for d in records:
                c = singular_class(d[id_txt], d[name_txt])
                c.plural_class = self.cls
                self._records.setdefault(c.id, c)

    def createNewRecord(self, args):
        return self.singular_class(0, args)

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
                result = self._names.get(x)
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
        elif mode == "semver":
            return "".join(
                random.choices(string.digits, k=2)
                + ["."]
                + random.choices(string.digits, k=2)
                + ["."]
                + random.choices(string.digits, k=2)
            )


class AdvancedComputerSearch(Record):
    plural_class = "AdvancedComputerSearches"
    singular_string = "advanced_computer_search"

    def refresh_data(self):
        results = self.classic.get_advanced_computer_search(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_advanced_computer_search(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_advanced_computer_search(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class AdvancedComputerSearches(Records, metaclass=Singleton):
    singular_class = AdvancedComputerSearch
    plural_string = "advanced_computer_searches"

    def refresh_records(self):
        records = self.classic.get_advanced_computer_searches()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "criteria": [],
                "display_fields": [],
                "id": 2,
                "mobile_devices": [],
                "name": self.random_value(),
                "sort_1": "",
                "sort_2": "",
                "sort_3": "",
                "view_as": "Standard Web Page",
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_advanced_computer_search(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class AdvancedMobileDeviceSearch(Record):
    plural_class = "AdvancedMobileDeviceSearches"
    singular_string = "advanced_mobile_device_search"

    def refresh_data(self):
        results = self.classic.get_advanced_mobile_device_search(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_advanced_mobile_device_search(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_advanced_mobile_device_search(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class AdvancedMobileDeviceSearches(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html
    singular_class = AdvancedMobileDeviceSearch
    plural_string = "advanced_mobile_device_searches"

    def refresh_records(self):
        records = self.classic.get_advanced_mobile_device_searches()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "criteria": [],
                "display_fields": [],
                "id": 2,
                "mobile_devices": [],
                "name": self.random_value(),
                "site": {"id": -1, "name": "None"},
                "sort_1": "",
                "sort_2": "",
                "sort_3": "",
                "view_as": "Standard Web Page",
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_advanced_mobile_device_search(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class AdvancedUserSearch(Record):
    plural_class = "AdvancedUserSearches"
    singular_string = "advanced_user_search"

    def refresh_data(self):
        results = self.classic.get_advanced_user_search(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_advanced_user_search(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_advanced_user_search(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class AdvancedUserSearches(Records, metaclass=Singleton):
    # http://localhost/users.html
    singular_class = AdvancedUserSearch
    plural_string = "advanced_user_searches"

    def refresh_records(self):
        records = self.classic.get_advanced_user_searches()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "criteria": [],
                "display_fields": [{"name": "Email Address"}, {"name": "Full Name"}],
                "id": 3,
                "name": self.random_value(),
                "site": {"id": -1, "name": "None"},
                "users": [],
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_advanced_user_search(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Building(Record):
    plural_class = "Buildings"
    singular_string = "building"

    def refresh_data(self):
        results = self.classic.get_building(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_building(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_building(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Buildings(Records, metaclass=Singleton):
    # http://localhost/view/settings/network/buildings
    singular_class = Building
    plural_string = "buildings"

    def refresh_records(self):
        records = self.classic.get_buildings()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {"id": 1, "name": self.random_value()}
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_building(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class BYOProfile(Record):
    plural_class = "BYOProfiles"
    singular_string = "byo_profile"

    def refresh_data(self):
        results = self.classic.get_byo_profile(self.id)
        self._data = results[self.singular_string]

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_byo_profile(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class BYOProfiles(Records, metaclass=Singleton):
    singular_class = BYOProfile
    plural_string = "byoprofiles"

    def refresh_records(self):
        records = self.classic.get_byo_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class Category(Record):
    plural_class = "Categories"
    singular_string = "category"

    def refresh_data(self):
        results = self.classic.get_category(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_category(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_category(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Categories(Records, metaclass=Singleton):
    # http://localhost/categories.html
    singular_class = Category
    plural_string = "categories"

    def refresh_records(self):
        records = self.classic.get_categories()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_category(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Class(Record):
    plural_class = "Classes"
    singular_string = "class"

    def refresh_data(self):
        results = self.classic.get_class(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_class(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_class(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Classes(Records, metaclass=Singleton):
    # http://localhost/classes.html
    singular_class = Class
    plural_string = "classes"

    def refresh_records(self):
        records = self.classic.get_classes()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "description": "",
                "id": 1,
                "mobile_device_group": {},
                "mobile_device_group_ids": [],
                "mobile_devices": [],
                "name": self.random_value(),
                "site": {"id": -1, "name": "None"},
                "source": "N/A",
                "student_group_ids": [],
                "student_ids": [],
                "students": [],
                "teacher_group_ids": [],
                "teacher_ids": [],
                "teachers": [],
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_class(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Computer(Record):
    plural_class = "Computers"
    singular_string = "computer"

    def refresh_data(self):
        results = self.classic.get_computer(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_computer(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_computer(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]

    def apps_print_during(self):
        plural_cls = eval(self.cls.plural_class)
        if not hasattr(plural_cls, "app_list"):
            plural_cls.app_list = {}
        if not hasattr(plural_cls, "computers"):
            plural_cls.computers = {}
        plural_cls.computers[self.name] = True
        try:
            apps = self.get_path("software/applications/application/path")
        except NotFound:
            apps = None
        try:
            versions = self.get_path("software/applications/application/version")
        except NotFound:
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

    def refresh_records(self):
        records = self.classic.get_computers()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_computer(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class ComputerExtensionAttribute(Record):
    plural_class = "ComputerExtensionAttributes"
    singular_string = "computer_extension_attribute"

    def refresh_data(self):
        results = self.classic.get_computer_extension_attribute(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_computer_extension_attribute(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_computer_extension_attribute(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class ComputerExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/computerExtensionAttributes.html
    singular_class = ComputerExtensionAttribute
    plural_string = "computer_extension_attributes"

    def refresh_records(self):
        records = self.classic.get_computer_extension_attributes()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_computer_extension_attribute(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class ComputerGroup(Record):
    plural_class = "ComputerGroups"
    singular_string = "computer_group"

    def refresh_data(self):
        results = self.classic.get_computer_group(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_computer_group(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_computer_group(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class ComputerGroups(Records, metaclass=Singleton):
    # http://localhost/smartComputerGroups.html
    # http://localhost/staticComputerGroups.html
    singular_class = ComputerGroup
    plural_string = "computer_groups"

    def refresh_records(self):
        records = self.classic.get_computer_groups()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "computers": [],
                "criteria": [],
                "is_smart": True,
                "name": self.random_value(),
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_computer_group(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class ComputerReport(Record):
    plural_class = "ComputerReports"
    singular_string = "computer_reports"

    def refresh_data(self):
        results = self.classic.get_computer_report(self.id)
        self._data = results[self.singular_string]

class ComputerReports(Records, metaclass=Singleton):
    singular_class = ComputerReport
    plural_string = "computer_reports"

    def refresh_records(self):
        records = self.classic.get_computer_reports()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class Department(Record):
    plural_class = "Departments"
    singular_string = "department"

    def refresh_data(self):
        results = self.classic.get_department(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_department(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_department(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Departments(Records, metaclass=Singleton):
    # http://localhost/departments.html
    singular_class = Department
    plural_string = "departments"

    def refresh_records(self):
        records = self.classic.get_departments()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_department(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class DirectoryBinding(Record):
    plural_class = "DirectoryBindings"
    singular_string = "directory_binding"

    def refresh_data(self):
        results = self.classic.get_directory_binding(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_directory_binding(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_directory_binding(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class DirectoryBindings(Records, metaclass=Singleton):
    singular_class = DirectoryBinding
    plural_string = "directory_bindings"

    def refresh_records(self):
        records = self.classic.get_directory_bindings()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "active_directory": {
                    "admin_groups": "",
                    "cache_last_user": False,
                    "default_shell": "/bin/bash",
                    "forest": "",
                    "gid": "",
                    "local_home": True,
                    "mount_style": "smb",
                    "multiple_domains": True,
                    "preferred_domain": "",
                    "require_confirmation": False,
                    "uid": "",
                    "use_unc_path": True,
                    "user_gid": "",
                },
                "computer_ou": "adsf",
                "domain": "asdf",
                "name": self.random_value(),
                "password_sha256": "********************",
                "priority": 1,
                "type": "Active Directory",
                "username": "asdf",
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_directory_binding(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class DiskEncryptionConfiguration(Record):
    plural_class = "DiskEncryptionConfigurations"
    singular_string = "disk_encryption_configuration"

    def refresh_data(self):
        results = self.classic.get_disk_encryption_configuration(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_disk_encryption_configuration(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_disk_encryption_configuration(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class DiskEncryptionConfigurations(Records, metaclass=Singleton):
    # http://localhost/diskEncryptions.html
    singular_class = DiskEncryptionConfiguration
    plural_string = "disk_encryption_configurations"

    def refresh_records(self):
        records = self.classic.get_disk_encryption_configurations()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_disk_encryption_configuration(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class DistributionPoint(Record):
    plural_class = "DistributionPoints"
    singular_string = "distribution_point"

    def refresh_data(self):
        results = self.classic.get_distribution_point(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_distribution_point(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_distribution_point(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class DistributionPoints(Records, metaclass=Singleton):
    singular_class = DistributionPoint
    plural_string = "distribution_points"

    def refresh_records(self):
        records = self.classic.get_distribution_points()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "connection_type": "SMB",
                "enable_load_balancing": False,
                "ipAddress": self.random_value(),
                "ip_address": self.random_value(),
                "is_master": False,
                "local_path": "",
                "name": self.random_value(),
                "no_authentication_required": True,
                "port": 80,
                "protocol": "http",
                "read_only_password_sha256": "********************",
                "read_only_username": self.random_value(),
                "read_write_password_sha256": "********************",
                "read_write_username": self.random_value(),
                "share_name": self.random_value(),
                "share_port": 139,
                "ssh_password_sha256": "",
                "ssh_username": "",
                "username_password_required": False,
                "workgroup_or_domain": "",
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_distribution_point(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata["file_share_distribution_point"]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class DockItem(Record):
    plural_class = "DockItems"
    singular_string = "dock_item"

    def refresh_data(self):
        results = self.classic.get_dock_item(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_dock_item(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_dock_item(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class DockItems(Records, metaclass=Singleton):
    # http://localhost/dockItems.html
    singular_class = DockItem
    plural_string = "dock_items"

    def refresh_records(self):
        records = self.classic.get_dock_items()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "path": "/",
                "type": "Folder",
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_dock_item(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Ebook(Record):
    plural_class = "Ebooks"
    singular_string = "ebook"

    def refresh_data(self):
        results = self.classic.get_ebook(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_ebook(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_ebook(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Ebooks(Records, metaclass=Singleton):
    singular_class = Ebook
    plural_string = "ebooks"

    def refresh_records(self):
        records = self.classic.get_ebooks()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {"name": self.random_value()}
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_ebook(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Ibeacon(Record):
    plural_class = "Ibeacons"
    singular_string = "ibeacon"

    def refresh_data(self):
        results = self.classic.get_ibeacon_region(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_ibeacon_region(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_ibeacon_region(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Ibeacons(Records, metaclass=Singleton):
    singular_class = Ibeacon
    plural_string = "ibeacons"

    def refresh_records(self):
        records = self.classic.get_ibeacon_regions()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "uuid": self.random_value("uuid"),
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_ibeacon_region(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class JSONWebTokenConfiguration(Record):
    plural_class = "JSONWebTokenConfigurations"
    singular_string = "json_web_token_configuration"

    def refresh_data(self):
        results = self.classic.get_json_web_token_configuration(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_json_web_token_configuration(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_json_web_token_configuration(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class JSONWebTokenConfigurations(Records, metaclass=Singleton):
    singular_class = JSONWebTokenConfiguration
    plural_string = "json_web_token_configurations"

    def refresh_records(self):
        records = self.classic.get_json_web_token_configurations()

        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "name": self.random_value(),
                "encryption_key": self.random_value(),
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_json_web_token_configuration(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class LDAPServer(Record):
    plural_class = "LDAPServers"
    singular_string = "ldap_server"

    def refresh_data(self):
        results = self.classic.get_ldap_server(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_ldap_server(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_ldap_server(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class LDAPServers(Records, metaclass=Singleton):
    singular_class = LDAPServer
    plural_string = "ldap_servers"

    def refresh_records(self):
        records = self.classic.get_ldap_servers()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class MacApplication(Record):
    plural_class = "MacApplications"
    singular_string = "mac_application"

    def refresh_data(self):
        results = self.classic.get_mac_application(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mac_application(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mac_application(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class MacApplications(Records, metaclass=Singleton):
    singular_class = MacApplication
    plural_string = "mac_applications"

    def refresh_records(self):
        records = self.classic.get_mac_applications()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

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

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mac_application(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class ManagedPreferenceProfile(Record):
    plural_class = "ManagedPreferenceProfiles"
    singular_string = "managed_preference_profile"

    def refresh_data(self):
        results = self.classic.get_managed_preference_profile(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_managed_preference_profile(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_managed_preference_profile(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class ManagedPreferenceProfiles(Records, metaclass=Singleton):
    singular_class = ManagedPreferenceProfile
    plural_string = "managed_preference_profiles"

    def refresh_records(self):
        records = self.classic.get_managed_preference_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class MobileDevice(Record):
    plural_class = "MobileDevices"
    singular_string = "mobile_device"

    def refresh_data(self):
        results = self.classic.get_mobile_device(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class MobileDevices(Records, metaclass=Singleton):
    # http://localhost/mobileDevices.html?queryType=MOBILE_DEVICES&query=
    singular_class = MobileDevice
    plural_string = "mobile_devices"

    def refresh_records(self):
        records = self.classic.get_mobile_devices()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceApplication(Record):
    plural_class = "MobileDeviceApplications"
    singular_string = "mobile_device_application"

    def refresh_data(self):
        results = self.classic.get_mobile_device_application(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_application(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device_application(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class MobileDeviceApplications(Records, metaclass=Singleton):
    singular_class = MobileDeviceApplication
    plural_string = "mobile_device_applications"

    def refresh_records(self):
        records = self.classic.get_mobile_device_applications()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "general": {
                    "name": self.random_value(),
                    "version": self.random_value("semver"),
                    "bundle_id": "edu.utah",
                }
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_application(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceCommand(Record):
    plural_class = "MobileDeviceCommands"
    singular_string = "mobile_device_command"

    def refresh_data(self):
        results = self.classic.get_mobile_device_command(self.id)
        self._data = results[self.singular_string]

class MobileDeviceCommands(Records, metaclass=Singleton):
    singular_class = MobileDeviceCommand
    plural_string = "mobile_device_commands"

    def refresh_records(self):
        records = self.classic.get_mobile_device_commands()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_command(data)
        newdata = convert.xml_to_dict(result)
        pprint(newdata)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceConfigurationProfile(Record):
    plural_class = "MobileDeviceConfigurationProfiles"
    singular_string = "mobile_device_configuration_profile"

    def refresh_data(self):
        results = self.classic.get_mobile_device_configuration_profile(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_configuration_profile(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device_configuration_profile(
            newdata, id=self.id
        )
        self.refresh_data()
        self.name = self._data["name"]


class MobileDeviceConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceConfigurationProfile
    plural_string = "configuration_profiles"

    def refresh_records(self):
        records = self.classic.get_mobile_device_configuration_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_configuration_profile(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceEnrollmentProfile(Record):
    plural_class = "MobileDeviceEnrollmentProfiles"
    singular_string = "mobile_device_enrollment_profile"

    def refresh_data(self):
        results = self.classic.get_mobile_device_enrollment_profile(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_enrollment_profile(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device_enrollment_profile(
            newdata, id=self.id
        )
        self.refresh_data()
        self.name = self._data["name"]


class MobileDeviceEnrollmentProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceEnrollmentProfile
    plural_string = "mobile_device_enrollment_profiles"

    def refresh_records(self):
        records = self.classic.get_mobile_device_enrollment_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_enrollment_profile(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceExtensionAttribute(Record):
    plural_class = "MobileDeviceExtensionAttributes"
    singular_string = "mobile_device_extension_attribute"

    def refresh_data(self):
        results = self.classic.get_mobile_device_extension_attribute(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_extension_attribute(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device_extension_attribute(
            newdata, id=self.id
        )
        self.refresh_data()
        self.name = self._data["name"]


class MobileDeviceExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/mobileDeviceExtensionAttributes.html
    singular_class = MobileDeviceExtensionAttribute
    plural_string = "mobile_device_extension_attributes"

    def refresh_records(self):
        records = self.classic.get_mobile_device_extension_attributes()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_extension_attribute(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceInvitation(Record):
    plural_class = "MobileDeviceInvitations"
    singular_string = "mobile_device_invitation"

    def refresh_data(self):
        results = self.classic.get_mobile_device_invitation(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_invitation(self.id)
        self.plural().refresh_records()


class MobileDeviceInvitations(Records, metaclass=Singleton):
    singular_class = MobileDeviceInvitation
    plural_string = "mobile_device_invitations"

    def refresh_records(self):
        records = self.classic.get_mobile_device_invitations()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_invitation(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class MobileDeviceProvisioningProfile(Record):
    plural_class = "MobileDeviceProvisioningProfiles"
    singular_string = "mobile_device_provisioning_profile"

    def refresh_data(self):
        results = self.classic.get_mobile_device_provisioning_profile(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_mobile_device_provisioning_profile(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_mobile_device_provisioning_profile(
            newdata, id=self.id
        )
        self.refresh_data()
        self.name = self._data["name"]


class MobileDeviceProvisioningProfiles(Records, metaclass=Singleton):
    singular_class = MobileDeviceProvisioningProfile
    plural_string = "mobile_device_provisioning_profiles"

    def refresh_records(self):
        records = self.classic.get_mobile_device_provisioning_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_mobile_device_provisioning_profile(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class NetworkSegment(Record):
    plural_class = "NetworkSegments"
    singular_string = "network_segment"

    def refresh_data(self):
        results = self.classic.get_network_segment(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_network_segment(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_network_segment(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class NetworkSegments(Records, metaclass=Singleton):
    singular_class = NetworkSegment
    plural_string = "network_segments"

    def refresh_records(self):
        records = self.classic.get_network_segments()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_network_segment(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class OSXConfigurationProfile(Record):
    plural_class = "OSXConfigurationProfiles"
    singular_string = "osx_configuration_profile"

    def refresh_data(self):
        results = self.classic.get_osx_configuration_profile(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_osx_configuration_profile(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_osx_configuration_profile(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class OSXConfigurationProfiles(Records, metaclass=Singleton):
    singular_class = OSXConfigurationProfile
    plural_string = "os_x_configuration_profiles"

    def refresh_records(self):
        records = self.classic.get_osx_configuration_profiles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_osx_configuration_profile(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


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

    def refresh_data(self):
        results = self.classic.get_package(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_package(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_package(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]

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

    def refresh_related(self):
        related = {}
        patchsoftwaretitles = jamf_records(PatchSoftwareTitles)
        patchsoftwaretitles_definitions = {}
        for title in patchsoftwaretitles:
            pkgs = title.get_path("versions/version/package/name")
            versions = title.get_path("versions/version/software_version")
            if pkgs:
                for ii, pkg in enumerate(pkgs):
                    if pkg is None:
                        continue
                    if not str(title.id) in patchsoftwaretitles_definitions:
                        patchsoftwaretitles_definitions[str(title.id)] = {}
                    patchsoftwaretitles_definitions[str(title.id)][versions[ii]] = pkg
                    if pkg not in related:
                        related[pkg] = {"PatchSoftwareTitles": []}
                    if "PatchSoftwareTitles" not in related[pkg]:
                        related[pkg]["PatchSoftwareTitles"] = []
                    temp = title.name + " - " + versions[ii]
                    related[pkg]["PatchSoftwareTitles"].append(temp)
        patchpolicies = jamf_records(PatchPolicies)
        for policy in patchpolicies:
            patchsoftwaretitle_id = policy.get_path("software_title_configuration_id")
            parent_pkg_version = policy.get_path("general/target_version")
            if str(patchsoftwaretitle_id) in patchsoftwaretitles_definitions:
                patch_definitions = patchsoftwaretitles_definitions[
                    str(patchsoftwaretitle_id)
                ]
                if parent_pkg_version in patch_definitions:
                    pkg = patch_definitions[parent_pkg_version]
                    if pkg not in related:
                        related[pkg] = {"PatchPolicies": []}
                    if "PatchPolicies" not in related[pkg]:
                        related[pkg]["PatchPolicies"] = []
                    related[pkg]["PatchPolicies"].append(policy.name)
        policies = jamf_records(Policies)
        for policy in policies:
            try:
                pkgs = policy.get_path("package_configuration/packages/package/name")
            except NotFound:
                pkgs = []
            if pkgs:
                for pkg in pkgs:
                    if pkg not in related:
                        related[pkg] = {"Policies": []}
                    if "Policies" not in related[pkg]:
                        related[pkg]["Policies"] = []
                    related[pkg]["Policies"].append(policy.name)
        groups = jamf_records(ComputerGroups)
        for group in groups:
            try:
                criterions = group.get_path("criteria/criterion/value")
            except NotFound:
                criterions = None
            if criterions:
                for pkg in criterions:
                    if pkg and re.search(".pkg|.zip|.dmg", pkg[-4:]):
                        if pkg not in related:
                            related[pkg] = {"ComputerGroups": []}
                        if "ComputerGroups" not in related[pkg]:
                            related[pkg]["ComputerGroups"] = []
                        related[pkg]["ComputerGroups"].append(group.name)
        self.__class__._related = related

    @property
    def related(self):
        if not hasattr(self.__class__, "_related"):
            self.refresh_related()
        if self.name in self.__class__._related:
            return self.__class__._related[self.name]
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

    groups = {}
    sub_commands = {
        "usage": {"required_args": 0, "args_description": ""},
    }

    def refresh_records(self):
        records = self.classic.get_packages()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {
            self.singular_class.singular_string: {
                "allow_uninstalled": False,
                "category": "No category assigned",
                "filename": self.random_value(),
                "fill_existing_users": False,
                "fill_user_template": False,
                "hash_type": "MD5",
                "hash_value": "",
                "id": 147,
                "info": "",
                "install_if_reported_available": "false",
                "name": self.random_value(),
                "notes": "",
                "os_requirements": "",
                "priority": 10,
                "reboot_required": False,
                "reinstall_option": "Do Not Reinstall",
                "required_processor": "None",
                "send_notification": False,
                "switch_with_package": "Do Not Install",
                "triggering_files": {},
            }
        }

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_package(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class PatchExternalSource(Record):
    plural_class = "PatchExternalSources"
    singular_string = "patch_external_source"

    def refresh_data(self):
        results = self.classic.get_patch_external_source(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_patch_external_source(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_patch_external_source(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class PatchExternalSources(Records, metaclass=Singleton):
    singular_class = PatchExternalSource
    plural_string = "patch_external_sources"

    def refresh_records(self):
        records = self.classic.get_patch_external_sources()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_patch_external_source(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class PatchInternalSource(Record):
    plural_class = "PatchInternalSources"
    singular_string = "patch_internal_source"

    def refresh_data(self):
        results = self.classic.get_patch_internal_source(self.id)
        pprint(results)
        self._data = results[self.singular_string]

class PatchInternalSources(Records, metaclass=Singleton):
    singular_class = PatchInternalSource
    plural_string = "patch_internal_sources"

    def refresh_records(self):
        records = self.classic.get_patch_internal_sources()
        records = records[self.plural_string]
        pprint(records)
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class PatchPolicy(Record):
    plural_class = "PatchPolicies"
    singular_string = "patch_policy"

    def refresh_data(self):
        results = self.classic.get_patch_policy(self.id)  # , data_type="xml"
        # results = convert.xml_to_dict(results)
        print(results)
        print(type(results))
        pprint(results)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_patch_policy(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_patch_policy(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]

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

    def save(self):
        # If you don't delete the self_service_icon then it will error
        #   <Response [409]>: PUT - https://example.com:8443/JSSResource/patchpolicies/id/18:
        #   Conflict: Error: Problem with icon
        #   Couldn't save changed record: <Response [409]>
        if "self_service_icon" in self.data["user_interaction"]:
            del self.data["user_interaction"]["self_service_icon"]
        return super().save()


class PatchPolicies(Records, metaclass=Singleton):
    singular_class = PatchPolicy
    plural_string = "patch_policies"

    sub_commands = {
        "set_version": {"required_args": 1, "args_description": ""},
    }

    def refresh_records(self):
        records = self.classic.get_patch_policies()
        records = records[self.plural_string]
        pprint(records)
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_patch_policy(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class PatchSoftwareTitle(Record):
    plural_class = "PatchSoftwareTitles"
    singular_string = "patch_software_title"

    def refresh_data(self):
        results = self.classic.get_patch_software_title(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_patch_software_title(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_patch_software_title(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]

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
            except NotFound:
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

    sub_commands = {
        "patchpolicies": {"required_args": 0, "args_description": ""},
        "packages": {"required_args": 0, "args_description": ""},
        "set_package_for_version": {"required_args": 2, "args_description": ""},
        "set_all_packages": {"required_args": 0, "args_description": ""},
        "versions": {"required_args": 0, "args_description": ""},
    }

    def refresh_records(self):
        records = self.classic.get_patch_software_titles()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_patch_software_title(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Peripheral(Record):
    plural_class = "Peripherals"
    singular_string = "peripheral"

    def refresh_data(self):
        results = self.classic.get_peripheral(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_peripheral(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_peripheral(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Peripherals(Records, metaclass=Singleton):
    singular_class = Peripheral
    plural_string = "peripherals"

    def refresh_records(self):
        records = self.classic.get_peripherals()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class PeripheralType(Record):
    plural_class = "PeripheralTypes"
    singular_string = "peripheral_type"

    def refresh_data(self):
        results = self.classic.get_peripheral_type(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_peripheral_type(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_peripheral_type(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class PeripheralTypes(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = PeripheralType
    plural_string = "peripheral_types"

    def refresh_records(self):
        records = self.classic.get_peripheral_types()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}


class Policy(Record):
    plural_class = "Policies"
    singular_string = "policy"

    def refresh_data(self):
        results = self.classic.get_policy(self.id)
        self._data = results[self.singular_string]

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

    def refresh_records(self):
        records = self.classic.get_policies()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_computer_group(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Printer(Record):
    plural_class = "Printers"
    singular_string = "printer"

    def refresh_data(self):
        results = self.classic.get_printer(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_printer(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_printer(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Printers(Records, metaclass=Singleton):
    # http://localhost/printers.html
    singular_class = Printer
    plural_string = "printers"

    def refresh_records(self):
        records = self.classic.get_printers()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_printer(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class RemovableMACAddress(Record):
    plural_class = "RemovableMACAddresses"
    singular_string = "removable_mac_address"

    def refresh_data(self):
        results = self.classic.get_removable_mac_address(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_removable_mac_address(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_removable_mac_address(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class RemovableMACAddresses(Records, metaclass=Singleton):
    # I have no idea how to view this data in the web interface
    singular_class = RemovableMACAddress
    plural_string = "removable_mac_addresses"

    def refresh_records(self):
        records = self.classic.get_removable_mac_addresses()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_removable_mac_address(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Script(Record):
    plural_class = "Scripts"
    singular_string = "script"

    def refresh_data(self):
        results = self.classic.get_script(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_script(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_script(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]

    def script_contents_print_during(self):
        try:
            printme = self.get_path("script_contents")
            print(printme[0])
        except NotFound:
            printme = None


class Scripts(Records, metaclass=Singleton):
    # http://localhost/view/settings/computer/scripts
    singular_class = Script
    plural_string = "scripts"

    sub_commands = {
        "script_contents": {"required_args": 0, "args_description": ""},
    }

    def refresh_records(self):
        records = self.classic.get_scripts()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_script(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class Site(Record):
    plural_class = "Sites"
    singular_string = "site"

    def refresh_data(self):
        results = self.classic.get_site(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_site(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_site(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Sites(Records, metaclass=Singleton):
    # http://localhost/sites.html
    singular_class = Site
    plural_string = "sites"

    def refresh_records(self):
        records = self.classic.get_sites()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_site(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class SoftwareUpdateServer(Record):
    plural_class = "SoftwareUpdateServers"
    singular_string = "update_software_server"

    def refresh_data(self):
        results = self.classic.get_update_software_server(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_update_software_server(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_software_update_server(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class SoftwareUpdateServers(Records, metaclass=Singleton):
    singular_class = SoftwareUpdateServer
    plural_string = "software_update_servers"

    def refresh_records(self):
        records = self.classic.get_software_update_servers()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_update_software_server(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class User(Record):
    plural_class = "Users"
    singular_string = "user"

    def refresh_data(self):
        results = self.classic.get_user(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_user(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_user(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class Users(Records, metaclass=Singleton):
    # http://localhost/users.html?query=
    singular_class = User
    plural_string = "users"

    def refresh_records(self):
        records = self.classic.get_users()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_user(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class UserExtensionAttribute(Record):
    plural_class = "UserExtensionAttributes"
    singular_string = "user_extension_attribute"

    def refresh_data(self):
        results = self.classic.get_user_extension_attribute(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_computer_group(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_user_extension_attribute(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class UserExtensionAttributes(Records, metaclass=Singleton):
    # http://localhost/userExtensionAttributes.html
    singular_class = UserExtensionAttribute
    plural_string = "user_extension_attributes"

    def refresh_records(self):
        records = self.classic.get_user_extension_attributes()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_user_extension_attribute(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class UserGroup(Record):
    plural_class = "UserGroups"
    singular_string = "user_group"

    def refresh_data(self):
        results = self.classic.get_user_group(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_user_group(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_user_group(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class UserGroups(Records, metaclass=Singleton):
    singular_class = UserGroup
    plural_string = "user_groups"

    def refresh_records(self):
        records = self.classic.get_user_groups()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_user_group(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class VPPAccount(Record):
    plural_class = "VPPAccounts"
    singular_string = "vpp_account"

    def refresh_data(self):
        results = self.classic.get_vpp_account(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_vpp_account(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_vpp_account(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class VPPAccounts(Records, metaclass=Singleton):
    singular_class = VPPAccount
    plural_string = "vpp_accounts"

    def refresh_records(self):
        records = self.classic.get_vpp_accounts()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_vpp_account(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class VPPAssignment(Record):
    plural_class = "VPPAssignments"
    singular_string = "vpp_assignment"

    def refresh_data(self):
        results = self.classic.get_vpp_assignment(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_vpp_assignment(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_vpp_assignment(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class VPPAssignments(Records, metaclass=Singleton):
    singular_class = VPPAssignment
    plural_string = "vpp_assignments"

    def refresh_records(self):
        records = self.classic.get_vpp_assignments()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_vpp_assignment(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class VPPInvitation(Record):
    plural_class = "VPPInvitations"
    singular_string = "vpp_invitation"

    def refresh_data(self):
        results = self.classic.get_vpp_invitation(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_vpp_invitation(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_vpp_invitation(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class VPPInvitations(Records, metaclass=Singleton):
    singular_class = VPPInvitation
    plural_string = "vpp_invitations"

    def refresh_records(self):
        records = self.classic.get_vpp_invitations()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_vpp_invitation(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


class WebHook(Record):
    plural_class = "WebHooks"
    singular_string = "webhook"

    def refresh_data(self):
        results = self.classic.get_webhook(self.id)
        self._data = results[self.singular_string]

    def delete(self):
        results = self.classic.delete_webhook(self.id)
        self.plural().refresh_records()

    def save(self):
        if isinstance(self._data, dict):
            newdata = {singular_string: self._data}
            newdata = convert.dict_to_xml(newdata)
            newdata = newdata.encode("utf-8")
        results = self.classic.update_webhook(newdata, id=self.id)
        self.refresh_data()
        self.name = self._data["name"]


class WebHooks(Records, metaclass=Singleton):
    singular_class = WebHook
    plural_string = "webhooks"

    def refresh_records(self):
        records = self.classic.get_webhooks()
        records = records[self.plural_string]
        super().refresh_records(self.singular_class, records)

    def stub_record(self):
        return {self.singular_class.singular_string: {"name": self.random_value()}}

    def create(self, data=None):
        if data is None:
            data = self.stub_record()
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
            data = data.encode("utf-8")
        result = self.classic.create_webhook(data)
        newdata = convert.xml_to_dict(result)
        new_id = newdata[self.singular_class.singular_string]["id"]
        self.refresh_records()
        return self.recordWithId(new_id)


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
