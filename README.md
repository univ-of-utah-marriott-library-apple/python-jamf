# python-jamf
_Programmatic Automation, Access & Control of Jamf Pro_

![python_jamf_logo](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_logo.png)

## Introduction

`python-jamf` is a Python 3 module to access the Jamf Pro Classic API. The Classic API is the primary tool for programmatic access to data on a Jamf Pro server to allow integrations with other utilities or systems. The concept behind it is to have a class or simply a collection of data (variables) and methods (functions) that maps directly to the API (https://example.com:8443/api).

The `python-jamf` API class doesn't hide anything from you. It handles the URL requests, authentication, and converts between XML/JSON to Python dictionaries/lists.

The `python-jamf` module also provides undocumented access to Jamf Admin functionality used for uploading items to Jamf Distribution Points.

![python_jamf workflow](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/python_jamf_workflow.png)

### Supported Jamf Records

Currently, the `python-jamf` supports 56 Jamf records like Buildings, Categories, Computers, OSXConfigurationProfiles, and Policies for example.

Each record is a Python object, but they are generic. Objects do not have member variables for Jamf data. All Jamf Pro data is stored as a Python dictionary that is accessed with the data() method. Lists of records and individual records use the same object type as well. So all class names are plural, regardless if they represent a list of objects or one object.

## Getting Help

### Wiki

For further in-depth details please check out [the wiki](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki).

### MacAdmin Slack Channel

If you have additional questions, or need more help getting started, post a question on the MacAdmin's Slack [jctl](https://macadmins.slack.com/archives/C01C8KVV2UD) channel.

<p align="center">
<img src="https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/images/MacAdmins_Slack_logo.png" alt="MacAdmin's Slack Logo">
</p>

### Virtual JNUC 2021 Presentation

We will be presenting on `python-jamf` and `jctl` at the upcoming Virtual JNUC 2021 on on Thursday, Oct 21 at 1:00 PM - 1:30 PM MDT on [Turn 1000 clicks into 1 with python-jamf and jctl](https://reg.jamf.com/flow/jamf/jnuc2021/sessioncatalog/page/sessioncatalog/session/1620431676367001smXi)

Since 2010, Apple IT, users, and InfoSec leaders from around the world have rallied at the Jamf Nation User Conference (JNUC) for community presentations, deep-dive education sessions, and expert product insights. Focusing on new and better ways to connect, manage and protect Apple devices that simplify workflows for IT and InfoSec and keep users productive. The Virtual JNUC 2021 experience will be October 19 - October 21, 2021, and there will be no cost to attend the online keynote and sessions.

Anyone and everyone is invited to register for the [virtual experience](https://reg.jamf.com/flow/jamf/jnuc2021/reg/login).

#### What are `python-jamf` and `jctl`?

Originally, it was a "patch" project that was focused on patch management including installer package management, patch management, including assigning package to patch definition, updating versions, version release branching (i.e. development, testing, production), and scripting and automation. Later, it was split into two projects, `python-jamf`, which is a python library that connects to a Jamf Pro server using Jamf Pro Classic API, including keychain support for Jamf Pro credentials via [keyring](https://github.com/jaraco/keyring) python project, support for [PyPi](https://pypi.org/project/python-jamf/) to support pip installation and currently supports 56 Jamf Pro record types which will expand in number as the project continues.

The second project, `jctl`,  is a command-line tool that uses the `python-jamf` library to select objects to create, delete, print and update. It allows performing Jamf Pro repetitive tasks quickly and provides options not available in the web GUI. It is similar to SQL statements, but far less complex. And recently added [PyPi](https://pypi.org/project/https://pypi.org/project/jctl//) to support pip installation.

Our presentation will cover how it works internally as a simple alternative to the usual cURL usage; usage example of workflows comparing using Jamf Pro web interface vs `jctl`; and lastly advanced usage and package management including example os subcommands for specific object types, filtering making interacting with the API simple & easy.

