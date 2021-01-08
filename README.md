# python-jamf

This is a Python 3 module to access the Jamf Pro classic API. The idea behind it is to have a class that maps directly to the API (https://example.com:8443/api). The API class doesn't abstract anything or hide anything from you. It simply wraps the url requests, authentication, and converts between python dictionaries and xml. It also prints json.

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

*For further details please check out [the wiki](https://github.com/univ-of-utah-marriott-library-apple/python-jamf/wiki/Introduction).

