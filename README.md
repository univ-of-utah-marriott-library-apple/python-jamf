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

Since we recorded our session over a month ago, some of the information in our presentation is out of date already. We have spent the time between when we recorded the presentation and now (October 14, 2021) getting GitHub actions working so that it will test and publish to pypi.com. It took longer to get this working than we thought. So that's about where we are. But it works now. We also added some Docker containers that you can run locally to try out `python-jamf` and `jctl`. There are also some minor differences in `pkgctl` than what is shown in the presentation.

I should also mention, one of us also had an issue where we assumed that `pkgctl` was crashing our production Jamf Pro server. But, increasing the amount of RAM and CPU's for that server fixed this issue.
