# -*- coding: utf-8 -*-
#pylint: disable=missing-class-docstring, invalid-name
#pylint: disable=relative-beyond-top-level, missing-function-docstring
#pylint: disable=unused-argument, no-else-return, no-self-use

"""
Mock JSS API for testing Jamf object classes
"""

"""
This is incredibly ugly code, ass evidenced by the plethora of pylint
disables above. I should be shot. But it's ugly to do an ugly job.
"""
import logging

# local imports
from . import data #pylint disable:=relative-beyond-top-level

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
            'categories': data.Data.categories,
            'categories/id/1': data.Data.category_by_id,
            'categories/name/TEST': data.Data.category_by_name,
            'computer_groups': data.Data.computer_groups,
            'computer_groups/id/21': data.Data.computer_group_by_id,
            'advanced_computer_searches': data.Data.computer_searches,
            'advanced_computer_searches/id/1': data.Data.computer_search,
            'advanced_computer_searches/name/1': data.Data.computer_search,
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
                    f"Operation not supported {record} {val}"
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
