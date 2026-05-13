# python-jamf
_Programmatic Automation, Access & Control of Jamf Pro_

![python_jamf_logo](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_logo.png)

## Introduction

`python-jamf` is a Python 3 library to access the Jamf Pro Classic API. It also comes with the CLI tool, `jctl`. The Classic API is a tool for programmatic access to data on a Jamf Pro server to allow integrations with other utilities or systems. The concept behind it is to have a class or simply a collection of data (variables) and methods (functions) that maps directly to the API (https://example.com:8443/api).

![python_jamf workflow](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_workflow.png)

### What are `python-jamf` and `jctl`?

This repository contains both the `python-jamf` library and the `jctl` command-line interface.

`python-jamf` is a Python library that allows [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) operations on about 50 Jamf records using the Classic API and [jps-api-wrapper](https://pypi.org/project/jps-api-wrapper/). It includes keychain support for Jamf Pro credentials using the [keyring](https://github.com/jaraco/keyring) library. We are slowly adding newer Jamf Pro API support. You can install python-jamf and `jctl` using [PyPi](https://pypi.org/project/python-jamf/).

`jctl` exposes `python-jamf` CRUD operations at the command line, allowing you to incorporate Jamf tasks into scripts (including BASH). It can automate repetitive tasks and provide options not available in the web GUI.

There are a few other tools that are part of this project. `pkgctl` automates operations with packages, such as promotion and creating patch definitions.

### Supported Jamf Records

Currently, the `python-jamf` and `jctl` support about 50 Jamf records like Buildings, Categories, Computers, OSXConfigurationProfiles, and Policies. The supported records are very similar to each other and so if learn how to work with one record type, you will know how to work with almost all of them.

Each record is a generic Python object and most functionality comes from the parent Record class. Objects do not have member variables for Jamf data. All Jamf Pro data is stored as a Python dictionary that is accessed with the `data` attribute. All lists of records are subclasses of the Records class.

Except for create and delete, all changes you make are local until you save or refresh the object.

To work with Jamf records that we don't support yet, it's best to use the [jps-api-wrapper](https://pypi.org/project/jps-api-wrapper/) library directly.

### Quick Example

`jctl` gives the shell access to Jamf records:

```bash
# List all computers.
jctl computers

# Show one computer.
jctl computers --name "Lab Mac 01" --long

# Print the serial number from matching records.
jctl computers --regex "^Lab Mac" --path general/serial_number

# Create a category from JSON.
jctl categories --json --create '{"name": "Testing"}'

# Update a category.
jctl categories --name "Testing" --update name="Testing Updated"

# Delete a category after confirmation.
jctl categories --name "Testing Updated" --delete
```

`pkgctl` is a cli tool that allows package promotion and patch package patching.

Here are some examples of jtcl and pkgctl.

```
# Create a smart computer group with a with a criteria.
jctl computergroups -j -c '{"name": "Needs Zoom 5.11.11", "is_smart": "true", "criteria": {"size": "1", "criterion": [{"name": "Computer Name", "priority": "0", "and_or": "and", "search_type": "is", "value": "computer1", "opening_paren": "false", "closing_paren": "false"}]}}'

# Create 3 packages
jctl packages -c "Zoom-5.11.11 (10514).pkg"
jctl packages -c "Zoom-5.11.10 (10279).pkg"
jctl packages -c "Zoom-5.11.9 (10046).pkg"

# Create a policy and add a package step
jctl policies -c "Install Zoom1"
jctl policies -r "Install Zoom1" -j -u package_configuration='{"packages": {"package": [{"name": "Zoom-5.11.11 (10514).pkg", "action": "Install"}]}}'

# Create a patch policy
jctl patchsoftwaretitles -j -c '{"name": "Zoom Client for Meetings", "name_id": "0F9", "source_id": "1"}'

# Match patch with packages
pkgctl -p

# Create patch policies
jctl patchpolicies -j -c '{"general": {"name": "Zoom 1","target_version": "5.11.10 (10279)"},"software_title_configuration_id": "2"}'
jctl patchpolicies -j -c '{"general": {"name": "Zoom 2","target_version": "5.11.11 (10514)"},"software_title_configuration_id": "2"}'
```

The `python-jamf` library is what powers jctl. The following code creates a computer record, changes the new record's name, shows examples of how to find records, then deletes the record created by the script.

```python
from python_jamf import Server

# Uses the config created by `conf-python-jamf`.
jps = Server()

# Get all the computer records.
computers = jps.Computers()

# for a list of all record types, see the wiki
# https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki#supported-jamf-records

# Print the names of all the computers, then print all the ids
print(computers.names())
print(computers.ids())

# Clean up any records left by a previous run of this example.
for computer in computers.recordsWithRegex("^python-jamf-example"):
    computer.delete()

# Create the record. The record is saved immediately.
test_computer = computers.create({"general": {"name": "python-jamf-example"}})

# Get the computer by name. It is possible for Jamf Pro to have multiple
# records with the same name, so this returns a list.
test_computer = computers.recordsWithName("python-jamf-example")[0]

# Change the name and then save.
test_computer.set_path("general/name", "python-jamf-example-updated")
test_computer.save()

# Print the whole record.
print(test_computer.data)

# Search by regex.
for computer in computers.recordsWithRegex("^python-jamf-example"):
    print(f"{computer.name} has id {computer.id}")

# Search by ID.
last_result = computers.recordWithId(test_computer.id)
if last_result:
    print(f"{last_result.id} has name {last_result.name}")

# Delete is instant, with no need to save.
print("Deleting record created by this script")
test_computer.delete()
```

All supported record types are accessed like this: `jps.Computers()`, `jps.Policies()`, `jps.Packages()`, etc. Note: python-jamf versions prior to 0.10.0 used `jps.records.Computers()`. 0.10.0 deprecates this. Please switch to `jps.Computers()`.

## Quick Start

### Installing

For those that want to try `python-jamf` quickly here are some general steps:

- Install Module & Requirements: `pip3 install python-jamf`
- Create an Jamf Pro API User: `conf-python-jamf`
- Enter hostname, username, and password
- Test: `conf-python-jamf -t`

You might need to use `sudo pip3 install python-jamf`, depending on how you have Python installed.

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
pip3 install --upgrade python-jamf
```

You might need to use `sudo pip3 install --upgrade python-jamf`, depending on how you have Python installed.

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

We would like to thank the following for their contributions: <em>0xmachos, homebysix, Honestpuck, ORyanHampton, pythoninthegrass, SamBaRufus, Tophernad, yairf-s1</em>
