# python-jamf
_Programmatic Automation, Access & Control of Jamf Pro_

![python_jamf_logo](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_logo.png)

## Introduction

`python-jamf` is a Python 3 module to access the Jamf Pro Classic API. The Classic API is the primary tool for programmatic access to data on a Jamf Pro server to allow integrations with other utilities or systems. The concept behind it is to have a class or simply a collection of data (variables) and methods (functions) that maps directly to the API (https://example.com:8443/api).

The `python-jamf` API class doesn't hide anything from you. It handles the URL requests, authentication, and converts between XML/JSON to Python dictionaries/lists.

The `python-jamf` module also provides undocumented access to Jamf Admin functionality used for uploading items to Jamf Distribution Points.

![python_jamf workflow](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_workflow.png)

### What are `python-jamf` and `jctl`?

Originally, it was a "patch" project that was focused on patch management including installer package management, patch management, including assigning package to patch definition, updating versions, version release branching (i.e. development, testing, production), and scripting and automation. Later, it was split into two projects, `python-jamf`, which is a python library that connects to a Jamf Pro server using Jamf Pro Classic API, including keychain support for Jamf Pro credentials via [keyring](https://github.com/jaraco/keyring) python project, support for [PyPi](https://pypi.org/project/python-jamf/) to support pip installation and currently supports 56 Jamf Pro record types which will expand in number as the project continues.

The second project, `jctl`,  is a command-line tool that uses the `python-jamf` library to select objects to create, delete, print and update. It allows performing Jamf Pro repetitive tasks quickly and provides options not available in the web GUI. It is similar to SQL statements, but far less complex. And recently added [PyPi](https://pypi.org/project/https://pypi.org/project/jctl//) to support pip installation.

Please check out the [jctl github page](https://github.com/univ-of-utah-marriott-library-apple/jctl) for more information.

### Supported Jamf Records

Currently, the `python-jamf` supports about 50 Jamf records like Buildings, Categories, Computers, OSXConfigurationProfiles, and Policies for example.

Each record is a singleton Python object, but they are generic and most functionality comes from the parent Record class. Objects do not have member variables for Jamf data. All Jamf Pro data is stored as a Python dictionary that is accessed with the data() method. All lists of records are singleton subclasses of the Records class.

By being singleton classes, you perform one fetch to the server for each list or record. This prevents multiple fetches for the same object. All changes you make are local until you save or refresh the object.

Note, python-jamf can work with unsupported Jamf records, it just isn't as easy as the next section shows.

### Quick Example

This is just a quick example of the power and ease-of-use of python-jamf. The following code prints the last_contact_time from all computer records, from a computer record with the ID of 1, a computer record named "Jimmy's Mac", and computer records that match a regex. Then, it searches for a computer by name and if it exists then it changes the name. Lastly, it shows how to delete and create records.

	import jamf
	for computer in jamf.Computers(): # Retreive the data from the server
		print(computer.data["general"]["last_contact_time"])

	computers = jamf.Computers()      # Use the data retrieved above, don't re-download
	computers.refresh()               # Re-download the records from the server

	if "1" in computers:
	    print(computers.recordWithId(1).data['general']['last_contact_time'])

	if "Jimmy's Mac" in computers:
	    print(computers.recordWithName("Jimmy's Mac").data['general']['last_contact_time'])

	for computer in computers.recordsWithRegex("J[ia]m[myes]{2}'s? Mac"): # Matches Jimmy's, James', and James's
		print(computer.data["general"]["last_contact_time"])

	computer = computers.recordWithName("James's Mac)
	if computer:
		computer.refresh()            # Re-download the record from the server
		computer.data['general']['name'] = "James' Mac"
		computer.save()

A few notes. You can replace `jamf.Computers()` with `jamf.Policies()` or any supported record type.

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

:new: [python-jamf - 0.7.4](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/releases/tag/0.7.4-af4107c6)

 - Bearer token support
 - Fixed bug when creating records (shallow vs deep copy)
 - Fixed version in setup.py bug
 - Removed jamfnet from main docker-compose and move it to it's own file
 - Support smb mounting on linux

Thank you yairf-s1 and pythoninthegrass for your contributions.

See `python-jamf` [upgrade](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/Installing#upgrading) documentation to upgrade to latest release.

### Known Breaking Changes on the Roadmap

There is a change that we would eventually like to make that we realize could break anything built with this library. This takes a little explaining.

Sam Forester, the original author of the API, and others have said that the JSON returned from the Jamf server is buggy. I believe someone at Jamf has said that a lot of it has been fixed, but we don't really know the status. All we know is that the API isn't getting JSON, it's getting XML and converting it to python data structures. However, the XML is formatted in such a way that this library does array conversion goofy. Here is an example.

This XML is of an array with 1 item.

	<?xml version="1.0" encoding="UTF-8"?>
	<policies>
		<size>1</size>
		<policy>
			<id>1</id>
			<name>Update Inventory</name>
		</policy>
	</policies>

This XML is of an array with 2 items.

	<?xml version="1.0" encoding="UTF-8"?>
	<policies>
		<size>2</size>
		<policy>
			<id>2</id>
			<name>New</name>
		</policy>
		<policy>
			<id>1</id>
			<name>Update Inventory</name>
		</policy>
	</policies>

This is the python with 1 item.

	{
		'policies': {
			'size': '1',
			'policy': { 'id': '1', 'name': 'Update Inventory'
			}
		}
	}

This is the python with 2 items.

	{
		'policies': {
			'size': '2',
			'policy': [
				{'id': '2', 'name': 'New'},
				{'id': '1', 'name': 'Update Inventory'}
			]
		}
	}

Do you see the huge difference? When an array has more than one item, it's converted into an actual Python array. But if it's only got one, it's converted to a dictionary. This is a giant problem and has been a pain in our side. Our goal is to fix this.

There are several giveaways to help us fix it. First, array's have a size key/value pair. I think some arrays don't include a size key/value pair, but there's more giveaways. Second, the items in the array have singlar names of the parent array ("policy" inside of "policies"). Third, we have a swagger specification file that tells us what should be an array. Lastly, we could just get the JSON, but unless we do an exhaustive comparison to make sure it's not buggy, I'd rather just stick with the XML.

We have written code to deal with this on a case by case basis as we bump into errors, but we really need to solve this globally. We haven't started working on this yet, but it is on our roadmap.

