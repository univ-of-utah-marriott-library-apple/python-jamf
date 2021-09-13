# -*- coding: utf-8 -*-

"""
JAMF Packages
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.1.3"

# import re
import os
import shutil
import hashlib
import logging
import pathlib
import plistlib
import subprocess
import datetime as dt
from distutils.version import StrictVersion, LooseVersion
from xml.etree import ElementTree as ET

from .records import Categories
from . import config

# GLOBALS
TMPDIR = os.environ.get('TMPDIR', '/tmp')
TMPDIR = pathlib.Path(TMPDIR).resolve() / 'edu.utah.mlib.packages'
VERSIONKEY = 'edu.utah.mlib.jctl:LSMinimumSystemVersion'
# RECEIPTS = pathlib.Path('/var/db/receipts').resolve()
# logger = logging.getLogger(__name__)


class Error(Exception):
    pass


class InvalidPackageError(Error):
    pass


class Manager:
    """
    Package Manager
    """
    def __init__(self, api, admin):
        self.log = logging.getLogger(f"{__name__}.Manager")
        self.admin = admin
        # self.repos = repos
        self.api = api
        self._packages = {'jss': []}
        # self._uploaded = {}

    def find_name(self, name):
        """
        :param name:        name of package
        :returns Package:
        """
        raise NotImplementedError()
        #if not name and not jssid and not path:
        #    raise ValueError("must specify name, path, or ID")

    def _find(self, key, value):
        """
        :param key:        search key
        :param value:      value of search
        :returns Package:
        """
        raise NotImplementedError()

    def new_packages(self, repo, **kwargs):
        """
        :param repo <Repo>:  package.Repo object
        :returns <list>:     list of new packages
        """
        names = [r['name'] for r in self.jss_packages(**kwargs)]
        return [pkg for pkg in repo.packages if pkg.name not in names]

    def jss_packages(self, refresh=False):
        """
        get all packages from JSS
        """
        if refresh or not self._packages['jss']:
            pkgs = self.api.get('packages')['packages']['package']
            self._packages['jss'] = pkgs
        return self._packages['jss']

    def archive(self, pkg, path=None):
        """
        Archive package
        """
        raise NotImplementedError()

    def upload_package(self, pkg):
        """
        Upload package to JDS and create new database entry
        """
        return self.admin.add(pkg)

    def upload_packages(self, pkgs):
        """
        Upload package to JDS and create new database entry
        """
        return [self.admin.add(pkg) for pkg in pkgs]

    def update_packages(self, pkgs):
        """
        Upload package to JDS and create new database entry
        """
        return [self.admin.add(pkg) for pkg in pkgs]

    def cleanup(self):
        """
        cleanup
        """
        raise NotImplementedError()


class BasePackage:

    def __init__(self, name):
        self.name = name
        self.info = {'pkginfo': {'install-location': None,
                                 'identifier': None,
                                 'version': None},
                     'name': name,
                     'path': None,
                     'contents': []}

    @property
    def identifier(self):
        _id = self.info['pkginfo']['identifier']
        if not _id:
            raise ValueError("unable to determine identifier")
        return _id

    @property
    def version(self):
        _version = self.info['pkginfo']['version']
        if not _version:
            # attempt to figure out the version from the name?
            raise ValueError("unable to determine version")
        return _version

    def __eq__(self, x):
        """self.__eq__(x, y): x == y"""
        if isinstance(x, str):
            return x == self.name
        elif isinstance(x, BasePackage):
            self.info == x.info
        else:
            raise TypeError(f"unable to compare {x!r}: {type(x)}")

    def __lt__(self, x):
        """self.__lt__(x, y): x < y"""
        if isinstance(x, str):
            return self.name < x
        elif isinstance(x, BasePackage):
            if not self.identifier == x.identifier:
                raise ValueError(f"{self.identifer} != {x.identifier}")
            # if versions are identical, check the name
            return (self.version < x.version
                   if not self.version == x.version else self.name < x.name)
        else:
            raise TypeError(f"unable to compare {x!r}: {type(x)}")

    def __gt__(self, x):
        """self.__gt__(x, y): x > y"""
        if isinstance(x, str):
            return self.name > x
        elif isinstance(x, BasePackage):
            if not self.identifier == x.identifier:
                raise ValueError(f"{self.identifer} != {x.identifier}")
            # if versions are identical, check the name
            return (self.version > x.version
                   if not self.version == x.version else self.name > x.name)
        else:
            raise TypeError(f"unable to compare {x!r}: {type(x)}")

    def __le__(self, x):
        """self.__le__(x, y): x <= y"""
        return self == x or self < x

    def __ge__(self, x):
        """self.__ge__(x, y): x >= y"""
        return self == x or self < x

    def __repr__(self):
        # <cls>('/path/to/package') e.g. Package('/tmp/example.pkg')
        return f"{self.__class__.__name__}('{self.name}')"

    def __str__(self):
        return self.name


class App:

    def __init__(self, data):
        self.identifier = data['CFBundleIdentifier']
        self.version = data['CFBundleShortVersionString']
        self.bundle_version = data['CFBundleVersion']
        self.minimum_os = data.get('LSMinimumSystemVersion')

    def values(self):
        keys = ('identifier', 'version', 'bundle_version', 'minimum_os')
        return tuple(getattr(self, k) for k in keys)

    def items(self):
        return {k:v for k, v in self.__dict__.items() if not k.startswith('_')}

    def __iter__(self):
        yield self.values()


class Package:

    def __init__(self, path):
        self.log = logging.getLogger(f"{__name__}.Package")
        self.path = pathlib.Path(path)
        self.expanded = None
        if not self.path.exists():
            self.log.error(f"no such file: '{self.path}'")
            raise FileNotFoundError(self.path)
        self.name = self.path.name
        self._apps = []
        self._version = None
        self._md5 = None
        self._sha512 = None
        self._stat = None
        self._created = None
        self._info = None
        self._min_os_ver = None

    @property
    def md5(self):
        """
        calculate md5 digest on demand
        """
        if not self._md5:
            self._calculate_checksums()
        return self._md5

    @property
    def sha512(self):
        """
        calculate sha512 digest on demand
        """
        if not self._sha512:
            self._calculate_checksums()
        return self._sha512

    @property
    def size(self):
        """
        :returns: size of package in bytes
        """
        if not self._stat:
            self._stat = self.path.stat()
        return self._stat.st_size

    @property
    def created(self):
        if not self._created:
            self._created = dt.datetime.fromtimestamp(self.stat.st_ctime)
        return self._created

    @property
    def version(self):
        """
        :returns: package version
        """
        if not self._version:
            v = self.info['pkginfo']['version']
            if v:
                try:
                    # NOTE: StrictVersion(None) and StrictVersion('')
                    #       both initialize, but raise AttributeError if
                    #       accessed (may cause issues later)
                    self._version = StrictVersion(v)
                except ValueError:
                    self._version = LooseVersion(v)
            else:
                raise ValueError(f"version: {v!r}")
        return self._version

    @property
    def identifier(self):
        """
        :returns: package bundle identifier
        """
        return self.info['pkginfo']['identifier']

    @property
    def location(self):
        """
        :returns: package install-location
        """
        return self.info['pkginfo']['install-location']

    @property
    def apps(self):
        """
        :returns: list of apps that will be installed by the package
        """
        if not self._apps:
            for bundle in self.info['contents']:
                if bundle['name'].endswith('.app'):
                    os = {'LSMinimumSystemVersion': str(self.minimum_os)}
                    bundle.update(os)
                    self._apps.append(bundle)
        return self._apps

    @property
    def minimum_os(self):
        """
        :returns: minimum version of macOS that will install the package
        """
        if not self._min_os_ver:
            # check for our metadata flag
            try:
                _version = xattr('-p', VERSIONKEY, self.path)
            except subprocess.CalledProcessError:
                pass
            else:
                # exception wasn't raised
                if _version:
                    self._min_os_ver = StrictVersion(_version)
                else:
                    # remove empty metadata key
                    xattr('-d', VERSIONKEY, self.path)
        # if there's no metadata, we have to check the plist in the payload
        if not self._min_os_ver:
            # missing metadata key
            expanded = self.expand()
            _pkg = package_information(path=expanded/'PackageInfo')
            versions = []
            for bundle in _pkg['bundles']:
                payload = expanded / 'Payload'
                # very expensive for large packages (especially over network)
                try:
                    plist = extract_info_plist(payload, bundle['path'])
                except subprocess.CalledProcessError:
                    pass
                else:
                    # default LSMinimumSystemVersion == 10.0.0 (Apple Developer)
                    v = plist.get('LSMinimumSystemVersion', '10.0')
                    # some developers are dumb...
                    v.replace(' ', '')
                    try:
                        versions.append(StrictVersion(v))
                    except ValueError as e:
                        self.log.error(f"invalid version: {v!r} (using default)")
                        versions.append(StrictVersion('10.0'))
            # minimum version is the HIGHEST version of all bundles
            # NOTE: if one component requires 10.14.6, but another requires
            #       10.2.0, then the lowest OS the app run on is 10.14.6
            self.log.debug(f"versions: {sorted(versions)}")
            try:
                self._min_os_ver = sorted(versions)[-1]
            except IndexError:
                self._min_os_ver = StrictVersion('10.0')
            # save the metadata for future use
            try:
                xattr('-w', VERSIONKEY, self._min_os_ver, self.path)
            except subprocess.CalledProcessError:
                self.log.error(f"xattr failed")
        return self._min_os_ver

    @property
    def info(self):
        if not self._info:
            try:
                _pkginfo = extract(self.path, 'PackageInfo', TMPDIR)
            except subprocess.CalledProcessError:
                raise InvalidPackageError(self.path)
            _pkg = package_information(info=_pkginfo)
            self._info = {'name': self.path.name,
                          'path': str(self.path.absolute()),
                          'pkginfo': _pkg['pkginfo']}
            location = pathlib.Path(_pkg['pkginfo']['install-location'])
            info_keys = ('CFBundleShortVersionString', 'CFBundleVersion')
            contents = []
            for bundle in _pkg['bundles']:
                _info = {k: v for k, v in bundle.items() if k in info_keys}
                path = location / bundle['path']
                _info.update({'CFBundleIdentifier': bundle['id'],
                              'name': path.name,
                              'path': str(path)})
                contents.append(_info)
            self._info['contents'] = contents
        return self._info

    @property
    def stat(self):
        if not self._stat:
            self._stat = self.path.stat()
        return self._stat

    # @property
    # def reboot(self):
    #     """
    #     calculate md5 digest on demand
    #     """
    #     if not self._md5:
    #         self._calculate_checksums()
    #     return self._md5

    def expand(self):
        """
        Expand a package
        """
        if not self.expanded:
            self.log.info(f"expanding: {self.name}")
            if not TMPDIR.exists():
                TMPDIR.mkdir(mode=0o755)
            e = TMPDIR / self.path.stem
            if e.exists():
                # check to see if the information matches
                _extracted = extract(self.path, 'PackageInfo', e)
                _pkg = package_information(info=_extracted)
                _exists = package_information(path=e/'PackageInfo')
                # continue with expansion if different, or use existing
                # TO-DO: should probably test for empty directory
                self.expanded = (expand_package(self.path, path=e, ov=True)
                                 if _exists != _pkg else e)
            else:
                # no existing path was found
                self.expanded = expand_package(self.path, path=e)
        return self.expanded

    def _calculate_checksums(self):
        """
        calculates md5 and sha512 checksums simultaneiously
        """
        hashes = [hashlib.md5(), hashlib.sha512()]
        _checksums = calculate_checksums(self.path, hashes)
        self._md5, self._sha512 = [h.hexdigest() for h in _checksums]

    def install(self, target='/'):
        """
        convenience function to install this package
        """
        install_package(self.path)

    def __del__(self):
        try:
            if self.expanded:
                self.log.debug(f"cleaning up: '{self.expanded}'")
                shutil.rmtree(self.expanded, ignore_errors=True)
                self.log.info(f"cleaning up: '{TMPDIR}'")
                shutil.rmtree(TMPDIR, ignore_errors=True)
        except AttributeError:
            pass

    def __eq__(self, x):
        """x == y"""

        if not isinstance(x, Package):
            raise TypeError(f"not a Package: {x!r}")
        if self is x:
            return True
        elif self.path.samefile(x.path):
            return True
        else:
            return self.identifier == x.identifier and self.apps == x.apps

    def __lt__(self, x):
        """x < y"""
        if not isinstance(x, Package):
            raise TypeError(f"not a Package: {x!r}")
        if not self.identifier == x.identifier:
            raise ValueError(f"{self.identifer} != {x.identifier}")
        # if versions are identical, check the creation timestamp
        if self.version == x.version:
            return self.stat.st_ctime < x.stat.st_ctime
        else:
            return self.version < x.version

    def __gt__(self, x):
        """x > y"""
        if not isinstance(x, Package):
            raise TypeError(f"not a Package: {x!r}")
        if not self.identifier == x.identifier:
            raise ValueError(f"{self.identifer} != {x.identifier}")
        # if versions are identical, check the creation timestamp
        if self.version == x.version:
            return self.stat.st_ctime > x.stat.st_ctime
        else:
            return self.version > x.version

    def __le__(self, x):
        """x >= y"""
        return self == x or self < x

    def __ge__(self, x):
        """x <= y"""
        return self == x or self < x

    def __repr__(self):
        # <cls>('/path/to/package') e.g. Package('/tmp/example.pkg')
        return f"{self.__class__.__name__}('{self.path}')"

    def __str__(self):
        return str(self.path)


