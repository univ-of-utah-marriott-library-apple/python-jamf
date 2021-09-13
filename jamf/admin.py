# -*- coding: utf-8 -*-

"""
Tools for interacting with Jamf Admin (the undocumented Jamf API)

See https://apple.lib.utah.edu/reverse-engineering-jamf-admin/
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.3.0"

import re
import os
import sys
import glob
import json
import time
import pprint
import shutil
import urllib
import hashlib
import logging
import pathlib
import requests
import subprocess
from xml.etree import ElementTree as et

from . import api
from . import config
from . import convert
from . import package
from . import records

# GLOBALS
logger = logging.getLogger(__name__)

class Error(Exception):
    pass


class UploadError(Error):
    pass


class DuplicatePackageError(Error):
    pass


class MissingPackageError(Error):
    pass


class TimeoutError(Error):
    pass


class Singleton(type):
    """
    Use single instance of class
    """
    _instances = {}
    def __call__(cls, *a, **kw):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*a, **kw)
        return cls._instances[cls]


class JamfAdmin(metaclass=Singleton):
    """
    Class for uploading/updating packages in Jamf Admin.app
    """
    def __init__(self,
                 config_path=None,
                 hostname=None,
                 username=None,
                 password=None,
                 prompt=True):
        """
        :param hostname <str>:  JSS hostname (e.g. 'your.jss.domain')
        :param auth <tuple>:    JSS authentication credentials (user, passwd)
        :param path <str>:      path to jamf.config.PREFERENCES file
        :param port <int>:      JSS port (default: 8443)
        """
        self.log = logging.getLogger(f"{__name__}.JamfAdmin")

        conf = config.Config(config_path=config_path,
                             hostname=hostname,
                             username=username,
                             password=password,
                             prompt=prompt)
        hostname = hostname or conf.hostname
        username = username or conf.username
        password = password or conf.password

        if not hostname and not username and not password:
            print("No jamf hostname or credentials could be found.")
            exit(1)

        self.hostname = hostname

        self.session = requests.Session()
        self.session.auth = (username, password)
        self.data = self.authenticate()
        self.categories = records.Categories()
        for share in self.fileservers:
            if share['master'] == 'true':
                self.fileshare = FileShare.fromJXML(share)
                break
        self._packages = None
        self._refreshed = {'packages': False}

    def __del__(self):
        for pkg in self.packages:
            if not pkg.path.exists():
                self.log.info(f"removing deleted package record: {pkg.name}")
                self.remove(pkg)

    @property
    def packages(self):
        """
        :returns: list of packages from Jamf Admin
        """
        _trigger = self._refreshed['packages']
        if not self._packages or _trigger:
            if not self.fileshare.mounted:
                self.fileshare.mount()
            self._refreshed['packages'] = False
            _data = self.data['packages']['package']
            # fix xml_to_dict issues by ensuring sure it's a list
            if isinstance(_data, dict):
                _data = [_data]
            self._packages = PackageList()
            for d in _data:
                try:
                    pkg = Package(d, self.fileshare)
                except FileNotFoundError:
                    self.remove(d['id'])
                else:
                    if pkg in self._packages:
                        err = f"duplicate package: {pkg.jssid}: {pkg.name}"
                        self.log.error(err)
                        self.remove(pkg.jssid)
                    else:
                        self._packages.append(pkg)
        return self._packages

    @property
    def fileservers(self):
        """
        :returns: list of fileservers from Jamf Admin
        """
        _data = self.data['fileservers']['fileserver']
        # fix xml_to_dict issues by making sure we return a list
        return _data if isinstance(_data, list) else [_data]

    @property
    def groups(self):
        """
        :returns: list of groups from Jamf Admin
        """
        _data = self.data['groups']['group']
        # fix xml_to_dict issues by making sure we return a list
        return _data if isinstance(_data, list) else [_data]

    def authenticate(self):
        """
        Authenticate Jamf Admin session
        """
        self.log.debug("authenticating session: %r", self.hostname)
        username, passwd = self.session.auth
        form = {'username': username, 'password': passwd,
                'casperAdminVersion': '', 'skipComputers': 'true'}
        # authenticate session (uses 'JSESSIONID' cookie for future requests)
        response = self.session.post(f"{self.hostname}//casper.jxml", data=form)
        # NOTE: failed requests will still return <Response [200]>
        #       failed requests will only have
        if not response.ok:
            # NOTE: response.ok requires requests.__version__ >= '2.18.4'
            # failed requests will still return <Response [200]>
            raise Error(f"{self.hostname}: authentication failed: {response}")
        # convert xml response to dict
        info = convert.xml_to_dict(response.text)
        # check authentication
        # TO-DO: figure out best way to determine bad authentication
        # NOTE: failed requests will only have 'epoch' and 'response' tags
        #       successful requests will not have 'response' tag
        failure = info['jamfServlet'].get('response')
        if failure:
            raise Error(f"{self.hostname}: authentication failed: {failure}")
        return info['jamfServlet']

    def refresh(self):
        """
        reauthenticate and refresh data
        """
        self.data = self.authenticate()
        self._refreshed = {k:True for k in self._refreshed.keys()}
        return self.data

    def index(self, pkg):
        """
        Not Implemented
        """
        # if not isinstance(pkg, ServerPackage):
        #     raise Error("can't index local package")
        # url = f"{self.url}//packageIndex.jxml"
        raise NotImplementedError()

    def uploaded(self, pkg):
        return self.fileshare.packages in pkg.path.parents

    def upload(self, pkg, verify=True, force=False):
        """
        Upload local package
        """
        if not isinstance(pkg, package.Package):
            raise TypeError(f"invalid package: {pkg!r}")
        # check if package is already uploaded
        if self.uploaded(pkg) and not force:
            raise ValueError(f"package already uploaded: {pkg.name}")
        self.log.info(f"uploading package: {pkg.name}")
        # mount fileshare
        self.fileshare.mount()
        # upload package file
        dest = self.fileshare.packages / pkg.name
        self.log.debug(f"> cp {pkg.path} {dest}")
        subprocess.check_call(['/bin/cp', '-p', pkg.path, dest])
        self.log.debug(f"successfully copied package: {pkg.path}")
        uploaded = package.Package(dest)
        try:
            existing = self.find(uploaded.name)
        except MissingPackageError:
            pass
        else:
            uploaded = existing
        if verify:
            if not self.verify_upload(pkg, uploaded):
                raise UploadError(f"failed to upload package: {pkg.path}")
        return uploaded

    def verify_upload(self, orig, new):
        # verify file copied
        # TO-DO: get size of server file to compare to original (fast)
        # TO-DO: calculate checksums of each (slow)
        self.log.info(f"verifying package upload")
        self.log.warning("upload verification minimally implemented")
        verified = True
        self.log.debug("checking sizes")
        if orig.size != new.size:
            self.log.error("mismatching package sizes")
            verified = False
        return verified

    def add(self, pkg, force=False):
        # create new package entry in the database
        if not isinstance(pkg, package.Package):
            raise ValueError(f"invalid package: {pkg!r}")
        # check if package was already uploaded
        try:
            uploaded = self.find(pkg.name)
        except MissingPackageError:
            # this is what we want to happen
            uploaded = self.upload(pkg)
        else:
            if not force:
                raise DuplicatePackageError(f"package already added: {pkg}")
            self.log.debug(f"forcing upload")
            self.upload(pkg)
            return uploaded

        # get package data form
        form = package_upload_form(pkg)
        form.update({'username': self.session.auth[0],
                     'password': self.session.auth[1]})
        # submit package upload form
        self.log.debug("submitting package form")
        url = f"{self.hostname}//casperAdminAddObject.jxml"
        r = self.session.post(url, data=form)
        # get the ID of the newly created package
        jssid = convert.xml_to_dict(r.text)['jamfServlet']['new_id']
        logger.debug(f"new package ID: {jssid}")
        added = Package.fromPackage(jssid, pkg, self.fileshare)
        self.packages.append(added)
        self.log.info(f"successfully added: {added.name}")
        return added

    def delete(self, pkg):
        if not isinstance(pkg, Package):
            pkg = self.find(pkg.name)
        self.remove(pkg)
        self.packages.remove(pkg)
        if pkg.path.exists():
            pkg.path.unlink()

    def remove(self, x):
        self.log.info(f"removing package record: {x}")
        if isinstance(x, package.Package):
            jssid = self.find(x.name).jssid
        elif isinstance(x, (str, int)):
            jssid = x
        form = {'username': self.session.auth[0],
                'allScriptsMigratedToJSS': 'true',
                'deletedPackageID': jssid}
        self.session.post(f"{self.hostname}//casperAdminSave.jxml", data=form)

    def update(self, pkg, notes=''):
        if not hasattr(pkg, 'jssid'):
            try:
                pkg = self.find(pkg.name)
            except AttributeError:
                raise TypeError(f"invalid package: {pkg!r}")
            except FileNotFoundError:
                raise TypeError(f"package never added: {pkg!r}")

        self.log.info(f"updating package: id: {pkg.jssid}: {pkg.name}")
        form = package_update_form(pkg)
        form.update({'username': self.session.auth[0],
                     'password': self.session.auth[1],
                     'allScriptsMigratedToJSS': 'true'})
        if notes:
            form['packageNotes'] = notes
        self.session.post(f"{self.hostname}//casperAdminSave.jxml", data=form)

    def find(self, name):
        """
        :returns: appropriate package for name
        """
        if isinstance(name, package.Package):
            name = name.name
        for pkg in self.packages:
            if pkg.name == name:
                return pkg
        raise MissingPackageError(f"missing package: {name}")


class PackageList(list):

    @property
    def names(self):
        return [p.name for p in self]

    def __contains__(self, x):
        return x.name in self.names


class Package(package.Package):

    _instances = {}

    @classmethod
    def fromJXML(cls, conf, fileshare):
        """
        Create Package object from JamfAdmin info
        """
        try:
            volume = pathlib.Path(fileshare.path)
        except TypeError:
            fileshare.mount()
            volume = pathlib.Path(fileshare.path)
        path = volume / 'Packages' / conf['filename']
        keys = ('checksum', 'hashValue', 'info', 'notes', 'groupid')
        return cls({k:conf[k] for k in keys if k in conf}, fileshare)

    @classmethod
    def fromPackage(cls, jssid, pkg, fileshare):
        """
        Create ServerPackage object from existing Package object
        """
        data = {'id': jssid, 'filename': pkg.name,
                'checksum': pkg.md5, 'hashValue': pkg.sha512}
        return cls(data, fileshare)

    def __new__(cls, data, fileshare):
        """
        returns existing package if one has been instantiated
        """
        logger = logging.getLogger(__name__)
        # logger.debug(f'data: {data}')
        jssid = int(data['id'])
        if jssid not in cls._instances:
            cls._instances[jssid] = super(Package, cls).__new__(cls)
        return cls._instances[jssid]

    def __init__(self, data, fileshare):
        path =  fileshare.path / 'Packages' / data['filename']
        # if not path.exists():
        #     raise ValueError(f"unable to find package on server: {path}")
        super().__init__(path)
        self.log = logging.getLogger(f"{__name__}.Package")
        self._md5 = data.get('checksum')
        self._sha512 = data.get('hashValue')
        self.jssid = int(data['id'])
        self.category = records.Categories().find(data.get('groupid', '-1'))
        self.notes = data.get('notes', '')
        try:
            self._info = json.loads(data.get('info', '{}'))
        except (json.decoder.JSONDecodeError, TypeError):
            self._info = {}
        try:
            self._min_os_ver = self._info.get('minimum_os')
        except AttributeError:
            pass

    def __eq__(self, x):
        # this significantly speeds up
        return self.name == x.name

    @property
    def info(self):
        _info = super().info
        _info.update({'minimum_os': self.minimum_os})
        return _info


class FileShare:

    @classmethod
    def fromJXML(cls, jxml):
        """
        Use Jamf Admin fileserver info to create new FileShare
        :returns: FileShare object
        """
        protocol = jxml['type']
        # default domain (fallback to ip), raises KeyError if no fallback
        # NOTE: Jamf Admin incorrectly uses domain in 'ip'
        host = jxml.get('domain') or jxml['ip']
        auth = (jxml['adminUsername'], jxml['adminPassword'])
        kwargs = {'share': jxml['share'], 'name': jxml['displayname']}
        return cls(protocol, host, auth, **kwargs)

    def __init__(self, protocol, hostname, auth, name=None, share=''):
        self.log = logging.getLogger(f"{__name__}.FileShare")
        self.log.debug(f"protocol: {protocol!r}")
        self.log.debug(f"hostname: {hostname!r}")
        self.log.debug(f"name: {name!r}")
        self.log.debug(f"share: {share!r}")
        self.protocol = protocol
        self.host = hostname
        self.name = name or hostname
        self.auth = auth
        self.share = share
        self.path = None
        # attempt to find previously mounted volume
        if self.mounted:
            # has side-effect of setting self.path (should be changed)
            self.log.info(f"found previously mounted volume: {self.path}")

    # @property
    # def path(self):
    #     if self._path and not self._path.exists():
    #         self._path = None
    #     if not self._path:

    @property
    def mounted(self):
        """
        Check if fileshare is mounted, and if so, update the path
        :returns: True if fileshare is currently mounted
        """
        # look for
        # e.g. 'remote.file.share.domain/ShareVolume'
        # identifier = os.path.join(self.host, self.share)
        identifier = f"{self.host}/{self.share}"
        for device, path, _ in mounted_volumes():
            if identifier in device:
                # update the path of the file share
                self.path = pathlib.Path(path)
                break
        return True if self.path and self.path.exists() else False

    @property
    def packages(self, automount=True):
        """
        :returns <Path>: absolute path to Packages directory on fileshare
        """
        if automount and not self.mounted:
            self.mount()
        # verify there is actually a path to return
        if not self.path:
            raise Error(f"{self.name}: not mounted")
        return self.path / 'Packages'

    def mount(self, timeout=5):
        """
        Mount the fileshare
        :returns <Path>: mounted volume path
        """
        if self.mounted:
            self.log.warning(f"{self.name}: already mounted")
            return self.path

        self.log.debug(f"mounting: {self.name}", self.name)
        user, passwd = [urllib.parse.quote(s) for s in self.auth]
        url = f"{self.protocol}://{user}:{passwd}@{self.host}/{self.share}"
        self.log.debug(f"> open {url.replace(passwd, '******')}")
        subprocess.check_call(['/usr/bin/open', url])
        self._wait_for_mount(timeout=timeout)
        self.log.info(f"successfully mounted: {self.name}")
        self.log.debug(f"path: {str(self.path)!r}")
        return self.path

    def unmount(self):
        """
        Unmount the fileshare
        """
        if not self.mounted:
            self.log.warning(f"{self.name}: already unmounted")
            return
        self.log.debug(f"unmounting: {self.name}")
        subprocess.check_call(['/sbin/umount', self.path])
        self.path = None
        self.log.info(f"{self.name}: succesfully unmounted")

    def _wait_for_mount(self, timeout=5, poll=1):
        """
        Wait for fileshare to mount
        """
        self.log.debug(f"{self.name}: waiting for mount")
        time.sleep(poll)
        w = poll
        while not self.mounted:
            if w >= timeout:
                self.log.error(f"{self.name}: failed to mount")
                raise TimeoutError(f"timed out after {w} second(s)")
            time.sleep(poll)
            w += poll


def package_upload_form(pkg):
    """
    :returns: form to post for package uploads
    """
    # TO-DO: this will require .mpkg support
    if pkg.path.suffix == '.pkg':
        type_ = 'package'
    else:
        raise ValueError(f"unsupported package type: {pkg.path.suffix!r}")
    # return populated form for package
    return {'type': type_,
            'packageName': pkg.name,
            'packageFileName': pkg.name,
            'adobeInstall': 'false',
            'osInstall': 'false',
            'osInstallerVersion': '',
            'parentPackageID': '-1',
            'checksum': str(pkg.md5),
            'hashType': '1',
            'hashValue': str(pkg.sha512),
            'reboot': 'false', # str(pkg.reboot).lower(),
            'packagePriority': '10'}


def package_update_form(pkg):
    """
    :returns: form to post for package updates
    """
    # TO-DO: this will require .mpkg support
    if pkg.path.suffix == '.pkg':
        format = 'Apple Package'
    else:
        raise ValueError(f"unsupported package type: {pkg.path.suffix!r}")
    try:
        _info = pkg.info
        _info['minimum_os'] = pkg.minimum_os
    except Exception as e:
        _info = {'ERROR': f"failed to dump package info: {e}"}

    try:
        pkginfo = json.dumps(_info, indent=2)
    except Exception as e:
        pkginfo = ''
    try:
        notes = str(pkg.notes)
    except AttributeError:
        notes = ''
    # return populated form template
    return {'packageID': pkg.jssid,
            'packageName': pkg.name,
            'packageFileName': pkg.name,
            'checksum': str(pkg.md5),
            'hashType': '1',
            'hashValue': str(pkg.sha512),
            'packageGroupID': pkg.category.id,
            'packagePriority': '10',
            'packageInfo': pkginfo,
            'packageNotes': notes,
            'packageFormat': format,
            'packageSize': 'n/a',
            'packageRequirements': '',
            'bootVolumeRequired': 'false',
            'fut': 'false',
            'feu': 'false',
            'ifswu': 'false',
            'reboot': 'false',
            'uninstall': 'false',
            'packageRequiredProcessor': 'None',
            'packageSwitchWithPackageID': '-1',
            'selfHealingAction': 'nothing',
            'selfHealingNotify': 'false',
            'adobeInstall': 'false',
            'adobeInstallerImage': 'false',
            'adobeUpdater': 'false',
            'osInstall': 'false',
            'osInstallerVersion': '',
            'packageSerialNumber': '',
            'parentPackageID': '-1',
            'basePath': '',
            'ignoreConflictingProcesses': 'false',
            'suppressFromDock': 'false',
            'suppressEULA': 'false',
            'suppressRegistration': 'false',
            'suppressUpdates': 'false',
            'installLanguage': 'en_US'}


# def package_info(pkg):
#     """
#     :returns <str>:  information about the package
#     """
#     info = (f"identifier: {pkg.identifier}\n"
#             f"version: {pkg.version}\n"
#             f"install-location: {pkg.location}\n"
#             "Contents:")
#     keys = ('path', 'CFBundleIdentifier', 'CFBundleShortVersionString',
#             'CFBundleVersion')
#     for app in pkg.apps:
#         i = "\n".join([f"    {k}: {app[k]}" for k in keys])
#         info += f"\n  {app['name']}:\n{i}"
#     return info


