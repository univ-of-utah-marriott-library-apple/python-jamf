# -*- coding: utf-8 -*-

"""
Unittests for jamf.package
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.0.1"

# import os
import pprint
import shutil
import pathlib
import unittest

from .. import package
from .. import api
from .. import category

# location for temporary files created with tests
LOCATION = pathlib.Path(__file__).parent
TMPDIR = LOCATION / 'tmp' / 'package'
DATA = LOCATION / 'data' / 'package'

def setUpModule():
    """
    One time setup for entire module.
    If exception is raised, no tests in entire module are run.
    """
    # OPTIONAL
    TMPDIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    package.TMPDIR = TMPDIR / 'edu.utah.mlib.package.tests'


def tearDownModule():
    """
    One time cleanup for entire module.
    """
    # OPTIONAL
    shutil.rmtree(TMPDIR, ignore_errors=True)


class BaseTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.tmpdir = TMPDIR

    def tearDown(self):
        pass


class TestPackageInit(BaseTestCase):
    # pass
    # def setUp(self):
    #     super().setUp()
    #     self.path = DATA / 'pkgs' / 'edu.utah.mlib.package.test.pkg'

    def test_missing_path_fails(self):
        """
        test FileNotFoundError is raised when given a bad path
        """
        path = pathlib.Path('/does/not/exist')
        if not path.exists():
            with self.assertRaises(FileNotFoundError):
                package.Package(path)

    def test_existing_pkg(self):
        """
        test initialization succeeds
        """
        path = DATA / 'pkgs' / 'edu.utah.mlib.package.test.pkg'
        if path.exists():
            pkg = package.Package(path)


class PackageTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.path = DATA / 'pkgs' / 'edu.utah.mlib.package.test.pkg'
        self.pkg = package.Package(self.path)

    def test_sha512_checksum(self):
        """
        test package sha512 checksum hexdigest
        """
        # `openssl sha512 /path/to/edu.utah.mlib.package.test.pkg`
        expected = ('137aa99516b7c9e4d9e8e11e7fffbeb706f380886ff'
                    '390da0b786053993903acc1190e3c27c1cde054f351'
                    '5369e449f33be15c287aeba116d2e9f1a8dc2f5ff9')
        result = self.pkg.sha512
        self.assertEqual(expected, result)

    def test_md5_checksum(self):
        """
        test package md5 checksum hexdigest
        """
        # `openssl md5 /path/to/edu.utah.mlib.package.test.pkg`
        expected = 'a37ae984343b3bbcedb7316e0f3cb349'
        result = self.pkg.md5
        self.assertEqual(expected, result)

    def test_path(self):
        """
        test path is expected
        """
        expected = self.path
        result = self.pkg.path
        self.assertEqual(expected, result)

    def test_name(self):
        """
        test package name is basename of file
        """
        expected = self.path.name
        result = self.pkg.name
        self.assertEqual(expected, result)

    def test_info_keys(self):
        """
        test all package info keys are accounted for
        """
        expected = ['contents', 'name', 'path', 'pkginfo']
        result = sorted([str(x) for x in self.pkg.info.keys()])
        self.assertEqual(expected, result)

    def test_identifier(self):
        """
        test package identifier
        """
        expected = 'test.package'
        result = self.pkg.identifier
        self.assertEqual(expected, result)

    def test_version(self):
        """
        test package version
        """
        expected = '1.0.1'
        result = self.pkg.version
        self.assertEqual(expected, result)

    def test_location(self):
        """
        test package install-location
        """
        expected = '/Applications/Test Package'
        result = self.pkg.location
        self.assertEqual(expected, result)

    def test_apps(self):
        """
        test package app
        """
        expected = [{'CFBundleIdentifier': 'edu.utah.mlib.package.test',
                     'CFBundleShortVersionString': '1.0.0',
                     'CFBundleVersion': '100',
                     'LSMinimumSystemVersion': '10.7.5',
                     'name': 'package.app',
                     'path': '/Applications/Test Package/package.app'}]
        result = self.pkg.apps
        self.assertEqual(expected, result)

    def test_pkginfo(self):
        """
        test package information
        """
        expected = {'auth': 'root',
                    'format-version': '2',
                    'generator-version': 'InstallCmds-681 (18G2022)',
                    'identifier': 'test.package',
                    'install-location': '/Applications/Test Package',
                    'overwrite-permissions': 'true',
                    'postinstall-action': 'none',
                    'relocatable': 'false',
                    'version': '1.0.1'}
        result = self.pkg.info['pkginfo']
        self.assertEqual(expected, result)

    def test_size(self):
        """
        test package size
        """
        expected = 2573
        result = self.pkg.size
        self.assertEqual(expected, result)

    def test_expand(self):
        """
        test package expansion
        """
        path = self.pkg.expand()
        self.assertTrue(path.exists())

    def test_cleanup(self):
        """
        test package expansion cleanup
        """
        path = self.pkg.expand()
        del(self.pkg)
        self.assertFalse(path.exists())

    def test_pkg_as_str(self):
        """
        test package as string
        """
        expected = str(self.pkg.path)
        self.assertTrue(str(self.pkg) == expected)



if __name__ == '__main__':
    unittest.main(verbosity=1)