class Repo:
    """
    Package Repository
    """
    def __init__(self, path, pattern='*pkg'):
        self.log = logging.getLogger(f"{__name__}.Repo")
        self._config = None
        self.path = pathlib.Path(path).absolute()
        self.archive = self.path / 'archive'
        # "*pkg" should match [*.mpkg, '*.pkg']
        self.pattern = pattern
        self._packages = None

    @property
    def packages(self):
        """
        :returns <list>:    list of all Packages
        """
        if not self._packages:
            self._packages = []
            for path in self.path.glob(self.pattern):
                # exclude hidden files
                if not path.name.startswith('.'):
                    self._packages.append(Package(path))
        return self._packages

    @property
    def category(self):
        return self.config.get('category', 'No category assigned')

    @property
    def config(self):
        # TO-DO: this should be handled by config.Config()
        if not self._config:
            path = self.path / 'edu.utah.mlib.jctl.plist'
            self._config = config.Config(path=path)
            if not self._config.load():
                # TO-DO: need to create a template
                template = {}
                self._config.save(template)

        return self._config

    @property
    def archived_packages(self):
        return

    def archive_packages(self, pkgs):
        """
        :returns <list>:    list of all Packages
        """
        if not self.archive.exists():
            # create archive directory if missing
            self.log.debug(f"creating archive: {self.archive}")
            self.archive.mkdir()
        archiving = set(self.packages).intersection(pkgs)
        self.log.info(f"archiving: {', '.join([x.name for x in archiving])}")
        self._packages = list(set(self.packages).difference(archiving))
        self.log.debug(f"repo packages: {', '.join([x.name for x in self.packages])}")
        for pkg in archiving:
            _archived = self.archive / pkg.name
            pkg.path.rename(_archived)
            pkg.path = _archived

    def refresh(self):
        """
        look for new packages in repo
        """
        known = [pkg.path for pkg in self._packages]
        for path in self.path.glob(self.pattern):
            if path not in known:
                self._packages.append(Package(path))
        # self._packages = [x for x in self._packages
        #                   if self.archive not in x.path.parents]

    def find(self, condition=lambda x: False):
        """
        Find all Packages matching conditional callback

        :param condition <func>:  limit results to condition(pkg)
        :returns <list>:          all Packages matching condition

        Examples:
           # packages > 1GB in size
           >>> repo.find(lambda pkg: pkg.size > 1000000000)

           # packages with name that starts with 'busycal'
           >>> repo.find(lambda pkg: pkg.name.startswith('busycal'))

        """
        return [pkg for pkg in self.packages if condition(pkg)]


