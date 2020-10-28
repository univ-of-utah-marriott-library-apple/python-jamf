# -*- coding: utf-8 -*-

"""
JSS Categories
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.1.0"

import logging
from .api import API


class Singleton(type):
    _instances = {}

    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class Category:
    _instances = {}

    def __new__(cls, jssid, name):
        """
        returns existing category if one has been instantiated
        """
        jssid = int(jssid)
        if jssid not in cls._instances:
            cls._instances[jssid] = super(Category, cls).__new__(cls)
        return cls._instances[jssid]

    def __init__(self, jssid, name):
        self.id = int(jssid)
        self.name = name

    def __eq__(self, x):
        if isinstance(x, Category):
            return self is x
            # return self.name == x.name and self.id == x.id
        elif isinstance(x, int):
            return self.id == x
        elif isinstance(x, str):
            if x.isdigit() or x == '-1':
                return self.id == int(x)
            else:
                return self.name == x
        elif isinstance(x, dict):
            jssid = int(x.get('id', -1))
            return self.name == x.get('name') and self.id == jssid
        else:
            raise TypeError(f"can't test equality of {x!r}")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id}, {self.name!r})"


class CategoriesIterator:
    def __init__(self, categories):
        self._categories = categories
        self._ids = categories.ids()
        self._index = 0

    def __next__(self):
        if self._index < (len(self._ids)):
            if self._index < len(self._ids):
                id = self._ids[self._index]
                result = self._categories.categoryWithId(id)
            self._index += 1
            return result
        # End of Iteration
        raise StopIteration


class Categories(metaclass=Singleton):

    _categories = {-1: Category('-1', 'No category assigned')}

    def __init__(self, api=None):
        self.log = logging.getLogger(f"{__name__}.Categories")
        self._categories = self.__class__._categories
        self.api = api or API()
        self.data = {}
        self._jssids = {v.id: v for v in self._categories.values()}
        self._names = {v.name: v for v in self._categories.values()}

    def __contains__(self, x):
        return True if self.find(x) else False

    def names(self):
        if not self.data:
            self.refresh()
        return [x for x in self._names.keys()]

    def ids(self):
        if not self.data:
            self.refresh()
        return [x for x in self._jssids.keys()]

    def categoryWithId(self, x):
        if not self.data:
            self.refresh()
        return self._jssids.get(x)

    def categoryWithName(self, x):
        if not self.data:
            self.refresh()
        return self._names.get(x)

    def refresh(self):
        orig_size = int(self.data.get('size', 0))
        self.data = self.api.get('categories')['categories']
        updated_size = int(self.data['size'])
        if orig_size != updated_size:
            for d in self.data['category']:
                c = Category(d['id'], d['name'])
                self._categories.setdefault(int(d['id']), c)
                self._names.setdefault(c.name, c)
                self._jssids.setdefault(c.id, c)

    def find(self, x):
        if not self.data:
            self.refresh()
        if isinstance(x, int):
            # check for category id
            result = self._jssids.get(x)
        elif isinstance(x, str):
            try:
                result = self._jssids.get(int(x))
            except ValueError:
                result = self._names.get(x)
        elif isinstance(x, dict):
            keys = ('id', 'jssid', 'name', 'packageGroupID')
            try:
                key = [k for k in x.keys() if k in keys][0]
            except IndexError:
                result = None
            else:
                if key in ('id', 'jssid', 'packageGroupID'):
                    result = self._jssids.get(int(x[key]))
                elif key == 'name':
                    result = self._names.get(key)
        elif isinstance(x, Category):
            result = x
        else:
            raise TypeError(f"can't look for {type(x)}")
        return result

    def __iter__(self):
        return CategoriesIterator(self)


def categories(name='', exclude=()):
    """
    Get JSS Categories

    :param name  <str>:      name in category['name']
    :param exclude  <iter>:  category['name'] not in exclude

    :returns:  list of dicts: [{'id': jssid, 'name': name}, ...]
    """
    # exclude specified categories by full name
    included = [c for c in Categories() if c.name not in exclude]
    # NOTE: empty string ('') always in all other strings
    return [c for c in included if name in c.name]