# def package_notes(path):
#     path = pathlib.Path(path)
#     *name, ver, date, author = path.stem.split('_')
#     return f"{date}, {author.upper()}"


def mounted_volumes():
    """
    Uses `/sbin/mount` to get information about mounted file systems
    :returns: list of tuples for each mounted file system
                e.g. [(device, path, types), ...]
    """
    logger = logging.getLogger(__name__)
    # e.g. '/dev/disk1s1 on / (apfs, local, journaled)'
    #  -> ('/dev/disk1s1', '/', 'apfs, local, journaled')
    r = re.compile(r'^(.+) on (.+) \((.+)\)$')
    logger.debug(f"checking mounted volumes")
    out = subprocess.check_output(['/sbin/mount']).decode()
    return [re.match(r, x).groups() for x in out.splitlines()]


def package_checksums(path, bufsize=8192):
    """
    calculate md5 and sha512 digests of path
    :param path:        path to file
    :param bufsize:     block size buffer to read (default: 4096)
    :returns:           (md5.hexdigest(), sha512.hexdigest())
    """
    raise NotImplementedError("use jamf.package.calculate_checksums instead")
    logger = logging.getLogger(__name__)
    logger.debug("calculating checksums: %r", path)
    md5 = hashlib.md5()
    sha512 = hashlib.sha512()
    with open(path, 'rb') as f:
        while True:
            data = f.read(bufsize)
            if not data:
                break
            md5.update(data)
            sha512.update(data)
    return (md5.hexdigest(), sha512.hexdigest())