# def verify(api, pkg):
#     """
#     Verify package on JSS
#
#     :param api:  jamf.API object
#     :param pkg:  Package object
#     """
#     raise NotImplementedError()


def install_package(pkg, target='/'):
    """
    Install a package

    :param pkg <str|Path|Package>:      package to install
    :param target <str|Path>:           target volume
    """
    logger = logging.getLogger(__name__)
    path = pkg.path.absolute() if isinstance(pkg, Package) else pkg
    logger.info(f"installing package: {path}")
    cmd = ['/usr/sbin/installer', '-pkg', path, '-target', target]
    logger.debug(f"> sudo -n installer -pkg {path!r} -target {target!r}")
    subprocess.check_call(['/usr/bin/sudo', '-n'] + cmd)


# def jss_package_details(api, name=None):
#     """
#     :returns: detailed list of all packages in the JSS
#     """
#     # Each dict has the following keys:
#     # ['allow_uninstalled',              # <bool> likely the index value (would be cool if it could be indexed via modification)
#     #  'boot_volume_required',           # <bool> ? (universally: False)
#     #  'category',                       # <str>  name of category
#     #  'filename',                       # <str>  name of pkg file
#     #  'fill_existing_users',            # <bool> ? (universally: False)
#     #  'fill_user_template',             # <bool> ? (universally: False)
#     #  'id',                             # <int>  JSS id
#     #  'info',                           # <str>  contents of "Info" field
#     #  'install_if_reported_available',  # <str>  ? (universally: 'false')
#     #  'name',                           # <str>  name of package (typically same as filename)
#     #  'notes',                          # <str>  contents of "Notes" field
#     #  'os_requirements',                # <str>  os requirements? (universally: '')
#     #  'priority',                       # <int>  installation priority? (universally: 10)
#     #  'reboot_required',                # <bool> package requires reboot
#     #  'reinstall_option',               # <str>  ? (universally: "Do Not Reinstall")
#     #  'required_processor',             # <str>  processor limitation? (universally: 'None')
#     #  'send_notification',              # <bool> ? (universally: False)
#     #  'switch_with_package',            # <str>  ? (universally: 'Do Not Install')
#     #  'triggering_files']               # <dict> ? (universally: {})
#
#     # detailed list of every package (takes a long time)
#     pkgs = []
#     # isolating packages by name is handled by packages()
#     for pkg in jamf_records(Packages, name):
#         details = api.get(f"packages/id/{pkg['id']}")
#         pkgs.append(details['package'])
#     return pkgs


