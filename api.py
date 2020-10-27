#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JSS API
Modifications by Tony Williams (tonyw@honestpuck.com) (ARW)
Modifications have been to make "raw=True" always return raw, removed the
ability to ask for json, and simplified the config code. It no longer
asks for config but reads a config file in AutoPkg format.
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.4.0"

import html.parser
import logging
import logging.handlers
import pathlib
from os import path
import plistlib
import subprocess
import requests

from . import convert
from . import config

LOGLEVEL = logging.DEBUG

#pylint: disable=unnecessary-pass
class Error(Exception):
    """ just passing through """
    pass


#pylint: disable=super-init-not-called
class APIError(Error):
    """ Error in our call """
    def __init__(self, response):
        self.response = response
        err = parse_html_error(response.text)
        self.message = ": ".join(err) or 'failed'

    def __getattr__(self, attr):
        """
        missing attributes fallback on response
        """
        return getattr(self.response, attr)

    def __str__(self):
        rsp = self.response
        return f"{rsp}: {rsp.request.method} - {rsp.url}: {self.message}"


class Singleton(type):
    """ allows us to share a single object """
    _instances = {}
    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class API(metaclass=Singleton):
    """
    Class for making api calls to JSS
    """
    session = False

    def __init__(self, autopkg_config=None, hostname=None, auth=None, config_path=None):
        """
        Create requests.Session with JSS address and authentication

        :param autopkg_config <str>: Path to file containing config. If it
                                     starts with '~' character we pass it
                                     to expanduser.
        :param hostname <str>:       hostname of server
        :param auth <(str, str)>:    (username, password) for server
        """
        self.log = logging.getLogger(f"{__name__}.API")
        self.log.setLevel(LOGLEVEL)

        conf = config.SecureConfig(path=config_path)
        if conf.exists():
            # get url from /Library/Preferences/com.jamfsoftware.jamf.plist?
            hostname = hostname or conf.get('JSSHostname', prompt='JSS Hostname')
            auth = conf.credentials(hostname, auth)
            hostname = f"https://{hostname}:8443"

        if not hostname:
            if not autopkg_config:
                autopkg_config = "~/Library/Preferences/com.github.autopkg.plist"

            if autopkg_config[0] == '~':
                plist = path.expanduser(autopkg_config)
            else:
                plist = autopkg_config
            fptr = open(plist, 'rb')
            prefs = plistlib.load(fptr)
            fptr.close()
            hostname = prefs["JSS_URL"]
            auth = (prefs["API_USERNAME"], prefs["API_PASSWORD"])

        self.url = f"{hostname}/JSSResource"
        self.session = requests.Session()
        self.session.auth = auth
        self.session.headers.update({'Accept': 'application/xml'})

        # The commented ones are untested because I don't have any data of that
        # type in my JSS
        self.base_search_paths = {
            'accounts': [
                'accounts',
                'accounts',
                'users',
                'user'
            ],
#             'accountGroups': [
#                 'accounts',
#                 'accounts',
#                 'groups',
#                 'group'
#             ],
            'advancedcomputersearches': [
                'advancedcomputersearches',
                'advanced_computer_searches',
                'advanced_computer_search'
            ],
#             'advancedmobiledevicesearches': [
#                 'advancedmobiledevicesearches',
#                 'advanced_mobile_device_searches',
#                 'advanced_mobile_device_search'
#             ],
#             'advancedusersearches': [
#                 'advancedusersearches',
#                 'advanced_user_searches',
#                 'advanced_user_search'
#             ],
            'buildings': [
                'buildings',
                'buildings',
                'building'
            ],
#             'byoprofiles': [
#                 'byoprofiles',
#                 'byoprofiles',
#                 'byoprofile'
#             ],
            'categories': [
                'categories',
                'categories',
                'category'
            ],
#             'classes': [
#                 'classes',
#                 'classes',
#                 'class'
#             ],
            'computerconfigurations': [
                'computerconfigurations',
                'computer_configurations',
                'computer_configuration'
            ],
            'computergroups': [
                'computergroups',
                'computer_groups',
                'computer_group'
            ],
            'computerreports': [
                'computerreports',
                'computer_reports',
                'computer_report'
            ],
            'computers': [
                'computers',
                'computers',
                'computer'
            ],
            'departments': [
                'departments',
                'departments',
                'department'
            ],
            'directorybindings': [
                'directorybindings',
                'directory_bindings',
                'directory_binding'
            ],
            'diskencryptionconfigurations': [
                'diskencryptionconfigurations',
                'disk_encryption_configurations',
                'disk_encryption_configuration'
            ],
            'distributionpoints': [
                'distributionpoints',
                'distribution_points',
                'distribution_point'
            ],
#             'dockitems': [
#                 'dockitems',
#                 'dock_items',
#                 'dock_item'
#             ],
#             'ebooks': [
#                 'ebooks',
#                 'ebooks',
#                 'ebook'
#             ],
#             'ibeacons': [
#                 'ibeacons',
#                 'ibeacons',
#                 'ibeacon'
#             ],
#             'jsonwebtokenconfigurations': [
#                 'jsonwebtokenconfigurations',
#                 'json_web_token_configurations',
#                 'json_web_token_configuration'
#             ],
#             'ldapservers': [
#                 'ldapservers',
#                 'ldap_servers',
#                 'ldap_server'
#             ],
            'licensedsoftware': [
                'licensedsoftware',
                'licensed_software',
                'licensed_software'
            ],
#             'macapplications': [
#                 'macapplications',
#                 'mac_applications',
#                 'mac_application'
#             ],
#             'managedpreferenceprofiles': [
#                 'managedpreferenceprofiles',
#                 'managed_preference_profiles',
#                 'managed_preference_profile'
#             ],
#             'mobiledeviceapplications': [
#                 'mobiledeviceapplications',
#                 'mobile_device_applications',
#                 'mobile_device_application'
#             ],
#             'mobiledevicecommands': [
#                 'mobiledevicecommands',
#                 'mobile_device_commands',
#                 'mobile_device_command'
#             ],
#             'mobiledeviceconfigurationprofiles': [
#                 'mobiledeviceconfigurationprofiles',
#                 'mobile_device_configuration_profiles',
#                 'configuration_profiles'
#             ],
#             'mobiledeviceenrollmentprofiles': [
#                 'mobiledeviceenrollmentprofiles',
#                 'mobile_device_enrollment_profiles',
#                 'mobile_device_enrollment_profile'
#             ],
#             'mobiledeviceextensionattributes': [
#                 'mobiledeviceextensionattributes',
#                 'mobile_device_extension_attributes',
#                 'mobile_device_extension_attribute'
#             ],
#             'mobiledeviceinvitations': [
#                 'mobiledeviceinvitations',
#                 'mobile_device_invitations',
#                 'mobile_device_invitation'
#             ],
#             'mobiledeviceprovisioningprofiles': [
#                 'mobiledeviceprovisioningprofiles',
#                 'mobile_device_provisioning_profiles',
#                 'mobile_device_provisioning_profile'
#             ],
#             'mobiledevices': [
#                 'mobiledevices',
#                 'mobile_devices',
#                 'mobile_device'
#             ],
            'netbootservers': [
                'netbootservers',
                'netboot_servers',
                'netboot_server'
            ],
            'networksegments': [
                'networksegments',
                'network_segments',
                'network_segment'
            ],
            'osxconfigurationprofiles': [
                'osxconfigurationprofiles',
                'os_x_configuration_profiles',
                'os_x_configuration_profile'
            ],
            'packages': [
                'packages',
                'packages',
                'package'
            ],
            'patchexternalsources': [
                'patchexternalsources',
                'patch_external_sources',
                'patch_external_source'
            ],
            'patchinternalsources': [
                'patchinternalsources',
                'patch_internal_sources',
                'patch_internal_source'
            ],
            'patchpolicies': [
                'patchpolicies',
                'patch_policies',
                'patch_policy'
            ],
            'patchsoftwaretitles': [
                'patchsoftwaretitles',
                'patch_software_titles',
                'patch_software_title'
            ],
#             'peripherals': [
#                 'peripherals',
#                 'peripherals',
#                 'peripheral'
#             ],
            'peripheraltypes': [
                'peripheraltypes',
                'peripheral_types',
                'peripheral_type'
            ],
            'policies': [
                'policies',
                'policies',
                'policy'
            ],
            'printers': [
                'printers',
                'printers',
                'printer'
            ],
#             'removablemacaddresses': [
#                 'removablemacaddresses',
#                 'removable_mac_addresses',
#                 'removable_mac_address'
#             ],
            'restrictedsoftware': [
                'restrictedsoftware',
                'restricted_software',
                'restricted_software_title'
            ],
            'scripts': [
                'scripts',
                'scripts',
                'script'
            ],
#             'sites': [
#                 'sites',
#                 'sites',
#                 'site'
#             ],
#             'softwareupdateservers': [
#                 'softwareupdateservers',
#                 'software_update_servers',
#                 'software_update_server'
#             ],
#             'userextensionattributes': [
#                 'userextensionattributes',
#                 'user_extension_attributes',
#                 'user_extension_attribute'
#             ],
#             'usergroups': [
#                 'usergroups',
#                 'user_groups',
#                 'user_group'
#             ],
            'users': [
                'users',
                'users',
                'user'
            ],
#             'vppaccounts': [
#                 'vppaccounts',
#                 'vpp_accounts',
#                 'vpp_account'
#             ],
#             'vppassignments': [
#                 'vppassignments',
#                 'vpp_assignments',
#                 'vpp_assignment'
#             ],
#             'vppinvitations': [
#                 'vppinvitations',
#                 'vpp_invitations',
#                 'vpp_invitation'
#             ],
#             'webhooks': [
#                 'webhooks',
#                 'webhooks',
#                 'webhook'
#             ],
        }

    def get(self, endpoint, raw=False):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("getting: %s", endpoint)
        response = self.session.get(url)

        if raw:
            return response
        if not response.ok:
            raise APIError(response)
        return convert.xml_to_dict(response.text)

    def post(self, endpoint, data, raw=False):
        """
        Create new entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("creating: %s", endpoint)
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
        response = self.session.post(url, data=data)

        if raw:
            return response
        if not response.ok:
            raise APIError(response)

        # return successfull response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def put(self, endpoint, data, raw=False):
        """
        Update existing entries on JSS

        :param endpoint <str>:  JSS endpoint (e.g. "policies/id/0")
        :param data <dict>:     data to be submitted
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns dict:          response data
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("updating: %s", endpoint)
        if isinstance(data, dict):
            data = convert.dict_to_xml(data)
        response = self.session.put(url, data=data)

        if raw:
            return response
        if not response.ok:
            raise APIError(response)

        # return successful response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def delete(self, endpoint, raw=False):
        """
        Delete entry on JSS

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw  <bool>:     return requests.Response obj (skip errors)

        :returns <dict|requests.Response>:
        """
        url = f"{self.url}/{endpoint}"
        self.log.debug("getting: %s", endpoint)
        response = self.session.delete(url)

        if raw:
            return response
        if not response.ok:
            raise APIError(response)

        # return successful response data (usually: {'id': jssid})
        return convert.xml_to_dict(response.text)

    def convertJSSPathToArray(self, mydict, path):
        """
        Dig into a JSS Search Result and returns an array

        For some reason the JSS API returns arrays when there's more than one
        object type, but returns a dict if there's only one object. So if you
        have one computer, it will be a dict, but if you have 2, it will be an
        array. This converts deals with it and returns only an array, even if
        it's an array with one item.

        For this function to work the path must end with a list of
        dictionaries that have 'name' and 'id' or end with a single
        dictionary that has 'name' and 'id'.

        :param mydict <dict>:  The dictionary to dive into
        :param path <dict>:  The path used to search

        :returns list:
        """

        temp = mydict
        for ii in path:
            if not temp:
                # accountGroups goes down this path
                # print("empty array 1")
                return []
            if ii in temp:
                # print(f"Looking for {ii}")
                temp = temp[ii]
        # print(f"Result {temp}")
        if not temp:
            raise APIError("convertJSSPathToArray error 1, temp in undef")
        elif isinstance(temp, (dict)):
            if 'size' in temp and temp['size'] == '0':
                # print("empty array 3")
                return []
            elif 'name' in temp and 'id' in temp:
                return [temp]
            else:
                self.log.debug(f"getting: {endpoint!r}")

                print(f"DICT: {temp}")
                raise APIError("convertJSSPathToArray error 1, temp is a dict."
                               "This method only returns lists")
