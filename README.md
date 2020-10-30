# python-jamf

This is a Python 3 utility for maintaining & automating Jamf Pro patch management via command-line. The idea behind it is to have a class that maps directly to the Jamf API (https://example.com:8443/api). The API class doesn't abstract anything or hide anything from you. It simply wraps the url requests, authentication, and converts between python dictionaries and xml. It also prints json.

## Under construction!

Note: we are currently (late 2020) splitting this project into 2 different repositories and adding it to pypi.org so that it can be easily installed with pip. Because we are in the middle of the move, we haven't finished updating this readme to reflect all of those changes. The last commit before we started making changes is  [9e8343eb10](https://github.com/univ-of-utah-marriott-library-apple/jctl/tree/9e8343eb10634ee74cd6024885e348672146181d).

## Requirements

The python-jamf project requires python3 and the requests library. Please make sure you have those by running the following commands.

	python --version

or

	python3 --version

To check requests, run this.

	python3
	import requests

macOS does not include python3. You can get python3 with [Anaconda](https://www.anaconda.com/) or [Homerew](https://brew.sh/). For example, this is how you install python3 with Homebrew.

	brew install python3

## Installation

To install python-jamf:

	pip3 install python-jamf
	pip3 install requests

If you have /usr/local/bin/plistlib.py make sure it is the python 3 version.

## Authentication

In order to talk to your Jamf Pro server, you need to set the hostname, username, and password first. This can setup several ways. First, you can download [jctl](https://github.com/univ-of-utah-marriott-library-apple/jctl) and run the setconfig.py script. Or you can use the [JSSImporter/python-jss configuration](https://github.com/jssimporter/python-jss/wiki/Configuration). Or, you can do it by running some python commands. Instructions are forthcoming.

### Troubleshooting Authentication Setup

The above command should reset the authorization property list, but if you have issues with it not working properly delete the property list file and run the command above again.

`rm ~/Library/Preferences/edu.utah.mlib.jamfutil.plist`

### Authenication File Obfuscation

The authorization property list is obfuscated and encrypted based upon the hostname of the Jamf Pro server and user credentials.

### View Authentication File

To view what is stored in this property list, you could use a command-line tool like `cat`, `less`, etc.

For example...

```
$ cat ~/Library/Preferences/edu.utah.mlib.jamfutil.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>Credentials</key>
	<data>
	YnBsaXN0MDSRAQRfEBNjYXNwZXIuc2NsLnV0YWguZWR1TxBCH/k+SqHI7doBuB0l/GIS
	4onl2JLjVwjkMFax1+6YgrEUaYlSI9K83euiuR99iVIj0r/d6qO5H32JUiPSvN3qo7kA
	CAshAAAAAAAAAQEAAAAAAAAAAwAAAAAAAAAAAAAAACAAAGY=
	</data>
	<key>JSSHostname</key>
	<string>jamf.domain.edu</string>
</dict>
</plist>
```

## Using the API

The API script interacts with Jamf using the get, post, put, and delete commands in combination with the API resources. To see all of your resources, go to the following URL on your server. https://example.com:8443/api

The api can be interacted with via python3 shell. This is how you set it up.

```bash
cd python-jamf
python3
```

```python
from pprint import pprint
import logging
import jamf

fmt = '%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s'
logging.basicConfig(level=logging.DEBUG, format=fmt)
logger = logging.getLogger(__name__)

# create an jamf.API object (requires requests lib)
logger.debug("creating api")
jss = jamf.API()
```

### Getting data

Note: The API get method downloads the data from Jamf. If you store it in a variable, it does not update itself. If you make changes on the server, you'll need to run the API get again.

```python
# Get any information from your jss using the classic api endpoints. This includes nested dictionaries.

pprint(jss.get('accounts'))
pprint(jss.get('buildings'))
pprint(jss.get('categories'))
pprint(jss.get('computergroups'))
pprint(jss.get('computers'))
pprint(jss.get('departments'))
pprint(jss.get('licensedsoftware'))
pprint(jss.get('networksegments'))
pprint(jss.get('osxconfigurationprofiles'))
pprint(jss.get('packages'))
pprint(jss.get('patches'))
pprint(jss.get('policies'))
pprint(jss.get('scripts'))

# Get all categories (and deal with the nested dictionaries)

categories = jss.get('categories')['categories']['category']
category_names = [x['name'] for x in categories]
print(f"first category: {category_names[0]}")
pprint(category_names)

# Get computer management information (this demonstrates using an id in the get request)

computers = jss.get('computers')['computers']['computer']
pprint(computers[0])
pprint(jss.get(f"computermanagement/id/{computers[0]['id']}"))
pprint(jss.get(f"computermanagement/id/{computers[0]['id']}/subset/general"))

# Getting smart computer groups using list comprehension filtering.

computergroups = jss.get('computergroups')['computer_groups']['computer_group']
smartcomputergroups = [i for i in computergroups if i['is_smart'] == 'true']
pprint(smartcomputergroups)
staticcomputergroups = [i for i in computergroups if i['is_smart'] != 'true']
pprint(staticcomputergroups)
computergroupids = [i['id'] for i in computergroups]
pprint(computergroupids)
```

### Posting data

```python
# Create a new static computer group. Note, the id in the url ("1") is ignored and the next available id is used. The name in the url ("ignored") is also ignored and the name in the data ("realname") is what is actually used.
import json
jss.post("computergroups/id/1",json.loads( '{"computer_group": {"name": "test", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
jss.post("computergroups/name/ignored",json.loads( '{"computer_group": {"name": "realname", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
```

### Updating data

```python
# Create a new static computer group. Note, the id ("1") is ignored and the next available id is used.

import json
jss.put("computergroups/name/realname",json.loads( '{"computer_group": {"name": "new name", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
jss.put("computergroups/id/900",json.loads( '{"computer_group": {"name": "newer name", "is_smart": "false", "site": {"id": "-1", "name": "None"}, "criteria": {"size": "0"}, "computers": {"size": "0"}}}' ))
```

### Deleting data

```python
jss.delete("computergroups/name/new name")
jss.delete("computergroups/id/900")
```

### Updating policies en masse

This is where the real power of this utility comes in.

The following example searches all policies for the custom trigger "update_later" and replaces it with "update_now".

```python
#!/usr/bin/env python3

import jamf

jss = jamf.API()
all_policies = jss.get('policies')['policies']['policy']
for policy_hook in all_policies:
    policy = jss.get(f"policies/id/{policy_hook['id']}")
    name = policy['policy']['general']['name']
    custom_trigger = policy['policy']['general']['trigger_other']
    print(f"Working on {name}")
    if (custom_trigger == "update_later"):
        policy['policy']['general']['trigger_other'] = "update_now"
        jss.put(f"policies/id/{policy_hook['id']}", policy)
        print(f"Changed custom trigger from {custom_trigger} to update_now")
```

The next example prints out the code you'd need to enter into a python3 repl to set the custom_triggers. Save the output of this script to a file, then edit the file with the custom triggers you want for each item. Delete the items you don't want to change.

```python
#!/usr/bin/env python3

import jamf

jss = jamf.API()
all_policies = jss.get('policies')['policies']['policy']

print("""#!/usr/bin/env python3

import jamf

jss = jamf.API()
""")

for policy_hook in all_policies:
    policy = jss.get(f"policies/id/{policy_hook['id']}")
    custom_trigger = policy['policy']['general']['trigger_other']
    print(f"print(f\"Working on {policy['policy']['general']['name']}\")\n"
          f"policy = jss.get(\"policies/id/{policy_hook['id']}\")\n"
          f"policy['policy']['general']['trigger_other'] = "
          f"\"{policy['policy']['general']['trigger_other']}\"\n"
          f"jss.put(\"policies/id/{policy_hook['id']}\", policy)\n\n")
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

```bash
cd python-jamf

# runs all tests
python3 -m unittest discover -v

# run tests individually
python3 -m jamf.tests.test_api
python3 -m jamf.tests.test_config
python3 -m jamf.tests.test_convert
python3 -m jamf.tests.test_package
```

If you see an error that says something like SyntaxError: invalid syntax, check to see if you're using python3.

## Contributers

- Sam Forester
- James Reynolds
- Topher Nadauld
- Tony Williams