def jss_packages(jss, name=None):
    """
    returns packages matching name (case-insensitive)

    :param name <str>:  target name (i.e. name in d['name'])

    :returns:   list of dicts w/ keys: ('id', 'name')
                  e.g. [{'id': 23, 'name': 'vfuse-1.0.3.pkg'}, ...]
    """
    # return [pkg for pkg in packages if name in pkg['name']]
    name = name.lower()
    pkgs = []
    # for pkg in jss.get('packages', xml=True)['packages']['package']:
    for pkg in jss.get('packages')['packages']:
        if not name or name in pkg['name'].lower():
            pkgs.append(pkg)
    return pkgs


def installer_packages():
    """
    quick and dirty dump of packages on InstallerPackages
    """
    vol = '/Volumes/InstallerPackages/munkipkg_projects'
    import glob
    g = os.path.join(vol, '*/payload/*.app')
    info = {}
    for path in glob.glob(g):
        name = os.path.splitext(os.path.basename(path))[0]
        directory = path.split('/payload')[0]
        folder = os.path.basename(directory)
        pkgs = []
        for pkg in glob.glob(os.path.join(directory, 'build/*.pkg')):
            pkgs.append(os.path.basename(pkg))
        plist = os.path.join(directory, 'build-info.plist')
        with open(plist, 'rb') as f:
            b_info = plistlib.load(f)
        info[name] = {'pkgs': pkgs, 'folder': folder,
                      'build': b_info, 'name': name}