#                 return None

        elif isinstance(temp, (list)):
            return temp
        else:
            print(f"What is this: {temp}")
            raise APIError("convertJSSPathToArray error 1, temp is not a list."
                           "This method only returns lists")

    def convertJSSPathToNamedIds(self, mydict, path):
        """
        Dig into a JSS Query Result and returns an array of dictionaries
        with the JSS object names as keys and the ids as the value. Note,
        this method will throw away all data except 'name' and 'id'. If you
        want all of the data use convertJSSPathToNamedDict.

        For this function to work the path must end with a list of
        dictionaries that have 'name' and 'id' or end with a single
        dictionary that has 'name' and 'id'.

        :param mydict <dict>:  The dictionary to dive into
        :param path <dict>:  The path used to search

        :returns list:
        """
        mydict = self.convertJSSPathToArray(mydict, path)
        objs = {ii['name']: ii['id'] for ii in mydict}
        return objs

    def convertJSSPathToNamedDicts(self, mydict, path):
        """
        Dig into a JSS Query Result and returns an array of dictionaries
        with the JSS object names as keys and the rest of the object as the
        value. It's just like convertJSSPathToNamedIds but it doesn't
        throw away any data.

        For this function to work the path must end with a list of
        dictionaries that have 'name' and 'id' or end with a single
        dictionary that has 'name' and 'id'.

        :param mydict <dict>:  The dictionary to dive into
        :param path <dict>:  The path used to search

        :returns list:
        """
        mydict = self.convertJSSPathToArray(mydict, path)
        objs = {}
        for item in mydict:
            objs[item['name']] = item
            del(item['name'])
        return objs

    def getNamedDicts(self, endpoint):
        """
        Queries the JSS server and retrieves Objects indexed by name.

        :param endpoint <str>:  API "search all" endpoint (e.g. "policies")

        :returns dict:
        """

        if endpoint not in self.base_search_paths:
            raise APIError(f"{endpoint} is not a valid endpoint")
        search_path = self.base_search_paths[endpoint]
        mydict = self.get(search_path[0])
        objs = self.convertJSSPathToNamedDicts(mydict, search_path[1:])
        if endpoint == "categories":
            objs['No category assigned'] = {'id': -1}
        return objs

    def getNamedIds(self, endpoint):
        """
        Queries the JSS server and retrieves Objects indexed by name.

        :param endpoint <str>:  API "search all" endpoint (e.g. "policies")

        :returns dict:
        """

        if endpoint not in self.base_search_paths:
            raise APIError(f"{endpoint} is not a valid endpoint")
        search_path = self.base_search_paths[endpoint]
        mydict = self.get(search_path[0])
        objs = self.convertJSSPathToNamedIds(mydict, search_path[1:])
        if endpoint == "categories":
            objs['No category assigned'] = -1
        return objs

    def getAllNamedDicts(self):
        """
        Queries the JSS server and retrieves all Objects indexed by name.
        These aren't recursive queries, they are mostly names and ids.

        :returns dict:
        """
        all_endpoints = {}
        for endpoint in self.base_search_paths:
            all_endpoints[endpoint] = self.getNamedDicts(endpoint)
        return all_endpoints

    def __del__(self):
        self.log.debug("closing session")
        self.session.close()