def package_index(path, cleanup=True):
    """
    package indexing payload form data for requests.post
    requests.post(url, data=package_index('/path/to/example.pkg'))

    :param  path  <str>:    path of .pkg file
    :returns  <list>:       key/value tuple pairs
    """
    logger = logging.getLogger(__name__)
    # expand package boms (see `man pkgutil` for more info)
    logger.debug(f"> pkgutil --bom {path}")
    boms = subprocess.check_output(['/usr/sbin/pkgutil', '--bom', path])
    # process all boms included in package
    boms = [x for x in boms.splitlines() if x]
    if not boms:
        raise RuntimeError(f"no bill of materials found: {path}")
    # see `man lsbom` for formatting
    logger.debug(f"> lsbom -p fMguTsc '%s'", "', '".join(boms))
    cmd = ['/usr/bin/lsbom', '-p', 'fMguTsc'] + boms
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    if p.returncode != 0 or not out:
        raise RuntimeError(err)

    if cleanup:
        # cleanup all bom files created in /tmp by `pkgutil`
        for path in glob.glob(f"/tmp/{path}.boms*"):
            shutil.rmtree(path)

    form = []
    keys = ('path', 'mode', 'owner', 'group', 'date', 'size', 'checksum')
    for line in out.splitlines():
        # list of values per line (converted from byte string)
        values = [x.decode().strip() for x in line.split(b'\t')]

        # NOTE: Jamf Admin removes '.' from beginning of path
        # modify path to exclude leading '.'
        # values[0] = values[0][1:]

        # NOTE: Jamf Admin does not submit package root in its index
        # create entry for every non-root entry in bom (i.e. '.' > 1 == False)
        if len(values[0]) > 1:
            # remove double space between month and single digit dates
            # (e.g. 'Sun Jun  9 01:00:00 2019' -> 'Sun Jun 9 01:00:00 2019')
            values[4] = values[4].replace('  ', ' ')
            form.extend([z for z in zip(keys, values)])
    return form