def pkgutil(*args):
    """
    Execute `pkgutil` with specified args (see `man pkgutil` for more info)
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"args: {args!r}")
    cmd = ['/usr/sbin/pkgutil'] + [str(x) for x in args]
    out = subprocess.check_output(cmd, stderr=subprocess.PIPE)
    try:
        result = plistlib.loads(out)
        logger.debug("successfully converted plist")
    except plistlib.InvalidFileException:
        logger.debug("output not in plist format")
        result = out
    return result


def expand_package(pkg, path=None, full=False, ov=False):
    """
    Expand Mac OS X Installer packages

    :param pkg <str|Path>:     path of package to expand
    :param path <str|Path>:    expand package path to specified path
                                 (parent directory must exist)
    :param full <bool>:        fully expand all package files
    :param ov <bool>:          overwrite previously expanded package

    :returns <Path>:           expanded package directory
    """
    logger = logging.getLogger(__name__)
    pkg = pathlib.Path(pkg).absolute()
    logger.info(f"expanding package: {pkg.name}")
    try:
        # use user specified path
        expanded = pathlib.Path(path)
    except TypeError:
        # default: $TMPDIR/edu.utah.mlib.packages/{name}
        expanded = TMPDIR / pkg.stem
    # overwrite existing destination ()
    if ov and expanded.exists():
        logger.info(f"overwriting path: {expanded}")
        shutil.rmtree(expanded)
    elif expanded.exists():
        logger.error(f"destination already exists: {expanded}")
        raise FileExistsError(expanded)
    # https://stackoverflow.com/questions/41166805/how-to-extract-contents-from-payload-file-in-a-apple-macos-update-package
    expand_type = '--expand-full' if full else '--expand'
    # will fail if parent directory does not exist
    pkgutil(expand_type, pkg, expanded)
    return expanded


def calculate_checksums(path, hashes, copy=True, bufsize=8192):
    """
    Update multiple hashlib.HASH objects with single file read.

    :param path <str|Path>:    path to file
    :param hashes <iterable>:  iterable of hashlib.HASH objects
    :param copy <bool>:        copy each hash before updating
    :param bufsize <int>:      specify size of buffer

    :returns <list>:           list of updated hashlib.HASH objects
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"calculating checksums: {path}")
    # copy each hash if specified, otherwise update original hash objects
    hashes = [hash.copy() if copy else hash for hash in hashes]
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(bufsize), b''):
            # update each hash with the contents of file as it's read
            for hash in hashes:
                hash.update(chunk)
    return hashes


