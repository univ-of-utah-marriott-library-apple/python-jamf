#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Jamf Config
"""

__author__ = "Sam Forester"
__email__ = "sam.forester@utah.edu"
__copyright__ = "Copyright (c) 2020 University of Utah, Marriott Library"
__license__ = "MIT"
__version__ = "1.0.6"


import argparse
import getpass
import logging
import platform
import sys

import jamf


class Parser:
    def __init__(self):
        myplatform = platform.system()
        if myplatform == "Darwin":
            default_pref = jamf.config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = jamf.config.LINUX_PREFS_TILDA
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument(
            "-H", "--hostname", help="specify hostname (default: prompt)"
        )
        self.parser.add_argument(
            "-u", "--user", help="specify username (default: prompt)"
        )
        self.parser.add_argument(
            "-p", "--passwd", help="specify password (default: prompt)"
        )
        self.parser.add_argument(
            "-r", "--revoke-token", action="store_true", help="Revoke Bearer token"
        )
        self.parser.add_argument(
            "-C",
            "--config",
            dest="path",
            metavar="PATH",
            default=default_pref,
            help=f"specify config file (default {default_pref})",
        )
        self.parser.add_argument(
            "-P",
            "--print",
            action="store_true",
            help="print existing config profile (except password!)",
        )
        self.parser.add_argument(
            "-t",
            "--test",
            action="store_true",
            help="Connect to the Jamf server using the config file",
        )

    def parse(self, argv):
        """
        :param argv:    list of arguments to parse
        :returns:       argparse.NameSpace object
        """
        return self.parser.parse_args(argv)


def test(config_path):
    api = jamf.API(config_path=config_path)
    try:
        print(api.get("accounts"))
        print("Connection successful")
    except SystemExit as error:
        print(f"Connection failed, check your settings\n{error}")


def print_config(config_path):
    conf = jamf.config.Config(prompt=False, explain=True, config_path=config_path)
    print(conf.hostname)
    print(conf.username)
    if conf.password:
        print("Password is set")
    else:
        print("Password is not set")


def revoke_token(config_path):
    api = jamf.API(config_path=config_path)
    api.revoke_token()


def interactive(args, config_path):
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
        prompt=False,
        config_path=config_path,
    )
    conf.save()
    print("Test the config by invoking `conf-python-jamf -t`")


def setconfig(argv):
    logger = logging.getLogger(__name__)
    args = Parser().parse(argv)
    logger.debug(f"args: {args!r}")
    if args.path:
        config_path = args.path
    else:
        myplatform = platform.system()
        if myplatform == "Darwin":
            default_pref = jamf.config.MACOS_PREFS_TILDA
        elif myplatform == "Linux":
            default_pref = jamf.config.LINUX_PREFS_TILDA
        config_path = default_pref
    config_path = jamf.config.resolve_config_path(config_path)
    if args.test:
        test(config_path)
    elif args.print:
        print_config(config_path)
    elif args.revoke_token:
        revoke_token(config_path)
    else:
        interactive(args, config_path)


def main():
    fmt = "%(asctime)s: %(levelname)8s: %(name)s - %(funcName)s(): %(message)s"
    logging.basicConfig(level=logging.INFO, format=fmt)
    setconfig(sys.argv[1:])


if __name__ == "__main__":
    main()