#pylint: disable=too-few-public-methods, abstract-method
class _DummyTag:
    """
    Minimal mock implementation of bs4.element.Tag (only has text attribute)

    >>> eg = _DummyTag('some text')
    >>> eg.text
    'some text'
    """
    def __init__(self, text):
        self.text = text


class JSSErrorParser(html.parser.HTMLParser):
    """
    Minimal mock implementation of bs4.BeautifulSoup()

    >>> [t.text for t in JSSErrorParser(html).find_all('p')]
    ['Unauthorized', 'The request requires user authentication',
     'You can get technical details here. {...}']
    """
    def __init__(self, _html):
        super().__init__()
        self._data = {}
        if _html:
            self.feed(_html)

    def find_all(self, tag):
        """
        Minimal mock implemetation of BeautifulSoup(html).find_all(tag)

        :param tag <str>:   html tag
        :returns <list>:    list of _DummyTags
        """
        return self._data.get(tag, [])

    #pylint: disable=attribute-defined-outside-init
    def handle_data(self, data):
        """
        override HTMLParser().handle_data()
            (automatically called during HTMLParser.feed())
        creates _DummyTag with text attribute from data
        """
        self._dummytag = _DummyTag(data)

    def handle_endtag(self, tag):
        """
        override HTMLParser().handle_endtag()
            (automatically called during HTMLParser.feed())
        add _DummyTag object to dictionary based on tag
        """
        # only create new list if one doesn't already exist
        self._data.setdefault(tag, [])
        self._data[tag].append(self._dummytag)


