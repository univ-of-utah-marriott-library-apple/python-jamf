# -*- coding: utf-8 -*-
#pylint: disable=relative-beyond-top-level, missing-function-docstring
#pylint: disable=missing-class-docstring, missing-module-docstring, invalid-name

"""
test_records
Test the Jamf object classes
"""

import unittest

from .. import records
from . import data
from .MockAPI import MockAPI, MockAPIError


class TestListToDict(unittest.TestCase):

    def setUp(self):
        self.c = records.Categories()
        self.c.session = MockAPI()

    def test_list_to_dict(self):
        lst = data.Data.categories['categories']['category']
        expected = data.Data.categories_expected
        result = self.c.list_to_dict(lst)
        self.assertEqual(expected, result)


# Advanced Computer Searches
class TestComputerSearches(unittest.TestCase):

    def setUp(self):
        self.c = records.ComputerSearches()
        self.c.session = MockAPI()

    def test_computer_searches_get(self):
        expected = data.Data.computer_searches_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_computer_search(self):
        expected = data.Data.computer_search_expected
        result = self.c.get('1')
        self.assertEqual(expected, result)

    def test_computer_search_post(self):
        expected = {'id': '1'}
        dta = data.Data.computer_search_expected
        result = self.c.post('1', dta)
        self.assertEqual(expected, result)

    def test_computer_search_put_by_name(self):
        expected = {'id': '1'}
        record = data.Data.computer_search_expected
        result = self.c.put('Advanced', record)
        self.assertEqual(expected, result)

    def test_computer_search_post_by_name(self):
        expected = {'id': '1'}
        dta = data.Data.computer_search_expected
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
        expected = data.Data.categories_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_category(self):
        expected = data.Data.category_by_id_expected
        result = self.c.get('1')
        self.assertEqual(expected, result)

    def test_category_put(self):
        expected = {'id': '1'}
        record = data.Data.category_by_id_expected
        result = self.c.put('1', record)
        self.assertEqual(expected, result)

    def test_category_put_bad_id(self):
        record = data.Data.category_by_id_expected
        self.assertRaises(MockAPIError, self.c.put, '3', record)

    def test_category_put_name(self):
        record = data.Data.category_by_id_expected
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
        expected = data.Data.computer_groups_expected
        result = self.c.get()
        self.assertEqual(expected, result)

    def test_single_computer_group(self):
        expected = sorted(data.Data.computer_group_by_id_expected)
        result = sorted(self.c.get('21'))
        self.assertEqual(expected, result)

    def test_members(self):
        expected = data.Data.members_expected
        result = self.c.members(data.Data.computer_group_by_id_expected)
        self.assertEqual(expected, result)
