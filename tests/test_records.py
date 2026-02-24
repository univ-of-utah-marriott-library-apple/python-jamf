#!/usr/bin/env python3

# https://developer.jamf.com/jamf-pro/

import sys
from os import environ
from pathlib import Path
from pprint import pprint

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python_jamf import server

# valid_records = server.records.valid_records()
valid_records = (
    # Done
    "AdvancedComputerSearches",
    "AdvancedMobileDeviceSearches",
    "AdvancedUserSearches",
    "Buildings",
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
    "MacApplications",
    "MobileDeviceApplications",
    "MobileDeviceExtensionAttributes",
    "MobileDeviceInvitations",
    "MobileDevices",
    "NetworkSegments",
    "Packages",
    "Policies",
    "Printers",
    "RemovableMACAddresses",
    "Scripts",
    "Sites",
    "UserExtensionAttributes",
    "UserGroups",
    "Users",
    "MobileDeviceConfigurationProfiles",
    "MobileDeviceEnrollmentProfiles",
    "WebHooks",
    ######################################################################################
    ## Requires setup
    #"PatchPolicies",
    #"PatchSoftwareTitles",
    ######################################################################################
    ## Who knows
    # "BYOProfiles",
    # "LDAPServers",
    # "ManagedPreferenceProfiles",
    # "MobileDeviceProvisioningProfiles",
    # "OSXConfigurationProfiles",
    # "PatchExternalSources",
    # "PatchInternalSources",
    # "Peripherals",
    # "PeripheralTypes",
    # "SoftwareUpdateServers",
    # "VPPAccounts",
    # "VPPAssignments",
    # "VPPInvitations",
)


def get_creds(hostname_env, username_env, password_env):
    hostname = None
    username = None
    password = None
    if hostname_env in environ:
        hostname = environ[hostname_env]
    if username_env in environ:
        username = environ[username_env]
    if password_env in environ:
        password = environ[password_env]
    return (hostname, username, password)


def print_one(item):
    # Print one
    print("---------------")
    print(f"Print one - {item}")
    pprint(item)
    pprint(item.data)


def delete(item):
    # Delete
    if hasattr(item, "delete_method"):
        print("---------------")
        print(f"Delete - {item}")
        item.delete()


def update(item):
    # Update
    if hasattr(item, "update_method"):
        print("---------------")
        print(f"Update - {item}")
        print(item)
        item.set_data_name(item.get_data_name() + " Updated")
        item.save()


def create(objType, data=None):
    print("---------------")
    print(f"Create - {objType}")
    item = objType.create(data)
    return item


def print_all(objType):
    # Print all
    first_time = True
    for item in objType:
        if first_time:
            print("---------------")
            print(f"Print all - {objType}")
            first_time = False
        print("---------------")
        pprint(item)
        # Check if item contains the "data" attribute
        if hasattr(item, "data"):
            pprint(item.data)


def pre_patch_policy(jps, objType):
    print("Creating a PatchSoftwareTitle first!")
    pstObj = jps.records("PatchSoftwareTitles")
    pstItem = None
    try:
        pstItem = create(pstObj)
    except:
        pass
    if pstItem is None:
        print("PatchSoftwareTitle probably already exists, searching for it.")
        pstItem = pstObj.recordsWithName("Bare Bones BBEdit")[0]
        if pstItem is None:
            print("Failed to create or find 'Bare Bones BBEdit' PatchSoftwareTitle!")
            exit()
    pgkVer = pstItem.data["versions"]["version"][0]
    if pgkVer["package"] is None:
        print("Creating a Package first!")
        pkgObj = jps.records("Packages")
        pkgItem = create(pkgObj)
        if pkgItem is None:
            print("Failed to create Package!")
            exit()
        pgkVer["package"] = {"id": pkgItem.data["id"], "name": pkgItem.data["name"]}
        pstItem.save()
    data = objType.stub_record()
    data["software_title_configuration_id"] = pstItem.data["id"]
    data["general"]["target_version"] = pgkVer["software_version"]
    pprint(data)
    return data


def post_patch_policy(jps):
    pstObj = jps.records("PatchSoftwareTitles")
    pstItem = pstObj.recordsWithName("Bare Bones BBEdit")[0]
    delete(pstItem)


def main():
    pprint(valid_records)

    print("------------------------------------------------")

    servers = []
    for env_var_names in [
        ["JAMF_HOSTNAME", "JAMF_USERNAME", "JAMF_PASSWORD"],
        #["JAMF_HOSTNAME2", "JAMF_USERNAME2", "JAMF_PASSWORD2"],
    ]:
        hostname, username, password = get_creds(env_var_names[0], env_var_names[1], env_var_names[2])
        print(hostname, username)
        if password is not None and password != "":
            print("Password is set")
            jps = server.Server(debug=True, hostname=hostname, username=username, password=password)
            servers.append(jps)

    for jps in servers:
        print("------------------------------------------------------------------------------------------")
        print(f"Server: {jps.config.hostname}")
        for valid_record in valid_records:
            print("-----------------------------------------")
            print(valid_record)

            objType = jps.records(valid_record)
            print(objType)
            print_all(objType)
            data = None
            if hasattr(objType, "create_method"):
                if valid_record == "PatchPolicies":
                    data = pre_patch_policy(jps, objType)

                pprint(data)
                item = create(objType, data)

                if item is not None:
                    pprint(item)
                    pprint(item.data)

                    item = objType.recordWithId(item.id)
                    print_one(item)

                    update(item)

                    item = objType.recordWithId(item.id)
                    print_one(item)

                    delete(item)

                else:
                    print("Failed to create!")
                    exit()

                if valid_record == "PatchPolicies":
                    post_patch_policy(jps)

            print_all(objType)


if __name__ == "__main__":
    main()