def parse_html_error(error):
    """
    Get meaningful error information from JSS Error response HTML

    :param html <str>:  JSS HTML error text
    :returns <list>:    list of meaningful error strings
    """
    if not error:
        return []
    try:
        soup = BeautifulSoup(error, features="html.parser")
    except NameError:
        # was unable to import BeautifulSoup
        soup = JSSErrorParser(error)
    # e.g.: ['Unauthorized', 'The request requires user authentication',
    #        'You can get technical details here. (...)']
    # NOTE: get first two <p> tags from HTML error response
    #       3rd <p> is always 'You can get technical details here...'
    return [t.text for t in soup.find_all('p')][0:2]

    def upload(self, endpoint, path, name=None, mime_type=None):
        """
        Upload files to JSS

        :param endpoint <str>:  JSS fileuploads endpoint (e.g. "policies/id/0")
        :param path <str>:      Path to file

        Optional:
        :param name <str>:      Name of file (requires extension)
        :param mime_type <str>: MIME type (e.g. 'image/png')

        if unspecified, MIME type will attempt to be calculated via `file`

        :returns None:
        """
        url = f"{self.url}/fileuploads/{endpoint}"
        path = pathlib.Path(path)
        self.log.debug(f"uploading: {url!r}: {path}")

        if not path.exists():
            raise FileNotFoundError(path)
        # determine filename (if unspecified)
        name = name or path.name()

        # NOTE: JSS requires filename extension (or upload will fail)
        if not path.suffix:
            raise Error(f"missing file extension: {path}")

        # determine mime-type of file (if unspecified)
        mime_type = mime_type or file_mime_type(path)

        with open(path, 'rb') as f:
            # Example of posted data:
            # {'name': ('example.png',
            #           <_io.BufferedReader name="./example.png">,
            #           'image/png')}
            files = {'name': (name, f, mime_type)}
            self.log.debug(f"files: {files}")
            response = self.session.post(url, files=files)

        if not response.ok:
            raise APIError(response)

def file_mime_type(path):
    """
    Uses `/usr/bin/file` to determine mime-type (requires Developer Tools)

    :param path <str>:  Path to file
    :returns str:       content type of file
    """
    cmd = ['/usr/bin/file', '-b', '--mime-type', path]
    return subprocess.check_output(cmd).rstrip()
