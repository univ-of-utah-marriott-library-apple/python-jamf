#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jamf Config
"""

__author__ = 'Sam Forester'
__email__ = 'sam.forester@utah.edu'
__copyright__ = 'Copyright (c) 2020 University of Utah, Marriott Library'
__license__ = 'MIT'
__version__ = "1.0.4"

min_jamf_version = "0.4.7"


import argparse
import getpass
import jamf
import logging
import platform
import pprint
import sys
from os import path

class Parser:

    def __init__(self):
        myplatform = platform.system()
        if myplatform == "Darwin":
            default_pref = jamf.config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = jamf.config.LINUX_PREFS_TILDA

        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            '-H',
            '--hostname',
            help='specify hostname (default: prompt)')
        self.parser.add_argument(
            '-u',
            '--user',
            help='specify username (default: prompt)')
        self.parser.add_argument(
            '-p',
            '--passwd',
            help='specify password (default: prompt)')
        self.parser.add_argument(
            '-c',
            '--config',
            dest='path',
            metavar='PATH',
            default=default_pref,
            help=f"specify config file (default {default_pref})")
        self.parser.add_argument(
            '-P',
            '--print',
            action='store_true',
            help='print existing config profile (except password!)')
        self.parser.add_argument(
            '-t',
            '--test',
            action='store_true',
            help='Connect to the Jamf server using the config file')

    def parse(self, argv):
        """
        :param argv:    list of arguments to parse
        :returns:       argparse.NameSpace object
        """
        return self.parser.parse_args(argv)

def check_version():

    try:
        jamf_first, jamf_second, jamf_third = jamf.__version__.split(".")
        min_first, min_second, min_third = min_jamf_version.split(".")

        if ( int(jamf_first) <= int(min_first) and
             int(jamf_second) <= int(min_second) and
             int(jamf_third) < int(min_third)):
             print(f"Your Version is: {jamf.__version__}, you need at least version {min_jamf_version} to run jctl.")
             sys.exit()

    except AttributeError:
             print(f"Your Version is below 0.4.2, you need at least version {min_jamf_version} to run jctl.")
             sys.exit()

def setconfig(argv):
    logger = logging.getLogger(__name__)
    args = Parser().parse(argv)
    logger.debug(f"args: {args!r}")

    if args.test:
        api = jamf.API()
        pprint.pprint(api.get('accounts'))

    elif args.print:
        conf = jamf.config.Config(prompt=False,explain=True)
        print(conf.hostname)
        print(conf.username)
        if conf.password:
            print("Password is set")
        else:
            print("Password is not set")
    else:
        if args.path:
            config_path = args.path
        else:
            config_path = self.default_pref

        if config_path[0] == '~':
            config_path = path.expanduser(config_path)

        if args.hostname:
            hostname = args.hostname
        else:
            hostname = jamf.config.prompt_hostname()

        if args.user:
            user = args.user
        else:
            user = input("username: ")

        if args.passwd:
            passwd = args.passwd
        else:
            passwd = getpass.getpass()

        conf = jamf.config.Config(
            hostname=hostname,
            username=user,
            password=passwd,
            prompt=False
        )
        conf.save(config_path=config_path)


def main():
    check_version()
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    setconfig(sys.argv[1:])


if __name__ == "__main__":
    main()
