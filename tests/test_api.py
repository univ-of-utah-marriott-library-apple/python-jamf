# -*- coding: utf-8 -*-
#pylint: disable=relative-beyond-top-level, too-few-public-methods, unused-argument
#pylint: disable=missing-class-docstring, missing-function-docstring
"""
Tests for JSS API
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.0.0"

import unittest
import logging

from .. import api


class MockResponse:

    def __init__(self, data, path=None):
        class MockRequest:
            pass
        self.request = MockRequest()
        self.return_code = data['code']
        self.request.method = data.get('method', 'GET')
        self.url = data.get('url', 'http://mock.url')
        if path:
            with open(path, 'rb') as fptr:
                self.text = fptr.read()
        else:
            self.text = data.get('text', '')

    @property
    def ok(self): #pylint: disable=invalid-name
        return 200 <= self.return_code <= 400


class MockSession:

    def __init__(self, response=None):
        self.headers = {}
        self.response = response

    def get(self, url, *args, **kwargs):
        return self.response

    def post(self, url, *args, **kwargs):
        return self.response

    def put(self, url, *args, **kwargs):
        return self.response

    def close(self):
        pass


class BaseTestCase(unittest.TestCase):
    pass


class TestAPI(unittest.TestCase):

    def setUp(self):
        response = MockResponse({'text': '<>', 'code': 200})
        self.api = api.API()
        self.api.session = MockSession(response)


UNAUTHORIZED = ('<html>\n'
                '<head>\n'
                '<title>Status page</title>\n'
                '</head>\n'
                '<body style="font-family: sans-serif;">\n'
                '<p style="font-size: 1.2em;font-weight: bold;margin: 1em '
                '0px;">Unauthorized</p>\n'
                '<p>The request requires user authentication</p>\n'
                '<p>You can get technical details '
                '<a href="http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.'
                'html#sec10.4.2">here</a>.<br>\n'
                'Please continue your visit at our '
                '<a href="/">home page</a>.\n'
                '</p>\n'
                '</body>\n'
                '</html>\n')


class TestAPIError(unittest.TestCase):

    def setUp(self):
        self.html = UNAUTHORIZED
        self.response = MockResponse({'text': self.html,
                                      'code': 401,
                                      'method': 'GET'})

    def test_empty_response_text(self):
        """
        Test APIError still works if response.text == ''
        """
        expected = 'failed'
        self.response.text = ''
        err = api.APIError(self.response)
        result = err.message
        self.assertEqual(expected, result)
        with self.assertRaises(api.APIError):
            raise err

    def test_none_response_text(self):
        """
        Test APIError still works if response.text == None
        """
        expected = 'failed'
        self.response.text = None
        err = api.APIError(self.response)
        result = err.message
        self.assertEqual(expected, result)
        with self.assertRaises(api.APIError):
            raise err

    def test_unauthorized_response_text(self):
        """
        Test APIError parses response.text
        """
        err = api.APIError(self.response)
        expected = "Unauthorized: The request requires user authentication"
        result = str(err)
        self.assertTrue(result.endswith(expected))

    def test_attribute_fallback(self):
        """
        Test missing attributes fall back to request.Response
        """
        err = api.APIError(self.response)
        self.assertEqual(401, err.return_code)

    def test_attribute_fallback_missing(self):
        """
        Test non-request.Response attributes still raise AttributeError
        """
        err = api.APIError(self.response)
        with self.assertRaises(AttributeError):
            unused = err.undefined_attribute #pylint: disable=unused-variable


class TestParseError(unittest.TestCase):

    def test_parse_empty_string(self):
        """
        test parse_html_error return empty list on ''
        """
        expected = []
        result = api.parse_html_error('')
        self.assertEqual(expected, result)

    def test_parse_none(self):
        """
        test parse_html_error return empty list on None
        """
        expected = []
        result = api.parse_html_error(None)
        self.assertEqual(expected, result)

    def test_parse_unauthorized(self):
        """
        test parse_html_error parses results
        """
        expected = ['Unauthorized', 'The request requires user authentication']
        result = api.parse_html_error(UNAUTHORIZED)
        self.assertEqual(expected, result)


class TestJSSErrorParser(unittest.TestCase):

    def test_parse_unauthorized(self):
        """
        test parse_html_error parses results
        """
        expected = ['Unauthorized', 'The request requires user authentication']
        parsed = api.JSSErrorParser(UNAUTHORIZED)
        result = [t.text for t in parsed.find_all('p')][0:2]
        self.assertEqual(expected, result)

    def test_parse_empty_string(self):
        expected = []
        result = api.JSSErrorParser('').find_all('p')
        self.assertEqual(expected, result)

    def test_parse_none(self):
        expected = []
        result = api.JSSErrorParser(None).find_all('p')
        self.assertEqual(expected, result)


if __name__ == '__main__':
    FMT = '%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=FMT)
    unittest.main(verbosity=1)
