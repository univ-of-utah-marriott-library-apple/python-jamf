# -*- coding: utf-8 -*-

"""
tests for jamf.config
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "0.1.1"

import copy
import shutil
import logging
import pathlib
import plistlib
import unittest
import datetime as dt

from jamf import config

# temporary files created with tests
LOCATION = pathlib.Path(__file__).parent
TMPDIR = LOCATION / 'tmp' / 'config'
# DATA = LOCATION / 'data' / 'config'

DEFAULT_PREFERENCES = config.PREFERENCES
PREFERENCES = TMPDIR / 'jamf.config.test.plist'

def setUpModule():
    """
    single time setup for entire module.
    """
    TMPDIR.mkdir(mode=0o755, parents=True, exist_ok=True)


def tearDownModule():
    """
    single time cleanup for entire module.
    """
    shutil.rmtree(str(TMPDIR), ignore_errors=True)


class ConfigPathTests(unittest.TestCase):
    """
    config.PREFERENCES and path keyword argument tests
    """
    @classmethod
    def setUpClass(cls):
        """
        verify default config.PREFERENCES before any tests are run and
        save modified path (if any) to be restored later
        """
        cls._saved_prefs = config.PREFERENCES
        config.PREFERENCES = DEFAULT_PREFERENCES

    @classmethod
    def tearDownClass(cls):
        """
        restore any changes to config.PREFERENCES after all tests are finished
        """
        config.PREFERENCES = cls._saved_prefs

    def setUp(self):
        self.altpath = pathlib.Path('/tmp/jamf.config.test.alt.plist').resolve()

    def tearDown(self):
        """
        restore default config.PREFERENCES after each test
        """
        config.PREFERENCES = DEFAULT_PREFERENCES

    def test_modified_default_with_path_kwarg(self):
        """
        test specified path overrides config.PREFERENCES
        """
        test = config.Config(path=self.altpath)
        self.assertEqual(test.path, self.altpath)
        self.assertNotEqual(test.path, config.PREFERENCES)

    def test_modified_global_as_None_without_path(self):
        """
        test config.PREFERENCES = None and path=None raises TypeError
        """
        config.PREFERENCES = None
        with self.assertRaises(TypeError):
            test = config.Config()

    def test_default_global_with_path_as_None(self):
        """
        test config.PREFERENCES is used when path=None
        """
        test = config.Config(path=None)
        self.assertEqual(test.path, config.PREFERENCES)

    def test_default_global_with_path_kwarg(self):
        """
        test default config.PREFERENCES with path=None uses global
        """
        test = config.Config(path=self.altpath)
        self.assertEqual(test.path, self.altpath)
        self.assertNotEqual(test.path, config.PREFERENCES)

    def test_modified_global_without_kwarg(self):
        """
        test missing path kwarg uses modified config.PREFERENCES
        """
        config.PREFERENCES = self.altpath
        test = config.Config()
        self.assertEqual(test.path, config.PREFERENCES)

    def test_modified_global_with_None(self):
        """
        test explicit path kwarg as None uses modified config.PREFERENCES
        """
        config.PREFERENCES = self.altpath
        test = config.Config(path=None)
        self.assertEqual(test.path, config.PREFERENCES)


class BaseTestCase(unittest.TestCase):
    """
    Generic TestCase
    """
    @classmethod
    def setUpClass(cls):
        """
        single time setup for class.
        """
        pass

    @classmethod
    def tearDownClass(cls):
        """
        single time teardown for class.
        """
        pass

    def setUp(self):
        """
        create config with cusomt path for each test
        """
        self.config = config.Config(path=PREFERENCES)

    def tearDown(self):
        """
        teardown after each test
        """
        pass

    def test_path_attribute(self):
        """
        test config object has path attribute
        """
        self.assertTrue(self.config.path)

    def test_path_value(self):
        """
        test config.path is expected
        """
        self.assertEqual(self.config.path, PREFERENCES)


class ConfigTestCase(unittest.TestCase):

    def setUp(self):
        self.path = TMPDIR / 'jamf.config.test.plist'
        self.config = config.Config(path=self.path)

    def test_load_attribute(self):
        self.assertTrue(hasattr(self.config, 'load'))

    def test_save_attribute(self):
        self.assertTrue(hasattr(self.config, 'save'))

    def test_get_attribute(self):
        self.assertTrue(hasattr(self.config, 'get'))

    def test_set_attribute(self):
        self.assertTrue(hasattr(self.config, 'set'))

    def test_remove_attribute(self):
        self.assertTrue(hasattr(self.config, 'remove'))

    def test_reset_attribute(self):
        self.assertTrue(hasattr(self.config, 'reset'))


# @unittest.skip
class TestNewConfig(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """
        make sure the file is removed before performing tests
        """
        if PREFERENCES.exists():
            PREFERENCES.unlink()

    @classmethod
    def tearDownClass(cls):
        """
        single time teardown for class.
        """
        pass

    def setUp(self):
        """
        verify no existing config file exists before each test
        """
        super().setUp()
        self.assertNoFile(self.config.path)

    def tearDown(self):
        """
        remove created config file after each test (if created)
        """
        if self.config.path.exists():
            self.config.path.unlink()

    def assertNoFile(self, path):
        self.assertFalse(path.exists())

    def test_modified_config_does_not_create_file(self):
        """
        test modifying config does not create file
        """
        self.config.set('test', 'value')
        self.assertNoFile(self.config.path)

    def test_set_and_get_string(self):
        """
        test set and get key/value pair as {'string': 'string'}
        """
        expected = 'string'
        self.config.set('string', expected)
        result = self.config.get('string')
        self.assertEqual(expected, result)

    def test_set_and_get_date(self):
        """
        test set and get key/value pair as {'date': dt.datetime.now()}
        """
        expected = dt.datetime.now()
        self.config.set('date', expected)
        result = self.config.get('date')
        self.assertEqual(expected, result)

    def test_set_and_get_bool_true(self):
        """
        test set and get key/value pair as {'true': False}
        """
        expected = True
        self.config.set('true', expected)
        result = self.config.get('true')
        self.assertEqual(expected, result)

    def test_set_and_get_bool_false(self):
        """
        test set and get key/value pair as {'false': False}
        """
        expected = False
        self.config.set('false', expected)
        result = self.config.get('false')
        self.assertEqual(expected, result)

    def test_set_None(self):
        """
        test set value as None raises ValueError
        """
        with self.assertRaises(ValueError):
            self.config.set('test', None)

    def test_get_missing(self):
        """
        test get missing key raises KeyError
        """
        with self.assertRaises(KeyError):
            self.config.get('missing')


class TestSaveConfig(BaseTestCase):

    def setUp(self):
        super().setUp()
        if self.config.path.exists():
            self.config.path.unlink()
        self.data = {'string': 'string',
                     'integer': 1,
                     'true': True,
                     'false': False,
                     'date': dt.datetime(2020, 1, 13, 13, 13, 13),
                     'dict': {'key': 'value', 'one': 1},
                     'list': [1, 2, 3],
                     'data': b'binary-data',
                     'float': 0.01,
                     'nesteddict': {'d1': {'key': 'value'},
                                    'd2': {'key': 'value2'}},
                     'nestedlist': [[1, 2, 3], [4, 5, 6]],
                     'dictoflists': {'one': [1, 2, 3], 'two': [4, 5, 6]},
                     'listofdicts': [{'one': 1}, {'two': 2}]}
        self.config.data = copy.deepcopy(self.data)

    def test_save_creates_file(self):
        """
        test file is created when saved
        """
        self.assertFalse(self.config.path.exists())
        self.config.save()
        self.assertTrue(self.config.path.exists())

    def test_save_data(self):
        """
        Test expected data is saved
        """
        self.config.save()
        expected = self.data
        # read data from disk (raise FileNotFoundError if missing)
        with open(self.config.path, 'rb') as f:
            result = plistlib.load(f)
        self.assertDictEqual(expected, result)

    def test_bad_save_doesnt_modify_file(self):
        """
        Test file is not modified when saving an invalid value
        """
        expected = self.data
        # save data
        self.config.save()
        # misconfigure the data (None is not supported by plists)
        self.config.data.update({'None': None})
        # attempt to save the misconfigured data (raises TypeError)
        with self.assertRaises(TypeError):
            self.config.save()
        # manually reload data from disk (raises expatError if corrupt)
        with open(self.config.path, 'rb') as f:
            result = plistlib.load(f)
        # verify nothing is wrong
        self.assertDictEqual(expected, result)

    def test_bad_save_doesnt_create_file(self):
        """
        Test no new file is created when saving an invalid value
        """
        self.assertFalse(self.config.path.exists())
        # misconfigure the data (None is not supported by plists)
        self.config.data.update({'None': None})
        # attempt to save the misconfigured data (raises TypeError)
        with self.assertRaises(TypeError):
            self.config.save()
        # verify the config.path was not created
        self.assertFalse(self.config.path.exists())


class TestConfigLoading(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.data = {'string': 'string',
                     'integer': 1,
                     'true': True,
                     'false': False,
                     'date': dt.datetime(2020, 1, 13, 13, 13, 13),
                     'dict': {'key': 'value', 'one': 1},
                     'list': [1, 2, 3],
                     'data': b'binary-data',
                     'float': 0.01,
                     'nesteddict': {'d1': {'key': 'value'},
                                    'd2': {'key': 'value2'}},
                     'nestedlist': [[1, 2, 3], [4, 5, 6]],
                     'dictoflists': {'one': [1, 2, 3], 'two': [4, 5, 6]},
                     'listofdicts': [{'one': 1}, {'two': 2}]}
        # manually create file before each test
        with open(self.config.path, 'wb') as f:
            plistlib.dump(self.data, f)

    def tearDown(self):
        try:
            self.config.path.unlink()
        except FileNotFoundError:
            pass

    def test_load_data(self):
        """
        Test expected data is loaded
        """
        expected = self.data
        result = self.config.load()
        self.assertDictEqual(expected, result)

    def test_load_missing_file(self):
        """
        Test FileNotFoundError raised when loading a missing file
        """
        self.config.path.unlink()
        with self.assertRaises(FileNotFoundError):
            self.config.load()

    def test_load_corrupt_file(self):
        """
        Test CorruptedConfigError raised when loading a corrupted config
        """
        self.data.update({'None': None})
        # intentionally corrupt the file
        with self.assertRaises(TypeError):
            with open(self.config.path, 'wb') as f:
                plistlib.dump(self.data, f)
        # verify
        with self.assertRaises(config.CorruptedConfigError):
            self.config.load()

    def test_load_empty_file(self):
        """
        Test plistlib.InvalidFileException raised when loading an empty config
        """
        self.config.path.unlink()
        self.config.path.touch()
        with self.assertRaises(plistlib.InvalidFileException):
            self.config.load()


class SecureConfigTestCase(ConfigTestCase):

    def setUp(self):
        self.path = TMPDIR / 'jamf.config.secure.test.plist'
        self.config = config.SecureConfig(path=self.path)
        self.transpose = config.transposition(config.MAGIC)

    def test_credentials_attribute(self):
        self.assertTrue(hasattr(self.config, 'credentials'))

    def test_something(self):
        expected = ('username', 'password')
        if self.path.exists():
            self.path.unlink()
        self.config.credentials('test', expected)
        result = self.config.credentials('test')
        self.assertEqual(expected, result)


class TestSaveSecureConfig(TestSaveConfig):

    def setUp(self):
        self.path = TMPDIR / 'jamf.config.secure.test.plist'
        self.config = config.SecureConfig(path=self.path)
        super().setUp()


class TestSecureConfigLoading(TestConfigLoading):

    def setUp(self):
        self.path = TMPDIR / 'jamf.config.secure.test.plist'
        self.config = config.SecureConfig(path=self.path)
        super().setUp()


class CredentialsTest(unittest.TestCase):

    def setUp(self):
        self.key = 'secret'
        self.callback = config.transposition(self.key)
        self.credentials = config.Credentials({}, callback=self.callback)

    def test_retrieve_missing(self):
        with self.assertRaises(KeyError):
            self.credentials.retrieve('missing')

    def test_register_and_retrieve(self):
        expected = 'value'
        self.credentials.register('key', expected)
        # print(self.credentials.data)
        # bplist = self.callback(self.credentials.data['key'])
        # print(plistlib.loads(bplist))
        result = self.credentials.retrieve('key')
        self.assertEqual(expected, result)

    def test_register_None(self):
        # with self.assertRaises(ValueError):
        #     self.credentials.register('key', None)
        expected = None
        self.credentials.register('key', expected)
        result = self.credentials.retrieve('key')
        # print(self.credentials.data)
        # bplist = self.callback(self.credentials.data['key'])
        # print(bplist)
        # print(plistlib.loads(bplist))
        self.assertEqual(expected, result)

    def test_register_Credentials(self):
        c = config.Credentials({'test': 'value'}, callback=self.callback)
        expected = c.data
        self.credentials.register('key', c)
        result = self.credentials.retrieve('key')
        # print(result)
        self.assertEqual(expected, result)

    def test_something(self):
        c = config.Credentials({'test': 'value'}, callback=self.callback)
        expected = c.data
        self.credentials.register('key', c)
        result = self.credentials.retrieve('key')
        # print(result)
        self.assertEqual(expected, result)


class TranspositionTest(unittest.TestCase):

    def setUp(self):
        self.key = 'test'
        self.secret = 'secret information'

    def assertMirroredTransposition(self, func, secret):
        """
        assert the same func can be used to both encrypt and decrypt the secret
        """
        expected = secret
        transposed = func(secret)
        result = func(transposed)
        self.assertEqual(expected, result)

    def assertEncryptedTransposition(self, func, secret):
        """
        assert the same func can be used to both encrypt and decrypt the secret
        """
        expected = (bytes(secret, encoding='utf-8')
                    if isinstance(secret, str) else secret)
        # encrypt the secret
        encrypted = func(secret)
        # verify the encrypted secret != original secret
        self.assertNotEqual(encrypted, expected)
        e = 'transposition returned {0!r}: bytes expected'
        self.assertIsInstance(encrypted, bytes, msg=e.format(encrypted))
        # decrypt the encrypted secret using the same function
        result = func(encrypted)
        self.assertIsInstance(result, bytes, msg=e.format(result))
        # make sure the decoded result == original secret
        self.assertEqual(expected, result)

    def test_transposition(self):
        """
        test transposition
        """
        transpose = config.transposition(b'test')
        self.assertEqual(transpose(b'test'), b'\x00\x00\x00\x00')

    def test_reverse_transposition(self):
        """
        test reverse transposition
        """
        transpose = config.transposition(b'test')
        self.assertEqual(transpose(b'\x00\x00\x00\x00'), b'test')

    def test_tuple_key(self):
        """
        test key as tuple
        """
        key = tuple([ord(x) for x in self.key])
        func = config.transposition(key)
        self.assertEncryptedTransposition(func, self.secret)

    def test_list_key(self):
        """
        test key as list
        """
        key = [ord(x) for x in self.key]
        func = config.transposition(key)
        self.assertEncryptedTransposition(func, self.secret)

    def test_str_key(self):
        """
        test key as string
        """
        key = self.key
        func = config.transposition(key)
        self.assertEncryptedTransposition(func, self.secret)

    def test_bytes_key(self):
        """
        test key as bytes
        """
        key = bytes(self.key, encoding='utf-8')
        func = config.transposition(key)
        self.assertEncryptedTransposition(func, self.secret)

    def test_mixed_key_fails(self):
        """
        test iterable of different types raises ValueError
        """
        with self.assertRaises(ValueError):
            f = config.transposition((7, 't'))

    def test_default_transposition(self):
        key = self.key
        self.assertMirroredTransposition(lambda x: x, self.secret)


if __name__ == '__main__':
    fmt = '%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s'
    logging.basicConfig(level=logging.FATAL, format=fmt)
    unittest.main(verbosity=1)
