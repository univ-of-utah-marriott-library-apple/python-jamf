# -*- coding: utf-8 -*-
#pylint: disable=relative-beyond-top-level, missing-function-docstring
#pylint: disable=missing-class-docstring, missing-module-docstring, invalid-name

"""
test_records
Test the Jamf object classes
"""

import unittest
import logging

from jamf import records

LOGLEVEL = logging.DEBUG

class Error(Exception):
    pass


class MockAPIError(Error):

    def __init__(self, method, message): #pylint: disable=super-init-not-called
        self.method = method
        self.message = message

    def __getattr__(self, attr):
        """
        missing attributes fallback on response
        """
        return getattr(self.message, attr)

    def __str__(self):
        return f"API: {self.method} failed: {self.message}"


class Singleton(type):
    _instances = {}
    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class MockAPI(metaclass=Singleton):
    """
    Class for making api calls to JSS

    This is where we start our mockery
    """

    def __init__(self, config=None, hostname=None, auth=None):
        """
        Create requests.Session with JSS address and authentication

        :param config <str>:    Path to file containing config. If it starts
                                with '~' character we pass it to expanduser.
        :param hostname <str>:  hostname of server
        :param auth <(str, str):    (username, password) for server
        """
        self.log = logging.getLogger(f"{__name__}.API")
        self.log.setLevel(LOGLEVEL)
        self.url = f"{hostname}/JSSResource"
        self.auth = auth
        self.put_by_name = True
        self.post_by_name = True
        self.delete_by_name = True
        # for errors
        self.response = "failed"

    def get(self, endpoint, raw=False):
        """
        Get JSS information

        :param endpoint <str>:  API endpoint (e.g. "policies/id/1")
        :param raw <bool>:      return requests.Response obj  (skip errors)

        :returns <dict|requests.Response>:
        """
        return {
            'categories': Data.categories,
            'categories/id/1': Data.category_by_id,
            'categories/name/TEST': Data.category_by_name,
            'computergroups': Data.computer_groups,
            'computergroups/id/21': Data.computer_group_by_id,
            'advancedcomputersearches': Data.computer_searches,
            'advancedcomputersearches/id/1': Data.computer_search,
            'advancedcomputer_searches/name/1': Data.computer_search,
        }[endpoint]

    def put(self, record, dta, raw=False):
        r = record.split('/')
        if len(r) != 3 or r[1] not in ('id', 'name'):
            raise MockAPIError('put', f"bad request: {record}")
        try:
            val = int(record)
        except ValueError:
            if self.post_by_name:
                return {'id': '1'}
            else:
                raise MockAPIError(
                    'put',
                    f"Operation not supported {record}"
                )
        return {'id': '1'}

    def delete(self, record, raw=False):
        r = record.split('/')
        if len(r) != 3 or r[1] not in ('id', 'name'):
            raise MockAPIError('delete', f"bad request: {record}")
        try:
            val = int(r[2])
        except ValueError:
            if self.delete_by_name:
                return {'id': '1'}
            else:
                raise MockAPIError(
                    'delete',
                    f"Operation not supported {record}"
                )
        if val == 1:
            return {'id': '1'}
        else:
            raise MockAPIError('delete', 'No matching record: {record}')

    def post(self, record, dta, raw=False):
        r = record.split('/')
        if r[1] not in ('id', 'name'):
            raise MockAPIError('post', f"bad record: {record}")
        try:
            val = int(r[2])
        except ValueError:
            if self.delete_by_name:
                return {'id': '1'}
            else:
                raise MockAPIError('post', "not passed id")
        if val != 1:
            raise MockAPIError('post', "no record with that id")
        return {'id': '1'}