def extract_info_plist(payload, app_path):
    """
    extract Info.plist from package payload
    :param payload <str|Path>:      path to zipped pkg payload
    :param app_path <str|Path>:     path to app to extract in payload
    """
    path = pathlib.Path(app_path) / 'Contents' / 'Info.plist'
    return plistlib.loads(extract_tar(path, payload))


def extract_tar(payload, path):
    logger = logging.getLogger(__name__)
    logger.info(f"extracting using tar: '{path}'")
    logger.info(f"> tar -xOf '{payload}' '{path}'")
    tar_output = subprocess.check_output(['/usr/bin/tar', '-xOf', path, payload])
    return tar_output


def extract(path, payload, save_dir):
    logger = logging.getLogger(__name__)
    logger.info(f"extracting using xar: '{path}'")
    if not TMPDIR.exists():
        TMPDIR.mkdir(mode=0o755)
    logger.debug(f"> xar -xf '{path}' '{payload}' -C '{save_dir}'")
    xar_output = subprocess.check_output(['/usr/bin/xar', '-xf', path, payload, '-C', save_dir])
    pkg_info = subprocess.check_output(['/bin/cat', save_dir / payload])
    return (pkg_info)


def find_payload(archive):
    """
    locate payload inside of an archive
    """
    # https://dev.to/aarohmankad/bash-functions-a-more-powerful-alias-4p3i
    cmd = ['/usr/bin/xar', '-tf', archive]
    raise NotImplementedError()


def package_information(path=None, info=None):
    """
    Get information from PackageInfo XML

    :param path <str|Path>:  path to PackageInfo XML

    :returns: dict of information regarding the package
        e.g.    {'install-location': '/Applications/Programming',
                 'relocatable': None,
                 'id': 'com.barebones.bbedit',
                 'version': '13.0.2',
                 'bundles': [{'CFBundleShortVersionString': '13.0.2',
                              'CFBundleVersion': '413044',
                              'path': './BBEdit.app',
                              'id': 'com.barebones.bbedit'}]}
    """
    logger = logging.getLogger(__name__)
    if path:
        logger.info(f"reading package info file: {path}")
        path = pathlib.Path(path).absolute()
        root = ET.parse(path).getroot()
    elif info:
        root = ET.fromstring(info)
    else:
        raise TypeError("must specify path or string")

    # verify root tag == 'pkg-info'
    if root.tag != 'pkg-info':
        raise Error(f"unexpected xml tag: {root.tag!r} != 'pkg-info'")
    # unsure if this is necessary (I haven't seen anything other than 2)
    fmt_ver = int(root.attrib['format-version'])
    if fmt_ver != 2:
        logger.debug("unsure if this error can be ignored")
        raise Error(f"unexpected 'format-version': {fmt_ver} != 2")
    # get information about package
    _pkginfo = root.attrib.copy()
    _pkginfo.setdefault('install-location', '/')
    info = {'pkginfo': _pkginfo, 'bundles': []}

    # get a list of bundle-ids that we care about
    ids = [e.attrib['id'] for e in root.findall('bundle-version/bundle')]
    # find all bundles that are installed and get information about each one
    for e in root.findall('bundle'):
        id_ = e.attrib.get('id')
        if id_ and id_ in ids:
            # only get attributes for bundles in 'pkg-info/bundle-version'
            info['bundles'].append(e.attrib.copy())
    return info


def xattr(*args):
    """
    Execute `xattr` with specified args (see `man pkgutil` for more info)
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"xattr args: {args!r}")
    cmd = ['/usr/bin/xattr'] + [str(x) for x in args]
    out = subprocess.check_output(cmd, stderr=subprocess.PIPE)
    return out.decode('utf-8').rstrip()
