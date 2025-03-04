# python-jamf
_Programmatic Automation, Access & Control of Jamf Pro_

![python_jamf_logo](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_logo.png)

## Introduction

`python-jamf` is a Python 3 module to access the Jamf Pro Classic API. The Classic API is a tool for programmatic access to data on a Jamf Pro server to allow integrations with other utilities or systems. The concept behind it is to have a class or simply a collection of data (variables) and methods (functions) that maps directly to the API (https://example.com:8443/api).

![python_jamf workflow](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_workflow.png)

### What are `python-jamf` and `jctl`?

Originally, it was a "patch" project that was focused on patch management including installer package management, patch management, including assigning package to patch definition, updating versions, version release branching (i.e. development, testing, production), and scripting and automation. Later, it was split into two projects. The main project, `python-jamf`, is a python library that allows [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations on about 50 Jamf records using Jamf Pro Classic API and [jps-api-wrapper](https://pypi.org/project/jps-api-wrapper/). It includes keychain support for Jamf Pro credentials using the [keyring](https://github.com/jaraco/keyring) library. You can install python-jamf using [PyPi](https://pypi.org/project/python-jamf/).

The second project, `jctl`,  is a tool that exposes the `python-jamf` CRUD operations to the command line, allowing you to incorporate the tasks in any script, including BASH. It allows performing Jamf Pro repetitive tasks quickly and provides options not available in the web GUI. It is also available from [PyPi](https://pypi.org/project/https://pypi.org/project/jctl/). Please check out the [jctl github page](https://github.com/univ-of-utah-marriott-library-apple/jctl) for more information.

### Supported Jamf Records

Currently, the `python-jamf` supports about 50 Jamf records like Buildings, Categories, Computers, OSXConfigurationProfiles, and Policies for example. The records that `python-jamf` support are very similar and so the code that works with them is almost identical. That means that if learn how to work with one record type, you now know how to work with almost all of them.

Each record is a generic Python object and most functionality comes from the parent Record class. Objects do not have member variables for Jamf data. All Jamf Pro data is stored as a Python dictionary that is accessed with the data() method. All lists of records are subclasses of the Records class.

Except for create and delete, all changes you make are local until you save or refresh the object.

To work with Jamf records that we don't support yet, it's best to use the [jps-api-wrapper](https://pypi.org/project/jps-api-wrapper/) library directly.

### Quick Example

This is just a quick example of the power and ease-of-use of python-jamf. The following code creates a computer record, changes the new record's name, then shows some examples of how to find records, then deletes the record created by the script.

```python
from python_jamf import server

jps = server.Server()

# Get all the computer records.
computers = jps.records.Computers()

# for a list of all record types, see the wiki
# https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki#supported-jamf-records

if "test" not in computers:
    # Create the record (record is auto-saved)
    test_computer = jps.records.Computers().create({'general':{'name': 'test'}})
    record_to_delete = test_computer
else:
    # Get the existing record
    results = computers.recordsWithName("test")
    record_to_delete = None

    # Note, it's possible to create computers with the same name using the API, so you
    # must work with multiple records
    if results > 0:
        # Just take the first one (because multiple records is probably unintended)
        test_computer = results[0]

# Change the name and then save
test_computer.data["general"]["name"] = "test2"
test_computer.save()

# Print the whole record
print(test_computer.data)

# Search by regex
for computer in computers.recordsWithRegex("tes"):
    print(f"{computer.data['general']['name']} has id {computer.data['general']['id']}")
    last_id = computer.data['general']['id']

# Search by ID
last_result = computers.recordWithId(last_id)
if last_result:
    print(f"{last_result.data['general']['name']} has id {computer.data['general']['id']}")

# If this script created a record, delete it
if record_to_delete:
    print(f"Deleting record created by this script")
    record_to_delete.delete() # delete is instant, no need to save
```

All supported record types are accessed like this: `jps.records.Computers()`, `jps.records.Policies()`, `jps.records.Packages()`, etc.

## Quick Start

### Installing

For those that want to try `python-jamf` quickly here are some general steps:

 - Install Module & Requirements: `sudo pip3 install python-jamf`
 - Create an Jamf Pro API User
 - Enter hostname, username, and password
 - Test: `conf-python-jamf -t`

### Uninstalling

Uninstalling `python-jamf` is easy if you installed it via `pip`. `pip` is the **P**ackage **I**nstaller for **P**ython.

To uninstall `python-jamf` run the following command:

```bash
sudo pip3 uninstall python-jamf
```

### Upgrading

Upgrading `python-jamf` is easy if you installed it via `pip`. `pip` is the **P**ackage **I**nstaller for **P**ython.

To upgrade `python-jamf` run the following command:

```bash
sudo pip3 install --upgrade python-jamf
```

## Getting Help

### Wiki

#### More Documentation

For further in-depth details please check out [the wiki](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki).

#### Searching the wiki

To search this wiki use the "Search" field in the GitHub navigation bar above. Then on the search results page select the "Wiki" option or [click here](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/search?q=&type=Wikis&utf8=✓) and search.

### MacAdmin Slack Channel

If you have additional questions, or need more help getting started, post a question on the MacAdmin's Slack [jctl](https://macadmins.slack.com/archives/C01C8KVV2UD) channel.

<p align="center">
<img src="https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/MacAdmins_Slack_logo.png" alt="MacAdmin's Slack Logo">
</p>

## Latest Status

### Releases

Please see the [Changelog](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/blob/main/CHANGELOG.md) for all release notes.

Thank you yairf-s1 and pythoninthegrass for your contributions.

See `python-jamf` [upgrade](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/Installing#upgrading) documentation to upgrade to latest release.

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
