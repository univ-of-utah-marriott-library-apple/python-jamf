#!/usr/bin/env python3

# https://developer.jamf.com/jamf-pro/

from os import environ
from pprint import pprint

from python_jamf import server

HOSTNAME = "http://localhost"
USERNAME = "python-jamf"
PASSWORD = "secret"

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
    # Requires setup
    "PatchPolicies",
    "PatchSoftwareTitles",
    ######################################################################################
    # Who knows
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

pprint(valid_records)


def get_creds():
    if "JAMF_HOSTNAME" in environ:
        hostname = environ["JAMF_HOSTNAME"]
    else:
        hostname = HOSTNAME
    if "JAMF_USERNAME" in environ:
        username = environ["JAMF_USERNAME"]
    else:
        username = USERNAME
    if "JAMF_PASSWORD" in environ:
        password = environ["JAMF_PASSWORD"]
    else:
        password = PASSWORD
    return (hostname, username, password)


hostname, username, password = get_creds()
jps = server.Server(debug=True, hostname=hostname, username=username, password=password)


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
    print("---------------")
    print(f"Print all - {objType}")
    for item in objType:
        print("---------------")
        pprint(item)
        # Check if item contains the "data" attribute
        if hasattr(item, "data"):
            pprint(item.data)


def pre_patch_policy(objType):
    print("Creating a PatchSoftwareTitle first!")
    pstObj = server.records.PatchSoftwareTitles()
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
        pkgObj = getattr(server.records, "Packages")()
        pkgItem = create(pkgObj)
        if pkgItem is None:
            print("Failed to create Package!")
            exit()
        pgkVer["package"] = {"id": pkgItem.data["id"], "name": pkgItem.data["name"]}
        pstItem.save()
    data = objType.stub_record()
    data["patch_policy"]["software_title_configuration_id"] = pstItem.data["id"]
    data["patch_policy"]["general"]["target_version"] = pgkVer["software_version"]
    pprint(data)
    return data


def post_patch_policy():
    pstObj = server.records.PatchSoftwareTitles()
    pstItem = pstObj.recordsWithName("Bare Bones BBEdit")[0]
    delete(pstItem)


def main():
    for valid_record in valid_records:
        print("------------------------------------------------")
        print(valid_record)
        objType = getattr(server.records, valid_record)()
        print_all(objType)
        data = None

        if hasattr(objType, "create_method"):
            if valid_record == "PatchPolicies":
                data = pre_patch_policy(objType)

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
                post_patch_policy()

        print_all(objType)


if __name__ == "__main__":
    main()