class Data():
    """
    Class to hold the fake data for MockAPI to feed to test_records
    and test_records to compare what it gets.
    """

    computer_searches = {
        'advanced_computer_searches': {
            'advanced_computer_search': [
                {'id': '1', 'name': 'Advanced'},
                {'id': '2', 'name': 'fudge'},
                {'id': '3', 'name': 'bizz'},
            ],
            'size': '1',
        }
    }

    computer_searches_expected = {'1': 'Advanced', '2': 'fudge', '3': 'bizz'}

    computer_search = {
        'advanced_computer_search': {
            'id': '1',
            'name': 'Advanced',
            'view_as': 'Standard Web Page',
            'sort_1': 'string',
            'sort_2': 'string',
            'sort_3': 'string',
            'criteria': {
                'size': '1',
                'criterion':
                {
                    'name': 'Last Inventory Update',
                    'priority': '0',
                    'and_or': 'and',
                    'search_type': 'more than x days ago',
                    'value': '7',
                    'opening_paren': 'false',
                    'closing_paren': 'false'
                }
            },
            'display_fields': {'size': '1', 'display_field': {'name': 'IP Address'}},
            'computers': {
                'size': '2',
                'computer':  [
                    {
                        'id': '1',
                        'name': 'Joes iMac',
                        'udid': '55900BDC-347C-58B1-D249-F32244B11D30',
                        'Computer_Name': 'Joes iMac'
                    },
                    {
                        'id': '22',
                        'name': 'Petes iMac',
                        'udid': '55900BDC-347C-58B1-D249-F322C2B11D30',
                        'Computer_Name': 'Petes iMac'
                    }
                ]
            },
            'site': {'id': '-1', 'name': 'None'}
        }
    }

    computer_search_expected = {
        'id': '1',
        'name': 'Advanced',
        'view_as': 'Standard Web Page',
        'sort_1': 'string',
        'sort_2': 'string',
        'sort_3': 'string',
        'criteria': {
            'size': '1',
            'criterion': {
                'name': 'Last Inventory Update',
                'priority': '0',
                'and_or': 'and',
                'search_type': 'more than x days ago',
                'value': '7',
                'opening_paren': 'false',
                'closing_paren': 'false'
            }
        },
        'display_fields': {'size': '1', 'display_field': {'name': 'IP Address'}},
        'computers': {
            'size': '2',
            'computer':  [
                {
                    'id': '1',
                    'name': 'Joes iMac',
                    'udid': '55900BDC-347C-58B1-D249-F32244B11D30',
                    'Computer_Name': 'Joes iMac'
                },
                {
                    'id': '22',
                    'name': 'Petes iMac',
                    'udid': '55900BDC-347C-58B1-D249-F322C2B11D30',
                    'Computer_Name': 'Petes iMac'
                }
            ]
        },
        'site': {'id': '-1', 'name': 'None'}
    }

    computer_groups = {
        'computer_groups': {
            'size': '25',
            'computer_group': [
                {'id': '80', 'name': 'All 10.13', 'is_smart': 'true'},
                {'id': '79', 'name': 'All 10.14', 'is_smart': 'true'},
                {'id': '77', 'name': 'All 10.15', 'is_smart': 'true'},
                {'id': '1', 'name': 'All Managed Clients', 'is_smart': 'true'},
                {'id': '58', 'name': 'Azure Token', 'is_smart': 'true'},
                {'id': '63', 'name': 'BrokenAudit', 'is_smart': 'true'},
                {'id': '62', 'name': 'Build Mini', 'is_smart': 'true'},
                {'id': '36', 'name': 'Hardware - MacBook', 'is_smart': 'true'},
                {'id': '35', 'name': 'Hardware - MacBook Air', 'is_smart': 'true'},
                {'id': '34', 'name': 'Hardware - MacBook Pro', 'is_smart': 'true'},
                {'id': '87', 'name': 'has Privileges.app', 'is_smart': 'true'},
                {'id': '54', 'name': 'Installed - Adobe CC', 'is_smart': 'true'},
                {'id': '74', 'name': 'Installed - BlueCoat4.10.3', 'is_smart': 'true'},
                {'id': '46', 'name': 'Installed - Cisco Webex', 'is_smart': 'true'},
                {'id': '44', 'name': 'Installed - Firefox', 'is_smart': 'true'},
                {'id': '21', 'name': 'Installed - GarageBand', 'is_smart': 'true'},
                {'id': '28', 'name': 'Installed - Google Chrome', 'is_smart': 'true'},
                {'id': '30', 'name': 'Installed - Skim', 'is_smart': 'true'},
                {'id': '45', 'name': 'Installed - Spotify', 'is_smart': 'true'},
                {'id': '27', 'name': 'Installed - The Unarchiver', 'is_smart': 'true'},
                {'id': '31', 'name': 'Installed - VLC', 'is_smart': 'true'},
                {'id': '42', 'name': 'Compliance - Manual Exclusion', 'is_smart': 'false'},
                {'id': '38', 'name': 'Test - Compliance Test', 'is_smart': 'false'},
                {'id': '37', 'name': 'Test - WiFi Computers', 'is_smart': 'false'},
                {'id': '8', 'name': 'Test Computers', 'is_smart': 'false'}
            ]
        }
    }

    computer_groups_expected = {
        '80': {'name': 'All 10.13', 'is_smart': 'true'},
        '79': {'name': 'All 10.14', 'is_smart': 'true'},
        '77': {'name': 'All 10.15', 'is_smart': 'true'},
        '1': {'name': 'All Managed Clients', 'is_smart': 'true'},
        '58': {'name': 'Azure Token', 'is_smart': 'true'},
        '63': {'name': 'BrokenAudit', 'is_smart': 'true'},
        '62': {'name': 'Build Mini', 'is_smart': 'true'},
        '36': {'name': 'Hardware - MacBook', 'is_smart': 'true'},
        '35': {'name': 'Hardware - MacBook Air', 'is_smart': 'true'},
        '34': {'name': 'Hardware - MacBook Pro', 'is_smart': 'true'},
        '87': {'name': 'has Privileges.app', 'is_smart': 'true'},
        '54': {'name': 'Installed - Adobe CC', 'is_smart': 'true'},
        '74': {'name': 'Installed - BlueCoat4.10.3', 'is_smart': 'true'},
        '46': {'name': 'Installed - Cisco Webex', 'is_smart': 'true'},
        '44': {'name': 'Installed - Firefox', 'is_smart': 'true'},
        '21': {'name': 'Installed - GarageBand', 'is_smart': 'true'},
        '28': {'name': 'Installed - Google Chrome', 'is_smart': 'true'},
        '30': {'name': 'Installed - Skim', 'is_smart': 'true'},
        '45': {'name': 'Installed - Spotify', 'is_smart': 'true'},
        '27': {'name': 'Installed - The Unarchiver', 'is_smart': 'true'},
        '31': {'name': 'Installed - VLC', 'is_smart': 'true'},
        '42': {'name': 'Compliance - Manual Exclusion', 'is_smart': 'false'},
        '38': {'name': 'Test - Compliance Test', 'is_smart': 'false'},
        '37': {'name': 'Test - WiFi Computers', 'is_smart': 'false'},
        '8': {'name': 'Test Computers', 'is_smart': 'false'}
    }

    # note: the serial numbers and mac addresses are from a random
    # generator so don't mean anything beyond conforming to the right
    # length and format.

    computer_group_by_id = {
        'computer_group': {
            'id': '21',
            'name': 'Installed - GarageBand',
            'is_smart': 'true',
            'site': {'id': '-1', 'name': 'None'},
            'criteria': {
                'size': '1',
                'criterion': {
                    'name': 'Application Title',
                    'priority': '0',
                    'and_or': 'and',
                    'search_type': 'is',
                    'value': 'Pages.app',
                    'opening_paren': 'false',
                    'closing_paren': 'false'
                }
            },
            'computers': {
                'size': '4',
                'computer': [
                    {
                        'id': '120',
                        'name': 'C0265B896WZ9',
                        'mac_address': '98:C0:48:D4:83:F7',
                        'alt_mac_address': '83:23:23:C0:55:83',
                        'serial_number': 'C0265B896WZ9'
                    },
                    {
                        'id': '123',
                        'name': 'C024B2BADVYD',
                        'mac_address': '67:68:55:C0:67:67',
                        'alt_mac_address': '83:83:98:23:F7:68',
                        'serial_number': 'C024B2BADVYD'
                    },
                    {
                        'id': '125',
                        'name': 'C02DZVCT6U00',
                        'mac_address': 'E7:55:83:E7:83:E7',
                        'alt_mac_address': 'C7:B4:C7:67:F7:98',
                        'serial_number': 'C02DZVCT6U00'
                    },
                    {
                        'id': '256',
                        'name': 'C02DA56FXCAD',
                        'mac_address': 'A3:A4:67:55:55:98',
                        'alt_mac_address': 'A4:C0:00:A3:83:7A',
                        'serial_number': 'C02Z18BVLVDC'
                    }
                ]
            }
        }
    }

    members_expected = {
        '120': {
            'name': 'C0265B896WZ9',
            'mac_address': '98:C0:48:D4:83:F7',
            'alt_mac_address': '83:23:23:C0:55:83',
            'serial_number': 'C0265B896WZ9'
        },
        '123': {
            'name': 'C024B2BADVYD',
            'mac_address': '67:68:55:C0:67:67',
            'alt_mac_address': '83:83:98:23:F7:68',
            'serial_number': 'C024B2BADVYD'
        },
        '125': {
            'name': 'C02DZVCT6U00',
            'mac_address': 'E7:55:83:E7:83:E7',
            'alt_mac_address': 'C7:B4:C7:67:F7:98',
            'serial_number': 'C02DZVCT6U00'
        },
        '256': {
            'name': 'C02DA56FXCAD',
            'mac_address': 'A3:A4:67:55:55:98',
            'alt_mac_address': 'A4:C0:00:A3:83:7A',
            'serial_number': 'C02Z18BVLVDC'
        }
    }

    computer_group_by_id_expected = {
        'id': '21',
        'name': 'Installed - GarageBand',
        'is_smart': 'true',
        'site': {'id': '-1', 'name': 'None'},
        'criteria': {
            'size': '1',
            'criterion': {
                'name': 'Application Title',
                'priority': '0',
                'and_or': 'and',
                'search_type': 'is',
                'value': 'Pages.app',
                'opening_paren': 'false',
                'closing_paren': 'false'
            }
        },
        'computers': {
            'size': '4',
            'computer': [
                {
                    'id': '120',
                    'name': 'C0265B896WZ9',
                    'mac_address': '98:C0:48:D4:83:F7',
                    'alt_mac_address': '83:23:23:C0:55:83',
                    'serial_number': 'C0265B896WZ9'
                },
                {
                    'id': '123',
                    'name': 'C024B2BADVYD',
                    'mac_address': '67:68:55:C0:67:67',
                    'alt_mac_address': '83:83:98:23:F7:68',
                    'serial_number': 'C024B2BADVYD'
                },
                {
                    'id': '125',
                    'name': 'C02DZVCT6U00',
                    'mac_address': 'E7:55:83:E7:83:E7',
                    'alt_mac_address': 'C7:B4:C7:67:F7:98',
                    'serial_number': 'C02DZVCT6U00'},
                {
                    'id': '256',
                    'name': 'C02DA56FXCAD',
                    'mac_address': 'A3:A4:67:55:55:98',
                    'alt_mac_address': 'A4:C0:00:A3:83:7A',
                    'serial_number': 'C02Z18BVLVDC'
                }
            ]
        }
    }

    categories = {
        'categories': {
            'size': '16',
            'category': [
                {'id': '1', 'name': 'Applic'},
                {'id': '2', 'name': 'CIS'},
                {'id': '3', 'name': 'DEP-Onboarding'},
                {'id': '15', 'name': 'Deprecated/Superceded'},
                {'id': '16', 'name': 'Developer'},
                {'id': '5', 'name': 'End User Experience'},
                {'id': '6', 'name': 'First Aid'},
                {'id': '11', 'name': 'How To Guides'},
                {'id': '12', 'name': 'Intranet Shortcuts'},
                {'id': '13', 'name': 'Maintenance'},
                {'id': '7', 'name': 'Microsoft'},
                {'id': '8', 'name': 'Networking'},
                {'id': '17', 'name': 'OS Upgrades'},
                {'id': '9', 'name': 'Security'},
                {'id': '10', 'name': 'TEST'},
                {'id': '14', 'name': 'User Guides'}
            ]
        }
    }

    categories_expected = {
        '1': 'Applic',
        '2': 'CIS',
        '3': 'DEP-Onboarding',
        '15': 'Deprecated/Superceded',
        '16': 'Developer',
        '5': 'End User Experience',
        '6': 'First Aid',
        '11': 'How To Guides',
        '12': 'Intranet Shortcuts',
        '13': 'Maintenance',
        '7': 'Microsoft',
        '8': 'Networking',
        '17': 'OS Upgrades',
        '9': 'Security',
        '10': 'TEST',
        '14': 'User Guides'
    }

    category_by_id = {
        'category': {'id': '1', 'name': 'Applications', 'priority': '2'}
    }

    category_by_id_expected = {'id': '1', 'name': 'Applications', 'priority': '2'}

    category_by_name = {
        'category': {'id': '10', 'name': 'TEST', 'priority': '9'}
    }

    category_by_name_expected = {'id': '10', 'name': 'TEST', 'priority': '9'}

    extension_attributes = {
        'computer_extension_attributes': {
            'size': '2',
            'computer_extension_attribute': [
                {
                    'id': '1',
                    'name': 'silliness',
                    'enabled': 'true'
                },
                {
                    'id': '11',
                    'name': 'extended',
                    'enabled': 'true'
                }
            ]
        }
    }


