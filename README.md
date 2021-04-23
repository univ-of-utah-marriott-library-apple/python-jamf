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
