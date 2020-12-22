# python-jamf

This is a Python 3 utility for maintaining & automating Jamf Pro patch management via command-line. The idea behind it is to have a class that maps directly to the Jamf API (https://example.com:8443/api). The API class doesn't abstract anything or hide anything from you. It simply wraps the url requests, authentication, and converts between python dictionaries and xml. It also prints json.

## Requirements

This utility has been tested on macOS 10.14, macOS 10.15, macOS 11, and CentOS 7.

The python-jamf project requires python3. Please make sure you have that by running the following command.

```bash
python --version
```

or

```bash
python3 --version
```

macOS does not include python3. You can get python3 with [Anaconda](https://www.anaconda.com/) or [Homerew](https://brew.sh/). For example, this is how you install python3 with Homebrew.

```bash
brew install python3
```

## Installation

To install python-jamf globally:

```bash
sudo pip3 install python-jamf
```

To install it locally for the current user:

```bash
pip3 install python-jamf --user
```

If you have /usr/local/bin/plistlib.py make sure it is the python 3 version.

If you don't want to install python-jamf globally you will also need to install requests first.

```bash
pip3 install requests
pip3 install python-jamf
```

## Test

To test your install, start python3's REPL.

```bash
python3
```

Create an api.

```python
import jamf
api = jamf.API()
```

Enter your credentials (it is only interactive if you don't have a config file--see below).

	Hostname (don't forget https:// and :8443): https://example.com:8443
	username: james
	Password:

Then pull some data from the server and print it out.

```python
from pprint import pprint
pprint(api.get('accounts'))
```

You should see something like this.

	{'accounts': {'groups': None,
				'users': {'user': [{'id': '2', 'name': 'james'},
									{'id': '1', 'name': 'root'}]}}}

Are you exited? Try getting these as well.

```python
pprint(api.get('computers'))
pprint(api.get('computergroups'))
pprint(api.get('policies'))
pprint(api.get('categories'))
```

You can view all of the things you can query by going to this url on your jamf server. https://example.com:8443/api/

## Config file

The config file can be setup several ways.

First, you can download [jctl](https://github.com/univ-of-utah-marriott-library-apple/jctl) and run the setconfig.py script. Please see that project for instructions.

Or you can use the [JSSImporter/python-jss configuration](https://github.com/jssimporter/python-jss/wiki/Configuration).

If you don't want to do either of these methods, this script will also look for /Library/Preferences/com.jamfsoftware.jamf.plist and grab the server from there and just ask for username and password.

Or you can specify it in code. By specifying any of the connection settings in code, the config file will be ignored. You either have to specify hostname, username, and password, or you have to pass in promt=True to get it to prompt if you don't specify one of the required parameters (hostname, username, password).

```bash
python3
```

This specifies all of the credentials

```python
import jamf
api = jamf.API(hostname='https://example.com:8443', username='james', password='secret')
```

Or to prompt for the password, use this.

```python
import jamf
api = jamf.API(hostname='https://example.com:8443', username='james', prompt=True)
```

Note, on Linux, the config file is stored as a plist file at ~/.edu.utah.mlib.jamfutil.plist

## Using the API

The API script interacts with Jamf using the get, post, put, and delete commands in combination with the API resources. To see all of your resources, go to the following URL on your server. https://example.com:8443/api

The api can be interacted with via python3 shell. This is how you set it up.

```bash
python3
```

```python
from pprint import pprint
import jamf
api = jamf.API()
```

### Getting data

Note: The API get method downloads the data from Jamf. If you store it in a variable, it does not update itself. If you make changes on the server, you'll need to run the API get again.

Get any information from your jamf server using the classic api endpoints. This includes nested dictionaries.

```python
pprint(api.get('accounts'))
pprint(api.get('buildings'))
pprint(api.get('categories'))
pprint(api.get('computergroups'))
pprint(api.get('computers'))
pprint(api.get('departments'))
pprint(api.get('licensedsoftware'))
pprint(api.get('networksegments'))
pprint(api.get('osxconfigurationprofiles'))
pprint(api.get('packages'))
pprint(api.get('patches'))
pprint(api.get('policies'))
pprint(api.get('scripts'))
```

Get all categories (and deal with the nested dictionaries)

```python
categories = api.get('categories')['categories']['category']
category_names = [x['name'] for x in categories]
print(f"first category: {category_names[0]}")
pprint(category_names)
```

Get computer management information (this demonstrates using an id in the get request)

```python
computers = api.get('computers')['computers']['computer']
pprint(computers[0])
pprint(api.get(f"computermanagement/id/{computers[0]['id']}"))
pprint(api.get(f"computermanagement/id/{computers[0]['id']}/subset/general"))
```

Getting computer groups and filtering using list comprehension filtering.

```python
computergroups = api.get('computergroups')['computer_groups']['computer_group']
smartcomputergroups = [i for i in computergroups if i['is_smart'] == 'true']
pprint(smartcomputergroups)
staticcomputergroups = [i for i in computergroups if i['is_smart'] != 'true']
pprint(staticcomputergroups)
computergroupids = [i['id'] for i in computergroups]
pprint(computergroupids)
```

### Posting data

Create a new static computer group. Note, the id in the url ("1") is ignored and the next available id is used. The name in the url ("ignored") is also ignored and the name in the data ("realname") is what is actually used.

```python
import json
api.post("computergroups/id/1",json.loads( '{"computer_group": {"name": "test", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
api.post("computergroups/name/ignored",json.loads( '{"computer_group": {"name": "realname", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
```

### Updating data

This changes the group "realname" created above to "new name".

```python
import json
api.put("computergroups/name/realname",json.loads( '{"computer_group": {"name": "new name", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
```

This is how you'd get the id.

```python
computergroups = api.get('computergroups')['computer_groups']['computer_group']
newgroup = [i for i in computergroups if i['name'] == 'new name']
```

And this is how to change the name by id.

```python
api.put(f"computergroups/id/{newgroup[0]['id']}",json.loads( '{"computer_group": {"name": "newer name", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
```

### Deleting data

This deletes the 2 groups we just created.

```python
api.delete("computergroups/name/test")
api.delete(f"computergroups/id/{newgroup[0]['id']}")
```

### Updating policies en masse

This is where the real power of this utility comes in.

The following example searches all policies for the custom trigger "update_later" and replaces it with "update_now".

```python
#!/usr/bin/env python3

import jamf

api = jamf.API()
all_policies = api.get('policies')['policies']['policy']
for policy_hook in all_policies:
    policy = api.get(f"policies/id/{policy_hook['id']}")
    name = policy['policy']['general']['name']
    custom_trigger = policy['policy']['general']['trigger_other']
    print(f"Working on {name}")
    if (custom_trigger == "update_later"):
        policy['policy']['general']['trigger_other'] = "update_now"
        api.put(f"policies/id/{policy_hook['id']}", policy)
        print(f"Changed custom trigger from {custom_trigger} to update_now")
```

The next example prints out the code you'd need to enter into a python3 repl to set the custom_triggers. Save the output of this script to a file, then edit the file with the custom triggers you want for each item. Delete the items you don't want to change.

```python
#!/usr/bin/env python3

import jamf

api = jamf.API()
all_policies = api.get('policies')['policies']['policy']

print("""#!/usr/bin/env python3

import jamf

api = jamf.API()
""")

for policy_hook in all_policies:
    policy = api.get(f"policies/id/{policy_hook['id']}")
    custom_trigger = policy['policy']['general']['trigger_other']
    print(f"print(f\"Working on {policy['policy']['general']['name']}\")\n"
          f"policy = api.get(\"policies/id/{policy_hook['id']}\")\n"
          f"policy['policy']['general']['trigger_other'] = "
          f"\"{policy['policy']['general']['trigger_other']}\"\n"
          f"api.put(\"policies/id/{policy_hook['id']}\", policy)\n\n")
```

Save the script as "custom_triggers_1.py" Run it like this.

```bash
./custom_triggers_1.py > custom_triggers_2.py
chmod 755 custom_triggers_2.py
```

Then edit custom_triggers_2.py with the custom triggers you want (and remove what you don't want to modify). Then run custom_triggers_2.py.

### Categories

```python
from jamf.category import Categories
allcategories = Categories()
allcategories.names()
allcategories.ids()
allcategories.categoryWithName("Utilities")
allcategories.categoryWithId(141)

for item in allcategories:
    repr(item)

category = Categories().find("Utilities")
repr(category)
category = Categories().find(141)
repr(category)
```

## Running Tests

The following doesn't work as of 2020/12.

```bash
cd python-jamf

# runs all tests
python3 -m unittest discover -v

# run tests individually
python3 -m python-jamf.tests.test_api
python3 -m jamf.tests.test_config
python3 -m jamf.tests.test_convert
python3 -m jamf.tests.test_package
```

If you see an error that says something like SyntaxError: invalid syntax, check to see if you're using python3.

## Uninstall

Uninstalling python-jamf is easy if you installed it via PIP.
```bash
pip3 uninstall python-jamf

```
PIP will ask you if you want to remove the repositories.
```bash
% pip3 uninstall python-jamf
Found existing installation: python-jamf 0.4.7
Uninstalling python-jamf-0.4.7:
  Would remove:
    /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/jamf/*
    /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/python_jamf-0.4.7.dist-info/*
    /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/tests/*
Proceed (y/n)? 

```
Enter "y" and python-jamf will be removed.

If downloaded via other means you will have to find the package and delete it from there. To find where an older python-jamf version is hiding, look below in the troubleshooting section.

## Troubleshooting

Having errors with different elements of python-jamf. Here are some common errors and how to fix them.

### Which python-jamf is Python using?

With Python having different locations where site-packages can be stored, it can be a difficult to make sure that it is using the correct version. Python-jamf is located in one of the site-package directories. To find the location we have to look at how Python uses site-packages. Python has a hierarchical list of directories it checks for the library. 
The list can be found by using Python's site command.
 ```bash
python3 -m site

```
This produces the list of site-package directories Python checks.
 ```bash
% python3 -m site                                               
sys.path = [
    '/Users/topher/Documents/GitHub/jctl',
    '/Library/Frameworks/Python.framework/Versions/3.8/lib/python38.zip',
    '/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8',
    '/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/lib-dynload',
    '/Users/topher/Library/Python/3.8/lib/python/site-packages',
    '/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages',
]
USER_BASE: '/Users/topher/Library/Python/3.8' (exists)
USER_SITE: '/Users/topher/Library/Python/3.8/lib/python/site-packages' (exists)
ENABLE_USER_SITE: True

```
The top directory in the list is the first place that Python tries to find the particular site-package. Preform a list directory on the file and see if you find "jamf" or "python-jamf" in the directory. "jamf" was the old name that was installed pre-0.4.0. Continue down the list until you have reached where pip has installed python-jamf for you. 

To figure out where PIP has installed python-jamf for you, use this command:
 ```bash
pip show python-jamf

```
In location it will display where PIP has installed python-jamf.
 ```bash
% pip show python-jamf
Name: python-jamf
Version: 0.4.7
Summary: Python wrapper for Jamf Pro API
Home-page: https://github.com/univ-of-utah-marriott-library-apple/python-jamf
Author: The University of Utah
Author-email: mlib-its-mac@lists.utah.edu
License: UNKNOWN
Location: /Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages
Requires: requests
Required-by: 
```
By the time that you have reached the PIP installed directory, the other python-jamf should have been discovered.

## Contributers

- Sam Forester
- James Reynolds
- Topher Nadauld
- Tony Williams