class TestListToDict(unittest.TestCase):

    def setUp(self):
        self.c = records.Categories()
        self.c.session = MockAPI()

    def test_list_to_dict(self):
        lst = Data.categories['categories']['category']
        expected = Data.categories_expected
        result = self.c.list_to_dict(lst)
        self.assertEqual(expected, result)


# Advanced Computer Searches
class TestComputerSearches(unittest.TestCase):

    def setUp(self):
        self.c = records.ComputerSearches()
        self.c.session = MockAPI()

    def test_computer_searches_get(self):
        expected = Data.computer_searches_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_computer_search(self):
        expected = Data.computer_search_expected
        result = self.c.get('1')
        self.assertEqual(expected, result)

    def test_computer_search_post(self):
        expected = {'id': '1'}
        dta = Data.computer_search_expected
        result = self.c.post('1', dta)
        self.assertEqual(expected, result)

    def test_computer_search_put_by_name(self):
        expected = {'id': '1'}
        record = Data.computer_search_expected
        result = self.c.put('Advanced', record)
        self.assertEqual(expected, result)

    def test_computer_search_post_by_name(self):
        expected = {'id': '1'}
        dta = Data.computer_search_expected
        result = self.c.post('Advanced', dta)
        self.assertEqual(expected, result)

    def test_computer_search_delete_by_name(self):
        expected = {'id': '1'}
        result = self.c.delete('Advanced')
        self.assertEqual(expected, result)

class TestCategories(unittest.TestCase):

    def setUp(self):
        self.c = records.Categories()
        self.c.session = MockAPI()

    def test_categories_get(self):
        expected = Data.categories_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_category(self):
        expected = Data.category_by_id_expected
        result = self.c.get('1')
        self.assertEqual(expected, result)

    def test_category_put(self):
        expected = {'id': '1'}
        record = Data.category_by_id_expected
        result = self.c.put('1', record)
        self.assertEqual(expected, result)

    def test_category_put_bad_id(self):
        record = Data.category_by_id_expected
        self.assertRaises(MockAPIError, self.c.put, '3', record)

    def test_category_put_name(self):
        record = Data.category_by_id_expected
        self.assertRaises(records.JamfError, self.c.put, 'Gonzo', record)

    def test_category_delete(self):
        expected = {'id': '1'}
        result = self.c.delete('1')
        self.assertEqual(expected, result)

    def test_category_delete_bad_id(self):
        self.assertRaises(MockAPIError, self.c.delete, '3')

    def test_category_delete_name(self):
        self.assertRaises(records.JamfError, self.c.delete, 'Ernie')


class TestComputerGroups(unittest.TestCase):

    def setUp(self):
        self.c = records.ComputerGroups()
        self.c.session = MockAPI()

    def test_computer_groups_get(self):
        expected = Data.computer_groups_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_computer_group(self):
        expected = sorted(Data.computer_group_by_id_expected)
        result = sorted(self.c.get('21'))
        self.assertEqual(expected, result)

    def test_members(self):
        expected = Data.members_expected
        result = self.c.members(Data.computer_group_by_id_expected)
        self.assertEqual(expected, result)

if __name__ == '__main__':
    unittest.main(verbosity=1)